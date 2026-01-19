# Streamlit Migration Plan

## 🎯 Ziel
Migration der bestehenden Tkinter-basierten Desktop-App zu einer modernen Web-App mit **Streamlit**.
Dies ermöglicht eine einfachere Bedienung, bessere Visualisierung und zukünftige Cloud-Bereitstellung.

## 🗓️ Phase 1: Setup & Basis (Woche 1)
- [✓] **Branch erstellen:** `feature/streamlit-migration` (Erledigt)
- [✓] **Dependencies:** `streamlit` zu `requirements.txt` hinzufügen.
- [✓] **Hello World:** Erstellen einer `app.py`, die "CV Generator" anzeigt.
- [✓] **Layout-Konzept:** Sidebar für Einstellungen (API-Key, Modell), Hauptbereich für Uploads.
- [✓] **Secrets Management:** Implementierung einer Logik, die `st.secrets` (Cloud) und `.env` (Lokal) unterstützt.

## 🎨 Phase 2: UI-Migration (Frontend)
- [✓] **Mode Selection:** Buttons für "Basic", "Advanced" (ersetzt `ModeSelectionDialog`).
  - **Basic**: CV only (single file)
  - **Advanced**: Full analysis with CV + job profile + matching + feedback + offers (1+ CVs)
- [✓] **File Upload:** `st.file_uploader` für CV (PDF) und Stellenprofil (PDF).
- [✓] **Konfiguration:** Eingabefelder für OpenAI API Key (falls nicht in .env).
- [✓] **Validierung:** Prüfen, ob Dateien hochgeladen wurden, bevor der "Start"-Button aktiv wird.

## ⚙️ Phase 3: Backend-Refactoring
*Das ist der wichtigste Teil. Die Logik muss von der GUI entkoppelt werden.*
- [✓] **Entkopplung:** `pipeline.py` so anpassen, dass sie **keine** Tkinter-Dialoge mehr aufruft. (Erledigt via `streamlit_pipeline.py`)
- [✓] **Status-Callbacks:** Statt `ProcessingDialog.update_step()` eine Callback-Funktion nutzen, die `st.progress` oder `st.status` aktualisiert.
- [✓] **Session State:** Nutzen von `st.session_state` um Daten zwischen den Reruns zu speichern (z.B. extrahierte JSONs).

## 📊 Phase 4: Output & Visualisierung
- [✓] **Ergebnisse anzeigen:**
    - Extrahierte Daten als JSON-Baum (`st.json`).
    - Match-Score als Metrik (`st.metric`).
    - Feedback als Text/Markdown (`st.markdown`).
- [✓] **Downloads:** `st.download_button` für:
    - Generiertes Word-Dokument.
    - JSON-Dateien.
    - Dashboard (HTML).
- [✓] **Dashboard-Integration:** Das HTML-Dashboard direkt in der App anzeigen (`st.components.v1.html`).

## 🚀 Phase 5: Testing & Cleanup
- [✓] **Testen:** Durchlauf aller Modi (Basic, Advanced).
- [✓] **Mode Consolidation:** Refaktorierung von 3 Modi (Basic, Analysis, Full) zu 2 Modi (Basic, Advanced).
- [✓] **Batch Offers:** Offer generation für mehrere CVs im Advanced Mode.
- [✓] **File Naming:** Job profile name konsistent durch batch pipeline.
- [ ] **Cleanup:** Entfernen von `scripts/dialogs.py` und Tkinter-Referenzen (wenn komplett migriert).
- [ ] **Dokumentation:** Update der `README.md` mit Start-Anweisungen (`streamlit run app.py`).

## ☁️ Phase 6: Deployment (Streamlit Cloud)
- [ ] **Vorbereitung:** Sicherstellen, dass keine sensiblen Daten im Git-Repo sind (nur via Secrets).
- [ ] **Secrets Konfiguration:** Einrichten der Secrets in der Streamlit Cloud Console (OpenAI Key).
- [ ] **Deployment:** Verbinden des GitHub Repos mit Streamlit Cloud (Private App).
- [ ] **Zugriff:** Einladen von Benutzern (Kollegen) via E-Mail.

## 📝 Notizen
- Streamlit läuft immer von oben nach unten ("Rerun" bei jeder Interaktion). Wir müssen `st.session_state` nutzen, um zu verhindern, dass die KI bei jedem Klick neu läuft.
- Die `pipeline.py` Klasse `CVGeneratorPipeline` muss wahrscheinlich in kleinere, statische Funktionen zerlegt oder angepasst werden.
