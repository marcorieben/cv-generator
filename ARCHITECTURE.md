# CV Generator Architecture

## System Overview

The CV Generator provides two distinct pipelines for creating professional CV documents:

1. **Unified Pipeline**: Converts PDF CVs to Word documents via intelligent OpenAI extraction
2. **Direct Pipeline**: Converts pre-existing JSON files directly to Word documents

Both pipelines converge at the validation and document generation stages, ensuring consistent output quality.

---

## Flow Diagram

```mermaid
graph TB
    subgraph "Entry Points"
        A1[run_pipeline.bat]
        A2[run_cv.bat]
        A3["python run_pipeline.py"]
        A4["python scripts/generate_cv.py"]
    end

    subgraph "Unified Pipeline - PDF to Word"
        B1[PDF File<br/>input/pdf/*.pdf]
        B2[select_pdf_file<br/>Dialog]
        B3[extract_text_from_pdf<br/>PyPDF2]
        B4[OpenAI API<br/>gpt-4o-mini]
        B5[pdf_to_json_structure.json<br/>Schema]
        B6[normalize_json_structure<br/>Fix OpenAI deviations]
        B7[normalize_date_format<br/>MM/YYYY conversion]
        B8[Fix 3-category skills<br/>Keyword mapping]
        B9[Save JSON<br/>input/json/]
    end

    subgraph "Validation Layer"
        C1[validate_json_structure]
        C2{Critical<br/>Errors?}
        C3[Info Warnings<br/>Print to console]
        C4[❌ Stop Pipeline<br/>Save JSON for manual fix]
    end

    subgraph "JSON to Word Pipeline"
        D1[JSON File<br/>input/json/*.json]
        D2[show_initial_dialog<br/>File picker]
        D3[Load styles.json<br/>Colors, fonts, spacing]
        D4[generate_cv<br/>Main generator]
    end

    subgraph "Document Generation"
        E1[add_basic_info_table<br/>Role, nationality, education]
        E2[add_heading_1/2<br/>Orange/gray styling]
        E3[add_fachwissen_table<br/>3 fixed categories]
        E4[add_education_table<br/>Degrees only]
        E5[add_trainings_table<br/>Courses, certifications]
        E6[add_sprachen_table<br/>★ ratings, 6 columns]
        E7[add_referenzprojekte_table<br/>Customer, bullets, tech]
        E8[remove_cell_borders<br/>XML manipulation]
        E9[highlight_missing_data<br/>Yellow: ! bitte prüfen !]
    end

    subgraph "Output"
        F1[Word Document<br/>output/word/*.docx]
        F2[show_success_dialog<br/>Open file option]
    end

    %% Unified Pipeline Flow
    A1 --> A3
    A3 --> B2
    B1 --> B2
    B2 --> B3
    B3 --> B4
    B5 -.Schema embedded in prompt.-> B4
    B4 --> B6
    B6 --> B7
    B7 --> B8
    B8 --> B9
    B9 --> C1

    %% Direct Pipeline Flow
    A2 --> A4
    A4 --> D2
    D1 --> D2
    D2 --> C1

    %% Validation Flow
    C1 --> C2
    C2 -->|Yes| C4
    C2 -->|No| C3
    C3 --> D3

    %% Generation Flow
    D3 --> D4
    D4 --> E1
    E1 --> E2
    E2 --> E3
    E3 --> E4
    E4 --> E5
    E5 --> E6
    E6 --> E7
    E7 --> E8
    E8 --> E9
    E9 --> F1
    F1 --> F2

    style A1 fill:#e1f5ff
    style A2 fill:#e1f5ff
    style B4 fill:#fff3cd
    style B5 fill:#fff3cd
    style C2 fill:#f8d7da
    style C4 fill:#f8d7da
    style F1 fill:#d4edda
    style F2 fill:#d4edda
```

---

## Pipeline Details

### 🔵 Unified Pipeline (PDF → JSON → Word)

**Entry**: `run_pipeline.bat` or `python run_pipeline.py [pdf_path]`

**Process**:
1. **PDF Extraction**: PyPDF2 extracts raw text from all pages
2. **OpenAI API Call**: Sends extracted text + JSON schema to GPT model
3. **Normalization**: Corrects common OpenAI structural deviations:
   - Fixes nested `Expertise` wrapper → flat `Fachwissen_und_Schwerpunkte`
   - Renames `BulletList` → `Inhalt`
   - Maps arbitrary skill categories → 3 fixed categories (Projektmethodik, Tech Stack, Weitere Fähigkeiten)
   - Converts all dates to `MM/YYYY` format
4. **JSON Saved**: `input/json/{Vorname}_{Nachname}_{timestamp}.json`
5. **Continues to validation** → Word generation

**Key Files**:
- `run_pipeline.py`: Orchestration logic
- `scripts/pdf_to_json.py`: Extraction + OpenAI integration
- `scripts/pdf_to_json_structure.json`: Schema contract

### 🔵 Direct Pipeline (JSON → Word)

**Entry**: `run_cv.bat` or `python scripts/generate_cv.py`

**Process**:
1. **File Selection**: Dialog to pick JSON from `input/json/`
2. **Continues to validation** → Word generation

**Use Cases**:
- Manual JSON creation
- Editing failed extractions
- Batch processing pre-existing JSONs

---

## Validation Layer

**Function**: `validate_json_structure(data)` returns `(critical, info)`

### Critical Errors (Blocks Generation)
- Missing required fields
- Wrong data types (e.g., array instead of object)
- Invalid structure (e.g., missing `Titel`/`Beschreibung` in `Hauptrolle`)

### Info Warnings (Allows Generation)
- Suboptimal field lengths (e.g., role description not 5-10 words)
- Invalid language levels
- Missing optional fields

**On Failure**: JSON is saved for manual correction, user notified to fix and rerun with `run_cv.bat`

---

## Document Generation

### Key Patterns

1. **Borderless Tables**: All sections use tables for layout control
   - Column widths in Inches (e.g., `Inches(1.5)`, `Inches(5.5)`)
   - Borders removed via XML manipulation (`remove_cell_borders()`)

2. **Styling System**: `styles.json` defines:
   - `heading1`: Orange, 16pt, bold (section headers)
   - `heading2`: Gray, 11pt, bold (subsection headers)
   - `text`: Black, 11pt (body content)
   - `bullet`: Orange square (■), hanging indent

3. **Missing Data Handling**:
   - Marker variants normalized to `"! bitte prüfen !"`
   - All instances highlighted yellow in final document

4. **Language Stars**: Levels 1-5 mapped to text + star ratings
   - Sorted descending by level before display

### Generation Sequence

1. Basic Info Table (role, nationality, education)
2. Kurzprofil (profile summary)
3. Fachwissen (3 fixed skill categories)
4. Education (academic degrees only)
5. Trainings (courses, certifications)
6. Languages (with star ratings)
7. Reference Projects (customer, activities, tech, methodology)

---

## File Organization

```
cv_generator/
├── run_pipeline.py          # Unified pipeline orchestrator
├── run_pipeline.bat         # Windows launcher (unified)
├── run_cv.bat               # Windows launcher (direct)
├── scripts/
│   ├── pdf_to_json.py       # PDF extraction + OpenAI
│   ├── generate_cv.py       # JSON → Word converter
│   ├── pdf_to_json_structure.json  # Schema contract
│   └── styles.json          # Visual styling
├── input/
│   ├── pdf/                 # Source PDFs
│   └── json/                # Extracted/manual JSONs
└── output/
    └── word/                # Generated CVs
```

---

## External Dependencies

- **OpenAI API**: GPT-4o-mini for intelligent PDF extraction
  - Requires `.env` file with `OPENAI_API_KEY`
  - Schema-driven prompting ensures structured output
  - Temperature=0 for consistency

- **python-docx**: Word document manipulation
  - Direct XML access for border removal
  - Fine-grained paragraph/run formatting

- **PyPDF2**: PDF text extraction
  - Page-by-page processing
  - Fallback error handling

---

## Design Decisions

### Why Two Pipelines?
- **Unified**: Ideal for quick CV updates from candidate PDFs
- **Direct**: Allows manual quality control and custom JSON creation

### Why OpenAI API?
- Handles messy PDF layouts intelligently
- Understands semantic meaning (e.g., "Education" vs "Training")
- Adapts to varying CV formats without brittle regex parsing

### Why Fixed 3-Category Skills?
- Consistent presentation across all CVs
- Client requirement for standardized format
- Keyword mapping handles OpenAI's category variations

### Why Save JSON Intermediate?
- Debugging: inspect what OpenAI extracted
- Quality control: manual fixes before Word generation
- Reusability: generate Word multiple times from same JSON
- Archival: structured data for future processing

---

## See Also

- [SETUP.md](SETUP.md) - Installation and first-time setup
- [.github/copilot-instructions.md](.github/copilot-instructions.md) - Development patterns and conventions
