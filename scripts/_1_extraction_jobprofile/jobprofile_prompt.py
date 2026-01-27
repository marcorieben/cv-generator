"""
Job profile extraction prompt rules.

Consolidates all rules previously inline in jobprofile_extractor.py and jobprofile_schema.json.

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-27
Last Updated: 2026-01-27
"""
import json

from scripts._shared.prompt_rules import (
    COMMON_RULES,
    build_language_instruction,
)


# Jobprofile-specific extraction rules
JOBPROFILE_EXTRACTION_RULES = [
    "ANFORDERUNGEN: Jedes Kriterium als SEPARATEN Eintrag. Keine Zusammenfassungen.",
    "PRIORISIERUNG: Rollenbeschreibungen und Aufgaben über Marketingtext.",
    "LISTEN: Dokumentgranularität beibehalten, nicht konsolidieren.",
]


def build_jobprofile_system_prompt(schema: dict, target_language: str = "de", missing_marker: str = "! bitte prüfen !") -> str:
    """
    Build the system prompt for jobprofile extraction.

    Args:
        schema: The JSON schema dictionary (without _extraction_control)
        target_language: Target language code (de, en, fr)
        missing_marker: Marker for missing data

    Returns:
        The complete system prompt string
    """
    system_parts = [
        "Du bist ein Experte für die Analyse von IT-Projektangeboten und Stellenprofilen "
        "und arbeitest für eine IT-Beratungsfirma.",
        "",
        "Deine Aufgabe: Extrahiere alle Anforderungen und Rahmendaten aus dem bereitgestellten "
        "Stellenprofil und erstelle ein strukturiertes JSON gemäss dem folgenden Schema.",
        f"Zielsprache für die Extraktion ist: {target_language.upper()} "
        "(de=Deutsch, en=Englisch, fr=Französisch).",
        "",
        "WICHTIGE REGELN:",
    ]

    # Common rules
    rule_num = 1
    system_parts.append(f"{rule_num}. {COMMON_RULES['strict_schema']}")
    rule_num += 1
    system_parts.append(f'{rule_num}. {COMMON_RULES["missing_marker"].format(marker=missing_marker)}')
    rule_num += 1
    system_parts.append(f"{rule_num}. {COMMON_RULES['no_invention']}")
    rule_num += 1
    system_parts.append(f"{rule_num}. {COMMON_RULES['swiss_spelling']}")
    rule_num += 1
    system_parts.append(f"{rule_num}. {build_language_instruction(target_language)}")

    # Jobprofile-specific rules
    for rule in JOBPROFILE_EXTRACTION_RULES:
        rule_num += 1
        system_parts.append(f"{rule_num}. {rule}")

    # Schema
    system_parts.append("")
    system_parts.append("SCHEMA:")
    system_parts.append(json.dumps(schema, ensure_ascii=False, indent=2))
    system_parts.append("")
    system_parts.append("Antworte ausschliesslich mit dem validen JSON-Objekt gemäss diesem Schema.")

    return "\n".join(system_parts)


def build_jobprofile_user_prompt(text: str, target_language: str = "de") -> str:
    """
    Build the user prompt for jobprofile extraction.

    Args:
        text: The extracted text from the PDF
        target_language: Target language code

    Returns:
        The complete user prompt string
    """
    return f"Extrahiere die Stellenprofil-Daten (Zielsprache: {target_language.upper()}) aus folgendem Text:\n\n{text}"
