# Cleanup System - Quick Start Guide

Du kannst jetzt das Cleanup-System aufrufen und manuelle Cleanups durchführen.

## ⚡ Quick Start

### 1️⃣ Analyze Mode (SAFE - Keine Änderungen)

**Via Python:**
```bash
python scripts/cleanup/cleanup.py
```

**Oder als Python-Modul:**
```bash
python -m scripts.cleanup.cleanup
```

**Via BAT-Datei (Windows):**
```bash
scripts\cleanup\cleanup.bat
```

**Was passiert:**
- Scannt alle Dateien im Projekt
- Klassifiziert jede Datei (10 Kategorien)
- Wendet Entscheidungsregeln an
- Generiert Bericht (JSON + Markdown)
- **Keine Dateien werden gelöscht!**

### 2️⃣ Apply Mode (GEFÄHRLICH - Löscht Dateien)

**Via Python:**
```bash
python scripts/cleanup/cleanup.py apply
```

**Via BAT-Datei (Windows):**
```bash
scripts\cleanup\cleanup.bat apply
```

**Was passiert:**
- Lädt den letzten Analyze-Bericht
- Zeigt Liste der zu löschenden Dateien
- Fordert Bestätigung (`yes/no`)
- Löscht nur DELETE_SAFE Dateien
- Speichert Log in `deleted_files.log`

---

## 📊 Berichte Ansehen

Nach jedem Lauf findest du Reports hier:
```
scripts/cleanup/runs/YYYY-MM-DD_HH-MM-SS/
├── cleanup_report.json      (Machine-readable)
├── cleanup_report.md        (Human-readable)
└── deleted_files.log        (Bei apply mode)
```

**Bericht in Browser öffnen:**
```bash
scripts/cleanup/runs/2026-01-23_14-30-00/cleanup_report.md
```

---

## 🏷️ File Categories (10 Kategorien)

Das System klassifiziert jede Datei:

| Kategorie | Beispiele | Behandlung |
|-----------|-----------|-----------|
| **SOURCE_CODE** | `.py`, `.ts`, `.js` | Immer KEEP |
| **CONFIG** | `.yaml`, `.json` config | Immer KEEP |
| **PROMPT** | `/prompts/` Dateien | Immer KEEP |
| **INPUT_DATA** | `/input/` Dateien | Immer KEEP |
| **INTERMEDIATE_ARTIFACT** | `/data/intermediate/` | DELETE_SAFE wenn alt |
| **GENERATED_OUTPUT** | `/output/`, htmlcov | Überprüfung nötig |
| **LOG_FILE** | `.log`, `/logs/` | DELETE_SAFE wenn alt |
| **TEMP_FILE** | `.tmp`, `.bak`, `.cache` | DELETE_SAFE wenn alt |
| **EXPERIMENT** | `*_experiment_*`, `*_test_*` | Überprüfung nötig |
| **UNKNOWN** | Keine Regel passt | Überprüfung nötig |

---

## ✅ / ❌ / ⚠️ Entscheidungen

Jede Datei erhält eine von 3 Entscheidungen:

### ✅ DELETE_SAFE (99% Sicherheit)
- **Kategorie:** TEMP_FILE, LOG_FILE oder INTERMEDIATE_ARTIFACT
- **Alter:** >= 14 Tage (konfigurierbar)
- **Verweise:** Keine Referenzen im Code
- **Risiko:** Sehr niedrig

### ❌ KEEP_REQUIRED (100% Sicherheit)
- SOURCE_CODE oder CONFIG
- In required_artifacts Liste
- Im protected_paths (script/, tests/, core/, etc.)
- Kein Risiko

### ⚠️ REVIEW_REQUIRED (Unsicher)
- Unbekannte Kategorie
- Niedrige Confidence
- Generierte Dateien ohne Regenerator
- **Manuell überprüfen bevor löschen!**

---

## 🛡️ Sicherheitsgarantien

✅ **Analyse Mode ist 100% sicher** - Keine Änderungen  
✅ **DELETE_SAFE hat 99% Confidence** - Nur sichere Dateien  
✅ **Bestätigungsabfrage vor Apply** - Keine Überraschungen  
✅ **Immutable Run History** - Jeder Lauf dokumentiert  
✅ **Keine gelöschten Dateien Logs** - Traceability  
✅ **Protected Paths** - Scripts, Tests, Docs sind safe  

---

## 🚀 Nächste Schritte

### Test Laufen
```bash
python run_cleanup.py
```

→ Öffne `cleanup/runs/` Ordner und schaue dir den Report an

### Wenn alles OK ist
```bash
python run_cleanup.py apply
```

→ Tippe `yes` wenn die Zusammenfassung gut aussieht

### Probleme?
- Schau den Bericht in `cleanup_report.md` an
- Suche nach REVIEW_REQUIRED Dateien
- Überprüfe die risk_assessment Erklärungen

---

## ⚙️ Konfiguration

Standard-Einstellungen in `scripts/cleanup/models.py`:

```python
age_threshold_days = 14          # Dateien müssen 14 Tage alt sein
confidence_threshold = 0.95      # Nur 95%+ Sicherheit
protected_paths = [              # Niemals löschen:
    "/cleanup",
    "/scripts", 
    "/tests",
    "/.git",
    "/.venv",
    "/docs",
    "/core"
]
required_artifacts = [           # Wichtige Dateien:
    "requirements.txt",
    "pytest.ini",
    "config.yaml",
    "app.py"
]
max_deletion_size_mb = 100.0     # Höchstens 100MB löschen
```

---

## 📝 Tipps

1. **Immer erst Analyze laufen** - Schau dir den Report an
2. **Apply nur wenn sicher** - Sei vorsichtig mit `apply`
3. **Regelmäßig laufen** - Z.B. monatlich
4. **Archive statt Delete** - Bei REVIEW_REQUIRED

---

## Noch Fragen?


Siehe vollständige Dokumentation:
- [../feature_structured_cleanup/REQUIREMENTS.md](../feature_structured_cleanup/REQUIREMENTS.md)
- [../feature_structured_cleanup/README.md](../feature_structured_cleanup/README.md)
- [../feature_structured_cleanup/CHECKLIST.md](../feature_structured_cleanup/CHECKLIST.md)

Oder schau den generierten Bericht nach dem ersten Lauf an!
