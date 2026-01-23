"""
Cleanup Executor

Orchestrates the cleanup analysis and optional apply modes.
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


def scan_project_files(exclude_dirs: Optional[List[str]] = None) -> List[str]:
    """
    Scan entire project directory for files to analyze.
    
    Excludes:
    - .git
    - .venv
    - __pycache__
    - .pytest_cache
    - htmlcov
    - node_modules
    
    Args:
        exclude_dirs: Additional directories to exclude
        
    Returns:
        List of file paths (relative to project root)
    """
    default_excludes = {
        '.git', '.venv', '__pycache__', '.pytest_cache',
        'htmlcov', 'node_modules', '.eggs', '*.egg-info'
    }
    
    if exclude_dirs:
        default_excludes.update(exclude_dirs)
    
    files = []
    project_root = Path(__file__).parent.parent.parent  # cv_generator root
    
    for root, dirs, filenames in os.walk(str(project_root)):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in default_excludes and not d.endswith('.egg-info')]
        
        for filename in filenames:
            filepath = Path(root) / filename
            rel_path = filepath.relative_to(project_root)
            files.append(str(rel_path).replace('\\', '/'))
    
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
    
    # Create initial analysis
    analysis = FileAnalysis(
        file_path=path,
        category=category,
        last_modified=last_modified,
        size_kb=size_kb,
        decision=DecisionType.KEEP_REQUIRED,  # Default, will be overridden
        confidence=0.0,
        reasoning=[],
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
        print("=" * 60)
        print("🧹 CLEANUP SYSTEM")
        print("=" * 60)
        print(f"Mode: {mode.upper()}")
        print(f"Run ID: {run_id}")
        print("")
    
    # Scan all project files
    if verbose:
        print("📂 Scanning project files...")
    
    files = scan_project_files()
    
    if verbose:
        print(f"✅ Found {len(files)} files to analyze")
        print("")
    
    # Analyze each file
    if verbose:
        print("🔍 Analyzing files...")
    
    analyses = []
    for i, filepath in enumerate(files):
        if verbose and i % 50 == 0:
            print(f"   Progress: {i}/{len(files)}")
        
        try:
            analysis = analyze_file(filepath, config)
            analyses.append(analysis)
        except Exception as e:
            if verbose:
                print(f"   ⚠️  Error analyzing {filepath}: {e}")
            continue
    
    if verbose:
        print(f"✅ Analyzed {len(analyses)} files")
        print("")
    
    # Create report
    report = CleanupReport(
        run_id=run_id,
        mode=mode,
        timestamp=now.isoformat(),
        total_files=len(analyses),
        files=analyses,
    )
    
    # Print summary
    if verbose:
        summary = report.summary
        print("📊 SUMMARY")
        print("-" * 60)
        print(f"DELETE_SAFE:     {summary['delete_safe']:4d} files")
        print(f"KEEP_REQUIRED:   {summary['keep_required']:4d} files")
        print(f"REVIEW_REQUIRED: {summary['review_required']:4d} files")
        print("-" * 60)
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
            
            for analysis in delete_safe:
                try:
                    if os.path.exists(analysis.file_path):
                        size_kb = get_file_size_kb(analysis.file_path)
                        os.remove(analysis.file_path)
                        deleted_count += 1
                        deleted_log.append(f"{analysis.file_path} ({size_kb:.1f} KB)")
                        
                        if verbose:
                            print(f"   🗑️  {analysis.file_path}")
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
        print("=" * 60)
        print("")
    
    return report


def _get_run_folder(run_id: str) -> str:
    """Get the cleanup run folder path."""
    project_root = Path(__file__).parent.parent.parent
    run_folder = project_root / "cleanup" / "runs" / run_id
    return str(run_folder)
