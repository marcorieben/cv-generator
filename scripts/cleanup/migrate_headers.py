"""
Module description

Purpose: populate all project files with standardized metadata headers
Expected Lifetime: temporary
Category: PROMPT
Created: 2026-01-24
Last Updated: 2026-01-24
"""
#!/usr/bin/env python3
"""
Batch migration script to add file headers to all analyzed files

Purpose: Populate all project files with standardized metadata headers
         for faster cleanup runs and version control tracking
Expected Lifetime: temporary
Category: PROMPT
Created: 2026-01-24
Last Updated: 2026-01-24
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.cleanup.executor import scan_project_files, analyze_file
from scripts.cleanup.file_headers import write_file_header
from scripts.cleanup.models import FileCategory, CleanupConfig

def main():
    """Migrate all project files with headers"""
    
    print("\n" + "=" * 70)
    print("🔄 FILE HEADER MIGRATION")
    print("=" * 70)
    print("")
    print("This script will add standardized metadata headers to all project files")
    print("Format: Purpose, Expected Lifetime, Category")
    print("")
    print("Target files: .py, .ts, .js, .sh files in scripts/, core/, tests/, docs/")
    print("")
    
    input("Press Enter to continue...")
    print("")
    
    # Scan all project files
    print("📄 Scanning project files...")
    files = list(scan_project_files())
    print(f"✅ Found {len(files)} files to analyze")
    print("")
    
    # Analyze and write headers
    print("🔍 Analyzing and writing headers...")
    print("")
    
    # Create default config for analysis
    config = CleanupConfig()
    
    headers_written = 0
    skipped = 0
    errors = 0
    
    for i, file_path in enumerate(files, 1):
        # Only process text files
        suffix = Path(file_path).suffix
        if suffix not in ['.py', '.ts', '.js', '.sh', '.bat', '.cmd']:
            skipped += 1
            continue
        
        # Analyze file
        try:
            analysis = analyze_file(file_path, config)
            
            # Write header with detected metadata including dates
            purpose = analysis.file_purpose or f"Analyzed as {analysis.category.value}"
            lifetime = analysis.expected_lifetime or "permanent"
            created = analysis.created_date or ""
            last_updated = analysis.last_updated_date or ""
            
            if write_file_header(file_path, purpose, lifetime, analysis.category, created, last_updated):
                headers_written += 1
                status = "✅"
            else:
                status = "⏭️ "  # Skipped (binary or no write needed)
                skipped += 1
            
            # Progress
            pct = int(100 * i / len(files))
            bar_len = 40
            filled = int(bar_len * i / len(files))
            bar = "█" * filled + "░" * (bar_len - filled)
            print(f"\r[{bar}] {pct:3d}% ({i}/{len(files)}) {status}", end="", flush=True)
            
        except Exception as e:
            errors += 1
            print(f"\n  ❌ Error processing {Path(file_path).name}: {e}")
    
    print("")
    print("")
    print("=" * 70)
    print("📊 MIGRATION SUMMARY")
    print("=" * 70)
    print(f"Headers Written: {headers_written}")
    print(f"Skipped (binary/non-text): {skipped}")
    print(f"Errors: {errors}")
    print(f"Total Files: {len(files)}")
    print("=" * 70)
    print("")
    print("✅ Migration complete!")
    print("")
    print("Next steps:")
    print("1. Review file headers in your editor to verify metadata")
    print("2. Commit changes to git: git add . && git commit -m 'Add file metadata headers'")
    print("3. Future cleanup runs will read from headers (faster classification)")
    print("")

if __name__ == "__main__":
    main()
