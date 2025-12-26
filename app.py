import streamlit as st
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from scripts.streamlit_pipeline import StreamlitCVGenerator

# Page config
st.set_page_config(
    page_title="CV Generator",
    page_icon="📄",
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

# --- Sidebar ---
with st.sidebar:
    # Logo Placeholder (will be filled if logo exists)
    logo_placeholder = st.empty()
    
    st.title("⚙️ Einstellungen")
    
    # API Key Handling
    api_key = get_api_key()
    if not api_key:
        st.warning("Kein API Key gefunden!")
        user_key = st.text_input("OpenAI API Key eingeben:", type="password")
        if user_key:
            st.session_state.api_key = user_key
            st.rerun()
    else:
        st.success("API Key aktiv ✅")
    
    st.divider()

    # --- CI/CD Settings ---
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
    
    st.divider()
    
    # --- Model Settings ---
    with st.expander("🤖 KI-Modell", expanded=False):
        model_options = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "mock"]
        selected_model = st.selectbox(
            "Modell auswählen:",
            options=model_options,
            index=0,
            format_func=lambda x: "🧪 Test-Modus (Kostenlos)" if x == "mock" else x
        )
        # Set model in env for the pipeline to pick up
        os.environ["MODEL_NAME"] = selected_model
        
        if selected_model == "mock":
            st.info("🧪 Test-Modus aktiv: Es werden keine echten API-Calls gemacht.")
        
        st.caption(f"Aktueller Modus: {os.getenv('CV_GENERATOR_MODE', 'full')}")

    st.divider()
    
    # --- History Section ---
    st.subheader("📜 Verlauf")
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
            
            with st.expander(f"{display_time} - {name}"):
                st.caption(f"Modus: {item.get('mode')}")
                if item.get("match_score"):
                    st.caption(f"Match: {item.get('match_score')}%")
                
                # Download Links for History Items
                if item.get("word_path") and os.path.exists(item.get("word_path")):
                    with open(item["word_path"], "rb") as f:
                        st.download_button("📄 Word", f, file_name=os.path.basename(item["word_path"]), key=f"hist_word_{timestamp}")
                
                if item.get("dashboard_path") and os.path.exists(item.get("dashboard_path")):
                    with open(item["dashboard_path"], "rb") as f:
                        st.download_button("📊 Dashboard", f, file_name=os.path.basename(item["dashboard_path"]), key=f"hist_dash_{timestamp}")

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
        st.rerun()
    st.caption("Extrahiert Daten aus dem CV und erstellt ein Word-Dokument.")

with col_m2:
    if st.button("🔍 Analysis\n(CV + Profil)", use_container_width=True, type="primary" if st.session_state.selected_mode.startswith("Analysis") else "secondary"):
        st.session_state.selected_mode = "Analysis (CV + Stellenprofil)"
        st.rerun()
    st.caption("Optimiert den CV basierend auf einem Stellenprofil.")

with col_m3:
    if st.button("✨ Full Suite\n(All-in-One)", use_container_width=True, type="primary" if st.session_state.selected_mode.startswith("Full") else "secondary"):
        st.session_state.selected_mode = "Full (CV + Stellenprofil + Match + Feedback)"
        st.rerun()
    st.caption("Das volle Programm: CV, Match-Score, Feedback & Dashboard.")

mode = st.session_state.selected_mode
st.divider()

# Check for Mock Mode
is_mock = os.environ.get("MODEL_NAME") == "mock"

# Dynamic Columns based on Mode
if mode.startswith("Basic"):
    # Single centered column for CV upload
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("1. Lebenslauf (CV)")
        if is_mock:
            st.success("🧪 **Test-Modus aktiv**")
            st.caption("Es wird ein beispielhafter Lebenslauf verwendet.")
            cv_file = None
        else:
            cv_file = st.file_uploader("Laden Sie den CV als PDF hoch", type=["pdf"])
        job_file = None # No job file in Basic mode
else:
    # Two columns for CV and Job Profile
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. Lebenslauf (CV)")
        if is_mock:
            st.success("🧪 **Test-Modus aktiv**")
            st.caption("Es wird ein beispielhafter Lebenslauf verwendet.")
            cv_file = None
        else:
            cv_file = st.file_uploader("Laden Sie den CV als PDF hoch", type=["pdf"])

    with col2:
        st.subheader("2. Stellenprofil")
        if is_mock:
            st.success("🧪 **Test-Modus aktiv**")
            st.caption("Es wird ein beispielhaftes Stellenprofil verwendet.")
            job_file = None
        else:
            job_file = st.file_uploader("Laden Sie das Stellenprofil als PDF hoch", type=["pdf"])

st.divider()

# DSGVO / Privacy Notice
with st.expander("🔒 Datenschutz & Hinweise", expanded=False):
    st.markdown("""
    **Wichtiger Hinweis zur Datenverarbeitung:**
    * Die hochgeladenen Dokumente werden zur Analyse an die OpenAI API gesendet.
    * Bitte stellen Sie sicher, dass Sie keine vertraulichen Firmengeheimnisse hochladen.
    * Die Daten werden nicht dauerhaft gespeichert, sondern nur für die Dauer der Sitzung verarbeitet.
    """)
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

if st.button("🚀 Generierung starten", disabled=start_disabled, type="primary"):
    
    # Container for progress visualization
    progress_container = st.container()
    
    with progress_container:
        st.write("### 🔄 Verarbeitung läuft...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
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
             # Basic: CV -> Valid -> Word -> Dashboard
             visible_steps = [s for s in all_steps if s[0] in [1, 2, 3, 7]]
        elif mode == "Analyse & Matching":
             # Analysis: All except Offer(6)
             visible_steps = [s for s in all_steps if s[0] in [0, 1, 2, 3, 4, 5, 7]]
        else:
             # Full
             visible_steps = all_steps

        # Create placeholders for each step
        step_placeholders = {}
        for idx, label, icon in visible_steps:
            step_placeholders[idx] = st.empty()

        def render_step(idx, label, icon, status):
            # status: pending, running, completed
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
            
            # Use markdown to style
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

        # Initialize all steps as pending
        for idx, label, icon in visible_steps:
            render_step(idx, label, icon, "pending")

        def update_progress(percent, text, state):
            progress_bar.progress(percent)
            status_text.markdown(f"**{text}**")
            
            # Determine status for each step based on percentage
            # 10 -> Job Profile (Step 0)
            # 30 -> CV (Step 1)
            # 50 -> Validation (Step 2)
            # 70 -> Generation (Steps 3, 4, 5, 6)
            # 90 -> Dashboard (Step 7)
            # 100 -> Done
            
            for idx, label, icon in visible_steps:
                status = "pending"
                
                if percent >= 100:
                    status = "completed"
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
        
        # Determine if job file should be used
        use_job_file = job_file if mode != "Basic (Nur CV)" else None
        
        # Get custom styles from session state
        custom_styles = st.session_state.get("custom_styles")
        custom_logo_path = st.session_state.get("custom_logo_path")

        results = generator.run(
            cv_file=cv_file,
            job_file=use_job_file,
            api_key=api_key,
            progress_callback=update_progress,
            custom_styles=custom_styles,
            custom_logo_path=custom_logo_path
        )
        
        if results["success"]:
            # Mark all as completed
            for idx, label, icon in visible_steps:
                render_step(idx, label, icon, "completed")
                
            st.success("✅ Generierung erfolgreich abgeschlossen!")
            st.balloons()
            
            # Save to History
            history_entry = {
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "candidate_name": os.path.basename(results["cv_json"]).split('_')[1] + " " + os.path.basename(results["cv_json"]).split('_')[2] if results.get("cv_json") else "Unbekannt",
                "mode": mode,
                "word_path": results.get("word_path"),
                "cv_json": results.get("cv_json"),
                "dashboard_path": results.get("dashboard_path"),
                "match_score": results.get("match_score")
            }
            save_to_history(history_entry)
            
            # Display Results
            res_col1, res_col2, res_col3 = st.columns(3)
            
            with res_col1:
                if results["word_path"] and os.path.exists(results["word_path"]):
                    with open(results["word_path"], "rb") as f:
                        st.download_button(
                            label="📄 Word-CV herunterladen",
                            data=f,
                            file_name=os.path.basename(results["word_path"]),
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
            
            with res_col2:
                if results["cv_json"] and os.path.exists(results["cv_json"]):
                    with open(results["cv_json"], "rb") as f:
                        st.download_button(
                            label="📋 JSON-Daten herunterladen",
                            data=f,
                            file_name=os.path.basename(results["cv_json"]),
                            mime="application/json"
                        )

            with res_col3:
                if results["dashboard_path"] and os.path.exists(results["dashboard_path"]):
                    with open(results["dashboard_path"], "rb") as f:
                        st.download_button(
                            label="📊 Dashboard (HTML) herunterladen",
                            data=f,
                            file_name=os.path.basename(results["dashboard_path"]),
                            mime="text/html"
                        )

            # Show Match Score if available
            if results.get("match_score"):
                st.metric(label="Match Score", value=f"{results['match_score']}%")
                
            # Show Dashboard Preview
            if results["dashboard_path"] and os.path.exists(results["dashboard_path"]):
                st.subheader("Dashboard Vorschau")
                with open(results["dashboard_path"], "r", encoding='utf-8') as f:
                    html_content = f.read()
                    st.components.v1.html(html_content, height=800, scrolling=True)

        else:
            st.error(f"Fehler: {results['error']}")

