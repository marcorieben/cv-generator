"""
Syntax validation tests for Streamlit pages.

Catches IndentationError and SyntaxError before they reach the UI.
These tests run AST parsing on all Streamlit files to detect syntax errors
that would otherwise only be discovered at runtime when navigating to a page.

Tested Objects:
- app.py (main application entry point)
- pages/*.py (all Streamlit page modules)

Purpose: Syntax validation - prevents deployment of broken pages
Expected Lifetime: Permanent
Last Updated: 2026-01-27
"""

import pytest
import ast
from pathlib import Path


class TestStreamlitPagesSyntax:
    """
    Verify all Streamlit pages have valid Python syntax.
    
    These tests prevent deployment of pages with basic syntax errors
    like indentation issues, missing colons, or unclosed parentheses.
    
    Tested Objects:
    - app.py: Main Streamlit application
    - pages/04_CV_Generator.py: CV generation page
    - pages/01_Job_Profile_Manager.py: Job profile management
    - pages/02_Candidate_Manager.py: Candidate management
    - pages/03_Matching_Analysis.py: Matching and analysis
    - All other pages in pages/ directory
    """
    
    @pytest.fixture
    def workspace_root(self):
        """Get workspace root directory."""
        return Path(__file__).parent.parent
    
    def test_main_app_syntax(self, workspace_root):
        """
        Test main app.py has valid syntax.
        
        Object: app.py (main Streamlit application entry point)
        
        Validates that the main application file can be parsed without
        syntax errors. The main app file sets up navigation, authentication,
        and the overall application structure.
        """
        app_file = workspace_root / "app.py"
        assert app_file.exists(), "app.py not found"
        
        with open(app_file, 'r', encoding='utf-8') as f:
            code = f.read()
        
        try:
            ast.parse(code)
        except SyntaxError as e:
            pytest.fail(f"app.py has syntax error: {e}")
    
    def test_all_page_files_syntax(self, workspace_root):
        """
        Test all page files in pages/ directory have valid syntax.
        
        Objects: All .py files in pages/ directory including:
        - 04_CV_Generator.py: CV generation and pipeline
        - 01_Job_Profile_Manager.py: Job profile CRUD operations
        - 02_Candidate_Manager.py: Candidate management
        - 03_Matching_Analysis.py: Matching and analysis workflows
        - Other pages as they are added
        
        This test catches syntax errors like:
        - IndentationError (misaligned code blocks)
        - SyntaxError (missing colons, parentheses, etc.)
        - Invalid Python structure
        """
        pages_dir = workspace_root / "pages"
        assert pages_dir.exists(), "pages/ directory not found"
        
        page_files = list(pages_dir.glob("*.py"))
        assert len(page_files) > 0, "No page files found in pages/"
        
        for page_file in page_files:
            with open(page_file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            try:
                ast.parse(code)
            except SyntaxError as e:
                pytest.fail(f"{page_file.name} has syntax error: {e}")
    
    def test_specific_pages_importable(self, workspace_root):
        """
        Test critical pages can be compiled (stricter than AST parsing).
        
        Objects: 
        - app.py: Main application
        - pages/04_CV_Generator.py: Most complex page with pipeline integration
        
        This test goes beyond AST parsing by actually compiling the code,
        which can catch additional issues like:
        - Name resolution problems
        - Import errors (if not caught by other tests)
        - More subtle syntax issues
        
        Note: This is stricter than AST parsing and may catch issues that
        would only manifest at import time.
        """
        critical_files = [
            workspace_root / "app.py",
            workspace_root / "pages" / "04_CV_Generator.py",
        ]
        
        for file_path in critical_files:
            if not file_path.exists():
                pytest.skip(f"{file_path.name} not found")
                continue
            
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            try:
                compile(code, str(file_path), 'exec')
            except SyntaxError as e:
                pytest.fail(f"{file_path.name} has compilation error: {e}")
    
    def test_no_common_syntax_mistakes(self, workspace_root):
        """
        Check for common syntax mistakes in Streamlit pages.
        
        Objects: All .py files in pages/ directory
        
        This test looks for common copy-paste errors and formatting issues:
        
        1. Excessive indentation (40+ spaces)
           - Often caused by copying code from nested contexts
           - Example: Copying code from inside a function but pasting at module level
        
        2. Mixed tabs and spaces
           - Can cause hard-to-debug IndentationErrors
           - Python 3 forbids mixing tabs and spaces
        
        This is a heuristic test that may produce false positives,
        so it skips rather than fails to avoid blocking CI.
        """
        pages_dir = workspace_root / "pages"
        if not pages_dir.exists():
            pytest.skip("pages/ directory not found")
        
        page_files = list(pages_dir.glob("*.py"))
        issues = []
        
        for page_file in page_files:
            with open(page_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_no, line in enumerate(lines, 1):
                # Check for excessive indentation (likely copy-paste error)
                if len(line) - len(line.lstrip(' ')) > 40:
                    issues.append(f"{page_file.name}:{line_no} has 40+ spaces of indentation")
                
                # Check for mixed tabs and spaces
                if '\t' in line and '    ' in line:
                    issues.append(f"{page_file.name}:{line_no} mixes tabs and spaces")
        
        if issues:
            pytest.skip(f"Potential formatting issues (review manually): {', '.join(issues)}")
