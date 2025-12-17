"""
Integration Tests für direkte Script-Ausführung
Testet, dass Entry Points ohne Import-Fehler starten
"""
import subprocess
import sys
import os
import pytest


class TestDirectExecution:
    """Tests für direkte Ausführung von Scripts"""
    
    def test_generate_cv_imports_correctly(self):
        """Test dass generate_cv.py ohne Import-Fehler startet"""
        # Test nur den Import, nicht die GUI
        code = """
import sys
sys.path.insert(0, '.')
try:
    from scripts import generate_cv
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"""
        result = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert 'SUCCESS' in result.stdout, f"Import failed: {result.stderr}"
        assert result.returncode == 0
    
    def test_pipeline_imports_correctly(self):
        """Test dass pipeline.py ohne Import-Fehler startet"""
        code = """
import sys
sys.path.insert(0, '.')
try:
    from scripts import pipeline
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"""
        result = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert 'SUCCESS' in result.stdout, f"Import failed: {result.stderr}"
        assert result.returncode == 0
    
    def test_dialogs_imports_correctly(self):
        """Test dass dialogs.py ohne Import-Fehler startet"""
        code = """
import sys
sys.path.insert(0, '.')
try:
    from scripts import dialogs
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"""
        result = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert 'SUCCESS' in result.stdout, f"Import failed: {result.stderr}"
        assert result.returncode == 0
    
    def test_pdf_to_json_imports_correctly(self):
        """Test dass pdf_to_json.py ohne Import-Fehler startet"""
        code = """
import sys
sys.path.insert(0, '.')
try:
    from scripts import pdf_to_json
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"""
        result = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert 'SUCCESS' in result.stdout, f"Import failed: {result.stderr}"
        assert result.returncode == 0


class TestModuleFunctions:
    """Tests für kritische Modul-Funktionen"""
    
    def test_all_modules_have_required_functions(self):
        """Prüfe dass alle Module ihre Hauptfunktionen exportieren"""
        from scripts.generate_cv import generate_cv, validate_json_structure
        from scripts.pdf_to_json import pdf_to_json, extract_text_from_pdf
        from scripts.dialogs import show_success, show_error, select_json_file
        
        # Wenn dieser Test durchläuft, sind alle Imports valide
        assert callable(generate_cv)
        assert callable(validate_json_structure)
        assert callable(pdf_to_json)
        assert callable(extract_text_from_pdf)
        assert callable(show_success)
        assert callable(show_error)
        assert callable(select_json_file)
