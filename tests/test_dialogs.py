"""
Tests für Dialog-Größen und Sichtbarkeit
Stellt sicher, dass alle Dialog-Elemente sichtbar sind
"""
import pytest
from unittest.mock import patch, MagicMock


class TestDialogDimensions:
    """Tests für Dialog-Größen und -Layout"""
    
    def test_success_dialog_height_without_details(self):
        """SuccessDialog ohne Details sollte 450px hoch sein"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import SuccessDialog
            
            dialog = SuccessDialog(
                title="Test",
                message="Test message"
            )
            
            # Höhe sollte 450px sein (Standard)
            assert dialog.height == 450, \
                f"SuccessDialog ohne Details sollte 450px hoch sein, ist aber {dialog.height}px"
    
    def test_success_dialog_height_with_details_only(self):
        """SuccessDialog mit nur Details bleibt bei 450px"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import SuccessDialog
            
            dialog = SuccessDialog(
                title="Test",
                message="Test message",
                details="Some details here"
            )
            
            # Höhe bleibt 450px - nur wenn Details UND file_path/dashboard vorhanden wird es 550px
            assert dialog.height == 450, \
                f"SuccessDialog mit nur Details sollte 450px hoch sein, ist aber {dialog.height}px"
    
    def test_success_dialog_height_with_file_path(self):
        """SuccessDialog mit nur file_path bleibt bei 450px"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import SuccessDialog
            
            dialog = SuccessDialog(
                title="Test",
                message="Test message",
                file_path="C:\\test\\file.docx"
            )
            
            # Höhe bleibt 450px
            assert dialog.height == 450, \
                f"SuccessDialog mit nur file_path sollte 450px hoch sein, ist aber {dialog.height}px"
    
    def test_success_dialog_height_with_both(self):
        """SuccessDialog mit Details UND file_path sollte größer sein"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import SuccessDialog
            
            dialog = SuccessDialog(
                title="Test",
                message="Test message",
                details="Some details",
                file_path="C:\\test\\file.docx"
            )
            
            # Höhe sollte 550px sein wenn Details UND file_path vorhanden
            assert dialog.height == 550, \
                f"SuccessDialog mit Details und file_path sollte 550px hoch sein, ist aber {dialog.height}px"
    
    def test_warning_dialog_height_without_details(self):
        """WarningDialog ohne Details sollte 400px hoch sein"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import WarningDialog
            
            dialog = WarningDialog(
                title="Warnung",
                message="Test warning"
            )
            
            # Höhe sollte 400px sein wenn keine Details
            assert dialog.height == 400, \
                f"WarningDialog ohne Details sollte 400px hoch sein, ist aber {dialog.height}px"
    
    def test_warning_dialog_height_with_details(self):
        """WarningDialog mit Details sollte 650px hoch sein"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import WarningDialog
            
            dialog = WarningDialog(
                title="Warnung",
                message="Test warning",
                details="🔴 KRITISCHE PROBLEME:\n❌ Error 1\n❌ Error 2"
            )
            
            # Höhe sollte 650px sein wenn Details vorhanden (Platz für scrollbare Liste)
            assert dialog.height == 650, \
                f"WarningDialog mit Details sollte 650px hoch sein, ist aber {dialog.height}px"
    
    def test_error_dialog_height(self):
        """ErrorDialog sollte feste Höhe haben"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import ErrorDialog
            
            dialog = ErrorDialog(
                title="Fehler",
                message="Test error"
            )
            
            # ErrorDialog hat feste Höhe von 380px
            assert dialog.height == 380, \
                f"ErrorDialog sollte 380px hoch sein, ist aber {dialog.height}px"
    
    def test_confirm_dialog_height(self):
        """ConfirmDialog sollte kompakte Höhe haben"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import ConfirmDialog
            
            dialog = ConfirmDialog(
                title="Bestätigung",
                message="Test confirmation"
            )
            
            # ConfirmDialog ist kompakt, 250px
            assert dialog.height == 250, \
                f"ConfirmDialog sollte 250px hoch sein, ist aber {dialog.height}px"


class TestDialogMinimumDimensions:
    """Tests die sicherstellen, dass Dialoge groß genug für alle Elemente sind"""
    
    def test_warning_dialog_minimum_height_for_buttons(self):
        """WarningDialog muss hoch genug sein, dass Buttons sichtbar sind"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import WarningDialog
            
            dialog = WarningDialog(
                title="Warnung",
                message="Test",
                details="Very long details\n" * 50  # Viele Details
            )
            
            # Auch mit vielen Details müssen Buttons sichtbar bleiben
            # 650px sollte ausreichen für Details-Scrollbereich + Buttons (jeweils ~40px)
            assert dialog.height >= 400, \
                "WarningDialog muss mindestens 400px hoch sein für Buttons"
            assert dialog.height == 650, \
                "WarningDialog mit Details sollte genau 650px hoch sein"
    
    def test_success_dialog_minimum_height_for_buttons(self):
        """SuccessDialog muss hoch genug sein, dass alle Buttons sichtbar sind"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import SuccessDialog
            
            dialog = SuccessDialog(
                title="Erfolg",
                message="Test",
                details="Some details",
                file_path="C:\\test.docx"
            )
            
            # Mit Details und file_path gibt es 2 Buttons: "OK" und "Word öffnen"
            # 550px sollte ausreichen für alle Elemente
            assert dialog.height >= 450, \
                "SuccessDialog muss mindestens 450px hoch sein"
            assert dialog.height == 550, \
                "SuccessDialog mit Details/file_path sollte genau 550px hoch sein"


class TestDialogWidthConsistency:
    """Tests für konsistente Dialog-Breiten"""
    
    def test_warning_dialog_width(self):
        """WarningDialog sollte 650px breit sein"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import WarningDialog
            
            dialog = WarningDialog(title="Test", message="Test")
            
            assert dialog.width == 650, \
                f"WarningDialog sollte 650px breit sein, ist aber {dialog.width}px"
    
    def test_success_dialog_width(self):
        """SuccessDialog sollte 650px breit sein"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import SuccessDialog
            
            dialog = SuccessDialog(title="Test", message="Test")
            
            assert dialog.width == 650, \
                f"SuccessDialog sollte 650px breit sein, ist aber {dialog.width}px"
    
    def test_error_dialog_width(self):
        """ErrorDialog sollte 600px breit sein"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import ErrorDialog
            
            dialog = ErrorDialog(title="Test", message="Test")
            
            assert dialog.width == 600, \
                f"ErrorDialog sollte 600px breit sein, ist aber {dialog.width}px"
    
    def test_confirm_dialog_width(self):
        """ConfirmDialog sollte 550px breit sein"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import ConfirmDialog
            
            dialog = ConfirmDialog(title="Test", message="Test")
            
            assert dialog.width == 550, \
                f"ConfirmDialog sollte 550px breit sein, ist aber {dialog.width}px"

