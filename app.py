import streamlit as st
import os
import json
import yaml
import sys
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from datetime import datetime
from dotenv import load_dotenv
from scripts.streamlit_pipeline import StreamlitCVGenerator
from scripts.generate_angebot import generate_angebot_json
from scripts.generate_angebot_word import generate_angebot_word
from scripts.batch_comparison import run_batch_comparison
from scripts.batch_results_display import (
    display_batch_results,
    get_batch_output_dir,
    move_candidate_files_to_batch
)

# Page config must be the first Streamlit command
st.set_page_config(
    page_title="CV Generator",
    page_icon="templates/logo.png",
    layout="wide"
)

# Initialize session state variables
if 'language' not in st.session_state:
    st.session_state.language = "de"

# --- Helper Functions ---
def load_translations():
    """Loads translations from the central JSON file."""
    # Try different paths to be more robust
    paths = [
        os.path.join(os.path.dirname(__file__), "scripts", "translations.json"),
        os.path.join("scripts", "translations.json"),
        "translations.json"
    ]
    
    for trans_path in paths:
        if os.path.exists(trans_path):
            try:
                with open(trans_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading translations from {trans_path}: {e}")
                continue
    
    # Fallback empty structure
    print("❌ Critical: Could not find or load translations.json anywhere!")
    return {"ui": {}, "cv": {}, "offer": {}}

# Global translations object for easier access
translations = load_translations()

def get_text(section, key, lang="de"):
    """Safely retrieves translated text from the global translations object."""
    try:
        return translations.get(section, {}).get(key, {}).get(lang, key)
    except:
        return key

def reset_all_pipeline_states():
    """Resets all session state variables related to the pipeline dialog/view."""
    st.session_state.show_pipeline_dialog = False
    st.session_state.show_results_view = False
    if "current_generation_results" in st.session_state:
        del st.session_state.current_generation_results
    # Note: we don't necessarily want to delete st.session_state.generation_results 
    # as that's used for the background 'ERGEBNISSE' view if needed.

@st.dialog(get_text('ui', 'dialog_model_overview', st.session_state.language), width="large")
def show_model_info_dialog():
    st.markdown(get_text('ui', 'model_overview_markdown', st.session_state.language))

def get_git_history(limit=10):
    """Fetches the recent git commit history with detailed body."""
    commits = []
    try:
        import subprocess
        # Get commit hash, date, author, subject, and body
        # Format: %h|%cd|%an|%s|%b
        # %b is the body of the commit message
        # Using --date=format:"%Y-%m-%d %H:%M:%S" for full timestamp
        cmd = ["git", "log", "-n", str(limit), "--pretty=format:COMMIT_START%h|%cd|%an|%s|%bCOMMIT_END", "--date=format:%Y-%m-%d %H:%M:%S"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8')
        
        raw_commits = result.stdout.split("COMMIT_START")
        for raw in raw_commits:
            if not raw.strip():
                continue
            
            content = raw.replace("COMMIT_END", "").strip()
            parts = content.split("|", 4)
            if len(parts) >= 4:
                commits.append({
                    "hash": parts[0],
                    "date": parts[1],
                    "author": parts[2],
                    "message": parts[3],
                    "body": parts[4] if len(parts) > 4 else ""
                })
        return commits
    except Exception as e:
        return [{"hash": "-", "date": "-", "author": "System", "message": f"Konnte Git-History nicht laden: {str(e)}", "body": ""}]

@st.dialog(get_text('ui', 'dialog_app_info', st.session_state.language), width="large")
def show_app_info_dialog():
    language = st.session_state.language
    st.markdown(f"""
    {get_text("ui", "app_info_title", language)}
    
    {get_text("ui", "app_info_name", language)}
    
    {get_text("ui", "app_info_main_desc", language)}
    
    {get_text("ui", "app_info_features_title", language)}
    {get_text("ui", "app_info_feature1", language)}
    {get_text("ui", "app_info_feature2", language)}
    {get_text("ui", "app_info_feature3", language)}
    {get_text("ui", "app_info_feature4", language)}
    
    ---
    """)
    
    st.subheader(get_text("ui", "changelog_title", language))
    
    commits = get_git_history(20)
    
    relevant_types = {
        "feat": get_text("commit_types", "feat", language),
        "feature": get_text("commit_types", "feature", language),
        "fix": get_text("commit_types", "fix", language),
        "ui": get_text("commit_types", "ui", language),
        "perf": get_text("commit_types", "perf", language),
        "docs": get_text("commit_types", "docs", language),
        "refactor": get_text("commit_types", "refactor", language),
        "chore": get_text("commit_types", "chore", language)
    }
    
    visible_count = 0
    for commit in commits:
        msg = commit['message']
        category = get_text("ui", "changelog_general", language)
        clean_msg = msg
        is_relevant = False
        
        # Parse Conventional Commits
        if ":" in msg:
            parts = msg.split(":", 1)
            type_scope = parts[0].lower()
            # Handle scopes like feat(ui):
            if "(" in type_scope:
                type_key = type_scope.split("(")[0]
            else:
                type_key = type_scope.strip()
            
            if type_key in relevant_types:
                category = relevant_types[type_key]
                clean_msg = parts[1].strip().replace("{", "&#123;").replace("}", "&#125;")
                is_relevant = True
        else:
            # Show non-conventional commits as general, unless they look like merges
            if not msg.startswith("Merge"):
                clean_msg = msg.replace("{", "&#123;").replace("}", "&#125;")
                is_relevant = True

        if is_relevant:
            visible_count += 1
            
            # Use st.expander for detailed view
            with st.expander(f"{commit['date']} | {category} | {clean_msg}"):
                st.markdown(f"**Commit Hash:** `{commit['hash']}`")
                st.markdown(f"**Autor:** {commit['author']}")
                
                if commit.get('body'):
                    st.markdown("**Details:**")
                    # Clean up body (remove leading/trailing whitespace and handle markdown)
                    body = commit['body'].strip()
                    if body:
                        # Convert common markers or newlines in commit body for better display
                        st.markdown(body)
                    else:
                        st.caption("Keine weiteren Details vorhanden.")
                elif "localization" in clean_msg.lower() or "language selectors" in clean_msg.lower():
                    # Fallback for the multi-language update
                    st.markdown("**Details des Commits:**")
                    st.info("• Vollständige Internationalisierung (DE, EN, FR)\n• Umzug aller UI-Texte in zentrale `translations.json`\n• Integration Sprach-Steuerung in Word-Generierung (Lebenslauf & Angebot)\n• Fix: Streamlit Absturz bei App-Initialisierung\n• Sprachumschalter DE/EN/FR in der Sidebar")
                elif "harmonize status values" in clean_msg.lower():
                    # Fallback for the current complex commit if body is empty but info is in title
                    st.markdown("**Details des Commits:**")
                    st.info("• Vereinheitlichung der Statuswerte (✅, ⚠️, ❌)\n• Update Kriterien-Matrix Layout\n• Refactoring Dokument-Styling\n• Anpassung Brief-Formatierung")
                else:
                    st.markdown("**Details:**")
                    st.caption("Keine weiteren Details vorhanden.")
                    st.caption("Keine weiteren Details vorhanden.")
            
    if visible_count == 0:
        st.caption("Keine relevanten Änderungen in den letzten Commits gefunden.")

# --- Custom CSS for Corporate Identity ---
# Initial CSS (will be overwritten by sidebar selection)
st.markdown("""
    <style>
    /* Default styles */
    </style>
""", unsafe_allow_html=True)

# Load environment variables (for local dev)
load_dotenv()

# --- Authentication ---
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Center the login form
col1, col2, col3 = st.columns([3, 2, 3])
with col2:
    authenticator.login('main')

    if st.session_state["authentication_status"] is False:
        st.error(get_text("ui", "auth_error", st.session_state.language))
        st.info(get_text("ui", "auth_forgot", st.session_state.language))
        st.stop()
    elif st.session_state["authentication_status"] is None:
        st.warning(get_text("ui", "auth_missing", st.session_state.language))
        st.stop()

# If we get here, the user is authenticated
name = st.session_state["name"]
username = st.session_state["username"]

# --- Sidebar ---
with st.sidebar:
    # Logo (Top Left)
    if os.path.exists("templates/logo.png"):
        st.image("templates/logo.png", use_container_width=True)

    
    st.divider()

# --- History Management ---
HISTORY_FILE = os.path.join("output", "run_history.json")

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_to_history(entry):
    history = load_history()
    # Add new entry at the beginning
    history.insert(0, entry)
    # Keep only last 50 entries
    history = history[:50]
    
    os.makedirs("output", exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def get_api_key():
    """
    Retrieves the OpenAI API Key from secrets (Cloud), environment variables (Local),
    or user input.
    """
    # 1. Try Streamlit Secrets (Cloud)
    try:
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except FileNotFoundError:
        # Local run without secrets.toml
        pass
    except Exception:
        # Other errors accessing secrets
        pass
    
    # 2. Try Environment Variable (Local .env)
    env_key = os.getenv("OPENAI_API_KEY")
    if env_key:
        return env_key
    
    # 3. Fallback: User Input in Session State
    if "api_key" in st.session_state:
        return st.session_state.api_key
    
    return None

# --- Sidebar Settings ---
with st.sidebar:
    # Language Selector (Buttons)
    st.write(f"**{get_text('ui', 'language_label', st.session_state.language)}:**")
    lang_cols = st.columns(3)
    
    # Simple logic to handle language buttons
    if lang_cols[0].button("DE", use_container_width=True, 
                           type="primary" if st.session_state.language == "de" else "secondary"):
        st.session_state.language = "de"
        st.rerun()
        
    if lang_cols[1].button("EN", use_container_width=True,
                           type="primary" if st.session_state.language == "en" else "secondary"):
        st.session_state.language = "en"
        st.rerun()
        
    if lang_cols[2].button("FR", use_container_width=True,
                           type="primary" if st.session_state.language == "fr" else "secondary"):
        st.session_state.language = "fr"
        st.rerun()
    
    st.divider()
    
    st.title(get_text( "ui", "sidebar_title", st.session_state.language))
    
    # Placeholder for logo at the top
    logo_placeholder = st.empty()
    
    # --- Settings Menu ---
    with st.expander(get_text( "ui", "personal_settings", st.session_state.language), expanded=False):
        try:
            if authenticator.reset_password(username, 'main'):
                st.success(get_text("ui", "password_changed", st.session_state.language))
                with open('config.yaml', 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)
        except Exception as e:
            st.error(e)

    with st.expander(get_text( "ui", "design_settings", st.session_state.language), expanded=False):
        st.caption(get_text( "ui", "design_desc", st.session_state.language))
        
        # Default values from styles.json (Orange #FF7900)
        primary_color = st.color_picker(get_text( "ui", "primary_color", st.session_state.language), "#FF7900")
        secondary_color = st.color_picker(get_text( "ui", "secondary_color", st.session_state.language), "#444444")
        
        # Font Selection
        font_options = ["Aptos", "Arial", "Calibri", "Helvetica", "Times New Roman"]
        selected_font = st.selectbox(get_text( "ui", "font_label", st.session_state.language), font_options, index=0)
        
        # Logo Upload
        uploaded_logo = st.file_uploader(get_text( "ui", "logo_label", st.session_state.language), type=["png", "jpg", "jpeg"])
        if uploaded_logo:
            # Save logo temporarily for processing
            os.makedirs("input/logos", exist_ok=True)
            logo_path = os.path.join("input", "logos", "custom_logo.png")
            with open(logo_path, "wb") as f:
                f.write(uploaded_logo.getbuffer())
            
            # Store path in session state
            st.session_state.custom_logo_path = logo_path
            
            # Display Logo in Sidebar (Top) - using the placeholder created earlier
            logo_placeholder.image(uploaded_logo, use_container_width=True)
        
        # Apply CSS dynamically based on user selection
        st.markdown(f"""
            <style>
            /* Import Fonts if needed (Google Fonts example) */
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
            
            /* Apply Font Globally */
            html, body, [class*="css"] {{
                font-family: '{selected_font}', sans-serif !important;
            }}
            
            /* Headings */
            h1 {{ color: {primary_color} !important; font-family: '{selected_font}', sans-serif !important; }}
            h2, h3 {{ color: {secondary_color} !important; font-family: '{selected_font}', sans-serif !important; }}
            
            /* Buttons */
            .stButton>button {{
                background-color: {primary_color} !important;
                color: white !important;
                border: none;
                font-family: '{selected_font}', sans-serif !important;
                transition: all 0.3s ease;
            }}
            
            /* Disabled Button Styling */
            .stButton>button:disabled {{
                background-color: #cccccc !important;
                color: #666666 !important;
                cursor: not-allowed;
                opacity: 0.6;
                box-shadow: none !important;
                transform: none !important;
            }}
            
            /* Button Hover Effect */
            .stButton>button:hover {{
                opacity: 0.85;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
            
            /* Secondary Buttons (Inactive Modes) */
            button[kind="secondary"] {{
                background-color: #f0f2f6 !important;
                color: {secondary_color} !important;
                border: 1px solid #ddd !important;
            }}
            button[kind="secondary"]:hover {{
                background-color: #e0e2e6 !important;
                border-color: {primary_color} !important;
                color: {primary_color} !important;
            }}
            
            /* Sidebar Background (Optional: Light tint of primary color) */
            [data-testid="stSidebar"] {{
                background-color: #f8f9fa;
                border-right: 1px solid #ddd;
            }}

            /* Translate the "Drag and drop file here" text for st.file_uploader */
            [data-testid="stFileUploader"] section > button + div {{
                display: none;
            }}
            [data-testid="stFileUploader"] section::after {{
                content: "{get_text("ui", "uploader_drag_drop", st.session_state.language)}";
                display: block;
                color: #444;
                margin-top: 10px;
            }}
            </style>
        """, unsafe_allow_html=True)
        
        # Update styles.json in session state (conceptually) or pass to pipeline
        # For now, we store these in session_state to pass to the generator later
        st.session_state.custom_styles = {
            "primary_color": primary_color,
            "secondary_color": secondary_color,
            "font": selected_font
        }
    
    # --- Model Settings ---
    with st.expander(get_text( "ui", "model_settings", st.session_state.language), expanded=False):
        model_options = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "mock"]
        
        # Model Info Dictionary
        model_details = {
            "gpt-4o-mini": {"cost": "~$0.01", "rec": "✅ Empfohlen"},
            "gpt-4o": {"cost": "~$0.15", "rec": "💎 High-End"},
            "gpt-3.5-turbo": {"cost": "~$0.005", "rec": "⚠️ Legacy"},
            "mock": {"cost": "0.00", "rec": "🧪 Test"}
        }

        col_sel, col_info = st.columns([0.85, 0.15])
        with col_sel:
            selected_model = st.selectbox(
                get_text( "ui", "select_model", st.session_state.language),
                options=model_options,
                index=0,
                key="model_selection_sidebar",
                format_func=lambda x: f"{x} ({model_details.get(x, {}).get('rec', '')})",
                on_change=reset_all_pipeline_states
            )
        with col_info:
            st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
            if st.button("ℹ️", key="model_info_btn", help=get_text( "ui", "model_info_btn_help", st.session_state.language)):
                show_model_info_dialog()

        # Display Cost Info
        details = model_details.get(selected_model, {})
        st.caption(f"💰 Kosten: **{details.get('cost')}** / Lauf | {details.get('rec')}")

        # Set model in env for the pipeline to pick up
        os.environ["MODEL_NAME"] = selected_model
        
        if selected_model == "mock":
            st.info("🧪 Test-Modus aktiv: Es werden keine echten API-Calls gemacht.")
        
        st.caption(f"Aktueller Modus: {os.getenv('CV_GENERATOR_MODE', 'full')}")

        # API Key Handling (Admin only)
        if username == 'admin':
            st.divider()
            api_key = get_api_key()
            if not api_key:
                st.warning("Kein API Key gefunden!")
                user_key = st.text_input("OpenAI API Key eingeben:", type="password")
                if user_key:
                    st.session_state.api_key = user_key
                    st.rerun()
            else:
                st.success(get_text("ui", "api_key_active", st.session_state.language))
                # Only show change button if key is not from environment
                if not os.getenv("OPENAI_API_KEY") and "OPENAI_API_KEY" not in st.secrets:
                    if st.button(get_text("ui", "change_api_key", st.session_state.language)):
                        if "api_key" in st.session_state:
                            del st.session_state.api_key
                        st.rerun()
        
        st.caption(f"{get_text('ui', 'current_mode', st.session_state.language)}: {os.getenv('CV_GENERATOR_MODE', 'full')}")

    # --- Application Info ---
    with st.expander(get_text("ui", "app_info", st.session_state.language), expanded=False):
        st.caption(get_text("ui", "app_info_desc", st.session_state.language))
        if st.button(get_text("ui", "show_details", st.session_state.language), use_container_width=True):
            show_app_info_dialog()

    st.divider()
    
    # --- History Section ---
    with st.expander(get_text("ui", "history_tab", st.session_state.language), expanded=False):
        history = load_history()
        
        if not history:
            st.caption(get_text("ui", "history_empty", st.session_state.language))
        else:
            for i, item in enumerate(history):
                timestamp = item.get("timestamp", "")
                # Format timestamp nicely if possible (YYYYMMDD_HHMMSS -> DD.MM.YYYY HH:MM)
                try:
                    dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    display_time = dt.strftime("%d.%m. %H:%M")
                except:
                    display_time = timestamp

                candidate_name = item.get("candidate_name", get_text( "ui", "history_unknown", st.session_state.language))

                with st.expander(f"{display_time} - {candidate_name}", expanded=False):
                    model_used = item.get("model_name", get_text( "ui", "history_unknown", st.session_state.language))
                    is_batch = item.get("is_batch", False)
                    batch_folder = item.get("batch_folder", "")
                    
                    st.caption(f"Modus: {item.get('mode')} | Modell: {model_used}")
                    
                    # Show batch folder if applicable
                    if is_batch and batch_folder:
                        st.caption(f"📂 Batch Folder: `{batch_folder}`")

                    # 1. Visual Score Bar
                    score = item.get("match_score")
                    if score:
                        try:
                            score_val = float(score)
                            # Thresholds matching visualize_results.py
                            if score_val >= 80:
                                bar_color = "#27ae60" # Green
                            elif score_val >= 60:
                                bar_color = "#f39c12" # Orange
                            else:
                                bar_color = "#c0392b" # Red

                            st.markdown(f"""
                                <div style="margin-bottom: 5px; font-size: 0.8em; color: #666;">{get_text( 'dashboard', 'matching_score', st.session_state.language)}: {score}%</div>
                                <div style="background-color: #eee; border-radius: 4px; height: 8px; width: 100%; margin-bottom: 15px;">
                                    <div style="background-color: {bar_color}; width: {score_val}%; height: 100%; border-radius: 4px;"></div>
                                </div>
                            """, unsafe_allow_html=True)
                        except:
                            pass

                    # 2. Action Buttons
                    if st.button(get_text( 'ui', 'history_details_btn', st.session_state.language), key=f"hist_btn_{timestamp}_{i}", use_container_width=True):
                        st.session_state.generation_results = item
                        st.session_state.show_pipeline_dialog = True
                        st.session_state.show_results_view = True
                        st.rerun()
    
    # Spacer to push content to bottom
    st.markdown("<div style='flex-grow: 1;'></div>", unsafe_allow_html=True)
    
    st.divider()
    
    # --- User Info & Logout (Bottom) ---
    st.write(f'{get_text( "ui", "welcome_msg", st.session_state.language)} *{name}*')
    authenticator.logout(get_text( "ui", "logout_btn", st.session_state.language), 'sidebar')

# --- Main Content ---
st.title(get_text( "ui", "app_title", st.session_state.language))
st.markdown(get_text( "ui", "app_subtitle", st.session_state.language))

# Mode Selection with Cards
st.subheader(get_text( "ui", "mode_select_title", st.session_state.language))

col_m1, col_m2, col_m3, col_m4 = st.columns(4)

# Helper to style cards
def card_style(selected):
    border = f"2px solid {primary_color}" if selected else "1px solid #ddd"
    bg = f"{primary_color}10" if selected else "#fff" # 10% opacity
    return f"""
        border: {border};
        background-color: {bg};
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        height: 100%;
        cursor: pointer;
    """

# Initialize mode in session state if not present
if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = "Full (CV + Stellenprofil + Match + Feedback)"

# Create clickable columns (using buttons as proxies for cards)
with col_m1:
    if st.button(get_text( "ui", "mode_basic", st.session_state.language), use_container_width=True, type="primary" if st.session_state.selected_mode.startswith("Basic") else "secondary"):
        st.session_state.selected_mode = "Basic (Nur CV)"
        # Reset pipeline state
        st.session_state.show_pipeline_dialog = False
        st.session_state.show_results_view = False
        st.rerun()
    st.caption(get_text( "ui", "mode_basic_desc", st.session_state.language))

with col_m2:
    if st.button(get_text( "ui", "mode_analysis", st.session_state.language), use_container_width=True, type="primary" if st.session_state.selected_mode.startswith("Analysis") else "secondary"):
        st.session_state.selected_mode = "Analysis (CV + Stellenprofil)"
        # Reset pipeline state
        st.session_state.show_pipeline_dialog = False
        st.session_state.show_results_view = False
        st.rerun()
    st.caption(get_text( "ui", "mode_analysis_desc", st.session_state.language))

with col_m3:
    if st.button(get_text( "ui", "mode_full", st.session_state.language), use_container_width=True, type="primary" if st.session_state.selected_mode.startswith("Full") else "secondary"):
        st.session_state.selected_mode = "Full (CV + Stellenprofil + Match + Feedback)"
        # Reset pipeline state
        st.session_state.show_pipeline_dialog = False
        st.session_state.show_results_view = False
        st.rerun()
    st.caption(get_text( "ui", "mode_full_desc", st.session_state.language))

with col_m4:
    if st.button(get_text( "ui", "mode_batch", st.session_state.language), use_container_width=True, type="primary" if st.session_state.selected_mode.startswith("Batch") else "secondary"):
        st.session_state.selected_mode = "Batch (Mehrere CVs + Stellenprofil)"
        # Reset pipeline state
        st.session_state.show_pipeline_dialog = False
        st.session_state.show_results_view = False
        st.rerun()
    st.caption(get_text( "ui", "mode_batch_desc", st.session_state.language))

mode = st.session_state.selected_mode
st.divider()

# Test Mode Button (specifically for Batch)
if mode.startswith("Batch"):
    test_mode_col, _ = st.columns([1, 4])
    with test_mode_col:
        if st.button("🧪 Test Mode (Batch)", use_container_width=True):
            # Set mock mode and populate test data
            os.environ["MODEL_NAME"] = "mock"
            # Pre-select mock files
            if "batch_cv_files" not in st.session_state or not st.session_state.batch_cv_files:
                st.session_state.batch_cv_files = ["mock_cv_1.pdf", "mock_cv_2.pdf", "mock_cv_3.pdf"]
            if "shared_job_file" not in st.session_state or not st.session_state.shared_job_file:
                st.session_state.shared_job_file = "mock_job_profile.pdf"
            st.success("✅ Test Mode activated with mock batch data")
            st.info("📌 Mock data: 3 CVs, 1 job profile - ready to process")
            st.rerun()
    st.divider()

# Check for Mock Mode
is_mock = os.environ.get("MODEL_NAME") == "mock"

# Helper function for custom upload UI
def render_custom_uploader(label, key_prefix, file_type=["pdf"]):
    # Use shared session state keys for CV and Job Profile to persist across mode switches
    if "cv" in key_prefix.lower():
        file_state_key = "shared_cv_file"
    elif "job" in key_prefix.lower():
        file_state_key = "shared_job_file"
    else:
        file_state_key = f"{key_prefix}_file"
    
    # Initialize state if needed
    if file_state_key not in st.session_state:
        st.session_state[file_state_key] = None
    
    # Title is ALWAYS visible
    st.subheader(label)
    
    # We use a stable widget key based on the key_prefix
    widget_key = f"{key_prefix}_widget"
    
    # Native Streamlit uploader is the most reliable for drag-and-drop
    uploaded_file = st.file_uploader(
        label, 
        type=file_type, 
        key=widget_key, 
        label_visibility="collapsed"
    )
    
    # Sync uploader state to session state
    if uploaded_file:
        # Check if it's a NEW file upload (compare name and size for stability)
        prev_file = st.session_state.get(file_state_key)
        is_new_file = False
        if prev_file is None:
            is_new_file = True
        elif uploaded_file.name != prev_file.name or uploaded_file.size != prev_file.size:
            is_new_file = True

        if is_new_file:
            st.session_state[file_state_key] = uploaded_file
            # Reset pipeline and results when a new file is uploaded
            # This prevents the dashboard from reappearing when changing files
            if "generation_results" in st.session_state:
                del st.session_state.generation_results
            if "current_generation_results" in st.session_state:
                del st.session_state.current_generation_results
            st.session_state.show_pipeline_dialog = False
            st.session_state.show_results_view = False
        else:
            # Keep the existing file object (to maintain ID stability)
            pass
    elif st.session_state[file_state_key] is not None:
        # If the widget is empty but we have something in session state,
        # the user intentionally removed the file.
        st.session_state[file_state_key] = None
        # Also reset pipeline states when a file is removed
        st.session_state.show_pipeline_dialog = False
        st.session_state.show_results_view = False
        if "generation_results" in st.session_state:
            del st.session_state.generation_results

    # Visual Feedback (Success State)
    current_file = st.session_state[file_state_key]
    if current_file:
        st.markdown(f"""
            <div style="background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 10px 15px; border-radius: 5px; margin-top: -10px; margin-bottom: 10px;">
                <strong>{get_text( "ui", "file_active", st.session_state.language)}</strong> {current_file.name}
            </div>
        """, unsafe_allow_html=True)
                
    return current_file

def render_batch_cv_uploader(label, key_prefix):
    """Upload multiple CV files for batch comparison mode."""
    file_state_key = "batch_cv_files"
    
    # Initialize state if needed
    if file_state_key not in st.session_state:
        st.session_state[file_state_key] = []
    
    # Title is ALWAYS visible
    st.subheader(label)
    st.caption(get_text("ui", "batch_upload_hint", st.session_state.language))
    
    # Native Streamlit uploader for multiple files
    widget_key = f"{key_prefix}_widget"
    uploaded_files = st.file_uploader(
        label,
        type=["pdf"],
        key=widget_key,
        label_visibility="collapsed",
        accept_multiple_files=True
    )
    
    # Sync uploader state to session state
    if uploaded_files:
        # Check for new or changed files
        new_files = []
        for uploaded_file in uploaded_files:
            is_new = True
            for existing in st.session_state[file_state_key]:
                if uploaded_file.name == existing.name and uploaded_file.size == existing.size:
                    is_new = False
                    break
            if is_new:
                new_files.append(uploaded_file)
        
        if new_files:
            st.session_state[file_state_key] = uploaded_files
            # Reset pipeline and results when files change
            if "generation_results" in st.session_state:
                del st.session_state.generation_results
            if "current_generation_results" in st.session_state:
                del st.session_state.current_generation_results
            st.session_state.show_pipeline_dialog = False
            st.session_state.show_results_view = False
    else:
        # If the widget is empty but we have files in session state, user removed them
        if st.session_state[file_state_key]:
            st.session_state[file_state_key] = []
            st.session_state.show_pipeline_dialog = False
            st.session_state.show_results_view = False
            if "generation_results" in st.session_state:
                del st.session_state.generation_results

    # Visual Feedback (Success State)
    current_files = st.session_state[file_state_key]
    if current_files:
        st.markdown(f"""
            <div style="background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 10px 15px; border-radius: 5px; margin-top: -10px; margin-bottom: 10px;">
                <strong>{get_text("ui", "files_active", st.session_state.language)}</strong> {len(current_files)} {get_text("ui", "cvs_selected", st.session_state.language)}
            </div>
        """, unsafe_allow_html=True)
        with st.expander(get_text("ui", "view_files", st.session_state.language)):
            for i, file in enumerate(current_files, 1):
                st.write(f"{i}. {file.name}")
                
    return current_files

# Dynamic Columns based on Mode
if mode.startswith("Basic"):
    # Left-aligned column for CV upload (using same ratio as Full mode)
    col1, col2 = st.columns(2)
    with col1:
        if is_mock:
            st.subheader(get_text( "ui", "cv_title", st.session_state.language))
            st.success(get_text( "ui", "test_mode_active", st.session_state.language))
            st.caption(get_text( "ui", "test_mode_desc", st.session_state.language))
            cv_file = None
        else:
            cv_file = render_custom_uploader(get_text( "ui", "cv_title", st.session_state.language), "cv_basic")
        job_file = None # No job file in Basic mode
    cv_files = []  # Initialize for consistency
elif mode.startswith("Batch"):
    # Batch mode: Multiple CVs + Job Profile
    col1, col2 = st.columns(2)

    with col1:
        if is_mock:
            st.subheader(get_text( "ui", "cv_title", st.session_state.language))
            st.success(get_text( "ui", "test_mode_active", st.session_state.language))
            st.caption(get_text( "ui", "test_mode_desc", st.session_state.language))
            cv_files = []
        else:
            cv_files = render_batch_cv_uploader(get_text( "ui", "cv_batch_title", st.session_state.language), "cv_batch")

    with col2:
        if is_mock:
            st.subheader(get_text( "ui", "job_title", st.session_state.language))
            st.success(get_text( "ui", "test_mode_active", st.session_state.language))
            st.caption(get_text( "ui", "test_mode_desc", st.session_state.language))
            job_file = None
        else:
            job_file = render_custom_uploader(get_text( "ui", "job_title", st.session_state.language), "job_batch")
    
    # For batch mode, we'll handle cv_files differently below
    cv_file = None
else:
    # Two columns for CV and Job Profile (Analysis and Full modes)
    col1, col2 = st.columns(2)

    with col1:
        if is_mock:
            st.subheader(get_text( "ui", "cv_title", st.session_state.language))
            st.success(get_text( "ui", "test_mode_active", st.session_state.language))
            st.caption(get_text( "ui", "test_mode_desc", st.session_state.language))
            cv_file = None
        else:
            cv_file = render_custom_uploader(get_text( "ui", "cv_title", st.session_state.language), "cv_full")

    with col2:
        if is_mock:
            st.subheader(get_text( "ui", "job_title", st.session_state.language))
            st.success(get_text( "ui", "test_mode_active", st.session_state.language))
            st.caption(get_text( "ui", "test_mode_desc", st.session_state.language))
            job_file = None
        else:
            job_file = render_custom_uploader(get_text( "ui", "job_title", st.session_state.language), "job_full")
    
    cv_files = []  # Initialize for consistency

st.divider()

# DSGVO / Privacy Notice
st.markdown(f"### {get_text( 'ui', 'privacy_title', st.session_state.language)}")
st.caption(get_text( 'ui', 'privacy_desc', st.session_state.language))
dsgvo_accepted = st.checkbox(get_text( 'ui', 'privacy_accept', st.session_state.language), value=False)

# Action Button
is_mock = os.environ.get("MODEL_NAME") == "mock"

if is_mock:
    # In Mock mode, we don't need files or API key
    start_disabled = False
    # Use dummy files if not uploaded
    if mode.startswith("Batch"):
        if not cv_files: cv_files = ["MOCK_CV1.pdf", "MOCK_CV2.pdf"]
    else:
        if not cv_file: cv_file = "MOCK_CV.pdf"
    if not job_file and mode != "Basic (Nur CV)": job_file = "MOCK_JOB.pdf"
    # Use dummy key if not present (to satisfy checks)
    if not api_key: api_key = "mock-key"
else:
    if mode.startswith("Batch"):
        # Batch mode: need multiple CVs, job file, and acceptance
        start_disabled = not cv_files or not job_file or not api_key or not dsgvo_accepted
    else:
        # Single CV modes
        start_disabled = not cv_file or not api_key or not dsgvo_accepted

@st.dialog(get_text('ui', 'dialog_pipeline', st.session_state.language), width="large")
def run_cv_pipeline_dialog(cv_file, job_file, api_key, mode, custom_styles, custom_logo_path):
    
    # Determine Phase: 'processing' or 'results'
    # If loading from history (generation_results + show_results_view), go directly to results
    is_history_load = "generation_results" in st.session_state and st.session_state.get("show_results_view")
    
    if is_history_load:
        phase = "results"
    else:
        phase = "processing"

    # Custom CSS to adjust dialog width and height based on phase
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
        # Processing phase - narrower width
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
                # Prepare inputs
                current_custom_styles = {
                    "primary_color": primary_color,
                    "secondary_color": secondary_color,
                    "font": selected_font
                }
                current_custom_logo_path = st.session_state.get("custom_logo_path")
                
                # Check Cache
                if "current_generation_results" in st.session_state:
                    results = st.session_state.current_generation_results
                else:
                    # Determine if batch mode or single CV
                    is_batch = mode.startswith("Batch")
                    
                    if is_batch:
                        # Batch Mode: Process multiple CVs
                        log_container.write(f"🔄 Processing {len(cv_file)} CVs...")
                        batch_response = run_batch_comparison(
                            cv_files=cv_file,
                            job_file=job_file,
                            api_key=api_key,
                            custom_styles=current_custom_styles,
                            custom_logo_path=current_custom_logo_path,
                            pipeline_mode=mode,
                            language=st.session_state.language,
                            progress_callback=progress_callback
                        )
                        
                        # Extract batch results and metadata
                        batch_results = batch_response.get("results", [])
                        batch_folder = batch_response.get("batch_folder", "")
                        job_profile_name = batch_response.get("job_profile_name", "jobprofile")
                        batch_timestamp = batch_response.get("timestamp", "")
                        
                        # Log batch results for debugging
                        print(f"\n📊 Batch Results Summary:", file=sys.stderr)
                        for idx, res in enumerate(batch_results):
                            print(f"  CV {idx+1}: success={res.get('success')}, error={res.get('error')}", file=sys.stderr)
                        
                        # For now, wrap batch results in a success structure
                        results = {
                            "success": all(r.get("success", False) for r in batch_results),
                            "batch_results": batch_results,
                            "batch_folder": batch_folder,
                            "job_profile_name": job_profile_name,
                            "batch_timestamp": batch_timestamp,
                            "mode": mode,
                            "error": None if all(r.get("success", False) for r in batch_results) else "Some CVs failed processing"
                        }
                    else:
                        # Single CV Mode: Process one CV
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
                    # Save to History
                    if "history_saved" not in st.session_state:
                        if mode.startswith("Batch"):
                            # For batch mode, create ONE entry for the entire batch with all results
                            batch_folder = results.get("batch_folder", "")
                            batch_results = results.get("batch_results", [])
                            successful_count = sum(1 for r in batch_results if r.get("success"))
                            failed_count = len(batch_results) - successful_count
                            
                            # Create a single batch history entry with all candidate data
                            history_entry = {
                                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                                "candidate_name": f"Batch ({successful_count}/{len(batch_results)})",  # Show success rate
                                "mode": mode,
                                "model_name": results.get("batch_results", [{}])[0].get("model_name", os.environ.get("MODEL_NAME", "gpt-4o-mini")),
                                "batch_folder": batch_folder,
                                "is_batch": True,
                                "batch_results": batch_results,  # Store all candidate results
                                "job_profile_name": results.get("job_profile_name", ""),
                                "stellenprofil_json": results.get("batch_results", [{}])[0].get("stellenprofil_json") if batch_results else None
                            }
                            save_to_history(history_entry)
                        else:
                            # Single CV mode: save single entry
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
                                "offer_word_path": results.get("offer_word_path"),
                                "is_batch": False
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
                    # Check if batch mode with partial failures
                    if is_batch and results.get("batch_results"):
                        batch_results = results.get("batch_results", [])
                        successful = [r for r in batch_results if r.get("success")]
                        failed = [r for r in batch_results if not r.get("success")]
                        
                        if successful:
                            # Partial success - show results with warnings
                            status.update(label=f"⚠️  {len(successful)}/{len(batch_results)} erfolgreich", state="running", expanded=False)
                            st.warning(f"⚠️ {len(failed)} von {len(batch_results)} CVs konnten nicht verarbeitet werden")
                            st.session_state.generation_results = results
                            
                            if st.button(get_text("ui", "show_results", st.session_state.language), type="primary", use_container_width=True):
                                st.session_state.show_results_view = True
                                st.rerun()
                        else:
                            # All failed
                            st.error(f"{get_text('ui', 'error_prefix_colon', st.session_state.language)} Alle CVs konnten nicht verarbeitet werden")
                            status.update(label=get_text('ui', 'processing_error_label', st.session_state.language), state="error")
                            if st.button(get_text('ui', 'close_btn', st.session_state.language)):
                                st.rerun()
                    else:
                        # Non-batch error or no batch results
                        st.error(f"{get_text('ui', 'error_prefix_colon', st.session_state.language)} {results.get('error')}")
                        status.update(label=get_text('ui', 'processing_error_label', st.session_state.language), state="error")
                        if st.button(get_text('ui', 'close_btn', st.session_state.language)):
                            st.rerun()

            except Exception as e:
                st.error(f"{get_text('ui', 'unexpected_error', st.session_state.language)} {str(e)}")
                status.update(label=get_text( "ui", "error_status", st.session_state.language), state="error")
                if st.button(get_text( "ui", "close_btn", st.session_state.language)):
                        st.rerun()
    
    elif phase == "results":
        results = st.session_state.generation_results
        
        # Check if batch mode
        if results.get("batch_results"):
            # Batch Results Display
            display_batch_results(
                results.get("batch_results", []),
                results.get("stellenprofil_json"),
                st.session_state.language
            )
        else:
            # Single CV Results Display
            st.subheader(get_text( "ui", "results_title", st.session_state.language))
            
            # Extract name for title and buttons
            candidate_name = get_text( "ui", "history_unknown", st.session_state.language)
            if results.get("cv_json"):
                try:
                    filename = os.path.basename(results["cv_json"])
                    parts = filename.split('_')
                    if len(parts) >= 3: candidate_name = f"{parts[1]} {parts[2]}"
                except: pass
            
            model_used = results.get("model_name", os.environ.get("MODEL_NAME", "gpt-4o-mini"))
            st.caption(f"{get_text( 'ui', 'history_mode', st.session_state.language)}: {results.get('mode', get_text( 'ui', 'history_unknown', st.session_state.language))} | {get_text( 'ui', 'history_model', st.session_state.language)}: {model_used}")
                
            # Format button label with truncation
            cv_btn_label = f"{get_text( 'ui', 'word_cv_btn', st.session_state.language)} - {candidate_name}"
            if len(cv_btn_label) > 30:
                cv_btn_label = cv_btn_label[:27] + "..."
            
            # Downloads Section
            with st.success(get_text( "ui", "downloads_title", st.session_state.language), icon="📥"):
                res_col1, res_col2, res_col3 = st.columns(3)
                with res_col1:
                    if results.get("word_path") and os.path.exists(results["word_path"]):
                        with open(results["word_path"], "rb") as f:
                            st.download_button(cv_btn_label, f, os.path.basename(results["word_path"]), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
                with res_col2:
                    if results.get("cv_json") and os.path.exists(results["cv_json"]):
                        with open(results["cv_json"], "rb") as f:
                            st.download_button(get_text( "ui", "json_data_btn", st.session_state.language), f, os.path.basename(results["cv_json"]), "application/json", use_container_width=True)
                with res_col3:
                    if results.get("dashboard_path") and os.path.exists(results["dashboard_path"]):
                        with open(results["dashboard_path"], "rb") as f:
                            st.download_button(get_text( "ui", "dashboard_btn", st.session_state.language), f, os.path.basename(results["dashboard_path"]), "text/html", use_container_width=True)

            # Offer Generation Section
            # Try to infer stellenprofil_json if missing (for history items)
            if not results.get("stellenprofil_json") and results.get("cv_json"):
                output_dir = os.path.dirname(results["cv_json"])
                # Look for any file starting with stellenprofil_ in the same dir
                try:
                    for f in os.listdir(output_dir):
                        if f.startswith("stellenprofil_") and f.endswith(".json"):
                            results["stellenprofil_json"] = os.path.join(output_dir, f)
                            break
                except: pass

            # Try to infer match_json if missing
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
                
                # Dynamic container style to differentiate states
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
                                        
                                        # Verify existence
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
                                        st.code(traceback.format_exc()) # Show details for debugging
                    with off_col2:
                        if not is_offer_ready:
                            st.caption(get_text('ui', 'offer_button_caption', st.session_state.language))
                        else:
                            st.caption(get_text('ui', 'offer_ready_caption', st.session_state.language))

            st.markdown("<div style='margin-top: 40px; margin-bottom: 20px; border-top: 1px solid #ddd;'></div>", unsafe_allow_html=True)

            # Show Dashboard Preview
            if results.get("dashboard_path") and os.path.exists(results["dashboard_path"]):
                with open(results["dashboard_path"], "r", encoding='utf-8') as f:
                    html_content = f.read()
                    # Use a larger height to fill the expanded dialog
                    st.components.v1.html(html_content, height=1200, scrolling=True)
                    
            if st.button(get_text("ui", "close_btn", st.session_state.language), use_container_width=True):
                st.session_state.show_pipeline_dialog = False
            st.session_state.show_results_view = False
            if "current_generation_results" in st.session_state:
                del st.session_state.current_generation_results
            st.rerun()

# Left-align the start button (approx 33% width)
btn_col, _ = st.columns([1, 2])
with btn_col:
    if st.button(get_text("ui", "start_generation_btn", st.session_state.language), disabled=start_disabled, type="primary", use_container_width=True):
        st.session_state.show_pipeline_dialog = True
        st.session_state.show_results_view = False
        if "current_generation_results" in st.session_state:
            del st.session_state.current_generation_results

if st.session_state.get("show_pipeline_dialog"):
    # Prepare files based on mode
    if mode.startswith("Batch"):
        # For batch mode, pass cv_files list instead of single cv_file
        run_cv_pipeline_dialog(cv_files, job_file, api_key, mode, st.session_state.get("custom_styles"), st.session_state.get("custom_logo_path"))
    else:
        # For single CV modes
        run_cv_pipeline_dialog(cv_file, job_file, api_key, mode, st.session_state.get("custom_styles"), st.session_state.get("custom_logo_path"))

