import os
import json
import sys
from datetime import datetime

# Add scripts directory to path
sys.path.append(os.path.dirname(__file__))

from visualize_results import generate_dashboard

def create_clean_test_data():
    # Base paths
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    output_dir = os.path.join(base_dir, "output", "Test_Clean_20251228_120500")
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a dummy CV JSON (Clean)
    cv_data = {
        "Vorname": "Max",
        "Nachname": "Mustermann",
        "Hauptrolle": {"Titel": "Senior Developer", "Beschreibung": "Erfahrener Entwickler mit Fokus auf Python und Cloud Technologien."},
        "Nationalität": "Schweiz",
        "Ausbildung": "Master of Science",
        "Kurzprofil": "Max Mustermann ist ein erfahrener Software Engineer...",
        "Fachwissen_und_Schwerpunkte": [{"Kategorie": "Tech", "Inhalt": ["Python"]}],
        "Aus_und_Weiterbildung": [],
        "Trainings_und_Zertifizierungen": [],
        "Sprachen": [{"Sprache": "Deutsch", "Level": "Muttersprache"}],
        "Ausgewählte_Referenzprojekte": []
    }
    
    cv_json_path = os.path.join(output_dir, "cv_clean.json")
    with open(cv_json_path, "w", encoding="utf-8") as f:
        json.dump(cv_data, f, indent=2, ensure_ascii=False)
        
    # NO WARNINGS
    warnings = []
    
    # Generate Dashboard
    dashboard_path = generate_dashboard(
        cv_json_path=cv_json_path,
        match_json_path=None,
        feedback_json_path=None,
        output_dir=output_dir,
        validation_warnings=warnings,
        model_name="TEST-MODEL-GPT-4",
        pipeline_mode="Test Mode"
    )
    
    print(f"Dashboard created at: {dashboard_path}")
    
    # Update run_history.json
    history_path = os.path.join(base_dir, "output", "run_history.json")
    history_entry = {
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "candidate_name": "Max Mustermann (Clean Test)",
        "mode": "Basic (Nur CV)",
        "word_path": None,
        "cv_json": cv_json_path,
        "dashboard_path": dashboard_path,
        "match_score": 0,
        "stellenprofil_json": None,
        "match_json": None,
        "offer_word_path": None
    }
    
    history = []
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            try:
                history = json.load(f)
            except:
                pass
    
    # Insert at beginning
    history.insert(0, history_entry)
    
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
        
    print("Run history updated.")

if __name__ == "__main__":
    create_clean_test_data()
