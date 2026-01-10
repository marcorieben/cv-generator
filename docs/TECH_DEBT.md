# Tech Debt Report - CV Generator

**Generated**: 2026-01-10
**Branch**: `feature/serverless-migration`
**Analyzed Version**: Multi-Language Support (DE/EN/FR)

---

## Executive Summary

**Serverless Readiness Score**: 3/10 🔴
**Monthly API Cost** (1000 CVs): ~CHF 10
**Average Processing Time**: 2-3 minutes per CV
**Critical Issues**: 3 | High Priority: 5 | Medium: 3

---

## Architecture Overview

### Current Stack
```
Entry Points:
├── app.py                      # Streamlit Web UI (Production)
└── run_pipeline.py            # CLI Pipeline with Tkinter dialogs

Core Pipeline:
├── scripts/pdf_to_json.py     # PDF → JSON (OpenAI GPT-4o-mini)
├── scripts/generate_cv.py     # JSON → Word (.docx)
├── scripts/generate_matchmaking.py  # Job matching logic
├── scripts/generate_angebot_word.py # Offer generation
└── scripts/visualize_results.py     # HTML Dashboard
```

### Key Dependencies
```python
openai>=2.14.0           # GPT-4o-mini API
pypdf>=6.5.0            # PDF text extraction
python-docx>=1.2.0      # Word document generation
streamlit>=1.52.2       # Web UI framework
```

---

## Cost Analysis

### OpenAI API Usage (GPT-4o-mini)

**Per Full Pipeline** (CV + Job Matching + Feedback + Offer):
- Total Input Tokens: ~20,500
- Total Output Tokens: ~10,000
- **Cost per CV**: ~CHF 0.01 (€0.008)

**Volume Pricing**:
| Monthly Volume | Total Cost |
|---------------|------------|
| 100 CVs       | CHF 1.00   |
| 1,000 CVs     | CHF 10.00  |
| 10,000 CVs    | CHF 100.00 |

### Performance Metrics

**Latency Breakdown**:
```
PDF Extraction:        30-60s
Job Profile Extract:   20-30s
Matchmaking:          20-40s
Feedback Generation:   15-25s
Offer Generation:      25-35s
Dashboard Creation:    2-5s
────────────────────────────
TOTAL:                2-3 min per CV
```

**Bottlenecks**:
- Sequential OpenAI API calls (no parallelization)
- Blocking UI during processing
- No caching for repeated CV uploads

---

## Critical Issues 🔴

### 1. API Key Security
**Location**: `.env`, `app.py`

**Problem**:
- API keys stored in `.env` files (risk of accidental commit)
- No secrets manager integration
- Keys loaded into Streamlit session state (memory exposure)

**Impact**: High security risk in multi-user environments

**Recommendation**:
- Migrate to AWS Secrets Manager / Azure Key Vault
- Implement IAM role-based access
- Remove hardcoded API keys from codebase

---

### 2. No Error Recovery
**Location**: `scripts/streamlit_pipeline.py:122-264`

**Problem**:
```python
# Current: No retry logic
response = client.chat.completions.create(...)
# If this fails → entire pipeline aborts, no partial save
```

**Impact**:
- Lost work on API timeouts (after 2 minutes of processing)
- No retry with exponential backoff
- User has to restart from scratch

**Recommendation**:
```python
# Implement retry with tenacity
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_openai_with_retry():
    return client.chat.completions.create(...)
```

---

### 3. Blocking UI (Streamlit)
**Location**: `app.py`, `scripts/streamlit_pipeline.py`

**Problem**:
- Streamlit runs synchronously
- UI freezes during 2-3 minute processing
- No true background jobs
- Progress callbacks are cosmetic (not async)

**Impact**:
- Poor UX (user sees frozen screen)
- Cannot process multiple CVs in parallel
- Not production-ready for high traffic

**Recommendation**:
- Migrate to FastAPI + Celery for background tasks
- Use WebSockets for real-time progress
- Decouple frontend from backend processing

---

## High Priority Issues 🟡

### 4. Hardcoded Business Logic
**Location**: `scripts/pdf_to_json.py:418-465`

**Problem**:
- 15-page system prompt hardcoded in Python
- Schema changes require code deployment
- No A/B testing capability for prompt optimization

**Recommendation**:
- Move prompts to database/config files
- Implement prompt versioning
- Enable dynamic schema updates

---

### 5. No Caching Layer
**Problem**:
- Same CV uploaded twice → 2 API calls (2x cost)
- No content-hash-based deduplication
- No intermediate result caching

**Cost Impact**:
- 30-40% of API calls are duplicates (typical pattern)
- Potential savings: CHF 3-4 per 1000 CVs

**Recommendation**:
```python
import hashlib
import redis

def get_or_generate_cv_json(pdf_content):
    content_hash = hashlib.sha256(pdf_content).hexdigest()
    cached = redis.get(f"cv:{content_hash}")
    if cached:
        return json.loads(cached)

    result = pdf_to_json(pdf_content)
    redis.setex(f"cv:{content_hash}", 86400, json.dumps(result))  # 24h TTL
    return result
```

---

### 6. File System Dependency
**Location**: `scripts/generate_cv.py:1115-1128`

**Problem**:
```python
# Current: Local file system writes
output_dir = f"output/{name}_{timestamp}/"
doc.save(f"{output_dir}/cv_{name}.docx")
```

**Impact**:
- Cannot scale horizontally (shared FS required)
- No cloud storage integration
- Difficult to deploy on serverless (ephemeral FS)

**Recommendation**:
- S3/Azure Blob for document storage
- Generate pre-signed URLs for downloads
- Use DynamoDB/CosmosDB for metadata

---

### 7. Weak Authentication
**Location**: `app.py` (Streamlit Authenticator)

**Problem**:
- `streamlit-authenticator` is deprecated/unmaintained
- No RBAC (role-based access control)
- Session state only (no JWT)
- No SSO integration

**Recommendation**:
- Migrate to Auth0 / Cognito
- Implement JWT-based auth
- Add role management (admin/user/viewer)

---

## Medium Priority Issues 🟢

### 8. No Test Coverage
**Location**: `tests/` (minimal)

**Current State**:
- Only mock fixtures for offline testing
- No unit tests for business logic
- No integration tests
- No CI/CD pipeline validation

**Recommendation**:
- Target 80% code coverage
- Add pytest suite for core functions
- Integration tests for OpenAI mocking
- Pre-commit hooks for test execution

---

### 9. Monolithic Pipeline
**Location**: `scripts/pipeline.py:220-470`

**Problem**:
- All steps in single process
- No microservice boundaries
- Hard to debug partial failures
- Cannot scale individual components

**Recommendation**:
- Split into microservices:
  - `pdf-extractor-service`
  - `cv-generator-service`
  - `matching-service`
  - `offer-service`

---

### 10. No Observability
**Problem**:
- Print statements instead of structured logging
- No metrics collection (latency, success rate)
- No distributed tracing
- No alerting on failures

**Recommendation**:
```python
import structlog
import prometheus_client

logger = structlog.get_logger()
latency = prometheus_client.Histogram('cv_generation_latency_seconds')

@latency.time()
def generate_cv(json_path):
    logger.info("cv_generation_started", json_path=json_path)
    # ... processing
    logger.info("cv_generation_completed", duration_ms=elapsed)
```

---

## Serverless Readiness Assessment

### ✅ What Works
- Stateless business logic (JSON in → JSON out)
- Clear function boundaries (each step is isolatable)
- ENV-based configuration (`.env` for API keys)
- Multi-language support (DE/EN/FR)

### ❌ What Blocks Serverless
- **File System Dependency**: Local `output/` folder writes
- **No Async Execution**: Blocking I/O operations
- **Streamlit Architecture**: Not cloud-native
- **No Containerization**: Missing Dockerfile
- **Session State**: In-memory state (not distributed)

### Recommended First Steps
1. **Phase 1**: Add S3 storage for outputs (remove FS dependency)
2. **Phase 2**: Containerize with Docker
3. **Phase 3**: Deploy to AWS Lambda + API Gateway
4. **Phase 4**: Add SQS for async job processing
5. **Phase 5**: Replace Streamlit with Next.js + FastAPI

---

## Action Items

### Immediate (This Sprint)
- [ ] Fix pre-commit hook emoji encoding issue
- [ ] Add retry logic to OpenAI calls
- [ ] Implement content-hash-based caching (Redis)
- [ ] Move API keys to environment secrets manager

### Short-term (Next 2 Sprints)
- [ ] Replace Streamlit with FastAPI backend
- [ ] Add S3 storage for Word/HTML outputs
- [ ] Implement structured logging (structlog)
- [ ] Add unit tests for core business logic

### Long-term (Next Quarter)
- [ ] Full serverless migration (AWS Lambda)
- [ ] Replace file system with DynamoDB + S3
- [ ] Implement Auth0 / Cognito authentication
- [ ] Add Datadog / CloudWatch observability

---

## Appendix: File Structure Analysis

**Total Python Files**: 19
**Lines of Code**: ~8,500
**Main Entry Points**: 2 (app.py, run_pipeline.py)
**Core Modules**: 11
**Test Files**: 2

**Largest Files**:
1. `scripts/generate_cv.py` - 1,517 LOC (Word generation)
2. `scripts/visualize_results.py` - 923 LOC (HTML dashboard)
3. `scripts/generate_angebot_word.py` - 615 LOC (Offer Word)
4. `scripts/pdf_to_json.py` - 509 LOC (PDF extraction)
5. `scripts/pipeline.py` - 528 LOC (CLI pipeline)

---

**Next Steps**: See [SERVERLESS_ARCHITECTURE.md](./SERVERLESS_ARCHITECTURE.md) for migration plan.
