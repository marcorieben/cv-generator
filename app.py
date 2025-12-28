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
    
    **Empfehlung:** Nutzen Sie standardmäßig `gpt-4o-mini`. Wechseln Sie nur zu `gpt-4o`, wenn die Extraktion ungenau ist.
    """)

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
        st.error('Username/password is incorrect')
        st.info('Forgot your password? Please contact the administrator.')
        st.stop()
    elif st.session_state["authentication_status"] is None:
        st.warning('Please enter your username and password')
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

        def reset_pipeline_state():
            st.session_state.show_pipeline_dialog = False
            st.session_state.show_results_view = False

        col_sel, col_info = st.columns([0.85, 0.15])
        with col_sel:
            selected_model = st.selectbox(
                "Modell auswählen:",
                options=model_options,
                index=0,
                format_func=lambda x: f"{x} ({model_details.get(x, {}).get('rec', '')})",
                on_change=reset_pipeline_state
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

                name = item.get("candidate_name", "Unbekannt")
                
                with st.expander(f"{display_time} - {name}", expanded=False):
                    st.caption(f"Modus: {item.get('mode')}")
                    
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
    st.write(f'Welcome *{name}*')
    authenticator.logout('Logout', 'sidebar')

# --- Main Content ---
st.title("📄 CV Generator")
st.markdown("Generieren Sie maßgeschneiderte Lebensläufe basierend auf PDF-Inputs.")

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
    # Check for delete action via query param (triggered by HTML link)
    delete_key = f"delete_{key_prefix}"
    # Handle query params safely (Streamlit >= 1.30)
    try:
        if delete_key in st.query_params:
            st.session_state[f"{key_prefix}_file"] = None
            st.query_params.clear()
            st.rerun()
    except:
        pass # Fallback for older versions or errors

    # Title is ALWAYS visible
    st.subheader(label)
    
    # Persistent state key for the file object
    file_state_key = f"{key_prefix}_file"
    
    # Initialize state if needed
    if file_state_key not in st.session_state:
        st.session_state[file_state_key] = None
    
    uploaded_file = st.session_state[file_state_key]
    
    if uploaded_file:
        # SUCCESS STATE: Custom Green Box (HTML) with Integrated Delete Link
        st.markdown(f"""
            <div style="
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                color: #155724;
                padding: 10px 15px;
                border-radius: 5px;
                display: flex;
                align-items: center;
                justify-content: space-between;
            ">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 1.5em; margin-right: 15px;">✅</span>
                    <div>
                        <div style="font-weight: bold;">Datei erfolgreich hochgeladen</div>
                        <div style="font-size: 0.9em; color: #155724;">{uploaded_file.name} ({round(uploaded_file.size / 1024, 1)} KB)</div>
                    </div>
                </div>
                <a href="?{delete_key}=true" target="_self" style="text-decoration: none; font-size: 1.2em; margin-left: 10px; cursor: pointer;" title="Datei entfernen">🗑️</a>
            </div>
        """, unsafe_allow_html=True)
                
        return uploaded_file
    else:
        # UPLOAD STATE: Standard uploader
        # Use a temporary widget key. When file is uploaded, we save it and rerun.
        widget_key = f"{key_prefix}_widget"
        new_file = st.file_uploader(label, type=file_type, key=widget_key, label_visibility="collapsed")
        
        if new_file:
            st.session_state[file_state_key] = new_file
            # Reset pipeline state on new upload
            st.session_state.show_pipeline_dialog = False
            st.session_state.show_results_view = False
            st.rerun()
            
        return None

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

    if phase == "processing":
        st.subheader("Verarbeitung läuft...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        st.caption("ℹ️ Hinweis: Die Verarbeitung kann je nach Komplexität der Dateien 1-3 Minuten dauern.")
        
        # Define steps based on mode
        all_steps = [
            (0, "Stellenprofil analysieren", "🔍"),
            (1, "CV analysieren", "📄"),
            (2, "Qualitätsprüfung & Validierung", "✅"),
            (3, "Word-Dokument erstellen", "📝"),
            (4, "Match-Making Analyse", "🤝"),
            (5, "CV-Feedback generieren", "💡"),
            (6, "Angebot erstellen", "💼"),
            (7, "Dashboard erstellen", "📊")
        ]
        
        visible_steps = []
        if mode == "Basic (Nur CV)":
                visible_steps = [s for s in all_steps if s[0] in [1, 2, 3, 7]]
        elif mode == "Analyse & Matching":
                visible_steps = [s for s in all_steps if s[0] in [0, 1, 2, 3, 4, 5, 7]]
        else:
                visible_steps = all_steps

        # Create placeholders for each step
        step_placeholders = {}
        for idx, label, icon in visible_steps:
            step_placeholders[idx] = st.empty()

        def render_step(idx, label, icon, status):
            color = "#cccccc"
            status_icon = "⚪"
            font_weight = "normal"
            bg_color = "white"
            
            if status == "running":
                color = "#FF7900"
                status_icon = "🔄"
                font_weight = "bold"
                bg_color = "#FFF5EB"
            elif status == "completed":
                color = "#28a745"
                status_icon = "✅"
                bg_color = "#F8F9FA"
            
            step_placeholders[idx].markdown(
                f"""
                <div style="display: flex; align-items: center; margin-bottom: 8px; padding: 12px; background-color: {bg_color}; border-radius: 8px; border: 1px solid #eee;">
                    <div style="font-size: 24px; margin-right: 15px; width: 40px; text-align: center; color: {color};">{icon}</div>
                    <div style="flex-grow: 1; font-family: 'Segoe UI', sans-serif; color: #444;">
                        <div style="font-weight: {font_weight}; font-size: 16px;">{label}</div>
                    </div>
                    <div style="font-size: 20px; color: {color};">{status_icon}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Initialize steps
        initial_status = "completed" if "current_generation_results" in st.session_state else "pending"
        for idx, label, icon in visible_steps:
            render_step(idx, label, icon, initial_status)

        def update_progress(percent, text, state):
            progress_bar.progress(percent)
            status_text.markdown(f"**{text}**")
            
            for idx, label, icon in visible_steps:
                status = "pending"
                if percent >= 100: status = "completed"
                elif percent >= 90:
                    if idx < 7: status = "completed"
                    elif idx == 7: status = "running"
                elif percent >= 70:
                    if idx < 3: status = "completed"
                    elif idx in [3, 4, 5, 6]: status = "running"
                elif percent >= 50:
                    if idx < 2: status = "completed"
                    elif idx == 2: status = "running"
                elif percent >= 30:
                    if idx < 1: status = "completed"
                    elif idx == 1: status = "running"
                elif percent >= 10:
                    if idx == 0: status = "running"
                render_step(idx, label, icon, status)

        generator = StreamlitCVGenerator(os.getcwd())
        use_job_file = job_file if mode != "Basic (Nur CV)" else None
        
        # 1. Check Cache
        if "current_generation_results" in st.session_state:
            results = st.session_state.current_generation_results
            progress_bar.progress(100)
            status_text.markdown("**Fertig!**")
        else:
            # 2. Run Generation
            results = generator.run(
                cv_file=cv_file,
                job_file=use_job_file,
                api_key=api_key,
                progress_callback=update_progress,
                custom_styles=custom_styles,
                custom_logo_path=custom_logo_path
            )
            st.session_state.current_generation_results = results
            
            # 3. Save History (Only on fresh run)
            if results["success"]:
                history_entry = {
                    "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                    "candidate_name": os.path.basename(results["cv_json"]).split('_')[1] + " " + os.path.basename(results["cv_json"]).split('_')[2] if results.get("cv_json") else "Unbekannt",
                    "mode": mode,
                    "word_path": results.get("word_path"),
                    "cv_json": results.get("cv_json"),
                    "dashboard_path": results.get("dashboard_path"),
                    "match_score": results.get("match_score"),
                    "stellenprofil_json": results.get("stellenprofil_json"),
                    "match_json": results.get("match_json"),
                    "offer_word_path": results.get("offer_word_path")
                }
                save_to_history(history_entry)

        if results["success"]:
            for idx, label, icon in visible_steps:
                render_step(idx, label, icon, "completed")
                
            st.success("✅ Generierung erfolgreich abgeschlossen!")
            
            st.session_state.generation_results = results
            if st.button("Ergebnisse anzeigen", type="primary", use_container_width=True):
                st.session_state.show_results_view = True
                st.rerun()
        else:
            st.error(f"Fehler: {results['error']}")

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
                        if st.button("Angebot erstellen", use_container_width=True):
                            with st.spinner("Erstelle Angebot..."):
                                try:
                                    cv_json = results["cv_json"]
                                    stellenprofil_json = results["stellenprofil_json"]
                                    match_json = results.get("match_json")
                                    output_dir = os.path.dirname(cv_json)
                                    base_name = os.path.basename(cv_json).replace("cv_", "").replace(".json", "")
                                    angebot_json_path = os.path.join(output_dir, f"Angebot_{base_name}.json")
                                    angebot_word_path = os.path.join(output_dir, f"Angebot_{base_name}.docx")
                                    schema_path = os.path.join(os.getcwd(), "scripts", "angebot_json_schema.json")
                                    generate_angebot_json(cv_json, stellenprofil_json, match_json, angebot_json_path, schema_path)
                                    generate_angebot_word(angebot_json_path, angebot_word_path)
                                    results["offer_word_path"] = angebot_word_path
                                    st.session_state.generation_results = results
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Fehler bei der Angebotserstellung: {e}")
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
                st.components.v1.html(html_content, height=800, scrolling=True)
                
        if st.button("Schließen", use_container_width=True):
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

