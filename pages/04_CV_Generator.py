"""
Streamlit page for CV Generation Hub
Central location for managing CV generation across the application

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-21
Last Updated: 2026-01-27
"""

import streamlit as st
import os
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
import sys
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core.database.db import Database
from core.database.translations import initialize_translations
from core.utils.session import get_database, get_translations_manager, get_text
from scripts.streamlit_pipeline import StreamlitCVGenerator
# F003: Imports updated in Offer generation on-demand section (no longer at top level)

# Set current page for sidebar
st.session_state.current_page = "pages/04_CV_Generator.py"

# --- Import render_simple_sidebar from app ---
try:
    from app import render_simple_sidebar
except ImportError:
    def render_simple_sidebar():
        """Fallback if sidebar rendering fails"""
        pass


# --- Helper Functions ---
def t(section, key, lang="de"):
    """Get translated text using database-backed translations"""
    return get_text(section, key, lang)


def reset_all_pipeline_states():
    """Resets all session state variables related to the pipeline dialog/view."""
    st.session_state.show_pipeline_dialog = False
    st.session_state.show_results_view = False
    if "current_generation_results" in st.session_state:
        del st.session_state.current_generation_results

def load_history():
    HISTORY_FILE = os.path.join("output", "run_history.json")
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_to_history(entry):
    HISTORY_FILE = os.path.join("output", "run_history.json")
    history = load_history()
    history.insert(0, entry)
    history = history[:50]
    
    os.makedirs("output", exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def get_api_key():
    """Retrieves the OpenAI API Key from secrets (Cloud), environment variables (Local), or user input."""
    try:
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except FileNotFoundError:
        pass
    except Exception:
        pass
    
    env_key = os.getenv("OPENAI_API_KEY")
    if env_key:
        return env_key
    
    if "api_key" in st.session_state:
        return st.session_state.api_key
    
    return None

# Initialize language if not set
if 'language' not in st.session_state:
    st.session_state.language = "de"

# Set current page for sidebar active state detection
st.session_state.current_page = "pages/04_CV_Generator.py"

# Reset results view on page load ONLY if not explicitly requested from history details button
# This prevents old results from being shown when navigating to this page
if not st.session_state.get("show_results_view_requested", False):
    st.session_state.show_results_view = False
else:
    # Clear the flag after using it (one-time use)
    st.session_state.show_results_view_requested = False

# --- Simple Sidebar with Logo and Navigation ---
render_simple_sidebar()

# --- Sidebar Navigation ---
db = get_database()
tm = get_translations_manager()

# --- Page Content ---
st.title(get_text("ui", "app_title", st.session_state.language))
st.markdown(get_text("ui", "app_subtitle", st.session_state.language))

# Mode Selection with Cards
st.subheader(get_text("ui", "mode_select_title", st.session_state.language))

col_m1, col_m2, col_m3 = st.columns(3)

# Initialize mode in session state if not present
if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = "Full (CV + Stellenprofil + Match + Feedback)"

primary_color = st.session_state.get("custom_styles", {}).get("primary_color", "#FF7900")
secondary_color = st.session_state.get("custom_styles", {}).get("secondary_color", "#444444")
selected_font = st.session_state.get("custom_styles", {}).get("font", "Aptos")

# Create clickable columns
with col_m1:
    if st.button(get_text("ui", "mode_basic", st.session_state.language), use_container_width=True, type="primary" if st.session_state.selected_mode.startswith("Basic") else "secondary"):
        st.session_state.selected_mode = "Basic (Nur CV)"
        reset_all_pipeline_states()
        st.rerun()
    st.caption(get_text("ui", "mode_basic_desc", st.session_state.language))

with col_m2:
    if st.button(get_text("ui", "mode_analysis", st.session_state.language), use_container_width=True, type="primary" if st.session_state.selected_mode.startswith("Analysis") else "secondary"):
        st.session_state.selected_mode = "Analysis (CV + Stellenprofil)"
        reset_all_pipeline_states()
        st.rerun()
    st.caption(get_text("ui", "mode_analysis_desc", st.session_state.language))

with col_m3:
    if st.button(get_text("ui", "mode_full", st.session_state.language), use_container_width=True, type="primary" if st.session_state.selected_mode.startswith("Full") else "secondary"):
        st.session_state.selected_mode = "Full (CV + Stellenprofil + Match + Feedback)"
        reset_all_pipeline_states()
        st.rerun()
    st.caption(get_text("ui", "mode_full_desc", st.session_state.language))

mode = st.session_state.selected_mode
st.divider()

# Check for Mock Mode
is_mock = os.environ.get("MODEL_NAME") == "mock"

# Helper function to show results content
def show_results_content(results, lang):
    """Display CV generation results with downloads and dashboard"""
    st.subheader(get_text("ui", "results_title", lang))
    
    candidate_name = get_text("ui", "history_unknown", lang)
    if results.get("cv_json"):
        try:
            filename = os.path.basename(results["cv_json"])
            parts = filename.split('_')
            if len(parts) >= 3: candidate_name = f"{parts[1]} {parts[2]}"
        except (IndexError, AttributeError):
            pass
    
    model_used = results.get("model_name", os.environ.get("MODEL_NAME", "gpt-4o-mini"))
    st.caption(f"{get_text('ui', 'history_mode', lang)}: {results.get('mode', get_text('ui', 'history_unknown', lang))} | {get_text('ui', 'history_model', lang)}: {model_used}")
        
    cv_btn_label = f"{get_text('ui', 'word_cv_btn', lang)} - {candidate_name}"
    if len(cv_btn_label) > 30:
        cv_btn_label = cv_btn_label[:27] + "..."
    
    with st.success(get_text("ui", "downloads_title", lang), icon="📥"):
        res_col1, res_col2, res_col3, res_col4 = st.columns(4)
        with res_col1:
            # F003: CV Word Download from bytes (no more file paths)
            cv_word_bytes = results.get("cv_word_bytes")
            cv_word_filename = results.get("cv_word_filename", "CV.docx")
            
            if cv_word_bytes:
                # CV Word already generated - show download
                st.download_button(
                    cv_btn_label, 
                    cv_word_bytes, 
                    cv_word_filename, 
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                    use_container_width=True
                )
            else:
                # Fallback message (shouldn't happen with F003)
                st.info(get_text("ui", "cv_not_available", lang), icon="ℹ️")
            
        with res_col2:
            # JSON Data Button
            if results.get("cv_json") and os.path.exists(results["cv_json"]):
                with open(results["cv_json"], "rb") as f:
                    st.download_button(get_text("ui", "json_data_btn", lang), f, os.path.basename(results["cv_json"]), "application/json", use_container_width=True)
                    
        with res_col3:
            # F003: Dashboard Button from bytes
            dashboard_bytes = results.get("dashboard_bytes")
            dashboard_filename = results.get("dashboard_filename", "Dashboard.html")
            if dashboard_bytes:
                st.download_button(
                    get_text("ui", "dashboard_btn", lang), 
                    dashboard_bytes, 
                    dashboard_filename, 
                    "text/html", 
                    use_container_width=True
                )
        
        with res_col4:
            # F003: ZIP Bundle Download from workspace
            workspace = results.get("workspace")
            run_id = results.get("run_id", "download")
            if workspace:
                try:
                    zip_bytes = workspace.bundle_as_zip()
                    # Use new naming convention for ZIP filename
                    jobprofile_slug = results.get("jobprofile_slug", "gdjob_unknown")
                    candidate_name = results.get("candidate_name", f"{results.get('vorname', 'Unknown')}_{results.get('nachname', '')}")
                    timestamp = results.get("timestamp", datetime.now().strftime("%Y%m%d_%H%M%S"))
                    zip_filename = f"{jobprofile_slug}_{candidate_name}_{timestamp}.zip"
                    
                    st.download_button(
                        "📦 ZIP Bundle",
                        zip_bytes,
                        zip_filename,
                        "application/zip",
                        use_container_width=True,
                        help="Alle Dateien als ZIP"
                    )
                except Exception as e:
                    st.caption(f"ZIP: {str(e)[:30]}")
            else:
                st.caption("ZIP nicht verfügbar")

    if not results.get("stellenprofil_json") and results.get("cv_json"):
        output_dir = os.path.dirname(results["cv_json"])
        try:
            for f in os.listdir(output_dir):
                # Support both old naming (stellenprofil_*) and new naming (*_jobprofile_*)
                if (f.startswith("stellenprofil_") or "_jobprofile_" in f) and f.endswith(".json"):
                    results["stellenprofil_json"] = os.path.join(output_dir, f)
                    break
        except OSError:
            pass

    if not results.get("match_json") and results.get("cv_json"):
        output_dir = os.path.dirname(results["cv_json"])
        try:
            for f in os.listdir(output_dir):
                # Support both old naming (Match_*) and new naming (*_match_*)
                if (f.startswith("Match_") or "_match_" in f) and f.endswith(".json"):
                    results["match_json"] = os.path.join(output_dir, f)
                    break
        except OSError:
            pass

    if results.get("stellenprofil_json") and os.path.exists(results["stellenprofil_json"]):
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        
        # F003: Check for Offer bytes from workspace
        offer_word_bytes = results.get("offer_word_bytes")
        offer_word_filename = results.get("offer_word_filename", "Offer.docx")
        is_offer_ready = offer_word_bytes is not None
        
        if is_offer_ready:
            offer_container = st.success(get_text("ui", "offer_ready", lang), icon="✅")
        else:
            offer_container = st.info(get_text("ui", "offer_create_title", lang), icon="✨")
        
        with offer_container:
            off_col1, off_col2, off_col3 = st.columns(3)
            with off_col1:
                if is_offer_ready:
                    st.download_button(
                        get_text("ui", "offer_download_btn", lang), 
                        offer_word_bytes, 
                        offer_word_filename, 
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                        use_container_width=True, 
                        type="primary"
                    )
                else:
                    off_btn_key = f"gen_offer_btn_{results.get('cv_json', '')}"
                    if st.button(get_text("ui", "offer_create_btn", lang), use_container_width=True, key=off_btn_key):
                        with st.status(get_text("ui", "status_offer", lang), expanded=True) as status:
                            try:
                                from scripts._5_generation_offer.offer_generator import generate_angebot_json
                                from scripts._5_generation_offer.offer_word import generate_offer_bytes
                                
                                cv_json = results["cv_json"]
                                stellenprofil_json = results["stellenprofil_json"]
                                match_json = results.get("match_json")
                                output_dir = os.path.dirname(cv_json)
                                base_name = os.path.basename(cv_json).replace("cv_", "").replace(".json", "")
                                angebot_json_path = os.path.join(output_dir, f"Angebot_{base_name}.json")
                                schema_path = os.path.join(os.getcwd(), "scripts", "_5_generation_offer", "offer_schema.json")
                                
                                status.write("🧠 KI-Inhalte generieren...")
                                generate_angebot_json(cv_json, stellenprofil_json, match_json, angebot_json_path, schema_path, language=lang)
                                
                                # F003: Generate Offer Word using bytes API
                                status.write("📝 Word-Dokument formatieren...")
                                with open(angebot_json_path, 'r', encoding='utf-8') as f:
                                    offer_data = json.load(f)
                                offer_bytes, offer_filename = generate_offer_bytes(offer_data, language=lang)
                                
                                # Store in results for download
                                results["offer_word_bytes"] = offer_bytes
                                results["offer_word_filename"] = offer_filename
                                st.session_state.generation_results = results
                                st.session_state.show_pipeline_dialog = True
                                st.session_state.show_results_view = True
                                status.update(label=get_text('ui', 'offer_ready_label', lang), state="complete")
                                st.success(get_text('ui', 'offer_success', lang))
                                st.rerun()
                            except Exception as e:
                                status.update(label=get_text('ui', 'error_label', lang), state="error")
                                st.error(f"{get_text('ui', 'offer_error', lang)} {e}")
                                import traceback
                                st.code(traceback.format_exc())
            with off_col2:
                if not is_offer_ready:
                    st.caption(get_text('ui', 'offer_button_caption', lang))
                else:
                    st.caption(get_text('ui', 'offer_ready_caption', lang))

    st.markdown("<div style='margin-top: 40px; margin-bottom: 20px; border-top: 1px solid #ddd;'></div>", unsafe_allow_html=True)

    # F003: Dashboard Preview from bytes
    dashboard_bytes = results.get("dashboard_bytes")
    if dashboard_bytes:
        html_content = dashboard_bytes.decode('utf-8')
        st.components.v1.html(html_content, height=1200, scrolling=True)

# Helper function for custom upload UI
def render_custom_uploader(label, key_prefix, file_type=["pdf"]):
    if "cv" in key_prefix.lower():
        file_state_key = "shared_cv_file"
    elif "job" in key_prefix.lower():
        file_state_key = "shared_job_file"
    else:
        file_state_key = f"{key_prefix}_file"
    
    if file_state_key not in st.session_state:
        st.session_state[file_state_key] = None
    
    st.subheader(label)
    
    widget_key = f"{key_prefix}_widget"
    
    uploaded_file = st.file_uploader(
        label, 
        type=file_type, 
        key=widget_key, 
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        prev_file = st.session_state.get(file_state_key)
        is_new_file = False
        if prev_file is None:
            is_new_file = True
        elif uploaded_file.name != prev_file.name or uploaded_file.size != prev_file.size:
            is_new_file = True

        if is_new_file:
            st.session_state[file_state_key] = uploaded_file
            if "generation_results" in st.session_state:
                del st.session_state.generation_results
            if "current_generation_results" in st.session_state:
                del st.session_state.current_generation_results
            st.session_state.show_pipeline_dialog = False
            st.session_state.show_results_view = False
    elif st.session_state[file_state_key] is not None:
        st.session_state[file_state_key] = None
        st.session_state.show_pipeline_dialog = False
        st.session_state.show_results_view = False
        if "generation_results" in st.session_state:
            del st.session_state.generation_results

    current_file = st.session_state[file_state_key]
    if current_file:
        st.markdown(f"""
            <div style="background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 10px 15px; border-radius: 5px; margin-top: -10px; margin-bottom: 10px;">
                <strong>{get_text("ui", "file_active", st.session_state.language)}</strong> {current_file.name}
            </div>
        """, unsafe_allow_html=True)
                
    return current_file

# Dynamic Columns based on Mode
if mode.startswith("Basic"):
    col1, col2 = st.columns(2)
    with col1:
        if is_mock:
            st.subheader(get_text("ui", "cv_title", st.session_state.language))
            st.success(get_text("ui", "test_mode_active", st.session_state.language))
            st.caption(get_text("ui", "test_mode_desc", st.session_state.language))
            cv_file = None
        else:
            cv_file = render_custom_uploader(get_text("ui", "cv_title", st.session_state.language), "cv_basic")
        job_file = None
else:
    col1, col2 = st.columns(2)

    with col1:
        if is_mock:
            st.subheader(get_text("ui", "cv_title", st.session_state.language))
            st.success(get_text("ui", "test_mode_active", st.session_state.language))
            st.caption(get_text("ui", "test_mode_desc", st.session_state.language))
            cv_file = None
        else:
            cv_file = render_custom_uploader(get_text("ui", "cv_title", st.session_state.language), "cv_full")

    with col2:
        if is_mock:
            st.subheader(get_text("ui", "job_title", st.session_state.language))
            st.success(get_text("ui", "test_mode_active", st.session_state.language))
            st.caption(get_text("ui", "test_mode_desc", st.session_state.language))
            job_file = None
        else:
            job_file = render_custom_uploader(get_text("ui", "job_title", st.session_state.language), "job_full")

st.divider()

# DSGVO / Privacy Notice
st.markdown(f"### {get_text('ui', 'privacy_title', st.session_state.language)}")
st.caption(get_text('ui', 'privacy_desc', st.session_state.language))
dsgvo_accepted = st.checkbox(get_text('ui', 'privacy_accept', st.session_state.language), value=False)

# Action Button
api_key = get_api_key()

if is_mock:
    start_disabled = False
    if not cv_file: cv_file = "MOCK_CV.pdf"
    if not job_file: job_file = "MOCK_JOB.pdf"
    if not api_key: api_key = "mock-key"
else:
    start_disabled = not cv_file or not api_key or not dsgvo_accepted

@st.dialog("Pipeline Processing", width="large")
def run_cv_pipeline_dialog(cv_file, job_file, api_key, mode, custom_styles, custom_logo_path):
    
    if "generation_results" in st.session_state and st.session_state.get("show_results_view"):
        phase = "results"
    else:
        phase = "processing"
    
    # Apply wide CSS if results are being shown OR if explicitly requested
    if phase == "results" or st.session_state.get("show_results_view_requested"):
        st.markdown("""
            <style>
            div[data-testid="stDialog"] div[role="dialog"] {
                width: 98vw !important;
                max-width: 100vw !important;
                height: 95vh !important;
                min-height: 95vh !important;
            }
            div[data-testid="stDialog"] div[role="dialog"] > div:nth-child(2) {
                 height: calc(95vh - 80px) !important;
                 overflow-y: auto !important;
                 width: 100% !important;
                 max-width: 100% !important;
                 padding-left: 1rem !important;
                 padding-right: 1rem !important;
            }
            iframe {
                width: 100% !important;
            }
            </style>
        """, unsafe_allow_html=True)

    if phase == "processing":
        lang = st.session_state.get("language", "de")
        with st.status(get_text("ui", "processing_title", lang), expanded=True) as status:
            log_container = st.empty()
            
            def progress_callback(pct, text, state="running"):
                log_container.write(f"{get_text('ui', 'current_step', lang)} {text}")
                status.update(label=f"🔄 {text} ({pct}%)", state="running")

            try:
                current_custom_styles = {
                    "primary_color": primary_color,
                    "secondary_color": secondary_color,
                    "font": selected_font
                }
                current_custom_logo_path = st.session_state.get("custom_logo_path")
                
                if "current_generation_results" in st.session_state:
                    results = st.session_state.current_generation_results
                else:
                    generator = StreamlitCVGenerator(os.getcwd())
                    results = generator.run(
                        cv_file=cv_file,
                        job_file=job_file if mode != "Basic (Nur CV)" else None,
                        api_key=api_key,
                        progress_callback=progress_callback,
                        custom_styles=current_custom_styles,
                        custom_logo_path=current_custom_logo_path,
                        pipeline_mode=mode,
                        language=lang
                    )
                    st.session_state.current_generation_results = results
                
                if results.get("success"):
                    if "history_saved" not in st.session_state:
                        history_entry = {
                            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                            "candidate_name": f"{results.get('vorname', 'Unbekannt')} {results.get('nachname', '')}".strip(),
                            "mode": mode,
                            "word_path": results.get("word_path"),
                            "cv_json": results.get("cv_json"),
                            "cv_json_path": results.get("cv_json_path"),  # Für spätere on-demand Word-Generierung
                            "output_dir": results.get("output_dir"),  # Für spätere on-demand Word-Generierung
                            "dashboard_path": results.get("dashboard_path"),
                            "match_score": results.get("match_score"),
                            "model_name": results.get("model_name", os.environ.get("MODEL_NAME", "gpt-4o-mini")),
                            "stellenprofil_json": results.get("stellenprofil_json"),
                            "match_json": results.get("match_json"),
                            "offer_word_path": results.get("offer_word_path"),
                            "word_generation_pending": results.get("word_generation_pending", False)  # Flag für Button-Anzeige
                        }
                        save_to_history(history_entry)
                        st.session_state.history_saved = True

                    st.session_state.generation_results = results
                    # Set flag BEFORE showing results so CSS renders correctly
                    st.session_state.show_results_view = True
                    
                    status.update(label=get_text('ui', 'processing_complete_label', lang), state="complete")
                    st.success(get_text('ui', 'generation_success', lang))
                    st.markdown("<hr style='margin: 20px 0;'/>", unsafe_allow_html=True)
                    
                    # Show results immediately after processing
                    show_results_content(results, lang)
                else:
                    st.error(f"{get_text('ui', 'error_prefix_colon', lang)} {results.get('error')}")
                    status.update(label=get_text('ui', 'processing_error_label', lang), state="error")
                    if st.button(get_text('ui', 'close_btn', lang)):
                        st.rerun()

            except Exception as e:
                st.error(f"{get_text('ui', 'unexpected_error', lang)} {str(e)}")
                status.update(label=get_text("ui", "error_status", lang), state="error")
                if st.button(get_text("ui", "close_btn", lang)):
                        st.rerun()
    
    elif phase == "results":
        lang = st.session_state.get("language", "de")
        results = st.session_state.generation_results
        
        # Show results content
        show_results_content(results, lang)
        
        # Close button
        if st.button(get_text("ui", "close_btn", lang), use_container_width=True):
            st.session_state.show_pipeline_dialog = False
            st.session_state.show_results_view = False
            if "current_generation_results" in st.session_state:
                del st.session_state.current_generation_results
            st.rerun()

# Left-align the start button
btn_col, _ = st.columns([1, 2])
with btn_col:
    if st.button(get_text("ui", "start_generation_btn", st.session_state.language), disabled=start_disabled, type="primary", use_container_width=True):
        st.session_state.show_pipeline_dialog = True
        st.session_state.show_results_view = False
        if "current_generation_results" in st.session_state:
            del st.session_state.current_generation_results

if st.session_state.get("show_pipeline_dialog"):
    run_cv_pipeline_dialog(cv_file, job_file, api_key, mode, st.session_state.get("custom_styles"), st.session_state.get("custom_logo_path"))
