"""
CV feedback generation prompt rules.

Wraps the existing translations-based prompt and provides a clean interface.

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-27
Last Updated: 2026-01-27
"""
import json

try:
    from scripts.utils.translations import load_translations, get_text
except ImportError:
    from utils.translations import load_translations, get_text


def build_feedback_system_prompt(schema: dict, language: str = "de") -> str:
    """
    Build the system prompt for CV feedback generation.

    Uses the multilingual prompt template from translations.json.

    Args:
        schema: The JSON schema dictionary
        language: Target language code (de, en, fr)

    Returns:
        The complete system prompt string
    """
    language_map = {
        "de": "Deutsch (Schweizer Rechtschreibung)",
        "en": "English",
        "fr": "Français"
    }
    target_language = language_map.get(language, language)

    translations = load_translations()
    prompt_template = get_text(translations, 'system', 'feedback_prompt', language)

    system_prompt = prompt_template.replace("{target_language}", target_language) + "\n" + (
        "Schema (nur als Vorgabe, nicht ausgeben):\n" +
        json.dumps(schema, ensure_ascii=False, indent=2)
    )

    return system_prompt


def build_feedback_user_prompt(cv_data: dict, stellenprofil_data: dict = None) -> str:
    """
    Build the user prompt for CV feedback generation.

    Args:
        cv_data: The CV JSON data
        stellenprofil_data: Optional job profile JSON data

    Returns:
        The complete user prompt string
    """
    user_prompt = "CV JSON:\n" + json.dumps(cv_data, ensure_ascii=False, indent=2)

    if stellenprofil_data:
        user_prompt += "\n\nStellenprofil JSON:\n" + json.dumps(stellenprofil_data, ensure_ascii=False, indent=2)

    return user_prompt
