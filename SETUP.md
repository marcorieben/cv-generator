# Setup Guide - Unified Pipeline

## 🚀 Quick Setup (First Time Only)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Get OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create new API key
3. Copy the key (starts with `sk-proj-...`)

### Step 3: Create `.env` file
```bash
# Copy the example file
copy .env.example .env

# Edit .env and add your actual API key
OPENAI_API_KEY=sk-proj-YOUR-ACTUAL-KEY-HERE
MODEL_NAME=gpt-4o-mini
```

**IMPORTANT:** Never commit `.env` to Git! (Already in .gitignore)

---

## 📖 Usage

### Option 1: Double-click Batch File (Easiest)
- Double-click `run_pipeline.bat`
- Select PDF file in dialog
- Done! Word document is generated

### Option 2: Command Line
```bash
# With file picker dialog
python run_pipeline.py

# Direct with file path
python run_pipeline.py "input/pdf/Marco_Rieben.pdf"
```

---

## 📋 What Happens?

```
1. PDF → Extract text
2. OpenAI API → Structure as JSON
3. Validate JSON structure
4. Generate Word document
5. Open Word file
```

**Output Files:**
- JSON: `input/json/filename_timestamp.json`
- Word: `output/word/Vorname_Nachname_CV_timestamp.docx`

---

## 🔧 Troubleshooting

**Error: "OpenAI API Key not found"**
→ Create `.env` file with your API key (see Step 3)

**Error: "No module named 'openai'"**
→ Run `pip install -r requirements.txt`

**Error: "File not found"**
→ Make sure PDF is in `input/pdf/` or provide full path

**JSON validation errors**
→ OpenAI couldn't extract all fields. JSON is saved, manually fix it and use `run_cv.bat` with the JSON file

---

## 💰 API Costs

**GPT-4o-mini** (default):
- ~$0.002 per CV (0.2 cents)
- Very affordable for regular use

**Upgrade to GPT-4o** (better quality):
- Change `MODEL_NAME=gpt-4o` in `.env`
- ~$0.03 per CV (3 cents)

---

## 📁 File Structure

```
cv_generator/
├── run_pipeline.py         # Main unified pipeline
├── run_pipeline.bat        # Windows launcher
├── run_cv.bat              # Original JSON→Word only
├── requirements.txt        # Python dependencies
├── .env                    # Your API keys (DO NOT COMMIT!)
├── .env.example            # Template for .env
├── scripts/
│   ├── pdf_to_json.py      # NEW: PDF→JSON converter
│   ├── generate_cv.py      # Existing: JSON→Word generator
│   └── styles.json         # Styling configuration
├── input/
│   ├── pdf/                # Put your PDF files here
│   └── json/               # Generated JSON + manual JSON
└── output/
    └── word/               # Generated Word documents
```

---

## 🎯 Next Steps

1. **Test with one PDF**: Put a CV PDF in `input/pdf/` and run `run_pipeline.bat`
2. **Check output**: Review generated JSON and Word document
3. **Adjust if needed**: If extraction quality is low, upgrade to GPT-4o in `.env`

Happy CV generating! 🎉
