# TODO: Multi-Language Support (DE / EN / FR)

## 📋 Feature Overview
Scalable internationalization for the CV Generator & Matchmaking Suite to support German, English, and French across all pipelines (PDF -> JSON -> Word).

## 🚀 To-Do List

### 1. Infrastructure & State Management
- [ ] Create `scripts/translations.json` for centralized UI & Word labels.
- [ ] Implement language selection in Streamlit sidebar (dropdown [DE, EN, FR]).
- [ ] Manage `st.session_state.language` and persist across session.

### 2. Extraction & AI Prompts (Parsing)
- [ ] **Dynamic Prompts:** Refactor `pdf_to_json.py` to select system prompts based on target language.
- [ ] **Schema Expansion:** Update `pdf_to_json_struktur_cv.json` descriptions to instruct the LLM on target language extraction/translation.
- [ ] **Date Parsing:** Extend `normalize_date_format` in `pdf_to_json.py` with French month names (Janvier, Février, etc.).

### 3. Word Generation (Output)
- [ ] **CV Labels:** Refactor `generate_cv.py` to use labels from `translations.json` (e.g., "Berufserfahrung" vs "Work Experience").
- [ ] **Offer Labels:** Refactor `generate_angebot_word.py` (e.g., "Einsatzkonditionen" vs "Engagement Terms").
- [ ] **Layout Adjustments:** Check table widths for longer French terms.

### 4. UI Localization
- [ ] **Dashboard:** Localize HTML templates and legends in `visualize_results.py`.
- [ ] **App Info:** Translate the "Application Information" dialog in `app.py`.

## ⏱ Effort Estimate
Estimated total: **26 - 36 Hours**
- Foundation/UI: 4-6h
- Word Generation Logic: 12-16h
- AI Prompting: 6-8h
- Layout/Date Testing: 4-6h

## 🛠 Design Pattern
Use a simple dictionary-based lookup for translations:
```json
{
  "de": { "work_experience": "Berufserfahrung" },
  "en": { "work_experience": "Work Experience" },
  "fr": { "work_experience": "Expérience professionnelle" }
}
```
