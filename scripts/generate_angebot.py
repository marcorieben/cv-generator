import os
import json
from openai import OpenAI
from datetime import datetime

def generate_angebot_json(cv_json_path, stellenprofil_json_path, match_json_path, output_path, schema_path):
    """
    Generate an Offer (Angebot) JSON using the provided CV, Stellenprofil, and Match JSONs.
    """
    # Load schema
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    # Load input data
    with open(cv_json_path, 'r', encoding='utf-8') as f:
        cv_data = json.load(f)
    
    with open(stellenprofil_json_path, 'r', encoding='utf-8') as f:
        stellenprofil_data = json.load(f)
        
    match_data = None
    if os.path.exists(match_json_path):
        with open(match_json_path, 'r', encoding='utf-8') as f:
            match_data = json.load(f)

    # Prepare prompt for OpenAI
    system_prompt = (
        "Du bist ein Experte für die Erstellung von professionellen IT-Dienstleistungsangeboten. "
        "Erstelle ein strukturiertes Angebot basierend auf dem Stellenprofil, dem Kandidaten-CV und dem Matching-Ergebnis. "
        "Halte dich strikt an das vorgegebene JSON-Schema. "
        "Erfinde keine Fakten, sondern leite alles aus den Eingabedaten ab. "
        "Schema (nur als Vorgabe, nicht ausgeben):\n" +
        json.dumps(schema, ensure_ascii=False, indent=2)
    )
    
    user_prompt = (
        "Stellenprofil JSON:\n" + json.dumps(stellenprofil_data, ensure_ascii=False, indent=2) +
        "\n\nCV JSON:\n" + json.dumps(cv_data, ensure_ascii=False, indent=2)
    )
    
    if match_data:
        user_prompt += "\n\nMatching Ergebnis JSON:\n" + json.dumps(match_data, ensure_ascii=False, indent=2)

    model_name = os.environ.get("MODEL_NAME", "gpt-4o-mini")
    
    if model_name == "mock":
        print("🧪 TEST-MODUS (Angebot): Verwende Mock-Daten")
        # Create a mock offer based on the schema structure
        angebot_json = {
            "angebots_metadata": {
                "angebots_id": stellenprofil_data.get("metadata", {}).get("document_id", "OFFER-2025-001"),
                "anbieter": "Orange Business",
                "kunde": stellenprofil_data.get("projekt_kontext", {}).get("auftraggeber", "! bitte prüfen !"),
                "datum": datetime.now().strftime("%d.%m.%Y"),
                "ansprechpartner": {
                    "name": stellenprofil_data.get("kontakt", {}).get("name", "! bitte prüfen !"),
                    "rolle": stellenprofil_data.get("kontakt", {}).get("rolle", "! bitte prüfen !"),
                    "kontakt": "! bitte prüfen !"
                }
            },
            "stellenbezug": {
                "rollenbezeichnung": stellenprofil_data.get("rolle", {}).get("titel", "! bitte prüfen !"),
                "organisationseinheit": stellenprofil_data.get("projekt_kontext", {}).get("organisationseinheit", "! bitte prüfen !"),
                "kurzkontext": stellenprofil_data.get("projekt_kontext", {}).get("kurzbeschreibung", "! bitte prüfen !")
            },
            "kandidatenvorschlag": {
                "name": f"{cv_data.get('Vorname', '')} {cv_data.get('Nachname', '')}".strip(),
                "angebotene_rolle": cv_data.get("Hauptrolle", {}).get("Beschreibung", "! bitte prüfen !"),
                "eignungs_summary": "Der Kandidat verfügt über die relevanten Erfahrungen für diese Position."
            },
            "profil_und_kompetenzen": {
                "methoden_und_technologien": [
                    item.get("Inhalt", [])[0] if isinstance(item.get("Inhalt"), list) and item.get("Inhalt") else "! bitte prüfen !"
                    for item in cv_data.get("Fachwissen_und_Schwerpunkte", [])
                ],
                "operative_und_fuehrungserfahrung": [
                    "Erfahrung in der Umsetzung komplexer Projekte",
                    "Fundierte Fachkenntnisse im relevanten Bereich"
                ]
            },
            "einsatzkonditionen": {
                "pensum": stellenprofil_data.get("einsatzrahmen", {}).get("pensum", "100%"),
                "verfuegbarkeit": stellenprofil_data.get("einsatzrahmen", {}).get("zeitraum", {}).get("start", "ab sofort"),
                "stundensatz": "165.00 CHF (exkl. MWST)",
                "subunternehmen": "Nein"
            },
            "kriterien_abgleich": {
                "muss_kriterien": [
                    {
                        "kriterium": k.get("kriterium", k) if isinstance(k, dict) else k,
                        "erfuellt": True,
                        "begruendung": "Gemäss CV vorhanden."
                    } for k in stellenprofil_data.get("anforderungen", {}).get("muss_kriterien", [])[:3]
                ],
                "soll_kriterien": [
                    {
                        "kriterium": k.get("kriterium", k) if isinstance(k, dict) else k,
                        "erfuellt": True,
                        "begruendung": "Gemäss CV vorhanden."
                    } for k in stellenprofil_data.get("anforderungen", {}).get("soll_kriterien", [])[:2]
                ]
            },
            "gesamtbeurteilung": {
                "zusammenfassung": f"{cv_data.get('Vorname', '')} {cv_data.get('Nachname', '')} passt hervorragend auf das Profil.",
                "mehrwert_fuer_kunden": [
                    "Schnelle Einarbeitung",
                    "Hohe Fachkompetenz"
                ],
                "empfehlung": "Wir empfehlen den Kandidaten für die Besetzung der Stelle."
            },
            "abschluss": {
                "verfuegbarkeit_gespraech": "Nach Absprache kurzfristig möglich.",
                "kontakt_hinweis": "Wir freuen uns auf Ihre Rückmeldung."
            }
        }
    else:
        client = OpenAI()
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            angebot_json = json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"❌ Fehler bei der Angebots-Generierung: {e}")
            raise e

    # Save result
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(angebot_json, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Angebot JSON generiert: {output_path}")
    return output_path
