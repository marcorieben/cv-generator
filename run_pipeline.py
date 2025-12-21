"""
Unified CV Generation Pipeline (Wrapper)
Delegiert an die neue Class-based Implementation in scripts/pipeline.py

Usage:
    python run_pipeline.py                     # Mit Dialog
    python run_pipeline.py path/to/file.pdf    # Direkt mit PDF
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
