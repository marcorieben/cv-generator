"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-23
Last Updated: 2026-01-24
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from scripts.cleanup.models import (
    FileAnalysis,
    FileCategory,
    DecisionType,
    CleanupConfig,
    CleanupReport,
)
from scripts.cleanup.classify import (
    classify_file,
    get_file_age_days,
    get_file_size_kb,
)
from scripts.cleanup.decisions import apply_decision_rules
from scripts.cleanup.reports import save_reports
from scripts.cleanup.dependencies import find_references_for_file
from scripts.cleanup.file_headers import extract_header_metadata, write_file_header


def scan_project_files(exclude_dirs: Optional[List[str]] = None) -> List[str]:
    """
    Scan project directories that are meaningful for cleanup.
    
    Includes:
    - scripts/        (all Python modules)
    - core/           (core functionality)
    - tests/          (test files)
    - docs/           (documentation)
    - Root level files: *.py, *.json, *.yaml, *.bat, *.cmd, *.md, *.txt
    
    Excludes:
    - input/          (user input data)
    - output/         (generated files)
    - .git, .venv, __pycache__, .pytest_cache, htmlcov
    - node_modules, .eggs
    - .github/workflows (CI/CD - auto-generated)
    - cleanup/runs/ (cleanup history)
    
    Args:
        exclude_dirs: Additional directories to exclude
        
    Returns:
        List of file paths (relative to project root)
    """
    default_excludes = {
        '.git', '.venv', '__pycache__', '.pytest_cache',
        'htmlcov', 'node_modules', '.eggs', '*.egg-info',
        '.github/workflows',  # CI/CD automation
        'cleanup/runs',  # Cleanup history
        'output',  # Generated output
        'input',  # User input data
    }
    
    if exclude_dirs:
        default_excludes.update(exclude_dirs)
    
    # Directories to include in cleanup scan
    whitelist_dirs = {
        'scripts',
        'core',
        'tests',
        'docs',
        '.github',
        '.streamlit',
        '.devcontainer',
        '.vscode',
    }
    
    # Root level file extensions to include
    root_extensions = {'.py', '.json', '.yaml', '.yml', '.bat', '.cmd', '.md', '.txt', '.ini'}
    
    files = []
    project_root = Path(__file__).parent.parent.parent  # cv_generator root
    
    for root, dirs, filenames in os.walk(str(project_root)):
        # Get relative directory path
        rel_dir = Path(root).relative_to(project_root)
        rel_dir_str = str(rel_dir).lower()
        
        # Check if directory is excluded
        if any(exc in rel_dir_str for exc in default_excludes):
            dirs[:] = []  # Don't descend
            continue
        
        # Check if directory is whitelisted (or is root)
        is_root = str(rel_dir) == '.'
        is_whitelisted = (
            is_root or  # Root directory - with selective extensions
            any(
                rel_dir_str.startswith(wl.lower()) or
                rel_dir_str == wl.lower()
                for wl in whitelist_dirs
            )
        )
        
        if is_whitelisted:
            for filename in filenames:
                filepath = Path(root) / filename
                rel_path = filepath.relative_to(project_root)
                
                # For root directory, only include specific file extensions
                if is_root:
                    if Path(filename).suffix.lower() not in root_extensions:
                        continue
                
                files.append(str(rel_path).replace('\\', '/'))
        else:
            # Don't descend into non-whitelisted directories
            dirs[:] = []
    
    return files


def analyze_file(path: str, config: CleanupConfig) -> FileAnalysis:
    """
    Analyze a single file and return FileAnalysis.
    
    Args:
        path: File path
        config: CleanupConfig
        
    Returns:
        FileAnalysis with decision and reasoning
    """
    category = classify_file(path)
    last_modified = datetime.fromtimestamp(
        os.path.getmtime(path) if os.path.exists(path) else 0
    ).isoformat() if os.path.exists(path) else "unknown"
    
    size_kb = get_file_size_kb(path)
    
    # Extract purpose, lifetime, dates from file header
    try:
        purpose, lifetime, category_from_header, created, last_updated = extract_header_metadata(path)
        if not purpose:
            purpose = ""
        if not lifetime:
            lifetime = ""
        if not created:
            created = ""
        if not last_updated:
            last_updated = ""
    except:
        purpose, lifetime, created, last_updated = "", "", "", ""
    
    # Create initial analysis
    analysis = FileAnalysis(
        file_path=path,
        category=category,
        last_modified=last_modified,
        size_kb=size_kb,
        decision=DecisionType.KEEP_REQUIRED,  # Default, will be overridden
        confidence=0.0,
        reasoning=[],
        file_purpose=purpose,
        expected_lifetime=lifetime,
        created_date=created,
        last_updated_date=last_updated,
    )
    
    # Apply decision rules
    analysis = apply_decision_rules(analysis, config)
    
    return analysis


def run_cleanup(
    mode: str = "analyze",
    config: Optional[CleanupConfig] = None,
    verbose: bool = True,
) -> CleanupReport:
    """
    Main cleanup function - analyze and optionally apply cleanup.
    
    Args:
        mode: "analyze" (no changes) or "apply" (may delete files)
        config: CleanupConfig (uses defaults if None)
        verbose: Print progress messages
        
    Returns:
        CleanupReport with analysis and summary
        
    Raises:
        ValueError: If mode is invalid
    """
    if mode not in ["analyze", "apply"]:
        raise ValueError(f"Invalid mode: {mode}. Must be 'analyze' or 'apply'")
    
    if config is None:
        config = CleanupConfig()
    
    # Generate run ID (timestamp)
    now = datetime.now()
    run_id = now.strftime("%Y-%m-%d_%H-%M-%S")
    
    if verbose:
        print("")
        print("=" * 70)
        print("🧹 CLEANUP SYSTEM - Enhanced Analysis")
        print("=" * 70)
        print(f"Mode: {mode.upper()}")
        print(f"Run ID: {run_id}")
        print("")
    
    # Scan meaningful project directories
    if verbose:
        print("📂 Scanning meaningful project directories...")
        print("   Including: scripts/, core/, tests/, docs/")
        print("   Root level: *.py, *.json, *.yaml, *.bat, *.cmd, *.md, *.txt")
        print("   Excluding: .git, .venv, __pycache__, .pytest_cache, htmlcov, cleanup/runs, input/, output/")
    
    files = scan_project_files()
    
    if verbose:
        print(f"✅ Found {len(files)} files to analyze")
        print("")
    
    # Analyze each file with detailed progress
    if verbose:
        print("🔍 Analyzing files...")
        print("")
    
    analyses = []
    project_root = Path(__file__).parent.parent.parent
    
    # Category stats for progress display
    category_stats = {cat: 0 for cat in FileCategory}
    decision_stats = {dec: 0 for dec in DecisionType}
    unclassified = []
    
    for i, filepath in enumerate(files):
        # Detailed progress every 20 files or at specific intervals
        if verbose and (i % 20 == 0 or i == len(files) - 1):
            percent = int((i / len(files)) * 100)
            status_bar = "▓" * (percent // 5) + "░" * (20 - percent // 5)
            print(f"   [{status_bar}] {percent:3d}% ({i+1:3d}/{len(files)}) ", end="")
            
            if len(unclassified) > 0:
                print(f"⚠️  {len(unclassified)} unclassified", end="")
            
            print()
        
        try:
            analysis = analyze_file(filepath, config)
            
            # Track category and decision
            category_stats[analysis.category] += 1
            decision_stats[analysis.decision] += 1
            
            # Track unclassified files
            if analysis.category == FileCategory.UNKNOWN:
                unclassified.append(filepath)
            
            # Check for references in source code (with detailed context)
            if analysis.decision == DecisionType.REVIEW_REQUIRED:
                refs = find_references_for_file(filepath, str(project_root))
                if refs:
                    direct_refs = [r for r in refs if not r.is_indirect]
                    indirect_refs = [r for r in refs if r.is_indirect]
                    
                    analysis.references = refs
                    analysis.reasoning.append(
                        f"Found {len(direct_refs)} direct + {len(indirect_refs)} indirect references"
                    )
                    
                    # Build recommended action with file references
                    ref_files = list(set([r.file_path for r in refs]))
                    if ref_files:
                        analysis.recommended_action = f"References found in: {', '.join(ref_files[:3])}" + (
                            f" and {len(ref_files)-3} more" if len(ref_files) > 3 else ""
                        )
            
            analyses.append(analysis)
        except Exception as e:
            if verbose and i % 20 == 0:
                print(f"   ⚠️  Error analyzing {filepath}: {e}")
            continue
    
    if verbose:
        print("")
        print(f"✅ Analyzed {len(analyses)} files")
        print("")
    
    # Show unclassified files (UNKNOWN after classification)
    unclassified = [f for f in analyses if f.category == FileCategory.UNKNOWN]
    if unclassified and verbose:
        print("⚠️  UNCLASSIFIED FILES (FileCategory.UNKNOWN)")
        print(f"   {len(unclassified)} files could not be automatically classified:")
        for unc in unclassified[:10]:
            print(f"      • {unc.file_path} ({Path(unc.file_path).suffix})")


        if len(unclassified) > 10:
            print(f"      • ... and {len(unclassified) - 10} more")
        print("")
    
    # Create report
    report = CleanupReport(
        run_id=run_id,
        mode=mode,
        timestamp=now.isoformat(),
        total_files=len(analyses),
        files=analyses,
    )
    
    # Print detailed summary with category breakdown
    if verbose:
        summary = report.summary
        print("📊 SUMMARY")
        print("=" * 70)
        print(f"DELETE_SAFE:     {summary['delete_safe']:4d} files 🗑️ ")
        print(f"KEEP_REQUIRED:   {summary['keep_required']:4d} files 🔒")
        print(f"REVIEW_REQUIRED: {summary['review_required']:4d} files ⚠️ ")
        print("=" * 70)
        
        # Category breakdown
        print("")
        print("📂 CATEGORY BREAKDOWN")
        print("-" * 70)
        for cat in sorted(FileCategory, key=lambda x: category_stats[x], reverse=True):
            count = category_stats[cat]
            if count > 0:
                percent = int((count / len(analyses)) * 100)
                print(f"  {cat.value:25s} {count:4d} ({percent:3d}%)")
        
        print("")
    
    # Save reports
    run_folder = _get_run_folder(run_id)
    save_reports(report, run_folder)
    
    if verbose:
        print(f"📁 Run folder: {run_folder}")
        print("")
    
    # Apply cleanup if requested
    if mode == "apply":
        if verbose:
            print("⚠️  APPLY MODE - Files will be deleted")
            print("")
        
        # Get confirmation
        delete_safe = [f for f in analyses if f.decision == DecisionType.DELETE_SAFE]
        if delete_safe:
            total_size_mb = sum(f.size_kb for f in delete_safe) / 1024.0
            
            if verbose:
                print(f"Ready to delete {len(delete_safe)} files ({total_size_mb:.1f} MB)")
                response = input("Continue? (yes/no): ").strip().lower()
                
                if response != "yes":
                    print("❌ Cleanup cancelled")
                    return report
            
            # Delete files
            deleted_count = 0
            deleted_log = []
            
            for idx, analysis in enumerate(delete_safe):
                if verbose:
                    percent = int(((idx + 1) / len(delete_safe)) * 100)
                    print(f"   [{percent:3d}%] 🗑️  {analysis.file_path}")
                
                try:
                    if os.path.exists(analysis.file_path):
                        size_kb = get_file_size_kb(analysis.file_path)
                        os.remove(analysis.file_path)
                        deleted_count += 1
                        deleted_log.append(f"{analysis.file_path} ({size_kb:.1f} KB)")
                except Exception as e:
                    if verbose:
                        print(f"   ⚠️  Failed to delete {analysis.file_path}: {e}")
            
            # Save deleted files log
            deleted_log_path = os.path.join(run_folder, "deleted_files.log")
            with open(deleted_log_path, 'w', encoding='utf-8') as f:
                f.write(f"# Cleanup Run: {run_id}\n")
                f.write(f"# Deleted {deleted_count} files\n")
                f.write("#\n")
                for entry in deleted_log:
                    f.write(f"{entry}\n")
            
            if verbose:
                print("")
                print(f"✅ Deleted {deleted_count} files")
                print("")
    
    if verbose:
        print("=" * 70)
        print("")
        print("💾 WRITING FILE HEADERS")
        print("   Adding Purpose, Lifetime, Created, Last Updated, and Category metadata...")
        print("")
    
    # Write headers to files with valid metadata
    headers_written = 0
    for analysis in analyses:
        # Only update text files with proper metadata
        if (analysis.file_purpose or analysis.expected_lifetime) and \
           Path(analysis.file_path).suffix in ['.py', '.ts', '.js', '.sh']:
            
            purpose = analysis.file_purpose or "TODO: Add purpose"
            lifetime = analysis.expected_lifetime or "permanent"
            created = analysis.created_date or ""
            last_updated = analysis.last_updated_date or ""
            
            if write_file_header(analysis.file_path, purpose, lifetime, analysis.category, created, last_updated):
                headers_written += 1
    
    if verbose and headers_written > 0:
        print(f"✅ Updated {headers_written} file headers with metadata")
        print("")
    
    if verbose:
        print("=" * 70)
        print("")
    
    return report


def _get_run_folder(run_id: str) -> str:
    """Get the cleanup run folder path."""
    project_root = Path(__file__).parent.parent.parent
    run_folder = project_root / "scripts" / "cleanup" / "runs" / run_id
    return str(run_folder)
