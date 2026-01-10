# CV Generator

**Multi-language AI-powered CV processing and job matching pipeline**

Generate professional CVs from PDF uploads using OpenAI GPT-4o-mini, with automated job profile matching and quality feedback.

---

## Features

- 📄 **PDF → Word**: Extract CV data from PDF and generate formatted Word documents
- 🎯 **Job Matching**: AI-powered candidate-to-job profile matching (Muss/Soll criteria)
- 📊 **Analytics Dashboard**: HTML dashboard with match scores and criteria breakdown
- 🌍 **Multi-language**: Full support for German, English, and French
- ✅ **Quality Checks**: Automated CV quality feedback and validation
- 📝 **Offer Generation**: Automatic offer document creation (Word format)

---

## Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key

### Installation

```bash
# Clone repository
git clone https://github.com/marcorieben/cv-generator.git
cd cv-generator

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

### Usage

**Option 1: Streamlit Web UI** (Recommended)
```bash
streamlit run app.py
```
Navigate to http://localhost:8501 and upload your CV PDF.

**Option 2: CLI Pipeline**
```bash
python run_pipeline.py path/to/cv.pdf [path/to/job_profile.pdf]
```

**Option 3: Programmatic**
```python
from scripts.pdf_to_json import pdf_to_json
from scripts.generate_cv import generate_cv

# Extract CV data
cv_data = pdf_to_json("cv.pdf", target_language="en")

# Generate Word document
word_path = generate_cv("cv_data.json", language="en")
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Streamlit Frontend                     │
│                  (app.py / run_pipeline.py)             │
└────────────────┬────────────────────────────────────────┘
                 │
     ┌───────────▼────────────┐
     │   PDF Upload Handler   │
     └───────────┬────────────┘
                 │
     ┌───────────▼────────────┐
     │  PDF → JSON Extractor  │
     │  (OpenAI GPT-4o-mini)  │
     └───────────┬────────────┘
                 │
     ┌───────────▼────────────────────────────────────┐
     │         Parallel Processing                     │
     ├─────────────────────────────────────────────────┤
     │  • CV Generator (JSON → Word)                   │
     │  • Job Matcher (AI-powered criteria check)      │
     │  • Quality Feedback (CV validation)             │
     │  • Offer Generator (Word offer document)        │
     └───────────┬─────────────────────────────────────┘
                 │
     ┌───────────▼────────────┐
     │  Dashboard Generator   │
     │  (HTML + Chart.js)     │
     └────────────────────────┘
```

**Technologies:**
- **Backend**: Python 3.10+
- **UI**: Streamlit (web) / Tkinter (CLI dialogs)
- **AI**: OpenAI API (GPT-4o-mini for extraction & matching)
- **Document Processing**: `pypdf`, `python-docx`
- **Storage**: Local file system (`output/` directory)

---

## Cost & Performance

**OpenAI API Usage** (per full pipeline):
- **Cost**: ~CHF 0.01 per CV (~€0.008)
- **Latency**: 2-3 minutes average processing time
- **Volume Pricing**:
  - 100 CVs/month: ~CHF 1
  - 1,000 CVs/month: ~CHF 10
  - 10,000 CVs/month: ~CHF 100

**Performance Breakdown**:
- PDF Extraction: 30-60s
- Job Matching: 20-40s
- Quality Feedback: 15-25s
- Word Generation: 5-10s
- Dashboard: 2-5s

---

## Documentation

### User Guides
- **Getting Started**: [Installation & Setup](#quick-start)
- **API Reference**: See `docs/API.md` (coming soon)
- **Configuration**: See `docs/CONFIGURATION.md` (coming soon)

### Technical Documentation
- **[Tech Debt Report](docs/TECH_DEBT.md)** - Current architecture analysis, cost breakdown, and improvement roadmap
- **[Serverless Architecture](docs/SERVERLESS_ARCHITECTURE.md)** - AWS Lambda migration plan (40-60% cost reduction)
- **[Migration Runbook](docs/MIGRATION_RUNBOOK.md)** - Step-by-step serverless deployment guide

### Development
- **Changelog**: See [scripts/CHANGELOG.md](scripts/CHANGELOG.md)
- **Testing**: Run `pytest` (45 tests, 36% coverage)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md) (coming soon)

---

## Project Structure

```
cv_generator/
├── app.py                      # Streamlit web UI entry point
├── run_pipeline.py             # CLI pipeline entry point
├── scripts/
│   ├── pdf_to_json.py          # PDF extraction (OpenAI)
│   ├── generate_cv.py          # Word document generation
│   ├── generate_matchmaking.py # Job matching logic
│   ├── generate_angebot_word.py # Offer document generation
│   ├── visualize_results.py    # HTML dashboard
│   ├── pipeline.py             # CLI pipeline orchestration
│   ├── streamlit_pipeline.py   # Streamlit backend
│   ├── styles.json             # Word template styling
│   ├── translations.json       # Multi-language support (DE/EN/FR)
│   └── schemas/                # JSON schemas for validation
├── templates/                  # Word template assets (logos, etc.)
├── output/                     # Generated files (git-ignored)
├── tests/                      # Pytest test suite
│   ├── fixtures/               # Test data & mocks
│   └── hooks/                  # Pre-commit hooks
├── docs/                       # Technical documentation
│   ├── TECH_DEBT.md
│   ├── SERVERLESS_ARCHITECTURE.md
│   └── MIGRATION_RUNBOOK.md
└── requirements.txt            # Python dependencies
```

---

## Roadmap

### Current (Q1 2026)
- [x] Multi-language support (DE/EN/FR)
- [x] Serverless architecture design
- [ ] AWS Lambda migration (see [Migration Runbook](docs/MIGRATION_RUNBOOK.md))
- [ ] Caching layer (Redis) for 30-40% cost reduction

### Future (Q2-Q3 2026)
- [ ] Next.js frontend (replace Streamlit)
- [ ] Auth0 / AWS Cognito authentication
- [ ] Multi-region deployment (EU + US)
- [ ] A/B testing for prompt optimization
- [ ] Real-time WebSocket progress updates
- [ ] REST API for programmatic access

See [TECH_DEBT.md](docs/TECH_DEBT.md) for full action items.

---

## Configuration

### Environment Variables

```bash
# .env file
OPENAI_API_KEY=sk-...                    # Required: OpenAI API key
MODEL_NAME=gpt-4o-mini                   # Optional: AI model (default: gpt-4o-mini)
CV_GENERATOR_MODE=full                   # Optional: 'full' or 'cv_only'
```

### Customization

**Styling** (`scripts/styles.json`):
- Fonts, colors, spacing for Word documents
- Table layouts and header configurations
- Company logo and branding

**Translations** (`scripts/translations.json`):
- UI labels (DE/EN/FR)
- Dashboard text
- Offer document templates

---

## Troubleshooting

### Common Issues

**1. OpenAI API Timeout**
```
Error: Request timed out after 120s
```
**Solution**: Increase timeout in `scripts/pdf_to_json.py` or retry with smaller PDF.

**2. Word Document Formatting Issues**
```
Warning: python-docx compatibility issue
```
**Solution**: Ensure `python-docx>=1.2.0` and check template in `templates/`.

**3. Missing Dependencies**
```
ModuleNotFoundError: No module named 'openai'
```
**Solution**: Reinstall dependencies: `pip install -r requirements.txt`

**4. Pre-commit Hook Failures**
```
UnicodeEncodeError in hooks
```
**Solution**: Fixed in latest commit (Windows encoding compatibility).

---

## License

This project is proprietary software. All rights reserved.

---

## Support

For questions or issues:
1. Check [TECH_DEBT.md](docs/TECH_DEBT.md) for known issues
2. Review [Migration Runbook](docs/MIGRATION_RUNBOOK.md) for deployment help
3. Open an issue on GitHub (if public repo)

---

## Acknowledgments

- **OpenAI** for GPT-4o-mini API
- **Streamlit** for rapid prototyping framework
- **python-docx** for Word document generation

Built with ❤️ by [Marco Rieben](https://github.com/marcorieben)

---

**Last Updated**: 2026-01-10 | **Branch**: `feature/serverless-migration`
