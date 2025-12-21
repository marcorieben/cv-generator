import os
import sys

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from scripts.visualize_results import generate_dashboard

def test_dashboard():
    # Define paths to existing test data
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "output", "Arthur_Fischer_20251218_113349")
    
    cv_json_path = os.path.join(output_dir, "Arthur_Fischer_20251218_113349.json")
    match_json_path = os.path.join(output_dir, "Match_Arthur_Fischer_20251218_113349.json")
    feedback_json_path = os.path.join(output_dir, "CV_Feedback_Arthur_Fischer_20251218_113349.json")
    
    # Check if files exist
    if not os.path.exists(cv_json_path):
        print(f"❌ Test data not found: {cv_json_path}")
        return
        
    print("🚀 Starting Dashboard Generation Test...")
    print(f"📂 Input Dir: {output_dir}")
    
    try:
        dashboard_path = generate_dashboard(
            cv_json_path=cv_json_path,
            match_json_path=match_json_path,
            feedback_json_path=feedback_json_path,
            output_dir=output_dir
        )
        
        print(f"\n✅ Test Successful!")
        print(f"📊 Dashboard created at: {dashboard_path}")
        
        # Open the dashboard
        import platform
        import subprocess
        if platform.system() == 'Windows':
            os.startfile(dashboard_path)
        elif platform.system() == 'Darwin':
            subprocess.run(['open', dashboard_path])
        else:
            subprocess.run(['xdg-open', dashboard_path])
            
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dashboard()
