# Deployment Checklist - Gradio Migration

**Target Platform:** Railway.app
**Estimated Time:** 15-20 minutes
**Cost:** $6/month (Railway $5 + API $1 for 100 CVs)

---

## ✅ Pre-Deployment (Local Testing)

- [x] Install Gradio and Anthropic SDK
  ```bash
  pip install gradio anthropic
  ```

- [x] Run validation tests
  ```bash
  python test_gradio_app.py
  ```
  **Status:** ✅ All tests passed

- [x] Create app_gradio.py with:
  - [x] Real-time progress tracking
  - [x] Multi-user queuing (5 concurrent)
  - [x] 4 tabs (Generate CV, Cost Calculator, Model Comparison, About)
  - [x] Integration with model_registry
  - [x] Railway compatibility (PORT env var)

- [ ] Test locally (OPTIONAL - requires API keys)
  ```bash
  # Set .env file first
  python app_gradio.py
  # Open http://localhost:7860
  ```

---

## 🚀 Railway Deployment

### Step 1: Install Railway CLI

Choose one:

```bash
# Option A: npm (if you have Node.js)
npm install -g @railway/cli

# Option B: Homebrew (Mac/Linux)
brew install railway

# Option C: Manual (Windows)
# Download from: https://github.com/railwayapp/cli/releases
```

### Step 2: Login to Railway

```bash
railway login
```

This opens your browser for authentication.

### Step 3: Initialize Project (if not already done)

```bash
cd c:\Users\mrieben\Documents\cv_generator
railway init
```

Select:
- **Create new project** → Name: `cv-generator`
- Region: Choose closest to you (e.g., `Frankfurt`)

### Step 4: Set Environment Variables

```bash
# Required for OpenAI models
railway variables set OPENAI_API_KEY=sk-your-openai-key-here

# Optional for Claude models
railway variables set ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Default model (optional)
railway variables set MODEL_NAME=gpt-4o-mini

# Processing mode (optional)
railway variables set CV_GENERATOR_MODE=full
```

**Where to get API keys:**
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/settings/keys

### Step 5: Deploy!

```bash
# Make sure you're on the correct branch
git checkout feature/serverless-migration

# Deploy to Railway
railway up
```

**Expected output:**
```
🚀 Building...
✓ Build successful
🚀 Deploying...
✓ Deployment successful
```

### Step 6: Get Your URL

```bash
railway domain
```

**Output:**
```
https://cv-generator-production.up.railway.app
```

### Step 7: Test Production

1. Open the URL from Step 6
2. Upload a test CV from `input/cv/pdf/`
3. Select model: **GPT-4o Mini (Cheapest)**
4. Select language: **de**
5. Click **"🚀 Generate CV"**
6. Verify:
   - ✅ Progress bar updates
   - ✅ Word file downloads
   - ✅ Dashboard shows in preview

---

## 🔍 Post-Deployment Verification

### Monitor Deployment

```bash
# View live logs
railway logs

# View metrics (CPU, RAM, requests)
railway metrics

# View environment variables
railway variables
```

### Test All Features

- [ ] **CV Generation (CV only mode)**
  - Upload CV PDF only
  - Set mode to "cv_only"
  - Verify Word file generated

- [ ] **Full Pipeline (with Job Matching)**
  - Upload CV PDF + Job PDF
  - Set mode to "full"
  - Verify:
    - Word CV generated
    - Match score displayed
    - Dashboard shows matching analysis

- [ ] **Cost Calculator**
  - Switch to "Cost Calculator" tab
  - Test slider (100 CVs)
  - Verify calculations correct

- [ ] **Model Comparison**
  - Switch to "Model Comparison" tab
  - Verify 8 models listed
  - Check recommendations section

- [ ] **Multi-Language Support**
  - Generate CV in German (de)
  - Generate CV in English (en)
  - Generate CV in French (fr)
  - Verify all outputs in correct language

### Performance Check

```bash
# Check response time
curl -w "\nTime: %{time_total}s\n" https://cv-generator-production.up.railway.app/

# Expected: < 2s for initial load
```

### Cost Monitoring

1. Go to Railway Dashboard: https://railway.app/dashboard
2. Click on your project: `cv-generator`
3. Go to **"Usage"** tab
4. Set alerts:
   - Monthly spend limit: **$10**
   - Alert at: **$5**

---

## 🔧 Configuration (Optional)

### Add Authentication

Edit `app_gradio.py`:

```python
demo.launch(
    server_name="0.0.0.0",
    server_port=int(os.getenv("PORT", 7860)),
    auth=("admin", "your-secure-password"),  # ADD THIS LINE
    ...
)
```

Then redeploy:
```bash
git add app_gradio.py
git commit -m "Add authentication"
railway up
```

### Add Custom Domain (Railway Pro only)

1. Go to Railway Dashboard → Project Settings
2. Click "Add Domain"
3. Enter your domain: `cv-generator.yourdomain.com`
4. Add CNAME record in your DNS:
   ```
   cv-generator.yourdomain.com → [railway-provided-domain]
   ```

### Enable HTTPS (Automatic)

Railway automatically provisions SSL certificates via Let's Encrypt.
No configuration needed!

---

## 📊 Usage Tracking

### Simple File-Based Tracking

Add to `app_gradio.py`:

```python
import json
from datetime import datetime
from pathlib import Path

def log_usage(model_name, language, cv_filename):
    """Log usage to file"""
    log_file = Path("usage_log.jsonl")

    entry = {
        "timestamp": datetime.now().isoformat(),
        "model": model_name,
        "language": language,
        "cv_file": cv_filename,
        "cost": ModelRegistry.get_available_models()[model_name]['cost_per_cv']
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

# In process_cv_pipeline(), after successful generation:
log_usage(model_id, language, cv_pdf.name)
```

### View Usage

```bash
# On Railway
railway run cat usage_log.jsonl

# Or download locally
railway run cat usage_log.jsonl > usage_local.jsonl

# Analyze with Python
python -c "
import json
total_cost = 0
with open('usage_local.jsonl') as f:
    for line in f:
        entry = json.loads(line)
        total_cost += entry['cost']
print(f'Total cost: ${total_cost:.2f}')
"
```

---

## 🐛 Troubleshooting

### Deployment fails

**Symptom:**
```
Error: Build failed
```

**Solutions:**
1. Check `requirements.txt` is up to date:
   ```bash
   pip freeze > requirements.txt
   git add requirements.txt
   git commit -m "Update requirements"
   railway up
   ```

2. Check Railway logs:
   ```bash
   railway logs
   ```

### App crashes on startup

**Symptom:**
```
Error: Application failed to start
```

**Solutions:**
1. Check environment variables are set:
   ```bash
   railway variables
   ```

2. Verify OPENAI_API_KEY is set:
   ```bash
   railway variables set OPENAI_API_KEY=sk-...
   ```

3. Check logs for detailed error:
   ```bash
   railway logs --follow
   ```

### Slow performance

**Symptom:**
CVs take >2 minutes to process

**Solutions:**
1. Check Railway plan (Hobby tier has limited resources)
2. Consider upgrading to Railway Pro ($20/month)
3. Check API response times:
   - OpenAI Status: https://status.openai.com/
   - Anthropic Status: https://status.anthropic.com/

### High costs

**Symptom:**
Bill higher than expected

**Solutions:**
1. Check usage log (see "Usage Tracking" above)
2. Review model selection:
   - Are users selecting expensive models (O1)?
   - Recommend GPT-4o-mini by default
3. Implement caching (see `LEAN_DEPLOYMENT.md`)
4. Set Railway spend limits:
   ```bash
   # In Railway Dashboard → Settings → Usage Limits
   Monthly Spend Limit: $10
   ```

---

## 📈 Scaling Plan

### Current Setup (0-100 CVs/month)
- **Platform:** Railway Hobby ($5/month)
- **Model:** GPT-4o-mini ($0.01/CV)
- **Total:** $6/month
- **Supports:** 5 concurrent users

### Phase 2 (100-500 CVs/month)
- **Platform:** Railway Hobby ($5/month)
- **Optimization:** Add Redis caching (-30% API costs)
- **Total:** $8-10/month
- See: `LEAN_DEPLOYMENT.md` - Section "Redis Caching"

### Phase 3 (500-1000 CVs/month)
- **Platform:** Railway Pro ($20/month)
- **Features:** More CPU/RAM, custom domain
- **Total:** $30-35/month

### Phase 4 (1000+ CVs/month)
- **Platform:** Migrate to AWS Lambda
- **Total:** $40-50/month (40% cheaper than Railway at scale)
- See: `MIGRATION_RUNBOOK.md`

---

## ✅ Deployment Complete!

Once all steps are done:

- [x] Railway deployment successful
- [x] Environment variables set
- [x] Domain URL received
- [x] Production testing complete
- [x] Cost monitoring configured
- [x] Team notified of new URL

**Next Steps:**
1. Share URL with internal team (max 5 users)
2. Gather feedback for 1-2 weeks
3. Monitor costs and performance
4. Add Redis caching if >200 CVs/month (see `LEAN_DEPLOYMENT.md`)

---

**Deployment Time:** ⏱️ ~15 minutes
**Status:** 🎉 **READY TO DEPLOY**

**Any questions?** Check:
- `docs/GRADIO_MIGRATION.md` - Full migration guide
- `docs/LEAN_DEPLOYMENT.md` - Railway deployment details
- Railway Docs: https://docs.railway.app/
