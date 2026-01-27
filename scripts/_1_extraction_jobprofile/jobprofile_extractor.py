"""
Jobprofile Extraction - PDF to structured JSON.

Extracts job profile/requirement data from PDF using OpenAI API.

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-26
Last Updated: 2026-01-26
"""
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

from scripts._shared.pdf_utils import extract_text_from_pdf
from scripts._1_extraction_jobprofile.jobprofile_prompt import build_jobprofile_system_prompt, build_jobprofile_user_prompt
from scripts.utils.translations import load_translations, get_text


def load_schema(schema_path):
    """
    Lädt ein JSON-Schema.

    Args:
        schema_path: Absoluter oder relativer Pfad zur Schema-Datei

    Returns:
        Dictionary mit dem Schema
    """
    if os.path.isabs(schema_path):
        full_path = schema_path
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(base_dir, schema_path)

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Schema nicht gefunden: {full_path}")

    with open(full_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_jobprofile(pdf_path, output_path=None, schema_path=None, target_language="de"):
    """
    Extrahiert Stellenprofil-Daten aus PDF via OpenAI API.

    Args:
        pdf_path: Pfad zur PDF-Datei oder Streamlit UploadedFile
        output_path: Optionaler Pfad für JSON-Output
        schema_path: Pfad zur Schema-Datei (default: jobprofile_schema.json im selben Ordner)
        target_language: Zielsprache (de, en, fr)

    Returns:
        Dictionary mit den extrahierten Stellenprofil-Daten
    """
    if pdf_path is None:
        raise ValueError("PDF-Datei ist leer (None). Bitte laden Sie eine gültige PDF-Datei hoch.")

    load_dotenv()

    # Default schema path
    if schema_path is None:
        schema_path = os.path.join(os.path.dirname(__file__), "jobprofile_schema.json")

    model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
    if model_name == "mock":
        print("TEST-MODUS AKTIV: Verwende Mock-Daten (keine API-Kosten)")
        import time
        time.sleep(2)

        mock_data = {
            "Titel": "Senior Software Engineer",
            "Beschreibung": "Wir suchen einen erfahrenen Entwickler...",
            "Anforderungen": ["Python", "Cloud", "Agile"],
            "Aufgaben": ["Entwicklung", "Architektur"]
        }

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
    text = extract_text_from_pdf(pdf_path)
    print(f"   -> {len(text)} Zeichen extrahiert")

    print("Lade Schema...")
    schema = load_schema(schema_path)

    print("Sende Anfrage an OpenAI API...")
    client = OpenAI(api_key=api_key)

    translations = load_translations()
    missing_marker = get_text(translations, "system", "missing_data_marker", target_language)

    system_prompt = build_jobprofile_system_prompt(schema, target_language, missing_marker)
    user_content = build_jobprofile_user_prompt(text, target_language)

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
        print("JSON erfolgreich erstellt")

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"JSON gespeichert: {output_path}")

        return json_data

    except Exception as e:
        print(f"Fehler: {str(e)}")
        raise
