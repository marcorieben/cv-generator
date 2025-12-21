"""
Test script for ProcessingDialog
Tests the logic of the processing dialog using mocks
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to path
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def test_cv_only():
    """Test mit nur CV-Dokument"""
    with patch('tkinter.Tk'), patch('tkinter.Label'), patch('tkinter.Frame'):
        from scripts.dialogs import show_processing
        
        dialog = show_processing("Max_Mustermann_CV.pdf")
        
        assert dialog.cv_filename == "Max_Mustermann_CV.pdf"
        assert dialog.stellenprofil_filename is None
        
        # Verify steps are initialized
        assert len(dialog.steps) == 8
        assert dialog.step_widgets is not None

def test_cv_and_angebot():
    """Test mit CV und Angebot"""
    with patch('tkinter.Tk'), patch('tkinter.Label'), patch('tkinter.Frame'):
        from scripts.dialogs import show_processing
        
        dialog = show_processing(
            "Max_Mustermann_CV.pdf",
            "Stellenangebot_Senior_Developer.pdf"
        )
        
        assert dialog.cv_filename == "Max_Mustermann_CV.pdf"
        assert dialog.stellenprofil_filename == "Stellenangebot_Senior_Developer.pdf"
