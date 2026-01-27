# Feature Requirement: Storage Abstraction for Railway Deployment
**Feature ID:** F003  
**Status:** Planning → Implementation  
**Date:** 2026-01-27  
**Owner:** MR  

---

## 1. EXECUTIVE SUMMARY

### Problem Statement

Die CV-Generator-App ist **nicht deploybar** auf Railway (oder anderen Cloud-Plattformen):
- **File System Dependency:** Alle 5 Generatoren schreiben in lokale `input/`, `output/` Ordner
- **Multi-User Conflicts:** Shared folders führen zu Race Conditions (User A überschreibt User B)
- **Ephemeral Filesystem:** Railway-Container haben kein persistentes Filesystem → Dateien verschwinden nach Request
- **Path Hardcoding:** ~50-70 Stellen mit `../output/word/cv_*.docx` über gesamte Codebase

### Value Proposition

**Railway-ready in 4 Tagen statt 4 Wochen:**
- ✅ **Run Isolation:** Jeder Pipeline-Run bekommt isolierten Workspace (keine Konflikte)
- ✅ **Zero Configuration:** Railway deployment ohne Volume Mounts oder persistenten Storage
- ✅ **Business Traceability:** Run-IDs enthalten Jobprofile + Candidate Name → durchsuchbar
- ✅ **Supabase-Ready:** Migrationsweg zu persistent storage dokumentiert (Post-Railway)
- ✅ **Clean Architecture:** Generatoren arbeiten bytes-basiert (keine Pfade mehr)

### Approach: Simplified vs. Original

| Aspect | Original Plan | Simplified Approach |
|--------|--------------|---------------------|
| **Interface** | StorageProvider (abstract) | RunWorkspace (concrete class) |
| **Code Size** | 500 Zeilen | 50 Zeilen |
| **Implementations** | 4 (Local, Memory, S3, Azure) | 1 (tempfile-basiert) |
| **Timeline** | 36h / 4 Wochen | 15h / 4 Tage |
| **Cloud Support** | Day 1 | Post-Railway (Supabase) |

**Decision:** Simplified Approach gewählt (siehe [Requirements Analysis](../README.md#ziele))

---

## 2. FEATURE GOAL & SCOPE

### Core Concept: RunWorkspace (tempfile-based)

```python
from pathlib import Path
import tempfile
import zipfile
from datetime import datetime

class RunWorkspace:
    """
    Ephemeral workspace for a single pipeline run.
    Lives in tempfile, dies with the container.
    """
    
    def __init__(self, run_id: str):
        self.run_id = run_id

## 2. FEATURE GOAL & SCOPE

### Primary Goals (Railway Deployment)

1. **Run Isolation:** Jeder Pipeline-Run erhält unique Workspace (kein Shared State)
2. **Railway-Ready:** Funktioniert auf ephemeral Container-Filesystems ohne Volume Mounts
3. **All 5 Generators:** CV, Offer, Dashboard (primary) + Matchmaking, Feedback (reports) migriert
4. **Existing UI Compatible:** Dashboard mit individuellen Download-Buttons bleibt unverändert
5. **Structured Downloads:** ZIP-Download als zusätzliche Option (enthält alle Dateien)
6. **Bytes-Based Pipeline:** Generatoren arbeiten ohne File I/O (nur Memory)

### Secondary Goals (Post-Railway)

6. **Supabase-Ready:** RunWorkspace austauschbar gegen SupabaseWorkspace (Future)
7. **Document History:** Database-Tracking für persistent storage (Future)

### Explicit Non-Goals

- ❌ Cloud Storage (S3, Azure) in Phase 1 → Post-Railway mit Supabase
- ❌ Backwards Compatibility → Clean Break, atomic migration
- ❌ Feature Flags → Dead Code wird gelöscht
- ❌ Long-term File Retention → Ephemeral by design (für jetzt)
- ❌ **Changing Dashboard UI** → Existing layout with individual download buttons preserved

---

## 3. ARCHITECTURE

### 3.1 RunWorkspace Class (Core Component)

**File:** `core/storage/workspace.py`

```python
from pathlib import Path
import tempfile
import zipfile
from datetime import datetime

class RunWorkspace:
    """
    Lightweight workspace for single pipeline run.
    Railway-ready (tempfile), Supabase-swappable later.
    """
    
    def __init__(self, run_id: str):
        self.run_id = run_id
        self._tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tempdir.name) / run_id
        self.root.mkdir(parents=True, exist_ok=True)
        
        # Two subdirectories: that's it
        self.primary_outputs = self.root / "primary_outputs"
        self.artifacts = self.root / "artifacts"
        self.primary_outputs.mkdir(exist_ok=True)
        self.artifacts.mkdir(exist_ok=True)
    
    def save_primary(self, filename: str, content: bytes) -> Path:
        """Save user-facing output (CV, Offer, Dashboard, Match, Feedback)"""
        path = self.primary_outputs / filename
        path.write_bytes(content)
        return path
    
    def save_artifact(self, filename: str, content: bytes) -> Path:
        """Save technical artifact (JSON, logs)"""
        path = self.artifacts / filename
        path.write_bytes(content)
        return path
    
    def get_primary(self, filename: str) -> bytes:
        """Retrieve individual primary file (for dashboard download buttons)"""
        path = self.primary_outputs / filename
        return path.read_bytes()
    
    def get_artifact(self, filename: str) -> bytes:
        """Retrieve individual artifact file"""
        path = self.artifacts / filename
        return path.read_bytes()
    
    def bundle_as_zip(self) -> bytes:
        """Create ZIP of entire workspace for download"""
        zip_path = self.root.parent / f"{self.run_id}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in self.root.rglob('*'):
                if file.is_file():
                    arcname = file.relative_to(self.root)
                    zf.write(file, arcname)
        return zip_path.read_bytes()
    
    def cleanup(self):
        """Cleanup tempdir (automatic on Railway container exit)"""
        self._tempdir.cleanup()
```

**Key Design Decisions:**
- ✅ Concrete Class (kein Interface) - YAGNI für MVP
- ✅ tempfile.TemporaryDirectory - Python-native, auto-cleanup
- ✅ 2 Ordner-Struktur - Primary (User) + Artifacts (Technical)
- ✅ Individual File Access - `get_primary()` für Dashboard-Buttons
- ✅ ZIP Bundle - `bundle_as_zip()` für kompletten Download
- ✅ ~60 Zeilen Code - 90% weniger als original StorageProvider Pattern

---

### 3.2 Run-ID Generation (Business-Meaningful)

**File:** `core/utils/run_id.py`

**Convention:**
```python
# Format: jobprofile_candidate_timestamp
run_id = f"{jobprofile_slug}_{candidate_slug}_{timestamp}"

# Beispiel: Senior-Java-Developer_Marco-Rieben_20260127-142305
```

**Komponenten (existierende Pipeline-Variablen):**
- `jobprofile_slug`: Normalisiert aus Jobprofile-Titel
  - Quelle: `jobprofile_data['Stellenbezeichnung']` oder `jobprofile_data['title']`
  - Beispiel: "Senior Java Developer" → "Senior-Java-Developer"
- `candidate_slug`: Normalisiert aus CV-Daten
  - Quelle: `cv_data['Vorname']` + `cv_data['Nachname']`
  - Beispiel: "Marco Rieben" → "Marco-Rieben"
- `timestamp`: `YYYYMMdd-HHMMSS` (Bindestrich für Lesbarkeit)

### Implementation

```python
import re
from datetime import datetime

def generate_run_id(jobprofile_title: str, firstname: str, lastname: str) -> str:
    """Generate business-meaningful run ID for workspace isolation"""
    
    def slugify(text: str, max_length: int = 50) -> str:
        """Normalize text: remove special chars, spaces to hyphens"""
        text = re.sub(r'[^a-zA-Z0-9\s-]', '', text)
        text = re.sub(r'\s+', '-', text.strip())
        return text[:max_length]
    
    jobprofile_slug = slugify(jobprofile_title)
    candidate_slug = f"{slugify(firstname)}-{slugify(lastname)}"
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    
    return f"{jobprofile_slug}_{candidate_slug}_{timestamp}"
```

**Vorteile:**
- ✅ Human-readable & searchable
- ✅ Traceability: Welche Dokumente für welche Stelle
- ✅ Database-friendly: Kann in Spalten extrahiert werden
- ✅ Nutzt existierende Pipeline-Daten

---

## 4. MIGRATION APPROACH

### 4.1 Generator Refactoring Pattern

**Applied identically to all 5 generators:** CV, Offer, Dashboard, Matchmaking, Feedback

**Before (path-based):**
```python
def generate_cv(json_path: str, output_dir: str = None, language: str = "de") -> str:
    """Generate CV from JSON file, save to output_dir, return file path"""
    
    # Load JSON from file
    with open(json_path, 'r', encoding='utf-8') as f:
        cv_data = json.load(f)
    
    # Generate document
    doc = Document()
    # ... add content ...
    
    # Save to file
    output_path = os.path.join(output_dir, f"cv_{firstname}_{lastname}.docx")
    doc.save(output_path)
    return output_path  # Returns path
```

**After (bytes-based):**
```python
def generate_cv_bytes(cv_data: dict, language: str = "de") -> bytes:
    """Generate CV from dict, return bytes (no file I/O)"""
    
    # cv_data already in memory (no file loading)
    
    # Generate document
    doc = Document()
    # ... add content ...
    
    # Return bytes
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()  # Returns bytes
```

### 4.2 Streamlit Pipeline Integration

```python
# Streamlit entry point
def run_cv_pipeline(cv_bytes, job_bytes=None):
    # Generate business-meaningful run ID
    run_id = generate_run_id(
        jobprofile_data['Stellenbezeichnung'],
        cv_data['Vorname'],
        cv_data['Nachname']
    )  # → "Senior-Java-Developer_Marco-Rieben_20260127-142305"
    
    workspace = RunWorkspace(run_id)
    
    # Extract (returns dict, no file I/O)
    cv_data = extract_cv(cv_bytes, job_profile_dict=None)
    workspace.save_artifact("cv_extracted.json", json.dumps(cv_data).encode())
    
    # Generate all 5 documents (returns bytes)
    cv_bytes = generate_cv_bytes(cv_data)
    offer_bytes = generate_offer_bytes(offer_data)
    dashboard_bytes = generate_dashboard_bytes(dashboard_data)
    match_bytes = generate_matchmaking_bytes(match_data)
    feedback_bytes = generate_feedback_bytes(feedback_data)
    
    # Save to workspace (3 primary + 2 reports)
    workspace.save_primary("CV_Marco_Rieben.docx", cv_bytes)
    workspace.save_primary("Offer_Marco_Rieben.docx", offer_bytes)
    workspace.save_primary("Dashboard_Marco_Rieben.html", dashboard_bytes)
    workspace.save_artifact("Matchmaking_Report.docx", match_bytes)  # Report, not primary
    workspace.save_artifact("Feedback_Report.docx", feedback_bytes)  # Report, not primary
    
    # Existing Dashboard UI: Individual download buttons (UNCHANGED)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "📄 Download CV",
            workspace.get_primary("CV_Marco_Rieben.docx"),
            "CV_Marco_Rieben.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    with col2:
        st.download_button(
            "📄 Download Offer",
            workspace.get_primary("Offer_Marco_Rieben.docx"),
            "Offer_Marco_Rieben.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    with col3:
        st.download_button(
            "📊 Download Dashboard",
            workspace.get_primary("Dashboard_Marco_Rieben.html"),
            "Dashboard_Marco_Rieben.html",
            "text/html"
        )
    
    # Additional: ZIP download with all files
    st.download_button(
        "📦 Alle Dokumente herunterladen",
        workspace.bundle_as_zip(),
        f"{run_id}.zip",
        "application/zip"
    )
```

**ZIP-Struktur:**
```
Senior-Java-Developer_Marco-Rieben_20260127-142305.zip
├── primary_outputs/          # User-facing documents
│   ├── CV_Marco_Rieben.docx
│   ├── Offer_Marco_Rieben.docx
│   └── Dashboard_Marco_Rieben.html
└── artifacts/                # Technical outputs & reports
    ├── Matchmaking_Report.docx
    ├── Feedback_Report.docx
    ├── cv_extracted.json
    ├── matching_result.json
    └── feedback.json
```

---

## 5. IMPLEMENTATION TIMELINE

### Day 1: Core + 2 Primary Generators (5h)
- [ ] **1h:** Implement `RunWorkspace` class (`core/storage/workspace.py`)
- [ ] **1h:** Implement `generate_run_id()` function (`core/utils/run_id.py`)
- [ ] **1h:** Refactor CV generator → `generate_cv_bytes()` (primary)
- [ ] **1h:** Refactor Offer generator → `generate_offer_bytes()` (primary)
- [ ] **1h:** Update CV + Offer Streamlit pipelines, write unit tests

### Day 2: Dashboard + Reports (5h)
- [ ] **1.5h:** Refactor Dashboard generator → `generate_dashboard_bytes()` (primary)
- [ ] **1.5h:** Refactor Matchmaking generator → `generate_matchmaking_bytes()` (report/artifact)
- [ ] **1h:** Refactor Feedback generator → `generate_feedback_bytes()` (report/artifact)
- [ ] **1h:** Update remaining 3 Streamlit pipelines

### Day 3: Testing & Deployment (3h)
- [ ] **1h:** Local testing: Alle 5 Generatoren → ZIP download funktioniert
- [ ] **1h:** Railway deployment: Push, configure environment
- [ ] **1h:** Smoke test: Jeder Dokumenttyp auf Railway generieren

### Day 4: Cleanup & Merge (2h)
- [ ] **30min:** Delete old `input/`, `output/` folder code
- [ ] **1h:** Update docs: README.md, development_guidelines.md
- [ ] **30min:** Merge to `development` branch

**Total:** 15 hours over 4 days

---

## 6. DEFINITION OF DONE
        cv_data = json.load(f)
    
    # ... build document ...
    doc = Document()
    # ... add content ...
    
    # Save to hardcoded path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    firstname = cv_data.get('Vorname', 'Unknown')
    lastname = cv_data.get('Nachname', 'Unknown')
    output_dir = output_dir or abs_path("../output/word/")
    os.makedirs(output_dir, exist_ok=True)
    out_docx = os.path.join(output_dir, f"cv_{firstname}_{lastname}_{timestamp}.docx")
    
    doc.save(out_docx)
    return out_docx  # Returns file path
```

### After (refactored for RunWorkspace)

```python
def generate_cv_bytes(cv_data: dict, language: str = "de") -> tuple[bytes, str]:
    """Generate CV from dict, return bytes + filename (no file I/O)"""
    
    # No file loading - data comes as dict
    # ... build document ...
    doc = Document()
    # ... add content ...
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    firstname = cv_data.get('Vorname', 'Unknown')
    lastname = cv_data.get('Nachname', 'Unknown')
    filename = f"cv_{firstname}_{lastname}_{timestamp}.docx"
    
    # Return bytes instead of saving
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    return buffer.read(), filename
```

### Integration in Streamlit Pipeline

```python
# OLD (file-based)
json_path = save_json_to_file(cv_data)
word_path = generate_cv(json_path, output_dir="output/word/")
with open(word_path, 'rb') as f:
    st.download_button("Download CV", f)

# NEW (byte-based + workspace)
workspace = RunWorkspace(run_id)
cv_bytes, filename = generate_cv_bytes(cv_data)
workspace.save_primary(filename, cv_bytes)

# Download entire workspace as ZIP
st.download_button("Download Results", workspace.bundle_as_zip(), 
                   f"{run_id}.zip", "application/zip")
```

**Key Changes:**
- Input: `json_path` → `cv_data` (dict)
- Output: file path → bytes + filename
- Orchestration: Streamlit calls `workspace.save_primary()`
- Download: Single ZIP instead of individual files

---

## 6. DEFINITION OF DONE

### Functional Requirements
- [ ] `RunWorkspace` class implemented in `core/storage/workspace.py`
- [ ] `generate_run_id()` function implemented in `core/utils/run_id.py`
- [ ] All 5 generators refactored to `*_bytes()` functions:
  - [ ] `generate_cv_bytes()` (primary)
  - [ ] `generate_offer_bytes()` (primary)
  - [ ] `generate_dashboard_bytes()` (primary)
  - [ ] `generate_matchmaking_bytes()` (report/artifact)
  - [ ] `generate_feedback_bytes()` (report/artifact)
- [ ] All 5 Streamlit pipelines updated to use `RunWorkspace`
- [ ] ZIP download with `primary_outputs/` + `artifacts/` structure

### Testing Requirements
- [ ] Unit tests: `RunWorkspace` (save, bundle, cleanup)
- [ ] Integration tests: Alle 5 Generatoren produzieren valide bytes
- [ ] Local test: ZIP download enthält 3 primary + 2 reports (5 total)
- [ ] Railway smoke test: Each generator works on Railway

### Deployment Requirements
- [ ] Railway deployment erfolgreich (no file-not-found errors)
- [ ] ZIP download funktioniert im Railway-deployed UI
- [ ] No hardcoded `input/`, `output/` paths in codebase

### Documentation Requirements
- [ ] Feature README.md updated (Status: "Integrated")
- [ ] FEATURE_INDEX.md updated
- [ ] Development guidelines: RunWorkspace pattern documented (optional)

### Cleanup Requirements
- [ ] Old `input/`, `output/` folder references deleted
- [ ] Old file-based generator signatures deleted (no backwards compat)
- [ ] Unused imports removed (os.path, file operations)

---

## 7. FUTURE: SUPABASE MIGRATION PATH

### Why Document This Now?

RunWorkspace ist bewusst **Supabase-kompatibel** designed, damit spätere Migration minimal invasiv ist:
- ✅ Gleiche Methoden-Signatur (`save_primary`, `save_artifact`, `bundle_as_zip`)
- ✅ Byte-basierte Generatoren (unabhängig vom Storage-Backend)
- ✅ Run-ID als Namespace (direkt als Supabase Storage Prefix verwendbar)

### ❌ "Let's make it cloud-agnostic now"
**Problem:** Premature abstraction leads to over-engineering  
**Solution:** Solve Railway deployment. Cloud later.

### ❌ "Let's support both old and new code paths"
**Problem:** Feature flags double maintenance burden  
**Solution:** Delete old code. Deploy new code. Done.

### ❌ "Let's design the perfect storage abstraction"
**Problem:** Perfect is the enemy of shipped  
**Solution:** `RunWorkspace` with 4 methods. Ship it.

---

### SupabaseWorkspace Class (Future Implementation)

```python
class SupabaseWorkspace:
    """
    Supabase Storage implementation.
    Same interface as RunWorkspace, different backend.
    """
    
    def __init__(self, run_id: str, supabase_client, bucket: str = "user-documents"):
        self.run_id = run_id
        self.supabase = supabase_client
        self.bucket = bucket
    
    def save_primary(self, filename: str, content: bytes) -> str:
        """Upload to Supabase Storage, return public URL"""
        path = f"{self.run_id}/primary_outputs/{filename}"
        self.supabase.storage.from_(self.bucket).upload(path, content)
        return self.supabase.storage.from_(self.bucket).get_public_url(path)
    
    def save_artifact(self, filename: str, content: bytes) -> str:
        """Upload artifacts to Supabase"""
        path = f"{self.run_id}/artifacts/{filename}"
        self.supabase.storage.from_(self.bucket).upload(path, content)
        return path
    
    def bundle_as_zip(self) -> bytes:
        """Download all files from Supabase, bundle as ZIP"""
        files = self.supabase.storage.from_(self.bucket).list(self.run_id)
        
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zf:
            for file in files:
                content = self.supabase.storage.from_(self.bucket).download(file['name'])
                zf.writestr(file['name'], content)
        return buffer.getvalue()
```

### Database Schema (Persistent Storage)

```sql
CREATE TABLE generated_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id TEXT NOT NULL,        -- "Senior-Java-Developer_Marco-Rieben_20260127-142305"
    user_id TEXT NOT NULL,
    jobprofile_title TEXT,       -- Extracted for search
    candidate_name TEXT,         -- Extracted for search
    document_type TEXT NOT NULL, -- 'cv', 'offer', 'dashboard', etc.
    storage_path TEXT NOT NULL,  -- Supabase Storage path
    filename TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB,
    INDEX idx_user_documents (user_id, created_at DESC),
    INDEX idx_candidate_search (candidate_name, created_at DESC),
    INDEX idx_jobprofile_search (jobprofile_title, created_at DESC)
);
```

### Migration Impact (Generator Code: ZERO)

```python
# Current (RunWorkspace - tempfile)
workspace = RunWorkspace(run_id)
cv_bytes = generate_cv_bytes(cv_data)
workspace.save_primary("cv.docx", cv_bytes)

# Future (SupabaseWorkspace - cloud)
workspace = SupabaseWorkspace(run_id, supabase_client)
cv_bytes = generate_cv_bytes(cv_data)  # SAME!
workspace.save_primary("cv.docx", cv_bytes)  # SAME!
```

**Generatoren müssen NICHT geändert werden** - nur Workspace-Instanz austauschen!
