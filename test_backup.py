"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-23
Last Updated: 2026-01-24
"""
import streamlit as st
import yaml
import os
from pathlib import Path


def load_sidebar_config():
    """Lädt die sidebar_config.yaml"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "scripts",
        "sidebar_config.yaml"
    )
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        st.warning(f"Konnte sidebar_config.yaml nicht laden: {e}")
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
    Rendert die Sidebar basierend auf der config
    
    Args:
        config: Geladene YAML config
        get_text_func: Funktion zum Übersetzen (get_text)
        language: Sprache (de/en/fr)
        Various component functions für die dynamische Rendering
    """
    
    if not config or "sidebar_structure" not in config:
        st.error("Sidebar-Config nicht verfügbar")
        return
    
    # Language Selection (Top of Sidebar)
    current_lang = st.session_state.get("language", "de")
    
    # Language buttons - with active/inactive coloring
    lang_col1, lang_col2, lang_col3 = st.columns(3, gap="small")
    
    with lang_col1:
        lang_type = "primary" if current_lang == "de" else "secondary"
        if st.button("DE", width="stretch", key="lang_de_sidebar", type=lang_type):
            st.session_state.language = "de"
            st.rerun()
    
    with lang_col2:
        lang_type = "primary" if current_lang == "en" else "secondary"
        if st.button("EN", width="stretch", key="lang_en_sidebar", type=lang_type):
            st.session_state.language = "en"
            st.rerun()
    
    with lang_col3:
        lang_type = "primary" if current_lang == "fr" else "secondary"
        if st.button("FR", width="stretch", key="lang_fr_sidebar", type=lang_type):
            st.session_state.language = "fr"
            st.rerun()
    
    st.divider()
    
    items = config["sidebar_structure"]
    
    # Render all top-level items
    for item in items:
        if item.get("hidden", False):
            continue
        
        _render_item(
            item,
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
        )


def _render_item(
    item,
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
    """Rendert ein einzelnes Item (rekursiv für children)"""
    
    item_type = item.get("type", "unknown")
    icon = item.get("icon", "")
    label_key = item.get("label_key")
    hidden = item.get("hidden", False)
    
    if hidden:
        return
    
    # Get label text
    if label_key:
        label = f"{icon} {get_text_func('ui', label_key, language)}".strip()
    else:
        label = icon.strip() if icon else ""
    
    # ============ RENDER BASED ON TYPE ============
    
    if item_type == "button":
        _render_button(item, label, get_text_func, language)
    
    elif item_type == "expander":
        _render_expander(
            item,
            label,
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
        )
    
    elif item_type == "divider":
        st.divider()
    
    elif item_type == "spacer":
        st.markdown("<div style='flex-grow: 1;'></div>", unsafe_allow_html=True)
    
    elif item_type == "custom":
        _render_custom_component(
            item,
            get_text_func,
            language,
            show_app_info_func,
            load_authenticator,
            load_password_reset_func,
            name
        )


def _render_button(item, label, get_text_func, language):
    """Rendert einen Button"""
    import streamlit as st
    
    action = item.get("action")
    key = item.get("key", f"btn_{id(item)}")
    page = item.get("page", "")
    
    # Alle Buttons sind secondary (grau)
    button_clicked = st.button(
        label,
        width="stretch",
        key=key,
        type="secondary"
    )
    
    if button_clicked:
        if action == "switch_page" and page:
            st.switch_page(page)


def _render_expander(
    item,
    label,
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
    """Rendert einen Expander mit (optionalen) Children"""
    
    expanded = item.get("expanded", False)
    component_name = item.get("component")
    children = item.get("children", [])
    
    with st.expander(label, expanded=expanded):
        # Render component if specified
        if component_name:
            _render_component(
                component_name,
                get_text_func,
                language,
                show_model_settings_func,
                reset_pipeline_states_func,
                show_model_info_func,
                get_api_key_func,
                username,
                load_history_func,
                load_authenticator,
                load_password_reset_func
            )
        
        # Render children
        for child in children:
            if child.get("hidden", False):
                continue
            _render_item(
                child,
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
            )


def _render_component(
    component_name,
    get_text_func,
    language,
    show_model_settings_func,
    reset_pipeline_states_func,
    show_model_info_func,
    get_api_key_func,
    username,
    load_history_func,
    load_authenticator,
    load_password_reset_func
):
    """Rendert eine Custom Component"""
    
    if component_name == "model_settings":
        _render_model_settings(
            get_text_func,
            language,
            reset_pipeline_states_func,
            show_model_info_func,
            get_api_key_func,
            username
        )
    
    elif component_name == "history_section":
        _render_history_component(get_text_func, language, load_history_func)
    
    elif component_name == "personal_settings":
        _render_personal_settings(
            get_text_func,
            language,
            load_authenticator,
            load_password_reset_func,
            username
        )
    
    elif component_name == "design_settings":
        _render_design_settings(get_text_func, language)


def _render_custom_component(
    item,
    get_text_func,
    language,
    show_app_info_func,
    load_authenticator,
    load_password_reset_func,
    name
):
    """Rendert eine vollständig Custom Component (Level 1)"""
    
    component_name = item.get("component")
    
    if component_name == "app_info_section":
        st.caption(get_text_func("ui", "app_info_desc", language))
        if st.button(get_text_func("ui", "show_details", language), width="stretch"):
            show_app_info_func()
    
    elif component_name == "user_info_logout":
        authenticator = load_authenticator()
        st.write(f'{get_text_func("ui", "welcome_msg", language)} *{name}*')
        authenticator.logout(get_text_func("ui", "logout_btn", language), 'sidebar')


# ============ COMPONENT IMPLEMENTATIONS ============

def _render_history_component(get_text_func, language, load_history_func):
    """Rendert die History Section"""
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

                if st.button(get_text_func('ui', 'history_details_btn', language), key=f"hist_btn_{timestamp}_{i}", width="stretch"):
                    st.session_state.generation_results = item
                    st.session_state.show_pipeline_dialog = True
                    st.session_state.show_results_view = True
                    st.rerun()


def _render_personal_settings(get_text_func, language, load_authenticator, load_password_reset_func, username):
    """Rendert Personal Settings"""
    try:
        authenticator = load_authenticator()
        if authenticator.reset_password(username, 'main'):
            st.success(get_text_func("ui", "password_changed", language))
    except Exception as e:
        st.error(e)


def _render_model_settings(get_text_func, language, reset_pipeline_states_func, show_model_info_func, get_api_key_func, username):
    """Rendert Model Settings Komponente"""
    
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
        if st.button("ℹ️", key="model_info_btn", help=get_text_func("ui", "model_info_btn_help", language)):
            show_model_info_func()

    details = model_details.get(selected_model, {})
    st.caption(f"💰 Kosten: **{details.get('cost')}** / Lauf | {details.get('rec')}")
    os.environ["MODEL_NAME"] = selected_model
    
    if selected_model == "mock":
        st.info("🧪 Test-Modus aktiv: Es werden keine echten API-Calls gemacht.")
    
    st.caption(f"Aktueller Modus: {os.getenv('CV_GENERATOR_MODE', 'full')}")

    if username == 'admin':
        st.divider()
        api_key = get_api_key_func()
        if not api_key:
            st.warning("Kein API Key gefunden!")
            user_key = st.text_input("OpenAI API Key eingeben:", type="password")
            if user_key:
                st.session_state.api_key = user_key
                st.rerun()
        else:
            st.success(get_text_func("ui", "api_key_active", language))
            if not os.getenv("OPENAI_API_KEY") and "OPENAI_API_KEY" not in st.secrets:
                if st.button(get_text_func("ui", "change_api_key", language)):
                    if "api_key" in st.session_state:
                        del st.session_state.api_key
                    st.rerun()
        
        st.caption(f"{get_text_func('ui', 'current_mode', language)}: {os.getenv('CV_GENERATOR_MODE', 'full')}")


def _render_design_settings(get_text_func, language):
    """Rendert Design Settings"""
    import os
    
    st.caption(get_text_func('ui', 'design_desc', language))
    
    # Farbauswahl
    col1, col2 = st.columns(2)
    with col1:
        primary_color = st.color_picker(get_text_func('ui', 'primary_color', language), "#FF7900")
    with col2:
        secondary_color = st.color_picker(get_text_func('ui', 'secondary_color', language), "#444444")
    
    # Visuelle Indikatoren für aktive/inaktive Farben
    indicator_col1, indicator_col2 = st.columns(2)
    with indicator_col1:
        st.markdown(f"""
            <div style='
                padding: 10px;
                border-radius: 5px;
                background-color: {primary_color};
                color: white;
                text-align: center;
                font-weight: bold;
            '>
                ● AKTIV (Primary)
            </div>
        """, unsafe_allow_html=True)
    with indicator_col2:
        st.markdown(f"""
            <div style='
                padding: 10px;
                border-radius: 5px;
                background-color: {secondary_color};
                color: white;
                text-align: center;
                font-weight: bold;
            '>
                ○ INAKTIV (Secondary)
            </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    font_options = ["Aptos", "Arial", "Calibri", "Helvetica", "Times New Roman"]
    selected_font = st.selectbox(get_text_func('ui', 'font_label', language), font_options, index=0)
    
    uploaded_logo = st.file_uploader(get_text_func('ui', 'logo_label', language), type=["png", "jpg", "jpeg"])
    if uploaded_logo:
        os.makedirs("input/logos", exist_ok=True)
        logo_path = os.path.join("input", "logos", "custom_logo.png")
        with open(logo_path, "wb") as f:
            f.write(uploaded_logo.getbuffer())
        st.session_state.custom_logo_path = logo_path
    
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
        
        html, body, [class*="css"] {{
            font-family: '{selected_font}', sans-serif !important;
        }}
        
        h1 {{ color: {primary_color} !important; font-family: '{selected_font}', sans-serif !important; }}
        h2, h3 {{ color: {secondary_color} !important; font-family: '{selected_font}', sans-serif !important; }}
        
        .stButton>button {{
            background-color: {primary_color} !important;
            color: white !important;
            border: none;
            font-family: '{selected_font}', sans-serif !important;
        }}
        </style>
    """, unsafe_allow_html=True)
    
    st.session_state.custom_styles = {
        "primary_color": primary_color,
        "secondary_color": secondary_color,
        "font": selected_font
    }
