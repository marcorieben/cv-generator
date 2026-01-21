#!/usr/bin/env python3
"""
Cleanup Script: Archive unused files
Interactive utility to identify and archive old files.
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

# Configuration
EXCLUDE_DIRS = {'.git', '__pycache__', '.pytest_cache', 'htmlcov', '.venv', 'node_modules', 'archive'}
EXCLUDE_EXTENSIONS = {'.pyc', '.pyo', '.pyd', '.so', '.o', '.a', '.dylib', '.dll'}
UNUSED_THRESHOLD_DAYS = 180
ARCHIVE_DIR = 'archive/unused'


def scan_unused_files(root_dir='.', threshold_days=UNUSED_THRESHOLD_DAYS):
    """Scan for unused files"""
    unused_files = []
    current_time = datetime.now().timestamp()
    threshold_seconds = threshold_days * 86400

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]

        for file in files:
            if any(file.endswith(ext) for ext in EXCLUDE_EXTENSIONS):
                continue

            filepath = os.path.join(root, file)
            try:
                mtime = os.path.getmtime(filepath)
                age_seconds = current_time - mtime
                age_days = age_seconds / 86400

                if age_days > threshold_days:
                    unused_files.append((filepath, age_days))
            except OSError:
                pass

    return sorted(unused_files, key=lambda x: x[1], reverse=True)


def archive_files(unused_files, interactive=True):
    """Archive files with optional user confirmation"""
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    archived = []
    skipped = []

    for filepath, age_days in unused_files:
        if interactive:
            print(f"\n📄 {filepath}")
            print(f"   Last modified: {age_days:.0f} days ago")
            choice = input("   Archive? (y/n/all/skip): ").lower().strip()

            if choice == 'skip':
                break
            elif choice == 'all':
                interactive = False
            elif choice != 'y':
                skipped.append(filepath)
                continue

        try:
            # Create archive subdirectory structure
            rel_path = os.path.relpath(filepath)
            archive_path = os.path.join(ARCHIVE_DIR, rel_path)
            os.makedirs(os.path.dirname(archive_path), exist_ok=True)

            # Move file
            shutil.move(filepath, archive_path)
            archived.append((filepath, archive_path))
            print(f"  ✅ Archived to: {archive_path}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            skipped.append(filepath)

    return archived, skipped


def main():
    """Main cleanup script"""
    print("\n" + "="*60)
    print("🧹 CLEANUP: Archive Unused Files")
    print("="*60)

    print(f"\nScanning for files older than {UNUSED_THRESHOLD_DAYS} days...")
    unused = scan_unused_files()

    if not unused:
        print("✅ No unused files found")
        return 0

    print(f"\n⚠️  Found {len(unused)} unused files:")
    print("\nTop 10 oldest files:")
    for i, (filepath, age_days) in enumerate(unused[:10], 1):
        print(f"  {i}. {filepath} ({age_days:.0f} days old)")

    if len(unused) > 10:
        print(f"  ... and {len(unused) - 10} more")

    print(f"\nArchive location: {ARCHIVE_DIR}/")

    if len(sys.argv) > 1 and sys.argv[1] == '--all':
        print("\n🔄 Archiving all unused files (non-interactive)...")
        archived, skipped = archive_files(unused, interactive=False)
    else:
        print("\n🔄 Review each file (interactive):")
        archived, skipped = archive_files(unused, interactive=True)

    print("\n" + "="*60)
    print(f"✅ Archived: {len(archived)} files")
    print(f"⏭️  Skipped: {len(skipped)} files")
    print("="*60)

    if archived:
        print(f"\n💾 Total size freed: ~{sum(os.path.getsize(Path(src)) for src, _ in archived) / (1024*1024):.2f} MB")

    return 0


if __name__ == '__main__':
    sys.exit(main())
