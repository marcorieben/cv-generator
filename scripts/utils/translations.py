"""
Shared translation utilities for the CV Generator project.

Purpose: Centralized translation loading and text retrieval
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-24
Last Updated: 2026-01-24
"""
import os
import json
from typing import Dict, Any, Optional

# Cache for loaded translations
_translations_cache: Optional[Dict[str, Any]] = None


def load_translations() -> Dict[str, Any]:
    """
    Loads translations from scripts/translations.json.

    Uses a module-level cache to avoid repeated file reads.

    Returns:
        Dict containing all translations, or empty dict if loading fails.
    """
    global _translations_cache

    if _translations_cache is not None:
        return _translations_cache

    # Try multiple possible paths to find translations.json
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "translations.json"),  # scripts/translations.json
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts", "translations.json"),  # From root
    ]

    for trans_path in possible_paths:
        if os.path.exists(trans_path):
            try:
                with open(trans_path, "r", encoding="utf-8") as f:
                    _translations_cache = json.load(f)
                    return _translations_cache
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load translations from {trans_path}: {e}")

    # Return empty dict if no translations found
    _translations_cache = {}
    return _translations_cache


def get_text(translations: Dict[str, Any], section: str, key: str, lang: str = "de") -> str:
    """
    Helper to get translated text from the translations dictionary.

    Args:
        translations: The translations dictionary (from load_translations())
        section: The section name (e.g., 'ui', 'cv', 'offer')
        key: The key within the section
        lang: The language code ('de', 'en', 'fr')

    Returns:
        The translated text, or the key wrapped in brackets if not found.
    """
    try:
        return translations.get(section, {}).get(key, {}).get(lang, f"[{key}]")
    except (AttributeError, TypeError):
        return f"[{key}]"


def clear_cache() -> None:
    """
    Clears the translations cache, forcing a reload on next access.
    Useful for testing or when translations file has been updated.
    """
    global _translations_cache
    _translations_cache = None
