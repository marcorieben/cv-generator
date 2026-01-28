"""
Naming conventions and filename generation utilities.

Purpose: Central naming logic for all output files and folders
Expected Lifetime: Permanent (Core Module)
Category: CORE
Created: 2026-01-28
Last Updated: 2026-01-28

This module implements the naming conventions documented in docs/NAMING_CONVENTIONS.md
All output files follow consistent patterns based on 4 core variables:
- jobprofile_slug: Job profile identification (gdjob_{id}_{name})
- candidate_name: Candidate name (Vorname_Nachname)
- timestamp: Timestamp (YYYYMMdd_HHMMSS)
- filetype: Document type (cv, offer, dashboard, etc.)

Usage:
    from core.utils.naming import generate_filename, FileType
    
    filename = generate_filename(
        jobprofile_slug="gdjob_12881_senior_business_analyst",
        candidate_name="Marco_Rieben",
        filetype=FileType.CV,
        timestamp="20260119_170806",
        extension="docx"
    )
    # Returns: "gdjob_12881_senior_business_analyst_Marco_Rieben_cv_20260119_170806.docx"
"""

import re
from typing import Optional


class FileType:
    """Defined document types for output files."""
    CV = "cv"
    OFFER = "offer"
    DASHBOARD = "dashboard"
    MATCH = "match"
    FEEDBACK = "feedback"
    JOBPROFILE = "jobprofile"
    
    @classmethod
    def all_types(cls) -> list[str]:
        """Return all defined file types."""
        return [cls.CV, cls.OFFER, cls.DASHBOARD, cls.MATCH, cls.FEEDBACK, cls.JOBPROFILE]


def slugify(text: str, max_length: int = 50) -> str:
    """
    Normalize text for use in filenames.
    
    Removes special characters, converts spaces to underscores, truncates to max length.
    
    Args:
        text: Text to normalize
        max_length: Maximum length of output (default: 50)
        
    Returns:
        Normalized slug string (lowercase, alphanumeric + underscores only)
        
    Examples:
        >>> slugify("Senior Java Developer")
        'senior_java_developer'
        
        >>> slugify("C++ & Python Expert!!!")
        'c_python_expert'
        
        >>> slugify("Müller-Schmidt Ä Ö Ü")
        'muller_schmidt_a_o_u'
    """
    # Convert to lowercase
    text = text.lower()
    
    # Replace German umlauts
    text = text.replace('ä', 'a').replace('ö', 'o').replace('ü', 'u')
    text = text.replace('ß', 'ss')
    
    # Remove special characters (keep alphanumeric, spaces, hyphens, underscores)
    text = re.sub(r'[^a-z0-9\s\-_]', '', text)
    
    # Convert spaces and hyphens to underscores
    text = re.sub(r'[\s\-]+', '_', text.strip())
    
    # Normalize multiple underscores to single underscore
    text = re.sub(r'_+', '_', text)
    
    # Truncate to max length
    text = text[:max_length].strip('_')
    
    return text


def generate_jobprofile_slug(job_profile_id: int, job_profile_name: str, max_length: int = 50) -> str:
    """
    Generate Job Profile Slug for filenames.
    
    Format: gdjob_{id}_{truncated_slugified_name}
    
    Args:
        job_profile_id: Database ID or document ID of the job profile (can be 0 if unknown)
        job_profile_name: Title of the job profile (e.g., "Senior Business Analyst - BizDevOps Engineer")
        max_length: Maximum length of the name part (default: 50)
    
    Returns:
        Job Profile Slug (e.g., "gdjob_12881_senior_business_analyst_bizdevops_engi")
        If job_profile_id is 0 or None, returns "gdjob_unknown_{name}"
    
    Examples:
        >>> generate_jobprofile_slug(12881, "Senior Business Analyst - BizDevOps Engineer")
        'gdjob_12881_senior_business_analyst_bizdevops_engi'
        
        >>> generate_jobprofile_slug(99, "C++ & Python Expert!!!")
        'gdjob_99_c_python_expert'
        
        >>> generate_jobprofile_slug(0, "Senior Developer")
        'gdjob_unknown_senior_developer'
        
        >>> generate_jobprofile_slug(None, "Senior Developer")
        'gdjob_unknown_senior_developer'
    """
    name_slug = slugify(job_profile_name, max_length=max_length)
    
    # Fallback: If no valid ID, use "unknown"
    if job_profile_id is None or job_profile_id == 0 or job_profile_id == "":
        return f"gdjob_unknown_{name_slug}"
    
    # Handle string IDs (from document_id in jobprofile)
    if isinstance(job_profile_id, str):
        # Remove special characters from string IDs
        id_clean = re.sub(r'[^a-zA-Z0-9]', '', job_profile_id)
        if id_clean:
            return f"gdjob_{id_clean}_{name_slug}"
        else:
            return f"gdjob_unknown_{name_slug}"
    
    return f"gdjob_{job_profile_id}_{name_slug}"


def generate_candidate_name(vorname: str, nachname: str) -> str:
    """
    Generate candidate name for filenames.
    
    Format: {Vorname}_{Nachname}
    Preserves capitalization but removes special characters.
    
    Args:
        vorname: First name of the candidate
        nachname: Last name of the candidate
    
    Returns:
        Candidate name with underscore separator (e.g., "Marco_Rieben")
    
    Examples:
        >>> generate_candidate_name("Marco", "Rieben")
        'Marco_Rieben'
        
        >>> generate_candidate_name("Max", "Müller")
        'Max_Muller'
        
        >>> generate_candidate_name("Jean-Claude", "Van Damme")
        'JeanClaude_VanDamme'
    """
    # Replace German umlauts (preserve case)
    def replace_umlauts(text: str) -> str:
        replacements = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss'}
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    
    vorname_clean = replace_umlauts(vorname)
    nachname_clean = replace_umlauts(nachname)
    
    # Remove special characters, keep only alphanumeric (preserve case)
    vorname_clean = re.sub(r'[^a-zA-Z0-9]', '', vorname_clean)
    nachname_clean = re.sub(r'[^a-zA-Z0-9]', '', nachname_clean)
    
    return f"{vorname_clean}_{nachname_clean}"


def generate_filename(
    jobprofile_slug: str,
    candidate_name: str,
    filetype: str,
    timestamp: str,
    extension: str
) -> str:
    """
    Master function: Generate consistent filename for primary output files.
    
    Format: {jobprofile}_{candidate}_{filetype}_{timestamp}.{extension}
    
    Args:
        jobprofile_slug: Job Profile Slug (e.g., "gdjob_12881_senior_business_analyst")
        candidate_name: Candidate name (e.g., "Marco_Rieben")
        filetype: Document type (e.g., "cv", "offer", "dashboard")
        timestamp: Timestamp (e.g., "20260119_170806")
        extension: File extension without dot (e.g., "docx", "html", "json")
    
    Returns:
        Complete filename following naming conventions
    
    Examples:
        >>> generate_filename("gdjob_12881_senior_ba", "Marco_Rieben", "cv", "20260119_170806", "docx")
        'gdjob_12881_senior_ba_Marco_Rieben_cv_20260119_170806.docx'
        
        >>> generate_filename("gdjob_99_python_dev", "Max_Muller", "offer", "20260120_093000", "docx")
        'gdjob_99_python_dev_Max_Muller_offer_20260120_093000.docx'
    """
    # Validate filetype is lowercase
    filetype_clean = filetype.lower()
    
    # Remove dot from extension if present
    extension_clean = extension.lstrip('.')
    
    return f"{jobprofile_slug}_{candidate_name}_{filetype_clean}_{timestamp}.{extension_clean}"


def generate_folder_name(
    jobprofile_slug: str,
    candidate_name: str,
    timestamp: str
) -> str:
    """
    Generate folder name for ZIP archives and workspace directories.
    
    Format: {jobprofile}_{candidate}_{timestamp}
    
    Args:
        jobprofile_slug: Job Profile Slug
        candidate_name: Candidate name
        timestamp: Timestamp
    
    Returns:
        Folder name following naming conventions
    
    Examples:
        >>> generate_folder_name("gdjob_12881_senior_ba", "Marco_Rieben", "20260119_170806")
        'gdjob_12881_senior_ba_Marco_Rieben_20260119_170806'
    """
    return f"{jobprofile_slug}_{candidate_name}_{timestamp}"


def validate_filename(filename: str) -> tuple[bool, str]:
    """
    Validate filename against naming conventions.
    
    Checks for:
    - Invalid characters (only alphanumeric, _, -, . allowed)
    - Spaces (not allowed)
    - Double underscores (not allowed)
    - Length limits (min 10, max 200 chars)
    
    Args:
        filename: Filename to validate
    
    Returns:
        tuple[bool, str]: (is_valid, error_message)
            - is_valid: True if filename is valid, False otherwise
            - error_message: Empty string if valid, error description if invalid
    
    Examples:
        >>> validate_filename("gdjob_123_test_Marco_Rieben_cv_20260119_170806.docx")
        (True, '')
        
        >>> validate_filename("invalid file name.docx")
        (False, 'Filename contains spaces')
        
        >>> validate_filename("invalid__double__underscore.docx")
        (False, 'Filename contains double underscores')
    """
    # Check for invalid characters
    if re.search(r'[^a-zA-Z0-9_\-.]', filename):
        return False, "Filename contains invalid characters (only alphanumeric, _, -, . allowed)"
    
    # Check for spaces
    if ' ' in filename:
        return False, "Filename contains spaces"
    
    # Check for double underscores
    if '__' in filename:
        return False, "Filename contains double underscores"
    
    # Check minimum length
    if len(filename) < 10:
        return False, "Filename too short (min 10 characters)"
    
    # Check maximum length (Windows limit: 260 chars, safe limit: 200)
    if len(filename) > 200:
        return False, "Filename too long (max 200 characters)"
    
    return True, ""


def validate_naming_pattern(filename: str, expected_pattern: str = "primary") -> tuple[bool, str]:
    """
    Validate if filename matches expected naming pattern.
    
    Args:
        filename: Filename to validate
        expected_pattern: "primary" for output files, "folder" for directories
    
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    
    Patterns:
        - primary: {jobprofile}_{candidate}_{filetype}_{timestamp}.{ext}
        - folder: {jobprofile}_{candidate}_{timestamp}
    
    Examples:
        >>> validate_naming_pattern("gdjob_123_test_Marco_Rieben_cv_20260119_170806.docx", "primary")
        (True, '')
        
        >>> validate_naming_pattern("gdjob_123_test_Marco_Rieben_20260119_170806", "folder")
        (True, '')
        
        >>> validate_naming_pattern("invalid_name.docx", "primary")
        (False, "Filename doesn't match primary output pattern: invalid_name.docx")
    """
    if expected_pattern == "primary":
        # Expected: gdjob_{id}_{name}_{Candidate}_{filetype}_{timestamp}.{ext}
        # Pattern is flexible for name and candidate parts (alphanumeric + underscores)
        pattern = r'^gdjob_\d+_[a-z0-9_]+_[A-Za-z0-9_]+_(cv|offer|dashboard|match|feedback|jobprofile)_\d{8}_\d{6}\.\w+$'
        if not re.match(pattern, filename):
            return False, f"Filename doesn't match primary output pattern: {filename}"
    
    elif expected_pattern == "folder":
        # Expected: gdjob_{id}_{name}_{Candidate}_{timestamp}
        pattern = r'^gdjob_\d+_[a-z0-9_]+_[A-Za-z0-9_]+_\d{8}_\d{6}$'
        if not re.match(pattern, filename):
            return False, f"Foldername doesn't match pattern: {filename}"
    
    return True, ""


def extract_components_from_filename(filename: str) -> Optional[dict[str, str]]:
    """
    Extract naming components from a filename.
    
    Useful for parsing existing filenames to extract metadata.
    
    Args:
        filename: Filename following naming conventions
    
    Returns:
        dict with keys: jobprofile_id, jobprofile_name, candidate_name, filetype, timestamp, extension
        Returns None if filename doesn't match pattern
    
    Examples:
        >>> extract_components_from_filename("gdjob_123_senior_dev_Marco_Rieben_cv_20260119_170806.docx")
        {
            'jobprofile_id': '123',
            'jobprofile_name': 'senior_dev',
            'candidate_name': 'Marco_Rieben',
            'filetype': 'cv',
            'timestamp': '20260119_170806',
            'extension': 'docx'
        }
    """
    # Pattern: gdjob_{id}_{name}_{candidate}_{filetype}_{timestamp}.{ext}
    pattern = r'^gdjob_(\d+)_([a-z0-9_]+)_([A-Za-z0-9_]+)_(cv|offer|dashboard|match|feedback|jobprofile)_(\d{8}_\d{6})\.(\w+)$'
    match = re.match(pattern, filename)
    
    if not match:
        return None
    
    return {
        'jobprofile_id': match.group(1),
        'jobprofile_name': match.group(2),
        'candidate_name': match.group(3),
        'filetype': match.group(4),
        'timestamp': match.group(5),
        'extension': match.group(6)
    }
