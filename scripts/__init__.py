"""
CV Generator Scripts - Public API (Alias-Layer).

Consumer importieren ausschliesslich von hier:
    from scripts import extract_jobprofile, extract_cv, validate_cv
    from scripts import generate_matchmaking_json, generate_feedback_json
    from scripts import generate_offer_json, generate_offer_word
    from scripts import generate_dashboard
    from scripts import JOBPROFILE_SCHEMA_PATH, CV_SCHEMA_PATH, ...

Interne Ordnerstruktur (_1_extraction_jobprofile, _2_extraction_cv, ...)
ist Implementationsdetail und darf ausserhalb __init__.py nicht importiert werden.

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-21
Last Updated: 2026-01-26
"""

# ============================================================
# Public API - Import-Aliase
# ============================================================

# Step 1: Jobprofile Extraction
from scripts._1_extraction_jobprofile import extract_jobprofile
from scripts._1_extraction_jobprofile import SCHEMA_PATH as JOBPROFILE_SCHEMA_PATH

# Step 2: CV Extraction
from scripts._2_extraction_cv import extract_cv, validate_cv, generate_cv_word
from scripts._2_extraction_cv import SCHEMA_PATH as CV_SCHEMA_PATH

# Step 3: Matchmaking Analysis
from scripts._3_analysis_matchmaking import generate_matchmaking_json
from scripts._3_analysis_matchmaking import SCHEMA_PATH as MATCHMAKING_SCHEMA_PATH

# Step 4: CV Feedback
from scripts._4_analysis_feedback import generate_feedback_json
from scripts._4_analysis_feedback import SCHEMA_PATH as FEEDBACK_SCHEMA_PATH

# Step 5: Offer Generation
from scripts._5_generation_offer import generate_offer_json, generate_offer_word
from scripts._5_generation_offer import SCHEMA_PATH as OFFER_SCHEMA_PATH

# Step 6: Dashboard
from scripts._6_output_dashboard import generate_dashboard, generate_cv_word_on_demand
