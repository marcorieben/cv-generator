"""
Unified naming conventions for all modes (2, 3, 4).

Provides consistent file and folder naming across all CV processing modes.
Ensures dependency integrity and easy file tracking.
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any


def extract_job_profile_name_from_file(job_file_path: str) -> str:
    """
    Extract job profile name from uploaded file name.
    
    Takes filename (e.g., "Senior_Sales_Manager.pdf") and converts to
    (e.g., "senior_sales_manager")
    
    Args:
        job_file_path: File path or filename
        
    Returns:
        Sanitized job profile name
    """
    if not job_file_path:
        return "jobprofile"
    
    # Extract filename without extension
    filename = os.path.basename(job_file_path)
    name_without_ext = os.path.splitext(filename)[0]
    
    # Sanitize: remove special chars, lowercase
    sanitized = sanitize_filename(name_without_ext, max_length=50)
    
    return sanitized if sanitized else "jobprofile"


def extract_job_profile_name(job_profile_data: Optional[Dict[str, Any]]) -> str:
    """
    Extract job profile name from Stellenprofil JSON data.
    
    Priority:
    1. Stellenprofil.Stelle.Position (job title)
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
        sanitized = sanitize_filename(position_name, max_length=50)
        if sanitized:
            return sanitized
    
    return "jobprofile"


def extract_candidate_name_from_file(cv_file_path: str) -> str:
    """
    Extract candidate name from uploaded CV file name.
    
    Takes filename (e.g., "Max_Mustermann.pdf" or "Max.pdf") and converts to
    sanitized form (e.g., "max_mustermann" or "max")
    
    Args:
        cv_file_path: File path or filename
        
    Returns:
        Sanitized candidate name
    """
    if not cv_file_path:
        return "candidate"
    
    # Extract filename without extension
    filename = os.path.basename(cv_file_path)
    name_without_ext = os.path.splitext(filename)[0]
    
    # Sanitize: remove special chars, lowercase
    sanitized = sanitize_filename(name_without_ext, max_length=50)
    
    return sanitized if sanitized else "candidate"


def extract_candidate_name(cv_data: Optional[Dict[str, Any]]) -> str:
    """
    Extract candidate name from CV JSON data.
    
    Priority:
    1. Vorname + Nachname
    2. "candidate" (fallback)
    
    Args:
        cv_data: Parsed CV JSON dict
        
    Returns:
        Sanitized candidate name (lastname_firstname or firstname_lastname)
    """
    if not cv_data:
        return "candidate"
    
    vorname = cv_data.get("Vorname", "").strip()
    nachname = cv_data.get("Nachname", "").strip()
    
    if vorname and nachname:
        candidate_name = f"{nachname}_{vorname}"
    elif vorname:
        candidate_name = vorname
    elif nachname:
        candidate_name = nachname
    else:
        candidate_name = "candidate"
    
    sanitized = sanitize_filename(candidate_name, max_length=50)
    return sanitized if sanitized else "candidate"


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
    sanitized = "".join(c if c.isalnum() else "_" for c in name.lower())
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


def get_candidate_subfolder_path(
    batch_folder: str,
    candidate_name: str,
    timestamp: str
) -> str:
    """
    Generate candidate subfolder path within batch folder.
    
    Convention: candidateName_timestamp
    
    Args:
        batch_folder: Path to parent batch folder
        candidate_name: Extracted candidate name
        timestamp: Timestamp string (YYYYMMDD_HHMMSS)
        
    Returns:
        Full path to candidate subfolder
    """
    subfolder_name = f"{candidate_name}_{timestamp}"
    subfolder_path = os.path.join(batch_folder, subfolder_name)
    os.makedirs(subfolder_path, exist_ok=True)
    return subfolder_path


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
    candidate_name = extract_candidate_name({
        "Vorname": vorname,
        "Nachname": nachname
    })
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
    candidate_name = extract_candidate_name({
        "Vorname": vorname,
        "Nachname": nachname
    })
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
    candidate_name = extract_candidate_name({
        "Vorname": vorname,
        "Nachname": nachname
    })
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
    candidate_name = extract_candidate_name({
        "Vorname": vorname,
        "Nachname": nachname
    })
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
    candidate_name = extract_candidate_name({
        "Vorname": vorname,
        "Nachname": nachname
    })
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
    candidate_name = extract_candidate_name({
        "Vorname": vorname,
        "Nachname": nachname
    })
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


def build_output_path(
    mode: str,
    candidate_name: str = "",
    stellenprofil: str = "",
    artifact_type: str = "cv",
    is_batch: bool = False,
    timestamp: Optional[str] = None,
    base_output_dir: str = "output"
) -> Dict[str, str]:
    """
    Centralized function for all naming conventions across all modes.
    
    This function generates consistent paths and filenames based on:
    - Mode (basic or professional_analysis)
    - Batch flag (single CV vs multiple CVs)
    - Artifact type (cv, match, feedback, dashboard)
    
    Args:
        mode (str): 'basic' or 'professional_analysis'
        candidate_name (str): Candidate name (will be normalized)
        stellenprofil (str): Job profile name (will be normalized)
        artifact_type (str): Type of artifact ('cv', 'match', 'feedback', 'dashboard')
        is_batch (bool): True if batch processing, False for single
        timestamp (str, optional): Custom timestamp (YYYYMMDD_HHMMSS), auto-generated if None
        base_output_dir (str): Base output directory (default: 'output')
    
    Returns:
        Dict with keys:
        - 'mode': The mode used ('basic' or 'professional_analysis')
        - 'is_batch': Whether batch processing
        - 'folder_name': Name of the output folder (without path)
        - 'file_name': Name of the output file (without extension, without path)
        - 'file_with_ext': File name with extension
        - 'folder_path': Full path to folder
        - 'file_path': Full path to file
        
    Examples:
        # BASIC Mode (CV only, single)
        build_output_path(
            mode='basic',
            candidate_name='fischer_arthur',
            artifact_type='cv'
        )
        → {
            'folder_name': 'fischer_arthur_20260119_114357',
            'file_name': 'fischer_arthur_cv_20260119_114357',
            'file_with_ext': 'fischer_arthur_cv_20260119_114357.docx',
            'folder_path': 'output/fischer_arthur_20260119_114357',
            'file_path': 'output/fischer_arthur_20260119_114357/fischer_arthur_cv_20260119_114357.docx'
        }
        
        # PROFESSIONAL ANALYSIS (Single CV)
        build_output_path(
            mode='professional_analysis',
            candidate_name='fischer_arthur',
            stellenprofil='senior_business_analyst',
            artifact_type='cv',
            is_batch=False
        )
        → {
            'folder_name': 'senior_business_analyst_fischer_arthur_20260119_114357',
            'file_name': 'senior_business_analyst_fischer_arthur_cv_20260119_114357',
            'file_path': '.../senior_business_analyst_fischer_arthur_cv_20260119_114357.docx'
        }
        
        # PROFESSIONAL ANALYSIS (Batch)
        build_output_path(
            mode='professional_analysis',
            candidate_name='fischer_arthur',
            stellenprofil='senior_business_analyst',
            artifact_type='cv',
            is_batch=True
        )
        → Batch subfolder structure:
            batch_comparison_senior_business_analyst_20260119_114357/
            └── senior_business_analyst_fischer_arthur_20260119_114357/
                └── senior_business_analyst_fischer_arthur_cv_20260119_114357.docx
    """
    
    # Generate timestamp if not provided
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Normalize names
    candidate_normalized = sanitize_filename(candidate_name, max_length=50) if candidate_name else ""
    stellenprofil_normalized = sanitize_filename(stellenprofil, max_length=50) if stellenprofil else ""
    
    # Validate mode
    if mode not in ['basic', 'professional_analysis']:
        raise ValueError(f"Invalid mode '{mode}'. Must be 'basic' or 'professional_analysis'")
    
    # ========== MODE 1: BASIC (CV only) ==========
    if mode == 'basic':
        if not candidate_normalized:
            candidate_normalized = 'candidate'
        
        # Folder: candidate_timestamp
        folder_name = f"{candidate_normalized}_{timestamp}"
        # File: candidate_artifact_timestamp
        file_name = f"{candidate_normalized}_{artifact_type}_{timestamp}"
        
        folder_path = os.path.join(base_output_dir, folder_name)
        file_path = os.path.join(folder_path, f"{file_name}.ext")
        
        return {
            'mode': mode,
            'is_batch': False,
            'folder_name': folder_name,
            'file_name': file_name,
            'file_with_ext': f"{file_name}.ext",
            'folder_path': folder_path,
            'file_path': file_path,
            'timestamp': timestamp
        }
    
    # ========== MODE 2: PROFESSIONAL ANALYSIS ==========
    if mode == 'professional_analysis':
        if not stellenprofil_normalized:
            raise ValueError("stellenprofil is required for professional_analysis mode")
        
        if not candidate_normalized:
            candidate_normalized = 'candidate'
        
        # ===== CASE 1: BATCH MODE =====
        if is_batch:
            # Batch folder: batch_comparison_stellenprofil_timestamp
            batch_folder_name = f"batch_comparison_{stellenprofil_normalized}_{timestamp}"
            batch_folder_path = os.path.join(base_output_dir, batch_folder_name)
            
            # Stellenprofil JSON at batch root: stellenprofil_timestamp.json
            stellenprofil_file_name = f"{stellenprofil_normalized}_{timestamp}"
            stellenprofil_file_path = os.path.join(batch_folder_path, f"{stellenprofil_file_name}.json")
            
            # Candidate subfolder: stellenprofil_candidate_timestamp
            candidate_subfolder_name = f"{stellenprofil_normalized}_{candidate_normalized}_{timestamp}"
            candidate_subfolder_path = os.path.join(batch_folder_path, candidate_subfolder_name)
            
            # File in candidate subfolder: stellenprofil_candidate_artifact_timestamp
            file_name = f"{stellenprofil_normalized}_{candidate_normalized}_{artifact_type}_{timestamp}"
            file_path = os.path.join(candidate_subfolder_path, f"{file_name}.ext")
            
            return {
                'mode': mode,
                'is_batch': True,
                'batch_folder_name': batch_folder_name,
                'batch_folder_path': batch_folder_path,
                'stellenprofil_file_name': stellenprofil_file_name,
                'stellenprofil_file_path': stellenprofil_file_path,
                'candidate_subfolder_name': candidate_subfolder_name,
                'candidate_subfolder_path': candidate_subfolder_path,
                'folder_name': candidate_subfolder_name,  # Alias for compatibility
                'file_name': file_name,
                'file_with_ext': f"{file_name}.ext",
                'folder_path': candidate_subfolder_path,  # Alias for compatibility
                'file_path': file_path,
                'timestamp': timestamp
            }
        
        # ===== CASE 2: SINGLE CV MODE =====
        else:
            # Folder: stellenprofil_candidate_timestamp
            folder_name = f"{stellenprofil_normalized}_{candidate_normalized}_{timestamp}"
            folder_path = os.path.join(base_output_dir, folder_name)
            
            # File: stellenprofil_candidate_artifact_timestamp
            file_name = f"{stellenprofil_normalized}_{candidate_normalized}_{artifact_type}_{timestamp}"
            file_path = os.path.join(folder_path, f"{file_name}.ext")
            
            return {
                'mode': mode,
                'is_batch': False,
                'folder_name': folder_name,
                'file_name': file_name,
                'file_with_ext': f"{file_name}.ext",
                'folder_path': folder_path,
                'file_path': file_path,
                'timestamp': timestamp
            }

