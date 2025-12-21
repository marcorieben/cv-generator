import os
import sys
import time

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from scripts.dialogs import show_success

def test_success_dialog():
    print("Testing Success Dialog...")
    
    # Mock paths
    word_path = os.path.abspath("test_cv.docx")
    dashboard_path = os.path.abspath("test_dashboard.html")
    
    # Create dummy files if they don't exist
    with open(word_path, 'w') as f: f.write("dummy word")
    with open(dashboard_path, 'w') as f: f.write("dummy dashboard")
    
    try:
        show_success(
            message="Das ist ein Test.",
            details="Details hier...",
            file_path=word_path,
            dashboard_path=dashboard_path
        )
        print("Dialog closed successfully.")
    except Exception as e:
        print(f"Error showing dialog: {e}")
    finally:
        # Cleanup
        if os.path.exists(word_path): os.remove(word_path)
        if os.path.exists(dashboard_path): os.remove(dashboard_path)

if __name__ == "__main__":
    test_success_dialog()
