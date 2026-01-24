"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2025-12-17
Last Updated: 2026-01-24
"""
import sys
import os

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Importiere die Main-Funktion aus der neuen Pipeline
from scripts.pipeline import main

if __name__ == "__main__":
    # Starte die neue Pipeline
    sys.exit(main())
