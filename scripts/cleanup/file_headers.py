"""
Module description

Purpose: manage standardized file headers with metadata persistence
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-24
Last Updated: 2026-01-24
"""
import re
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
from scripts.cleanup.models import FileCategory


def _get_file_creation_date(filepath: str) -> str:
    """Get file creation date from filesystem (or last modified if created not available)"""
    try:
        path = Path(filepath)
        stat = path.stat()
        # Try to get creation time (Windows) or use modification time (fallback)
        if hasattr(stat, 'st_birthtime'):
            timestamp = stat.st_birthtime
        else:
            timestamp = stat.st_mtime
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
    except Exception:
        return datetime.now().strftime('%Y-%m-%d')


def extract_header_metadata(filepath: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Extract Purpose, Expected Lifetime, Category, Created, and Last Updated from file header.
    
    Returns:
        Tuple of (purpose, lifetime, category_str, created, last_updated) or (None, None, None, None, None)
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        lines = content.split('\n')[:50]  # Check first 50 lines
        full_header = '\n'.join(lines)
        
        purpose = None
        lifetime = None
        category = None
        created = None
        last_updated = None
        
        # Extract Purpose (case-insensitive)
        match = re.search(r'purpose[:\s=]+([^\n]+)', full_header, re.IGNORECASE)
        if match:
            purpose = match.group(1).strip().strip('"\'')
        
        # Extract Expected Lifetime (case-insensitive)
        match = re.search(r'expected lifetime[:\s=]+(\w+)', full_header, re.IGNORECASE)
        if match:
            lifetime = match.group(1).strip().lower()
        
        # Extract Category (case-insensitive) - should be all uppercase
        match = re.search(r'category[:\s=]+([^\n]+)', full_header, re.IGNORECASE)
        if match:
            category = match.group(1).strip().upper()
        
        # Extract Created date (YYYY-MM-DD) - case-insensitive
        match = re.search(r'created[:\s=]+(\d{4}-\d{2}-\d{2})', full_header, re.IGNORECASE)
        if match:
            created = match.group(1).strip()
        
        # Extract Last Updated date (YYYY-MM-DD) - case-insensitive
        match = re.search(r'last\s+updated[:\s=]+(\d{4}-\d{2}-\d{2})', full_header, re.IGNORECASE)
        if match:
            last_updated = match.group(1).strip()
        
        return purpose, lifetime, category, created, last_updated
    
    except Exception:
        return None, None, None, None, None


def get_category_from_header(path: str) -> FileCategory:
    """
    Extract Category from file header.
    
    Returns:
        FileCategory enum value if found in header, else FileCategory.UNKNOWN
    """
    _, _, category_str, _, _ = extract_header_metadata(path)
    
    if not category_str:
        return FileCategory.UNKNOWN
    
    # Try to match against FileCategory enum
    try:
        return FileCategory[category_str.upper()]
    except KeyError:
        return FileCategory.UNKNOWN


def write_file_header(
    filepath: str,
    purpose: str,
    lifetime: str,
    category: FileCategory,
    created: Optional[str] = None,
    last_updated: Optional[str] = None
) -> bool:
    """
    Write or update standardized header in a file.
    
    Supports: .py, .ts, .js, .sh, .bat, .cmd files
    
    Args:
        filepath: Path to file
        purpose: Purpose description
        lifetime: permanent or temporary
        category: FileCategory enum value
        created: Creation date (YYYY-MM-DD) - auto-detected if not provided
        last_updated: Last update date (YYYY-MM-DD) - defaults to today
    
    Returns:
        True if header was written, False if file type not supported
    """
    path = Path(filepath)
    
    # Only process text files
    if path.suffix not in ['.py', '.ts', '.js', '.sh', '.bat', '.cmd']:
        return False
    
    # Auto-detect dates if not provided
    if not created:
        created = _get_file_creation_date(filepath)
    if not last_updated:
        last_updated = datetime.now().strftime('%Y-%m-%d')
    
    # Get current file content
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            current_content = f.read()
    except Exception:
        return False
    
    # Build new header
    category_name = category.value if hasattr(category, 'value') else str(category)
    
    new_header = f'''"""
Module description

Purpose: {purpose}
Expected Lifetime: {lifetime}
Category: {category_name}
Created: {created}
Last Updated: {last_updated}
"""
'''
    
    # Remove existing header if present
    content = current_content
    
    # Pattern to match existing docstring at start of file
    docstring_pattern = r'^(""".*?""")\n+'
    match = re.match(docstring_pattern, content, re.DOTALL)
    
    if match:
        # Replace existing header
        new_content = new_header + content[match.end():]
    else:
        # Check for single-quoted docstring
        docstring_pattern = r"^('''.*?''')\n+"
        match = re.match(docstring_pattern, content, re.DOTALL)
        
        if match:
            new_content = new_header + content[match.end():]
        else:
            # No existing header, prepend new one
            new_content = new_header + content
    
    # Write updated content
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    except Exception:
        return False


def update_all_file_headers(files_with_metadata: dict) -> int:
    """
    Batch update headers for multiple files.
    
    Args:
        files_with_metadata: Dict mapping filepath to (purpose, lifetime, category, created, last_updated)
    
    Returns:
        Number of files successfully updated
    """
    updated = 0
    for filepath, (purpose, lifetime, category, created, last_updated) in files_with_metadata.items():
        if write_file_header(filepath, purpose, lifetime, category, created, last_updated):
            updated += 1
    return updated
