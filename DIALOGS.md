# Modern Dialogs Documentation

## Overview
The CV Generator now features modern, corporate-styled dialogs that replace the old tkinter messageboxes. All dialogs use the corporate color scheme from `styles.json` and professional icons for enhanced user experience.

## Corporate Styling

### Colors
- **Orange (#FF7900)**: Primary brand color for success states and primary actions
- **Gray (#444444)**: Secondary text and cancel buttons
- **Red (#DC3545)**: Error states
- **Yellow (#FFC107)**: Warning states
- **Green (#28A745)**: Success confirmation states

### Typography
- **Font**: Segoe UI (modern Windows system font)
- **Sizes**: 14pt for headers, 11pt for content, 10pt for buttons

### Icons
All dialogs include professional Unicode icons:
- ✅ Success
- ❌ Error
- ⚠️ Warning
- ℹ️ Info
- ❓ Question
- 📄 File/PDF
- 📋 JSON
- 📝 Word

## Dialog Types

### 1. Success Dialog
**Purpose**: Confirm successful completion of operations

```python
from scripts.modern_dialogs import show_success, ModernDialog

show_success(
    message="Der Lebenslauf wurde erfolgreich generiert.",
    title="Erfolg",
    details=(
        f"{ModernDialog.ICON_FILE} PDF Input: example.pdf\n"
        f"{ModernDialog.ICON_WORD} Output: output.docx"
    )
)
```

**Features**:
- Green header with checkmark icon
- Main message in large, readable text
- Optional details section in light gray box
- Orange "OK" button

### 2. Error Dialog
**Purpose**: Display critical errors that prevent operations

```python
from scripts.modern_dialogs import show_error

show_error(
    message="Die JSON-Struktur weist kritische Fehler auf.",
    title="Validierungsfehler",
    details="• Feld 'Vorname' fehlt\n• Feld 'Nachname' fehlt"
)
```

**Features**:
- Red header with X icon
- Bold error message
- Scrollable details box for stack traces
- Gray "Schließen" button

### 3. Warning Dialog
**Purpose**: Display warnings with Yes/No options

```python
from scripts.modern_dialogs import show_warning

result = show_warning(
    message="Die JSON-Datei weist Strukturprobleme auf.",
    title="Warnung",
    details="⚠️ Kritische Fehler:\n• Problem 1\n• Problem 2"
)

if result:
    # User clicked "Ja, fortfahren"
    proceed()
else:
    # User clicked "Abbrechen"
    cancel()
```

**Features**:
- Yellow header with warning icon
- Scrollable details section
- Two buttons: "Ja, fortfahren" (orange) and "Abbrechen" (gray)
- Returns True/False

### 4. Confirmation Dialog
**Purpose**: Ask yes/no questions

```python
from scripts.modern_dialogs import ask_yes_no

result = ask_yes_no(
    message="Möchten Sie das Dokument jetzt öffnen?",
    title="Bestätigung",
    icon_type="success"  # or "question", "info"
)

if result:
    open_document()
```

**Features**:
- Configurable header color based on icon_type
- Simple message display
- "Ja" (orange) and "Nein" (gray) buttons
- Returns True/False

### 5. File Picker Dialogs
**Purpose**: Select PDF or JSON files

```python
from scripts.modern_dialogs import select_pdf_file, select_json_file

# PDF picker
pdf_path = select_pdf_file("Wählen Sie eine PDF-Datei")
if pdf_path:
    process_pdf(pdf_path)

# JSON picker
json_path = select_json_file("Wählen Sie eine JSON-Datei")
if json_path:
    process_json(json_path)
```

**Features**:
- Automatically sets correct initial directory (input/pdf or input/json)
- File type filters
- Returns file path or None if cancelled

## Usage in Pipeline

### run_pipeline.py
All dialogs in the main pipeline have been upgraded:

1. **PDF Selection**: Modern file picker
2. **Validation Errors**: Structured error dialog with details
3. **Success**: Professional success dialog with file paths
4. **File Opening**: Confirmation dialog with success styling

### scripts/generate_cv.py
JSON validation warnings now use the modern warning dialog:

```python
if critical or info:
    proceed = show_warning(
        "Die JSON-Datei weist Strukturprobleme auf:",
        title="JSON-Validierung",
        details=formatted_issues
    )
    if not proceed:
        return None
```

## Testing
Run the demo script to see all dialog types:

```bash
python demo_dialogs.py
```

This will show:
1. Success dialog with file details
2. Error dialog with validation errors
3. Warning dialog with Yes/No options
4. Confirmation dialog for file opening
5. File picker (optional - can be cancelled)

## Customization

### Adding New Dialog Types
Extend the `ModernDialog` base class:

```python
from scripts.modern_dialogs import ModernDialog

class CustomDialog(ModernDialog):
    def __init__(self, title, message):
        super().__init__(title, width=500, height=250)
        
        # Create header
        self.create_header(title, self.ICON_INFO, self.ORANGE)
        
        # Create content
        content = self.create_content_frame()
        # ... add your content ...
        
        # Create buttons
        btn_frame = tk.Frame(self.root, bg=self.WHITE)
        btn_frame.pack(side='bottom', pady=20)
        self.create_button(btn_frame, "OK", self.close)
    
    def close(self):
        self.result = True
        self.root.destroy()
```

### Modifying Colors
Edit color constants in `scripts/modern_dialogs.py`:

```python
class ModernDialog:
    ORANGE = "#FF7900"      # Change to your brand color
    DARK_GRAY = "#444444"   # Change secondary color
    # ...
```

## Benefits

1. **Consistent Branding**: All dialogs match corporate identity
2. **Better UX**: Clear hierarchy, professional appearance
3. **Enhanced Readability**: Icons, proper spacing, readable fonts
4. **Professional Messages**: Well-formatted, structured information
5. **Modern Appearance**: Clean design, hover effects, centered layouts
6. **Maintainability**: Centralized in one module, easy to update

## Migration Notes

Old tkinter code has been replaced:
- ❌ `messagebox.showerror()` → ✅ `show_error()`
- ❌ `messagebox.askyesno()` → ✅ `ask_yes_no()` or `show_warning()`
- ❌ `filedialog.askopenfilename()` → ✅ `select_pdf_file()` / `select_json_file()`

All functionality is preserved while appearance is greatly enhanced.
