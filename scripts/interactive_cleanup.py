#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive Cleanup Scanner - Shows cleanup candidates and asks user
Integrated into pre-commit hook workflow
Uses argparse for robust CLI integration without stdin issues
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta

# Fix encoding for Windows BEFORE any I/O
if sys.platform == 'win32':
    import io
    # Use buffering=1 for line-buffered output
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)


class InteractiveCleanupScanner:
    """Interactive cleanup candidate scanner - argparse based"""
    
    CATEGORIES = {
        'REDUNDANT': 'Duplicate files - keep only one',
        'REGENERABLE': 'Build artifacts - can be recreated',
        'OBSOLETE': 'Deprecated code - old backups',
        'ARCHIVABLE': 'Old files >30 days - keep as reference'
    }
    
    def __init__(self):
        self.repo_root = Path('.')
        self.selected_for_archival = []
    
    def scan_cleanup_candidates(self) -> Dict[str, List[Dict]]:
        """Scan for cleanup candidates - silent scanning, no output"""
        candidates = {
            'REDUNDANT': [],
            'REGENERABLE': [],
            'OBSOLETE': [],
            'ARCHIVABLE': []
        }
        
        # Check for duplicate CHANGELOG files
        changelog_count = 0
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in {'.git', '.venv', '__pycache__', 'cleanup', 'htmlcov'}]
            
            for file in files:
                filepath = os.path.join(root, file)
                
                # Skip certain paths
                if '.git' in filepath or '.venv' in filepath or '__pycache__' in filepath or 'cleanup' in filepath:
                    continue
                
                # REDUNDANT: Duplicate CHANGELOG files
                if file == 'CHANGELOG.md':
                    changelog_count += 1
                    if changelog_count > 1:
                        candidates['REDUNDANT'].append({
                            'file': filepath,
                            'reason': 'Duplicate CHANGELOG file'
                        })
                
                # REGENERABLE: Build outputs
                if file in {'batch_test_output.txt', 'test_output.txt'}:
                    candidates['REGENERABLE'].append({
                        'file': filepath,
                        'reason': 'Build/test artifact'
                    })
                
                # OBSOLETE: Old backup files
                if file.endswith('.bkp'):
                    candidates['OBSOLETE'].append({
                        'file': filepath,
                        'reason': 'Obsolete backup file'
                    })
                
                # ARCHIVABLE: Files older than 30 days
                if os.path.isfile(filepath):
                    try:
                        mtime = os.path.getmtime(filepath)
                        age_days = (datetime.now() - datetime.fromtimestamp(mtime)).days
                        if age_days > 30 and not any(x in filepath for x in {'.git', '.venv', 'htmlcov', '__pycache__', '.docx', '.pdf'}):
                            if file.endswith(('.log', '.bak', '.tmp')):
                                candidates['ARCHIVABLE'].append({
                                    'file': filepath,
                                    'reason': f'Old file ({age_days} days)'
                                })
                    except:
                        pass
        
        return candidates
    
    def display_candidates(self, candidates: Dict[str, List[Dict]]) -> int:
        """Display candidates using stderr - returns count of selected items"""
        total = sum(len(items) for items in candidates.values())
        
        if total == 0:
            return 0
        
        try:
            print(f"\nFound {total} cleanup candidates:")
            print("=" * 70)
            
            item_index = 0
            for category, items in candidates.items():
                if not items:
                    continue
                
                print(f"\n{category} ({len(items)}):")
                print(f"{self.CATEGORIES[category]}")
                print("-" * 70)
                
                for item in items:
                    print(f"  [{item_index}] {item['file']}")
                    print(f"       {item['reason']}")
                    item_index += 1
            
            print("\n" + "=" * 70)
            print("Options:")
            print("  [a] Archive all")
            print("  [n] Skip cleanup")
            print("  [s] Select specific items")
        except Exception as e:
            pass
        
        return total
    
    def archive_selected(self) -> bool:
        """Archive selected items using subprocess to avoid I/O cascade"""
        if not self.selected_for_archival:
            return False
        
        try:
            import subprocess
            
            # Write items to temp JSON file
            temp_file = Path('.cleanup_temp.json')
            items = []
            for category, file_path in self.selected_for_archival:
                items.append({
                    'category': category,
                    'file': file_path,
                    'reason': 'User-selected'
                })
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(items, f)
            
            # Call simple_archiver in separate process
            result = subprocess.run(
                [sys.executable, 'scripts/simple_archiver.py', str(temp_file)],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            return result.returncode == 0
        except Exception as e:
            return False


def main():
    """Main entry point - uses argparse for robust flag-based system"""
    parser = argparse.ArgumentParser(
        description='Interactive cleanup scanner for CV Generator',
        add_help=True
    )
    parser.add_argument(
        '--auto-archive-all',
        action='store_true',
        help='Archive all candidates without prompting'
    )
    parser.add_argument(
        '--skip',
        action='store_true',
        help='Skip cleanup entirely'
    )
    parser.add_argument(
        '--silent',
        action='store_true',
        help='Run silently (no output)'
    )
    
    try:
        args = parser.parse_args()
    except SystemExit:
        sys.exit(0)
    
    # Create scanner
    scanner = InteractiveCleanupScanner()
    
    # Scan for candidates
    candidates = scanner.scan_cleanup_candidates()
    
    # Handle skip flag
    if args.skip:
        sys.exit(0)
    
    # Handle auto-archive-all flag
    if args.auto_archive_all:
        # Automatically select all for archival
        for category, items in candidates.items():
            for item in items:
                scanner.selected_for_archival.append((category, item['file']))
        
        if scanner.selected_for_archival:
            success = scanner.archive_selected()
            sys.exit(0 if success else 1)
        else:
            sys.exit(0)
    
    # Interactive mode (default): display and ask
    total = scanner.display_candidates(candidates)
    
    if total == 0:
        sys.exit(0)
    
    # Get user choice - use print for prompts
    try:
        print("\nYour choice [a/n/s]: ", end='', flush=True)
        choice = input().strip().lower()
    except (EOFError, ValueError):
        # If stdin is not available, default to skip
        sys.exit(0)
    
    if choice == 'a':
        # Archive all
        for category, items in candidates.items():
            for item in items:
                scanner.selected_for_archival.append((category, item['file']))
        if scanner.selected_for_archival:
            success = scanner.archive_selected()
            sys.exit(0 if success else 1)
    elif choice == 's':
        # Select specific
        try:
            print("Indices to archive (comma-separated, e.g. 0,2,3): ", end='', flush=True)
            indices_str = input().strip()
            indices = [int(x.strip()) for x in indices_str.split(',')]
            
            item_index = 0
            for category, items in candidates.items():
                for item in items:
                    if item_index in indices:
                        scanner.selected_for_archival.append((category, item['file']))
                    item_index += 1
            
            if scanner.selected_for_archival:
                success = scanner.archive_selected()
                sys.exit(0 if success else 1)
        except (ValueError, IndexError):
            sys.exit(0)
    
    # Default: skip (choice == 'n' or anything else)
    sys.exit(0)


if __name__ == '__main__':
    main()
