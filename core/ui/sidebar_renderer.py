"""
NEUE Sidebar Renderer - Vereinfacht für Option C (Custom HTML/CSS)

Nur die NEUEN Komponenten:
1. Language Selection (HTML/CSS)
2. Navigation Buttons (HTML/CSS)
3. Expander + Components (Streamlit)
4. User Info (Streamlit)
"""

import streamlit as st
import yaml
import os


def load_sidebar_config():
    """Laden der sidebar_config.yaml"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "scripts",
        "sidebar_config.yaml"
    )
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        st.error(f"Fehler beim Laden der Sidebar-Config: {e}")
        return None


def render_sidebar(
    config,
    get_text_func,
    language,
    show_model_settings_func,
    reset_pipeline_states_func,
    show_model_info_func,
    get_api_key_func,
    username,
    show_app_info_func,
    load_history_func,
    load_authenticator,
    load_password_reset_func,
    name
):
    """
    Rendert die komplette Sidebar mit Custom HTML/CSS für Navigation & Language
    """
    
    if not config:
        st.error("Sidebar-Konfiguration nicht verfügbar")
        return
    
    # ============ LANGUAGE SELECTION (HTML/CSS) ============
    _render_language_selection(get_text_func, language)
    
    st.divider()
    
    # ============ NAVIGATION BUTTONS (HTML/CSS) ============
    _render_navigation_buttons(config, get_text_func, language)
    
    st.divider()
    
    # ============ EXPANDERS & COMPONENTS (STREAMLIT) ============
    _render_settings_section(
        get_text_func, language,
        show_model_settings_func, reset_pipeline_states_func,
        show_model_info_func, get_api_key_func, username,
        show_app_info_func, load_history_func
    )
    
    st.divider()
    
    # ============ USER INFO & LOGOUT ============
    _render_user_section(
        get_text_func, language, 
        load_authenticator, load_password_reset_func, name
    )


def _render_language_selection(get_text_func, language):
    """Rendert Language Selection (DE/EN/FR) als HTML/CSS Custom Buttons"""
    
    current_lang = st.session_state.get("language", "de")
    
    # CSS für Language Buttons
    css = """
    <style>
    .lang-buttons {
        display: flex;
        gap: 8px;
        margin-bottom: 16px;
    }
    .lang-btn {
        flex: 1;
        padding: 8px 12px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-weight: bold;
        transition: background-color 0.2s;
        color: white;
    }
    .lang-btn.active {
        background-color: #FF7900;
    }
    .lang-btn.inactive {
        background-color: #444444;
    }
    .lang-btn:hover {
        opacity: 0.9;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    
    # Language Buttons
    lang_col1, lang_col2, lang_col3 = st.columns(3, gap="small")
    
    with lang_col1:
        if st.button("Deutsch", key="lang_de", use_container_width=True, type="primary" if current_lang == "de" else "secondary"):
            st.session_state.language = "de"
            st.rerun()
    
    with lang_col2:
        if st.button("English", key="lang_en", use_container_width=True, type="primary" if current_lang == "en" else "secondary"):
            st.session_state.language = "en"
            st.rerun()
    
    with lang_col3:
        if st.button("Français", key="lang_fr", use_container_width=True, type="primary" if current_lang == "fr" else "secondary"):
            st.session_state.language = "fr"
            st.rerun()


def _render_navigation_buttons(config, get_text_func, language):
    """Rendert Navigation Buttons (HTML/CSS) aus YAML"""
    
    current_page = st.session_state.get("current_page", "app.py")
    current_lang = st.session_state.get("language", "de")
    
    # Navigation Button Konfiguration mit translation keys
    nav_buttons = [
        ("ui", "nav_home", "app.py"),  # Home/Startseite
        ("ui", "sidebar_processes_profiles", "pages/01_Stellenprofile.py"),
        ("ui", "sidebar_processes_candidates", "pages/02_Kandidaten.py"),
        ("ui", "sidebar_processes_cv_generator", "pages/04_CV_Generator.py"),
    ]
    
    # Rendere jeden Button
    for section, key, page in nav_buttons:
        label = get_text_func(section, key, current_lang)
        is_active = page.lower() in current_page.lower() or current_page.lower() in page.lower()
        button_type = "primary" if is_active else "secondary"
        
        if st.button(label, use_container_width=True, key=f"nav_{page}", type=button_type):
            st.switch_page(page)


def _render_settings_section(
    get_text_func, language,
    show_model_settings_func, reset_pipeline_states_func,
    show_model_info_func, get_api_key_func, username,
    show_app_info_func, load_history_func
):
    """Rendert Settings Expanders"""
    
    # Settings
    with st.expander("⚙️ " + get_text_func("ui", "settings", language), expanded=False):
        st.caption(get_text_func('ui', 'design_desc', language))
        
        # Model Settings
        _render_model_settings(
            get_text_func, language,
            reset_pipeline_states_func, show_model_info_func,
            get_api_key_func, username
        )
        
        st.divider()
        
        # Design Settings
        _render_design_settings(get_text_func, language)
    
    # History
    with st.expander("📜 " + get_text_func("ui", "history", language), expanded=False):
        _render_history(get_text_func, language, load_history_func)
    
    # App Info
    with st.expander("ℹ️ " + get_text_func("ui", "app_info", language), expanded=False):
        st.caption(get_text_func("ui", "app_info_desc", language))
        if st.button(get_text_func("ui", "show_details", language), use_container_width=True):
            show_app_info_func()


def _render_model_settings(get_text_func, language, reset_pipeline_states_func, show_model_info_func, get_api_key_func, username):
    """Model Settings Komponente"""
    
    model_options = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "mock"]
    model_details = {
        "gpt-4o-mini": {"cost": "~$0.01", "rec": "✅ Empfohlen"},
        "gpt-4o": {"cost": "~$0.15", "rec": "💎 High-End"},
        "gpt-3.5-turbo": {"cost": "~$0.005", "rec": "⚠️ Legacy"},
        "mock": {"cost": "0.00", "rec": "🧪 Test"}
    }

    col_sel, col_info = st.columns([0.85, 0.15])
    with col_sel:
        selected_model = st.selectbox(
            get_text_func("ui", "select_model", language),
            options=model_options,
            index=0,
            key="model_selection_sidebar",
            format_func=lambda x: f"{x} ({model_details.get(x, {}).get('rec', '')})",
            on_change=reset_pipeline_states_func
        )
    with col_info:
        st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
        if st.button("ℹ️", key="model_info_btn"):
            show_model_info_func()

    details = model_details.get(selected_model, {})
    st.caption(f"💰 Kosten: **{details.get('cost')}** / Lauf | {details.get('rec')}")
    os.environ["MODEL_NAME"] = selected_model


def _render_design_settings(get_text_func, language):
    """Design Settings Komponente"""
    
    col1, col2 = st.columns(2)
    with col1:
        primary_color = st.color_picker(get_text_func('ui', 'primary_color', language), "#FF7900", key="primary_color_picker")
    with col2:
        secondary_color = st.color_picker(get_text_func('ui', 'secondary_color', language), "#444444", key="secondary_color_picker")
    
    # Speichere in session state
    st.session_state.custom_styles = {
        "primary_color": primary_color,
        "secondary_color": secondary_color
    }


def _render_history(get_text_func, language, load_history_func):
    """Rendert die History Section (aus alter Implementierung)"""
    from datetime import datetime
    
    history = load_history_func()
    
    if not history:
        st.caption(get_text_func("ui", "history_empty", language))
    else:
        for i, item in enumerate(history):
            timestamp = item.get("timestamp", "")
            try:
                dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                display_time = dt.strftime("%d.%m. %H:%M")
            except:
                display_time = timestamp

            candidate_name = item.get("candidate_name", get_text_func("ui", "history_unknown", language))

            with st.expander(f"{display_time} - {candidate_name}", expanded=False):
                model_used = item.get("model_name", get_text_func("ui", "history_unknown", language))
                st.caption(f"Modus: {item.get('mode')} | Modell: {model_used}")

                score = item.get("match_score")
                if score:
                    try:
                        score_val = float(score)
                        if score_val >= 80:
                            bar_color = "#27ae60"
                        elif score_val >= 60:
                            bar_color = "#f39c12"
                        else:
                            bar_color = "#c0392b"

                        st.markdown(f"""
                            <div style="margin-bottom: 5px; font-size: 0.8em; color: #666;">{get_text_func('dashboard', 'matching_score', language)}: {score}%</div>
                            <div style="background-color: #eee; border-radius: 4px; height: 8px; width: 100%; margin-bottom: 15px;">
                                <div style="background-color: {bar_color}; width: {score_val}%; height: 100%; border-radius: 4px;"></div>
                            </div>
                        """, unsafe_allow_html=True)
                    except:
                        pass

                # Details Button - zur Results-View navigieren
                if st.button(get_text_func('ui', 'history_details_btn', language), key=f"hist_btn_{timestamp}_{i}", use_container_width=True):
                    # Speichere die Run-Results in Session State
                    st.session_state.generation_results = item
                    st.session_state.show_results_view = True
                    st.session_state.show_results_view_requested = True  # Flag dass die Details explizit angefordert wurden
                    st.session_state.show_pipeline_dialog = True
                    # Navigiere zur CV_Generator Page
                    st.switch_page("pages/04_CV_Generator.py")


def _render_user_section(get_text_func, language, load_authenticator, load_password_reset_func, name):
    """User Info & Logout"""
    
    try:
        authenticator = load_authenticator()
        # Only show logout if authenticator exists and user is logged in
        if authenticator and name and name != "Guest":
            st.write(f'{get_text_func("ui", "welcome_msg", language)} *{name}*')
            try:
                authenticator.logout(get_text_func("ui", "logout_btn", language), 'sidebar')
            except Exception as logout_error:
                # If logout fails, just skip it silently
                pass
    except Exception as e:
        # Silently skip if there's any issue with authenticator
        pass
