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
from typing import List, Set, Tuple
from scripts.cleanup.models import ReferenceInfo


def extract_context(content: str, line_number: int, context_lines: int = 2) -> str:
    """
    Extract context around a line in code.
    
    Args:
        content: File content
        line_number: Line number (1-indexed)
        context_lines: Number of lines before/after to include
        
    Returns:
        Context string
    """
    lines = content.split('\n')
    start = max(0, line_number - 1 - context_lines)
    end = min(len(lines), line_number + context_lines)
    
    context_list = []
    for i in range(start, end):
        if i < len(lines):
            prefix = ">>> " if i == line_number - 1 else "    "
            context_list.append(f"{i+1:4d}: {prefix}{lines[i][:100]}")
    
    return "\n".join(context_list)


def classify_reference(content: str, line: str, filename: str) -> Tuple[str, bool]:
    """
    Classify reference type and whether it's indirect.
    
    Args:
        content: Full file content
        line: The line containing the reference
        filename: Name of file being referenced
        
    Returns:
        Tuple of (reference_type, is_indirect)
    """
    line_lower = line.lower()
    
    # Direct references
    if 'import' in line_lower:
        return ("import", False)
    if any(x in line_lower for x in ['from', 'require', 'include']):
        return ("include", False)
    if 'open(' in line_lower or 'read' in line_lower:
        return ("file_operation", False)
    if 'glob' in line_lower or 'walk' in line_lower:
        return ("glob_pattern", True)  # Often dynamic
    if f'"{filename}"' in line or f"'{filename}'" in line:
        return ("string_literal", False)
    
    # Indirect references
    if any(x in line_lower for x in ['eval', '__import__', 'getattr', 'dynamic', 'variable']):
        return ("dynamic", True)
    if 'f-string' in line_lower or 'format(' in line_lower:
        return ("dynamic_format", True)
    
    return ("reference", False)


def find_references_for_file(filepath: str, project_root: str = None) -> List[ReferenceInfo]:
    """
    Search for references to a file in source code with detailed context.
    
    Args:
        filepath: File path to search for
        project_root: Project root directory
        
    Returns:
        List of ReferenceInfo objects with location and context
    """
    if project_root is None:
        project_root = Path(__file__).parent.parent.parent
    else:
        project_root = Path(project_root)
    
    filename = Path(filepath).name
    filename_without_ext = Path(filepath).stem
    
    references = []
    
    # Search in source files only
    search_patterns = ['**/*.py', '**/*.json', '**/*.yaml', '**/*.yml', '**/*.md', '**/*.bat', '**/*.cmd']
    
    for pattern in search_patterns:
        try:
            for source_file in project_root.glob(pattern):
                # Skip the file itself and cleanup directories
                if 'cleanup/runs' in str(source_file).lower() or source_file == Path(filepath):
                    continue
                
                try:
                    with open(source_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.split('\n')
                        
                        for line_idx, line in enumerate(lines):
                            found = False
                            
                            # Check for exact filename
                            if filename in line:
                                found = True
                            # Also check for stem (without extension) if long enough
                            elif filename_without_ext in line and len(filename_without_ext) > 3:
                                found = True
                            
                            if found:
                                ref_type, is_indirect = classify_reference(content, line, filename)
                                context = extract_context(content, line_idx + 1)
                                
                                ref = ReferenceInfo(
                                    file_path=str(source_file.relative_to(project_root)),
                                    line_number=line_idx + 1,
                                    context=context,
                                    is_indirect=is_indirect,
                                    reference_type=ref_type
                                )
                                references.append(ref)
                except Exception:
                    pass
        except Exception:
            pass
    
    return references


def get_all_references(filepaths: List[str], project_root: str = None) -> dict:
    """
    Get references for multiple files.
    
    Args:
        filepaths: List of file paths
        project_root: Project root directory
        
    Returns:
        Dict mapping filepath to list of ReferenceInfo objects
    """
    if project_root is None:
        project_root = Path(__file__).parent.parent.parent
    
    result = {}
    for filepath in filepaths:
        refs = find_references_for_file(filepath, str(project_root))
        if refs:
            result[filepath] = refs
    
    return result
