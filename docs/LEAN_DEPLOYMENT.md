# Lean Deployment Strategy - CV Generator

**Ziel**: Minimale Kosten (~$5-10/Monat) bei maximaler Flexibilität für Testing (5 User, 100 CVs/Monat)

---

## 🎯 ANFORDERUNGEN

1. **Kosten niedrig halten** → Start mit $5/Monat
2. **Multi-Model Support** → OpenAI, Claude Haiku, PyResParser, etc.
3. **Skalierbar** → Von 100 → 10,000 CVs ohne Rewrite

---

## 📊 KOSTEN-VERGLEICH: 100 CVs/MONAT

| Option | Setup | Monatliche Kosten | Skalierung | Empfehlung |
|--------|-------|-------------------|------------|------------|
| **Railway.app** | 1h | **$5** + API | ✅ Auto | ⭐ Best für Start |
| **Render.com** | 1h | **$7** + API | ✅ Auto | ⭐ Alternative |
| **Fly.io** | 2h | **$0** + API | ✅ Manual | 💰 Cheapest |
| **AWS Lambda** | 2 Wochen | **$3** + API | ✅✅ Best | 🚀 Later |
| **Lokal (VM)** | 0h | **$30-50** | ❌ Nein | ❌ Teuer |

### API Kosten (pro 100 CVs):

```
GPT-4o-mini:          $1.00  ✅ (Current)
Claude 3.5 Haiku:     $3.00
PyResParser (FREE):   $0.00  💰 (Lower quality)
GPT-4o:               $15.00
Claude 3.5 Sonnet:    $18.00
```

**Total Cost (Railway + GPT-4o-mini)**: **$6/Monat** für 100 CVs ✅

---

## 🚀 OPTION 1: RAILWAY.APP (EMPFOHLEN)

### Warum Railway?
- ✅ **$5/Monat** Flat Fee (500 Stunden Runtime)
- ✅ **Auto-Scaling** (bei Traffic-Spikes)
- ✅ **GitHub Integration** (Push → Auto-Deploy)
- ✅ **Persistent Storage** (Outputs bleiben)
- ✅ **PostgreSQL Free Tier** (für Metadata)
- ✅ **Zero Config** (erkennt Streamlit automatisch)

### Setup (10 Minuten):

#### 1. Vorbereitung (Projekt anpassen)

**Erstelle `railway.json`:**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.enableCORS false",
    "healthcheckPath": "/_stcore/health",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

**Erstelle `Procfile` (Fallback):**
```
web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

**Update `requirements.txt`:**
```txt
# Add at top for Railway compatibility
gunicorn==21.2.0
python-dotenv==1.0.0

# Existing dependencies...
streamlit>=1.52.2
openai>=2.14.0
pypdf>=6.5.0
python-docx>=1.2.0
# ... rest of your requirements
```

#### 2. Deploy zu Railway

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# oder mit Homebrew (Mac)
brew install railway

# 2. Login
railway login

# 3. Initialize project
cd c:\Users\mrieben\Documents\cv_generator
railway init

# Wähle: "Create new project" → "cv-generator"

# 4. Add environment variables
railway variables set OPENAI_API_KEY=sk-your-key-here
railway variables set MODEL_NAME=gpt-4o-mini
railway variables set CV_GENERATOR_MODE=full

# Optional: Claude Support
railway variables set ANTHROPIC_API_KEY=sk-ant-your-key-here

# 5. Deploy!
railway up

# 6. Get URL
railway domain
# Output: https://cv-generator-production.up.railway.app
```

**DONE!** App läuft in <5 Minuten.

#### 3. Kosten-Kontrolle

**Railway Dashboard:**
- Gehe zu: https://railway.app/dashboard
- Projekt: cv-generator
- Settings → Usage Limits:
  ```
  Monthly Spend Limit: $10
  Alert at: $5
  ```

**Monitoring:**
```bash
# Check logs
railway logs

# Check metrics (CPU, RAM, Requests)
railway metrics
```

---

## 🤖 MULTI-MODEL SUPPORT INTEGRATION

### Streamlit Dropdown für Model-Auswahl

**Füge zu `app.py` hinzu** (nach imports):

```python
# Import Model Registry
from scripts.model_registry import ModelRegistry

# In Streamlit UI (vor CV Upload):
st.subheader("🤖 AI Model Selection")

models = ModelRegistry.get_available_models()

# Create dropdown options
model_options = {
    info["display_name"]: model_id
    for model_id, info in models.items()
}

selected_model_display = st.selectbox(
    "Select AI Model:",
    options=list(model_options.keys()),
    index=0,  # Default: first option (gpt-4o-mini)
    help="Different models have different costs and quality trade-offs"
)

selected_model = model_options[selected_model_display]

# Show cost estimate
model_info = models[selected_model]
st.info(f"""
**{model_info['display_name']}**
- Provider: {model_info['provider']}
- Cost per CV: ${model_info['cost_per_cv']:.3f}
- Speed: {model_info['speed']}
- Quality: {model_info['quality']}
""")

# Cost calculator
num_cvs = st.number_input("Estimate monthly CVs:", min_value=1, max_value=10000, value=100)
estimate = ModelRegistry.estimate_cost(selected_model, num_cvs)
st.metric("Monthly Cost", estimate['monthly_cost'])

# Pass selected model to pipeline
if cv_uploaded:
    # Store in session state
    st.session_state.selected_model = selected_model
```

**Update `scripts/streamlit_pipeline.py`:**

```python
# In generate_pipeline() function:
from scripts.model_registry import ModelRegistry

# Get model from session state or default
model_name = st.session_state.get('selected_model', 'gpt-4o-mini')

# Get provider
provider = ModelRegistry.get_provider(model_name)

# Use provider for extraction
cv_data = provider.extract_cv(pdf_text, schema, language)
```

### Environment Setup für Multi-Provider

**Update `.env` file:**
```bash
# OpenAI (Required)
OPENAI_API_KEY=sk-your-openai-key

# Anthropic Claude (Optional)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Default model
MODEL_NAME=gpt-4o-mini

# Mode
CV_GENERATOR_MODE=full
```

**Railway Variables:**
```bash
railway variables set OPENAI_API_KEY=sk-...
railway variables set ANTHROPIC_API_KEY=sk-ant-...
```

---

## 💰 KOSTEN-OPTIMIERUNG: CACHING

**Problem**: Duplicate CV uploads kosten 2x API calls.

**Lösung**: Redis Caching (Railway Free Tier!)

### Add Redis to Railway

```bash
# 1. Add Redis service
railway add redis

# 2. Link to your app (Railway does this automatically)

# 3. Update app to use Redis
```

**Install Redis client:**
```bash
pip install redis
```

**Update `scripts/pdf_to_json.py`:**

```python
import hashlib
import redis
import os
import json

# Connect to Railway Redis (URL auto-injected)
redis_client = None
if os.getenv('REDIS_URL'):
    redis_client = redis.from_url(os.getenv('REDIS_URL'))

def pdf_to_json_with_cache(pdf_path, output_path=None, schema_path=None, target_language="de"):
    """Cached version of pdf_to_json"""

    # Read PDF
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()

    # Generate content hash
    content_hash = hashlib.sha256(pdf_content).hexdigest()

    # Check cache
    if redis_client:
        cached = redis_client.get(f'cv:extraction:{content_hash}')
        if cached:
            print(f"✅ Cache HIT! Saved ${0.01:.3f}")
            return json.loads(cached)

    # Extract (original logic)
    cv_data = pdf_to_json(pdf_path, output_path, schema_path, target_language)

    # Cache result (30 days)
    if redis_client:
        redis_client.setex(
            f'cv:extraction:{content_hash}',
            86400 * 30,
            json.dumps(cv_data)
        )

    return cv_data
```

**Savings**: 30-40% API cost reduction (bei wiederholten Uploads).

---

## 📈 SKALIERUNGS-PFAD

### Phase 1: Railway (Jetzt)
- **Kosten**: $5-10/Monat
- **User**: 5-10
- **CVs**: 100-500/Monat
- **Setup**: 1 Stunde

### Phase 2: Railway + Redis (Monat 2-3)
- **Kosten**: $5/Monat (Redis Free Tier)
- **Savings**: -30% API costs
- **Setup**: 30 Minuten

### Phase 3: Railway Pro (bei 500+ CVs/Monat)
- **Kosten**: $20/Monat + API
- **Features**:
  - Mehr CPU/RAM
  - Custom Domain
  - Advanced Metrics

### Phase 4: AWS Lambda (bei 5000+ CVs/Monat)
- **Kosten**: $30-50/Monat (All-in)
- **Benefits**: -60% vs. Railway bei Scale
- **Setup**: 2-4 Wochen (siehe MIGRATION_RUNBOOK.md)

---

## 🔧 ALTERNATIVE: FLY.IO (KOMPLETT GRATIS)

**Fly.io Free Tier:**
- 3 shared-cpu VMs (256MB RAM each)
- 160GB Outbound Data Transfer
- **Total: $0/Monat!**

### Setup Fly.io:

```bash
# 1. Install Fly CLI
curl -L https://fly.io/install.sh | sh

# 2. Sign up
fly auth signup

# 3. Create app
fly launch

# Follow prompts:
# - App name: cv-generator
# - Region: Frankfurt (ams)
# - PostgreSQL: No
# - Redis: No (add later if needed)

# 4. Deploy
fly deploy

# 5. Set secrets
fly secrets set OPENAI_API_KEY=sk-...
fly secrets set MODEL_NAME=gpt-4o-mini

# 6. Open app
fly open
```

**Dockerfile** (Fly.io erkennt Streamlit automatisch, aber zur Sicherheit):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose Streamlit port
EXPOSE 8080

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
```

**Kosten**: **$0/Monat** für 100 CVs (nur API costs: $1)

**Limitation**: 256MB RAM → manchmal langsam bei großen PDFs (>10MB).

---

## 🎯 EMPFEHLUNG FÜR DICH

Basierend auf deinen Anforderungen:

### **START: Railway.app**
```
✅ Setup: 30 Minuten
✅ Kosten: $6/Monat (5 User, 100 CVs)
✅ Multi-Model: Dropdown in Streamlit
✅ Skalierbar: Bis 5000 CVs
```

**Deploy Commands:**
```bash
railway login
railway init
railway variables set OPENAI_API_KEY=sk-...
railway variables set ANTHROPIC_API_KEY=sk-ant-...
railway up
```

### **MONAT 2: Add Redis Caching**
```
✅ Kosten: $0 (Railway Free Tier)
✅ Savings: -30% API costs
✅ Setup: 15 Minuten
```

```bash
railway add redis
# Update code to use caching (siehe oben)
railway up
```

### **BEI 1000+ CVs: Migrate to AWS Lambda**
```
✅ Kosten: $40/Monat (vs. $60 Railway)
✅ Savings: -33%
✅ Setup: 2 Wochen (follow MIGRATION_RUNBOOK.md)
```

---

## 📊 COST TRACKER DASHBOARD

**Add to Streamlit Sidebar:**

```python
# sidebar.py
import streamlit as st
import os
from datetime import datetime

# Track API usage (store in Railway PostgreSQL or local file)
st.sidebar.header("💰 Cost Tracker")

# Get current month usage (mock for now)
monthly_cvs = st.sidebar.number_input("CVs processed this month:", value=42)
selected_model = st.session_state.get('selected_model', 'gpt-4o-mini')

# Calculate costs
from scripts.model_registry import ModelRegistry
estimate = ModelRegistry.estimate_cost(selected_model, monthly_cvs)

st.sidebar.metric("Monthly Cost", estimate['monthly_cost'])

# Budget alert
budget = 10  # $10/month
if float(estimate['monthly_cost'].replace('$', '')) > budget:
    st.sidebar.error(f"⚠️ Budget exceeded! Limit: ${budget}")
else:
    st.sidebar.success(f"✅ Within budget (${budget})")
```

---

## 🔄 NEXT STEPS

### Diese Woche:
1. [ ] Deploy to Railway (30 min)
2. [ ] Add Model Dropdown (1 hour)
3. [ ] Test with 5 users

### Nächste Woche:
1. [ ] Add Redis Caching (30 min)
2. [ ] Add Cost Tracker Dashboard (1 hour)
3. [ ] Monitor real usage

### Monat 2:
1. [ ] Review costs
2. [ ] If >1000 CVs → Start AWS Migration
3. [ ] Add PyResParser für Free Tier Testing

---

## 📞 SUPPORT

**Fragen?**
- Railway Docs: https://docs.railway.app/
- Fly.io Docs: https://fly.io/docs/
- Model Registry Code: `scripts/model_registry.py`

**Cost Monitoring:**
- Railway Dashboard: https://railway.app/dashboard
- OpenAI Usage: https://platform.openai.com/usage
- Anthropic Usage: https://console.anthropic.com/settings/usage

---

**Nächster Schritt**: Soll ich dir helfen, Railway zu deployen? Oder willst du zuerst den Model Dropdown lokal testen?
