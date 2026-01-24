"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-23
Last Updated: 2026-01-24
"""
import os
import re
from pathlib import Path
from scripts.cleanup.models import FileCategory


def get_category_from_header(path: str) -> FileCategory:
    """
    Try to extract Category from file header.
    
    Looks for: Category: SOURCE_CODE (or other FileCategory values)
    
    Args:
        path: File path
        
    Returns:
        FileCategory if found in header, else FileCategory.UNKNOWN
    """
    try:
        # Only check text files
        if not Path(path).suffix in ['.py', '.ts', '.js', '.sh', '.bat', '.cmd']:
            return FileCategory.UNKNOWN
        
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()[:30]
            header = ''.join(lines)
        
        # Look for Category: in header
        match = re.search(r'Category[:\s=]+([A-Z_]+)', header)
        if match:
            category_str = match.group(1).strip()
            # Try to match to FileCategory
            for cat in FileCategory:
                if cat.value == category_str:
                    return cat
    
    except Exception:
        pass
    
    return FileCategory.UNKNOWN


def classify_file(path: str) -> FileCategory:
    """
    Classify a file into one of 10 categories.
    
    Priority:
    1. Check file header for pre-classified metadata
    2. Apply pattern-based rules
    
    Rules applied in order:
    1. SOURCE_CODE: .py, .ts, .js, .md (not in docs/)
    2. CONFIG: .yaml, .json, .toml, .ini, .conf, .cfg files
    3. PROMPT: in /prompts/ or _prompt.txt files
    4. INPUT_DATA: files in /input/ or document formats
    5. INTERMEDIATE_ARTIFACT: in /data/intermediate/ or /tmp/
    6. GENERATED_OUTPUT: in /output/ directory
    7. LOG_FILE: .log files or in /logs/
    8. TEMP_FILE: .tmp, .bak, .cache, .pyc, etc.
    9. EXPERIMENT: experimental/test/demo markers
    10. Default: UNKNOWN
    
    Args:
        path: File path (relative or absolute)
        
    Returns:
        FileCategory: Assigned category
    """
    # First check header for pre-classified metadata
    header_category = get_category_from_header(path)
    if header_category != FileCategory.UNKNOWN:
        return header_category
    
    # Fall back to pattern-based classification
    path_lower = path.lower()
    path_obj = Path(path)
    filename_lower = path_obj.name.lower()
    
    # Special case: .coverage is temp
    if filename_lower == ".coverage" or ".coverage" in filename_lower:
        return FileCategory.TEMP_FILE
    
    # Special case: .env files are config
    if filename_lower.startswith(".env"):
        return FileCategory.CONFIG
    
    # Special case: .gitignore is config
    if filename_lower == ".gitignore":
        return FileCategory.CONFIG
    
    # Special case: *.bat and *.cmd in root or cleanup/ are runners/scripts
    if path_obj.suffix in ['.bat', '.cmd']:
        # Batch files - treat as utility/runner scripts (PROMPT category)
        return FileCategory.PROMPT
    
    # Special case: requirements*.txt is config
    if filename_lower.startswith('requirements') and path_obj.suffix == '.txt':
        return FileCategory.CONFIG
    
    # SOURCE_CODE: Python, TypeScript, JavaScript, Markdown (except docs/)
    if path_obj.suffix in ['.py', '.ts', '.js'] or path_obj.suffix == '.md':
        if 'docs/' not in path_lower and 'docs\\' not in path_lower:
            return FileCategory.SOURCE_CODE
    
    # CONFIG: YAML, JSON, TOML, INI, and other config formats
    config_extensions = ['.yaml', '.yml', '.json', '.toml', '.ini', '.conf', '.cfg']
    if path_obj.suffix in config_extensions:
        return FileCategory.CONFIG
    
    # CONFIG: Common config files by name
    config_files = ['config', 'settings', 'pytest.ini', 'setup.cfg', 'pyproject.toml', 
                    'devcontainer.json', 'tasks.json', 'launch.json', '.gitignore',
                    '.dockerignore', '.editorconfig', 'tox.ini', '.gitkeep', '.keep']
    if any(cf in filename_lower for cf in config_files):
        return FileCategory.CONFIG
    
    # CONFIG: Dotfiles in config/settings directories
    if filename_lower.startswith('.') and any(x in path_lower for x in ['.streamlit', '.vscode', '.devcontainer']):
        return FileCategory.CONFIG
    
    # PROMPT: Files in /prompts/ or named *_prompt.*
    if '/prompts/' in path_lower or '\\prompts\\' in path_lower:
        return FileCategory.PROMPT
    if '_prompt' in path_lower:
        return FileCategory.PROMPT
    
    # INPUT_DATA: Files in /input/ or /data/input/ or any data formats
    if '/input/' in path_lower or '\\input\\' in path_lower:
        return FileCategory.INPUT_DATA
    if '/data/input/' in path_lower or '\\data\\input\\' in path_lower:
        return FileCategory.INPUT_DATA
    
    # INPUT_DATA: Document and archive formats
    doc_extensions = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.zip', '.rar', '.7z']
    if path_obj.suffix.lower() in doc_extensions:
        return FileCategory.INPUT_DATA
    
    # INTERMEDIATE_ARTIFACT: /data/intermediate/ or /tmp/
    if '/data/intermediate/' in path_lower or '\\data\\intermediate\\' in path_lower:
        return FileCategory.INTERMEDIATE_ARTIFACT
    if '/tmp/' in path_lower or '\\tmp\\' in path_lower:
        return FileCategory.INTERMEDIATE_ARTIFACT
    
    # GENERATED_OUTPUT: /output/ directory
    if '/output/' in path_lower or '\\output\\' in path_lower:
        return FileCategory.GENERATED_OUTPUT
    
    # LOG_FILE: .log files or /logs/ directory
    if path_obj.suffix == '.log':
        return FileCategory.LOG_FILE
    if '/logs/' in path_lower or '\\logs\\' in path_lower:
        return FileCategory.LOG_FILE
    
    # TEMP_FILE: Temporary file extensions
    temp_extensions = ['.tmp', '.bak', '.backup', '.cache', '.pyc', '.pyo', '.swp', '.coverage']
    if path_obj.suffix in temp_extensions:
        return FileCategory.TEMP_FILE
    
    # TEMP_FILE: Backup and temporary file markers
    backup_markers = ['.bak', '.backup', '.old', '.orig', '~', '.tmp', '.temp']
    if any(path_lower.endswith(marker) for marker in backup_markers):
        return FileCategory.TEMP_FILE
    
    # EXPERIMENT: Files with experiment/test/demo markers in name
    experiment_markers = ['_experiment_', '_test_', '_demo_', '_scratch_', '_backup_', 
                         '_old_', 'test_', '_archive']
    if any(marker in path_lower for marker in experiment_markers):
        return FileCategory.EXPERIMENT
    
    # DOCUMENTATION: .md and .txt files (except code samples)
    if path_obj.suffix in ['.md', '.txt']:
        # But not if it's source code markdown
        if 'docs/' in path_lower or '\\docs\\' in path_lower:
            return FileCategory.SOURCE_CODE  # Documentation files
        if path_obj.suffix == '.txt':
            # Check if it's config-like or data-like
            if any(x in filename_lower for x in ['changelog', 'readme', 'license', 'todo', 'notes']):
                return FileCategory.SOURCE_CODE
            if any(x in path_lower for x in ['log', 'output', 'input', 'test']):
                if 'test_output' in filename_lower:
                    return FileCategory.EXPERIMENT  # Test output files
            return FileCategory.SOURCE_CODE  # Default .txt to SOURCE_CODE
    
    # Special case: .html files in /htmlcov/ are generated test coverage
    if '/htmlcov/' in path_lower or '\\htmlcov\\' in path_lower:
        return FileCategory.GENERATED_OUTPUT
    
    # Special case: __pycache__ is generated
    if '__pycache__' in path_lower or '.pytest_cache' in path_lower:
        return FileCategory.GENERATED_OUTPUT
    
    # Special case: .git directory contents
    if '/.git/' in path_lower or '\\.git\\' in path_lower:
        return FileCategory.CONFIG
    
    # Special case: .venv is generated/config
    if '/.venv/' in path_lower or '\\.venv\\' in path_lower:
        return FileCategory.CONFIG
    
    # Default to UNKNOWN
    return FileCategory.UNKNOWN


def get_file_age_days(path: str) -> float:
    """
    Get file age in days since last modification.
    
    Args:
        path: File path
        
    Returns:
        Age in days (float), or 999 if file doesn't exist
    """
    try:
        if not os.path.exists(path):
            return 999.0
        
        mtime = os.path.getmtime(path)
        from datetime import datetime
        
        mtime_dt = datetime.fromtimestamp(mtime)
        now = datetime.now()
        age = (now - mtime_dt).total_seconds() / (24 * 3600)
        
        return age
    except Exception:
        return 999.0


def get_file_size_kb(path: str) -> float:
    """
    Get file size in kilobytes.
    
    Args:
        path: File path
        
    Returns:
        Size in KB (float), or 0 if file doesn't exist
    """
    try:
        if not os.path.exists(path):
            return 0.0
        
        size_bytes = os.path.getsize(path)
        size_kb = size_bytes / 1024.0
        
        return size_kb
    except Exception:
        return 0.0
