#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple cleanup archiver - runs after interactive_cleanup.py identifies items
Standalone to avoid I/O cascade issues
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime


def archive_cleanup_items(items_file):
    """Archive items from JSON file"""
    try:
        with open(items_file, 'r', encoding='utf-8') as f:
            items = json.load(f)
        
        cleanup_dir = Path('cleanup')
        cleanup_dir.mkdir(exist_ok=True)
        
        for item in items:
            category = item['category']
            file_path = item['file']
            reason = item['reason']
            
            try:
                src = Path(file_path)
                if not src.exists():
                    continue
                
                # Create category dir
                cat_dir = cleanup_dir / category
                cat_dir.mkdir(exist_ok=True)
                
                # Preserve directory structure
                rel_path = src.relative_to('.')
                dst = cat_dir / rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                
                # Move file
                if src.is_file():
                    shutil.move(str(src), str(dst))
                
                sys.stderr.write(f"Archived: {file_path}\n")
                sys.stderr.flush()
            except Exception as e:
                sys.stderr.write(f"Failed: {file_path} ({e})\n")
                sys.stderr.flush()
        
        # Clean up temp file
        Path(items_file).unlink()
        
    except Exception as e:
        sys.stderr.write(f"Archive error: {e}\n")
        sys.stderr.flush()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        archive_cleanup_items(sys.argv[1])
    else:
        sys.exit(1)
