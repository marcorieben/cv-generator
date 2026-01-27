"""
Step 5: Offer Generation - Public API.

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-26
Last Updated: 2026-01-27
"""
from scripts._5_generation_offer.offer_generator import generate_angebot_json as generate_offer_json
from scripts._5_generation_offer.offer_word import generate_angebot_word as generate_offer_word
from scripts._5_generation_offer.offer_word import generate_offer_bytes  # F003: Storage abstraction
import os as _os

SCHEMA_PATH = _os.path.join(_os.path.dirname(__file__), "offer_schema.json")
