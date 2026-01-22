"""
Helper module to render sidebar in all pages
Ensures consistent sidebar across the entire application
"""

import streamlit as st
import yaml
import os
from core.ui.sidebar_renderer import load_sidebar_config, render_sidebar


def render_sidebar_in_page(
    get_text_func,
    language,
    authenticator=None,
    name=None,
    username=None,
    config=None
):
    """
    Renders the sidebar in any page.
    Call this function in the sidebar context of any page.
    
    Args:
        get_text_func: Function to get translated text
        language: Current language code
        authenticator: Streamlit authenticator instance
        name: User's display name
        username: User's username
        config: YAML config dict
    """
    with st.sidebar:
        # Logo (Top Left)
        if os.path.exists("templates/logo.png"):
            st.image("templates/logo.png", use_container_width=True)
        
        st.divider()
        
        # Load and render sidebar from config
        sidebar_config = load_sidebar_config()
        
        # Optional: Add manual reload button for testing
        if st.session_state.get("username") == "admin":
            if st.button("🔄 Sidebar neuladen", key="reload_sidebar_btn", use_container_width=False):
                st.rerun()
        
        if sidebar_config and authenticator and name and username:
            # Wrapper functions for components
            def show_model_settings_component(get_text_fn, lang, reset_fn, show_info_fn, get_key_fn, user):
                """This function is called by render_sidebar to display model settings"""
                pass
            
            def get_authenticator():
                return authenticator
            
            def reset_password_func(user, location):
                """Called by render_sidebar for password reset"""
                try:
                    if authenticator.reset_password(user, location):
                        st.success(get_text_func("ui", "password_changed", language))
                        if config:
                            with open('config.yaml', 'w') as file:
                                yaml.dump(config, file, default_flow_style=False)
                except Exception as e:
                    st.error(e)
            
            # Import functions from app.py context
            from app import (
                get_api_key,
                load_history,
                reset_all_pipeline_states,
                show_model_info_dialog,
                show_app_info_dialog
            )
            
            # Render sidebar
            render_sidebar(
                config=sidebar_config,
                get_text_func=get_text_func,
                language=language,
                show_model_settings_func=show_model_settings_component,
                reset_pipeline_states_func=reset_all_pipeline_states,
                show_model_info_func=show_model_info_dialog,
                get_api_key_func=get_api_key,
                username=username,
                show_app_info_func=show_app_info_dialog,
                load_history_func=load_history,
                load_authenticator=get_authenticator,
                load_password_reset_func=reset_password_func,
                name=name
            )
        else:
            if not sidebar_config:
                st.error("Sidebar-Konfiguration konnte nicht geladen werden")
