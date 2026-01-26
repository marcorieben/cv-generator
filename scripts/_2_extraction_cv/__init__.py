"""
Step 2: CV Extraction - Public API.

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-26
Last Updated: 2026-01-26
"""
from scripts._2_extraction_cv.cv_extractor import extract_cv
from scripts._2_extraction_cv.cv_word import validate_json_structure as validate_cv
from scripts._2_extraction_cv.cv_word import generate_cv as generate_cv_word
import os as _os

SCHEMA_PATH = _os.path.join(_os.path.dirname(__file__), "cv_schema.json")
