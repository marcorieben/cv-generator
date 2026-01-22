"""
Streamlit page for CV Generation Hub
Central location for managing CV generation across the application
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
from scripts.streamlit_pipeline import StreamlitCVGenerator
from scripts.generate_angebot import generate_angebot_json
from scripts.generate_angebot_word import generate_angebot_word
from core.ui.sidebar_init import render_sidebar_in_page

# Set current page for sidebar
st.session_state.current_page = "pages/04_CV_Generator.py"

# --- Page Configuration ---
st.set_page_config(
    page_title="CV Generator | CV Generator",
    page_icon="📄",
    layout="wide"
)

# --- Helper Functions ---
def get_translations_manager():
    """Get or initialize translations manager"""
    if "translations_manager" not in st.session_state:
        db = get_database()
        st.session_state.translations_manager = initialize_translations(db)
    return st.session_state.translations_manager

def t(section, key, lang="de"):
    """Get translated text using database-backed translations"""
    try:
        tm = get_translations_manager()
        return tm.get(section, key, lang) or key
    except Exception as e:
        print(f"Translation error: {e}")
        return key

def get_text(section, key, lang=None):
    """Safely retrieves translated text from database or fallback"""
    if lang is None:
        lang = st.session_state.get("language", "de")
    return t(section, key, lang)

def get_database():
    """Get or create database instance"""
    if "db_instance" not in st.session_state:
        db_path = os.path.join(os.path.dirname(__file__), "..", "data", "cv_generator.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        st.session_state.db_instance = Database(db_path)
    return st.session_state.db_instance

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
        except:
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

# --- Render Sidebar ---
if st.session_state.get("authentication_status"):
    try:
        from app import get_text, authenticator, config, name, username
        render_sidebar_in_page(
            get_text_func=get_text,
            language=st.session_state.language,
            authenticator=authenticator,
            name=name,
            username=username,
            config=config
        )
    except ImportError:
        st.sidebar.warning("Sidebar konnte nicht geladen werden")

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

@st.dialog(get_text('ui', 'dialog_pipeline', st.session_state.language), width="large")
def run_cv_pipeline_dialog(cv_file, job_file, api_key, mode, custom_styles, custom_logo_path):
    
    if "generation_results" in st.session_state and st.session_state.get("show_results_view"):
        phase = "results"
    else:
        phase = "processing"

    if phase == "results":
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
    else:
        st.markdown("""
            <style>
            div[data-testid="stDialog"] div[role="dialog"] {
                width: 50vw !important;
                max-width: 800px !important;
            }
            </style>
        """, unsafe_allow_html=True)

    if phase == "processing":
        with st.status(get_text("ui", "processing_title", st.session_state.language), expanded=True) as status:
            log_container = st.empty()
            
            def progress_callback(pct, text, state="running"):
                log_container.write(f"{get_text('ui', 'current_step', st.session_state.language)} {text}")
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
                        language=st.session_state.language
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
                            "dashboard_path": results.get("dashboard_path"),
                            "match_score": results.get("match_score"),
                            "model_name": results.get("model_name", os.environ.get("MODEL_NAME", "gpt-4o-mini")),
                            "stellenprofil_json": results.get("stellenprofil_json"),
                            "match_json": results.get("match_json"),
                            "offer_word_path": results.get("offer_word_path")
                        }
                        save_to_history(history_entry)
                        st.session_state.history_saved = True

                    st.session_state.generation_results = results
                    status.update(label=get_text('ui', 'processing_complete_label', st.session_state.language), state="complete", expanded=False)
                    st.success(get_text('ui', 'generation_success', st.session_state.language))
                    
                    if st.button(get_text("ui", "show_results", st.session_state.language), type="primary", use_container_width=True):
                        st.session_state.show_results_view = True
                        st.rerun()
                else:
                    st.error(f"{get_text('ui', 'error_prefix_colon', st.session_state.language)} {results.get('error')}")
                    status.update(label=get_text('ui', 'processing_error_label', st.session_state.language), state="error")
                    if st.button(get_text('ui', 'close_btn', st.session_state.language)):
                        st.rerun()

            except Exception as e:
                st.error(f"{get_text('ui', 'unexpected_error', st.session_state.language)} {str(e)}")
                status.update(label=get_text("ui", "error_status", st.session_state.language), state="error")
                if st.button(get_text("ui", "close_btn", st.session_state.language)):
                        st.rerun()
    
    elif phase == "results":
        results = st.session_state.generation_results
        st.subheader(get_text("ui", "results_title", st.session_state.language))
        
        candidate_name = get_text("ui", "history_unknown", st.session_state.language)
        if results.get("cv_json"):
            try:
                filename = os.path.basename(results["cv_json"])
                parts = filename.split('_')
                if len(parts) >= 3: candidate_name = f"{parts[1]} {parts[2]}"
            except: pass
        
        model_used = results.get("model_name", os.environ.get("MODEL_NAME", "gpt-4o-mini"))
        st.caption(f"{get_text('ui', 'history_mode', st.session_state.language)}: {results.get('mode', get_text('ui', 'history_unknown', st.session_state.language))} | {get_text('ui', 'history_model', st.session_state.language)}: {model_used}")
            
        cv_btn_label = f"{get_text('ui', 'word_cv_btn', st.session_state.language)} - {candidate_name}"
        if len(cv_btn_label) > 30:
            cv_btn_label = cv_btn_label[:27] + "..."
        
        with st.success(get_text("ui", "downloads_title", st.session_state.language), icon="📥"):
            res_col1, res_col2, res_col3 = st.columns(3)
            with res_col1:
                if results.get("word_path") and os.path.exists(results["word_path"]):
                    with open(results["word_path"], "rb") as f:
                        st.download_button(cv_btn_label, f, os.path.basename(results["word_path"]), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
            with res_col2:
                if results.get("cv_json") and os.path.exists(results["cv_json"]):
                    with open(results["cv_json"], "rb") as f:
                        st.download_button(get_text("ui", "json_data_btn", st.session_state.language), f, os.path.basename(results["cv_json"]), "application/json", use_container_width=True)
            with res_col3:
                if results.get("dashboard_path") and os.path.exists(results["dashboard_path"]):
                    with open(results["dashboard_path"], "rb") as f:
                        st.download_button(get_text("ui", "dashboard_btn", st.session_state.language), f, os.path.basename(results["dashboard_path"]), "text/html", use_container_width=True)

        if not results.get("stellenprofil_json") and results.get("cv_json"):
            output_dir = os.path.dirname(results["cv_json"])
            try:
                for f in os.listdir(output_dir):
                    if f.startswith("stellenprofil_") and f.endswith(".json"):
                        results["stellenprofil_json"] = os.path.join(output_dir, f)
                        break
            except: pass

        if not results.get("match_json") and results.get("cv_json"):
            output_dir = os.path.dirname(results["cv_json"])
            try:
                for f in os.listdir(output_dir):
                    if f.startswith("Match_") and f.endswith(".json"):
                        results["match_json"] = os.path.join(output_dir, f)
                        break
            except: pass

        if results.get("stellenprofil_json") and os.path.exists(results["stellenprofil_json"]):
            st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
            
            offer_word_path = results.get("offer_word_path")
            is_offer_ready = offer_word_path and os.path.exists(offer_word_path)
            
            if is_offer_ready:
                offer_container = st.success(get_text("ui", "offer_ready", st.session_state.language), icon="✅")
            else:
                offer_container = st.info(get_text("ui", "offer_create_title", st.session_state.language), icon="✨")
            
            with offer_container:
                off_col1, off_col2, off_col3 = st.columns(3)
                with off_col1:
                    if is_offer_ready:
                         with open(offer_word_path, "rb") as f:
                            st.download_button(get_text("ui", "offer_download_btn", st.session_state.language), f, os.path.basename(offer_word_path), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True, type="primary")
                    else:
                        off_btn_key = f"gen_offer_btn_{results.get('cv_json', '')}"
                        if st.button(get_text("ui", "offer_create_btn", st.session_state.language), use_container_width=True, key=off_btn_key):
                            with st.status(get_text("ui", "status_offer", st.session_state.language), expanded=True) as status:
                                try:
                                    cv_json = results["cv_json"]
                                    stellenprofil_json = results["stellenprofil_json"]
                                    match_json = results.get("match_json")
                                    output_dir = os.path.dirname(cv_json)
                                    base_name = os.path.basename(cv_json).replace("cv_", "").replace(".json", "")
                                    angebot_json_path = os.path.join(output_dir, f"Angebot_{base_name}.json")
                                    angebot_word_path = os.path.join(output_dir, f"Angebot_{base_name}.docx")
                                    schema_path = os.path.join(os.getcwd(), "scripts", "angebot_json_schema.json")
                                    
                                    status.write("🧠 KI-Inhalte generieren...")
                                    generate_angebot_json(cv_json, stellenprofil_json, match_json, angebot_json_path, schema_path, language=st.session_state.language)
                                    
                                    status.write("📝 Word-Dokument formatieren...")
                                    generate_angebot_word(angebot_json_path, angebot_word_path)
                                    
                                    if os.path.exists(angebot_word_path):
                                        results["offer_word_path"] = angebot_word_path
                                        st.session_state.generation_results = results
                                        st.session_state.show_pipeline_dialog = True
                                        st.session_state.show_results_view = True
                                        status.update(label=get_text('ui', 'offer_ready_label', st.session_state.language), state="complete", expanded=False)
                                        st.success(get_text('ui', 'offer_success', st.session_state.language))
                                        st.rerun()
                                    else:
                                        st.error(get_text('ui', 'file_not_found_on_disk', st.session_state.language))
                                except Exception as e:
                                    status.update(label=get_text('ui', 'error_label', st.session_state.language), state="error")
                                    st.error(f"{get_text('ui', 'offer_error', st.session_state.language)} {e}")
                                    import traceback
                                    st.code(traceback.format_exc())
                with off_col2:
                    if not is_offer_ready:
                        st.caption(get_text('ui', 'offer_button_caption', st.session_state.language))
                    else:
                        st.caption(get_text('ui', 'offer_ready_caption', st.session_state.language))

        st.markdown("<div style='margin-top: 40px; margin-bottom: 20px; border-top: 1px solid #ddd;'></div>", unsafe_allow_html=True)

        if results.get("dashboard_path") and os.path.exists(results["dashboard_path"]):
            with open(results["dashboard_path"], "r", encoding='utf-8') as f:
                html_content = f.read()
                st.components.v1.html(html_content, height=1200, scrolling=True)
                
        if st.button(get_text("ui", "close_btn", st.session_state.language), use_container_width=True):
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
