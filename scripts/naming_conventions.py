"""
Unified naming conventions for all modes (2, 3, 4).

Provides consistent file and folder naming across all CV processing modes.
Ensures dependency integrity and easy file tracking.
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any


def extract_job_profile_name(job_profile_data: Optional[Dict[str, Any]]) -> str:
    """
    Extract job profile name from Stellenprofil JSON data.
    
    Priority:
    1. Stellenprofil.Positition (job title)
    2. "jobprofile" (fallback)
    
    Args:
        job_profile_data: Parsed Stellenprofil JSON dict
        
    Returns:
        Sanitized job profile name
    """
    if not job_profile_data:
        return "jobprofile"
    
    # Try to extract position/title
    position = job_profile_data.get("Stelle", {})
    if isinstance(position, dict):
        position_name = position.get("Position", "") or position.get("Titel", "")
    else:
        position_name = str(position)
    
    if position_name:
        # Sanitize: remove special chars, limit length
        sanitized = "".join(c for c in position_name if c.isalnum() or c in "-_").lower()
        if sanitized:
            return sanitized[:30]  # Max 30 chars
    
    return "jobprofile"


def sanitize_filename(name: str, max_length: int = 50) -> str:
    """
    Sanitize a name for use in filenames.
    
    Args:
        name: Name to sanitize
        max_length: Maximum length
        
    Returns:
        Sanitized name safe for filenames
    """
    # Replace spaces and special chars with underscores
    sanitized = "".join(c if c.isalnum() else "_" for c in name)
    # Remove multiple underscores
    while "__" in sanitized:
        sanitized = sanitized.replace("__", "_")
    # Limit length
    return sanitized[:max_length].strip("_")


def get_output_folder_path(
    base_output_dir: str,
    job_profile_name: str,
    mode: str,  # "cv" for Mode 2/3, "batch-comparison" for Mode 4
    timestamp: str
) -> str:
    """
    Generate consistent output folder path for all modes.
    
    Folder naming convention:
    - Mode 2/3: jobprofileName_cv_timestamp
    - Mode 4: jobprofileName_batch-comparison_timestamp
    
    Args:
        base_output_dir: Base output directory (usually "output/")
        job_profile_name: Extracted job profile name
        mode: "cv" or "batch-comparison"
        timestamp: Timestamp string (YYYYMMDD_HHMMSS)
        
    Returns:
        Full path to output folder
    """
    folder_name = f"{job_profile_name}_{mode}_{timestamp}"
    folder_path = os.path.join(base_output_dir, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def get_cv_json_filename(
    job_profile_name: str,
    vorname: str,
    nachname: str,
    timestamp: str
) -> str:
    """
    Generate CV JSON filename.
    
    Convention: jobprofileName_candidateName_cv_timestamp.json
    
    Args:
        job_profile_name: Extracted job profile name
        vorname: Candidate first name
        nachname: Candidate last name
        timestamp: Timestamp string
        
    Returns:
        Filename (without path)
    """
    candidate_name = sanitize_filename(f"{vorname}_{nachname}")
    return f"{job_profile_name}_{candidate_name}_cv_{timestamp}.json"


def get_match_json_filename(
    job_profile_name: str,
    vorname: str,
    nachname: str,
    timestamp: str
) -> str:
    """
    Generate match JSON filename.
    
    Convention: jobprofileName_candidateName_match_timestamp.json
    """
    candidate_name = sanitize_filename(f"{vorname}_{nachname}")
    return f"{job_profile_name}_{candidate_name}_match_{timestamp}.json"


def get_feedback_json_filename(
    job_profile_name: str,
    vorname: str,
    nachname: str,
    timestamp: str
) -> str:
    """
    Generate feedback JSON filename.
    
    Convention: jobprofileName_candidateName_feedback_timestamp.json
    """
    candidate_name = sanitize_filename(f"{vorname}_{nachname}")
    return f"{job_profile_name}_{candidate_name}_feedback_{timestamp}.json"


def get_dashboard_html_filename(
    job_profile_name: str,
    vorname: str,
    nachname: str,
    timestamp: str
) -> str:
    """
    Generate dashboard HTML filename.
    
    Convention: jobprofileName_candidateName_dashboard_timestamp.html
    """
    candidate_name = sanitize_filename(f"{vorname}_{nachname}")
    return f"{job_profile_name}_{candidate_name}_dashboard_{timestamp}.html"


def get_angebot_json_filename(
    job_profile_name: str,
    vorname: str,
    nachname: str,
    timestamp: str
) -> str:
    """
    Generate offer JSON filename.
    
    Convention: jobprofileName_candidateName_angebot_timestamp.json
    """
    candidate_name = sanitize_filename(f"{vorname}_{nachname}")
    return f"{job_profile_name}_{candidate_name}_angebot_{timestamp}.json"


def get_angebot_word_filename(
    job_profile_name: str,
    vorname: str,
    nachname: str,
    timestamp: str
) -> str:
    """
    Generate offer Word filename.
    
    Convention: jobprofileName_candidateName_angebot_timestamp.docx
    """
    candidate_name = sanitize_filename(f"{vorname}_{nachname}")
    return f"{job_profile_name}_{candidate_name}_angebot_{timestamp}.docx"


def get_stellenprofil_json_filename(
    job_profile_name: str,
    timestamp: str
) -> str:
    """
    Generate Stellenprofil JSON filename (stored at folder root).
    
    Convention: jobprofileName_stellenprofil_timestamp.json
    """
    return f"{job_profile_name}_stellenprofil_{timestamp}.json"
