#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive workspace cleanup analysis
Identifies potentially unused files across the entire project
"""

import os
import re
import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Set, Dict, List, Tuple

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class WorkspaceAnalyzer:
    """Analyze workspace for unused files"""
    
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.all_files = set()
        self.imported_files = set()
        self.python_imports = defaultdict(set)
        self.config_files = set()
        self.doc_files = set()
        self.test_files = set()
        
        # Exclude patterns
        self.exclude_dirs = {
            '.git', '.venv', '__pycache__', '.pytest_cache', 
            'htmlcov', 'node_modules', '.pytest_cache', 'archive',
            '.drawio', 'htmlcov'
        }
        self.exclude_extensions = {
            '.pyc', '.pyo', '.pyd', '.so', '.o', '.a', '.dylib', 
            '.dll', '.bkp', '.tmp', '.log'
        }
    
    def should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded"""
        # Exclude hidden directories
        if any(part.startswith('.') for part in path.parts):
            return True
        
        # Exclude specific directories
        if any(excl in path.parts for excl in self.exclude_dirs):
            return True
        
        # Exclude file types
        if path.suffix in self.exclude_extensions:
            return True
            
        return False
    
    def collect_all_files(self):
        """Collect all project files"""
        print("🔍 Collecting all files...")
        for root, dirs, files in os.walk(self.repo_root):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                filepath = Path(root) / file
                if self.should_exclude(filepath):
                    continue
                
                rel_path = filepath.relative_to(self.repo_root)
                self.all_files.add(str(rel_path))
                
                # Categorize
                if filepath.suffix == '.py':
                    self.python_imports[str(rel_path)] = set()
                elif filepath.suffix in {'.md', '.txt'}:
                    self.doc_files.add(str(rel_path))
                elif filepath.suffix in {'.json', '.yaml', '.yml', '.toml', '.ini', '.cfg'}:
                    self.config_files.add(str(rel_path))
                elif 'test' in str(rel_path):
                    self.test_files.add(str(rel_path))
        
        print(f"  Total files: {len(self.all_files)}")
        print(f"  Python files: {len(self.python_imports)}")
        print(f"  Doc/Text files: {len(self.doc_files)}")
        print(f"  Config files: {len(self.config_files)}")
    
    def analyze_imports(self):
        """Analyze Python imports to find dependencies"""
        print("\n📦 Analyzing Python imports...")
        
        for py_file in self.python_imports.keys():
            filepath = self.repo_root / py_file
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Find all import statements
                    import_pattern = r'(?:from|import)\s+[\w\.]+'
                    imports = re.findall(import_pattern, content)
                    
                    for imp in imports:
                        # Extract module name
                        module = imp.replace('from', '').replace('import', '').strip().split('.')[0]
                        
                        # Check if it's a local import
                        if module in {'scripts', 'tests', 'core', 'templates'}:
                            self.python_imports[py_file].add(module)
                            self.imported_files.add(module)
                        
                        # Check for relative imports
                        if module and not module.startswith('_'):
                            # Try to find matching local file
                            for other_file in self.python_imports.keys():
                                if module in other_file or other_file.endswith(f'{module}.py'):
                                    self.python_imports[py_file].add(other_file)
                                    self.imported_files.add(other_file)
            except Exception as e:
                print(f"  ⚠️ Error parsing {py_file}: {e}")
    
    def analyze_references(self):
        """Analyze references in documentation and configs"""
        print("\n🔗 Analyzing file references...")
        
        # Check doc files for references
        for doc_file in self.doc_files:
            filepath = self.repo_root / doc_file
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Find file references
                    file_pattern = r'(?:scripts/|tests/|docs/)[a-zA-Z0-9_\-./]+'
                    references = re.findall(file_pattern, content)
                    
                    for ref in references:
                        if ref in self.all_files:
                            self.imported_files.add(ref)
            except Exception as e:
                pass
    
    def find_unused_files(self) -> List[str]:
        """Identify unused files"""
        unused = []
        
        for file in self.all_files:
            # Skip entry points
            if file in {'app.py', 'run_pipeline.py', 'config.yaml', 'pytest.ini'}:
                continue
            
            # Skip if it's imported somewhere
            if file in self.imported_files:
                continue
            
            # Skip if it's a main module
            if file.startswith('scripts/__') or file.startswith('tests/'):
                continue
            
            unused.append(file)
        
        return sorted(unused)
    
    def classify_cleanup_items(self):
        """Classify files by cleanup category with detailed criteria"""
        from datetime import datetime, timedelta
        import time
        
        cleanup_items = {
            'REDUNDANT': [],        # Duplicate files (keep only one)
            'REGENERABLE': [],      # Build artifacts, test outputs
            'OBSOLETE': [],         # Old TODOs, deprecated code
            'ARCHIVABLE': [],       # Old files >30 days
        }
        
        threshold_days = 30
        cutoff_time = time.time() - (threshold_days * 86400)
        
        for file in self.all_files:
            filepath = self.repo_root / file
            
            # 1. REDUNDANT - Multiple CHANGELOG files
            if file.endswith('CHANGELOG.md'):
                if not file == 'CHANGELOG.md':  # Keep only root CHANGELOG
                    cleanup_items['REDUNDANT'].append({
                        'file': file,
                        'reason': 'Duplicate CHANGELOG (keep only root/CHANGELOG.md)',
                        'severity': 'high'
                    })
                    continue
            
            # 2. REGENERABLE - Test outputs and build artifacts
            if any(x in file for x in ['test_output', 'batch_test_output', 'htmlcov/', '.pyc', '__pycache__']):
                cleanup_items['REGENERABLE'].append({
                    'file': file,
                    'reason': 'Test output / build artifact (can be regenerated)',
                    'severity': 'low'
                })
                continue
            
            if file.startswith('tests/fixtures/output/') and file.endswith(('.docx', '.html', '.json')):
                cleanup_items['REGENERABLE'].append({
                    'file': file,
                    'reason': 'Old test fixture output (regenerable)',
                    'severity': 'low'
                })
                continue
            
            # 3. OBSOLETE - Old TODOs and backups
            if '.bkp' in file:
                cleanup_items['OBSOLETE'].append({
                    'file': file,
                    'reason': 'Backup file (.bkp)',
                    'severity': 'medium'
                })
                continue
            
            if 'docs/TODO' in file and file.endswith('.md'):
                cleanup_items['OBSOLETE'].append({
                    'file': file,
                    'reason': 'Obsolete TODO documentation',
                    'severity': 'medium'
                })
                continue
            
            # 4. ARCHIVABLE - Files older than threshold
            try:
                if filepath.exists():
                    mtime = filepath.stat().st_mtime
                    if mtime < cutoff_time:
                        age_days = (time.time() - mtime) / 86400
                        if 'output/' in file and age_days > 30:
                            cleanup_items['ARCHIVABLE'].append({
                                'file': file,
                                'reason': f'Old output file ({int(age_days)} days old)',
                                'severity': 'low',
                                'age_days': int(age_days)
                            })
            except:
                pass
        
        return cleanup_items
    
    def generate_report(self):
        """Generate cleanup report"""
        self.collect_all_files()
        self.analyze_imports()
        self.analyze_references()
        
        cleanup_items = self.classify_cleanup_items()
        
        print("\n" + "=" * 70)
        print("📋 WORKSPACE CLEANUP ANALYSIS")
        print("=" * 70)
        
        print(f"\n📁 Total Files Analyzed: {len(self.all_files)}")
        
        # Summary by category
        total_cleanup = sum(len(v) for v in cleanup_items.values())
        print(f"\n🧹 Cleanup Items Found: {total_cleanup}")
        
        for category, items in cleanup_items.items():
            if items:
                icon = {'REDUNDANT': '🔄', 'REGENERABLE': '🔨', 'OBSOLETE': '⚠️', 'ARCHIVABLE': '📦'}[category]
                print(f"\n{icon} {category} ({len(items)}):")
                for item in items[:10]:  # Show first 10
                    severity_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[item.get('severity', 'low')]
                    age = f" | {item['age_days']} days old" if 'age_days' in item else ""
                    print(f"  {severity_icon} {item['file']}")
                    print(f"     └─ {item['reason']}{age}")
                if len(items) > 10:
                    print(f"  ... and {len(items) - 10} more")
        
        print("\n" + "=" * 70)
        
        # Return as structured data
        return {
            'total_files': len(self.all_files),
            'cleanup_items': cleanup_items,
            'total_cleanup_candidates': total_cleanup
        }


if __name__ == '__main__':
    analyzer = WorkspaceAnalyzer('.')
    report = analyzer.generate_report()
    
    # Save report
    with open('CLEANUP_ANALYSIS.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Report saved to CLEANUP_ANALYSIS.json")
