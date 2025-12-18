# Test entry point for dialog development


# Test entry point for dialog development (wirklich am Dateiende)
if __name__ == "__main__":
    result = show_welcome()
    print("Dialog result:", result)
"""
Modern Corporate-Styled Dialogs for CV Generator
Uses corporate colors from styles.json: Orange (#FF7900), Gray (#444444)
"""

import os
import json
import tkinter as tk
import platform
import subprocess
from tkinter import filedialog
from tkinter.font import Font

# Enable High DPI support on Windows
if platform.system() == "Windows":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


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
        self.root.lift()  # Force window to top of stack
        
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
    
    def create_button(self, parent, text, command, is_primary=True, width=15, bg_color=None):
        """Create styled button"""
        if bg_color is None:
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
    
    def __init__(self, title="Erfolg", message="", details=None, file_path=None, dashboard_path=None, match_score=None):
        # Increase height if we have both details and file button
        height = 550 if (details and (file_path or dashboard_path)) else 450
        super().__init__(title, width=650, height=height)
        
        # Store file paths
        self.file_path = file_path
        self.dashboard_path = dashboard_path
        
        # Header
        self.create_header(title, self.ICON_SUCCESS, self.SUCCESS_GREEN)
        
        # Button area (Pack first to ensure visibility at bottom)
        btn_frame = tk.Frame(self.root, bg=self.WHITE)
        btn_frame.pack(side='bottom', fill='x', pady=20)
        
        btn_container = tk.Frame(btn_frame, bg=self.WHITE)
        btn_container.pack(side='right', padx=30)

        # Content
        content = self.create_content_frame()
        
        # Top section with message and optional meter
        top_frame = tk.Frame(content, bg=self.WHITE)
        top_frame.pack(fill='x', pady=(0, 15))
        
        # Main message (Left)
        msg_label = tk.Label(
            top_frame,
            text=message,
            bg=self.WHITE,
            fg=self.DARK_GRAY,
            font=('Segoe UI', 11),
            justify='left',
            wraplength=400 if match_score is not None else 540
        )
        msg_label.pack(side='left', anchor='nw', fill='x', expand=True)
        
        # Meter (Right) if score exists
        if match_score is not None:
            self.create_meter(top_frame, match_score)
        
        # Details section if provided
        if details:
            details_frame = tk.Frame(content, bg=self.LIGHT_GRAY, relief='flat', bd=0)
            details_frame.pack(fill='both', expand=True, pady=(10, 20))
            
            # Scrollbar
            scrollbar = tk.Scrollbar(details_frame)
            scrollbar.pack(side='right', fill='y')
            
            # Text widget
            text_widget = tk.Text(
                details_frame,
                bg=self.LIGHT_GRAY,
                fg=self.DARK_GRAY,
                font=('Segoe UI', 9),
                wrap='word',
                relief='flat',
                bd=0,
                height=10,
                yscrollcommand=scrollbar.set
            )
            text_widget.pack(fill='both', expand=True, padx=15, pady=15)
            
            # Configure bold tag
            text_widget.tag_configure("bold_header", font=('Segoe UI', 9, 'bold'))
            
            # Parse details and insert with tags
            lines = details.split('\n')
            for line in lines:
                if any(header in line for header in ["📂 INPUT DATEIEN:", "📤 OUTPUT DATEIEN:", "📍 Speicherort:"]):
                    text_widget.insert('end', line + '\n', 'bold_header')
                else:
                    text_widget.insert('end', line + '\n')
            
            text_widget.config(state='disabled')
            
            scrollbar.config(command=text_widget.yview)
        
        def close():
            self.result = None
            self.root.destroy()
        
        def open_file_action(path):
            try:
                if platform.system() == 'Windows':
                    os.startfile(path)
                elif platform.system() == 'Darwin':
                    subprocess.run(['open', path])
                else:
                    subprocess.run(['xdg-open', path])
            except Exception as e:
                print(f"Error opening file: {e}")

        # Buttons
        self.create_button(btn_container, "Schließen", close, is_primary=False, width=15).pack(side='left', padx=5)
        
        if self.dashboard_path:
             self.create_button(btn_container, "📊 Dashboard", lambda: open_file_action(self.dashboard_path), is_primary=True, width=15, bg_color="#3498db").pack(side='left', padx=5)

        if self.file_path:
            self.create_button(btn_container, "📝 Word CV", lambda: open_file_action(self.file_path), is_primary=True, width=15).pack(side='left', padx=5)

    def create_meter(self, parent, score):
        """Create a visual meter for the match score"""
        meter_frame = tk.Frame(parent, bg=self.WHITE)
        meter_frame.pack(side='right', padx=(20, 0))
        
        # Increased size for better resolution
        canvas_size = 100
        canvas = tk.Canvas(meter_frame, width=canvas_size, height=canvas_size, bg=self.WHITE, highlightthickness=0)
        canvas.pack()
        
        padding = 8
        width = 10
        
        # Draw background circle (gray)
        canvas.create_oval(padding, padding, canvas_size-padding, canvas_size-padding, outline="#F0F0F0", width=width)
        
        # Determine color based on score
        if score >= 80: color = "#28A745" # Green
        elif score >= 60: color = "#FFC107" # Yellow
        else: color = "#DC3545" # Red
        
        # Draw progress arc
        angle = (score / 100) * 360
        # Use style='arc' for just the line
        canvas.create_arc(padding, padding, canvas_size-padding, canvas_size-padding, 
                         start=90, extent=-angle, outline=color, width=width, style='arc')
        
        # Draw text
        canvas.create_text(canvas_size/2, canvas_size/2, text=f"{score}%", font=('Segoe UI', 16, 'bold'), fill=self.DARK_GRAY)
        
        tk.Label(meter_frame, text="Match Score", bg=self.WHITE, fg="#777777", font=('Segoe UI', 9)).pack()


class ErrorDialog(ModernDialog):
    """Modern error message dialog"""
    
    def __init__(self, title="Fehler", message="", details=None):
        super().__init__(title, width=600, height=380)
        
        # Header
        self.create_header(title, self.ICON_ERROR, self.ERROR_RED)
        
        # Button area (Pack first to ensure visibility at bottom)
        btn_frame = tk.Frame(self.root, bg=self.WHITE)
        btn_frame.pack(side='bottom', fill='x', pady=20)
        
        btn_container = tk.Frame(btn_frame, bg=self.WHITE)
        btn_container.pack(side='right', padx=30)

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
        
        # Button area (pack first so it's at bottom)
        btn_frame = tk.Frame(self.root, bg=self.WHITE)
        btn_frame.pack(side='bottom', fill='x', pady=(0, 20))
        
        btn_container = tk.Frame(btn_frame, bg=self.WHITE)
        btn_container.pack(side='right', padx=30)

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
        
        # Button area (pack first so it's at bottom)
        btn_frame = tk.Frame(self.root, bg=self.WHITE)
        btn_frame.pack(side='bottom', fill='x', pady=20)
        
        btn_container = tk.Frame(btn_frame, bg=self.WHITE)
        btn_container.pack(side='right', padx=30)

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
        # Increased height to accommodate High DPI scaling and content
        super().__init__("CV Generator - Pipeline", width=750, height=950)
        
        # Initialize file paths
        self.cv_path = None
        self.stellenprofil_path = None
        self.cv_upload_btn = None
        self.stellenprofil_upload_btn = None
        
        # --- 1. Button Area (Create first to ensure visibility at bottom) ---
        btn_frame = tk.Frame(self.root, bg=self.WHITE, height=80)
        btn_frame.pack(side='bottom', fill='x', pady=(0, 15))
        btn_frame.pack_propagate(False)
        
        btn_container = tk.Frame(btn_frame, bg=self.WHITE)
        btn_container.pack(side='right', padx=50)
        
        def proceed():
            """Proceed with selected files"""
            if self.cv_path:
                self.result = (self.cv_path, self.stellenprofil_path, self.selected_model.get())
                self.root.destroy()
        
        def cancel():
            self.result = None
            self.root.destroy()
            
        btn_cancel = self.create_button(btn_container, "Abbrechen", cancel, is_primary=False, width=18)
        btn_cancel.pack(side='left', padx=5)
        
        btn_weiter = self.create_button(btn_container, "Weiter →", proceed, is_primary=True, width=18)
        btn_weiter.pack(side='left', padx=5)
        
        # Initially disable Weiter button
        btn_weiter.config(state='disabled', bg='#CCCCCC', cursor='arrow')
        
        def update_weiter_button():
            """Enable Weiter button only when CV is selected"""
            if self.cv_path:
                btn_weiter.config(state='normal', bg=self.ORANGE, cursor='hand2')
            else:
                btn_weiter.config(state='disabled', bg='#CCCCCC', cursor='arrow')

        # --- 2. Model Selection (Top) ---
        # Default: gpt-4o-mini
        self.selected_model = tk.StringVar(value="gpt-4o-mini")
        model_frame = tk.Frame(self.root, bg=self.WHITE)
        model_frame.pack(fill='x', padx=30, pady=(10, 0), anchor='w')
        
        tk.Label(
            model_frame,
            text="KI-Modell auswählen:",
            bg=self.WHITE,
            fg=self.DARK_GRAY,
            font=('Segoe UI', 10, 'bold')
        ).pack(side='left', padx=(0, 10))
        
        model_options = [
            ("GPT-4o Mini (empfohlen, günstig) – ca. 0,01€ (nur CV) / 0,02€ (CV+Stellenprofil)", "gpt-4o-mini"),
            ("GPT-4o (höchste Qualität) – ca. 0,10€ (nur CV) / 0,20€ (CV+Stellenprofil)", "gpt-4o"),
            ("GPT-3.5 Turbo (günstig, weniger präzise) – ca. 0,005€ (nur CV) / 0,01€ (CV+Stellenprofil)", "gpt-3.5-turbo-1106"),
            ("🧪 Test-Modus (Mock-Daten, kostenlos) – Keine KI-Kosten", "mock")
        ]
        
        # Show labels in dropdown, but use model name as value
        from tkinter import StringVar
        self.model_labels = [opt[0] for opt in model_options]
        self.model_values = [opt[1] for opt in model_options]
        self.label_to_value = dict(zip(self.model_labels, self.model_values))
        self.selected_model_label = StringVar(value=self.model_labels[0])
        
        def on_model_select(label):
            val = self.label_to_value[label]
            self.selected_model.set(val)
            self.selected_model_label.set(label)
            
            # If Mock mode selected, enable "Weiter" immediately and skip file checks
            if val == "mock":
                # Auto-fill dummy paths if not set
                if not self.cv_path:
                    self.cv_path = "MOCK_CV.pdf"
                    self.cv_status_label.config(text="MOCK-Modus: Keine Datei nötig", fg=self.ORANGE)
                if not self.stellenprofil_path:
                    self.stellenprofil_path = "MOCK_STELLENPROFIL.pdf"
                    self.stellenprofil_status_label.config(text="MOCK-Modus: Keine Datei nötig", fg=self.ORANGE)
                
                # Enable button regardless of DSGVO
                btn_weiter.config(state='normal', bg=self.ORANGE, cursor='hand2')
            else:
                # Reset if switching back from mock
                if self.cv_path == "MOCK_CV.pdf":
                    self.cv_path = None
                    self.cv_status_label.config(text="Bitte laden Sie hier den Lebenslauf hoch.", fg=self.DARK_GRAY)
                if self.stellenprofil_path == "MOCK_STELLENPROFIL.pdf":
                    self.stellenprofil_path = None
                    self.stellenprofil_status_label.config(text="Optional: Stellenprofil für maßgeschneiderten CV hochladen.", fg="#777777")
                
                # Re-evaluate button state
                update_weiter_button()

        tk.OptionMenu(
            model_frame,
            self.selected_model_label,
            *self.model_labels,
            command=on_model_select
        ).pack(side='left')

        # --- 3. Header ---
        self.create_header("CV Generator", self.ICON_FILE, self.ORANGE)
        
        # --- 4. Content Area ---
        content = tk.Frame(self.root, bg=self.WHITE)
        content.pack(fill='both', expand=True, padx=30, pady=(20, 10), side='top')
        
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
        
        # Pipeline visualization
        pipeline_outer = tk.Frame(content, bg=self.WHITE)
        pipeline_outer.pack(fill='x', pady=(10, 20))
        
        pipeline_container = tk.Frame(pipeline_outer, bg=self.WHITE)
        pipeline_container.pack(anchor='center')
        
        steps = [
            ("📄", "PDF\nauswählen"),
            ("🤖", "KI-\nExtraktion"),
            ("📋", "JSON-\nStruktur"),
            ("✅", "Vali-\ndierung"),
            ("📝", "Word-\nDokument")
        ]
        
        for i, (icon, label) in enumerate(steps):
            step_box = tk.Frame(pipeline_container, bg=self.LIGHT_GRAY, relief='flat', bd=1)
            step_box.pack(side='left', padx=5)
            
            icon_label = tk.Label(step_box, text=icon, bg=self.LIGHT_GRAY, font=('Segoe UI', 20))
            icon_label.pack(pady=(10, 5))
            
            text_label = tk.Label(step_box, text=label, bg=self.LIGHT_GRAY, fg=self.DARK_GRAY, font=('Segoe UI', 9), justify='center')
            text_label.pack(pady=(0, 10), padx=10)
            
            if i < len(steps) - 1:
                arrow_label = tk.Label(pipeline_container, text="→", bg=self.WHITE, fg=self.ORANGE, font=('Segoe UI', 16, 'bold'))
                arrow_label.pack(side='left', padx=3)
        
        # DSGVO Compliance Section
        dsgvo_frame = tk.Frame(content, bg=self.LIGHT_GRAY, relief='flat', bd=1)
        dsgvo_frame.pack(fill='x', pady=(10, 10))
        
        dsgvo_title = tk.Label(
            dsgvo_frame,
            text="⚖️  Datenschutzbestimmungen (DSGVO)",
            bg=self.LIGHT_GRAY,
            fg=self.DARK_GRAY,
            font=('Segoe UI', 10, 'bold')
        )
        dsgvo_title.pack(anchor='w', padx=15, pady=(12, 8))
        
        consent_var = tk.BooleanVar(value=False)
        cb_frame = tk.Frame(dsgvo_frame, bg=self.LIGHT_GRAY)
        cb_frame.pack(anchor='w', padx=25, pady=(0, 12))
        
        cb = tk.Checkbutton(
            cb_frame,
            text="",
            variable=consent_var,
            bg=self.LIGHT_GRAY,
            activebackground=self.LIGHT_GRAY,
            selectcolor=self.WHITE,
            font=('Segoe UI', 9)
        )
        cb.pack(side='left')
        
        label = tk.Label(
            cb_frame,
            text="Ich bestätige, dass die betroffene Person über die Datenverarbeitung informiert wurde und der Nutzung von KI-basierten Diensten zur CV-Erstellung zugestimmt hat.",
            bg=self.LIGHT_GRAY,
            fg=self.DARK_GRAY,
            font=('Segoe UI', 9),
            justify='left',
            wraplength=620
        )
        label.pack(side='left', padx=(5, 0))
        
        # --- File Selection Section ---
        # Schritt 1: CV-PDF
        self.cv_frame = tk.Frame(content, bg=self.LIGHT_GRAY, relief='flat', bd=2)
        self.cv_frame.pack(fill='x', pady=(10, 10))
        
        cv_header = tk.Frame(self.cv_frame, bg=self.LIGHT_GRAY)
        cv_header.pack(fill='x', padx=15, pady=(12, 8))
        
        cv_label_container = tk.Frame(cv_header, bg=self.LIGHT_GRAY)
        cv_label_container.pack(side='left')

        self.cv_header_label = tk.Label(cv_label_container, text="📄  Schritt 1: CV-PDF", bg=self.LIGHT_GRAY, fg=self.DARK_GRAY, font=('Segoe UI', 11, 'bold'))
        self.cv_header_label.pack(side='left')

        self.cv_required_label = tk.Label(cv_label_container, text=" (Pflichtfeld)", bg=self.LIGHT_GRAY, fg=self.ORANGE, font=('Segoe UI', 10, 'bold'))
        self.cv_required_label.pack(side='left')
        
        def select_cv():
            cv_path = FilePickerDialog.open_pdf(title="CV-PDF auswählen")
            if cv_path:
                self.cv_path = cv_path
                filename = os.path.basename(cv_path)
                success_bg = "#E8F5E9"
                self.cv_frame.config(bg=success_bg, bd=2, relief='solid')
                cv_header.config(bg=success_bg)
                cv_label_container.config(bg=success_bg)
                self.cv_header_label.config(bg=success_bg, fg="#2E7D32")
                self.cv_required_label.config(text=" ✓", bg=success_bg, fg="#2E7D32")
                self.cv_status_label.config(text=f"Ausgewählt: {filename}", bg=success_bg)
                self.cv_upload_btn.config(text="Ändern", bg=self.SUCCESS_GREEN)
                update_weiter_button()
        
        self.cv_upload_btn = self.create_button(cv_header, "📤 CV wählen", select_cv, is_primary=True, width=18)
        self.cv_upload_btn.pack(side='right', padx=10)
        
        self.cv_status_label = tk.Label(self.cv_frame, text="Bitte laden Sie hier den Lebenslauf hoch.", bg=self.LIGHT_GRAY, fg=self.DARK_GRAY, font=('Segoe UI', 9))
        self.cv_status_label.pack(anchor='w', padx=25, pady=(0, 12))
        
        # Schritt 2: Stellenprofil-PDF
        self.stellenprofil_frame = tk.Frame(content, bg=self.LIGHT_GRAY, relief='flat', bd=2)
        self.stellenprofil_frame.pack(fill='x', pady=(10, 10))
        
        stellenprofil_header = tk.Frame(self.stellenprofil_frame, bg=self.LIGHT_GRAY)
        stellenprofil_header.pack(fill='x', padx=15, pady=(12, 8))
        
        stellenprofil_label_container = tk.Frame(stellenprofil_header, bg=self.LIGHT_GRAY)
        stellenprofil_label_container.pack(side='left')

        self.stellenprofil_header_label = tk.Label(stellenprofil_label_container, text="📋  Schritt 2: Stellenprofil", bg=self.LIGHT_GRAY, fg=self.DARK_GRAY, font=('Segoe UI', 11, 'bold'))
        self.stellenprofil_header_label.pack(side='left')

        self.stellenprofil_optional_label = tk.Label(stellenprofil_label_container, text=" (Optional)", bg=self.LIGHT_GRAY, fg="#777777", font=('Segoe UI', 10))
        self.stellenprofil_optional_label.pack(side='left')
        
        def select_stellenprofil():
            stellenprofil_path = FilePickerDialog.open_pdf(
                title="Stellenprofil/Stellenbeschreibung auswählen",
                initial_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)), "input", "stellenprofil", "pdf")
            )
            if stellenprofil_path:
                self.stellenprofil_path = stellenprofil_path
                filename = os.path.basename(stellenprofil_path)
                success_bg = "#E8F5E9"
                self.stellenprofil_frame.config(bg=success_bg, bd=2, relief='solid')
                stellenprofil_header.config(bg=success_bg)
                stellenprofil_label_container.config(bg=success_bg)
                self.stellenprofil_header_label.config(bg=success_bg, fg="#2E7D32")
                self.stellenprofil_optional_label.config(text=" ✓", bg=success_bg, fg="#2E7D32")
                self.stellenprofil_status_label.config(text=f"Ausgewählt: {filename}", bg=success_bg, fg="#2E7D32")
                self.stellenprofil_upload_btn.config(text="Ändern", bg=self.SUCCESS_GREEN)
        
        self.stellenprofil_upload_btn = self.create_button(stellenprofil_header, "📤 Stellenprofil wählen", select_stellenprofil, is_primary=False, width=18)
        self.stellenprofil_upload_btn.pack(side='right', padx=10)
        
        self.stellenprofil_status_label = tk.Label(self.stellenprofil_frame, text="Optional: Stellenprofil für maßgeschneiderten CV hochladen.", bg=self.LIGHT_GRAY, fg="#777777", font=('Segoe UI', 9))
        self.stellenprofil_status_label.pack(anchor='w', padx=25, pady=(0, 12))
        
        # Initially disable upload buttons
        self.cv_upload_btn.config(state='disabled', bg='#CCCCCC', cursor='arrow')
        self.stellenprofil_upload_btn.config(state='disabled', bg='#CCCCCC', cursor='arrow')
        
        def update_button_state():
            """Called when DSGVO checkbox changes"""
            if consent_var.get():
                self.cv_upload_btn.config(state='normal', bg=self.ORANGE, cursor='hand2')
                self.stellenprofil_upload_btn.config(state='normal', bg=self.DARK_GRAY, cursor='hand2')
            else:
                self.cv_upload_btn.config(state='disabled', bg='#CCCCCC', cursor='arrow')
                self.stellenprofil_upload_btn.config(state='disabled', bg='#CCCCCC', cursor='arrow')
            update_weiter_button()
        
        cb.config(command=update_button_state)


class ProcessingDialog(ModernDialog):
    """Processing dialog with step-by-step progress visualization"""
    
    def __init__(self, cv_filename, stellenprofil_filename=None):
        """
        Create processing dialog with animated steps
        
        Args:
            cv_filename: Name of CV file being processed
            stellenprofil_filename: Optional name of Stellenprofil file being processed
        """
        super().__init__("CV Generator - Verarbeitung läuft...", width=600, height=750)
        
        self.cv_filename = cv_filename
        self.stellenprofil_filename = stellenprofil_filename
        self.animation_running = True
        
        # Define steps
        self.steps = [
            ("Stellenprofil analysieren", "🔍"),
            ("CV analysieren", "📄"),
            ("Qualitätsprüfung & Validierung", "✅"),
            ("Word-Dokument erstellen", "📝"),
            ("Match-Making Analyse", "🤝"),
            ("CV-Feedback generieren", "💡"),
            ("Dashboard erstellen", "📊")
        ]
        
        self.step_widgets = [] # List of dicts with widget references
        
        # Header
        self.create_header("Verarbeitung läuft", "⚙️", self.ORANGE)
        
        # Content Frame
        content = self.create_content_frame()
        
        # Intro Text
        tk.Label(
            content,
            text="Bitte haben Sie einen Moment Geduld.\nDie KI analysiert und generiert Ihre Dokumente.",
            bg=self.WHITE,
            fg=self.DARK_GRAY,
            font=('Segoe UI', 10),
            justify='center'
        ).pack(pady=(0, 20))
        
        # Steps Container
        steps_frame = tk.Frame(content, bg=self.WHITE)
        steps_frame.pack(fill='both', expand=True, padx=40)
        
        for i, (step_name, icon) in enumerate(self.steps):
            step_row = tk.Frame(steps_frame, bg=self.WHITE)
            step_row.pack(fill='x', pady=8)
            
            # 1. Main Icon (Left)
            icon_lbl = tk.Label(
                step_row, 
                text=icon, 
                bg=self.WHITE, 
                fg="#CCCCCC", # Gray initially
                font=('Segoe UI', 16)
            )
            icon_lbl.pack(side='left', padx=(0, 15))
            
            # 2. Step Name (Middle)
            name_lbl = tk.Label(
                step_row,
                text=step_name,
                bg=self.WHITE,
                fg="#999999", # Gray initially
                font=('Segoe UI', 11),
                anchor='w'
            )
            name_lbl.pack(side='left', fill='x', expand=True)
            
            # 3. Status Icon (Right) - Spinner/Check/Cross
            status_lbl = tk.Label(
                step_row,
                text="○", # Pending circle
                bg=self.WHITE,
                fg="#CCCCCC",
                font=('Segoe UI', 12)
            )
            status_lbl.pack(side='right', padx=5)
            
            self.step_widgets.append({
                "row": step_row,
                "icon": icon_lbl,
                "name": name_lbl,
                "status": status_lbl,
                "state": "pending" # pending, running, completed, error, skipped
            })
            
        # Footer Note
        tk.Label(
            content,
            text="Hinweis: Dieser Vorgang kann je nach Modell 1-3 Minuten dauern.",
            bg=self.WHITE,
            fg="#777777",
            font=('Segoe UI', 9, 'italic')
        ).pack(side='bottom', pady=20)

        # Spinner animation state
        self.spinner_chars = ["◐", "◓", "◑", "◒"]
        self.spinner_idx = 0
        self._animate_spinners()

    def update_step(self, step_index, status):
        """
        Update the status of a specific step.
        status: 'pending', 'running', 'completed', 'error', 'skipped'
        """
        # Ensure this runs on the GUI thread
        self.root.after(0, lambda: self._do_update_step(step_index, status))

    def _do_update_step(self, step_index, status):
        if step_index < 0 or step_index >= len(self.step_widgets):
            return
            
        widget = self.step_widgets[step_index]
        widget["state"] = status
        
        if status == "running":
            widget["icon"].config(fg=self.ORANGE)
            widget["name"].config(fg=self.DARK_GRAY, font=('Segoe UI', 11, 'bold'))
            widget["status"].config(text=self.spinner_chars[0], fg=self.ORANGE)
            
        elif status == "completed":
            widget["icon"].config(fg=self.SUCCESS_GREEN)
            widget["name"].config(fg=self.DARK_GRAY, font=('Segoe UI', 11)) # Back to normal weight but dark
            widget["status"].config(text="✓", fg=self.SUCCESS_GREEN, font=('Segoe UI', 14, 'bold'))
            
        elif status == "error":
            widget["icon"].config(fg=self.ERROR_RED)
            widget["name"].config(fg=self.ERROR_RED)
            widget["status"].config(text="✗", fg=self.ERROR_RED, font=('Segoe UI', 14, 'bold'))
            
        elif status == "skipped":
            widget["icon"].config(fg="#CCCCCC")
            widget["name"].config(fg="#AAAAAA", font=('Segoe UI', 11, 'italic'))
            widget["status"].config(text="-", fg="#CCCCCC", font=('Segoe UI', 14))
            
        elif status == "pending":
            widget["icon"].config(fg="#CCCCCC")
            widget["name"].config(fg="#999999", font=('Segoe UI', 11))
            widget["status"].config(text="○", fg="#CCCCCC")

    def _animate_spinners(self):
        if not self.animation_running:
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass
            return
            
        # Update all running steps
        char = self.spinner_chars[self.spinner_idx]
        self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner_chars)
        
        for widget in self.step_widgets:
            if widget["state"] == "running":
                widget["status"].config(text=char)
        
        self.root.after(150, self._animate_spinners)
        
    def close(self):
        self.animation_running = False

    def show(self):
        """Show dialog (non-blocking for threading)"""
        self.root.mainloop()


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
def show_success(message, title="Erfolg", details=None, file_path=None, dashboard_path=None, match_score=None):
    """Show modern success dialog with optional file open button"""
    dialog = SuccessDialog(title, message, details, file_path, dashboard_path, match_score)
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
    """
    Show welcome dialog with optional stellenprofil selection:
    1. Select CV-PDF (required)
    2. Optional: Click "Stellenprofil hinzufügen" button
    3. Click "Weiter" to proceed
    
    Returns:
        tuple: (cv_path, stellenprofil_path) or None if cancelled
               stellenprofil_path can be None if not selected
    """
    dialog = WelcomeDialog()
    result = dialog.show()  # Returns (cv_path, stellenprofil_path, model_name) or None
    if result is None:
        return None
    # Set environment variable for model, always use dropdown selection
    import os
    selected_model = result[2] if len(result) > 2 and result[2] else "gpt-4o-mini"
    os.environ["MODEL_NAME"] = selected_model
    return result[:2]  # (cv_path, stellenprofil_path)


def show_processing(cv_filename, stellenprofil_filename=None):
    """
    Show processing dialog with animated documents
    Returns dialog instance for manual control (close when done)
    
    Args:
        cv_filename: Name of CV file being processed
        stellenprofil_filename: Optional name of Stellenprofil file being processed
        
    Returns:
        ProcessingDialog instance (call .close() when processing is done)
    """
    dialog = ProcessingDialog(cv_filename, stellenprofil_filename)
    return dialog
