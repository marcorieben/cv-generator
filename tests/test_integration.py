"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2025-12-17
Last Updated: 2026-01-24
"""
import subprocess
import sys
import os
import pytest


class TestDirectExecution:
    """Tests für direkte Ausführung von Scripts"""
    
    def test_generate_cv_imports_correctly(self):
        """Test dass cv_word.py ohne Import-Fehler startet"""
        # Test nur den Import, nicht die GUI
        code = """
import sys
sys.path.insert(0, '.')
try:
    from scripts import generate_cv_word
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
        from scripts._2_extraction_cv.cv_word import generate_cv, validate_json_structure
        from scripts._2_extraction_cv.cv_extractor import extract_cv
        from scripts._shared.pdf_utils import extract_text_from_pdf
        from scripts.dialogs import show_success, show_error, select_json_file
        
        # Wenn dieser Test durchläuft, sind alle Imports valide
        assert callable(generate_cv)
        assert callable(validate_json_structure)
        assert callable(extract_cv)
        assert callable(extract_text_from_pdf)
        assert callable(show_success)
        assert callable(show_error)
        assert callable(select_json_file)


class TestPathResolution:
    """Tests für korrekte Pfadauflösung in Scripts"""
    
    def test_pipeline_resolves_correct_base_directory(self):
        """Test dass pipeline.py das Projekt-Root korrekt findet"""
        # Simuliere die Pfadauflösung wie in pipeline.py
        pipeline_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'scripts',
            'pipeline.py'
        )
        
        # Berechne base_dir wie in pipeline.py
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(pipeline_file)))
        
        # Prüfe dass base_dir auf Projekt-Root zeigt, nicht auf scripts/
        assert os.path.basename(base_dir) == 'cv_generator'
        assert os.path.exists(os.path.join(base_dir, 'scripts'))
        assert os.path.exists(os.path.join(base_dir, 'input'))
        
        # Prüfe dass JSON-Pfad korrekt aufgelöst wird
        json_path = os.path.join(base_dir, "input", "cv", "json", "test.json")
        assert 'scripts' not in os.path.dirname(json_path).replace(base_dir, '')
        assert json_path.endswith(os.path.join('input', 'cv', 'json', 'test.json'))
    
    def test_generate_cv_resolves_styles_correctly(self):
        """Test dass generate_cv.py styles.json im scripts/ findet"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        from scripts._2_extraction_cv.cv_word import abs_path
        
        # abs_path sollte relativ zum scripts/ Verzeichnis auflösen
        styles_path = abs_path('styles.json')
        
        assert os.path.exists(styles_path)
        assert styles_path.endswith(os.path.join('scripts', 'styles.json'))
    
    def test_input_output_directories_exist(self):
        """Test dass input/ und output/ Verzeichnisse im richtigen Ort existieren"""
        project_root = os.path.dirname(os.path.dirname(__file__))
        
        # Diese Ordner sollten im Projekt-Root sein, nicht in scripts/
        input_dir = os.path.join(project_root, 'input')
        output_dir = os.path.join(project_root, 'output')
        
        assert os.path.exists(input_dir), f"input/ nicht gefunden: {input_dir}"
        assert os.path.exists(output_dir), f"output/ nicht gefunden: {output_dir}"
        
        # Neue Struktur: input/cv/ und input/stellenprofil/ mit Unterordnern
        assert os.path.exists(os.path.join(input_dir, 'cv', 'json'))
        assert os.path.exists(os.path.join(input_dir, 'cv', 'pdf'))
        assert os.path.exists(os.path.join(input_dir, 'stellenprofil', 'json'))
        assert os.path.exists(os.path.join(input_dir, 'stellenprofil', 'pdf'))
        # output/word is legacy, new structure uses per-run folders in output/

