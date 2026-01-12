import os
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.generate_cv import generate_cv
from scripts.generate_matchmaking import generate_matchmaking_json
from scripts.generate_cv_feedback import generate_cv_feedback_json
from scripts.visualize_results import generate_dashboard

def update_test_data():
    """
    Regenerates all test artifacts based on the current logic and fixtures.
    This ensures that the 'Mock Mode' and offline tests always use the latest
    generation logic.
    """
    print("🔄 Updating Test Data Artifacts...")
    
    fixtures_dir = project_root / "tests" / "fixtures"
    output_dir = fixtures_dir / "output"
    output_dir.mkdir(exist_ok=True)
    
    # 1. Load Source Fixtures
    cv_json_path = fixtures_dir / "valid_cv.json"
    if not cv_json_path.exists():
        print(f"❌ Error: {cv_json_path} not found!")
        return False
        
    # Create a dummy job profile if needed
    job_json_path = fixtures_dir / "valid_job.json"
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
        word_path = generate_cv(str(cv_json_path), str(output_dir))
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
        dashboard_path = generate_dashboard(
            cv_json_path=str(cv_json_path),
            match_json_path=str(match_json_path),
            feedback_json_path=str(feedback_json_path),
            output_dir=str(output_dir)
        )
        print(f"      ✅ Created: {Path(dashboard_path).name}")
    except Exception as e:
        print(f"      ❌ Failed: {e}")
        return False
        
    print("✨ Test data update complete!")
    return True

if __name__ == "__main__":
    success = update_test_data()
    if not success:
        sys.exit(1)
