# Serverless Architecture - CV Generator

**Target Platform**: AWS (Primary) | Azure (Alternative)
**Estimated Migration Timeline**: 8-12 weeks
**Cost Reduction**: ~60% at scale (>5000 CVs/month)

---

## Executive Summary

This document outlines the **complete serverless migration strategy** for the CV Generator, transitioning from:
- **Current**: Streamlit monolith on local/VM infrastructure
- **Target**: Event-driven microservices on AWS Lambda + S3 + DynamoDB

**Key Benefits**:
- ✅ **Auto-scaling**: Handle 10→10,000 CVs/month without infrastructure changes
- ✅ **Cost Efficiency**: Pay-per-use (no idle server costs)
- ✅ **Global Availability**: Deploy to multiple regions (latency <100ms)
- ✅ **Zero Maintenance**: No server patching, OS updates, or capacity planning

---

## Phase 1: Current vs. Target Architecture

### Current Architecture (Monolithic)

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Server (VM)                    │
├─────────────────────────────────────────────────────────────┤
│  app.py (UI + Backend)                                       │
│    │                                                          │
│    ├─► pdf_to_json.py ──► OpenAI API ──► JSON               │
│    ├─► generate_cv.py ──► python-docx ──► Word File         │
│    ├─► generate_matchmaking.py ──► OpenAI ──► Match JSON    │
│    └─► visualize_results.py ──► HTML Dashboard              │
│                                                              │
│  File System:                                                │
│    └── output/{name}_{timestamp}/                           │
│         ├── cv_*.docx                                        │
│         ├── cv_*.json                                        │
│         ├── match_*.json                                     │
│         └── dashboard_*.html                                 │
└─────────────────────────────────────────────────────────────┘

Issues:
❌ Single point of failure (VM down = service down)
❌ Vertical scaling only (bigger VM = more $$)
❌ Manual deployment (SSH + restart service)
❌ No auto-scaling (traffic spike = downtime)
```

### Target Architecture (Serverless)

```
┌──────────────────────────────────────────────────────────────────────┐
│                          AWS CloudFront (CDN)                         │
│                      https://cv-generator.com                         │
└────────────────┬─────────────────────────────────────────────────────┘
                 │
     ┌───────────▼────────────┐
     │   Next.js Frontend     │
     │   (S3 + CloudFront)    │
     │   - Upload UI          │
     │   - Dashboard View     │
     │   - Real-time Progress │
     └───────────┬────────────┘
                 │
     ┌───────────▼────────────┐
     │   API Gateway (REST)   │
     │   /api/v1/cv/upload    │
     │   /api/v1/cv/status    │
     │   /api/v1/cv/download  │
     └───────────┬────────────┘
                 │
     ┌───────────▼──────────────────────────────────────────────┐
     │                    AWS Lambda Functions                   │
     ├──────────────────────────────────────────────────────────┤
     │                                                            │
     │  λ upload-handler        → Validate PDF, push to SQS      │
     │       │                                                    │
     │       └──► SQS Queue: cv-processing-queue                 │
     │                   │                                        │
     │  λ cv-extractor  ◄┘    → OpenAI GPT-4o-mini (PDF→JSON)   │
     │       │                                                    │
     │       ├──► λ cv-generator     → python-docx (JSON→Word)   │
     │       ├──► λ matcher          → OpenAI (Job Matching)     │
     │       ├──► λ feedback         → Quality Analysis          │
     │       └──► λ offer-generator  → Word Offer Document       │
     │                   │                                        │
     │  λ dashboard-builder ◄┘  → HTML + Chart.js               │
     │                                                            │
     └────────────────────────────────────────────────────────────┘
                 │                           │
     ┌───────────▼────────────┐  ┌──────────▼──────────┐
     │   DynamoDB Tables      │  │   S3 Buckets        │
     │   ─────────────────    │  │   ─────────────     │
     │   • cv-metadata        │  │   • cv-uploads/     │
     │   • job-profiles       │  │   • cv-outputs/     │
     │   • processing-status  │  │   • dashboards/     │
     │   • user-sessions      │  │                     │
     └────────────────────────┘  └─────────────────────┘

     ┌────────────────────────┐
     │   ElastiCache (Redis)  │
     │   • CV content-hash    │
     │   • API response cache │
     │   • Rate limiting      │
     └────────────────────────┘

     ┌────────────────────────┐
     │   Secrets Manager      │
     │   • OPENAI_API_KEY     │
     │   • DB_CREDENTIALS     │
     │   • AUTH0_CLIENT_ID    │
     └────────────────────────┘
```

---

## Phase 2: Component Breakdown

### 2.1 Frontend (Next.js on S3)

**Replace**: Streamlit UI
**With**: Next.js 14 + React + TypeScript

**Features**:
```typescript
// pages/upload.tsx
export default function UploadPage() {
  const uploadCV = async (file: File) => {
    const formData = new FormData();
    formData.append('cv', file);

    const response = await fetch('/api/v1/cv/upload', {
      method: 'POST',
      body: formData
    });

    const { jobId } = await response.json();

    // WebSocket for real-time progress
    const ws = new WebSocket(`wss://api.cv-gen.com/ws/${jobId}`);
    ws.onmessage = (event) => {
      const { step, status, progress } = JSON.parse(event.data);
      updateProgressBar(step, status, progress);
    };
  };
}
```

**Deployment**:
```bash
# Build static Next.js app
npm run build
npm run export

# Deploy to S3
aws s3 sync out/ s3://cv-generator-frontend
aws cloudfront create-invalidation --distribution-id E123 --paths "/*"
```

**Cost**: ~$5/month (S3 + CloudFront at 10k requests/day)

---

### 2.2 API Gateway

**Routes**:
```yaml
/api/v1/cv/upload:
  POST:
    - Validate PDF (size, type)
    - Generate job ID (UUID)
    - Upload to S3: s3://cv-uploads/{job_id}/input.pdf
    - Push message to SQS: cv-processing-queue
    - Return: { jobId, status: "pending" }

/api/v1/cv/status/{jobId}:
  GET:
    - Query DynamoDB: cv-metadata table
    - Return: { status, progress, steps: [...] }

/api/v1/cv/download/{jobId}:
  GET:
    - Generate pre-signed S3 URL (expires in 1 hour)
    - Return: { wordUrl, dashboardUrl, jsonUrl }

/api/v1/cv/webhook:
  POST:
    - Receive SNS notifications from Lambda failures
    - Trigger retry logic
```

**Authentication**: AWS Cognito JWT validation

**Throttling**: 100 requests/second per API key

---

### 2.3 Lambda Functions

#### λ cv-extractor
**Trigger**: SQS message from upload-handler
**Runtime**: Python 3.11
**Memory**: 512 MB
**Timeout**: 120s
**Concurrency**: 100

```python
# lambda_functions/cv_extractor/handler.py
import boto3
import json
from openai import OpenAI

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
secrets = boto3.client('secretsmanager')

def lambda_handler(event, context):
    for record in event['Records']:
        job_id = json.loads(record['body'])['jobId']

        # Update status in DynamoDB
        table = dynamodb.Table('cv-metadata')
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET #status = :status, step = :step',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'processing',
                ':step': 'pdf_extraction'
            }
        )

        # Download PDF from S3
        pdf_obj = s3.get_object(Bucket='cv-uploads', Key=f'{job_id}/input.pdf')
        pdf_content = pdf_obj['Body'].read()

        # Extract with OpenAI
        api_key = get_secret('openai-api-key')
        client = OpenAI(api_key=api_key)

        cv_json = pdf_to_json(pdf_content, client)

        # Save JSON to S3
        s3.put_object(
            Bucket='cv-outputs',
            Key=f'{job_id}/cv_data.json',
            Body=json.dumps(cv_json),
            ContentType='application/json'
        )

        # Trigger next step (fan-out to parallel Lambdas)
        sns = boto3.client('sns')
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:123:cv-extracted',
            Message=json.dumps({'jobId': job_id, 'cv_json_s3': f's3://cv-outputs/{job_id}/cv_data.json'})
        )

    return {'statusCode': 200}
```

**Dockerfile** (for Lambda Container Image):
```dockerfile
FROM public.ecr.aws/lambda/python:3.11

COPY requirements.txt .
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY handler.py ${LAMBDA_TASK_ROOT}
COPY scripts/ ${LAMBDA_TASK_ROOT}/scripts/

CMD ["handler.lambda_handler"]
```

**Deployment**:
```bash
# Build Docker image
docker build -t cv-extractor .

# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin 123.dkr.ecr.us-east-1.amazonaws.com
docker tag cv-extractor:latest 123.dkr.ecr.us-east-1.amazonaws.com/cv-extractor:latest
docker push 123.dkr.ecr.us-east-1.amazonaws.com/cv-extractor:latest

# Update Lambda
aws lambda update-function-code \
  --function-name cv-extractor \
  --image-uri 123.dkr.ecr.us-east-1.amazonaws.com/cv-extractor:latest
```

---

#### λ cv-generator (JSON → Word)
**Trigger**: SNS topic `cv-extracted`
**Runtime**: Python 3.11 (Container)
**Memory**: 1024 MB (python-docx needs more memory)
**Timeout**: 60s

```python
# lambda_functions/cv_generator/handler.py
from docx import Document
import boto3
import json

def lambda_handler(event, context):
    message = json.loads(event['Records'][0]['Sns']['Message'])
    job_id = message['jobId']

    # Download CV JSON from S3
    s3 = boto3.client('s3')
    cv_json_obj = s3.get_object(Bucket='cv-outputs', Key=f'{job_id}/cv_data.json')
    cv_data = json.loads(cv_json_obj['Body'].read())

    # Generate Word document
    doc = generate_word_cv(cv_data)

    # Save to S3 (in-memory buffer, no file system)
    from io import BytesIO
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    s3.put_object(
        Bucket='cv-outputs',
        Key=f'{job_id}/cv.docx',
        Body=buffer.getvalue(),
        ContentType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

    # Update DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('cv-metadata')
    table.update_item(
        Key={'jobId': job_id},
        UpdateExpression='SET step = :step, wordUrl = :url',
        ExpressionAttributeValues={
            ':step': 'word_generated',
            ':url': f's3://cv-outputs/{job_id}/cv.docx'
        }
    )
```

---

#### λ matcher (Job Matching)
**Trigger**: SNS topic `cv-extracted` (parallel to cv-generator)
**Memory**: 512 MB
**Timeout**: 90s

```python
def lambda_handler(event, context):
    # Similar pattern: download CV JSON + Job Profile JSON
    # Call OpenAI for matching
    # Save match_result.json to S3
    # Update DynamoDB with match score
```

---

### 2.4 Storage Layer

#### DynamoDB Tables

**cv-metadata** (Main table):
```json
{
  "jobId": "uuid-1234-5678",           // Partition Key
  "userId": "user-abc",                // Global Secondary Index
  "status": "completed",               // pending | processing | completed | failed
  "step": "dashboard_generated",       // Current pipeline step
  "createdAt": "2026-01-10T10:30:00Z",
  "updatedAt": "2026-01-10T10:33:45Z",
  "cvFileName": "John_Doe_CV.pdf",
  "jobProfileFileName": "Senior_Dev.pdf",
  "language": "de",                    // de | en | fr
  "outputs": {
    "cv_json": "s3://cv-outputs/uuid-1234/cv_data.json",
    "cv_word": "s3://cv-outputs/uuid-1234/cv.docx",
    "match_json": "s3://cv-outputs/uuid-1234/match_result.json",
    "dashboard_html": "s3://cv-outputs/uuid-1234/dashboard.html"
  },
  "matchScore": 87,
  "errorMessage": null,
  "retryCount": 0,
  "ttl": 1704931200                    // Auto-delete after 30 days
}
```

**job-profiles** (Reusable job profiles):
```json
{
  "profileId": "profile-abc",          // Partition Key
  "companyId": "company-123",
  "title": "Senior Software Engineer",
  "requirements": { ... },
  "createdAt": "2026-01-01T00:00:00Z",
  "s3Url": "s3://job-profiles/profile-abc.json"
}
```

#### S3 Buckets

```
cv-uploads/
├── {jobId}/
│   ├── input.pdf          (Original CV upload)
│   └── job_profile.pdf    (Optional)

cv-outputs/
├── {jobId}/
│   ├── cv_data.json       (Extracted CV data)
│   ├── cv.docx            (Generated Word document)
│   ├── match_result.json  (Matching analysis)
│   ├── feedback.json      (Quality feedback)
│   ├── offer.docx         (Generated offer)
│   └── dashboard.html     (HTML dashboard)

cv-cache/
└── content-hashes/
    └── {sha256}.json      (Cached extraction results)
```

**Lifecycle Policies**:
- `cv-uploads/`: Delete after 7 days
- `cv-outputs/`: Move to S3 Glacier after 90 days
- `cv-cache/`: Delete after 30 days

---

### 2.5 Caching Layer (ElastiCache Redis)

**Purpose**: Reduce OpenAI API costs by 30-40%

```python
# lambda_functions/cv_extractor/cache.py
import hashlib
import redis
import json

redis_client = redis.from_url(os.environ['REDIS_URL'])

def get_cached_cv_extraction(pdf_content: bytes) -> dict | None:
    content_hash = hashlib.sha256(pdf_content).hexdigest()
    cached = redis_client.get(f'cv:extraction:{content_hash}')

    if cached:
        print(f"Cache HIT for {content_hash[:8]}... (saved OpenAI call)")
        return json.loads(cached)

    return None

def cache_cv_extraction(pdf_content: bytes, cv_json: dict):
    content_hash = hashlib.sha256(pdf_content).hexdigest()
    redis_client.setex(
        f'cv:extraction:{content_hash}',
        86400 * 30,  # 30 days TTL
        json.dumps(cv_json)
    )
```

**Cost Savings Example**:
- Without cache: 1000 CVs/month → CHF 10
- With cache (40% hit rate): 600 API calls → CHF 6 (-40%)

---

## Phase 3: Event Flow (Fan-Out Pattern)

```
┌─────────────┐
│  User Upload │
└──────┬───────┘
       │
       ▼
┌─────────────────┐
│ λ upload-handler│  ──► Validate PDF
└──────┬──────────┘      Push to SQS
       │
       ▼
┌─────────────────┐
│  SQS Queue      │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ λ cv-extractor  │  ──► OpenAI API call
└──────┬──────────┘      Save JSON to S3
       │                 Publish to SNS
       │
       ▼
┌─────────────────────────────────────────────┐
│          SNS Topic: cv-extracted             │
└────┬────────┬──────────┬──────────┬─────────┘
     │        │          │          │
     ▼        ▼          ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ λ cv-   │ │ λ       │ │ λ       │ │ λ offer │
│ gen     │ │ matcher │ │feedback │ │ gen     │
└────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
     │           │           │           │
     └───────────┴───────────┴───────────┘
                      │
                      ▼
            ┌─────────────────┐
            │ λ dashboard-    │
            │ builder         │
            └────────┬─────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ Send Email /    │
            │ WebSocket       │
            │ Notification    │
            └─────────────────┘
```

**Benefits**:
- Parallel execution (cv-gen + matcher + feedback run simultaneously)
- Fault isolation (one Lambda failure doesn't block others)
- Auto-scaling (each function scales independently)

---

## Phase 4: Cost Comparison

### Current Architecture (VM-based)

**Monthly Costs** (1000 CVs/month):
```
EC2 t3.medium (2 vCPU, 4GB RAM, 24/7):
  - Instance:        $30/month
  - EBS Storage:     $10/month (100GB)
  - Data Transfer:   $5/month

OpenAI API:          $10/month

TOTAL:               $55/month
```

**Scaling Issues**:
- Need bigger VM for 2000 CVs → $70/month (t3.large)
- Traffic spike (5000 CVs in 1 day) → VM crashes or manual scale-up

---

### Serverless Architecture

**Monthly Costs** (1000 CVs/month):
```
Lambda Executions:
  - cv-extractor:    1000 × 60s × 512MB  = $0.50
  - cv-generator:    1000 × 30s × 1024MB = $0.75
  - matcher:         1000 × 45s × 512MB  = $0.40
  - feedback:        1000 × 20s × 512MB  = $0.25
  - offer:           500 × 30s × 512MB   = $0.15
  - dashboard:       1000 × 5s × 256MB   = $0.10

API Gateway:         1000 requests = $0.01

S3 Storage (3 months retention):
  - cv-uploads:      100GB = $2.30
  - cv-outputs:      50GB  = $1.15

DynamoDB (on-demand):
  - Writes:          5000 WCUs = $1.25
  - Reads:           10000 RCUs = $0.25

ElastiCache (t4g.micro): $11/month

CloudFront CDN:      $5/month

OpenAI API:          $10/month

TOTAL:               $33/month  (-40% vs. VM)
```

**At 10,000 CVs/month**:
- VM-based: ~$200/month (t3.xlarge + load balancer)
- Serverless: ~$120/month (-40%)

**Break-even Analysis**:
- Below 500 CVs/month: VM slightly cheaper
- Above 500 CVs/month: Serverless wins
- Above 5000 CVs/month: Serverless 60% cheaper

---

## Phase 5: Migration Roadmap

### Week 1-2: Foundation
- [ ] Set up AWS account + IAM roles
- [ ] Create DynamoDB tables (cv-metadata, job-profiles)
- [ ] Create S3 buckets (cv-uploads, cv-outputs)
- [ ] Deploy ElastiCache Redis cluster
- [ ] Set up Secrets Manager for API keys

### Week 3-4: Backend Migration
- [ ] Containerize `scripts/pdf_to_json.py` → λ cv-extractor
- [ ] Containerize `scripts/generate_cv.py` → λ cv-generator
- [ ] Create API Gateway endpoints
- [ ] Implement SQS + SNS event pipeline
- [ ] Add retry logic + error handling

### Week 5-6: Parallel Processing
- [ ] Deploy λ matcher (job matching)
- [ ] Deploy λ feedback (quality analysis)
- [ ] Deploy λ offer-generator
- [ ] Deploy λ dashboard-builder
- [ ] Add WebSocket support for real-time progress

### Week 7-8: Frontend Rebuild
- [ ] Build Next.js frontend
  - Upload page
  - Status tracking page
  - Dashboard viewer
  - Download manager
- [ ] Integrate Auth0 / Cognito
- [ ] Deploy to S3 + CloudFront

### Week 9-10: Testing & Optimization
- [ ] Load testing (simulate 1000 concurrent uploads)
- [ ] Cost optimization (right-size Lambda memory)
- [ ] Add caching layer (Redis)
- [ ] Implement content-hash deduplication

### Week 11-12: Production Cutover
- [ ] Blue-green deployment
- [ ] DNS migration (route traffic to CloudFront)
- [ ] Monitor for 48 hours
- [ ] Decommission old VM infrastructure

---

## Phase 6: Monitoring & Alerts

### CloudWatch Dashboards
```yaml
Metrics to Track:
  - Lambda invocation count (by function)
  - Lambda error rate (target: <1%)
  - Lambda duration (p50, p95, p99)
  - API Gateway latency
  - SQS queue depth (alert if >100 messages)
  - DynamoDB throttling events
  - S3 storage costs
  - OpenAI API costs (daily budget alarm)
```

### Alerts
```yaml
Critical Alerts (PagerDuty):
  - Lambda error rate > 5% (5 min window)
  - SQS DLQ has messages (retry failures)
  - API Gateway 5xx errors > 10/min
  - DynamoDB capacity exhausted

Warning Alerts (Email):
  - Lambda duration > 60s (approaching timeout)
  - S3 storage > 500GB (cost spike)
  - OpenAI API cost > $50/day (abuse detection)
```

---

## Phase 7: Security

### IAM Least Privilege
```yaml
# lambda-execution-role.yaml
Policies:
  - Effect: Allow
    Action:
      - s3:GetObject
      - s3:PutObject
    Resource: arn:aws:s3:::cv-uploads/*

  - Effect: Allow
    Action:
      - dynamodb:GetItem
      - dynamodb:PutItem
      - dynamodb:UpdateItem
    Resource: arn:aws:dynamodb:us-east-1:123:table/cv-metadata

  - Effect: Allow
    Action: secretsmanager:GetSecretValue
    Resource: arn:aws:secretsmanager:us-east-1:123:secret:openai-api-key

  - Effect: Deny
    Action: s3:DeleteObject
    Resource: "*"  # Prevent accidental data loss
```

### API Security
- **CORS**: Whitelist only production domain
- **Rate Limiting**: 10 requests/minute per IP
- **JWT Validation**: All routes except `/health`
- **S3 Pre-signed URLs**: Expire in 1 hour
- **VPC Endpoints**: Lambda → DynamoDB/S3 (private network)

---

## Conclusion

The serverless migration delivers:
- **40-60% cost reduction** at scale
- **99.9% availability** (multi-AZ)
- **Auto-scaling** (0 → 10,000 CVs seamlessly)
- **Zero maintenance** (no OS patching, no capacity planning)

**Recommended Next Step**: Start with Week 1-2 (Foundation) on a dev AWS account to validate feasibility.

---

**Related Documents**:
- [TECH_DEBT.md](./TECH_DEBT.md) - Technical debt analysis
- [MIGRATION_RUNBOOK.md](./MIGRATION_RUNBOOK.md) - Step-by-step deployment guide (coming next)
