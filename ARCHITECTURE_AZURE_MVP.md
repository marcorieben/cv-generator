# CV Generator - Lean MVP auf Microsoft Azure
## Architekturdokument für Entwicklung (Januar 2026)

---

## 1. OVERVIEW: WARUM AZURE?

### 1.1 Unternehmens-Kontext
Wenn dein Unternehmen bereits **Microsoft Enterprise Agreement** oder **Azure-Subscription** hat:

✅ **Vorteile Azure:**
- Kostenersparnisse durch bestehendes Budget
- Integration mit Microsoft Stack (Office 365, Teams, Active Directory)
- SSO / Azure AD für Authentication (kein separates System)
- Compliance & Governance (wenn wichtig für Unternehmen)
- Support über Microsoft Account Manager

❌ **Nachteile:**
- Teuer wenn kein bestehendes Budget
- Etwas komplexer als Heroku
- Weniger "einfach" als Heroku, aber immer noch machbar

---

## 2. AZURE LEAN MVP ARCHITEKTUR

### 2.1 High-Level Überblick
```
┌───────────────────────────────────────────┐
│ Browser                                   │
│ └─ Streamlit UI (bestehend)              │
└──────────────────┬────────────────────────┘
                   │ HTTPS
┌──────────────────────────────────────────┐
│ Azure Container Instances (ACI)           │
│ ├─ Streamlit Container                   │
│ └─ FastAPI Container                     │
│ Cost: €50-100/Monat (on-demand)          │
└──────────────────┬────────────────────────┘
                   │
    ┌──────────────┴──────────────┐
    ↓                             ↓
┌─────────────────┐      ┌──────────────────┐
│ Azure Database  │      │ Azure Blob       │
│ for PostgreSQL  │      │ Storage (Files)  │
│ €15-30/Monat    │      │ €1-5/Monat       │
│ ├─ Metadata     │      │ ├─ Archives      │
│ ├─ Job Tracking │      │ └─ Backups       │
│ └─ Audit Logs   │      │                  │
└─────────────────┘      └──────────────────┘
    │
    └─→ OpenAI API (€0.20-1.50/CV)
```

### 2.2 Azure Services im Detail

#### Option A: Container Instances (ACI) - SIMPLEST
```
Azure Container Instances (ACI)
├─ Pay per second
├─ €50-100/Monat für 2-4 Container (minimal)
├─ Auto-scaling: Nein (aber für MVP nicht nötig)
├─ Best für: Test, MVP, Beta
└─ Setup: Docker image → push zu Azure Container Registry → ACI starten

Workflow:
1. Build Docker image lokal
2. Push zu Azure Container Registry (€7/Monat)
3. Start ACI von Registry
4. Attach PostgreSQL Database
5. Setup DNS (Azure App Service Domain oder custom)
```

**Deployment:**
```bash
# 1. Build & Push Docker Image
docker build -t cv-generator:latest .
az acr build --registry myregistry --image cv-generator:latest .

# 2. Deploy to ACI
az container create \
  --resource-group mygroup \
  --name cv-generator \
  --image myregistry.azurecr.io/cv-generator:latest \
  --cpu 1 \
  --memory 1.5 \
  --ports 8000 8501 \
  --environment-variables \
    DB_HOST=mydb.postgres.database.azure.com \
    DB_USER=admin \
    OPENAI_API_KEY=$OPENAI_KEY
```

#### Option B: App Service (PaaS) - EASIER
```
Azure App Service
├─ Managed Platform (no containers needed)
├─ €15-50/Monat für B1 tier
├─ Auto-scaling: Ja (built-in)
├─ Best für: Production-ready, less ops
└─ Setup: Code → Git Deploy → Auto-run

Advantages over ACI:
- Einfacher Deployment (Git push only)
- Built-in deployment slots (staging/production)
- Application Insights (monitoring) inkludiert
- Auto-scaling included
- SSL/TLS automatic

Disadvantages:
- Teuer als ACI (€15-50 vs €5-10)
- Weniger Kontrolle über Environment
```

**Deployment:**
```bash
# 1. Create App Service Plan
az appservice plan create \
  --name myplan \
  --resource-group mygroup \
  --sku B1 \
  --is-linux

# 2. Create Web App
az webapp create \
  --resource-group mygroup \
  --plan myplan \
  --name my-cv-app \
  --runtime "PYTHON:3.11"

# 3. Deploy from GitHub
az webapp deployment source config-zip \
  --resource-group mygroup \
  --name my-cv-app \
  --src app.zip
```

#### 🎯 EMPFEHLUNG für MVP: **Container Instances (ACI)**
- Günstiger (€50-100 vs €15-50)
- Mehr Kontrolle für komplexes Setup
- Pay-per-second (perfekt für test/beta)
- Wenn Traffic wächst → einfach zu App Service upgraden

---

## 3. COMPLETE LEAN MVP STACK (AZURE)

### 3.1 Services & Kosten (Monatlich)

| Service | Cost | Beschreibung |
|---------|------|-------------|
| **Azure Container Instances** | €50-100 | 2-4 Container, CPU/Memory |
| **Azure Container Registry** | €7 | Docker Image Storage |
| **Azure Database PostgreSQL** | €15-30 | Single Server, 10GB Storage |
| **Azure Blob Storage** | €1-5 | File Storage (cheaper than S3) |
| **Azure Storage Queue** | €0.50 | Optional: Job Queue (alternative zu Redis) |
| **Azure App Configuration** | Free | Config Management (Secrets, Settings) |
| **Application Insights** | €2-5 | Error Tracking & Monitoring |
| **DNS/Custom Domain** | €0-5 | Optional: Custom domain |
| **Total Azure Infrastructure** | **€75-150/Monat** | |
| **OpenAI API** | €0.20-1.50/CV | Variable (600 CVs/Jahr = ~€1000) |
| **TOTAL MVP/MONAT** | **€75-150 + OpenAI** | |

### 3.2 Vergleich: Azure vs. Heroku vs. AWS

| Kriterium | Heroku | Azure ACI | AWS ECS |
|-----------|--------|----------|---------|
| **Setup Time** | 10 min | 30 min | 1+ Stunde |
| **Monthly Cost** | €50-100 | €75-150 | €100-200 |
| **Scaling** | Automatic | Manual | Automatic |
| **Database** | Heroku PG €9-50 | Azure DB €15-30 | RDS €30-50 |
| **Total/Monat** | €70-150 | €100-180 | €150-250 |
| **Complexity** | Very Low | Low | Medium |
| **Azure Integration** | ❌ | ✅ | ❌ |
| **Best For** | Small startups | Azure shops | Large scale |

**Fazit:** Azure ist **middle ground** - nicht am billigsten, aber integriert gut in Microsoft-Umgebungen.

---

## 4. AZURE MVP DEPLOYMENT ARCHITEKTUR

### 4.1 Complete Setup Diagram

```yaml
┌─ DEVELOPMENT ───────────────────────────────┐
│ Local Docker Build                          │
│ docker build -t cv-generator:latest .       │
└─────────────────┬──────────────────────────┘
                  │
┌─────────────────────────────────────────────┐
│ Azure Container Registry (ACR)              │
│ (Private Docker Image Storage)              │
│ URL: myregistry.azurecr.io                  │
└─────────────────┬──────────────────────────┘
                  │
┌─────────────────────────────────────────────┐
│ Azure Container Instances (ACI)             │
│ ├─ Web Container (Streamlit + FastAPI)      │
│ │   Port 8501 (Streamlit)                   │
│ │   Port 8000 (FastAPI)                     │
│ │   €50-100/Monat                           │
│ │   Environment Variables:                  │
│ │   ├─ DB_HOST                              │
│ │   ├─ DB_PASSWORD (from Key Vault)         │
│ │   ├─ OPENAI_API_KEY (from Key Vault)      │
│ │   └─ LOG_LEVEL                            │
│ │                                            │
│ └─ Restart Policy: On Failure               │
│    (Auto-restart bei Crash)                 │
└─────────────────┬──────────────────────────┘
      │           │           │
      ↓           ↓           ↓
   DB      Blob Storage   App Insights
```

### 4.2 Komponenten im Detail

#### A. Azure Container Registry (ACR) - Image Speicherung
```yaml
Resource:
  Name: myregistry
  Tier: Basic (€7/Monat, 10GB storage)
  Location: West Europe (oder regional)

Authentication:
  - Admin Keys (einfach für MVP)
  - Service Principal (später für CI/CD)

Usage:
  docker push myregistry.azurecr.io/cv-generator:latest
  az acr build --registry myregistry --image cv-generator:latest .
```

#### B. Azure Container Instances (ACI) - Runtime
```yaml
Resource:
  Name: cv-generator-container
  Image: myregistry.azurecr.io/cv-generator:latest
  CPU: 1 vCore
  Memory: 1.5 GB
  Ports:
    - 8501/tcp (Streamlit)
    - 8000/tcp (FastAPI)
  
Restart Policy: Always (auto-restart on crash)
Cost: ~€0.000011/second = €30-50/Monat bei ~50% utilization

Environment Variables (from Key Vault):
  DATABASE_URL: postgresql://user:pass@mydb.postgres.database.azure.com/cvdb
  OPENAI_API_KEY: sk-proj-xxx
  LOG_LEVEL: INFO
```

#### C. Azure Database for PostgreSQL - Data Storage
```yaml
Resource:
  Server Name: mydbserver
  Tier: Basic (€15-30/Monat)
  
Compute:
  vCore: 1 (B-series burstable)
  Memory: 2GB
  Storage: 50GB (included)
  
Connections:
  Max: 260 (overkill for MVP)
  
Security:
  - Firewall Rules (allow from ACI subnet)
  - SSL enforced
  - Backups: Daily (7-day retention)
  - Geo-redundant optional (€+5)

Database:
  Name: cvdb
  User: cvadmin
  Tables:
    - job_metadata (JSON metadata)
    - file_storage (BYTEA for PDFs/Word)
    - audit_logs (simple logging)
```

#### D. Azure Blob Storage - File Management
```yaml
Resource:
  Type: General Purpose v2
  Tier: Hot (frequent access)
  Replication: LRS (Locally Redundant)
  Cost: €1-5/Monat (cheap!)

Containers:
  - pdf-uploads/
    ├─ Active PDFs (next 30 days)
    └─ Cleanup: Auto-delete after 30 days
  
  - outputs/
    ├─ Generated Word documents
    └─ Cleanup: After user download (or 30 days)
  
  - archives/
    ├─ Compressed old files
    └─ Tier: Cool (cheaper, slower access)

Access:
  - SAS URLs for download (time-limited)
  - Managed Identity (no storage keys in code)
```

#### E. Azure Key Vault - Secrets Management
```yaml
Resource:
  Name: myvault
  Tier: Standard (free for MVP)

Secrets Stored:
  - db-password
  - openai-api-key
  - admin-password (for Streamlit)

Access:
  - Container Identity (no credentials in code)
  - Via Azure RBAC
  
Benefits:
  - No hardcoded secrets
  - Audit logging
  - Rotation support
```

#### F. Application Insights - Monitoring
```yaml
Resource:
  Type: Application Insights
  Tier: Free (€0) for MVP
  
Tracking:
  - App requests
  - Exceptions & errors
  - Performance metrics
  - Custom events
  
Integration:
  - Python SDK (pip install azure-monitor-opentelemetry)
  - Auto-instrument FastAPI & Streamlit
```

---

## 5. DEPLOYMENT PROZESS (STEP-BY-STEP)

### 5.1 Initial Setup (One-Time)
```bash
# 1. Create Resource Group
az group create --name cv-generator-rg --location westeurope

# 2. Create Container Registry
az acr create --resource-group cv-generator-rg \
  --name cvgenerator --sku Basic

# 3. Create PostgreSQL Database
az postgres server create \
  --resource-group cv-generator-rg \
  --name cvdb-server \
  --location westeurope \
  --admin-user cvadmin \
  --admin-password MySecurePass123! \
  --sku-name B_Gen5_1 \
  --storage-size 51200

# 4. Create Key Vault
az keyvault create --resource-group cv-generator-rg \
  --name cvvault \
  --location westeurope

# 5. Add Secrets to Key Vault
az keyvault secret set --vault-name cvvault \
  --name db-password --value MySecurePass123!
az keyvault secret set --vault-name cvvault \
  --name openai-api-key --value sk-proj-xxx

# 6. Create Storage Account
az storage account create --resource-group cv-generator-rg \
  --name cvfiles --location westeurope \
  --sku Standard_LRS
```

### 5.2 Application Deployment
```bash
# 1. Build Docker Image Locally
docker build -t cvgenerator.azurecr.io/cv-generator:v1.0 .
docker login cvgenerator.azurecr.io -u <username> -p <password>
docker push cvgenerator.azurecr.io/cv-generator:v1.0

# OR: Use ACR Build (build in cloud)
az acr build --registry cvgenerator \
  --image cv-generator:v1.0 .

# 2. Deploy to Container Instances
az container create \
  --resource-group cv-generator-rg \
  --name cv-app \
  --image cvgenerator.azurecr.io/cv-generator:v1.0 \
  --cpu 1 --memory 1.5 \
  --registry-login-server cvgenerator.azurecr.io \
  --registry-username <username> \
  --registry-password <password> \
  --ports 8501 8000 \
  --environment-variables \
    DATABASE_URL="postgresql://cvadmin:MySecurePass123!@cvdb-server.postgres.database.azure.com:5432/cvdb" \
    OPENAI_API_KEY="sk-proj-xxx" \
    LOG_LEVEL="INFO" \
  --restart-policy Always
```

### 5.3 CI/CD Pipeline (Optional für MVP, aber empfohlen)

**GitHub Actions + Azure DevOps:**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Azure ACI

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build & Push to ACR
        run: |
          az acr build --registry cvgenerator \
            --image cv-generator:${{ github.sha }} .
      
      - name: Update ACI
        run: |
          az container create \
            --resource-group cv-generator-rg \
            --name cv-app \
            --image cvgenerator.azurecr.io/cv-generator:${{ github.sha }} \
            ... (rest of parameters)
```

---

## 6. KOSTEN-VERGLEICH: HEROKU vs. AZURE

### 6.1 Year 1 Kostenübersicht

```
╔════════════════════════════════════════════════════╗
║ HEROKU Lean MVP                                    ║
╠════════════════════════════════════════════════════╣
║ Development:        €10,000 (einmalig)             ║
║ Heroku Dyno:        €500 × 12 = €6,000            ║
║ PostgreSQL:         €180 × 12 = €2,160            ║
║ OpenAI API:         ~€5,000 (600 CVs × €8)        ║
║ ────────────────────────────────────────────────   ║
║ TOTAL YEAR 1:       €23,160                       ║
║ YEAR 2+:            €13,160/Jahr                   ║
╚════════════════════════════════════════════════════╝

╔════════════════════════════════════════════════════╗
║ AZURE Lean MVP                                     ║
╠════════════════════════════════════════════════════╣
║ Development:        €10,000 (einmalig)             ║
║ ACI + ACR:          €1,200 × 12 = €1,200          ║
║ PostgreSQL:         €300 × 12 = €3,600            ║
║ Blob Storage:       €60 × 12 = €720               ║
║ App Insights:       €60 × 12 = €720               ║
║ OpenAI API:         ~€5,000 (600 CVs × €8)        ║
║ ────────────────────────────────────────────────   ║
║ TOTAL YEAR 1:       €20,840                       ║
║ YEAR 2+:            €10,840/Jahr                   ║
╚════════════════════════════════════════════════════╝

╔════════════════════════════════════════════════════╗
║ AWS Lean MVP (ECS)                                 ║
╠════════════════════════════════════════════════════╣
║ Development:        €10,000 (einmalig)             ║
║ ECS Fargate:        €1,500 × 12 = €1,500          ║
║ RDS PostgreSQL:     €450 × 12 = €5,400            ║
║ S3 Storage:         €120 × 12 = €1,440            ║
║ CloudWatch:         €240 × 12 = €240              ║
║ OpenAI API:         ~€5,000 (600 CVs × €8)        ║
║ ────────────────────────────────────────────────   ║
║ TOTAL YEAR 1:       €23,580                       ║
║ YEAR 2+:            €13,580/Jahr                   ║
╚════════════════════════════════════════════════════╝

WINNER: AZURE (if you have existing subscription)
- €2,320 cheaper in Year 1
- €2,320 cheaper per Year after
```

### 6.2 Break-Even Analyse

```
Wenn Azure schon vorhanden:
├─ Incremental cost (nur infrastructure): €1,200/Monat
├─ vs. Heroku: €500/Monat
└─ Zusatz für Azure: €700/Monat (für bessere Integration)

Wenn Azure nicht vorhanden:
├─ Heroku: Günstiger Einstieg
└─ Azure: Besser wenn IT-Stack vorhanden
```

---

## 7. AZURE ARCHITECTURE DECISIONS

### 7.1 PostgreSQL: Single Server vs. Flexible Server
```
SINGLE SERVER (EMPFOHLEN für MVP)
├─ Cost: €15-30/Monat
├─ Verwaltung: Minimal
├─ Storage: Included
├─ Backups: Automatic (7 days)
└─ Skalierung: Easy vertical scaling

FLEXIBLE SERVER
├─ Cost: €20-50/Monat
├─ Verwaltung: Mehr Optionen
├─ HA: Availability zones
├─ Features: Mehr advanced
└─ Best für: Production later

→ MVP: Single Server, später upgrade zu Flexible
```

### 7.2 Storage: Blob vs. Database
```
PostgreSQL BYTEA:
├─ Pros: Transactionen, ACID
├─ Cons: Backup-Größe wächst
├─ Best für: <1GB total

Azure Blob Storage:
├─ Pros: Billig, unbegrenzt
├─ Cons: Eventual consistency
├─ Best für: Large files, archives

EMPFEHLUNG für MVP:
├─ Active files (30 Tage): PostgreSQL
├─ Archives (>30 Tage): Blob Storage
└─ Hybrid approach (optimal)
```

### 7.3 Container: ACI vs. App Service vs. Kubernetes
```
ACI (EMPFOHLEN für MVP)
├─ Cost: €50-100/Monat
├─ Setup: 30 min
├─ Scaling: Manual
├─ Best für: MVP, Batch jobs

App Service
├─ Cost: €15-50/Monat
├─ Setup: 10 min
├─ Scaling: Auto (included)
├─ Best für: Production
├─ Upgrade path: ACI → App Service

AKS (Kubernetes)
├─ Cost: €100+/Monat
├─ Setup: Hours
├─ Scaling: Full auto
├─ Best für: Enterprise

MVP → App Service Phase 2 (easy migration)
```

---

## 8. SICHERHEIT IN AZURE

### 8.1 Best Practices (MVP)
```
✅ Secrets Management:
  ├─ Azure Key Vault (nicht im Code!)
  ├─ Managed Identity (kein hardcoded credentials)
  └─ Automatic rotation support

✅ Network Security:
  ├─ Firewall rules (restrict PostgreSQL access)
  ├─ NSG (Network Security Groups)
  └─ Private Endpoints (optional später)

✅ Data Protection:
  ├─ HTTPS/TLS everywhere
  ├─ Database backups (automatic)
  ├─ Blob Storage encryption (automatic)
  └─ RBAC (Role-Based Access Control)

✅ Compliance:
  ├─ Activity Logs (audit all actions)
  ├─ GDPR: Automatic retention policies
  └─ Encryption: At-rest + in-transit
```

### 8.2 Azure AD Integration (Bonus für Enterprise)
```
Falls ihr Microsoft Enterprise nutzt:

├─ Single Sign-On (SSO)
│  └─ Nutzer loggt sich mit Unternehmens-Konto ein
│
├─ Multi-Factor Authentication (MFA)
│  └─ Automatisch wenn corporate policy
│
└─ Access Control
   └─ Automatisch via Azure AD groups

Implementation für FastAPI:
from fastapi import Depends, HTTPException
from azure.identity import DefaultAzureCredential
from microsoft.graph import GraphServiceClient

async def verify_token(token: str = Header(...)):
    # Verify token gegen Azure AD
    ...
```

---

## 9. MONITORING & LOGGING IN AZURE

### 9.1 Application Insights
```yaml
Resource: Application Insights
Included:
  ├─ Request tracing
  ├─ Exception tracking
  ├─ Performance metrics
  ├─ Dependency tracking (DB, APIs)
  └─ Custom events

Integration (Python):
from azure.monitor.opentelemetry import configure_azure_monitor
configure_azure_monitor()

# Automatic tracking of:
# - FastAPI requests
# - PostgreSQL queries
# - External API calls (OpenAI)
```

### 9.2 Logs
```yaml
Options:
1. Application Insights (easiest for MVP)
2. Azure Monitor Logs (advanced, mehr features)
3. Storage Account (long-term archive)

MVP: Nur Application Insights (free)
```

---

## 10. DEPLOYMENT CHECKLIST

```
┌─ INFRASTRUCTURE (Day 1) ─────────────┐
│ ☐ Create Resource Group              │
│ ☐ Create Container Registry          │
│ ☐ Create PostgreSQL Database         │
│ ☐ Create Blob Storage Account        │
│ ☐ Create Key Vault                   │
│ ☐ Store Secrets in Key Vault         │
│ ☐ Create Application Insights        │
└──────────────────────────────────────┘

┌─ DOCKER IMAGE (Day 2) ───────────────┐
│ ☐ Dockerfile erstellen               │
│ ☐ docker build lokal testen          │
│ ☐ docker push zu ACR                 │
└──────────────────────────────────────┘

┌─ DEPLOYMENT (Day 2-3) ───────────────┐
│ ☐ Deploy to ACI                      │
│ ☐ Test connectivity (Streamlit/API)  │
│ ☐ Database migrations runnen         │
│ ☐ SSL/TLS setup (optional: custom domain)│
│ ☐ Backup testing                     │
└──────────────────────────────────────┘

┌─ CI/CD OPTIONAL (Day 4) ─────────────┐
│ ☐ GitHub Actions workflow            │
│ ☐ Auto-build on push                 │
│ ☐ Auto-deploy to ACI                 │
└──────────────────────────────────────┘
```

---

## 11. AZURE MVP TIMELINE

```
WEEK 1: Infrastructure & Deployment
├─ Day 1: Resource Group, Registry, Database, Storage Setup
├─ Day 2: Docker image build & push
├─ Day 3: ACI deployment & testing
└─ Day 4-5: Bug fixes & optimization

WEEK 2: Integration & Testing
├─ Day 1: Streamlit + FastAPI integration
├─ Day 2: Database migrations
├─ Day 3: OpenAI pipeline testing
├─ Day 4: End-to-end testing
└─ Day 5: Beta launch

TOTAL: 10 Arbeitstage (~2 Wochen)
```

---

## 12. AZURE vs. HEROKU: DECISION MATRIX

| Faktor | Heroku | Azure | Winner |
|--------|--------|-------|--------|
| **Setup Time** | 10 min | 30 min | Heroku |
| **Lernkurve** | Sehr einfach | Einfach | Heroku |
| **Cost (Year 1)** | €23k | €21k | Azure |
| **Scaling (later)** | Easy | Easy | Tie |
| **Microsoft Integration** | ❌ | ✅ | Azure |
| **SSO/AD Support** | ❌ | ✅ | Azure |
| **GDPR/Compliance** | ✅ | ✅✅ | Azure |
| **Monitoring** | Basic | Good | Azure |
| **Support** | Good | Excellent | Azure |

**ENTSCHEIDUNG:**
```
IF you have Azure subscription:
  → USE AZURE (save €2-3k/Jahr, better integration)

ELSE IF you want simplicity:
  → USE HEROKU (easier setup, still cheap)

ELSE IF you have AWS:
  → USE AWS (but pricier than Azure)
```

---

## 13. BEISPIEL DOCKERFILE (für Azure Deployment)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Environment for Azure
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Health check for ACI
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8501')" || exit 1

# Run both Streamlit and FastAPI
CMD sh -c "streamlit run app.py --server.port=8501 &  uvicorn scripts.streamlit_pipeline:app --host 0.0.0.0 --port 8000"
```

---

## 14. BEISPIEL: AZURE DEPLOYMENT SCRIPT

```bash
#!/bin/bash
# azure-deploy.sh - One-command deployment

set -e

RESOURCE_GROUP="cv-generator-rg"
LOCATION="westeurope"
REGISTRY_NAME="cvgenerator"
ACR_REGISTRY="${REGISTRY_NAME}.azurecr.io"
IMAGE_NAME="cv-generator"
IMAGE_TAG="v1.0"
CONTAINER_NAME="cv-app"

echo "🚀 Deploying CV Generator to Azure..."

# 1. Login to Azure
echo "1️⃣ Logging in to Azure..."
az login

# 2. Create Resource Group
echo "2️⃣ Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# 3. Create Container Registry
echo "3️⃣ Creating container registry..."
az acr create --resource-group $RESOURCE_GROUP \
  --name $REGISTRY_NAME --sku Basic

# 4. Create PostgreSQL
echo "4️⃣ Creating PostgreSQL database..."
az postgres server create \
  --resource-group $RESOURCE_GROUP \
  --name cvdb-server \
  --location $LOCATION \
  --admin-user cvadmin \
  --admin-password $(openssl rand -base64 16) \
  --sku-name B_Gen5_1

# 5. Build and push image
echo "5️⃣ Building and pushing Docker image..."
az acr build --registry $REGISTRY_NAME \
  --image ${IMAGE_NAME}:${IMAGE_TAG} \
  --image ${IMAGE_NAME}:latest .

# 6. Deploy to ACI
echo "6️⃣ Deploying to Container Instances..."
az container create \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --image ${ACR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} \
  --cpu 1 --memory 1.5 \
  --registry-login-server $ACR_REGISTRY \
  --registry-username $(az acr credential show --resource-group $RESOURCE_GROUP --name $REGISTRY_NAME --query "username" -o tsv) \
  --registry-password $(az acr credential show --resource-group $RESOURCE_GROUP --name $REGISTRY_NAME --query "passwords[0].value" -o tsv) \
  --ports 8501 8000 \
  --restart-policy Always

echo "✅ Deployment complete!"
echo "📊 Streamlit: http://$(az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query ipAddress.fqdn -o tsv):8501"
echo "🔌 FastAPI: http://$(az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query ipAddress.fqdn -o tsv):8000"
```

---

## 15. NÄCHSTE SCHRITTE

### Für Meeting mit Architekt:

1. **Präsentieren:** Lean MVP on Azure Optionen
2. **Kosten zeigen:** €20,840 Year 1 (vs. €23k Heroku, €23.5k AWS)
3. **Timeline:** 2 Wochen Development
4. **Fragen klären:**
   - Habt ihr bereits Azure Subscription?
   - Braucht ihr Azure AD Integration?
   - Microsoft Compliance wichtig?

### Quick Decision Tree:
```
Do you have Azure subscription? 
├─ YES  → Use AZURE (better integration, lower cost)
└─ NO   → Use HEROKU (simpler setup)

Need production-grade?
├─ YES  → Upgrade to App Service (easy migration)
└─ NO   → Keep ACI (cheaper, pay-per-second)

Need Auto-scaling?
├─ YES  → Use App Service or Kubernetes
└─ NO   → ACI is fine for MVP
```

---

## 16. RESOURCE LINKS

**Azure CLI Installation:**
```bash
# Windows
choco install azure-cli

# macOS
brew install azure-cli

# Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

**Useful Commands:**
```bash
# Login
az login

# List resources
az resource list --resource-group cv-generator-rg

# Tail logs
az container logs --resource-group cv-generator-rg --name cv-app -f

# Update container
az container restart --resource-group cv-generator-rg --name cv-app
```

**Microsoft Docs:**
- Azure Container Instances: https://docs.microsoft.com/azure/container-instances/
- Azure Database PostgreSQL: https://docs.microsoft.com/azure/postgresql/
- Azure Storage: https://docs.microsoft.com/azure/storage/
- Application Insights: https://docs.microsoft.com/azure/azure-monitor/app/app-insights-overview

---

## ZUSAMMENFASSUNG

```
┌──────────────────────────────────────────────┐
│ AZURE LEAN MVP EMPFEHLUNG                    │
├──────────────────────────────────────────────┤
│ ✅ Timeline: 2 Wochen Development            │
│ ✅ Cost: €20,840 Year 1 (€10,840 Year 2+)    │
│ ✅ Scaling: Einfach zu App Service later      │
│ ✅ Microsoft Integration: Full support        │
│ ✅ Security: Enterprise-grade                 │
│ ✅ Compliance: GDPR + Azure built-in         │
│                                              │
│ 🎯 Start: ACI (pay-per-second)              │
│ 📈 Phase 2: Upgrade to App Service          │
│ 🔄 Phase 3: Add Kubernetes if needed         │
└──────────────────────────────────────────────┘
```

---

**Dokument erstellt**: Januar 2026  
**Für**: Architecture Meeting - Azure Option  
**Status**: Ready for Discussion
