"""
Matchmaking analysis prompt rules.

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


def build_matchmaking_system_prompt(schema: dict, language: str = "de") -> str:
    """
    Build the system prompt for matchmaking analysis.

    Uses the multilingual prompt template from translations.json.

    Args:
        schema: The JSON schema dictionary
        language: Target language code (de, en, fr)

    Returns:
        The complete system prompt string
    """
    lang_names = {
        "de": "Deutsch (Schweizer Rechtschreibung)",
        "en": "English",
        "fr": "Français"
    }
    lang_name = lang_names.get(language, "Deutsch")

    translations = load_translations()
    prompt_template = get_text(translations, 'system', 'matchmaking_prompt', language)

    system_prompt = prompt_template.replace("{lang_name}", lang_name) + "\n\n" + (
        "Schema (nur als Vorgabe, nicht ausgeben):\n" +
        json.dumps(schema, ensure_ascii=False, indent=2)
    )

    return system_prompt


def build_matchmaking_user_prompt(stellenprofil_data: dict, cv_data: dict) -> str:
    """
    Build the user prompt for matchmaking analysis.

    Args:
        stellenprofil_data: The job profile JSON data
        cv_data: The CV JSON data

    Returns:
        The complete user prompt string
    """
    return (
        "Stellenprofil JSON:\n" + json.dumps(stellenprofil_data, ensure_ascii=False, indent=2) +
        "\n\nCV JSON:\n" + json.dumps(cv_data, ensure_ascii=False, indent=2)
    )
