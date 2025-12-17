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
        self.width = width
        self.height = height
        self.root = tk.Tk()
        self.root.title(title)
        self.root.resizable(False, False)
        self.root.configure(bg=self.WHITE)
        
        # Set size first
        self.root.geometry(f"{width}x{height}")
        
        # Withdraw to position offscreen before centering
        self.root.withdraw()
        self.root.update_idletasks()
        
        # Center window on main screen (horizontal and vertical)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Show window at centered position
        self.root.deiconify()
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
    
    def __init__(self, title="Erfolg", message="", details=None, file_path=None):
        # Increase height if we have both details and file button
        height = 420 if (details and file_path) else 380
        super().__init__(title, width=600, height=height)
        
        # Store file path for opening
        self.file_path = file_path
        
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
        btn_frame.pack(side='bottom', fill='x', pady=20)
        
        btn_container = tk.Frame(btn_frame, bg=self.WHITE)
        btn_container.pack(side='right', padx=30)
        
        def close():
            self.result = None  # Just close without opening
            self.root.destroy()
        
        def open_file():
            self.result = 'open'  # Signal to open file
            self.root.destroy()
        
        # Show "Open Document" button if file_path is provided
        if self.file_path:
            self.create_button(btn_container, "Schließen", close, is_primary=False, width=15).pack(side='left', padx=5)
            self.create_button(btn_container, "📝 Dokument öffnen", open_file, is_primary=True, width=20).pack(side='left', padx=5)
        else:
            self.create_button(btn_container, "OK", close, is_primary=True)


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
        btn_frame.pack(side='bottom', fill='x', pady=20)
        
        btn_container = tk.Frame(btn_frame, bg=self.WHITE)
        btn_container.pack(side='right', padx=30)
        
        def close():
            self.result = False
            self.root.destroy()
        
        self.create_button(btn_container, "Schließen", close, is_primary=False)


class WarningDialog(ModernDialog):
    """Modern warning dialog with Yes/No options"""
    
    def __init__(self, title="Warnung", message="", details=None):
        # Dynamic height: larger if details present
        dialog_height = 650 if details else 400
        super().__init__(title, width=650, height=dialog_height)
        
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
            
            # Configure tags for colored text
            text_widget.tag_configure("critical_header", foreground="#DC3545", font=('Segoe UI', 9, 'bold'))
            text_widget.tag_configure("info_header", foreground="#FFC107", font=('Segoe UI', 9, 'bold'))
            text_widget.tag_configure("critical_text", foreground="#DC3545")
            text_widget.tag_configure("info_text", foreground="#FF8C00")
            text_widget.tag_configure("footer", foreground="#444444", font=('Segoe UI', 9, 'italic'))
            
            scrollbar.pack(side='right', fill='y')
            text_widget.pack(fill='both', expand=True, padx=15, pady=15)
            
            # Parse and insert text with colors
            lines = details.split('\n')
            in_critical_section = False
            in_info_section = False
            
            for line in lines:
                if line.startswith("🔴 KRITISCHE PROBLEME:"):
                    text_widget.insert('end', line + '\n', 'critical_header')
                    in_critical_section = True
                    in_info_section = False
                elif line.startswith("🟡 WENIGER KRITISCHE HINWEISE:"):
                    text_widget.insert('end', line + '\n', 'info_header')
                    in_critical_section = False
                    in_info_section = True
                elif line.startswith("💡"):
                    text_widget.insert('end', line + '\n', 'footer')
                    in_critical_section = False
                    in_info_section = False
                elif line.strip().startswith(("❌", "⚠️", "🚫", "🔴")) and in_critical_section:
                    # Critical item with icon
                    text_widget.insert('end', line + '\n', 'critical_text')
                elif line.strip().startswith(("💡", "ℹ️", "🟡")) and in_info_section:
                    # Info item with icon
                    text_widget.insert('end', line + '\n', 'info_text')
                else:
                    text_widget.insert('end', line + '\n')
            
            text_widget.config(state='disabled')
        
        # Button area (pack first so it's at bottom)
        btn_frame = tk.Frame(self.root, bg=self.WHITE)
        btn_frame.pack(side='bottom', fill='x', pady=(0, 20))
        
        btn_container = tk.Frame(btn_frame, bg=self.WHITE)
        btn_container.pack(side='right', padx=30)
        
        # Question label above buttons (pack after so it's above)
        question_label = tk.Label(
            self.root,
            text="💡 Möchten Sie trotz der Probleme mit der Generierung fortfahren?",
            bg=self.WHITE,
            fg=self.DARK_GRAY,
            font=('Segoe UI', 10),
            anchor='e',
            justify='right'
        )
        question_label.pack(side='bottom', fill='x', padx=30, pady=(10, 10))
        
        def yes():
            self.result = True
            self.root.destroy()
        
        def no():
            self.result = False
            self.root.destroy()
        
        self.create_button(btn_container, "Abbrechen", no, is_primary=False, width=18).pack(side='left', padx=5)
        self.create_button(btn_container, "Ja, fortfahren", yes, is_primary=True, width=20).pack(side='left', padx=5)


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
        btn_frame.pack(side='bottom', fill='x', pady=20)
        
        btn_container = tk.Frame(btn_frame, bg=self.WHITE)
        btn_container.pack(side='right', padx=30)
        
        def yes():
            self.result = True
            self.root.destroy()
        
        def no():
            self.result = False
            self.root.destroy()
        
        self.create_button(btn_container, "Nein", no, is_primary=False, width=12).pack(side='left', padx=5)
        self.create_button(btn_container, "Ja", yes, is_primary=True, width=12).pack(side='left', padx=5)


class WelcomeDialog(ModernDialog):
    """Welcome dialog explaining the CV generation process"""
    
    def __init__(self):
        super().__init__("CV Generator - Pipeline", width=750, height=650)
        
        # Header
        self.create_header("CV Generator", self.ICON_FILE, self.ORANGE)
        
        # Content
        content = tk.Frame(self.root, bg=self.WHITE)
        content.pack(fill='both', expand=False, padx=30, pady=20, side='top')
        
        # Welcome message
        welcome = tk.Label(
            content,
            text="Willkommen zum CV Generator",
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
            wraplength=690
        )
        process_label.pack(anchor='w', pady=(0, 10))
        
        # Internet requirement notice
        internet_notice = tk.Label(
            content,
            text="ℹ️  Hinweis: Eine aktive Internetverbindung ist erforderlich.",
            bg=self.WHITE,
            fg=self.ORANGE,
            font=('Segoe UI', 9, 'bold'),
            justify='left'
        )
        internet_notice.pack(anchor='w', pady=(0, 20))
        
        # Pipeline visualization - horizontal boxes (centered)
        pipeline_outer = tk.Frame(content, bg=self.WHITE)
        pipeline_outer.pack(fill='x', pady=(10, 20))
        
        pipeline_container = tk.Frame(pipeline_outer, bg=self.WHITE)
        pipeline_container.pack(anchor='center')
        
        # Pipeline steps with icons
        steps = [
            ("📄", "PDF\nauswählen"),
            ("🤖", "KI-\nExtraktion"),
            ("📋", "JSON-\nStruktur"),
            ("✅", "Vali-\ndierung"),
            ("📝", "Word-\nDokument")
        ]
        
        # Create horizontal layout with arrows
        for i, (icon, label) in enumerate(steps):
            # Step box
            step_box = tk.Frame(pipeline_container, bg=self.LIGHT_GRAY, relief='flat', bd=1)
            step_box.pack(side='left', padx=5)
            
            # Icon
            icon_label = tk.Label(
                step_box,
                text=icon,
                bg=self.LIGHT_GRAY,
                font=('Segoe UI', 20)
            )
            icon_label.pack(pady=(10, 5))
            
            # Label
            text_label = tk.Label(
                step_box,
                text=label,
                bg=self.LIGHT_GRAY,
                fg=self.DARK_GRAY,
                font=('Segoe UI', 9),
                justify='center'
            )
            text_label.pack(pady=(0, 10), padx=10)
            
            # Arrow between steps (except after last step)
            if i < len(steps) - 1:
                arrow_label = tk.Label(
                    pipeline_container,
                    text="→",
                    bg=self.WHITE,
                    fg=self.ORANGE,
                    font=('Segoe UI', 16, 'bold')
                )
                arrow_label.pack(side='left', padx=3)
        
        # DSGVO Compliance Section
        dsgvo_frame = tk.Frame(content, bg=self.LIGHT_GRAY, relief='flat', bd=1)
        dsgvo_frame.pack(fill='x', pady=(20, 10))
        
        dsgvo_title = tk.Label(
            dsgvo_frame,
            text="⚖️  Datenschutzbestimmungen (DSGVO)",
            bg=self.LIGHT_GRAY,
            fg=self.DARK_GRAY,
            font=('Segoe UI', 10, 'bold')
        )
        dsgvo_title.pack(anchor='w', padx=15, pady=(15, 10))
        
        # Checkbox variables
        consent_vars = {
            'openai': tk.BooleanVar(value=False),
            'personal': tk.BooleanVar(value=False),
            'consent': tk.BooleanVar(value=False)
        }
        
        # Checkbox texts
        consent_texts = [
            ("openai", "Der/die Kandidat/in hat der Verarbeitung der CV-Daten über eine KI-basierte API zugestimmt."),
            ("personal", "Die ausdrückliche Einwilligung der betroffenen Person zur Datenverarbeitung liegt vor."),
            ("consent", "Die betroffene Person wurde über die Datenschutzhinweise informiert und hat diese akzeptiert.")
        ]
        
        # Create checkboxes
        for key, text in consent_texts:
            cb_frame = tk.Frame(dsgvo_frame, bg=self.LIGHT_GRAY)
            cb_frame.pack(anchor='w', padx=25, pady=5)
            
            cb = tk.Checkbutton(
                cb_frame,
                text="",
                variable=consent_vars[key],
                bg=self.LIGHT_GRAY,
                activebackground=self.LIGHT_GRAY,
                selectcolor=self.WHITE,
                font=('Segoe UI', 9),
                command=lambda: update_button_state()
            )
            cb.pack(side='left')
            
            label = tk.Label(
                cb_frame,
                text=text,
                bg=self.LIGHT_GRAY,
                fg=self.DARK_GRAY,
                font=('Segoe UI', 9),
                justify='left',
                wraplength=620
            )
            label.pack(side='left', padx=(5, 0))
        
        tk.Label(dsgvo_frame, bg=self.LIGHT_GRAY, height=1).pack()
        
        # Button area - positioned at bottom right
        btn_frame = tk.Frame(self.root, bg=self.WHITE, height=80)
        btn_frame.pack(side='bottom', fill='x', pady=15)
        btn_frame.pack_propagate(False)  # Prevent shrinking
        
        # Container for right-aligned buttons
        btn_container = tk.Frame(btn_frame, bg=self.WHITE)
        btn_container.pack(side='right', padx=30)
        
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
        
        btn_cancel = self.create_button(btn_container, "Abbrechen", cancel, is_primary=False, width=15)
        btn_cancel.pack(side='left', padx=5)
        
        btn_select = self.create_button(btn_container, "📄 PDF auswählen", select_pdf, is_primary=True, width=18)
        btn_select.pack(side='left', padx=5)
        
        # Initially disable PDF select button
        btn_select.config(state='disabled', bg='#CCCCCC', cursor='arrow')
        
        def update_button_state():
            """Enable/disable button based on all checkboxes"""
            all_checked = all(var.get() for var in consent_vars.values())
            if all_checked:
                btn_select.config(state='normal', bg=self.ORANGE, cursor='hand2')
            else:
                btn_select.config(state='disabled', bg='#CCCCCC', cursor='arrow')


class FilePickerDialog:
    """Modern file picker with corporate styling"""
    
    @staticmethod
    def open_pdf(title="PDF-Datei auswählen", initial_dir=None):
        """Open file picker for PDF files"""
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        if not initial_dir:
            initial_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "input", "cv", "pdf")
        
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
            initial_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "input", "cv", "json")
        
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
def show_success(message, title="Erfolg", details=None, file_path=None):
    """Show modern success dialog with optional file open button"""
    dialog = SuccessDialog(title, message, details, file_path)
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
