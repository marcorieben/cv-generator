"""
Run ID generation with business-meaningful identifiers.

Purpose:
    Generate unique, human-readable run IDs incorporating business context
    (job profile, candidate, timestamp) for traceability and searchability.

Expected Lifetime: Core Module (Stable)

Format:
    jobprofile_candidate_timestamp
    Example: "Senior-Java-Developer_Marco-Rieben_20260127-142305"

Components:
    - jobprofile_slug: Normalized job profile title (max 50 chars)
    - candidate_slug: Normalized candidate name (max 50 chars)
    - timestamp: YYYYMMdd-HHMMSS

Usage:
    run_id = generate_run_id("Senior Java Developer", "Marco", "Rieben")
    # → "Senior-Java-Developer_Marco-Rieben_20260127-142305"
"""

import re
from datetime import datetime
from typing import Optional


def slugify(text: str, max_length: int = 50) -> str:
    """
    Normalize text for use in run IDs.
    
    Removes special characters, converts spaces to hyphens, truncates to max length.
    
    Args:
        text: Text to normalize
        max_length: Maximum length of output (default: 50)
        
    Returns:
        Normalized slug string
        
    Examples:
        >>> slugify("Senior Java Developer")
        'Senior-Java-Developer'
        >>> slugify("C++ & Python Expert!!!")
        'C-Python-Expert'
    """
    # Remove special characters (keep alphanumeric, spaces, hyphens)
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text)
    
    # Convert spaces to hyphens and normalize multiple hyphens
    text = re.sub(r'\s+', '-', text.strip())
    text = re.sub(r'-+', '-', text)
    
    # Truncate to max length
    return text[:max_length].strip('-')


def generate_run_id(
    jobprofile_title: str,
    firstname: str,
    lastname: str,
    timestamp: Optional[datetime] = None
) -> str:
    """
    Generate business-meaningful run ID for workspace isolation.
    
    Args:
        jobprofile_title: Job profile title (e.g., "Senior Java Developer")
        firstname: Candidate first name (e.g., "Marco")
        lastname: Candidate last name (e.g., "Rieben")
        timestamp: Optional timestamp (defaults to now)
        
    Returns:
        Run ID string in format: jobprofile_candidate_timestamp
        
    Examples:
        >>> generate_run_id("Senior Java Developer", "Marco", "Rieben")
        'Senior-Java-Developer_Marco-Rieben_20260127-142305'
        
        >>> generate_run_id("C++ Engineer", "Max", "Müller")
        'C-Engineer_Max-Muller_20260127-142305'
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    jobprofile_slug = slugify(jobprofile_title)
    candidate_slug = f"{slugify(firstname)}-{slugify(lastname)}"
    timestamp_str = timestamp.strftime('%Y%m%d-%H%M%S')
    
    return f"{jobprofile_slug}_{candidate_slug}_{timestamp_str}"
