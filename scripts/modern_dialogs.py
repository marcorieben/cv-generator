"""
Modern Corporate-Styled Dialogs for CV Generator
Uses corporate colors from styles.json: Orange (#FF7900), Gray (#444444)
"""

import os
import json
import tkinter as tk
from tkinter import filedialog
from tkinter.font import Font


class ModernDialog:
    """Base class for modern corporate-styled dialogs"""
    
    # Corporate colors from styles.json
    ORANGE = "#FF7900"      # Primary brand color
    DARK_GRAY = "#444444"   # Secondary text/elements
    WHITE = "#FFFFFF"
    SUCCESS_GREEN = "#28A745"
    ERROR_RED = "#DC3545"
    WARNING_YELLOW = "#FFC107"
    LIGHT_GRAY = "#F8F9FA"
    
    # Icons (Unicode)
    ICON_SUCCESS = "✅"
    ICON_ERROR = "❌"
    ICON_WARNING = "⚠️"
    ICON_INFO = "ℹ️"
    ICON_QUESTION = "❓"
    ICON_FILE = "📄"
    ICON_JSON = "📋"
    ICON_WORD = "📝"
    
    def __init__(self, title, width=550, height=300):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")
        self.root.resizable(False, False)
        self.root.configure(bg=self.WHITE)
        
        # Center window
        self.root.eval('tk::PlaceWindow . center')
        self.root.attributes('-topmost', True)
        
        # Focus window
        self.root.focus_force()
        
        self.result = None
        
    def create_header(self, text, icon, bg_color):
        """Create styled header bar"""
        header = tk.Frame(self.root, bg=bg_color, height=60)
        header.pack(fill='x', side='top')
        header.pack_propagate(False)
        
        label = tk.Label(
            header,
            text=f"{icon}  {text}",
            bg=bg_color,
            fg=self.WHITE,
            font=('Segoe UI', 14, 'bold'),
            pady=15
        )
        label.pack()
        
        return header
    
    def create_content_frame(self):
        """Create white content area"""
        frame = tk.Frame(self.root, bg=self.WHITE)
        frame.pack(fill='both', expand=True, padx=30, pady=20, side='top')
        return frame
    
    def create_button(self, parent, text, command, is_primary=True, width=15):
        """Create styled button"""
        bg_color = self.ORANGE if is_primary else self.DARK_GRAY
        
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg_color,
            fg=self.WHITE,
            font=('Segoe UI', 10, 'bold'),
            width=width,
            relief='flat',
            cursor='hand2',
            pady=10,
            bd=0
        )
        
        # Hover effects
        def on_enter(e):
            btn.config(bg=self._darken_color(bg_color))
        
        def on_leave(e):
            btn.config(bg=bg_color)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    def _darken_color(self, hex_color, factor=0.9):
        """Darken a hex color for hover effect"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def show(self):
        """Display dialog and return result"""
        self.root.mainloop()
        return self.result


class SuccessDialog(ModernDialog):
    """Modern success message dialog"""
    
    def __init__(self, title="Erfolg", message="", details=None):
        super().__init__(title, width=600, height=380)
        
        # Header
        self.create_header(title, self.ICON_SUCCESS, self.SUCCESS_GREEN)
        
        # Content
        content = self.create_content_frame()
        
        # Main message
        msg_label = tk.Label(
            content,
            text=message,
            bg=self.WHITE,
            fg=self.DARK_GRAY,
            font=('Segoe UI', 11),
            justify='left',
            wraplength=540
        )
        msg_label.pack(anchor='w', pady=(0, 15))
        
        # Details section if provided
        if details:
            details_frame = tk.Frame(content, bg=self.LIGHT_GRAY, relief='flat', bd=0)
            details_frame.pack(fill='both', expand=True, pady=(10, 20))
            
            details_label = tk.Label(
                details_frame,
                text=details,
                bg=self.LIGHT_GRAY,
                fg=self.DARK_GRAY,
                font=('Segoe UI', 9),
                justify='left',
                wraplength=520
            )
            details_label.pack(anchor='w', padx=15, pady=15)
        
        # Button area
        btn_frame = tk.Frame(self.root, bg=self.WHITE)
        btn_frame.pack(side='bottom', pady=20)
        
        def close():
            self.result = True
            self.root.destroy()
        
        self.create_button(btn_frame, "OK", close, is_primary=True)


class ErrorDialog(ModernDialog):
    """Modern error message dialog"""
    
    def __init__(self, title="Fehler", message="", details=None):
        super().__init__(title, width=600, height=380)
        
        # Header
        self.create_header(title, self.ICON_ERROR, self.ERROR_RED)
        
        # Content
        content = self.create_content_frame()
        
        # Main message
        msg_label = tk.Label(
            content,
            text=message,
            bg=self.WHITE,
            fg=self.DARK_GRAY,
            font=('Segoe UI', 11, 'bold'),
            justify='left',
            wraplength=540
        )
        msg_label.pack(anchor='w', pady=(0, 15))
        
        # Details section if provided
        if details:
            # Details box with scrollbar
            details_frame = tk.Frame(content, bg=self.LIGHT_GRAY)
            details_frame.pack(fill='both', expand=True, pady=(10, 20))
            
            text_widget = tk.Text(
                details_frame,
                bg=self.LIGHT_GRAY,
                fg=self.DARK_GRAY,
                font=('Consolas', 9),
                wrap='word',
                relief='flat',
                bd=0,
                height=8
            )
            text_widget.pack(fill='both', expand=True, padx=15, pady=15)
            text_widget.insert('1.0', details)
            text_widget.config(state='disabled')
        
        # Button area
        btn_frame = tk.Frame(self.root, bg=self.WHITE)
        btn_frame.pack(side='bottom', pady=20)
        
        def close():
            self.result = False
            self.root.destroy()
        
        self.create_button(btn_frame, "Schließen", close, is_primary=False)


class WarningDialog(ModernDialog):
    """Modern warning dialog with Yes/No options"""
    
    def __init__(self, title="Warnung", message="", details=None):
        super().__init__(title, width=600, height=400)
        
        # Header
        self.create_header(title, self.ICON_WARNING, self.WARNING_YELLOW)
        
        # Content
        content = self.create_content_frame()
        
        # Main message
        msg_label = tk.Label(
            content,
            text=message,
            bg=self.WHITE,
            fg=self.DARK_GRAY,
            font=('Segoe UI', 11),
            justify='left',
            wraplength=540
        )
        msg_label.pack(anchor='w', pady=(0, 15))
        
        # Details section if provided
        if details:
            details_frame = tk.Frame(content, bg=self.LIGHT_GRAY)
            details_frame.pack(fill='both', expand=True, pady=(10, 20))
            
            text_widget = tk.Text(
                details_frame,
                bg=self.LIGHT_GRAY,
                fg=self.DARK_GRAY,
                font=('Segoe UI', 9),
                wrap='word',
                relief='flat',
                bd=0,
                height=8
            )
            scrollbar = tk.Scrollbar(details_frame, command=text_widget.yview)
            text_widget.config(yscrollcommand=scrollbar.set)
            
            scrollbar.pack(side='right', fill='y')
            text_widget.pack(fill='both', expand=True, padx=15, pady=15)
            text_widget.insert('1.0', details)
            text_widget.config(state='disabled')
        
        # Button area
        btn_frame = tk.Frame(self.root, bg=self.WHITE)
        btn_frame.pack(side='bottom', pady=20)
        
        def yes():
            self.result = True
            self.root.destroy()
        
        def no():
            self.result = False
            self.root.destroy()
        
        self.create_button(btn_frame, "Ja, fortfahren", yes, is_primary=True, width=18).pack(side='left', padx=5)
        self.create_button(btn_frame, "Abbrechen", no, is_primary=False, width=15).pack(side='left', padx=5)


class ConfirmDialog(ModernDialog):
    """Modern confirmation dialog with Yes/No options"""
    
    def __init__(self, title="Bestätigung", message="", icon_type="question"):
        super().__init__(title, width=550, height=250)
        
        # Select icon and color
        icon_map = {
            "question": (self.ICON_QUESTION, self.ORANGE),
            "info": (self.ICON_INFO, self.ORANGE),
            "success": (self.ICON_SUCCESS, self.SUCCESS_GREEN)
        }
        icon, color = icon_map.get(icon_type, (self.ICON_QUESTION, self.ORANGE))
        
        # Header
        self.create_header(title, icon, color)
        
        # Content
        content = self.create_content_frame()
        
        # Message
        msg_label = tk.Label(
            content,
            text=message,
            bg=self.WHITE,
            fg=self.DARK_GRAY,
            font=('Segoe UI', 11),
            justify='left',
            wraplength=490
        )
        msg_label.pack(anchor='w', pady=20)
        
        # Button area
        btn_frame = tk.Frame(self.root, bg=self.WHITE)
        btn_frame.pack(side='bottom', pady=20)
        
        def yes():
            self.result = True
            self.root.destroy()
        
        def no():
            self.result = False
            self.root.destroy()
        
        self.create_button(btn_frame, "Ja", yes, is_primary=True, width=12).pack(side='left', padx=5)
        self.create_button(btn_frame, "Nein", no, is_primary=False, width=12).pack(side='left', padx=5)


class WelcomeDialog(ModernDialog):
    """Welcome dialog explaining the CV generation process"""
    
    def __init__(self):
        super().__init__("CV Generator - Pipeline", width=650, height=520)
        
        # Header
        self.create_header("CV Generator", self.ICON_FILE, self.ORANGE)
        
        # Content
        content = tk.Frame(self.root, bg=self.WHITE)
        content.pack(fill='both', expand=False, padx=30, pady=20, side='top')
        
        # Welcome message
        welcome = tk.Label(
            content,
            text="Willkommen zum CV Generator Pipeline",
            bg=self.WHITE,
            fg=self.DARK_GRAY,
            font=('Segoe UI', 13, 'bold')
        )
        welcome.pack(anchor='w', pady=(0, 15))
        
        # Process explanation
        process_text = (
            "Dieser Prozess erstellt automatisch ein professionell formatiertes CV-Dokument "
            "in Ihrem Corporate Design."
        )
        process_label = tk.Label(
            content,
            text=process_text,
            bg=self.WHITE,
            fg=self.DARK_GRAY,
            font=('Segoe UI', 10),
            justify='left',
            wraplength=590
        )
        process_label.pack(anchor='w', pady=(0, 20))
        
        # Steps frame
        steps_frame = tk.Frame(content, bg=self.LIGHT_GRAY, relief='flat')
        steps_frame.pack(fill='x', pady=(0, 20))
        
        steps_title = tk.Label(
            steps_frame,
            text="Pipeline Schritte:",
            bg=self.LIGHT_GRAY,
            fg=self.DARK_GRAY,
            font=('Segoe UI', 10, 'bold')
        )
        steps_title.pack(anchor='w', padx=15, pady=(15, 10))
        
        steps = [
            "📄  PDF-Datei auswählen (Bewerbungsdossier/Lebenslauf)",
            "🤖  KI-gestützte Extraktion der Daten aus PDF",
            "📋  Strukturierung in JSON-Format",
            "✅  Validierung der extrahierten Daten",
            "📝  Generierung des formatierten Word-Dokuments"
        ]
        
        for step in steps:
            step_label = tk.Label(
                steps_frame,
                text=step,
                bg=self.LIGHT_GRAY,
                fg=self.DARK_GRAY,
                font=('Segoe UI', 10),
                anchor='w'
            )
            step_label.pack(anchor='w', padx=25, pady=4)
        
        tk.Label(steps_frame, bg=self.LIGHT_GRAY, height=1).pack()
        
        # Call to action
        cta_label = tk.Label(
            content,
            text="Klicken Sie auf 'PDF auswählen', um zu beginnen.",
            bg=self.WHITE,
            fg=self.ORANGE,
            font=('Segoe UI', 10, 'bold')
        )
        cta_label.pack(anchor='w', pady=(10, 0))
        
        # Button area - FIXED: ensure it's at bottom
        btn_frame = tk.Frame(self.root, bg=self.WHITE, height=80)
        btn_frame.pack(side='bottom', fill='x', pady=15)
        btn_frame.pack_propagate(False)  # Prevent shrinking
        
        # Container for centered buttons
        btn_container = tk.Frame(btn_frame, bg=self.WHITE)
        btn_container.place(relx=0.5, rely=0.5, anchor='center')
        
        def select_pdf():
            self.root.withdraw()  # Hide welcome dialog temporarily
            # Open file picker
            pdf_path = FilePickerDialog.open_pdf()
            if pdf_path:
                self.result = pdf_path  # Return the file path
            else:
                self.result = None  # User cancelled file picker
            self.root.destroy()
        
        def cancel():
            self.result = None
            self.root.destroy()
        
        btn_select = self.create_button(btn_container, "📄 PDF auswählen", select_pdf, is_primary=True, width=18)
        btn_select.pack(side='left', padx=5)
        
        btn_cancel = self.create_button(btn_container, "Abbrechen", cancel, is_primary=False, width=15)
        btn_cancel.pack(side='left', padx=5)


class FilePickerDialog:
    """Modern file picker with corporate styling"""
    
    @staticmethod
    def open_pdf(title="PDF-Datei auswählen", initial_dir=None):
        """Open file picker for PDF files"""
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        if not initial_dir:
            initial_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "input", "pdf")
        
        file_path = filedialog.askopenfilename(
            title=title,
            initialdir=initial_dir,
            filetypes=[
                ("PDF Dateien", "*.pdf"),
                ("Alle Dateien", "*.*")
            ]
        )
        
        root.destroy()
        return file_path if file_path else None
    
    @staticmethod
    def open_json(title="JSON-Datei auswählen", initial_dir=None):
        """Open file picker for JSON files"""
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        if not initial_dir:
            initial_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "input", "json")
        
        file_path = filedialog.askopenfilename(
            title=title,
            initialdir=initial_dir,
            filetypes=[
                ("JSON Dateien", "*.json"),
                ("Alle Dateien", "*.*")
            ]
        )
        
        root.destroy()
        return file_path if file_path else None


# Convenience functions for easy use
def show_success(message, title="Erfolg", details=None):
    """Show modern success dialog"""
    dialog = SuccessDialog(title, message, details)
    return dialog.show()


def show_error(message, title="Fehler", details=None):
    """Show modern error dialog"""
    dialog = ErrorDialog(title, message, details)
    return dialog.show()


def show_warning(message, title="Warnung", details=None):
    """Show modern warning dialog with Yes/No"""
    dialog = WarningDialog(title, message, details)
    return dialog.show()


def ask_yes_no(message, title="Bestätigung", icon_type="question"):
    """Show modern confirmation dialog"""
    dialog = ConfirmDialog(title, message, icon_type)
    return dialog.show()


def select_pdf_file(title="PDF-Datei auswählen"):
    """Show file picker for PDF"""
    return FilePickerDialog.open_pdf(title)


def select_json_file(title="JSON-Datei auswählen"):
    """Show file picker for JSON"""
    return FilePickerDialog.open_json(title)


def show_welcome():
    """Show welcome dialog explaining the CV generation pipeline"""
    dialog = WelcomeDialog()
    return dialog.show()  # Returns PDF path or None
