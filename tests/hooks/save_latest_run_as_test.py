"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-21
Last Updated: 2026-01-24
"""
import os
import shutil
import glob
from pathlib import Path
from datetime import datetime

def save_latest_run_as_test():
    """
    Finds the most recent output directory and copies its JSON files 
    to tests/test_data/complete_run to serve as offline test data.
    """
    project_root = Path(__file__).parent.parent.parent
    output_dir = project_root / "output"
    test_data_dir = project_root / "tests" / "test_data" / "complete_run"

    # Ensure test data dir exists
    test_data_dir.mkdir(parents=True, exist_ok=True)

    # Find latest output directory
    subdirs = [d for d in output_dir.iterdir() if d.is_dir()]
    if not subdirs:
        print("❌ No output directories found in output/")
        return

    latest_dir = max(subdirs, key=os.path.getmtime)
    print(f"📂 Found latest run: {latest_dir.name}")

    # Find JSON files
    json_files = list(latest_dir.glob("*.json"))
    if not json_files:
        print("⚠️ No JSON files found in latest run directory.")
        return

    print(f"🔄 Copying {len(json_files)} JSON files to {test_data_dir}...")
    
    copied_count = 0
    for json_file in json_files:
        dest = test_data_dir / json_file.name
        shutil.copy2(json_file, dest)
        print(f"  ✅ Copied {json_file.name}")
        copied_count += 1

    print(f"\n✨ Successfully updated test data with {copied_count} files.")
    print("   You can now run 'pytest tests/test_offline_generation.py' to test without AI costs.")

if __name__ == "__main__":
    save_latest_run_as_test()
