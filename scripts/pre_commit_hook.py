#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pre-Commit Hook: Structured Documentation & Cleanup
Scans for unused files, validates commit metadata, and generates in-app documentation.
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
EXCLUDE_DIRS = {'.git', '__pycache__', '.pytest_cache', 'htmlcov', '.venv', 'node_modules', 'archive'}
EXCLUDE_EXTENSIONS = {'.pyc', '.pyo', '.pyd', '.so', '.o', '.a', '.dylib', '.dll'}
UNUSED_THRESHOLD_DAYS = 180  # Files not modified in 180 days
ARCHIVE_DIR = 'archive/unused'

# Commit metadata structure
class CommitMetadata:
    """Structured commit metadata"""
    def __init__(self):
        self.icon = None  # feature, bug, docs, refactor, test, chore
        self.feature_name = None
        self.feature_details = None
        self.commit_message = None
        self.timestamp = datetime.now().isoformat()
        self.commit_hash = None
        self.author = None

    def to_dict(self):
        return {
            'icon': self.icon,
            'feature_name': self.feature_name,
            'feature_details': self.feature_details,
            'commit_message': self.commit_message,
            'timestamp': self.timestamp,
            'commit_hash': self.commit_hash,
            'author': self.author
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


def get_git_config():
    """Get git user info"""
    try:
        author = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True, text=True
        ).stdout.strip()
        return author or 'Unknown'
    except:
        return 'Unknown'


def get_uncommitted_changes():
    """Get list of uncommitted/staged files"""
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', '--cached'],
            capture_output=True, text=True
        )
        return set(result.stdout.strip().split('\n')) if result.stdout.strip() else set()
    except:
        return set()


def scan_unused_files(root_dir='.', threshold_days=UNUSED_THRESHOLD_DAYS):
    """
    Scan for unused/old files not in excluded directories
    Returns list of (filepath, last_modified_days_ago)
    """
    unused_files = []
    current_time = datetime.now().timestamp()
    threshold_seconds = threshold_days * 86400

    for root, dirs, files in os.walk(root_dir):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]

        for file in files:
            # Skip excluded extensions
            if any(file.endswith(ext) for ext in EXCLUDE_EXTENSIONS):
                continue

            filepath = os.path.join(root, file)
            try:
                mtime = os.path.getmtime(filepath)
                age_seconds = current_time - mtime
                age_days = age_seconds / 86400

                # Only include truly old files (not in git staging)
                if age_days > threshold_days:
                    # Check if it's in git
                    try:
                        subprocess.run(
                            ['git', 'ls-files', '--error-unmatch', filepath],
                            capture_output=True,
                            check=True
                        )
                        # File is tracked, can be archived
                        unused_files.append((filepath, age_days))
                    except subprocess.CalledProcessError:
                        # File not in git, skip
                        pass
            except OSError:
                pass

    return sorted(unused_files, key=lambda x: x[1], reverse=True)


def archive_unused_files(unused_files, dry_run=False):
    """Archive old unused files"""
    if not unused_files:
        print("✅ No unused files to archive")
        return

    print(f"\n📦 Archiving {len(unused_files)} unused files...")

    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    for filepath, age_days in unused_files:
        if dry_run:
            print(f"  [DRY RUN] Would archive: {filepath} (unused for {age_days:.0f} days)")
        else:
            try:
                # Move to archive
                archive_path = os.path.join(ARCHIVE_DIR, os.path.basename(filepath))
                os.rename(filepath, archive_path)
                print(f"  ✅ Archived: {filepath}")
                # Stage the move
                subprocess.run(['git', 'add', filepath, archive_path], capture_output=True)
            except Exception as e:
                print(f"  ⚠️  Could not archive {filepath}: {e}")


def extract_commit_metadata(commit_message):
    """
    Extract structured metadata from commit message
    Expected format: icon(type): feature_name - feature_details
    Example: 🎯(feature): Lean MVP Architecture - Heroku deployment guide
    """
    metadata = CommitMetadata()
    
    # Get commit hash
    try:
        commit_hash = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True, text=True
        ).stdout.strip()
        metadata.commit_hash = commit_hash
    except:
        pass

    # Parse message
    icon_map = {
        '✨': 'feature',
        '🐛': 'bug',
        '📝': 'docs',
        '♻️': 'refactor',
        '🧪': 'test',
        '🔧': 'chore',
        '🎯': 'feature',
        '🚀': 'feature',
        '⚡': 'performance',
        '🔒': 'security',
        '⬆️': 'dependencies',
        '➕': 'dependencies'
    }

    parts = commit_message.split(':', 1)
    if len(parts) >= 2:
        first_part = parts[0].strip()
        rest = parts[1].strip()

        # Check for icon
        for icon, icon_type in icon_map.items():
            if icon in first_part:
                metadata.icon = icon_type
                # Extract type in parentheses if present
                if '(' in first_part and ')' in first_part:
                    type_str = first_part.split('(')[1].split(')')[0]
                    metadata.icon = type_str.lower()
                break

        # Parse feature name and details
        if ' - ' in rest:
            feature_name, details = rest.split(' - ', 1)
            metadata.feature_name = feature_name.strip()
            metadata.feature_details = details.strip()
        else:
            metadata.feature_name = rest.strip()
            metadata.feature_details = ''
    else:
        metadata.feature_name = commit_message.strip()

    # Get author
    metadata.author = get_git_config()
    metadata.commit_message = commit_message

    return metadata


def generate_app_documentation(metadata_list):
    """Generate in-app documentation JSON"""
    doc_structure = {
        'generated_at': datetime.now().isoformat(),
        'total_changes': len(metadata_list),
        'changes': [m.to_dict() for m in metadata_list],
        'index_by_type': {}
    }

    # Build index by type
    for metadata in metadata_list:
        icon = metadata.icon or 'other'
        if icon not in doc_structure['index_by_type']:
            doc_structure['index_by_type'][icon] = []
        doc_structure['index_by_type'][icon].append({
            'name': metadata.feature_name,
            'timestamp': metadata.timestamp,
            'hash': metadata.commit_hash
        })

    return doc_structure


def validate_commit_message(commit_message):
    """Validate commit message format"""
    issues = []

    if not commit_message or len(commit_message.strip()) < 10:
        issues.append("❌ Commit message too short (minimum 10 characters)")

    if ':' not in commit_message:
        issues.append("⚠️  Consider using format: type(scope): message")

    if len(commit_message) > 100:
        issues.append("⚠️  Commit message is long (>100 chars)")

    return issues


def main():
    """Main pre-commit hook logic"""
    print("\n" + "="*60)
    print("PRE-COMMIT HOOK: Cleanup & Documentation")
    print("="*60)
    
    # Import cleanup logger
    from cleanup_logger import CleanupLogger
    from interactive_cleanup import InteractiveCleanupScanner
    logger = CleanupLogger()
    scanner = InteractiveCleanupScanner()

    try:
        # 0. Run interactive cleanup scanner
        print("\n Checking for cleanup candidates...")
        candidates = scanner.scan_cleanup_candidates()
        total_candidates = sum(len(v) for v in candidates.values())
        
        if total_candidates > 0:
            print(f"\n Found {total_candidates} cleanup candidates")
            selected = scanner.display_candidates(candidates)
            
            if selected > 0:
                scanner.archive_selected()
        
        # 1. Get commit message
        print("\n Reading commit message...")
        try:
            # Git provides commit message via argv or file
            if len(sys.argv) > 1:
                commit_msg_file = sys.argv[1]
                with open(commit_msg_file, 'r', encoding='utf-8') as f:
                    commit_message = f.read().strip()
            else:
                # Fallback: try to get from git
                result = subprocess.run(
                    ['git', 'log', '-1', '--pretty=%B'],
                    capture_output=True, text=True
                )
                commit_message = result.stdout.strip()
        except Exception as e:
            print(f"⚠️  Could not read commit message: {e}")
            commit_message = ""

        if commit_message:
            print(f"✅ Message: {commit_message[:60]}...")
        else:
            print("⚠️  No commit message found")

        # 2. Validate message
        print("\n📋 Validating commit message...")
        issues = validate_commit_message(commit_message)
        for issue in issues:
            print(f"  {issue}")
        if not issues:
            print("  ✅ Commit message format OK")

        # 3. Extract metadata
        print("\n📊 Extracting metadata...")
        metadata = extract_commit_metadata(commit_message)
        print(f"  📌 Type: {metadata.icon or 'not specified'}")
        print(f"  📝 Feature: {metadata.feature_name or 'not specified'}")
        print(f"  ✍️  Author: {metadata.author}")
        print(f"  🕐 Timestamp: {metadata.timestamp}")

        # 4. Scan for unused files
        print("\n📦 Scanning for unused files...")
        uncommitted = get_uncommitted_changes()
        unused = scan_unused_files(threshold_days=UNUSED_THRESHOLD_DAYS)

        if unused:
            print(f"  ⚠️  Found {len(unused)} unused files (>{UNUSED_THRESHOLD_DAYS} days old)")
            for filepath, age_days in unused[:5]:  # Show top 5
                print(f"    - {filepath} ({age_days:.0f} days old)")
            if len(unused) > 5:
                print(f"    ... and {len(unused) - 5} more")

            # Ask about archiving (non-interactive for hooks)
            print(f"\n  💡 Tip: Run './scripts/cleanup_unused.py' to archive old files")
        else:
            print("  ✅ No unused files found")

        # 5. Generate app documentation
        print("\n📚 Generating in-app documentation...")
        doc_structure = generate_app_documentation([metadata])

        # Save to JSON for app consumption
        doc_path = 'scripts/commit_metadata.json'
        os.makedirs(os.path.dirname(doc_path) or '.', exist_ok=True)

        # Append to existing metadata if file exists
        if os.path.exists(doc_path):
            try:
                with open(doc_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                    doc_structure['changes'].extend(existing.get('changes', []))
                    # Keep only last 100 entries
                    doc_structure['changes'] = doc_structure['changes'][:100]
            except:
                pass

        with open(doc_path, 'w', encoding='utf-8') as f:
            json.dump(doc_structure, f, indent=2, ensure_ascii=False)

        print(f"  ✅ Documentation saved to {doc_path}")

        # 6. Summary
        print("\n" + "="*60)
        print("PRE-COMMIT CHECKS PASSED")
        print("="*60)
        print(f"\n Commit details:")
        print(f"  Type: {metadata.icon or 'unspecified'}")
        print(f"  Feature: {metadata.feature_name or 'unnamed'}")
        print(f"  Metadata: scripts/commit_metadata.json")
        
        # Log this operation to cleanup logger
        try:
            commit_hash = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True, text=True
            ).stdout.strip()
            
            # Log the pre-commit operation
            logger.log_operation(
                operation_type='pre-commit-validation',
                items=[],  # No items archived in validation
                commit_hash=commit_hash,
                commit_message=commit_message,
                metadata={
                    'validated': True,
                    'metadata_extracted': True,
                    'author': metadata.author
                }
            )
        except Exception as e:
            print(f" Warning: Could not log to cleanup logger: {e}")
        
        print()

        return 0

    except Exception as e:
        print(f"\n ERROR in pre-commit hook: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
