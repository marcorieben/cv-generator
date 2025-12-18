import os
import json
from openai import OpenAI
from datetime import datetime

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
        "Du bist ein Matching-Experte. Vergleiche das folgende Stellenprofil und den CV gemäß der JSON-Schema-Vorgabe. "
        "Fülle die Struktur exakt aus, keine Felder hinzufügen oder weglassen. "
        "Nutze ausschließlich die bereitgestellten JSON-Daten. "
        "Schema (nur als Vorgabe, nicht ausgeben):\n" +
        json.dumps(schema, ensure_ascii=False, indent=2)
    )
    user_prompt = (
        "Stellenprofil JSON:\n" + json.dumps(stellenprofil_data, ensure_ascii=False, indent=2) +
        "\n\nCV JSON:\n" + json.dumps(cv_data, ensure_ascii=False, indent=2)
    )

    model_name = os.environ.get("MODEL_NAME", "gpt-3.5-turbo-1106")
    
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
                    "muss_kriterien": 60,
                    "soll_kriterien": 30,
                    "skill_abdeckung": 10
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
    
    # Ensure matching_datum is set to current date
    if "match_metadata" in match_json:
        match_json["match_metadata"]["matching_datum"] = datetime.now().strftime("%Y-%m-%d")
        
    # Save result
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(match_json, f, ensure_ascii=False, indent=2)
    print(f"✅ Matchmaking JSON gespeichert: {output_path}")
    return match_json
