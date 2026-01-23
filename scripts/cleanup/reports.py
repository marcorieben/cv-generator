"""
Report Generation

Generates JSON and Markdown reports from cleanup analysis results.
"""

import json
from datetime import datetime
from typing import List
from scripts.cleanup.models import FileAnalysis, CleanupReport, DecisionType


def generate_json_report(report: CleanupReport) -> str:
    """
    Generate machine-readable JSON report.
    
    Args:
        report: CleanupReport object
        
    Returns:
        JSON string (formatted with 2-space indent)
    """
    report_dict = report.to_dict()
    return json.dumps(report_dict, indent=2, ensure_ascii=False)


def generate_markdown_report(report: CleanupReport) -> str:
    """
    Generate human-readable Markdown report.
    
    Args:
        report: CleanupReport object
        
    Returns:
        Markdown string
    """
    lines = []
    
    # Header
    lines.append("# Cleanup Report")
    lines.append("")
    lines.append(f"**Run ID:** `{report.run_id}`")
    lines.append(f"**Mode:** {report.mode.upper()}")
    lines.append(f"**Timestamp:** {report.timestamp}")
    lines.append(f"**Total Files Analyzed:** {report.total_files}")
    lines.append("")
    
    # Summary
    summary = report.summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Decision | Count |")
    lines.append("|----------|-------|")
    lines.append(f"| DELETE_SAFE | {summary['delete_safe']} |")
    lines.append(f"| KEEP_REQUIRED | {summary['keep_required']} |")
    lines.append(f"| REVIEW_REQUIRED | {summary['review_required']} |")
    lines.append("")
    
    # DELETE_SAFE section
    delete_safe = [f for f in report.files if f.decision == DecisionType.DELETE_SAFE]
    if delete_safe:
        lines.append("## ✅ DELETE_SAFE Files")
        lines.append("")
        lines.append(f"**Count:** {len(delete_safe)}")
        lines.append("")
        lines.append("Files that are safe to delete (high confidence, low risk):")
        lines.append("")
        for f in delete_safe[:20]:  # Show first 20
            lines.append(f"- `{f.file_path}` ({f.size_kb:.1f} KB, {f.category.value})")
        if len(delete_safe) > 20:
            lines.append(f"- ... and {len(delete_safe) - 20} more")
        lines.append("")
    
    # REVIEW_REQUIRED section
    review_required = [f for f in report.files if f.decision == DecisionType.REVIEW_REQUIRED]
    if review_required:
        lines.append("## ⚠️  REVIEW_REQUIRED Files")
        lines.append("")
        lines.append(f"**Count:** {len(review_required)}")
        lines.append("")
        lines.append("Files that need human review before any action:")
        lines.append("")
        lines.append("| File | Category | Confidence | Risk |")
        lines.append("|------|----------|------------|------|")
        
        for f in review_required[:10]:  # Show first 10 in table
            risk_short = f.risk_assessment.split('.')[0][:60]
            confidence_pct = int(f.confidence * 100)
            lines.append(
                f"| `{f.file_path}` | {f.category.value} | "
                f"{confidence_pct}% | {risk_short}... |"
            )
        
        if len(review_required) > 10:
            lines.append(f"| ... | | | {len(review_required) - 10} more files |")
        
        lines.append("")
        
        # Detailed review section
        lines.append("### Detailed Review Items")
        lines.append("")
        for f in review_required[:5]:  # First 5 detailed
            lines.append(f"#### `{f.file_path}`")
            lines.append("")
            lines.append(f"- **Category:** {f.category.value}")
            lines.append(f"- **Size:** {f.size_kb:.1f} KB")
            lines.append(f"- **Confidence:** {int(f.confidence * 100)}%")
            lines.append(f"- **Risk:** {f.risk_assessment}")
            lines.append(f"- **Action:** {f.recommended_action}")
            lines.append("")
    
    # KEEP_REQUIRED section
    keep_required = [f for f in report.files if f.decision == DecisionType.KEEP_REQUIRED]
    if keep_required:
        lines.append(f"## 🔒 KEEP_REQUIRED Files")
        lines.append("")
        lines.append(f"**Count:** {len(keep_required)}")
        lines.append("")
        lines.append("These files must be kept (source code, config, protected paths).")
        lines.append("")
    
    # Mode-specific notes
    lines.append("## Notes")
    lines.append("")
    if report.mode == "analyze":
        lines.append("✅ **Analyze Mode:** No files were deleted or modified.")
        lines.append("")
        lines.append("To apply cleanup (DELETE_SAFE files will be deleted):")
        lines.append("```bash")
        lines.append("python -m scripts.cleanup apply")
        lines.append("```")
    else:  # apply mode
        lines.append("⚠️  **Apply Mode:** Files may have been deleted.")
        lines.append("")
        lines.append("Check the deleted_files.log in the run folder for details.")
    
    lines.append("")
    
    return "\n".join(lines)


def save_reports(
    report: CleanupReport,
    run_folder: str,
) -> None:
    """
    Save JSON and Markdown reports to disk.
    
    Args:
        report: CleanupReport object
        run_folder: Folder path to save reports to
    """
    import os
    
    # Ensure folder exists
    os.makedirs(run_folder, exist_ok=True)
    
    # Save JSON report
    json_path = os.path.join(run_folder, "cleanup_report.json")
    json_content = generate_json_report(report)
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(json_content)
    
    # Save Markdown report
    md_path = os.path.join(run_folder, "cleanup_report.md")
    md_content = generate_markdown_report(report)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"✅ Reports saved to: {run_folder}")
    print(f"   - cleanup_report.json")
    print(f"   - cleanup_report.md")
