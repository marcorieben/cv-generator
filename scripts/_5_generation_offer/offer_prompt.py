"""
Offer generation prompt rules.

Consolidates all rules previously inline in offer_generator.py.
Uses hint extraction from schema for field-specific guidance.

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-27
Last Updated: 2026-01-27
"""
import json

from scripts._shared.prompt_rules import (
    extract_hints_from_schema,
    get_language_name,
)


# Offer-specific generation rules
OFFER_GENERATION_RULES = [
    "SPRACHE: Generiere alle Texte (Werte im JSON) konsequent in **{lang_name}**.",
    "TONALITÄT: Professionell, empathisch, überzeugend. "
    "Falls die Ausgabe in Deutsch erfolgt: Nutze Schweizer Rechtschreibung (ss statt ß).",
    "WIR-FORM: Verwende konsequent die 'Wir-Form' (Wir als Orange Business), niemals die 'Ich-Form'.",
    "STRIKT POSITIV: Alle Kriterien gelten als erfüllt. Weise NIEMALS auf Lücken, "
    "fehlende Erfahrung oder Defizite hin (NICHT: 'Trotz fehlender...', 'Obwohl XY nicht...'). "
    "Formuliere ausschliesslich Stärken und Übereinstimmungen.",
    "STRUKTUR: Gib ein JSON-Objekt mit exakt diesen Feldern zurück. "
    "Beachte dabei unbedingt die HINWEISE (Hints) für jedes Feld:",
]


def build_offer_system_prompt(schema: dict, language: str = "de") -> str:
    """
    Build the system prompt for offer generation.

    Uses hint extraction for field-specific guidance.

    Args:
        schema: The JSON schema dictionary
        language: Target language code (de, en, fr)

    Returns:
        The complete system prompt string
    """
    lang_name = get_language_name(language)

    system_parts = [
        f"Du bist ein Experte für die Erstellung von professionellen "
        f"IT-Dienstleistungsangeboten in **{lang_name}**. "
        f"Erstelle die qualitativen Abschnitte eines Angebots basierend auf "
        f"dem bereitgestellten Kontext in **{lang_name}**.",
        "",
        "WICHTIGE REGELN:",
    ]

    for i, rule in enumerate(OFFER_GENERATION_RULES, 1):
        system_parts.append(f"{i}. {rule.format(lang_name=lang_name)}")

    # Extract hints from schema
    schema_hints = extract_hints_from_schema(schema)

    # Inject hints into system prompt
    prompt_hints = {
        "kurzkontext": schema_hints.get("stellenbezug", {}).get(
            "kurzkontext", "Persönliche Einleitung."
        ),
        "eignungs_summary": schema_hints.get("kandidatenvorschlag", {}).get(
            "eignungs_summary", "Zusammenfassung der Eignung."
        ),
        "methoden_technologien": schema_hints.get("profil_und_kompetenzen", {}).get(
            "methoden_und_technologien", "Relevante Skills."
        ),
        "erfahrung_ops_führung": schema_hints.get("profil_und_kompetenzen", {}).get(
            "operative_und_fuehrungserfahrung", "Erfahrung in Betrieb/Führung."
        ),
        "zusammenfassung": schema_hints.get("gesamtbeurteilung", {}).get(
            "zusammenfassung", "Detaillierte Argumentation."
        ),
        "mehrwert": schema_hints.get("gesamtbeurteilung", {}).get(
            "mehrwert_fuer_kunden", "Impact-Punkte."
        ),
        "empfehlung": schema_hints.get("gesamtbeurteilung", {}).get(
            "empfehlung", "Kurze Empfehlung."
        ),
        "verfuegbarkeit_gespraech": schema_hints.get("abschluss", {}).get(
            "verfuegbarkeit_gespraech", "Gesprächsbereitschaft."
        ),
        "kontakt_hinweis": schema_hints.get("abschluss", {}).get(
            "kontakt_hinweis", "Rückmeldung."
        ),
    }

    for field, hint in prompt_hints.items():
        system_parts.append(f"   - '{field}': {hint}")

    system_parts.append("")
    system_parts.append(
        "WICHTIG: Nutze für Schlagworte, Technologien und wichtige Begriffe "
        "konsequent **Fettschrift**. Besonders im 'kurzkontext' sollen der Kundenname, "
        "die Rolle und 2-3 Kernkompetenzen fett markiert werden."
    )

    return "\n".join(system_parts)


def build_offer_user_prompt(llm_context: dict) -> str:
    """
    Build the user prompt for offer generation.

    Args:
        llm_context: The reduced context dictionary for LLM

    Returns:
        The complete user prompt string
    """
    return f"Kontext für die Angebotserstellung:\n{json.dumps(llm_context, ensure_ascii=False, indent=2)}"
