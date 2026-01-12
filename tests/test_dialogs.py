"""
Tests für Dialog-Grössen und Sichtbarkeit
Stellt sicher, dass alle Dialog-Elemente sichtbar sind
"""
import pytest
from unittest.mock import patch, MagicMock


class TestDialogDimensions:
    """Tests für Dialog-Grössen und -Layout"""
    
    def test_success_dialog_height_without_details(self):
        """SuccessDialog ohne Details sollte Standard-Höhe haben"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import SuccessDialog
            
            dialog = SuccessDialog(
                title="Test",
                message="Test message"
            )
            
            # Höhe sollte Standard sein
            assert dialog.height == SuccessDialog.DEFAULT_HEIGHT, \
                f"SuccessDialog ohne Details sollte {SuccessDialog.DEFAULT_HEIGHT}px hoch sein, ist aber {dialog.height}px"

    def test_success_dialog_height_with_details_only(self):
        """SuccessDialog mit nur Details bleibt bei Standard-Höhe"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import SuccessDialog
            
            dialog = SuccessDialog(
                title="Test",
                message="Test message",
                details="Some details here"
            )
            
            # Höhe bleibt Standard - nur wenn Details UND file_path/dashboard vorhanden wird es grösser
            assert dialog.height == SuccessDialog.DEFAULT_HEIGHT

    def test_success_dialog_height_with_file_path(self):
        """SuccessDialog mit nur file_path bleibt bei Standard-Höhe"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import SuccessDialog
            
            dialog = SuccessDialog(
                title="Test",
                message="Test message",
                file_path="C:\\test\\file.docx"
            )
            
            # Höhe bleibt Standard
            assert dialog.height == SuccessDialog.DEFAULT_HEIGHT, \
                f"SuccessDialog mit nur file_path sollte {SuccessDialog.DEFAULT_HEIGHT}px hoch sein, ist aber {dialog.height}px"

    def test_success_dialog_height_with_both(self):
        """SuccessDialog mit Details UND file_path sollte grösser sein"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import SuccessDialog
            
            dialog = SuccessDialog(
                title="Test",
                message="Test message",
                details="Some details",
                file_path="C:\\test\\file.docx"
            )
            
            # Höhe sollte erweitert sein wenn Details UND file_path vorhanden
            assert dialog.height == SuccessDialog.EXPANDED_HEIGHT, \
                f"SuccessDialog mit Details und file_path sollte {SuccessDialog.EXPANDED_HEIGHT}px hoch sein, ist aber {dialog.height}px"
    def test_warning_dialog_height_without_details(self):
        """WarningDialog ohne Details sollte Standard-Höhe haben"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import WarningDialog
            
            dialog = WarningDialog(
                title="Warnung",
                message="Test warning"
            )
            
            # Höhe sollte Standard sein wenn keine Details
            assert dialog.height == WarningDialog.DEFAULT_HEIGHT, \
                f"WarningDialog ohne Details sollte {WarningDialog.DEFAULT_HEIGHT}px hoch sein, ist aber {dialog.height}px"
    
    def test_warning_dialog_height_with_details(self):
        """WarningDialog mit Details sollte erweitert sein"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import WarningDialog
            
            dialog = WarningDialog(
                title="Warnung",
                message="Test warning",
                details="🔴 KRITISCHE PROBLEME:\n❌ Error 1\n❌ Error 2"
            )
            
            # Höhe sollte erweitert sein wenn Details vorhanden
            assert dialog.height == WarningDialog.EXPANDED_HEIGHT, \
                f"WarningDialog mit Details sollte {WarningDialog.EXPANDED_HEIGHT}px hoch sein, ist aber {dialog.height}px"
    
    def test_error_dialog_height(self):
        """ErrorDialog sollte feste Höhe haben"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import ErrorDialog
            
            dialog = ErrorDialog(
                title="Fehler",
                message="Test error"
            )
            
            # ErrorDialog hat feste Höhe
            assert dialog.height == ErrorDialog.DEFAULT_HEIGHT, \
                f"ErrorDialog sollte {ErrorDialog.DEFAULT_HEIGHT}px hoch sein, ist aber {dialog.height}px"
    
    def test_confirm_dialog_height(self):
        """ConfirmDialog sollte kompakte Höhe haben"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import ConfirmDialog
            
            dialog = ConfirmDialog(
                title="Bestätigung",
                message="Test confirmation"
            )
            
            # ConfirmDialog ist kompakt
            assert dialog.height == ConfirmDialog.DEFAULT_HEIGHT, \
                f"ConfirmDialog sollte {ConfirmDialog.DEFAULT_HEIGHT}px hoch sein, ist aber {dialog.height}px"


class TestDialogMinimumDimensions:
    """Tests die sicherstellen, dass Dialoge gross genug für alle Elemente sind"""
    
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
            assert dialog.height == WarningDialog.EXPANDED_HEIGHT, \
                f"WarningDialog mit Details sollte genau {WarningDialog.EXPANDED_HEIGHT}px hoch sein"
    
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
            # 700px sollte ausreichen für alle Elemente
            assert dialog.height >= 450, \
                "SuccessDialog muss mindestens 450px hoch sein"
            assert dialog.height == SuccessDialog.EXPANDED_HEIGHT, \
                f"SuccessDialog mit Details/file_path sollte genau {SuccessDialog.EXPANDED_HEIGHT}px hoch sein"


class TestDialogWidthConsistency:
    """Tests für konsistente Dialog-Breiten"""
    
    def test_warning_dialog_width(self):
        """WarningDialog sollte Standard-Breite haben"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import WarningDialog
            
            dialog = WarningDialog(title="Test", message="Test")
            
            assert dialog.width == WarningDialog.DEFAULT_WIDTH, \
                f"WarningDialog sollte {WarningDialog.DEFAULT_WIDTH}px breit sein, ist aber {dialog.width}px"
    
    def test_success_dialog_width(self):
        """SuccessDialog sollte Standard-Breite haben"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import SuccessDialog
            
            dialog = SuccessDialog(title="Test", message="Test")
            
            assert dialog.width == SuccessDialog.DEFAULT_WIDTH, \
                f"SuccessDialog sollte {SuccessDialog.DEFAULT_WIDTH}px breit sein, ist aber {dialog.width}px"
    
    def test_error_dialog_width(self):
        """ErrorDialog sollte Standard-Breite haben"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import ErrorDialog
            
            dialog = ErrorDialog(title="Test", message="Test")
            
            assert dialog.width == ErrorDialog.DEFAULT_WIDTH, \
                f"ErrorDialog sollte {ErrorDialog.DEFAULT_WIDTH}px breit sein, ist aber {dialog.width}px"
    
    def test_confirm_dialog_width(self):
        """ConfirmDialog sollte Standard-Breite haben"""
        with patch('tkinter.Tk'):
            from scripts.dialogs import ConfirmDialog
            
            dialog = ConfirmDialog(title="Test", message="Test")
            
            assert dialog.width == ConfirmDialog.DEFAULT_WIDTH, \
                f"ConfirmDialog sollte {ConfirmDialog.DEFAULT_WIDTH}px breit sein, ist aber {dialog.width}px"

