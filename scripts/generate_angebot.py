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
                "angebots_id": "MOCK-12345",
                "anbieter": "Musterfirma AG",
                "kunde": "Musterkunde GmbH",
                "datum": datetime.now().strftime("%Y-%m-%d"),
                "ansprechpartner": {
                    "name": "Max Mustermann",
                    "rolle": "Account Manager",
                    "kontakt": "max.mustermann@musterfirma.ch"
                }
            },
            "stellenbezug": {
                "rollenbezeichnung": stellenprofil_data.get("titel", "Software Engineer"),
                "organisationseinheit": "IT",
                "kurzkontext": "Unterstützung im Projekt X"
            },
            "kandidatenvorschlag": {
                "name": f"{cv_data.get('Vorname', '')} {cv_data.get('Nachname', '')}",
                "angebotene_rolle": "Senior Developer",
                "eignungs_summary": "Der Kandidat verfügt über hervorragende Kenntnisse."
            },
            "profil_und_kompetenzen": {
                "methoden_und_technologien": ["Python", "Scrum", "Cloud"],
                "operative_und_fuehrungserfahrung": ["5 Jahre Entwicklung", "Teamleitung"]
            },
            "einsatzkonditionen": {
                "pensum": "100%",
                "verfuegbarkeit": "sofort",
                "stundensatz": "150.00",
                "subunternehmen": "-"
            },
            "kriterien_abgleich": {
                "muss_kriterien": [
                    {"kriterium": "Python", "erfuellt": True, "begruendung": "Experte"}
                ],
                "soll_kriterien": [
                    {"kriterium": "Java", "erfuellt": False, "begruendung": "Grundkenntnisse"}
                ]
            },
            "gesamtbeurteilung": {
                "zusammenfassung": "Sehr guter Fit.",
                "mehrwert_fuer_kunden": ["Schnelle Einarbeitung"],
                "empfehlung": "Klare Empfehlung"
            },
            "abschluss": {
                "verfuegbarkeit_gespraech": "Jederzeit",
                "kontakt_hinweis": "Bei Fragen stehen wir gerne zur Verfügung."
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
