# Testing Guide

## Test Setup

Das Test-Framework verwendet **pytest** mit Coverage-Reporting.

### Installation

```bash
pip install -r requirements-dev.txt
```

### Test-Struktur

```
tests/
├── __init__.py
├── test_validation.py          # JSON-Validierungs-Tests (✅ 15 Tests)
├── fixtures/
│   ├── valid_cv.json           # Vollständiges, valides CV
│   └── invalid_cv_missing_fields.json  # CV mit Strukturfehlern
```

---

## Tests Ausführen

### Alle Tests

```bash
python -m pytest
```

### Spezifische Test-Datei

```bash
python -m pytest tests/test_validation.py
```

### Mit Verbose Output

```bash
python -m pytest -v
```

### Mit Coverage Report

```bash
python -m pytest --cov=scripts --cov-report=html
```

Öffne dann `htmlcov/index.html` im Browser für detaillierte Coverage-Analyse.

---

## Test-Coverage Status

**Aktuell:** 11% Coverage
- `generate_cv.py`: 12% (949 Statements, 112 getestet)
- `modern_dialogs.py`: 16% (300 Statements, 49 getestet)

**Ziel:** 80% Coverage

---

## Implementierte Tests

### 1. TestValidateJsonStructure (6 Tests)
- ✅ Valid CV passes validation
- ✅ Missing required fields detected
- ✅ Hauptrolle structure validation
- ✅ Wrong field types detected
- ✅ Fachwissen structure validation
- ✅ Ausbildung structure validation

### 2. TestLanguageLevelValidation (7 Tests)
- ✅ Valid numeric levels (1-5)
- ✅ Invalid numeric levels rejected
- ✅ Valid text levels accepted
- ✅ Parse level from text
- ✅ Parse level from number
- ✅ Parse level from string number
- ✅ Invalid level returns zero

### 3. TestReferenzprojekteValidation (2 Tests)
- ✅ Required fields validation
- ✅ Tätigkeiten must be array

---

## Nächste Schritte

### Fehlende Test-Coverage

1. **PDF to JSON Tests** (Priority: High)
   - [ ] Mock OpenAI API calls
   - [ ] Test JSON normalization
   - [ ] Test date format normalization
   - [ ] Test 3-category skills structure

2. **CV Generation Tests** (Priority: High)
   - [ ] Test Word document creation
   - [ ] Test table generation
   - [ ] Test styling application
   - [ ] Test missing data highlighting

3. **Dialog Tests** (Priority: Medium)
   - [ ] Test dialog creation
   - [ ] Test button callbacks
   - [ ] Test file picker
   - [ ] Test DSGVO checkboxes

4. **Integration Tests** (Priority: High)
   - [ ] Full pipeline test (PDF → JSON → Word)
   - [ ] Error handling test
   - [ ] File system operations

---

## Test-Best-Practices

### Fixture Usage
```python
@pytest.fixture
def valid_cv_data():
    """Load valid CV fixture"""
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'valid_cv.json')
    with open(fixture_path, 'r', encoding='utf-8') as f:
        return json.load(f)
```

### Parametrized Tests
```python
@pytest.mark.parametrize("level,expected", [
    (1, True),
    (5, True),
    (0, False),
    (6, False)
])
def test_levels(level, expected):
    assert is_valid_level(level) == expected
```

### Mocking OpenAI
```python
from unittest.mock import Mock, patch

@patch('openai.ChatCompletion.create')
def test_pdf_to_json(mock_openai):
    mock_openai.return_value = {...}
    result = pdf_to_json("test.pdf")
    assert result is not None
```

---

## CI/CD Integration

Tests sollten automatisch bei jedem Push laufen:

```yaml
# .github/workflows/ci.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.14'
      - run: pip install -r requirements-dev.txt
      - run: pytest --cov=scripts --cov-report=xml
      - uses: codecov/codecov-action@v3
```

---

## Troubleshooting

### Import Errors
Stelle sicher, dass der Python Path korrekt ist:
```python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```

### Fixture Path Issues
Verwende immer absolute Pfade:
```python
fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'file.json')
```

### Coverage nicht vollständig
Prüfe `pytest.ini` für korrekte `omit` Patterns:
```ini
[coverage:run]
omit = 
    */tests/*
    */__pycache__/*
```
