#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cleanup Logger - Maintains centralized cleanup activity log
Automatically filled by pre-commit hook during cleanup operations
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class CleanupLogger:
    """Manages cleanup activity logging"""
    
    LOG_FILE = Path('cleanup') / 'CLEANUP_LOG.json'
    README_FILE = Path('cleanup') / 'CLEANUP_LOG.md'
    
    def __init__(self, repo_root: str = '.'):
        self.repo_root = Path(repo_root)
        self.log_file = self.repo_root / self.LOG_FILE
        self.readme_file = self.repo_root / self.README_FILE
        self.load_log()
    
    def load_log(self):
        """Load or initialize cleanup log"""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    self.log_data = json.load(f)
            except json.JSONDecodeError:
                self.log_data = self._init_log()
        else:
            self.log_data = self._init_log()
    
    def _init_log(self) -> Dict:
        """Initialize fresh log structure"""
        return {
            'log_version': '1.0',
            'created_at': datetime.now().isoformat(),
            'last_updated': None,
            'total_operations': 0,
            'total_items_archived': 0,
            'operations': []
        }
    
    def save_log(self):
        """Save log to JSON file"""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_data['last_updated'] = datetime.now().isoformat()
        
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.log_data, f, indent=2, ensure_ascii=False)
        
        self._update_readme()
    
    def log_operation(self, 
                     operation_type: str,
                     items: List[Dict],
                     commit_hash: str = '',
                     commit_message: str = '',
                     metadata: Optional[Dict] = None) -> bool:
        """
        Log a cleanup operation
        
        Args:
            operation_type: 'archive', 'scan', 'restore'
            items: List of items processed [{file, category, reason}]
            commit_hash: Git commit hash if from pre-commit
            commit_message: Commit message
            metadata: Additional metadata
        
        Returns:
            bool: Success status
        """
        try:
            operation = {
                'timestamp': datetime.now().isoformat(),
                'type': operation_type,
                'commit_hash': commit_hash,
                'commit_message': commit_message,
                'items_count': len(items),
                'items': items,
                'metadata': metadata or {}
            }
            
            self.log_data['operations'].append(operation)
            self.log_data['total_operations'] += 1
            self.log_data['total_items_archived'] += len(items)
            
            self.save_log()
            return True
        except Exception as e:
            print(f"Error logging operation: {e}")
            return False
    
    def _update_readme(self):
        """Generate human-readable README from log"""
        markdown = """# Cleanup Activity Log

Automatic log of all cleanup operations performed by the pre-commit hook system.

## Summary

"""
        
        markdown += f"""- **Total Operations:** {self.log_data['total_operations']}
- **Total Items Archived:** {self.log_data['total_items_archived']}
- **Log Created:** {self.log_data['created_at']}
- **Last Updated:** {self.log_data['last_updated']}

## Recent Operations

"""
        
        # Show recent operations
        for op in sorted(self.log_data['operations'], 
                        key=lambda x: x['timestamp'], 
                        reverse=True)[:20]:
            
            timestamp = op['timestamp'].split('T')[0]
            op_type = op['type'].upper()
            count = op['items_count']
            commit = op['commit_hash'][:8] if op['commit_hash'] else 'manual'
            
            markdown += f"""
### {timestamp} - {op_type} ({count} items)
- **Commit:** {commit}
- **Message:** {op['commit_message'][:60] or 'N/A'}
- **Items:**
"""
            
            for item in op['items'][:5]:
                markdown += f"  - `{item.get('file', 'unknown')}` ({item.get('category', 'unknown')})\n"
            
            if len(op['items']) > 5:
                markdown += f"  ... and {len(op['items']) - 5} more\n"
        
        markdown += """

## Categories

- **REDUNDANT:** Duplicate files (can be safely deleted)
- **REGENERABLE:** Build artifacts, test outputs (can be regenerated)
- **OBSOLETE:** Deprecated code, old backups (no value)
- **ARCHIVABLE:** Old files >30 days (archive but keep for reference)

## Restore Procedure

To restore an archived file:

```bash
python scripts/cleanup_archiver.py restore --file <original_path>
```

Then:
1. Review the restored file
2. Commit with: `♻️(chore): Restore <filename>`

---

*This log is automatically maintained. Do not edit manually.*
"""
        
        with open(self.readme_file, 'w', encoding='utf-8') as f:
            f.write(markdown)
    
    def get_statistics(self) -> Dict:
        """Get cleanup statistics"""
        stats = {
            'total_operations': self.log_data['total_operations'],
            'total_items_archived': self.log_data['total_items_archived'],
            'by_type': {},
            'by_category': {}
        }
        
        # Count by operation type
        for op in self.log_data['operations']:
            op_type = op['type']
            stats['by_type'][op_type] = stats['by_type'].get(op_type, 0) + 1
            
            # Count by category
            for item in op['items']:
                category = item.get('category', 'unknown')
                stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
        
        return stats
    
    def print_summary(self):
        """Print cleanup log summary"""
        stats = self.get_statistics()
        
        print("\n" + "=" * 70)
        print("📋 CLEANUP LOG SUMMARY")
        print("=" * 70)
        print(f"\n📊 Statistics:")
        print(f"  • Total Operations: {stats['total_operations']}")
        print(f"  • Total Items Archived: {stats['total_items_archived']}")
        
        if stats['by_type']:
            print(f"\n📈 By Operation Type:")
            for op_type, count in stats['by_type'].items():
                print(f"  • {op_type}: {count}")
        
        if stats['by_category']:
            print(f"\n🏷️  By Category:")
            for category, count in stats['by_category'].items():
                print(f"  • {category}: {count}")
        
        if self.log_data['operations']:
            print(f"\n⏰ Last 3 Operations:")
            for op in self.log_data['operations'][-3:]:
                timestamp = op['timestamp'].split('T')[0]
                print(f"  • {timestamp} - {op['type']} ({op['items_count']} items)")
        
        print("\n" + "=" * 70)


if __name__ == '__main__':
    logger = CleanupLogger()
    logger.print_summary()
