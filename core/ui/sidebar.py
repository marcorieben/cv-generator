"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-23
Last Updated: 2026-01-24
"""
import streamlit as st
import os
from pathlib import Path


def init_sidebar(translations_manager=None, language="de"):
    """
    Initialize sidebar with navigation and settings
    
    Args:
        translations_manager: TranslationsManager instance for translations
        language: Current language code (de, en, fr)
    """
    
    # Helper function to get text
    def get_text(section, key, lang=None):
        if lang is None:
            lang = language
        if translations_manager:
            return translations_manager.get(section, key, lang) or key
        return key
    
    with st.sidebar:
        # Language Selector (Top)
        st.write(f"**{get_text('ui', 'language_label', language)}:**")
        lang_cols = st.columns(3)
        
        lang_changed = False
        if lang_cols[0].button("DE", use_container_width=True, 
                               type="primary" if language == "de" else "secondary", key="lang_de"):
            st.session_state.language = "de"
            lang_changed = True
            
        if lang_cols[1].button("EN", use_container_width=True,
                               type="primary" if language == "en" else "secondary", key="lang_en"):
            st.session_state.language = "en"
            lang_changed = True
            
        if lang_cols[2].button("FR", use_container_width=True,
                               type="primary" if language == "fr" else "secondary", key="lang_fr"):
            st.session_state.language = "fr"
            lang_changed = True
        
        if lang_changed:
            st.rerun()
        
        st.divider()
        
        # --- Main Menu: Processes (Level 1) ---
        st.markdown(f"#### {get_text('ui', 'sidebar_processes', language)}")
        
        # Create menu buttons vertically
        if st.button(
            get_text('ui', 'sidebar_processes_profiles', language),
            use_container_width=True,
            key="nav_job_profiles",
            help="Manage job profile requirements"
        ):
            st.switch_page("pages/01_Stellenprofile.py")
        
        if st.button(
            get_text('ui', 'sidebar_processes_candidates', language),
            use_container_width=True,
            key="nav_candidates",
            help="Manage candidate information"
        ):
            st.switch_page("pages/02_Kandidaten.py")
        
        if st.button(
            get_text('ui', 'sidebar_processes_cv_generator', language),
            use_container_width=True,
            key="nav_cv_gen",
            help="Generate CVs with multiple modes"
        ):
            st.switch_page("pages/04_CV_Generator.py")
        
        if st.button(
            get_text('ui', 'sidebar_processes_status', language),
            use_container_width=True,
            key="nav_status",
            help="Track workflow status"
        ):
            st.switch_page("pages/03_Stellenprofil-Status.py")
        
        st.divider()
        
        # --- Settings Section (Level 1) ---
        st.markdown(f"#### {get_text('ui', 'sidebar_title', language)}")
        
        # Settings are typically handled in main app.py
        # This function focuses on navigation
        
        # Logout button at bottom
        with st.container():
            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True, key="sidebar_logout"):
                # Logout logic handled in main app
                pass


def render_language_selector(language="de"):
    """
    Standalone language selector component
    Can be used in pages that don't have full sidebar access
    
    Args:
        language: Current language code
    
    Returns:
        Selected language code
    """
    cols = st.columns(3)
    
    if cols[0].button("DE", use_container_width=True, 
                      type="primary" if language == "de" else "secondary"):
        return "de"
    
    if cols[1].button("EN", use_container_width=True,
                      type="primary" if language == "en" else "secondary"):
        return "en"
    
    if cols[2].button("FR", use_container_width=True,
                      type="primary" if language == "fr" else "secondary"):
        return "fr"
    
    return language
