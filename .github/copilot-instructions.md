# CV Generator Project Instructions

## Project Overview
This is a Python-based CV (resume) generator that converts structured JSON data into formatted Microsoft Word documents using the `python-docx` library. The system processes German-language CV data with predefined sections and styling.

## Architecture
- **Input**: JSON files in `input/json/` containing CV data with German field names
- **Processing**: `scripts/generate_cv.py` reads JSON, applies styling from `scripts/styles.json`, and generates Word documents
- **Output**: Timestamped `.docx` files in `output/word/`

## Key Components
- `scripts/generate_cv.py`: Main generator script with document creation functions
- `scripts/styles.json`: Font, color, and spacing definitions for consistent formatting
- `input/json/*.json`: CV data files with standardized structure
- `templates/cv_template_orange.docx`: Reference template (currently unused in code)

## Data Structure
JSON files must contain these top-level fields:
- `Vorname`, `Nachname`: Personal details
- `Hauptrolle`, `Nationalität`, `Hauptausbildung`: Basic info
- `Kurzprofil`: Summary text
- `Fachwissen_und_Schwerpunkte`: Array of skill categories with `Kategorie` and `Inhalt` arrays
- `Aus_und_Weiterbildung`: Education array with `Zeitraum`, `Institution`, `Ausbildung_Titel`
- `Trainings_und_Zertifizierungen`: Certifications array with `Zeitraum`, `Institution`, `Titel`
- `Sprachen`: Languages array with `Sprache` and `Level` (sorted by level descending: Muttersprache ★★★★★, Verhandlungssicher ★★★★☆, Sehr gute Kenntnisse ★★★☆☆, Gute Kenntnisse ★★☆☆☆, Grundkenntnisse ★☆☆☆☆; displayed in 6-column table)
- `Referenzprojekte`: Array of project objects with `Zeitraum`, `Rolle`, `Kunde`, `Tätigkeiten` array (displayed as sections with customer heading, time/role table, and activities list)

## Development Workflow
1. Run `python scripts/generate_cv.py` or double-click `run_cv.bat`
2. An initial dialog appears explaining the process and offering options:
   - "JSON Datei auswählen" to select a JSON file from `input/json/`
   - "Abbrechen" to exit
3. Select a JSON file using the file dialog
4. The CV is generated and a success dialog appears with:
   - Confirmation message with output directory and filename
   - "Datei öffnen" button to open the generated Word document
5. Check generated `.docx` in `output/word/`

## Coding Patterns
- **Styling**: All formatting defined in `styles.json` with keys: `heading1`, `heading2`, `text`, `bullet`
- **Table Creation**: Use borderless tables with custom column widths; remove borders via XML manipulation
- **Path Handling**: Use `abs_path()` helper for relative paths from `scripts/` directory
- **Document Structure**: Headings use `add_heading_1()`/`add_heading_2()`, content uses `add_normal_text()` or `add_bullet_item()`
- **Color Format**: RGB tuples in styles.json, converted to `RGBColor(*color)` in code

## Dependencies
- `python-docx` for Word document manipulation
- `tkinter` for file selection dialog (standard library)
- Standard library: `json`, `os`, `datetime`

## Common Tasks
- **Add new CV section**: Create `add_[section]_table()` function, call in `generate_cv()` after existing sections
- **Modify styling**: Update `styles.json` values, restart script
- **Process different JSON**: Change hardcoded path in `generate_cv()` call at script end
- **Debug output**: Check console for file save confirmation message

## File Organization
- `scripts/`: Core logic and configuration
- `input/json/`: Source data files
- `output/word/`: Generated documents
- `templates/`: Reference materials
- `01_Anfoderung/`: Project diagrams and specifications