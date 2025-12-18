# Processing Dialog - Implementation Summary

## Neue Features

### 1. ProcessingDialog Klasse
Eine neue Dialog-Klasse in `scripts/dialogs.py` für die Anzeige während der LLM-Verarbeitung:

**Features:**
- Animierte Fortschrittsanzeige (rotierende Punkte)
- Zeigt Dokument-Icons (📄 für CV, 📋 für Angebot)
- Automatisches Layout: 
  - **Nur CV**: Zentrierte Einzelanzeige
  - **CV + Angebot**: Nebeneinander (Side-by-Side)
- Dateinamen werden angezeigt (automatisch gekürzt wenn >25 Zeichen)
- Corporate Design (Orange #FF7900, Grau #444444)

### 2. Threading-Integration
Der Dialog läuft in einem separaten Thread, damit die LLM-Verarbeitung nicht blockiert wird.

**Pipeline-Flow:**
```
Welcome Dialog (Dateiauswahl)
    ↓
Processing Dialog START (in Thread)
    ↓
LLM Extraktion (PDF → JSON)
    ↓
Processing Dialog CLOSE
    ↓
Validierung + Word-Generierung
    ↓
Success Dialog (mit "Open" Button)
```

### 3. Angebot-Support
Die Pipeline unterstützt jetzt optional ein zweites Dokument (Stellenangebot):
- Welcome Dialog erlaubt optionale Angebot-Auswahl
- Processing Dialog zeigt beide Dokumente an
- `run_pipeline(cv_path, angebot_path=None)` akzeptiert beide Parameter

## Code-Änderungen

### scripts/dialogs.py
- **Neue Klasse:** `ProcessingDialog(ModernDialog)`
- **Neue Funktion:** `show_processing(cv_filename, angebot_filename=None)`
- **Animation:** `_animate_progress()` mit rotierenden Punkten

### scripts/pipeline.py
- **Import:** `threading` für Dialog-Threading
- **Import:** `show_processing` aus dialogs
- **Geändert:** `run_pipeline()` akzeptiert `angebot_path`
- **Geändert:** `main()` verarbeitet Tuple vom Welcome Dialog
- **Threading:** Dialog läuft in separatem Thread während LLM-Verarbeitung
- **Cleanup:** Dialog wird in `finally` Block geschlossen

## Verwendung

### Manueller Test
```bash
python test_processing_dialog.py
```

### In der Pipeline
```python
# Automatisch verwendet beim Starten:
python run_pipeline.py

# Oder mit Kommandozeilen-Argumenten:
python scripts/pipeline.py cv.pdf
python scripts/pipeline.py cv.pdf angebot.pdf
```

## Visuelle Beispiele

### Nur CV
```
┌─────────────────────────────────────┐
│   🤖  KI-Extraktion läuft           │
├─────────────────────────────────────┤
│                                     │
│         📄                          │
│      CV-Dokument                    │
│   Max_Mustermann_CV.pdf             │
│                                     │
│   Verarbeitung läuft...             │
│                                     │
└─────────────────────────────────────┘
```

### CV + Angebot
```
┌─────────────────────────────────────┐
│   🤖  KI-Extraktion läuft           │
├─────────────────────────────────────┤
│                                     │
│    📄              📋               │
│ CV-Dokument   Stellenangebot        │
│  Max_CV.pdf   Senior_Dev.pdf        │
│                                     │
│   Verarbeitung läuft...             │
│                                     │
└─────────────────────────────────────┘
```

## Technische Details

### Threading-Sicherheit
- Dialog läuft in Daemon-Thread
- `dialog_closed` Event für Synchronisation
- 0.5s Verzögerung für Dialog-Initialisierung
- `finally` Block garantiert Dialog-Schließung

### Animation
- 400ms Intervall für Punkt-Animation
- Zyklus: `"   "` → `".  "` → `".. "` → `"..."` → wiederholen
- Stoppt automatisch bei `animation_running = False`

### Layout
- **Breite:** 550px (konsistent mit anderen Dialogs)
- **Höhe:** 400px
- **Font:** Segoe UI (Windows Standard)
- **Icons:** Unicode Emojis (keine externen Assets)

## TODO / Future Enhancements
- [ ] Implementiere tatsächliche Angebot-Verarbeitung in `run_pipeline()`
- [ ] Füge Fortschritts-Prozentsatz hinzu (wenn API das unterstützt)
- [ ] Überlege: Rotierende Icon-Animation statt statische Icons?
- [ ] Logging der Verarbeitungszeit für Performance-Analyse
