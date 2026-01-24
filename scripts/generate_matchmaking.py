"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2025-12-24
Last Updated: 2026-01-24
"""
import os
import json
from openai import OpenAI
from datetime import datetime

try:
    from scripts.utils.translations import load_translations, get_text
except ImportError:
    from utils.translations import load_translations, get_text


def normalize_matching_values(data, language="de"):
    """
    Normalisiert die 'bewertung' Felder auf fix definierte, einheitliche Werte
    für alle Kriterientypen (Muss, Soll, Soft, Weitere).
    """
    translations = load_translations()
    
    # Target values in the selected language
    t_fulfilled = get_text(translations, 'status', 'fulfilled', language)
    t_partial = get_text(translations, 'status', 'partial', language)
    t_not_fulfilled = get_text(translations, 'status', 'not_fulfilled', language)
    t_potential = get_text(translations, 'status', 'potential', language)
    t_not_mentioned = get_text(translations, 'status', 'not_mentioned', language)

    # Dictionary mapping many variations to the target canonical value
    unified_map = {
        # German
        "erfüllt": t_fulfilled,
        "voll erfüllt": t_fulfilled,
        "ja": t_fulfilled,
        "teilweise": t_partial,
        "teilweise erfüllt": t_partial,
        "nicht erfüllt": t_not_fulfilled,
        "nein": t_not_fulfilled,
        "fehlt": t_not_fulfilled,
        "potenziell": t_potential,
        "potenziell erfüllt": t_potential,
        "implizit": t_potential,
        "nicht explizit": t_not_mentioned,
        "nicht explizit erwähnt": t_not_mentioned,
        "nicht erwähnt": t_not_mentioned,
        "neutral": t_not_mentioned,
        
        # English
        "fulfilled": t_fulfilled,
        "met": t_fulfilled,
        "yes": t_fulfilled,
        "partially": t_partial,
        "partially fulfilled": t_partial,
        "not fulfilled": t_not_fulfilled,
        "not met": t_not_fulfilled,
        "no": t_not_fulfilled,
        "missing": t_not_fulfilled,
        "potentially": t_potential,
        "potentially fulfilled": t_potential,
        "implicit": t_potential,
        "not explicitly mentioned": t_not_mentioned,
        "not mentioned": t_not_mentioned,

        # French
        "rempli": t_fulfilled,
        "satisfait": t_fulfilled,
        "oui": t_fulfilled,
        "partiellement": t_partial,
        "partiellement rempli": t_partial,
        "non rempli": t_not_fulfilled,
        "non satisfait": t_not_fulfilled,
        "non": t_not_fulfilled,
        "manquant": t_not_fulfilled,
        "potentiellement": t_potential,
        "potentiellement rempli": t_potential,
        "implicite": t_potential,
        "pas explicitement mentionné": t_not_mentioned,
        "pas mentionné": t_not_mentioned,
        
        "unklar": "! bitte prüfen !",
        "! bitte prüfen !": "! bitte prüfen !"
    }

    def get_normalized(val, mapping, default="! bitte prüfen !"):
        if not val or not isinstance(val, str):
            return default
        val_lower = val.lower().strip()
        for key, target in mapping.items():
            if key == val_lower or key in val_lower:
                return target
        return default

    # Verarbeite ALLE Listen mit der gleichen Logik
    sections = [
        "muss_kriterien_abgleich", 
        "soll_kriterien_abgleich", 
        "weitere_kriterien_abgleich",
        "soft_skills_abgleich"
    ]
    
    for section in sections:
        if section in data and isinstance(data[section], list):
            for item in data[section]:
                # 1. Konsistenzcheck: Wenn nichts gefunden wurde, kann es nicht 'erfüllt' sein
                found = item.get("im_cv_gefunden")
                found_bool = False
                if isinstance(found, bool):
                    found_bool = found
                elif isinstance(found, str):
                    found_bool = found.lower() in ["true", "ja", "yes", "vorhanden", "vrai"]
                
                # 2. Bestehende Bewertung normalisieren
                current_val = item.get("bewertung", "")
                normalized_val = get_normalized(current_val, unified_map, "! bitte prüfen !")
                
                # 3. Korrektur bei offensichtlicher Inkonsistenz
                if not found_bool and normalized_val == t_fulfilled:
                    if section != "soft_skills_abgleich":
                        normalized_val = t_not_fulfilled
                
                if not current_val or normalized_val == "! bitte prüfen !":
                    if section == "soft_skills_abgleich":
                        normalized_val = t_not_mentioned

                item["bewertung"] = normalized_val

    return data

def generate_matchmaking_json(cv_json_path, stellenprofil_json_path, output_path, schema_path, language="de"):
    """
    Generate a matchmaking JSON using the provided CV and Stellenprofil JSONs and the schema prompt.
    """
    translations = load_translations()
    
    # Load schema
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    # Load input data
    with open(cv_json_path, 'r', encoding='utf-8') as f:
        cv_data = json.load(f)
    with open(stellenprofil_json_path, 'r', encoding='utf-8') as f:
        stellenprofil_data = json.load(f)

    # Dictionary for language names
    lang_names = {
        "de": "Deutsch (Schweizer Rechtschreibung)",
        "en": "English",
        "fr": "Français"
    }
    lang_name = lang_names.get(language, "Deutsch")

    # Prepare prompt for OpenAI
    prompt_template = get_text(translations, 'system', 'matchmaking_prompt', language)
    system_prompt = prompt_template.replace("{lang_name}", lang_name) + "\n\n" + (
        "Schema (nur als Vorgabe, nicht ausgeben):\n" +
        json.dumps(schema, ensure_ascii=False, indent=2)
    )
    user_prompt = (
        "Stellenprofil JSON:\n" + json.dumps(stellenprofil_data, ensure_ascii=False, indent=2) +
        "\n\nCV JSON:\n" + json.dumps(cv_data, ensure_ascii=False, indent=2)
    )
    user_prompt = (
        "Stellenprofil JSON:\n" + json.dumps(stellenprofil_data, ensure_ascii=False, indent=2) +
        "\n\nCV JSON:\n" + json.dumps(cv_data, ensure_ascii=False, indent=2)
    )

    model_name = os.environ.get("MODEL_NAME", "gpt-4o-mini")
    
    if model_name == "mock":
        print("🧪 TEST-MODUS (Matchmaking): Verwende Mock-Daten")
        match_json = {
            "match_metadata": {
                "stellenprofil_vorhanden": True,
                "matching_datum": datetime.now().strftime("%Y-%m-%d")
            },
            "muss_kriterien_abgleich": [
                {
                    "kriterium": "Python Entwicklung",
                    "im_cv_gefunden": True,
                    "cv_evidenz": "5+ Jahre Python Erfahrung",
                    "bewertung": "erfüllt",
                    "kommentar": "Sehr gute Kenntnisse vorhanden."
                },
                {
                    "kriterium": "Cloud Erfahrung",
                    "im_cv_gefunden": True,
                    "cv_evidenz": "AWS Zertifizierung",
                    "bewertung": "erfüllt",
                    "kommentar": "Zertifiziert und Projekterfahrung."
                }
            ],
            "soll_kriterien_abgleich": [
                {
                    "kriterium": "Teamleitung",
                    "im_cv_gefunden": False,
                    "cv_evidenz": "",
                    "bewertung": "nicht erfüllt",
                    "kommentar": "Keine Führungserfahrung im CV gefunden."
                }
            ],
            "match_score": {
                "score_gesamt": 85,
                "gewichtung": {
                    "muss_kriterien": 90,
                    "soll_kriterien": 10
                }
            },
            "gesamt_fazit": {
                "empfehlung": "Go",
                "kurzbegruendung": "Mock-Matching: Der Kandidat erfüllt alle Muss-Kriterien und passt technisch sehr gut.",
                "naechste_schritte": ["Technisches Interview vereinbaren"]
            },
        }
    else:
        client = OpenAI()
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        match_json = json.loads(response.choices[0].message.content)
    
    # Normalisierung der Bewertungs-Werte
    match_json = normalize_matching_values(match_json, language=language)
    
    # Ensure matching_datum is set to current date
    if "match_metadata" in match_json:
        match_json["match_metadata"]["matching_datum"] = datetime.now().strftime("%Y-%m-%d")
        
    # Save result
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(match_json, f, ensure_ascii=False, indent=2)
    print(f"✅ Matchmaking JSON gespeichert: {output_path}")
    return match_json
