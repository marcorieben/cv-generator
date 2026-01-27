"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-14
Last Updated: 2026-01-24
"""
import os
import json
import sys
from datetime import datetime

# Add scripts directory to path
sys.path.append(os.path.dirname(__file__))

from visualize_results import generate_dashboard

def create_test_data():
    # Base paths
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    output_dir = os.path.join(base_dir, "output", "Test_Validation_20251228_120000")
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a dummy CV JSON
    cv_data = {
        "Vorname": "Test",
        "Nachname": "User",
        "Hauptrolle": {"Titel": "Developer", "Beschreibung": "Too short"},
        "Nationalität": "Schweiz",
        "Ausbildung": "Master",
        "Kurzprofil": "Ein Test Profil.",
        "Fachwissen_und_Schwerpunkte": [],
        "Aus_und_Weiterbildung": [],
        "Trainings_und_Zertifizierungen": [],
        "Sprachen": [{"Sprache": "Deutsch", "Level": "Unknown"}],
        "Ausgewählte_Referenzprojekte": []
    }
    
    cv_json_path = os.path.join(output_dir, "cv_test.json")
    with open(cv_json_path, "w", encoding="utf-8") as f:
        json.dump(cv_data, f, indent=2, ensure_ascii=False)
        
    # Define warnings
    warnings = [
        "Hauptrolle.Beschreibung sollte 5-10 Wörter haben (aktuell 2)",
        "Sprachen[0]: Ungültiges oder fehlendes Feld 'Level' (muss eine Zahl 1-5, Text wie 'Muttersprache' oder Kombination sein)",
        "Fachwissen_und_Schwerpunkte: Liste ist leer"
    ]
    
    # Generate Dashboard
    # F003: generate_dashboard now returns (bytes, filename) tuple
    dashboard_bytes, dashboard_filename = generate_dashboard(
        cv_json_path=cv_json_path,
        match_json_path=None,
        feedback_json_path=None,
        output_dir=output_dir,
        validation_warnings=warnings
    )
    # Write bytes to file
    dashboard_path = output_dir / dashboard_filename
    with open(dashboard_path, 'wb') as f:
        f.write(dashboard_bytes)
    
    print(f"Dashboard created at: {dashboard_path}")
    
    # Update run_history.json
    history_path = os.path.join(base_dir, "output", "run_history.json")
    history_entry = {
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "candidate_name": "Test User (Validation Warnings)",
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
            except json.JSONDecodeError:
                pass
    
    # Insert at beginning
    history.insert(0, history_entry)
    
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
        
    print("Run history updated.")

if __name__ == "__main__":
    create_test_data()
