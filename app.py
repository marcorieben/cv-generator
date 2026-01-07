import streamlit as st
import os
import json
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from datetime import datetime
from dotenv import load_dotenv
from scripts.streamlit_pipeline import StreamlitCVGenerator
from scripts.generate_angebot import generate_angebot_json
from scripts.generate_angebot_word import generate_angebot_word

# --- Helper Functions ---
def reset_all_pipeline_states():
    """Resets all session state variables related to the pipeline dialog/view."""
    st.session_state.show_pipeline_dialog = False
    st.session_state.show_results_view = False
    if "current_generation_results" in st.session_state:
        del st.session_state.current_generation_results
    # Note: we don't necessarily want to delete st.session_state.generation_results 
    # as that's used for the background 'ERGEBNISSE' view if needed.

@st.dialog("KI-Modell Übersicht", width="large")
def show_model_info_dialog():
    st.markdown("""
    ### 🤖 Modell-Empfehlungen & Kosten
    
    Die Kosten sind Schätzungen pro CV-Generierung (Input + Output Tokens).
    
    | Modell | Empfehlung | Kosten | Beschreibung |
    | :--- | :--- | :--- | :--- |
    | **gpt-4o-mini** | ✅ **Standard** | **~$0.01** | Schnell & günstig. Für 95% der Fälle. |
    | **gpt-4o** | 💎 **High-End** | **~$0.15** | Besser bei komplexen Layouts. |
    | **gpt-3.5-turbo** | ⚠️ **Legacy** | **~$0.005** | Nicht empfohlen (Formatierungsfehler). |
    | **mock** | 🧪 **Test** | **Gratis** | Nur für Entwicklung (Dummy-Daten). |
    
    **Empfehlung:** Nutzen Sie standardmässig `gpt-4o-mini`. Wechseln Sie nur zu `gpt-4o`, wenn die Extraktion ungenau ist.
    """)

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

@st.dialog("Applikations-Informationen", width="large")
def show_app_info_dialog():
    st.markdown("""
    ### 🏢 Geschäftszweck & Nutzen
    
    **CV Generator & Matchmaking Suite**
    
    Diese Applikation dient der automatisierten Verarbeitung, Analyse und Optimierung von Kandidatenprofilen. 
    Sie unterstützt HR-Teams und Recruiter dabei, den manuellen Aufwand bei der CV-Erstellung und dem Abgleich mit Stellenprofilen drastisch zu reduzieren.
    
    **Kernfunktionen:**
    *   **CV Parsing:** Extraktion strukturierter Daten aus PDF-Lebensläufen mittels KI.
    *   **Standardisierung:** Generierung von einheitlichen, gebrandeten Word-CVs.
    *   **Matchmaking:** Intelligenter Abgleich von Kandidatenprofilen gegen Stellenbeschreibungen.
    *   **Qualitätssicherung:** Automatische Prüfung auf Lücken, Inkonsistenzen und fehlende Skills.
    
    ---
    """)
    
    st.subheader("📜 Änderungshistorie (Changelog)")
    
    commits = get_git_history(20)
    
    relevant_types = {
        "feat": "✨ Neue Funktion",
        "fix": "🐛 Fehlerbehebung",
        "ui": "🎨 Design & UI",
        "perf": "⚡ Performance",
        "docs": "📚 Dokumentation"
    }
    
    visible_count = 0
    for commit in commits:
        msg = commit['message']
        category = "📝 Allgemein"
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
            elif type_key in ["chore", "refactor", "test", "ci", "build"]:
                is_relevant = False # Skip technical commits
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
                        st.info(body)
                    else:
                        st.caption("Keine weiteren Details vorhanden.")
                else:
                    st.caption("Keine weiteren Details vorhanden.")
            
    if visible_count == 0:
        st.caption("Keine relevanten Änderungen in den letzten Commits gefunden.")

# Page config
st.set_page_config(
    page_title="CV Generator",
    page_icon="templates/logo.png",
    layout="wide"
)

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
        st.error('Benutzername/Passwort ist falsch')
        st.info('Passwort vergessen? Bitte kontaktieren Sie den Administrator.')
        st.stop()
    elif st.session_state["authentication_status"] is None:
        st.warning('Bitte geben Sie Ihren Benutzernamen und Ihr Passwort ein')
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
    st.title("⚙️ Einstellungen")
    
    # Placeholder for logo at the top
    logo_placeholder = st.empty()
    
    # --- Settings Menu ---
    with st.expander("👤 Persönliche Einstellungen", expanded=False):
        try:
            if authenticator.reset_password(username, 'main'):
                st.success('Passwort erfolgreich geändert')
                with open('config.yaml', 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)
        except Exception as e:
            st.error(e)

    with st.expander("🎨 Design & Farben", expanded=False):
        st.caption("Passen Sie das Erscheinungsbild an:")
        
        # Default values from styles.json (Orange #FF7900)
        primary_color = st.color_picker("Primärfarbe (Überschriften)", "#FF7900")
        secondary_color = st.color_picker("Sekundärfarbe (Text)", "#444444")
        
        # Font Selection
        font_options = ["Aptos", "Arial", "Calibri", "Helvetica", "Times New Roman"]
        selected_font = st.selectbox("Schriftart", font_options, index=0)
        
        # Logo Upload
        uploaded_logo = st.file_uploader("Firmenlogo (PNG/JPG)", type=["png", "jpg", "jpeg"])
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
    with st.expander("🤖 KI-Modell", expanded=False):
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
                "Modell auswählen:",
                options=model_options,
                index=0,
                key="model_selection_sidebar",
                format_func=lambda x: f"{x} ({model_details.get(x, {}).get('rec', '')})",
                on_change=reset_all_pipeline_states
            )
        with col_info:
            st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
            if st.button("ℹ️", key="model_info_btn", help="Details zu Kosten & Modellen"):
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
                st.success("API Key aktiv ✅")
                # Only show change button if key is not from environment
                if not os.getenv("OPENAI_API_KEY") and "OPENAI_API_KEY" not in st.secrets:
                    if st.button("API Key ändern"):
                        if "api_key" in st.session_state:
                            del st.session_state.api_key
                        st.rerun()
        
        st.caption(f"Aktueller Modus: {os.getenv('CV_GENERATOR_MODE', 'full')}")

    # --- Application Info ---
    with st.expander("ℹ️ Applikations-Infos", expanded=False):
        st.caption("Details zur Applikation & Version")
        if st.button("Details anzeigen", use_container_width=True):
            show_app_info_dialog()

    st.divider()
    
    # --- History Section ---
    with st.expander("📜 Verlauf", expanded=False):
        history = load_history()
        
        if not history:
            st.caption("Noch keine Läufe gespeichert.")
        else:
            for item in history:
                timestamp = item.get("timestamp", "")
                # Format timestamp nicely if possible (YYYYMMDD_HHMMSS -> DD.MM.YYYY HH:MM)
                try:
                    dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    display_time = dt.strftime("%d.%m. %H:%M")
                except:
                    display_time = timestamp

                candidate_name = item.get("candidate_name", "Unbekannt")
                
                with st.expander(f"{display_time} - {candidate_name}", expanded=False):
                    model_used = item.get("model_name", "Unbekannt")
                    st.caption(f"Modus: {item.get('mode')} | Modell: {model_used}")
                    
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
                                <div style="margin-bottom: 5px; font-size: 0.8em; color: #666;">Match Score: {score}%</div>
                                <div style="background-color: #eee; border-radius: 4px; height: 8px; width: 100%; margin-bottom: 15px;">
                                    <div style="background-color: {bar_color}; width: {score_val}%; height: 100%; border-radius: 4px;"></div>
                                </div>
                            """, unsafe_allow_html=True)
                        except:
                            pass

                    # 2. Action Buttons
                    if st.button("🔎 Details anzeigen", key=f"hist_btn_{timestamp}", use_container_width=True):
                        st.session_state.generation_results = item
                        st.session_state.show_pipeline_dialog = True
                        st.session_state.show_results_view = True
                        st.rerun()
    
    # Spacer to push content to bottom
    st.markdown("<div style='flex-grow: 1;'></div>", unsafe_allow_html=True)
    
    st.divider()
    
    # --- User Info & Logout (Bottom) ---
    st.write(f'Willkommen *{name}*')
    authenticator.logout('Abmelden', 'sidebar')

# --- Main Content ---
st.title("📄 CV Generator")
st.markdown("Generieren Sie massgeschneiderte Lebensläufe basierend auf PDF-Inputs.")

# Mode Selection with Cards
st.subheader("Wählen Sie Ihren Modus")

col_m1, col_m2, col_m3 = st.columns(3)

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
    if st.button("🚀 Basic\n(Nur CV)", use_container_width=True, type="primary" if st.session_state.selected_mode.startswith("Basic") else "secondary"):
        st.session_state.selected_mode = "Basic (Nur CV)"
        # Reset pipeline state
        st.session_state.show_pipeline_dialog = False
        st.session_state.show_results_view = False
        st.rerun()
    st.caption("Extrahiert Daten aus dem CV und erstellt ein Word-Dokument.")

with col_m2:
    if st.button("🔍 Analysis\n(CV + Profil)", use_container_width=True, type="primary" if st.session_state.selected_mode.startswith("Analysis") else "secondary"):
        st.session_state.selected_mode = "Analysis (CV + Stellenprofil)"
        # Reset pipeline state
        st.session_state.show_pipeline_dialog = False
        st.session_state.show_results_view = False
        st.rerun()
    st.caption("Optimiert den CV basierend auf einem Stellenprofil.")

with col_m3:
    if st.button("✨ Full Suite\n(All-in-One)", use_container_width=True, type="primary" if st.session_state.selected_mode.startswith("Full") else "secondary"):
        st.session_state.selected_mode = "Full (CV + Stellenprofil + Match + Feedback)"
        # Reset pipeline state
        st.session_state.show_pipeline_dialog = False
        st.session_state.show_results_view = False
        st.rerun()
    st.caption("Das volle Programm: CV, Match-Score, Feedback & Dashboard.")

mode = st.session_state.selected_mode
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
                <strong>✅ Datei aktiv:</strong> {current_file.name}
            </div>
        """, unsafe_allow_html=True)
                
    return current_file

# Dynamic Columns based on Mode
if mode.startswith("Basic"):
    # Left-aligned column for CV upload (using same ratio as Full mode)
    col1, col2 = st.columns(2)
    with col1:
        if is_mock:
            st.subheader("📄 1. Lebenslauf (CV)")
            st.success("🧪 **Test-Modus aktiv**")
            st.caption("Es wird ein beispielhafter Lebenslauf verwendet.")
            cv_file = None
        else:
            cv_file = render_custom_uploader("📄 1. Lebenslauf (CV)", "cv_basic")
        job_file = None # No job file in Basic mode
else:
    # Two columns for CV and Job Profile
    col1, col2 = st.columns(2)

    with col1:
        if is_mock:
            st.subheader("📄 1. Lebenslauf (CV)")
            st.success("🧪 **Test-Modus aktiv**")
            st.caption("Es wird ein beispielhafter Lebenslauf verwendet.")
            cv_file = None
        else:
            cv_file = render_custom_uploader("📄 1. Lebenslauf (CV)", "cv_full")

    with col2:
        if is_mock:
            st.subheader("📋 2. Stellenprofil")
            st.success("🧪 **Test-Modus aktiv**")
            st.caption("Es wird ein beispielhaftes Stellenprofil verwendet.")
            job_file = None
        else:
            job_file = render_custom_uploader("📋 2. Stellenprofil", "job_full")

st.divider()

# DSGVO / Privacy Notice
st.markdown("### 🔒 Datenschutz & Hinweise")
st.caption("Dokumente werden zur Analyse an OpenAI gesendet und nicht dauerhaft gespeichert. Keine Firmengeheimnisse hochladen.")
dsgvo_accepted = st.checkbox("Ich bestätige, dass ich die Datenschutzhinweise gelesen habe und zustimme.", value=False)

# Action Button
is_mock = os.environ.get("MODEL_NAME") == "mock"

if is_mock:
    # In Mock mode, we don't need files or API key
    start_disabled = False
    # Use dummy files if not uploaded
    if not cv_file: cv_file = "MOCK_CV.pdf"
    if not job_file: job_file = "MOCK_JOB.pdf"
    # Use dummy key if not present (to satisfy checks)
    if not api_key: api_key = "mock-key"
else:
    start_disabled = not cv_file or not api_key or not dsgvo_accepted

@st.dialog("CV Generator Pipeline", width="large")
def run_cv_pipeline_dialog(cv_file, job_file, api_key, mode, custom_styles, custom_logo_path):
    
    # Determine Phase: 'processing' or 'results'
    if "generation_results" in st.session_state and st.session_state.get("show_results_view"):
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
        with st.status("🚀 Dokumente werden verarbeitet...", expanded=True) as status:
            log_container = st.empty()
            
            def progress_callback(pct, text, state="running"):
                log_container.write(f"**Aktueller Schritt:** {text}")
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
                    # Run Pipeline
                    generator = StreamlitCVGenerator(os.getcwd())
                    results = generator.run(
                        cv_file=cv_file,
                        job_file=job_file if mode != "Basic (Nur CV)" else None,
                        api_key=api_key,
                        progress_callback=progress_callback,
                        custom_styles=current_custom_styles,
                        custom_logo_path=current_custom_logo_path,
                        pipeline_mode=mode
                    )
                    st.session_state.current_generation_results = results
                
                if results.get("success"):
                    # Save to History
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
                    status.update(label="✅ Verarbeitung abgeschlossen!", state="complete", expanded=False)
                    st.success("✅ Generierung erfolgreich abgeschlossen!")
                    
                    if st.button("Ergebnisse anzeigen", type="primary", use_container_width=True):
                        st.session_state.show_results_view = True
                        st.rerun()
                else:
                    st.error(f"Fehler: {results.get('error')}")
                    status.update(label="❌ Fehler aufgetreten", state="error")
                    if st.button("Schließen"):
                        st.rerun()

            except Exception as e:
                st.error(f"Unerwarteter Fehler: {str(e)}")
                status.update(label="❌ Fehler", state="error")
                if st.button("Schließen"):
                        st.rerun()
    
    elif phase == "results":
        results = st.session_state.generation_results
        st.subheader("🎉 Ergebnisse")
        
        # Extract name for title and buttons
        candidate_name = "Unbekannt"
        if results.get("cv_json"):
            try:
                filename = os.path.basename(results["cv_json"])
                parts = filename.split('_')
                if len(parts) >= 3: candidate_name = f"{parts[1]} {parts[2]}"
            except: pass
        
        model_used = results.get("model_name", os.environ.get("MODEL_NAME", "gpt-4o-mini"))
        st.caption(f"Modus: {results.get('mode', 'Unbekannt')} | KI-Modell: {model_used}")
            
        # Format button label with truncation
        cv_btn_label = f"📄 Word-CV - {candidate_name}"
        if len(cv_btn_label) > 30:
            cv_btn_label = cv_btn_label[:27] + "..."
        
        # Downloads Section
        with st.success("📥 Downloads", icon="📥"):
            res_col1, res_col2, res_col3 = st.columns(3)
            with res_col1:
                if results.get("word_path") and os.path.exists(results["word_path"]):
                    with open(results["word_path"], "rb") as f:
                        st.download_button(cv_btn_label, f, os.path.basename(results["word_path"]), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
            with res_col2:
                if results.get("cv_json") and os.path.exists(results["cv_json"]):
                    with open(results["cv_json"], "rb") as f:
                        st.download_button("📋 JSON-Daten", f, os.path.basename(results["cv_json"]), "application/json", use_container_width=True)
            with res_col3:
                if results.get("dashboard_path") and os.path.exists(results["dashboard_path"]):
                    with open(results["dashboard_path"], "rb") as f:
                        st.download_button("📊 Dashboard", f, os.path.basename(results["dashboard_path"]), "text/html", use_container_width=True)

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
                offer_container = st.success("✅ Angebot fertiggestellt", icon="✅")
            else:
                offer_container = st.info("💼 Angebot erstellen", icon="✨")
            
            with offer_container:
                off_col1, off_col2, off_col3 = st.columns(3)
                with off_col1:
                    if is_offer_ready:
                         with open(offer_word_path, "rb") as f:
                            st.download_button("📄 Angebot herunterladen", f, os.path.basename(offer_word_path), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True, type="primary")
                    else:
                        off_btn_key = f"gen_offer_btn_{results.get('cv_json', '')}"
                        if st.button("Angebot erstellen", use_container_width=True, key=off_btn_key):
                            with st.status("🚀 Erstelle Angebot...", expanded=True) as status:
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
                                    generate_angebot_json(cv_json, stellenprofil_json, match_json, angebot_json_path, schema_path)
                                    
                                    status.write("📝 Word-Dokument formatieren...")
                                    generate_angebot_word(angebot_json_path, angebot_word_path)
                                    
                                    # Verify existence
                                    if os.path.exists(angebot_word_path):
                                        results["offer_word_path"] = angebot_word_path
                                        st.session_state.generation_results = results
                                        st.session_state.show_pipeline_dialog = True
                                        st.session_state.show_results_view = True
                                        status.update(label="✅ Angebot bereit!", state="complete", expanded=False)
                                        st.success("✅ Angebot erfolgreich erstellt!")
                                        st.rerun()
                                    else:
                                        st.error("Datei wurde generiert, aber nicht im Dateisystem gefunden.")
                                except Exception as e:
                                    status.update(label="❌ Fehler", state="error")
                                    st.error(f"Fehler bei der Angebotserstellung: {e}")
                                    import traceback
                                    st.code(traceback.format_exc()) # Show details for debugging
                with off_col2:
                    if not is_offer_ready:
                        st.caption("Erstellt ein Angebot basierend auf den Analysedaten.")
                    else:
                        st.caption("Das Angebot wurde erfolgreich generiert und steht zum Download bereit.")

        st.markdown("<div style='margin-top: 40px; margin-bottom: 20px; border-top: 1px solid #ddd;'></div>", unsafe_allow_html=True)

        # Show Dashboard Preview
        if results.get("dashboard_path") and os.path.exists(results["dashboard_path"]):
            with open(results["dashboard_path"], "r", encoding='utf-8') as f:
                html_content = f.read()
                # Use a larger height to fill the expanded dialog
                st.components.v1.html(html_content, height=1200, scrolling=True)
                
        if st.button("Schliessen", use_container_width=True):
            st.session_state.show_pipeline_dialog = False
            st.session_state.show_results_view = False
            if "current_generation_results" in st.session_state:
                del st.session_state.current_generation_results
            st.rerun()

# Left-align the start button (approx 33% width)
btn_col, _ = st.columns([1, 2])
with btn_col:
    if st.button("🚀 Generierung starten", disabled=start_disabled, type="primary", use_container_width=True):
        st.session_state.show_pipeline_dialog = True
        st.session_state.show_results_view = False
        if "current_generation_results" in st.session_state:
            del st.session_state.current_generation_results

if st.session_state.get("show_pipeline_dialog"):
    run_cv_pipeline_dialog(cv_file, job_file, api_key, mode, st.session_state.get("custom_styles"), st.session_state.get("custom_logo_path"))

