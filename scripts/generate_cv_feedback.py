import os
import json
from openai import OpenAI
from datetime import datetime

def generate_cv_feedback_json(cv_json_path, output_path, schema_path, stellenprofil_json_path=None):
    """
    Generate a CV feedback JSON using the provided CV JSON and the feedback schema prompt.
    """
    # Load schema
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    # Load input data
    with open(cv_json_path, 'r', encoding='utf-8') as f:
        cv_data = json.load(f)
    stellenprofil_data = None
    if stellenprofil_json_path and os.path.exists(stellenprofil_json_path):
        with open(stellenprofil_json_path, 'r', encoding='utf-8') as f:
            stellenprofil_data = json.load(f)

    # Prepare prompt for OpenAI
    system_prompt = (
        "Du bist ein CV-Qualitätsprüfer. Analysiere das folgende CV-JSON (und optional das Stellenprofil) gemäß der Feedback-Schema-Vorgabe. "
        "Fülle die Struktur exakt aus, keine Felder hinzufügen oder weglassen. "
        "Nutze ausschließlich die bereitgestellten JSON-Daten. "
        "Schema (nur als Vorgabe, nicht ausgeben):\n" +
        json.dumps(schema, ensure_ascii=False, indent=2)
    )
    user_prompt = (
        "CV JSON:\n" + json.dumps(cv_data, ensure_ascii=False, indent=2)
    )
    if stellenprofil_data:
        user_prompt += "\n\nStellenprofil JSON:\n" + json.dumps(stellenprofil_data, ensure_ascii=False, indent=2)

    model_name = os.environ.get("MODEL_NAME", "gpt-3.5-turbo-1106")
    
    if model_name == "mock":
        print("🧪 TEST-MODUS (Feedback): Verwende Mock-Daten")
        feedback_json = {
            "feedback_metadata": {
                "feedback_datum": datetime.now().strftime("%Y-%m-%d"),
                "stellenprofil_bezogen": False
            },
            "zusammenfassung": {
                "gesamt_einschaetzung": "gut",
                "kritische_punkte": 0,
                "empfehlung": "CV verwendbar"
            },
            "feldbezogenes_feedback": [
                {
                    "cv_feld": "Kurzprofil",
                    "feedback_typ": "unklar",
                    "beschreibung": "Könnte etwas prägnanter sein.",
                    "verbesserungsvorschlag": "Auf 3-4 Sätze kürzen."
                },
                {
                    "cv_feld": "Sprachen",
                    "feedback_typ": "strukturabweichung",
                    "beschreibung": "Level-Angaben prüfen.",
                    "verbesserungsvorschlag": "Standard-Skala verwenden."
                }
            ],
            "allgemeine_hinweise": [
                "Gutes Layout",
                "Klare Struktur"
            ]
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
        feedback_json = json.loads(response.choices[0].message.content)
    
    # Ensure feedback_datum is set to current date
    if "feedback_metadata" in feedback_json:
        feedback_json["feedback_metadata"]["feedback_datum"] = datetime.now().strftime("%Y-%m-%d")
        
    # Save result
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(feedback_json, f, ensure_ascii=False, indent=2)
    print(f"✅ CV-Feedback JSON gespeichert: {output_path}")
    return feedback_json
