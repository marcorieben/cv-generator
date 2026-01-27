"""
Shared prompt rules and utilities for all LLM generation modules.

Contains common rules, helper functions for building prompts,
and schema hint extraction utilities.

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-27
Last Updated: 2026-01-27
"""


# Common rules applied to all LLM calls
COMMON_RULES = {
    "swiss_spelling": (
        "SCHWEIZER RECHTSCHREIBUNG: Ersetze jedes 'ss' statt 'ß'."
    ),
    "no_invention": (
        "Keine Informationen erfinden oder raten. "
        "Nur explizit im Dokument enthaltene Informationen verwenden."
    ),
    "missing_marker": (
        "Bei fehlenden oder unklaren Informationen exakt '{marker}' setzen."
    ),
    "strict_schema": (
        "Verwende NUR Felder, die im Schema definiert sind - KEINE zusätzlichen Felder. "
        "Halte dich strikt an die Feldnamen und Struktur des Schemas."
    ),
}


def get_missing_marker(language: str = "de") -> str:
    """Return the language-specific marker for missing data."""
    markers = {
        "de": "! bitte prüfen !",
        "en": "! please check !",
        "fr": "! à vérifier !"
    }
    return markers.get(language, markers["de"])


def get_language_name(language_code: str) -> str:
    """Return the full language name for a language code."""
    names = {
        "de": "Deutsch",
        "en": "English",
        "fr": "Français"
    }
    return names.get(language_code, "Deutsch")


def build_language_instruction(target_language: str) -> str:
    """Build the language instruction for the prompt."""
    lang_name = get_language_name(target_language)
    return (
        f"ZIELSPRACHE: Alle Inhalte konsequent in {lang_name} "
        "extrahieren/übersetzen. Fachbegriffe bleiben in Fachsprache."
    )


def extract_hints_from_schema(schema: dict, prefix: str = "_hint_") -> dict:
    """
    Extract all _hint_ fields from a schema recursively.

    Args:
        schema: The JSON schema dictionary
        prefix: The prefix identifying hint fields (default: "_hint_")

    Returns:
        Dictionary with extracted hints
    """
    hints = {}
    if isinstance(schema, dict):
        for key, value in schema.items():
            if key.startswith(prefix):
                field_name = key[len(prefix):]
                hints[field_name] = value
            elif isinstance(value, (dict, list)):
                nested = extract_hints_from_schema(value, prefix)
                if nested:
                    hints[key] = nested
    elif isinstance(schema, list):
        for item in schema:
            nested = extract_hints_from_schema(item, prefix)
            hints.update(nested)
    return hints


def build_common_rules_block(missing_marker: str) -> list:
    """
    Build the common rules as a numbered list of strings.

    Args:
        missing_marker: The marker string for missing data

    Returns:
        List of rule strings (without numbering)
    """
    return [
        COMMON_RULES["strict_schema"],
        COMMON_RULES["missing_marker"].format(marker=missing_marker),
        COMMON_RULES["no_invention"],
        COMMON_RULES["swiss_spelling"],
    ]
