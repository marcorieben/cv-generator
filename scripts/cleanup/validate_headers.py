"""
Module description

Purpose: statement in header/docstring
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-24
Last Updated: 2026-01-24
"""
import sys
import re
from pathlib import Path
from typing import List, Tuple


def extract_header(filepath: str) -> str:
    """Extract first 20 lines (potential header) from file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()[:30]
            return ''.join(lines)
    except (OSError, IOError):
        return ""


def has_purpose_statement(header: str) -> Tuple[bool, str]:
    """
    Check if header contains Purpose statement.
    
    Returns:
        Tuple of (has_purpose, purpose_text)
    """
    patterns = [
        r'""".*?Purpose[:\s]+([^"\n]+)',
        r"'''.*?Purpose[:\s]+([^'\n]+)",
        r'#\s*Purpose[:\s]+(.+)',
        r'Purpose:\s*(.+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, header, re.IGNORECASE | re.DOTALL)
        if match:
            return True, match.group(1).strip()
    
    return False, ""


def has_lifetime_statement(header: str) -> Tuple[bool, str]:
    """
    Check if header contains Expected Lifetime statement.
    
    Returns:
        Tuple of (has_lifetime, lifetime_value)
    """
    patterns = [
        r'Expected Lifetime[:\s]+(temporary|permanent)',
        r'Lifetime[:\s]+(temporary|permanent)',
        r'Expected Lifetime[:\s]+(temporary|permanent)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, header, re.IGNORECASE)
        if match:
            return True, match.group(1).strip()
    
    return False, ""


def validate_file_header(filepath: str, verbose: bool = False) -> Tuple[bool, List[str]]:
    """
    Validate a single file header.
    
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    # Skip non-Python files
    if not filepath.endswith('.py'):
        return True, []
    
    # Skip test files (they have different requirements)
    if 'test_' in filepath or '_test.py' in filepath:
        return True, []
    
    header = extract_header(filepath)
    issues = []
    
    # Check for purpose
    has_purpose, purpose_text = has_purpose_statement(header)
    if not has_purpose:
        issues.append(f"Missing Purpose statement in header (add '# Purpose: ...' in first 30 lines)")
    elif verbose:
        print(f"  ✓ Purpose: {purpose_text}")
    
    # Check for lifetime
    has_lifetime, lifetime_value = has_lifetime_statement(header)
    if not has_lifetime:
        issues.append(f"Missing Expected Lifetime in header (add 'Expected Lifetime: temporary' or 'permanent')")
    elif verbose:
        print(f"  ✓ Lifetime: {lifetime_value}")
    
    return len(issues) == 0, issues


def validate_files(filepaths: List[str], verbose: bool = False) -> Tuple[bool, dict]:
    """
    Validate multiple files.
    
    Returns:
        Tuple of (all_valid, results_dict)
    """
    results = {}
    all_valid = True
    
    for filepath in filepaths:
        is_valid, issues = validate_file_header(filepath, verbose=verbose)
        
        if not is_valid:
            all_valid = False
            results[filepath] = issues
            if verbose:
                print(f"  ❌ {Path(filepath).name}: {'; '.join(issues)}")
    
    return all_valid, results


def print_validation_report(results: dict, verbose: bool = True) -> None:
    """Print formatted validation report."""
    if not results:
        print("✅ All files have proper headers!")
        return
    
    print("\n" + "="*70)
    print("🏷️  FILE HEADER VALIDATION ISSUES")
    print("="*70)
    
    for filepath, issues in results.items():
        print(f"\n❌ {filepath}")
        for issue in issues:
            print(f"   • {issue}")
    
    print("\n" + "="*70)
    print(f"Found {len(results)} file(s) with header issues.")
    print("\nAdd to your file headers (within first 30 lines):")
    print("  # Purpose: Brief description of what this file does")
    print("  # Expected Lifetime: temporary (or permanent)")
    print("="*70 + "\n")


def validate_staged_files() -> int:
    """
    Validate staged Python files (for pre-commit hook).
    
    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        import subprocess
        
        # Get staged files from git
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            capture_output=True,
            text=True
        )
        
        staged_files = [f for f in result.stdout.strip().split('\n') if f.endswith('.py')]
        
        if not staged_files:
            return 0
        
        # Validate each file
        all_valid, results = validate_files(staged_files, verbose=True)
        
        if not all_valid:
            print_validation_report(results)
            return 1
        
        return 0
    
    except Exception as e:
        print(f"❌ Error validating files: {e}")
        return 1


# ===== For testing/manual validation =====
def main():
    """Manual validation of specific files."""
    if len(sys.argv) < 2:
        print("Usage: python validate_headers.py <file1.py> [file2.py] ...")
        print("\nExamples:")
        print("  python validate_headers.py scripts/cleanup/cleanup.py")
        print("  python validate_headers.py scripts/**/*.py")
        sys.exit(1)
    
    filepaths = sys.argv[1:]
    all_valid, results = validate_files(filepaths, verbose=True)
    
    if results:
        print_validation_report(results)
        sys.exit(1)
    else:
        print("✅ All validated files have proper headers!")
        sys.exit(0)


if __name__ == "__main__":
    main()
