import os
import json
from openai import OpenAI
from datetime import datetime

def normalize_matching_values(data):
    """
    Normalisiert die 'bewertung' Felder auf fix definierte, einheitliche Werte
    für alle Kriterientypen (Muss, Soll, Soft, Weitere).
    """
    # Einheitliches Mapping für alle Kriterien
    unified_map = {
        "erfüllt": "erfüllt",
        "voll erfüllt": "erfüllt",
        "ja": "erfüllt",
        
        "teilweise": "teilweise erfüllt",
        "teilweise erfüllt": "teilweise erfüllt",
        
        "nicht erfüllt": "nicht erfüllt",
        "nein": "nicht erfüllt",
        "fehlt": "nicht erfüllt",
        
        "potenziell": "potenziell erfüllt",
        "potenziell erfüllt": "potenziell erfüllt",
        "implizit": "potenziell erfüllt",
        
        "nicht explizit": "nicht explizit erwähnt",
        "nicht explizit erwähnt": "nicht explizit erwähnt",
        "nicht erwähnt": "nicht explizit erwähnt",
        "neutral": "nicht explizit erwähnt",
        
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
                # Wir prüfen auf boolean False oder String "false" / "nein"
                found = item.get("im_cv_gefunden")
                found_bool = False
                if isinstance(found, bool):
                    found_bool = found
                elif isinstance(found, str):
                    found_bool = found.lower() in ["true", "ja", "yes", "vorhanden"]
                
                # 2. Bestehende Bewertung normalisieren
                current_val = item.get("bewertung", "")
                normalized_val = get_normalized(current_val, unified_map, "! bitte prüfen !")
                
                # 3. Korrektur bei offensichtlicher Inkonsistenz
                # Falls 'gefunden' = False, aber Bewertung = 'erfüllt', korrigieren wir auf 'nicht erfüllt'
                if not found_bool and normalized_val == "erfüllt":
                    # Ausnahme: Soft Skills werden oft nicht 'gefunden' aber als neutral/nicht erwähnt markiert
                    if section != "soft_skills_abgleich":
                        normalized_val = "nicht erfüllt"
                
                # Soft Skills erhalten als Default "nicht explizit erwähnt"
                if not current_val or normalized_val == "! bitte prüfen !":
                    if section == "soft_skills_abgleich":
                        normalized_val = "nicht explizit erwähnt"

                item["bewertung"] = normalized_val

    return data

def generate_matchmaking_json(cv_json_path, stellenprofil_json_path, output_path, schema_path):
    """
    Generate a matchmaking JSON using the provided CV and Stellenprofil JSONs and the schema prompt.
    """
    # Load schema
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    # Load input data
    with open(cv_json_path, 'r', encoding='utf-8') as f:
        cv_data = json.load(f)
    with open(stellenprofil_json_path, 'r', encoding='utf-8') as f:
        stellenprofil_data = json.load(f)

    # Prepare prompt for OpenAI
    system_prompt = (
        "Du bist ein kritischer Auditor für CV-Matching. Vergleiche das folgende Stellenprofil und den CV gemäss der JSON-Schema-Vorgabe.\n"
        "WICHTIGE REGELN ZUR VERMEIDUNG VON HALLUZINATIONEN UND FÜR STRUKTURELLE TREUE:\n"
        "1. Nutze AUSSCHLIESSLICH die bereitgestellten JSON-Daten des CVs. Erfinde keine Informationen.\n"
        "2. EXAKTE KONTINUITÄT & VOLLSTÄNDIGKEIT: Übernehme JEDES EINZELNE Kriterium aus dem Stellenprofil (anforderungen.muss_kriterien und anforderungen.soll_kriterien) ABSOLUT VOLLSTÄNDIG und WÖRTLICH. Es darf KEIN Wort ausgelassen, gekürzt oder zusammengefasst werden. Auch Aufzählungen innerhalb eines Kriteriums (z.B. 'SAFe, Kenntnisse als Coach' oder 'Deutsch- und Englischkenntnisse') müssen 1:1 übernommen werden. Das Kriterium im Match-JSON muss identisch mit dem Text im Stellenprofil-JSON sein. Die Anzahl der Einträge im Abgleich muss exakt der Anzahl der Kriterien im Profil entsprechen.\n"
        "3. KEINE AUSLASSUNGEN: Jedes Kriterium aus der Profil-Liste muss ein entsprechendes Gegenstück im Abgleich haben. Auch vermeintlich einfache Kriterien wie Sprachen (Deutsch/Englisch) MÜSSEN im Abgleich erscheinen.\n"
        "4. STRIKTES CLUSTERING: Alle Kriterien aus 'anforderungen.muss_kriterien' müssen zwingend in 'muss_kriterien_abgleich' landen. Alle Kriterien aus 'anforderungen.soll_kriterien' zwingend in 'soll_kriterien_abgleich'. Vermische diese Kategorien nicht und erstelle für jeden Punkt einen eigenen Eintrag.\n"
        "5. ZERTIFIZIERUNGEN: Scanne explizit das Feld 'Trainings_und_Zertifizierungen' sowie 'Aus_und_Weiterbildung' nach Übereinstimmungen mit den geforderten Zertifikaten. Auch wenn ein Zertifikat nur im Freitext der Projekterfahrungen erwähnt wird, gilt es als gefunden.\n"
        "6. IMPLIZITE MATCHES: Wenn ein Skill oder Zertifikat nicht explizit im CV steht, aber durch den Kontext (z.B. Rolle, Aufgaben, Projekterfahrung) sehr wahrscheinlich vorhanden ist, bewerte es als 'potenziell erfüllt'. Begründe dies im Kommentar.\n"
        "7. LOGISCHE KONSISTENZ: Falls 'im_cv_gefunden' = false ist, darf die 'bewertung' NIEMALS 'erfüllt' oder 'teilweise erfüllt' sein. In diesem Fall muss die Bewertung 'nicht erfüllt' oder 'nicht explizit erwähnt' lauten.\n"
        "8. CV-EVIDENZ & NACHWEIS: Formuliere im Feld 'cv_evidenz' eine prägnante Begründung basierend auf Fakten aus dem CV. Nutze Telegramm-Stil: keine Füllwörter, keine Personalpronomen, kein 'im CV nachgewiesen' oder 'laut Lebenslauf'. Erwähne explizite Fakten (Projekte, Rollen, Zertifikate) sowie implizite Herleitungen aus dem Kontext. Beispiel: 'Mehrjährige Erfahrung in SAFe-Projekten als Scrum Master' statt 'Die Person hat im CV Erfahrung mit SAFe'. Bei Sprachen: 'Deutsch (C2) und Englisch (C1) durch Projekterfahrung belegt'.\n"
        "9. LOGISCHE KONSISTENZ: Falls 'im_cv_gefunden' = false ist, darf die 'bewertung' NIEMALS 'erfüllt' oder 'teilweise erfüllt' sein. In diesem Fall muss die Bewertung 'nicht erfüllt' oder 'nicht explizit erwähnt' lauten.\n"
        "10. KOMMENTAR: Nutze das Feld 'kommentar' nur für zusätzliche, kritische Anmerkungen oder Erklärungen zur Bewertung, falls notwendig.\n"
        "11. SOFT SKILLS: Identifiziere und extrahiere eigenständig persönliche Kompetenzen (z.B. Teamfähigkeit, Kommunikation) in die Liste 'soft_skills_abgleich'.\n"
        "12. WEITERE KRITERIEN: Falls im Stellenprofil (z.B. in den Aufgaben oder Fliesstext) Anforderungen stehen, die nicht in den expliziten Muss/Soll-Listen aufgeführt sind, ordne diese in 'weitere_kriterien_abgleich' ein.\n"
        "13. SCHWEIZER RECHTSCHREIBUNG: Nutze ausschliesslich die Schweizer Schreibweise. Ersetze jedes 'ß' durch 'ss' (z.B. 'gross' statt 'groß', 'gemäss' statt 'gemäß').\n"
        "14. SCORE-BERECHNUNG (0-100%): Der Score berechnet sich ausschliesslich aus Muss- und Soll-Kriterien:\n"
        "    - Basis-Gewichtung: Muss-Kriterien (90%), Soll-Kriterien (10%).\n"
        "    - DYNAMISCHE ANPASSUNG: Falls eine der beiden Kategorien fehlt, wird die Gewichtung zu 100% auf die vorhandene Kategorie (Muss oder Soll) gelegt. Soft Skills und weitere Kriterien fliessen NICHT in den numerischen Score ein.\n"
        "    - BEWERTUNGS-LOGIK: 'erfüllt' = 100% des Kriterium-Werts, 'teilweise erfüllt' = 50%, 'potenziell erfüllt' = 40%, 'nicht erfüllt' / 'nicht explizit erwähnt' = 0%.\n"
        "    - Muss-Kriterien sind 'Showstopper': Ein 'nicht erfüllt' bei einem Muss-Kriterium führt zu einem massiven Abzug (mind. -20% vom Gesamtergebnis pro fehlendem Punkt).\n\n"
        "Schema (nur als Vorgabe, nicht ausgeben):\n" +
        json.dumps(schema, ensure_ascii=False, indent=2)
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
    match_json = normalize_matching_values(match_json)
    
    # Ensure matching_datum is set to current date
    if "match_metadata" in match_json:
        match_json["match_metadata"]["matching_datum"] = datetime.now().strftime("%Y-%m-%d")
        
    # Save result
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(match_json, f, ensure_ascii=False, indent=2)
    print(f"✅ Matchmaking JSON gespeichert: {output_path}")
    return match_json
