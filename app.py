"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-21
Last Updated: 2026-01-24
"""
import streamlit as st
import os
import yaml
import json
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from datetime import datetime
from dotenv import load_dotenv
from scripts.streamlit_pipeline import StreamlitCVGenerator
from scripts.generate_angebot import generate_angebot_json
from scripts.generate_angebot_word import generate_angebot_word
from core.database.db import Database
from core.database.translations import initialize_translations
from core.ui.sidebar_renderer import load_sidebar_config, render_sidebar

# Page config must be the first Streamlit command
st.set_page_config(
    page_title="CV Generator",
    page_icon="templates/logo.png",
    layout="wide"
)

# Initialize session state variables
if 'language' not in st.session_state:
    st.session_state.language = "de"

if 'custom_styles' not in st.session_state:
    st.session_state.custom_styles = {
        "primary_color": "#FF7900",
        "secondary_color": "#444444"
    }

# Set current page IMMEDIATELY for sidebar active state
st.session_state.current_page = "app.py"

# --- Helper Functions ---
def get_translations_manager():
    """Get or initialize translations manager from database"""
    if "translations_manager" not in st.session_state:
        try:
            db_path = os.path.join(os.path.dirname(__file__), "data", "cv_generator.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            db = Database(db_path)
            st.session_state.translations_manager = initialize_translations(db)
        except Exception as e:
            print(f"Error initializing translations: {e}")
            st.session_state.translations_manager = initialize_translations(None)
    return st.session_state.translations_manager

def get_text(section, key, lang=None):
    """Safely retrieves translated text from database or fallback"""
    if lang is None:
        lang = st.session_state.get("language", "de")
    try:
        tm = get_translations_manager()
        return tm.get(section, key, lang) or key
    except Exception as e:
        print(f"Translation error: {e}")
        return key

def render_simple_sidebar():
    """Render a consistent sidebar for all pages with full menu"""
    with st.sidebar:
        # Logo
        if os.path.exists("templates/logo.png"):
            st.image("templates/logo.png", use_container_width=True)
        
        st.divider()
        
        # Try to render the full sidebar menu
        try:
            sidebar_config = load_sidebar_config()
            
            if sidebar_config:
                def show_model_settings_component(get_text_fn, lang, reset_fn, show_info_fn, get_key_fn, user):
                    pass
                
                def get_authenticator():
                    try:
                        return authenticator
                    except NameError:
                        return None
                
                def reset_password_func(user, location):
                    try:
                        if 'authenticator' in globals():
                            if authenticator.reset_password(user, location):
                                st.success(get_text("ui", "password_changed", st.session_state.language))
                                if 'config' in globals():
                                    with open('config.yaml', 'w') as file:
                                        yaml.dump(config, file, default_flow_style=False)
                    except Exception as e:
                        pass
                
                render_sidebar(
                    config=sidebar_config,
                    get_text_func=get_text,
                    language=st.session_state.language,
                    show_model_settings_func=show_model_settings_component,
                    reset_pipeline_states_func=reset_all_pipeline_states,
                    show_model_info_func=show_model_info_dialog,
                    get_api_key_func=get_api_key,
                    username=st.session_state.get("username", ""),
                    show_app_info_func=show_app_info_dialog,
                    load_history_func=load_history,
                    load_authenticator=get_authenticator,
                    load_password_reset_func=reset_password_func,
                    name=st.session_state.get("name", "")
                )
            else:
                # Fallback: Simple navigation if sidebar config not available
                st.markdown("### 📱 Navigation")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("📋", use_container_width=True, help="Stellenprofile"):
                        st.switch_page("pages/01_Stellenprofile.py")
                with col2:
                    if st.button("👥", use_container_width=True, help="Kandidaten"):
                        st.switch_page("pages/02_Kandidaten.py")
                with col3:
                    if st.button("📊", use_container_width=True, help="Status"):
                        st.switch_page("pages/03_Stellenprofil-Status.py")
        except Exception as e:
            # Fallback: Simple navigation if sidebar rendering fails
            st.markdown("### 📱 Navigation")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📋", use_container_width=True, help="Stellenprofile"):
                    st.switch_page("pages/01_Stellenprofile.py")
            with col2:
                if st.button("👥", use_container_width=True, help="Kandidaten"):
                    st.switch_page("pages/02_Kandidaten.py")
            with col3:
                if st.button("📊", use_container_width=True, help="Status"):
                    st.switch_page("pages/03_Stellenprofil-Status.py")

def render_page_sidebar():
    """Render the sidebar for pages that call this function"""
    try:
        with st.sidebar:
            # Logo (Top Left)
            if os.path.exists("templates/logo.png"):
                st.image("templates/logo.png", use_container_width=True)
            
            st.divider()
            
            # Load and render sidebar from config
            sidebar_config = load_sidebar_config()
            
            if sidebar_config:
                def show_model_settings_component(get_text_fn, lang, reset_fn, show_info_fn, get_key_fn, user):
                    pass
                
                def get_authenticator():
                    try:
                        return authenticator
                    except NameError:
                        return None
                
                def reset_password_func(user, location):
                    try:
                        if 'authenticator' in globals():
                            if authenticator.reset_password(user, location):
                                st.success(get_text("ui", "password_changed", st.session_state.language))
                                if 'config' in globals():
                                    with open('config.yaml', 'w') as file:
                                        yaml.dump(config, file, default_flow_style=False)
                    except Exception as e:
                        pass
                
                try:
                    render_sidebar(
                        config=sidebar_config,
                        get_text_func=get_text,
                        language=st.session_state.language,
                        show_model_settings_func=show_model_settings_component,
                        reset_pipeline_states_func=reset_all_pipeline_states,
                        show_model_info_func=show_model_info_dialog,
                        get_api_key_func=get_api_key,
                        username=st.session_state.get("username", ""),
                        show_app_info_func=show_app_info_dialog,
                        load_history_func=load_history,
                        load_authenticator=get_authenticator,
                        load_password_reset_func=reset_password_func,
                        name=st.session_state.get("name", "")
                    )
                except Exception as e:
                    st.warning(f"Sidebar error: {str(e)[:50]}")
    except Exception as e:
        pass  # Silently fail if sidebar can't render

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
    """
    Retrieves the OpenAI API Key from secrets (Cloud), environment variables (Local),
    or user input.
    """
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

def reset_all_pipeline_states():
    """Resets all session state variables related to the pipeline dialog/view."""
    st.session_state.show_pipeline_dialog = False
    st.session_state.show_results_view = False
    if "current_generation_results" in st.session_state:
        del st.session_state.current_generation_results

def get_git_history(limit=10):
    """Fetches the recent git commit history with detailed body."""
    commits = []
    try:
        import subprocess
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

@st.dialog(get_text('ui', 'dialog_model_overview', st.session_state.language), width="large")
def show_model_info_dialog():
    st.markdown(get_text('ui', 'model_overview_markdown', st.session_state.language))

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
        
        if ":" in msg:
            parts = msg.split(":", 1)
            type_scope = parts[0].lower()
            if "(" in type_scope:
                type_key = type_scope.split("(")[0]
            else:
                type_key = type_scope.strip()
            
            if type_key in relevant_types:
                category = relevant_types[type_key]
                clean_msg = parts[1].strip().replace("{", "&#123;").replace("}", "&#125;")
                is_relevant = True
        else:
            if not msg.startswith("Merge"):
                clean_msg = msg.replace("{", "&#123;").replace("}", "&#125;")
                is_relevant = True

        if is_relevant:
            visible_count += 1
            
            with st.expander(f"{commit['date']} | {category} | {clean_msg}"):
                st.markdown(f"**Commit Hash:** `{commit['hash']}`")
                st.markdown(f"**Autor:** {commit['author']}")
                
                if commit.get('body'):
                    st.markdown("**Details:**")
                    body = commit['body'].strip()
                    if body:
                        st.markdown(body)
                    else:
                        st.caption("Keine weiteren Details vorhanden.")
                else:
                    st.markdown("**Details:**")
                    st.caption("Keine weiteren Details vorhanden.")
    
    if visible_count == 0:
        st.caption("Keine relevanten Änderungen in den letzten Commits gefunden.")

# Custom CSS for Corporate Identity
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

# Initialize database
db_path = os.path.join(os.path.dirname(__file__), "data", "cv_generator.db")
os.makedirs(os.path.dirname(db_path), exist_ok=True)
db = Database(db_path)
tm = initialize_translations(db)

# Set current page for sidebar active state detection
st.session_state.current_page = "app.py"

# --- Render Sidebar ---
render_page_sidebar()

# --- Main Content ---
st.title(get_text("ui", "app_title", st.session_state.language))
st.markdown(get_text("ui", "app_subtitle", st.session_state.language))

st.markdown("""
---
### 🎯 Willkommen im CV Generator!

Diese Anwendung bietet dir folgende Funktionen:

**📄 CV Generator** (Hauptfunktion)
- Extrahiere Daten aus Lebenslauf-PDFs
- Generiere optimierte Word-Dokumente
- Gleiche CVs mit Stellenprofilen ab
- Erstelle automatisch Angebote

**👤 Kandidaten Management**
- Verwalte deine Kandidatendatenbank
- Speichere Lebenslauf-Daten strukturiert
- Zugriff auf historische Einträge

**💼 Stellenprofile**
- Erstelle Anforderungsprofile für offene Positionen
- Verwalte aktive Stellenausschreibungen
- Überblick über Status und Anforderungen

---

**💡 Tipp:** Nutze das **CV Generator** Menü oben links um zu starten!
""")

