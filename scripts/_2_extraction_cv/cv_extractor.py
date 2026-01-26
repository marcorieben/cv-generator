"""
CV Extraction - PDF to structured JSON.

Extracts CV data from PDF using OpenAI API and normalizes the structure.

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-26
Last Updated: 2026-01-26
"""
import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

from scripts._shared.pdf_utils import extract_text_from_pdf
from scripts._shared.date_utils import normalize_date_format
from scripts.utils.translations import load_translations, get_text


def load_schema(schema_path):
    """
    Lädt ein JSON-Schema.

    Args:
        schema_path: Absoluter oder relativer Pfad zur Schema-Datei

    Returns:
        Dictionary mit dem Schema
    """
    # Wenn der Pfad bereits absolut ist, direkt verwenden
    if os.path.isabs(schema_path):
        full_path = schema_path
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(base_dir, schema_path)

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Schema nicht gefunden: {full_path}")

    with open(full_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def normalize_json_structure(data, language="de"):
    """
    Korrigiert verschachtelte Strukturen von OpenAI zum erwarteten Format.
    """
    translations = load_translations()
    missing_marker = get_text(translations, "system", "missing_data_marker", language)

    # Korrektur 0: Hauptausbildung -> Ausbildung
    if "Hauptausbildung" in data and "Ausbildung" not in data:
        data["Ausbildung"] = data["Hauptausbildung"]
        del data["Hauptausbildung"]

    # Korrektur 1: Expertise -> Fachwissen_und_Schwerpunkte
    if "Expertise" in data and isinstance(data["Expertise"], dict):
        if "Fachwissen_und_Schwerpunkte" in data["Expertise"]:
            data["Fachwissen_und_Schwerpunkte"] = data["Expertise"]["Fachwissen_und_Schwerpunkte"]
            del data["Expertise"]

    # Korrektur 2: BulletList -> Inhalt
    if "Fachwissen_und_Schwerpunkte" in data and isinstance(data["Fachwissen_und_Schwerpunkte"], list):
        for item in data["Fachwissen_und_Schwerpunkte"]:
            if "BulletList" in item and "Inhalt" not in item:
                item["Inhalt"] = item["BulletList"]
                del item["BulletList"]

    # Korrektur 2b: Erzwinge feste 3-Kategorien Struktur
    if "Fachwissen_und_Schwerpunkte" in data and isinstance(data["Fachwissen_und_Schwerpunkte"], list):
        skills = data["Fachwissen_und_Schwerpunkte"]

        projektmethodik_items = []
        tech_stack_items = []
        weitere_skills_items = []

        projektmethodik_keywords = ['projekt', 'methodik', 'methodologie', 'agil', 'agile', 'scrum', 'hermes', 'safe', 'kanban', 'waterfall']
        tech_keywords = ['tech', 'stack', 'tool', 'technolog', 'plattform', 'framework', 'sprach', 'databa', 'cloud',
                         'analytic', 'data', 'bi', 'microsoft', 'office', 'collaboration', 'software',
                         'python', 'java', 'sql', 'web', 'app', 'system', 'server']

        for item in skills:
            kategorie_lower = item.get("Kategorie", "").lower()
            inhalt = item.get("Inhalt", [])

            if any(kw in kategorie_lower for kw in projektmethodik_keywords):
                projektmethodik_items.extend(inhalt)
            elif any(kw in kategorie_lower for kw in tech_keywords):
                tech_stack_items.extend(inhalt)
            else:
                methoden_in_content = any(
                    any(method in str(i).lower() for method in ['scrum', 'agile', 'hermes', 'safe', 'kanban', 'waterfall'])
                    for i in inhalt
                )
                if methoden_in_content:
                    projektmethodik_items.extend(inhalt)
                else:
                    weitere_skills_items.extend(inhalt)

        if not projektmethodik_items:
            projektmethodik_items = [missing_marker]
        if not tech_stack_items:
            tech_stack_items = [missing_marker]
        if not weitere_skills_items:
            weitere_skills_items = [missing_marker]

        data["Fachwissen_und_Schwerpunkte"] = [
            {"Kategorie": get_text(translations, "skills_categories", "methodology", language), "Inhalt": projektmethodik_items},
            {"Kategorie": get_text(translations, "skills_categories", "tech_stack", language), "Inhalt": tech_stack_items},
            {"Kategorie": get_text(translations, "skills_categories", "other_skills", language), "Inhalt": weitere_skills_items}
        ]

    # Korrektur 3: Verschachtelte Referenzprojekte
    if "Ausgewählte_Referenzprojekte" in data and isinstance(data["Ausgewählte_Referenzprojekte"], dict):
        if "Referenzprojekte" in data["Ausgewählte_Referenzprojekte"]:
            data["Ausgewählte_Referenzprojekte"] = data["Ausgewählte_Referenzprojekte"]["Referenzprojekte"]

    # Korrektur 4: Normalisiere Zeitformate
    if "Aus_und_Weiterbildung" in data and isinstance(data["Aus_und_Weiterbildung"], list):
        for item in data["Aus_und_Weiterbildung"]:
            if "Zeitraum" in item and isinstance(item["Zeitraum"], str):
                norm = normalize_date_format(item["Zeitraum"])
                item["Zeitraum"] = re.sub(r'\d{2}/(\d{4})', r'\1', norm)

    if "Trainings_und_Zertifizierungen" in data and isinstance(data["Trainings_und_Zertifizierungen"], list):
        for item in data["Trainings_und_Zertifizierungen"]:
            if "Zeitraum" in item and isinstance(item["Zeitraum"], str):
                norm = normalize_date_format(item["Zeitraum"])
                item["Zeitraum"] = re.sub(r'\d{2}/(\d{4})', r'\1', norm)

    if "Ausgewählte_Referenzprojekte" in data and isinstance(data["Ausgewählte_Referenzprojekte"], list):
        for item in data["Ausgewählte_Referenzprojekte"]:
            if "Zeitraum" in item:
                item["Zeitraum"] = normalize_date_format(item["Zeitraum"])

    # Korrektur 5: Normalisiere Sprachen Level und Namen
    if "Sprachen" in data and isinstance(data["Sprachen"], list):
        if language == "en":
            language_mapping = {
                "english": "English", "german": "German", "french": "French",
                "italian": "Italian", "spanish": "Spanish", "portuguese": "Portuguese",
                "russian": "Russian", "chinese": "Chinese", "japanese": "Japanese"
            }
        elif language == "fr":
            language_mapping = {
                "english": "Anglais", "german": "Allemand", "french": "Français",
                "italian": "Italien", "spanish": "Espagnol", "portuguese": "Portugais",
                "russian": "Russe", "chinese": "Chinois", "japanese": "Japonais"
            }
        else:
            language_mapping = {
                "english": "Englisch", "german": "Deutsch", "french": "Französisch",
                "italian": "Italienisch", "spanish": "Spanisch", "portuguese": "Portugiesisch",
                "russian": "Russisch", "chinese": "Chinesisch", "japanese": "Japanisch"
            }

        for item in data["Sprachen"]:
            if "Sprache" in item and isinstance(item["Sprache"], str):
                lang_lower = item["Sprache"].lower().strip()
                if lang_lower in language_mapping:
                    item["Sprache"] = language_mapping[lang_lower]
                elif any(k in lang_lower for k in language_mapping):
                    for k, v in language_mapping.items():
                        if k in lang_lower:
                            item["Sprache"] = v
                            break

            if "Level" in item:
                level = item["Level"]
                if isinstance(level, str):
                    if "★" in level or "*" in level:
                        count = level.count("★") + level.count("*")
                        if count > 0:
                            item["Level"] = min(count, 5)
                    elif re.search(r'\b[1-5]\s*/\s*5', level) or re.match(r'^\s*[1-5]\s*$', level):
                        match = re.search(r'([1-5])', level)
                        if match:
                            item["Level"] = int(match.group(1))
                    elif level.lower() in ["muttersprache", "native", "native speaker"]:
                        item["Level"] = 5
                    elif any(x in level.lower() for x in ["verhandlungssicher", "fluent", "business fluent", "c2", "c1"]):
                        item["Level"] = 4
                    elif any(x in level.lower() for x in ["sehr gute kenntnisse", "very good", "proficient", "b2"]):
                        item["Level"] = 3
                    elif any(x in level.lower() for x in ["gute kenntnisse", "good", "intermediate", "b1"]):
                        item["Level"] = 2
                    elif any(x in level.lower() for x in ["grundkenntnisse", "basic", "beginner", "a1", "a2"]):
                        item["Level"] = 1

    return data


def extract_cv(pdf_path, output_path=None, schema_path=None, job_profile_context=None, target_language="de"):
    """
    Extrahiert CV-Daten aus PDF via OpenAI API.

    Args:
        pdf_path: Pfad zur PDF-Datei oder Streamlit UploadedFile
        output_path: Optionaler Pfad für JSON-Output
        schema_path: Pfad zur Schema-Datei (default: cv_schema.json im selben Ordner)
        job_profile_context: Optionales Dict mit Stellenprofildaten
        target_language: Zielsprache (de, en, fr)

    Returns:
        Dictionary mit den extrahierten CV-Daten
    """
    if pdf_path is None:
        raise ValueError("PDF-Datei ist leer (None). Bitte laden Sie eine gültige PDF-Datei hoch.")

    load_dotenv()

    # Default schema path
    if schema_path is None:
        schema_path = os.path.join(os.path.dirname(__file__), "cv_schema.json")

    model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
    if model_name == "mock":
        print("TEST-MODUS AKTIV: Verwende Mock-Daten (keine API-Kosten)")
        import time
        time.sleep(2)

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        fixture_path = os.path.join(base_dir, "tests", "2_extraction_cv", "fixtures", "valid_cv.json")
        if not os.path.exists(fixture_path):
            # Fallback: alte Position
            fixture_path = os.path.join(base_dir, "tests", "fixtures", "valid_cv.json")

        if os.path.exists(fixture_path):
            with open(fixture_path, 'r', encoding='utf-8') as f:
                mock_data = json.load(f)
        else:
            mock_data = {"Vorname": "Max", "Nachname": "Mustermann", "Mock": True}

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(mock_data, f, ensure_ascii=False, indent=2)
            print(f"Mock-JSON gespeichert: {output_path}")

        return mock_data

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OpenAI API Key nicht gefunden!\n"
            "Bitte erstellen Sie eine .env Datei mit:\n"
            "OPENAI_API_KEY=sk-proj-your-key-here"
        )

    filename = os.path.basename(pdf_path) if isinstance(pdf_path, str) else "Uploaded File"
    print(f"Lese PDF: {filename}")
    cv_text = extract_text_from_pdf(pdf_path)
    print(f"   -> {len(cv_text)} Zeichen extrahiert")

    print("Lade Schema...")
    schema = load_schema(schema_path)

    print("Sende Anfrage an OpenAI API...")
    client = OpenAI(api_key=api_key)

    translations = load_translations()
    missing_marker = get_text(translations, "system", "missing_data_marker", target_language)

    system_prompt = f"""Du bist ein Experte für CV-Extraktion und arbeitest für eine IT-Beratungsfirma.

Deine Aufgabe: Extrahiere alle Informationen aus dem bereitgestellten CV-Text und erstelle ein strukturiertes JSON gemäss dem folgenden Schema.
Zielsprache für die Extraktion ist: {target_language.upper()} (de=Deutsch, en=Englisch, fr=Französisch).

WICHTIGE REGELN:
1. Verwende NUR Felder, die im Schema definiert sind - KEINE zusätzlichen Felder
2. Bei fehlenden Informationen: Markiere mit "{missing_marker}"
3. Keine Informationen erfinden oder raten
4. Halte dich strikt an die Feldnamen und Struktur des Schemas
5. Sprachen: Level 1-5 numerisch. Normalisiere unterschiedliche Skalen auf 1-5:
   - WICHTIG: Wenn grafische Elemente (Sterne, Punkte, Balken) vorhanden sind, haben diese VORRANG vor Textbeschreibungen.
   - Zähle die vollen Sterne/Punkte.
   - 5er-Skala (Standard): 1=1, ..., 5=5
   - 3er-Skala: 1=1 (Grundkenntnisse), 2=3 (Gut), 3=5 (Exzellent/Muttersprache)
   - 4er-Skala: 1=1, 2=2, 3=4, 4=5
   - Text (A1-C2): A1/A2=1, B1=2, B2=3, C1=4, C2=5
   Sortiere absteigend nach Level.
6. REFERENZPROJEKTE: Erfasse VOLLSTÄNDIG ALLE beruflichen Stationen aus dem gesamten Lebenslauf.
   - 'Ausgewählte_Referenzprojekte' muss ALLE Stationen enthalten (nicht nur eine Auswahl).
   - Jede Station als eigenes Objekt.
   - TÄTIGKEITEN: Erfasse WÖRTLICH und VOLLSTÄNDIG, keine Kürzungen.
7. WICHTIG: Verwende "Inhalt" (NICHT "BulletList") für Fachwissen_und_Schwerpunkte
8. WICHTIG: Fachwissen_und_Schwerpunkte ist direkt auf oberster Ebene (NICHT in "Expertise" verschachtelt)
9. WICHTIG: Fachwissen_und_Schwerpunkte hat IMMER genau 3 Kategorien:
   - 1. "Projektmethodik"
   - 2. "Tech Stack"
   - 3. "Weitere Skills"
10. ZEITFORMATE: MM/YYYY. Ausnahme: "Aus_und_Weiterbildung" sowie "Trainings_und_Zertifizierungen" nur YYYY.
11. ALLE ZERTIFIKATE ERFASSEN: Ausnahmslos JEDES Zertifikat und Training.
12. KURZPROFIL: Vornamen verwenden, 3. Person, sachlich. 50-100 Wörter.
13. ROLLE in Referenzprojekten: Maximal 8 Wörter.
14. SCHWEIZER RECHTSCHREIBUNG: Ersetze jedes 'ss' statt 'ß'.
15. ZIELSPRACHE: Alle Inhalte konsequent in {target_language.upper()} extrahieren/übersetzen. Fachbegriffe bleiben in Fachsprache.

SCHEMA:
{json.dumps(schema, ensure_ascii=False, indent=2)}

Antworte ausschliesslich mit dem validen JSON-Objekt gemäss diesem Schema."""

    user_content = f"Extrahiere die CV-Daten (Zielsprache: {target_language.upper()}) aus folgendem Text:\n\n{cv_text}"

    if job_profile_context:
        user_content = (
            f"KONTEXT (Ziel-Stellenprofil):\n{json.dumps(job_profile_context, ensure_ascii=False)}\n\n"
            f"Nutze diesen Kontext, um im CV besonders auf relevante Erfahrungen, Zertifikate und Skills zu achten, "
            f"die für dieses Profil gefordert sind. Die Extraktion bleibt faktenbasiert auf dem CV-Text.\n\n"
            f"{user_content}"
        )

    try:
        response = client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        json_data = json.loads(response.choices[0].message.content)
        print("JSON erfolgreich erstellt. Starte Normalisierung...")

        json_data = normalize_json_structure(json_data, target_language)
        print("Normalisierung abgeschlossen")

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"JSON gespeichert: {output_path}")

        return json_data

    except Exception as e:
        print(f"Fehler: {str(e)}")
        raise
