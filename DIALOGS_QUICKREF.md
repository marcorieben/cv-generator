# Dialog System - Quick Reference

## 📁 Wo finde ich was?

```
cv_generator/
│
├── 📄 DIALOGS_REFERENCE.md          ← DU BIST HIER - Komplette Referenz
├── 📄 DIALOGS.md                    ← Alte Doku (kann gelöscht werden)
├── 📄 DIALOG_UPDATE_SUMMARY.md      ← Migration Guide (veraltet)
├── 📄 DIALOG_VISUAL_REFERENCE.md    ← Visual Mockups (veraltet)
│
├── scripts/
│   └── 📄 dialogs.py                ← HAUPTDATEI - Alle Dialog-Klassen
│       ├── ModernDialog (Base)      
│       ├── WelcomeDialog            → Pipeline-Start
│       ├── ProcessingDialog         → Warte-Animation (NEU!)
│       ├── SuccessDialog            → Erfolg
│       ├── ErrorDialog              → Fehler
│       ├── WarningDialog            → Warnung
│       ├── ConfirmDialog            → Ja/Nein
│       └── FilePickerDialog         → Dateiauswahl
│
├── 📄 demo_dialogs.py               ← Demo aller Dialogs
├── 📄 test_processing_dialog.py     ← Test für ProcessingDialog
│
├── tests/
│   └── 📄 test_dialogs.py           ← Unit-Tests
│
└── run_pipeline.py                  ← Verwendet Dialogs
```

---

## 🎯 Schnellzugriff

### "Ich will Dialog X anpassen"

| Dialog | Zeile in dialogs.py | Verwendet in | Testen mit |
|--------|---------------------|--------------|------------|
| **WelcomeDialog** | 424-747 | `run_pipeline.py` (Start) | `demo_dialogs.py` |
| **ProcessingDialog** | 749-928 | `run_pipeline.py` (während LLM) | `test_processing_dialog.py` |
| **SuccessDialog** | 133-199 | `run_pipeline.py` (Ende) | `demo_dialogs.py` |
| **ErrorDialog** | 201-257 | Überall bei Errors | `demo_dialogs.py` |
| **WarningDialog** | 259-371 | Bei Validierung | `demo_dialogs.py` |
| **ConfirmDialog** | 373-422 | Bei Ja/Nein Fragen | `demo_dialogs.py` |
| **FilePickerDialog** | 936-983 | In WelcomeDialog | `demo_dialogs.py` |

### "Ich will..."

#### → Text ändern
```python
# Beispiel: SuccessDialog Button-Text
# scripts/dialogs.py, Zeile ~188
self.create_button(btn_container, "OK", close)
# Ändere zu:
self.create_button(btn_container, "Schließen", close)
```

#### → Farbe ändern
```python
# scripts/dialogs.py, Zeile 17-23 (Class-Variablen)
ORANGE = "#FF7900"      # ← Hier ändern
DARK_GRAY = "#444444"
```

#### → Größe ändern
```python
# In __init__ der Dialog-Klasse:
super().__init__("Titel", width=600, height=450)
```

#### → Animation schneller/langsamer
```python
# ProcessingDialog, Zeile ~925
self.root.after(100, self._animate_spinners)  # ms ändern
```

#### → Neuen Dialog erstellen
```python
# In scripts/dialogs.py:
class MyDialog(ModernDialog):
    def __init__(self):
        super().__init__("Titel", width=550, height=300)
        self.create_header("Header", "🎯", self.ORANGE)
        content = self.create_content_frame()
        # Füge Content hinzu...
```

---

## 🧹 Cleanup-Empfehlung

**Diese Dateien können gelöscht werden (veraltet):**
- `DIALOGS.md` → Ersetzt durch `DIALOGS_REFERENCE.md`
- `DIALOG_UPDATE_SUMMARY.md` → Migration abgeschlossen
- `DIALOG_VISUAL_REFERENCE.md` → Nicht mehr aktuell

**Diese Dateien behalten:**
- ✅ `DIALOGS_REFERENCE.md` (diese Datei)
- ✅ `DIALOGS_QUICKREF.md` (diese Übersicht)
- ✅ `scripts/dialogs.py`
- ✅ `demo_dialogs.py`
- ✅ `test_processing_dialog.py`
- ✅ `tests/test_dialogs.py`

---

## 📞 Häufige Aufgaben

### Task: "DSGVO-Text anpassen"
1. Öffne `scripts/dialogs.py`
2. Gehe zu Zeile **537-548** (WelcomeDialog)
3. Ändere Label-Text im Checkbox-Bereich

### Task: "Spinner im ProcessingDialog ändern"
1. Öffne `scripts/dialogs.py`
2. Gehe zu Zeile **766**
3. Ändere `self.spinner_frames = ["◐", "◓", "◑", "◒"]`
4. Teste mit: `python test_processing_dialog.py`

### Task: "Success Button umbenennen"
1. Öffne `scripts/dialogs.py`
2. Gehe zu Zeile **188**
3. Ändere Button-Text
4. Teste mit: `python demo_dialogs.py`

### Task: "Neues Icon hinzufügen"
1. Öffne `scripts/dialogs.py`
2. Gehe zu Zeile **26-33** (Icon-Definitionen)
3. Füge hinzu: `ICON_MEIN_ICON = "🎯"`
4. Verwende mit: `ModernDialog.ICON_MEIN_ICON`

---

**Vollständige Dokumentation**: Siehe [`DIALOGS_REFERENCE.md`](DIALOGS_REFERENCE.md)
