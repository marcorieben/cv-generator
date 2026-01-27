"""
CV extraction prompt rules.

Consolidates all rules previously inline in cv_extractor.py and cv_schema.json.

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


# CV-specific extraction rules
CV_EXTRACTION_RULES = [
    # Sprachen
    (
        "SPRACHEN: Level 1-5 numerisch. Normalisiere unterschiedliche Skalen:\n"
        "   - WICHTIG: Wenn grafische Elemente (Sterne, Punkte, Balken) vorhanden sind, "
        "haben diese VORRANG vor Textbeschreibungen. Zähle die vollen Sterne/Punkte.\n"
        "   - 5er-Skala (Standard): 1=1, ..., 5=5\n"
        "   - 3er-Skala: 1=1 (Grundkenntnisse), 2=3 (Gut), 3=5 (Exzellent/Muttersprache)\n"
        "   - 4er-Skala: 1=1, 2=2, 3=4, 4=5\n"
        "   - Text (A1-C2): A1/A2=1, B1=2, B2=3, C1=4, C2=5\n"
        "   Sortiere absteigend nach Level."
    ),
    # Referenzprojekte
    (
        "REFERENZPROJEKTE: Erfasse VOLLSTÄNDIG ALLE beruflichen Stationen aus dem gesamten Lebenslauf.\n"
        "   - 'Ausgewählte_Referenzprojekte' muss ALLE Stationen enthalten (nicht nur eine Auswahl).\n"
        "   - Jede Station als eigenes Objekt.\n"
        "   - TÄTIGKEITEN: Erfasse WÖRTLICH und VOLLSTÄNDIG, keine Kürzungen."
    ),
    # Fachwissen
    (
        "WICHTIG: Fachwissen_und_Schwerpunkte hat IMMER genau 3 Kategorien:\n"
        '   1. "Projektmethodik" (Scrum, SAFe, HERMES, Kanban, etc.)\n'
        '   2. "Tech Stack" (Technologien, Tools, Sprachen)\n'
        '   3. "Weitere Skills" (Soft Skills, Domain-Wissen)\n'
        '   Verwende "Inhalt" (NICHT "BulletList"), direkt auf oberster Ebene (NICHT in "Expertise").'
    ),
    # Zertifikate
    "ALLE ZERTIFIKATE ERFASSEN: Ausnahmslos JEDES Zertifikat und Training. Keine Auslassungen.",
    # Kurzprofil
    "KURZPROFIL: 50-100 Wörter, 3. Person mit Vornamen. Nur belegbare Stärken, keine Übertreibungen.",
    # Rolle
    "ROLLE in Referenzprojekten: Maximal 8 Wörter, kurz und prägnant.",
    # Zeitformate
    (
        "ZEITFORMATE: MM/YYYY. Ausnahme: 'Aus_und_Weiterbildung' sowie "
        "'Trainings_und_Zertifizierungen' nur YYYY."
    ),
]


def build_cv_system_prompt(schema: dict, target_language: str = "de", missing_marker: str = "! bitte prüfen !") -> str:
    """
    Build the system prompt for CV extraction.

    Args:
        schema: The JSON schema dictionary (without _extraction_control)
        target_language: Target language code (de, en, fr)
        missing_marker: Marker for missing data

    Returns:
        The complete system prompt string
    """
    system_parts = [
        "Du bist ein Experte für CV-Extraktion und arbeitest für eine IT-Beratungsfirma.",
        "",
        "Deine Aufgabe: Extrahiere alle Informationen aus dem bereitgestellten CV-Text "
        "und erstelle ein strukturiertes JSON gemäss dem folgenden Schema.",
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

    # CV-specific rules
    for rule in CV_EXTRACTION_RULES:
        rule_num += 1
        system_parts.append(f"{rule_num}. {rule}")

    # Schema (without _extraction_control, only structure + hints)
    system_parts.append("")
    system_parts.append("SCHEMA:")
    system_parts.append(json.dumps(schema, ensure_ascii=False, indent=2))
    system_parts.append("")
    system_parts.append("Antworte ausschliesslich mit dem validen JSON-Objekt gemäss diesem Schema.")

    return "\n".join(system_parts)


def build_cv_user_prompt(cv_text: str, target_language: str = "de", job_profile_context: dict = None) -> str:
    """
    Build the user prompt for CV extraction.

    Args:
        cv_text: The extracted text from the PDF
        target_language: Target language code
        job_profile_context: Optional job profile data for context

    Returns:
        The complete user prompt string
    """
    user_content = f"Extrahiere die CV-Daten (Zielsprache: {target_language.upper()}) aus folgendem Text:\n\n{cv_text}"

    if job_profile_context:
        user_content = (
            f"KONTEXT (Ziel-Stellenprofil):\n{json.dumps(job_profile_context, ensure_ascii=False)}\n\n"
            "Nutze diesen Kontext, um im CV besonders auf relevante Erfahrungen, "
            "Zertifikate und Skills zu achten, die für dieses Profil gefordert sind. "
            "Die Extraktion bleibt faktenbasiert auf dem CV-Text.\n\n"
            + user_content
        )

    return user_content
