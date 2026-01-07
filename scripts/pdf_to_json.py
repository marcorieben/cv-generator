"""
PDF to JSON Converter using OpenAI API
Converts CV PDFs to structured JSON using the defined schema
"""

import os
import json
from openai import OpenAI
from pypdf import PdfReader
from dotenv import load_dotenv
import re


def get_text(translations, section, key, lang="de"):
    """Helper to get translated text from the dictionary."""
    try:
        return translations.get(section, {}).get(key, {}).get(lang, key)
    except:
        return key


def load_translations():
    """Loads translations from scripts/translations.json."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    trans_path = os.path.join(base_dir, "scripts", "translations.json")
    try:
        with open(trans_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Warning: Could not load translations: {e}")
        return {}


def normalize_date_format(date_str):
    """
    Konvertiert verschiedene Datumsformate zu MM/YYYY
    
    Beispiele:
    - "2020" -> "01/2020"
    - "Jan 2020" -> "01/2020"
    - "Januar 2020" -> "01/2020"
    - "2020 - 2021" -> "01/2020 - 01/2021"
    - "heute" / "heute" -> "heute" (unverändert)
    """
    if not date_str or not isinstance(date_str, str):
        return date_str
    
    # Wenn "heute", "Heute", "today" etc. -> unverändert
    if date_str.strip().lower() in ['heute', 'today', 'present', 'aktuell', 'aujourd\'hui', 'maintenant']:
        return date_str
    
    # Monatsnamen Mapping (Deutsch, Englisch und Französisch)
    months_map = {
        'januar': '01', 'jan': '01', 'jan.': '01', 'january': '01', 'janvier': '01', 'janv': '01',
        'februar': '02', 'feb': '02', 'feb.': '02', 'february': '02', 'février': '02', 'fév': '02',
        'märz': '03', 'mrz': '03', 'mar': '03', 'mar.': '03', 'mär': '03', 'mär.': '03', 'march': '03', 'mars': '03',
        'april': '04', 'apr': '04', 'apr.': '04', 'avril': '04', 'avr': '04',
        'mai': '05', 'may': '05',
        'juni': '06', 'jun': '06', 'jun.': '06', 'june': '06', 'juin': '06',
        'juli': '07', 'jul': '07', 'jul.': '07', 'july': '07', 'juillet': '07', 'juil': '07',
        'august': '08', 'aug': '08', 'aug.': '08', 'août': '08',
        'september': '09', 'sep': '09', 'sep.': '09', 'sept': '09', 'sept.': '09', 'septembre': '09',
        'oktober': '10', 'okt': '10', 'okt.': '10', 'oct': '10', 'oct.': '10', 'october': '10', 'octobre': '10',
        'november': '11', 'nov': '11', 'nov.': '11', 'novembre': '11',
        'dezember': '12', 'dez': '12', 'dez.': '12', 'dec': '12', 'dec.': '12', 'december': '12', 'décembre': '12', 'déc': '12'
    }
    
    # Pattern: "YYYY - YYYY" oder ähnliche Ranges - ZUERST behandeln!
    if ' - ' in date_str or ' – ' in date_str or ' — ' in date_str:
        separator = ' - ' if ' - ' in date_str else (' – ' if ' – ' in date_str else ' — ')
        parts = date_str.split(separator)
        if len(parts) == 2:
            start = normalize_date_format(parts[0].strip())
            end = normalize_date_format(parts[1].strip())
            return f"{start} - {end}"
    
    # Pattern: "MM/YYYY" oder "MM.YYYY" -> bereits korrekt oder leicht anpassbar
    if re.match(r'^\d{2}[/\.]\d{4}$', date_str.strip()):
        return date_str.replace('.', '/')
    
    # Pattern: "YYYY" -> "01/YYYY"
    if re.match(r'^\d{4}$', date_str.strip()):
        return f"01/{date_str.strip()}"
    
    # Pattern: "Monat YYYY" oder "MM YYYY" oder "MMM. YYYY"
    parts = re.split(r'[\s.]+', date_str.lower().strip())
    parts = [p for p in parts if p]  # Remove empty strings
    
    if len(parts) >= 2:
        month_part = parts[0].strip('.').lower()
        year_part = parts[-1]  # Last part is usually year
        
        # Check if month is in our names map
        if month_part in months_map and re.match(r'^\d{4}$', year_part):
            return f"{months_map[month_part]}/{year_part}"
    
    # Fallback: unverändert zurückgeben
    return date_str


def normalize_json_structure(data, language="de"):
    """
    Korrigiert verschachtelte Strukturen von OpenAI zum erwarteten Format
    """
    translations = load_translations()
    missing_marker = get_text(translations, "system", "missing_data_marker", language)

    # Korrektur 0: Hauptausbildung -> Ausbildung (Abwärtskompatibilität)
    if "Hauptausbildung" in data and "Ausbildung" not in data:
        data["Ausbildung"] = data["Hauptausbildung"]
        del data["Hauptausbildung"]
    
    # Korrektur 1: Expertise -> Fachwissen_und_Schwerpunkte
    if "Expertise" in data and isinstance(data["Expertise"], dict):
        if "Fachwissen_und_Schwerpunkte" in data["Expertise"]:
            data["Fachwissen_und_Schwerpunkte"] = data["Expertise"]["Fachwissen_und_Schwerpunkte"]
            del data["Expertise"]
    
    # Korrektur 2: BulletList -> Inhalt in Fachwissen_und_Schwerpunkte
    if "Fachwissen_und_Schwerpunkte" in data and isinstance(data["Fachwissen_und_Schwerpunkte"], list):
        for item in data["Fachwissen_und_Schwerpunkte"]:
            if "BulletList" in item and "Inhalt" not in item:
                item["Inhalt"] = item["BulletList"]
                del item["BulletList"]
    
    # Korrektur 2b: Erzwinge feste 3-Kategorien Struktur für Fachwissen_und_Schwerpunkte
    if "Fachwissen_und_Schwerpunkte" in data and isinstance(data["Fachwissen_und_Schwerpunkte"], list):
        skills = data["Fachwissen_und_Schwerpunkte"]
        
        # Erstelle die 3 Standard-Kategorien
        projektmethodik_items = []
        tech_stack_items = []
        weitere_skills_items = []
        
        # Mapping von Kategorienamen zu den 3 Standard-Kategorien
        projektmethodik_keywords = ['projekt', 'methodik', 'methodologie', 'agil', 'agile', 'scrum', 'hermes', 'safe', 'kanban', 'waterfall']
        tech_keywords = ['tech', 'stack', 'tool', 'technolog', 'plattform', 'framework', 'sprach', 'databa', 'cloud', 
                         'analytic', 'data', 'bi', 'microsoft', 'office', 'collaboration', 'software', 
                         'python', 'java', 'sql', 'web', 'app', 'system', 'server']
        
        for item in skills:
            kategorie_lower = item.get("Kategorie", "").lower()
            inhalt = item.get("Inhalt", [])
            
            # Versuche die Kategorie zuzuordnen - Projektmethodik hat Priorität
            if any(kw in kategorie_lower for kw in projektmethodik_keywords):
                projektmethodik_items.extend(inhalt)
            elif any(kw in kategorie_lower for kw in tech_keywords):
                tech_stack_items.extend(inhalt)
            else:
                # Wenn unklar, prüfe auch die Inhalte
                # Wenn es Methodiken sind (enthält bekannte Methoden-Namen)
                methoden_in_content = any(
                    any(method in str(i).lower() for method in ['scrum', 'agile', 'hermes', 'safe', 'kanban', 'waterfall'])
                    for i in inhalt
                )
                if methoden_in_content:
                    projektmethodik_items.extend(inhalt)
                else:
                    weitere_skills_items.extend(inhalt)
        
        # Falls Kategorien leer sind, Platzhalter einfügen
        if not projektmethodik_items:
            projektmethodik_items = [missing_marker]
        if not tech_stack_items:
            tech_stack_items = [missing_marker]
        if not weitere_skills_items:
            weitere_skills_items = [missing_marker]
        
        # Ersetze mit fester Struktur
        data["Fachwissen_und_Schwerpunkte"] = [
            {"Kategorie": get_text(translations, "skills_categories", "methodology", language), "Inhalt": projektmethodik_items},
            {"Kategorie": get_text(translations, "skills_categories", "tech_stack", language), "Inhalt": tech_stack_items},
            {"Kategorie": get_text(translations, "skills_categories", "other_skills", language), "Inhalt": weitere_skills_items}
        ]
    
    # Korrektur 3: Verschachtelte Referenzprojekte
    if "Ausgewählte_Referenzprojekte" in data and isinstance(data["Ausgewählte_Referenzprojekte"], dict):
        if "Referenzprojekte" in data["Ausgewählte_Referenzprojekte"]:
            data["Ausgewählte_Referenzprojekte"] = data["Ausgewählte_Referenzprojekte"]["Referenzprojekte"]
    
    # Korrektur 4: Normalisiere alle Zeitformate
    # Aus- und Weiterbildung (Nur Jahr YYYY)
    if "Aus_und_Weiterbildung" in data and isinstance(data["Aus_und_Weiterbildung"], list):
        for item in data["Aus_und_Weiterbildung"]:
            if "Zeitraum" in item and isinstance(item["Zeitraum"], str):
                norm = normalize_date_format(item["Zeitraum"])
                # MM/YYYY -> YYYY (auch in Ranges)
                item["Zeitraum"] = re.sub(r'\d{2}/(\d{4})', r'\1', norm)
    
    # Trainings & Zertifizierungen (Nur Jahr YYYY)
    if "Trainings_und_Zertifizierungen" in data and isinstance(data["Trainings_und_Zertifizierungen"], list):
        for item in data["Trainings_und_Zertifizierungen"]:
            if "Zeitraum" in item and isinstance(item["Zeitraum"], str):
                norm = normalize_date_format(item["Zeitraum"])
                # MM/YYYY -> YYYY (auch in Ranges)
                item["Zeitraum"] = re.sub(r'\d{2}/(\d{4})', r'\1', norm)
    
    # Referenzprojekte
    if "Ausgewählte_Referenzprojekte" in data and isinstance(data["Ausgewählte_Referenzprojekte"], list):
        for item in data["Ausgewählte_Referenzprojekte"]:
            if "Zeitraum" in item:
                item["Zeitraum"] = normalize_date_format(item["Zeitraum"])
    
    # Korrektur 5: Normalisiere Sprachen Level und Namen
    if "Sprachen" in data and isinstance(data["Sprachen"], list):
        # Mapping für gängige Sprachen (Englisch -> Deutsch)
        language_mapping = {
            "english": "Englisch",
            "german": "Deutsch",
            "french": "Französisch",
            "italian": "Italienisch",
            "spanish": "Spanisch",
            "portuguese": "Portugiesisch",
            "russian": "Russisch",
            "chinese": "Chinesisch",
            "japanese": "Japanisch"
        }

        for item in data["Sprachen"]:
            # 5a: Sprache Name normalisieren
            if "Sprache" in item and isinstance(item["Sprache"], str):
                lang_lower = item["Sprache"].lower().strip()
                # Direktes Match
                if lang_lower in language_mapping:
                    item["Sprache"] = language_mapping[lang_lower]
                # "English (Native)" -> "Englisch"
                elif any(k in lang_lower for k in language_mapping):
                    for k, v in language_mapping.items():
                        if k in lang_lower:
                            item["Sprache"] = v
                            break

            # 5b: Level normalisieren
            if "Level" in item:
                level = item["Level"]
                # Wenn String
                if isinstance(level, str):
                    # 1. Priorität: Sterne
                    if "★" in level or "*" in level:
                        # Zähle Sterne (ignoriere leere Sterne ☆ wenn möglich, aber hier zählen wir nur volle)
                        count = level.count("★") + level.count("*")
                        if count > 0:
                            item["Level"] = min(count, 5)
                    
                    # 2. Priorität: Explizite Zahl im String (z.B. "Level 5", "5/5")
                    # Aber Vorsicht vor "C1" (enthält 1) -> Regex muss isolierte Zahl oder X/5 sein
                    elif re.search(r'\b[1-5]\s*/\s*5', level) or re.match(r'^\s*[1-5]\s*$', level):
                         match = re.search(r'([1-5])', level)
                         if match:
                             item["Level"] = int(match.group(1))

                    # 3. Priorität: Text-Beschreibung
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


def extract_text_from_pdf(pdf_path):
    """
    Extrahiert Text aus einer PDF-Datei
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        
    Returns:
        String mit dem extrahierten Text
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        
        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Seite {page_num} ---\n{page_text}"
        
        if not text.strip():
            raise ValueError("Keine Text-Inhalte in PDF gefunden")
            
        return text
    
    except Exception as e:
        raise Exception(f"Fehler beim Lesen der PDF: {str(e)}")


def load_schema(schema_path="scripts/pdf_to_json_struktur_cv.json"):
    """
    Lädt das JSON-Schema für die CV-Struktur
    
    Args:
        schema_path: Pfad zur Schema-Datei
        
    Returns:
        Dictionary mit dem Schema
    """
    # Absoluten Pfad bilden
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base_dir, schema_path)
    
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Schema nicht gefunden: {full_path}")
    
    with open(full_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def pdf_to_json(pdf_path, output_path=None, schema_path="scripts/pdf_to_json_struktur_cv.json", job_profile_context=None, target_language="de"):
    """
    Konvertiert eine PDF-CV zu strukturiertem JSON via OpenAI API
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        output_path: Optionaler Pfad für JSON-Output (wenn None, nur zurückgeben)
        schema_path: Pfad zur Schema-Datei
        job_profile_context: Optionales Dictionary mit Stellenprofildaten zur Kontextualisierung
        target_language: Zielsprache für die Extraktion (de, en, fr)
        
    Returns:
        Dictionary mit den extrahierten CV-Daten
    """
    # Lade Environment Variables
    load_dotenv()
    
    # Check for Mock Mode
    model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
    if model_name == "mock":
        print("🧪 TEST-MODUS AKTIV: Verwende Mock-Daten (keine API-Kosten)")
        import time
        time.sleep(2) # Simulate processing time
        
        # Determine if we need CV or Offer mock data based on schema path
        is_offer = "stellenprofil" in schema_path.lower()
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        if is_offer:
            # Create a simple mock offer
            mock_data = {
                "Titel": "Senior Software Engineer",
                "Beschreibung": "Wir suchen einen erfahrenen Entwickler...",
                "Anforderungen": ["Python", "Cloud", "Agile"],
                "Aufgaben": ["Entwicklung", "Architektur"]
            }
        else:
            # Load valid CV fixture
            fixture_path = os.path.join(base_dir, "tests", "fixtures", "valid_cv.json")
            if os.path.exists(fixture_path):
                with open(fixture_path, 'r', encoding='utf-8') as f:
                    mock_data = json.load(f)
            else:
                # Fallback if fixture missing
                mock_data = {"Vorname": "Max", "Nachname": "Mustermann", "Mock": True}
                
        # Save if requested
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(mock_data, f, ensure_ascii=False, indent=2)
            print(f"💾 Mock-JSON gespeichert: {output_path}")
            
        return mock_data

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OpenAI API Key nicht gefunden!\n"
            "Bitte erstellen Sie eine .env Datei mit:\n"
            "OPENAI_API_KEY=sk-proj-your-key-here"
        )
    
    filename = os.path.basename(pdf_path) if isinstance(pdf_path, str) else "Uploaded File"
    print(f"📄 Lese PDF: {filename}")
    cv_text = extract_text_from_pdf(pdf_path)
    print(f"   → {len(cv_text)} Zeichen extrahiert")
    
    print("📋 Lade Schema...")
    schema = load_schema(schema_path)
    
    print("🤖 Sende Anfrage an OpenAI API...")
    client = OpenAI(api_key=api_key)
    
    # Load translations
    translations = load_translations()
    missing_marker = get_text(translations, "system", "missing_data_marker", target_language)
    
    # System Prompt mit Schema
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
   - Zähle die vollen Sterne/Punkte: ★★★★★ = 5, ★★★★☆ = 4.
   - 5er-Skala (Standard): 1=1, ..., 5=5
   - 3er-Skala: 1=1 (Grundkenntnisse), 2=3 (Gut), 3=5 (Exzellent/Muttersprache)
   - 4er-Skala: 1=1, 2=2, 3=4, 4=5
   - Text (A1-C2): A1/A2=1, B1=2, B2=3, C1=4, C2=5
   Sortiere absteigend nach Level.
6. REFERENZPROJEKTE UND BERUFSERFAHRUNG: Erfasse VOLLSTÄNDIG ALLE beruflichen Stationen, Projekte und Arbeitsverhältnisse aus dem gesamten Lebenslauf. Es gibt keine zeitliche Beschränkung nach hinten.
   - WICHTIG: Das Feld 'Ausgewählte_Referenzprojekte' muss entgegen seinem Namen VOLLSTÄNDIG ALLE beruflichen Stationen enthalten (nicht nur eine Auswahl). Es dient als vollständiger chronologischer Lebenslauf.
   - Es ist ein kritischer Fehler, Stationen auszulassen, nur weil sie älter sind oder nicht als "Projekt" bezeichnet werden.
   - Jede Station muss als eigenes Objekt in 'Ausgewählte_Referenzprojekte' erscheinen.
   - TÄTIGKEITEN/BULLET POINTS: Erfasse JEDE Tätigkeit ABSOLUT VOLLSTÄNDIG und WÖRTLICH so, wie sie im CV steht. 
   - WICHTIG: Es darf KEIN Wort ausgelassen, gekürzt oder zusammengefasst werden. Übernimm die gesamte Beschreibung des Aufpunkts unverändert. Die Beschränkung auf 5 Bullets entfällt komplett.
7. WICHTIG: Verwende "Inhalt" (NICHT "BulletList") für Fachwissen_und_Schwerpunkte
8. WICHTIG: Fachwissen_und_Schwerpunkte ist direkt auf oberster Ebene (NICHT in "Expertise" verschachtelt)
9. WICHTIG: Fachwissen_und_Schwerpunkte hat IMMER genau 3 Kategorien in dieser Reihenfolge:
   - 1. "Projektmethodik"
   - 2. "Tech Stack"
   - 3. "Weitere Skills"
10. ZEITFORMATE: Konvertiere Zeitangaben zu MM/YYYY (z.B. "01/2020"). Ausnahme: "Aus_und_Weiterbildung" sowie "Trainings_und_Zertifizierungen" verwenden NUR das Jahr YYYY (z.B. "2020" oder "2020 - 2022").
11. ALLE ZERTIFIKATE ERFASSEN: Erfasse ausnahmslos JEDES im PDF erwähnte Zertifikat und Training. Unabhängig vom Alter, Typ oder Bekanntheitsgrad. Gehe das Dokument chronologisch durch und stelle sicher, dass die Liste VOLLSTÄNDIG ist. Ein Auslassen von Zertifikaten ist nicht zulässig.
12. KURZPROFIL: Verwende den Vornamen der Person und schreibe in der 3. Person. Sei sachlich, hebe nur echte Stärken hervor, die aus dem CV ersichtlich sind. KEINE Übertreibungen oder Erfindungen!
13. ROLLE in Referenzprojekten: Maximal 8 Wörter! Kurz und prägnant formulieren.
14. SCHWEIZER RECHTSCHREIBUNG: Nutze ausschliesslich die Schweizer Schreibweise. Ersetze jedes 'ß' durch 'ss' (z.B. 'gross' statt 'groß', 'gemäss' statt 'gemäß').
15. ZIELSPRACHE: Extrahiere und übersetze den gesamten Inhalt (alle Felder) in die Zielsprache: {target_language.upper()}. Dies gilt insbesondere für Profile, Tätigkeiten und Projekterfolge. Fachbegriffe (z.B. 'Scrum', 'Cloud Architecture') sollten in ihrer üblichen Fachsprache bleiben, wenn dies in der Zielsprache üblich ist.

SCHEMA:
{json.dumps(schema, ensure_ascii=False, indent=2)}

Antworte ausschliesslich mit dem validen JSON-Objekt gemäss diesem Schema."""

    user_content = f"Extrahiere die CV-Daten (Zielsprache: {target_language.upper()}) aus folgendem Text:\n\n{cv_text}"
    
    # Falls Stellenprofil-Kontext vorhanden ist, diesen hinzufügen um die Extraktion zu fokussieren
    if job_profile_context:
        user_content = (
            f"KONTEXT (Ziel-Stellenprofil):\n{json.dumps(job_profile_context, ensure_ascii=False)}\n\n"
            f"Nutze diesen Kontext, um im CV besonders auf relevante Erfahrungen, Zertifikate und Skills zu achten, "
            f"die für dieses Profil gefordert sind. Falls das Projektprofil spezifische Zertifizierungen verlangt, "
            f"prüfe den CV extrem sorgfältig auf diese Begriffe. Die Extraktion soll aber weiterhin faktenbasiert auf dem CV-Text beruhen.\n\n"
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
        print(f"✅ JSON erfolgreich erstellt")
        
        # Post-Processing: Struktur korrigieren falls nötig
        json_data = normalize_json_structure(json_data, target_language)
        
        # Optional: In Datei speichern
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"💾 JSON gespeichert: {output_path}")
        
        return json_data
    
    except Exception as e:
        print(f"❌ Fehler: {str(e)}")
        sys.exit(1)
