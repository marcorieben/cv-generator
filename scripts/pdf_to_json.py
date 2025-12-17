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
    if date_str.strip().lower() in ['heute', 'today', 'present', 'aktuell']:
        return date_str
    
    # Monatsnamen Mapping (Deutsch und Englisch)
    months_de = {
        'januar': '01', 'jan': '01', 'jan.': '01',
        'februar': '02', 'feb': '02', 'feb.': '02',
        'märz': '03', 'mrz': '03', 'mar': '03', 'mar.': '03', 'mär': '03', 'mär.': '03',
        'april': '04', 'apr': '04', 'apr.': '04',
        'mai': '05',
        'juni': '06', 'jun': '06', 'jun.': '06',
        'juli': '07', 'jul': '07', 'jul.': '07',
        'august': '08', 'aug': '08', 'aug.': '08',
        'september': '09', 'sep': '09', 'sep.': '09', 'sept': '09', 'sept.': '09',
        'oktober': '10', 'okt': '10', 'okt.': '10', 'oct': '10', 'oct.': '10',
        'november': '11', 'nov': '11', 'nov.': '11',
        'dezember': '12', 'dez': '12', 'dez.': '12', 'dec': '12', 'dec.': '12'
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
        
        # Check if month is in German names
        if month_part in months_de and re.match(r'^\d{4}$', year_part):
            return f"{months_de[month_part]}/{year_part}"
    
    # Fallback: unverändert zurückgeben
    return date_str


def normalize_json_structure(data):
    """
    Korrigiert verschachtelte Strukturen von OpenAI zum erwarteten Format
    """
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
            projektmethodik_items = ["! fehlt – bitte prüfen!"]
        if not tech_stack_items:
            tech_stack_items = ["! fehlt – bitte prüfen!"]
        if not weitere_skills_items:
            weitere_skills_items = ["! fehlt – bitte prüfen!"]
        
        # Ersetze mit fester Struktur
        data["Fachwissen_und_Schwerpunkte"] = [
            {"Kategorie": "Projektmethodik", "Inhalt": projektmethodik_items},
            {"Kategorie": "Tech Stack", "Inhalt": tech_stack_items},
            {"Kategorie": "Weitere Skills", "Inhalt": weitere_skills_items}
        ]
    
    # Korrektur 3: Verschachtelte Referenzprojekte
    if "Ausgewählte_Referenzprojekte" in data and isinstance(data["Ausgewählte_Referenzprojekte"], dict):
        if "Referenzprojekte" in data["Ausgewählte_Referenzprojekte"]:
            data["Ausgewählte_Referenzprojekte"] = data["Ausgewählte_Referenzprojekte"]["Referenzprojekte"]
    
    # Korrektur 4: Normalisiere alle Zeitformate zu MM/YYYY
    # Aus- und Weiterbildung
    if "Aus_und_Weiterbildung" in data and isinstance(data["Aus_und_Weiterbildung"], list):
        for item in data["Aus_und_Weiterbildung"]:
            if "Zeitraum" in item:
                item["Zeitraum"] = normalize_date_format(item["Zeitraum"])
    
    # Trainings & Zertifizierungen
    if "Trainings_und_Zertifizierungen" in data and isinstance(data["Trainings_und_Zertifizierungen"], list):
        for item in data["Trainings_und_Zertifizierungen"]:
            if "Zeitraum" in item:
                item["Zeitraum"] = normalize_date_format(item["Zeitraum"])
    
    # Referenzprojekte
    if "Ausgewählte_Referenzprojekte" in data and isinstance(data["Ausgewählte_Referenzprojekte"], list):
        for item in data["Ausgewählte_Referenzprojekte"]:
            if "Zeitraum" in item:
                item["Zeitraum"] = normalize_date_format(item["Zeitraum"])
    
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


def load_schema(schema_path="scripts/pdf_to_json_schema.json"):
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


def pdf_to_json(pdf_path, output_path=None, schema_path="scripts/pdf_to_json_schema.json"):
    """
    Konvertiert eine PDF-CV zu strukturiertem JSON via OpenAI API
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        output_path: Optionaler Pfad für JSON-Output (wenn None, nur zurückgeben)
        schema_path: Pfad zur Schema-Datei
        
    Returns:
        Dictionary mit den extrahierten CV-Daten
    """
    # Lade Environment Variables
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OpenAI API Key nicht gefunden!\n"
            "Bitte erstellen Sie eine .env Datei mit:\n"
            "OPENAI_API_KEY=sk-proj-your-key-here"
        )
    
    print(f"📄 Lese PDF: {os.path.basename(pdf_path)}")
    cv_text = extract_text_from_pdf(pdf_path)
    print(f"   → {len(cv_text)} Zeichen extrahiert")
    
    print("📋 Lade Schema...")
    schema = load_schema(schema_path)
    
    print("🤖 Sende Anfrage an OpenAI API...")
    client = OpenAI(api_key=api_key)
    
    # System Prompt mit Schema
    system_prompt = f"""Du bist ein Experte für CV-Extraktion und arbeitest für eine IT-Beratungsfirma.

Deine Aufgabe: Extrahiere alle Informationen aus dem bereitgestellten CV-Text und erstelle ein strukturiertes JSON gemäss dem folgenden Schema.

WICHTIGE REGELN:
1. Verwende NUR Felder, die im Schema definiert sind - KEINE zusätzlichen Felder
2. Bei fehlenden Informationen: Markiere mit "! fehlt – bitte prüfen!"
3. Keine Informationen erfinden oder raten
4. Halte dich strikt an die Feldnamen und Struktur des Schemas
5. Sprachen nach Level sortieren (5=Muttersprache bis 1=Grundkenntnisse)
6. Maximal 5 Bullet Points pro Referenzprojekt
7. WICHTIG: Verwende "Inhalt" (NICHT "BulletList") für Fachwissen_und_Schwerpunkte
8. WICHTIG: Fachwissen_und_Schwerpunkte ist direkt auf oberster Ebene (NICHT in "Expertise" verschachtelt)
9. WICHTIG: Fachwissen_und_Schwerpunkte hat IMMER genau 3 Kategorien in dieser Reihenfolge:
   - 1. "Projektmethodik"
   - 2. "Tech Stack"
   - 3. "Weitere Skills"
10. ZEITFORMATE: Konvertiere ALLE Zeitangaben zu MM/YYYY Format (z.B. "01/2020", "12/2023")
11. AUS- UND WEITERBILDUNG vs. TRAININGS:
    - Aus_und_Weiterbildung: NUR akademische/formale Abschlüsse (Bachelor, Master, PhD, CAS, DAS, MAS, Diplome)
    - Trainings_und_Zertifizierungen: Kurse, Workshops, Zertifikate, Weiterbildungen ohne akademischen Abschluss
12. KURZPROFIL: Verwende den Vornamen der Person und schreibe in der 3. Person. Sei sachlich, hebe nur echte Stärken hervor, die aus dem CV ersichtlich sind. KEINE Übertreibungen oder Erfindungen!
13. ROLLE in Referenzprojekten: Maximal 8 Wörter! Kurz und prägnant formulieren.

SCHEMA:
{json.dumps(schema, ensure_ascii=False, indent=2)}

Antworte ausschliesslich mit dem validen JSON-Objekt gemäss diesem Schema."""

    try:
        response = client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extrahiere die CV-Daten aus folgendem Text:\n\n{cv_text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        json_data = json.loads(response.choices[0].message.content)
        print(f"✅ JSON erfolgreich erstellt")
        
        # Post-Processing: Struktur korrigieren falls nötig
        json_data = normalize_json_structure(json_data)
        
        # Optional: In Datei speichern
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"💾 JSON gespeichert: {output_path}")
        
        return json_data
    
    except Exception as e:
        raise Exception(f"Fehler bei OpenAI API-Aufruf: {str(e)}")


if __name__ == "__main__":
    # Test-Modus
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_json.py <pdf_file> [output_json]")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result = pdf_to_json(pdf_file, output_file)
        
        if not output_file:
            # Ausgabe auf Konsole
            print("\n" + "="*60)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            print("="*60)
    
    except Exception as e:
        print(f"❌ Fehler: {str(e)}")
        sys.exit(1)
