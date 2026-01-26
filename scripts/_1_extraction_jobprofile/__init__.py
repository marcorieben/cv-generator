"""
Step 1: Jobprofile Extraction - Public API.

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-26
Last Updated: 2026-01-26
"""
from scripts._1_extraction_jobprofile.jobprofile_extractor import extract_jobprofile
import os as _os

SCHEMA_PATH = _os.path.join(_os.path.dirname(__file__), "jobprofile_schema.json")
