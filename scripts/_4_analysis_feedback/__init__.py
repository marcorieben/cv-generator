"""
Step 4: CV Feedback Analysis - Public API.

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-26
Last Updated: 2026-01-26
"""
from scripts._4_analysis_feedback.feedback_generator import generate_cv_feedback_json as generate_feedback_json
import os as _os

SCHEMA_PATH = _os.path.join(_os.path.dirname(__file__), "feedback_schema.json")
