"""
Shared session management utilities for Streamlit pages.

Purpose: Centralized database and translations manager initialization
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-24
Last Updated: 2026-01-24
"""
import os
import streamlit as st
from pathlib import Path

from core.database.db import Database
from core.database.translations import initialize_translations


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def get_database() -> Database:
    """
    Get or create the database instance from session state.

    Returns:
        Database: The shared database instance.
    """
    if "db_instance" not in st.session_state:
        db_path = get_project_root() / "data" / "cv_generator.db"
        os.makedirs(db_path.parent, exist_ok=True)
        st.session_state.db_instance = Database(str(db_path))
    return st.session_state.db_instance


def get_translations_manager():
    """
    Get or initialize the translations manager from session state.

    Uses the shared database instance.

    Returns:
        TranslationsManager: The shared translations manager instance.
    """
    if "translations_manager" not in st.session_state:
        db = get_database()
        st.session_state.translations_manager = initialize_translations(db)
    return st.session_state.translations_manager


def get_text(section: str, key: str, lang: str = None) -> str:
    """
    Get translated text from the database-backed translations manager.

    Args:
        section: The translation section (e.g., 'ui', 'cv', 'offer')
        key: The translation key
        lang: The language code. If None, uses session state language.

    Returns:
        The translated text, or the key if not found.
    """
    if lang is None:
        lang = st.session_state.get("language", "de")
    try:
        tm = get_translations_manager()
        return tm.get(section, key, lang) or key
    except Exception:
        return key
