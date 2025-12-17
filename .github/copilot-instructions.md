# CV Generator Project Instructions

## Project Overview
A German-language CV generator with two pipelines: (1) **Unified Pipeline** converts PDF CVs → structured JSON (via OpenAI) → formatted Word documents, or (2) **Direct Pipeline** converts existing JSON → Word. Uses `python-docx` for Word generation and OpenAI's GPT models for intelligent PDF extraction.

## Architecture & Data Flow

### Unified Pipeline (Primary): `run_pipeline.py`
```
PDF → extract_text_from_pdf() → OpenAI API (with schema) → normalize_json_structure() 
  → validate_json_structure() → generate_cv() → Word Document
```

### Direct Pipeline: `run_cv.bat` / `scripts/generate_cv.py`
```
JSON → validate_json_structure() → generate_cv() → Word Document
```

**Key Files:**
- `run_pipeline.py`: Orchestrates PDF→JSON→Word with validation & user dialogs
- `scripts/pdf_to_json.py`: PDF extraction and OpenAI API interaction with structured prompting
- `scripts/generate_cv.py`: JSON→Word conversion with complex table layouts (1597 lines)
- `scripts/pdf_to_json_structure.json`: JSON schema contract enforced in OpenAI prompt
- `scripts/styles.json`: Visual styling (fonts, colors, spacing) for all document elements

## Critical Patterns

### 1. Missing Data Handling
**Pattern:** Use global `MISSING_DATA_MARKER = "! bitte prüfen !"` (with spaces) for incomplete data. OpenAI may return variants (`"! fehlt – bitte prüfen!"`, different dashes). The `normalize_json_structure()` in `pdf_to_json.py` corrects structural issues, while `highlight_missing_data_in_document()` in `generate_cv.py` searches all marker variants, normalizes to standard form, and highlights in yellow.

### 2. Schema-Driven OpenAI Extraction
**Pattern:** `pdf_to_json()` embeds the entire `pdf_to_json_structure.json` schema in the system prompt with detailed rules (e.g., fixed 3-category skills structure, date normalization, 5-bullet limit for projects). Set `response_format={"type": "json_object"}` and `temperature=0` for consistency. Post-process with `normalize_json_structure()` to fix common OpenAI structural deviations (nested objects, incorrect field names).

### 3. Date Format Normalization
**Pattern:** All dates must be `MM/YYYY` format (or `MM/YYYY - MM/YYYY` for ranges). Use `normalize_date_format()` which handles variations: `"2020"` → `"01/2020"`, `"Jan 2020"` → `"01/2020"`, recognizes "heute/today/present" as special keywords. Applied during JSON normalization to `Aus_und_Weiterbildung`, `Trainings_und_Zertifizierungen`, `Ausgewählte_Referenzprojekte`.

### 4. Fixed 3-Category Skills Structure
**Pattern:** `Fachwissen_und_Schwerpunkte` must have exactly 3 categories in order: (1) "Projektmethodik", (2) "Tech Stack", (3) "Weitere Fähigkeiten / Skills". OpenAI may return arbitrary categories—`normalize_json_structure()` intelligently maps skills using keyword matching (e.g., `["scrum", "agile", "hermes"]` → Projektmethodik). Fallback: insert `["! fehlt – bitte prüfen!"]` if category empty.

### 5. Borderless Table Construction
**Pattern:** All CV sections use tables for layout control (column widths in Inches). Remove borders via XML manipulation:
```python
def remove_cell_borders(cell):
    tcPr = cell._element.get_or_add_tcPr()
    tcBorders = parse_xml(r'<w:tcBorders ...><w:top w:val="none"/><w:left w:val="none"/>...</w:tcBorders>')
    # ... insert into tcPr
```
Apply to every cell after population. See examples: `add_basic_info_table()`, `add_referenzprojekte_table()`.

### 6. Language Level Mapping
**Pattern:** Languages displayed with star ratings (★). Level mapping: `5="Muttersprache ★★★★★"`, `4="Verhandlungssicher ★★★★☆"`, `3="Sehr gute Kenntnisse ★★★☆☆"`, `2="Gute Kenntnisse ★★☆☆☆"`, `1="Grundkenntnisse ★☆☆☆☆"`. Sort descending by level before display. Use 6-column table layout. Functions: `parse_level()`, `is_valid_level()` in `generate_cv.py`.

### 7. Validation Two-Tier System
**Pattern:** `validate_json_structure()` returns `(critical, info)` tuple. **Critical errors** block generation (missing required fields, wrong types, invalid structures). **Info warnings** allow generation but print console warnings (e.g., "Hauptrolle.Beschreibung sollte 5-10 Wörter haben"). Always call validation before `generate_cv()`.

## Development Workflows

### Run Unified Pipeline
```bash
python run_pipeline.py                    # File picker dialog
python run_pipeline.py path/to/file.pdf   # Direct path
# Or double-click: run_pipeline.bat
```
**Output:** JSON saved to `input/json/{Vorname}_{Nachname}_{timestamp}.json`, Word to `output/word/{Vorname}_{Nachname}_CV_{timestamp}.docx`

### Run JSON→Word Only
```bash
python scripts/generate_cv.py  # File picker for JSON in input/json/
# Or double-click: run_cv.bat
```

### Environment Setup (First-Time)
1. Install deps: `pip install -r requirements.txt` (python-docx, openai, PyPDF2, python-dotenv)
2. Create `.env` file with `OPENAI_API_KEY=sk-proj-...` and `MODEL_NAME=gpt-4o-mini`

### Debugging
- **Check console output:** Pipeline prints step-by-step progress with emoji indicators (📄, ✅, ❌)
- **Validation failures:** JSON saved even on failure—manually fix and rerun with `run_cv.bat`
- **Missing data markers:** Appear yellow-highlighted in Word output

## Common Modifications

### Add New CV Section
1. Create `add_[section]_table(doc, data)` function following borderless table pattern
2. Call from `generate_cv()` main flow (around line 1500) after existing sections
3. Update `validate_json_structure()` to check new field structure

### Change Visual Styling
Edit `scripts/styles.json`: `heading1` (orange, 16pt), `heading2` (gray, 11pt), `text` (black, 11pt), `bullet` (orange square, hanging indent). Color format: RGB arrays `[255, 121, 0]` → converted to `RGBColor(*color)` in code.

### Adjust OpenAI Extraction Rules
1. Edit `scripts/pdf_to_json_structure.json` to modify schema or field descriptions
2. Update system prompt in `pdf_to_json()` for additional extraction rules
3. Test with sample PDFs, check console output for API errors

## Schema Contract (Key Fields)
- **Required top-level:** `Vorname`, `Nachname`, `Hauptrolle` (object with `Titel`/`Beschreibung`), `Nationalität`, `Ausbildung`, `Kurzprofil`, `Fachwissen_und_Schwerpunkte` (3-item array), `Aus_und_Weiterbildung`, `Trainings_und_Zertifizierungen`, `Sprachen`, `Ausgewählte_Referenzprojekte`
- **Education vs Training:** `Aus_und_Weiterbildung` = academic degrees only (Bachelor, Master, CAS, DAS). `Trainings_und_Zertifizierungen` = courses, workshops, certifications
- **Projects:** Max 5 bullets per `Tätigkeiten` array. Role max 8 words. Display: customer heading, time/role row, activities bullets, tech/methodology rows
- **Kurzprofil:** 50-100 words, 3rd person using first name (e.g., "Marco verfügt über..."), factual—no invented skills

## Path Handling
**Pattern:** Use `abs_path(relative_path)` helper in `generate_cv.py` to resolve paths relative to `scripts/` directory. Example: `abs_path("styles.json")` → `c:\...\cv_generator\scripts\styles.json`. Critical for logo paths, style loading.