"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-21
Last Updated: 2026-01-24
"""
import os
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts._2_extraction_cv.cv_word import generate_cv
from scripts._3_analysis_matchmaking.matchmaking_generator import generate_matchmaking_json
from scripts._4_analysis_feedback.feedback_generator import generate_cv_feedback_json
from scripts._6_output_dashboard.dashboard_generator import generate_dashboard

def update_test_data():
    """
    Regenerates all test artifacts based on the current logic and fixtures.
    This ensures that the 'Mock Mode' and offline tests always use the latest
    generation logic.
    """
    print("🔄 Updating Test Data Artifacts...")
    
    output_dir = project_root / "tests" / "fixtures" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Source Fixtures (neue Step-Ordner)
    cv_json_path = project_root / "tests" / "2_extraction_cv" / "fixtures" / "valid_cv.json"
    if not cv_json_path.exists():
        print(f"❌ Error: {cv_json_path} not found!")
        return False

    # Create a dummy job profile if needed
    job_json_path = project_root / "tests" / "1_extraction_jobprofile" / "fixtures" / "valid_job.json"
    if not job_json_path.exists():
        job_data = {
            "Titel": "Senior Developer",
            "Beschreibung": "Wir suchen einen Senior Developer...",
            "Anforderungen": ["Python", "Cloud"],
            "Aufgaben": ["Coding", "Architecture"]
        }
        with open(job_json_path, 'w', encoding='utf-8') as f:
            json.dump(job_data, f, indent=2)
            
    # 2. Generate Word CV
    print("   📝 Generating Word CV...")
    try:
        word_path = generate_cv(str(cv_json_path), str(output_dir), interactive=False)
        print(f"      ✅ Created: {Path(word_path).name}")
    except Exception as e:
        print(f"      ❌ Failed: {e}")
        return False

    # 3. Generate Matchmaking JSON (Mock)
    print("   🤝 Generating Matchmaking JSON...")
    match_json_path = output_dir / "match_result.json"
    # We can't easily call the AI here, so we'll create a structure that matches the schema
    # Or if we have a logic that doesn't require AI (unlikely for matchmaking).
    # For now, we'll skip AI generation and just ensure the file exists for dashboard testing
    match_data = {
        "match_score": {"score_gesamt": 85, "begruendung": "Gute Übereinstimmung"},
        "analyse": {"starken": ["Python"], "schwachen": ["Java"]},
        "empfehlungen": ["Mehr Java lernen"]
    }
    with open(match_json_path, 'w', encoding='utf-8') as f:
        json.dump(match_data, f, indent=2)
    print(f"      ✅ Created: {match_json_path.name}")

    # 4. Generate Feedback JSON (Mock)
    print("   💡 Generating Feedback JSON...")
    feedback_json_path = output_dir / "feedback_result.json"
    feedback_data = {
        "feedback": {
            "staerken": ["Gute Struktur"],
            "schwaechen": ["Zu lang"],
            "empfehlungen": ["Kürzen"]
        }
    }
    with open(feedback_json_path, 'w', encoding='utf-8') as f:
        json.dump(feedback_data, f, indent=2)
    print(f"      ✅ Created: {feedback_json_path.name}")

    # 5. Generate Dashboard
    print("   📊 Generating Dashboard...")
    try:
        # F003: generate_dashboard now returns (bytes, filename) tuple
        dashboard_bytes, dashboard_filename = generate_dashboard(
            cv_json_path=str(cv_json_path),
            match_json_path=str(match_json_path),
            feedback_json_path=str(feedback_json_path),
            output_dir=str(output_dir)
        )
        # Write bytes to file for test fixtures
        dashboard_path = output_dir / dashboard_filename
        with open(dashboard_path, 'wb') as f:
            f.write(dashboard_bytes)
        print(f"      ✅ Created: {dashboard_filename}")
    except Exception as e:
        print(f"      ❌ Failed: {e}")
        return False
        
    print("✨ Test data update complete!")
    return True

if __name__ == "__main__":
    success = update_test_data()
    if not success:
        sys.exit(1)
