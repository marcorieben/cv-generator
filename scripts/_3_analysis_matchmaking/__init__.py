"""
Step 3: Matchmaking Analysis - Public API.

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-26
Last Updated: 2026-01-26
"""
from scripts._3_analysis_matchmaking.matchmaking_generator import (
    generate_matchmaking_json,
    normalize_matching_values,
)
import os as _os

SCHEMA_PATH = _os.path.join(_os.path.dirname(__file__), "matchmaking_schema.json")
