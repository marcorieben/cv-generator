#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cleanup Archiver - Organized archival system for cleanup items
Moves identified cleanup items into structured cleanup/ directory
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class CleanupArchiver:
    """Manages archival of cleanup items into organized structure"""
    
    CLEANUP_BASE = Path('cleanup')
    CATEGORIES = {
        'REDUNDANT': 'redundant (duplicates)',
        'REGENERABLE': 'regenerable (build artifacts, test outputs)',
        'OBSOLETE': 'obsolete (deprecated, backups)',
        'ARCHIVABLE': 'archivable (old files >30 days)'
    }
    
    def __init__(self, repo_root: str = '.'):
        self.repo_root = Path(repo_root)
        self.cleanup_base = self.repo_root / self.CLEANUP_BASE
        self.archive_log = self.cleanup_base / 'ARCHIVE_LOG.json'
        self.load_archive_log()
    
    def load_archive_log(self):
        """Load existing archive log or create new one"""
        if self.archive_log.exists():
            with open(self.archive_log, 'r', encoding='utf-8') as f:
                self.archive_log_data = json.load(f)
        else:
            self.archive_log_data = {
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'total_archived': 0,
                'items': []
            }
    
    def save_archive_log(self):
        """Save archive log"""
        self.cleanup_base.mkdir(exist_ok=True)
        self.archive_log_data['last_updated'] = datetime.now().isoformat()
        
        with open(self.archive_log, 'w', encoding='utf-8') as f:
            json.dump(self.archive_log_data, f, indent=2, ensure_ascii=False)
    
    def create_category_structure(self):
        """Create organized cleanup/ directory structure"""
        for category in self.CATEGORIES.keys():
            category_dir = self.cleanup_base / category.lower()
            category_dir.mkdir(parents=True, exist_ok=True)
            
            # Create README for each category
            readme_path = category_dir / 'README.md'
            if not readme_path.exists():
                readme_path.write_text(f"""# {category} Files

**Category:** {self.CATEGORIES[category]}

This directory contains files that have been archived as **{category}**.

## When to restore:
- REDUNDANT: Never restore (deleted duplicates)
- REGENERABLE: Safe to delete (can be regenerated)
- OBSOLETE: Never restore (deprecated content)
- ARCHIVABLE: Can restore if needed (old but potentially valuable)

## Restore process:
1. Move file back to original location
2. Update ARCHIVE_LOG.json status to 'restored'
3. Commit with message: "♻️(chore): Restore {filename}"

---
*Last updated: {datetime.now().isoformat()}*
""")
    
    def archive_file(self, source_file: str, category: str, reason: str = '') -> bool:
        """
        Archive a file into cleanup structure
        Preserves directory structure
        """
        if category not in self.CATEGORIES:
            sys.stderr.write(f"Unknown category: {category}\n")
            sys.stderr.flush()
            return False
        
        source_path = self.repo_root / source_file
        
        if not source_path.exists():
            sys.stderr.write(f"File not found: {source_file}\n")
            sys.stderr.flush()
            return False
        
        # Create target path preserving directory structure
        category_dir = self.cleanup_base / category.lower()
        target_path = category_dir / source_file
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Archive the file
        try:
            shutil.move(str(source_path), str(target_path))
            
            # Log the archival
            self.archive_log_data['items'].append({
                'file': source_file,
                'category': category,
                'reason': reason,
                'archived_at': datetime.now().isoformat(),
                'status': 'archived',
                'target': str(target_path.relative_to(self.repo_root))
            })
            self.archive_log_data['total_archived'] += 1
            self.save_archive_log()
            
            sys.stderr.write(f"Archived: {source_file} -> {category}/\n")
            sys.stderr.flush()
            return True
        
        except Exception as e:
            sys.stderr.write(f"Error archiving {source_file}: {e}\n")
            sys.stderr.flush()
            return False
    
    def archive_batch(self, items: Dict[str, List[Dict]]) -> Dict:
        """Archive multiple items from cleanup analysis"""
        results = {
            'total': 0,
            'succeeded': 0,
            'failed': 0,
            'by_category': {}
        }
        
        self.create_category_structure()
        
        for category, files in items.items():
            results['by_category'][category] = {'succeeded': 0, 'failed': 0}
            
            for item in files:
                file_path = item['file']
                reason = item.get('reason', '')
                
                if self.archive_file(file_path, category, reason):
                    results['succeeded'] += 1
                    results['by_category'][category]['succeeded'] += 1
                else:
                    results['failed'] += 1
                    results['by_category'][category]['failed'] += 1
                
                results['total'] += 1
        
        return results
    
    def list_archived(self, category: str = None) -> List[Dict]:
        """List archived files"""
        if category:
            return [item for item in self.archive_log_data['items'] 
                    if item['category'] == category and item['status'] == 'archived']
        else:
            return [item for item in self.archive_log_data['items'] 
                    if item['status'] == 'archived']
    
    def restore_file(self, file_path: str) -> bool:
        """Restore an archived file to original location"""
        # Find the archived file in cleanup/
        for item in self.archive_log_data['items']:
            if item['file'] == file_path:
                archive_target = self.repo_root / item['target']
                original_target = self.repo_root / file_path
                
                if not archive_target.exists():
                    print(f"❌ Archived file not found: {archive_target}")
                    return False
                
                try:
                    original_target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(archive_target), str(original_target))
                    
                    item['status'] = 'restored'
                    item['restored_at'] = datetime.now().isoformat()
                    self.save_archive_log()
                    
                    print(f"✓ Restored: {file_path}")
                    return True
                except Exception as e:
                    print(f"❌ Error restoring {file_path}: {e}")
                    return False
        
        print(f"❌ File not found in archive log: {file_path}")
        return False
    
    def generate_summary(self) -> str:
        """Generate cleanup summary"""
        summary = f"""
=================================================================
CLEANUP ARCHIVE SUMMARY
=================================================================

Created: {self.archive_log_data['created_at']}
Last Updated: {self.archive_log_data['last_updated']}
Total Archived: {self.archive_log_data['total_archived']}

BREAKDOWN BY CATEGORY:
"""
        
        for category in self.CATEGORIES.keys():
            items = [i for i in self.archive_log_data['items'] 
                    if i['category'] == category and i['status'] == 'archived']
            summary += f"\n{category} ({len(items)}):\n"
            for item in items[:5]:
                summary += f"  - {item['file']}\n"
            if len(items) > 5:
                summary += f"  ... and {len(items) - 5} more\n"
        
        summary += "\n" + "=" * 65 + "\n"
        return summary


def main():
    """CLI interface for cleanup archiver"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cleanup archiver for workspace organization')
    parser.add_argument('command', choices=['archive', 'list', 'restore', 'summary'],
                       help='Command to execute')
    parser.add_argument('--category', help='Filter by category')
    parser.add_argument('--file', help='File to archive or restore')
    parser.add_argument('--reason', help='Reason for archival')
    
    args = parser.parse_args()
    
    archiver = CleanupArchiver()
    
    if args.command == 'archive':
        if not args.file:
            print("❌ --file required for archive command")
            sys.exit(1)
        if not args.category:
            print("❌ --category required for archive command")
            sys.exit(1)
        
        success = archiver.archive_file(args.file, args.category, args.reason or '')
        sys.exit(0 if success else 1)
    
    elif args.command == 'list':
        items = archiver.list_archived(args.category)
        print(f"\nArchived Items ({len(items)}):")
        for item in items:
            print(f"  - {item['file']} ({item['category']}) - {item['reason']}")
    
    elif args.command == 'restore':
        if not args.file:
            print("❌ --file required for restore command")
            sys.exit(1)
        
        success = archiver.restore_file(args.file)
        sys.exit(0 if success else 1)
    
    elif args.command == 'summary':
        print(archiver.generate_summary())


if __name__ == '__main__':
    if len(sys.argv) > 1:
        main()
    else:
        # Demo mode
        archiver = CleanupArchiver()
        archiver.create_category_structure()
        print(archiver.generate_summary())
