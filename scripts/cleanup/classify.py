"""
Classification Engine

Assigns each file to one of 10 categories based on path and filename patterns.
"""

import os
from pathlib import Path
from scripts.cleanup.models import FileCategory


def classify_file(path: str) -> FileCategory:
    """
    Classify a file into one of 10 categories.
    
    Rules applied in order:
    1. SOURCE_CODE: .py, .ts, .js, .md (not in docs/)
    2. CONFIG: .yaml, .json in root/config areas
    3. PROMPT: in /prompts/ or _prompt.txt files
    4. INPUT_DATA: in /input/ or /data/input/
    5. INTERMEDIATE_ARTIFACT: in /data/intermediate/ or /tmp/
    6. GENERATED_OUTPUT: in /output/ with matching template
    7. LOG_FILE: .log or in /logs/
    8. TEMP_FILE: .tmp, .bak, .cache, .pyc
    9. EXPERIMENT: _experiment_, _test_, _demo_ in name
    10. Default: UNKNOWN
    
    Args:
        path: File path (relative or absolute)
        
    Returns:
        FileCategory: Assigned category
    """
    path_lower = path.lower()
    path_obj = Path(path)
    
    # SOURCE_CODE: Python, TypeScript, JavaScript, Markdown (except docs/)
    if path_obj.suffix in ['.py', '.ts', '.js'] or path_obj.suffix == '.md':
        if 'docs/' not in path_lower and 'docs\\' not in path_lower:
            return FileCategory.SOURCE_CODE
    
    # CONFIG: YAML and JSON in root or config directories
    if path_obj.suffix in ['.yaml', '.yml', '.json']:
        if any(p in path_lower for p in ['config', 'settings', '.env']):
            return FileCategory.CONFIG
        # Root-level config files
        if path_obj.parent.name == '':  # Root directory
            return FileCategory.CONFIG
    
    # PROMPT: Files in /prompts/ or named *_prompt.*
    if '/prompts/' in path_lower or '\\prompts\\' in path_lower:
        return FileCategory.PROMPT
    if '_prompt' in path_lower:
        return FileCategory.PROMPT
    
    # INPUT_DATA: Files in /input/ or /data/input/
    if '/input/' in path_lower or '\\input\\' in path_lower:
        return FileCategory.INPUT_DATA
    if '/data/input/' in path_lower or '\\data\\input\\' in path_lower:
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
    temp_extensions = ['.tmp', '.bak', '.cache', '.pyc', '.pyo', '.swp']
    if path_obj.suffix in temp_extensions:
        return FileCategory.TEMP_FILE
    
    # EXPERIMENT: Files with experiment/test/demo markers in name
    experiment_markers = ['_experiment_', '_test_', '_demo_', '_scratch_']
    if any(marker in path_lower for marker in experiment_markers):
        return FileCategory.EXPERIMENT
    
    # Special case: .html files in /htmlcov/ are generated test coverage
    if '/htmlcov/' in path_lower or '\\htmlcov\\' in path_lower:
        return FileCategory.GENERATED_OUTPUT
    
    # Special case: __pycache__ is generated
    if '__pycache__' in path_lower or '.pytest_cache' in path_lower:
        return FileCategory.GENERATED_OUTPUT
    
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
