"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-23
Last Updated: 2026-01-24
"""
from scripts.cleanup.models import FileAnalysis, DecisionType, FileCategory, CleanupConfig


def apply_decision_rules(
    analysis: FileAnalysis, config: CleanupConfig
) -> FileAnalysis:
    """
    Apply decision rules to determine DELETE_SAFE, KEEP_REQUIRED, or REVIEW_REQUIRED.
    
    DELETE_SAFE conditions (all must be true):
    - Category in [TEMP_FILE, LOG_FILE, INTERMEDIATE_ARTIFACT]
    - File age >= threshold
    - Not in protected paths
    - Confidence >= 0.95
    
    KEEP_REQUIRED conditions:
    - Category in [SOURCE_CODE, CONFIG]
    - In required_artifacts list
    - Found references in source code
    
    REVIEW_REQUIRED: Fallback for uncertain decisions
    
    Args:
        analysis: FileAnalysis object with category
        config: CleanupConfig with rules
        
    Returns:
        FileAnalysis with decision, confidence, and reasoning populated
    """
    
    # Always check if in protected paths first
    for protected in config.protected_paths:
        # Normalize paths for comparison
        protected_norm = protected.replace('/', '\\').lower()
        path_norm = analysis.file_path.replace('/', '\\').lower()
        
        if protected_norm in path_norm or path_norm.startswith(protected_norm):
            analysis.decision = DecisionType.KEEP_REQUIRED
            analysis.confidence = 1.0
            analysis.reasoning.append(
                f"File in protected path: {protected}"
            )
            analysis.recommended_action = "Keep this file - it's in a protected directory"
            return analysis
    
    # Check if in required artifacts
    filename = analysis.file_path.split('\\')[-1].split('/')[-1]
    if filename in config.required_artifacts:
        analysis.decision = DecisionType.KEEP_REQUIRED
        analysis.confidence = 1.0
        analysis.reasoning.append(
            f"File is in required_artifacts list: {filename}"
        )
        analysis.recommended_action = "Keep this file - it's required for the application"
        return analysis
    
    # Always keep source code and config
    if analysis.category in [FileCategory.SOURCE_CODE, FileCategory.CONFIG]:
        analysis.decision = DecisionType.KEEP_REQUIRED
        analysis.confidence = 1.0
        analysis.reasoning.append(
            f"Category {analysis.category.value} is never deleted"
        )
        analysis.recommended_action = "Keep this file - source code and config are always required"
        return analysis
    
    # DELETE_SAFE: Only safe temp/log/intermediate files
    if analysis.category in [
        FileCategory.TEMP_FILE,
        FileCategory.LOG_FILE,
        FileCategory.INTERMEDIATE_ARTIFACT,
    ]:
        # Check age threshold
        from scripts.cleanup.classify import get_file_age_days
        
        age_days = get_file_age_days(analysis.file_path)
        
        if age_days >= config.age_threshold_days:
            analysis.decision = DecisionType.DELETE_SAFE
            analysis.confidence = 0.98
            analysis.reasoning.extend([
                f"Category: {analysis.category.value}",
                f"Age: {age_days:.1f} days (threshold: {config.age_threshold_days})",
                "Not in required artifacts or source code",
                "Safe to delete - low risk of application breakage"
            ])
            analysis.recommended_action = f"Safe to delete. File is {age_days:.1f} days old {analysis.category.value.lower()}"
            return analysis
        else:
            # Too young to delete
            analysis.decision = DecisionType.KEEP_REQUIRED
            analysis.confidence = 1.0
            analysis.reasoning.extend([
                f"Category: {analysis.category.value}",
                f"Age: {age_days:.1f} days (threshold: {config.age_threshold_days})",
                "File is too recent to delete"
            ])
            analysis.recommended_action = f"Keep for now - file is only {age_days:.1f} days old. Revisit in {max(1, int(config.age_threshold_days - age_days))} days"
            return analysis
    
    # For UNKNOWN category or anything else: REVIEW_REQUIRED
    if analysis.category == FileCategory.UNKNOWN:
        analysis.decision = DecisionType.REVIEW_REQUIRED
        analysis.confidence = 0.5
        analysis.reasoning.append(
            "Category is UNKNOWN - human review required to assess risk"
        )
        analysis.risk_assessment = (
            "Cannot determine file purpose or dependencies. "
            "Manual inspection needed to verify file is safe to delete."
        )
        analysis.recommended_action = (
            "Review file manually. Check if it's imported anywhere. "
            "If purpose unclear, archive rather than delete."
        )
        return analysis
    
    # Generated output: typically safe to regenerate but needs review
    if analysis.category == FileCategory.GENERATED_OUTPUT:
        analysis.decision = DecisionType.REVIEW_REQUIRED
        analysis.confidence = 0.75
        analysis.reasoning.extend([
            f"Category: {analysis.category.value}",
            "File is generated output - can potentially be regenerated",
            "But needs verification that generator still exists and works"
        ])
        analysis.risk_assessment = (
            "If the generator script has been modified or removed, "
            "this file may not be easily regenerated."
        )
        analysis.recommended_action = (
            "Verify the generator exists and works. "
            "If regenerator exists, can safely delete. "
            "Otherwise, archive the file."
        )
        return analysis
    
    # Experiment files: lower confidence, requires review
    if analysis.category == FileCategory.EXPERIMENT:
        analysis.decision = DecisionType.REVIEW_REQUIRED
        analysis.confidence = 0.70
        analysis.reasoning.extend([
            "Category: EXPERIMENT",
            "File contains experiment/test/demo code",
            "May be referenced in Git history or documentation"
        ])
        analysis.risk_assessment = (
            "If experiment is referenced in documentation or Git commits, "
            "deletion could break future reference/reproduction."
        )
        analysis.recommended_action = (
            "Search Git history and docs for references. "
            "If referenced, archive instead of delete. "
            "If truly unused, safe to delete."
        )
        return analysis
    
    # Fallback: anything else is REVIEW_REQUIRED
    analysis.decision = DecisionType.REVIEW_REQUIRED
    analysis.confidence = 0.60
    analysis.reasoning.extend([
        f"Category: {analysis.category.value}",
        "No clear deletion rules for this file type",
        "Manual review recommended"
    ])
    analysis.risk_assessment = (
        f"Uncertain how this {analysis.category.value} file is used. "
        "Manual inspection recommended before deletion."
    )
    analysis.recommended_action = (
        "Search codebase for file references. "
        "If no references found and file is not critical to application startup, "
        "can archive. If uncertain, keep the file."
    )
    return analysis
