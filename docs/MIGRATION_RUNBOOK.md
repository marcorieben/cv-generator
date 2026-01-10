# Migration Runbook - Serverless CV Generator

**Target**: AWS Lambda + API Gateway + S3 + DynamoDB
**Timeline**: 12 weeks
**Risk Level**: Medium (requires blue-green deployment strategy)

---

## Prerequisites

### 1. AWS Account Setup
```bash
# Install AWS CLI
brew install awscli  # macOS
# or
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

# Configure credentials
aws configure
# AWS Access Key ID: <your-key>
# AWS Secret Access Key: <your-secret>
# Default region: us-east-1
# Default output format: json

# Verify access
aws sts get-caller-identity
```

### 2. Required Tools
```bash
# Docker (for Lambda containers)
docker --version  # 24.0+

# Terraform (IaC for AWS resources)
brew install terraform  # or download from terraform.io
terraform --version  # 1.7+

# Node.js (for Next.js frontend)
node --version  # 18.0+
npm install -g pnpm  # Faster than npm
```

### 3. Cost Budget Setup
```bash
# Set up AWS Budget alert
aws budgets create-budget \
  --account-id 123456789012 \
  --budget file://budget.json

# budget.json
{
  "BudgetName": "cv-generator-monthly",
  "BudgetLimit": {
    "Amount": "100",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
```

---

## Phase 1: Infrastructure as Code (Week 1)

### 1.1 Create Terraform Project

```bash
mkdir -p infrastructure/terraform
cd infrastructure/terraform
```

**File: `main.tf`**
```hcl
terraform {
  required_version = ">= 1.7"

  backend "s3" {
    bucket = "cv-generator-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "cv-generator"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# DynamoDB Table: cv-metadata
resource "aws_dynamodb_table" "cv_metadata" {
  name           = "cv-metadata-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"  # On-demand pricing
  hash_key       = "jobId"

  attribute {
    name = "jobId"
    type = "S"
  }

  attribute {
    name = "userId"
    type = "S"
  }

  global_secondary_index {
    name            = "UserIdIndex"
    hash_key        = "userId"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name = "CV Metadata Table"
  }
}

# S3 Bucket: cv-uploads
resource "aws_s3_bucket" "cv_uploads" {
  bucket = "cv-generator-uploads-${var.environment}"

  tags = {
    Name = "CV Uploads"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "cv_uploads_lifecycle" {
  bucket = aws_s3_bucket.cv_uploads.id

  rule {
    id     = "delete-old-uploads"
    status = "Enabled"

    expiration {
      days = 7
    }
  }
}

resource "aws_s3_bucket_cors_configuration" "cv_uploads_cors" {
  bucket = aws_s3_bucket.cv_uploads.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "POST"]
    allowed_origins = ["https://cv-generator.com"]
    max_age_seconds = 3000
  }
}

# S3 Bucket: cv-outputs
resource "aws_s3_bucket" "cv_outputs" {
  bucket = "cv-generator-outputs-${var.environment}"
}

resource "aws_s3_bucket_lifecycle_configuration" "cv_outputs_lifecycle" {
  bucket = aws_s3_bucket.cv_outputs.id

  rule {
    id     = "archive-old-outputs"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }
}

# SQS Queue: cv-processing
resource "aws_sqs_queue" "cv_processing" {
  name                       = "cv-processing-${var.environment}"
  visibility_timeout_seconds = 300  # 5 minutes (Lambda max timeout)
  message_retention_seconds  = 86400  # 24 hours

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.cv_processing_dlq.arn
    maxReceiveCount     = 3
  })
}

resource "aws_sqs_queue" "cv_processing_dlq" {
  name = "cv-processing-dlq-${var.environment}"
}

# SNS Topic: cv-extracted
resource "aws_sns_topic" "cv_extracted" {
  name = "cv-extracted-${var.environment}"
}

# ElastiCache Redis: cv-cache
resource "aws_elasticache_cluster" "cv_cache" {
  cluster_id           = "cv-cache-${var.environment}"
  engine               = "redis"
  node_type            = "cache.t4g.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379
}

# Secrets Manager: OpenAI API Key
resource "aws_secretsmanager_secret" "openai_api_key" {
  name        = "cv-generator/openai-api-key-${var.environment}"
  description = "OpenAI API Key for CV extraction"

  tags = {
    Name = "OpenAI API Key"
  }
}

# Output important ARNs
output "cv_metadata_table_name" {
  value = aws_dynamodb_table.cv_metadata.name
}

output "cv_uploads_bucket" {
  value = aws_s3_bucket.cv_uploads.id
}

output "cv_outputs_bucket" {
  value = aws_s3_bucket.cv_outputs.id
}

output "cv_processing_queue_url" {
  value = aws_sqs_queue.cv_processing.url
}

output "redis_endpoint" {
  value = aws_elasticache_cluster.cv_cache.cache_nodes[0].address
}
```

**File: `variables.tf`**
```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}
```

**Deploy Infrastructure**:
```bash
# Initialize Terraform
terraform init

# Plan deployment
terraform plan -out=tfplan

# Apply (create resources)
terraform apply tfplan

# Save outputs
terraform output -json > outputs.json
```

**Cost Estimate**: ~$15-20/month (ElastiCache is the main cost)

---

## Phase 2: Lambda Functions (Week 2-4)

### 2.1 Project Structure

```bash
lambda_functions/
├── cv-extractor/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── handler.py
│   └── scripts/
│       └── pdf_to_json.py  # Copied from existing project
├── cv-generator/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── handler.py
│   └── scripts/
│       └── generate_cv.py
├── matcher/
├── feedback/
├── offer-generator/
└── dashboard-builder/
```

### 2.2 Example: cv-extractor Lambda

**File: `lambda_functions/cv-extractor/Dockerfile`**
```dockerfile
FROM public.ecr.aws/lambda/python:3.11

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy application code
COPY handler.py ${LAMBDA_TASK_ROOT}/
COPY scripts/ ${LAMBDA_TASK_ROOT}/scripts/

# Set handler
CMD ["handler.lambda_handler"]
```

**File: `lambda_functions/cv-extractor/requirements.txt`**
```txt
openai>=2.14.0
pypdf>=6.5.0
boto3>=1.34.0
redis>=5.0.0
```

**File: `lambda_functions/cv-extractor/handler.py`**
```python
import json
import os
import boto3
import hashlib
import redis
from openai import OpenAI
from scripts.pdf_to_json import extract_text_from_pdf, load_schema

# Initialize AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
secrets_client = boto3.client('secretsmanager')
sns = boto3.client('sns')

# Get configuration from environment
TABLE_NAME = os.environ['CV_METADATA_TABLE']
UPLOADS_BUCKET = os.environ['CV_UPLOADS_BUCKET']
OUTPUTS_BUCKET = os.environ['CV_OUTPUTS_BUCKET']
SNS_TOPIC_ARN = os.environ['CV_EXTRACTED_TOPIC_ARN']
REDIS_URL = os.environ['REDIS_URL']

# Initialize Redis
redis_client = redis.from_url(REDIS_URL)

# Cache OpenAI client (reuse across invocations)
_openai_client = None

def get_openai_client():
    global _openai_client
    if _openai_client is None:
        # Get API key from Secrets Manager
        secret_response = secrets_client.get_secret_value(
            SecretId='cv-generator/openai-api-key'
        )
        api_key = json.loads(secret_response['SecretString'])['api_key']
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client

def get_cached_extraction(content_hash: str) -> dict | None:
    """Check Redis cache for previous extraction"""
    cached = redis_client.get(f'cv:extraction:{content_hash}')
    if cached:
        print(f"Cache HIT for {content_hash[:8]}...")
        return json.loads(cached)
    return None

def cache_extraction(content_hash: str, cv_json: dict):
    """Store extraction result in Redis (30-day TTL)"""
    redis_client.setex(
        f'cv:extraction:{content_hash}',
        86400 * 30,  # 30 days
        json.dumps(cv_json)
    )

def lambda_handler(event, context):
    """
    Triggered by SQS message from upload-handler
    Extracts CV data from PDF using OpenAI
    """
    for record in event['Records']:
        # Parse SQS message
        body = json.loads(record['body'])
        job_id = body['jobId']
        language = body.get('language', 'de')

        print(f"Processing job {job_id} (language: {language})")

        # Update status in DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET #status = :status, step = :step',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'processing',
                ':step': 'pdf_extraction'
            }
        )

        try:
            # Download PDF from S3
            pdf_obj = s3.get_object(
                Bucket=UPLOADS_BUCKET,
                Key=f'{job_id}/input.pdf'
            )
            pdf_content = pdf_obj['Body'].read()

            # Check cache first
            content_hash = hashlib.sha256(pdf_content).hexdigest()
            cv_json = get_cached_extraction(content_hash)

            if cv_json is None:
                # Extract text from PDF
                cv_text = extract_text_from_pdf(pdf_content)

                # Load schema
                schema = load_schema()

                # Call OpenAI
                client = get_openai_client()
                response = client.chat.completions.create(
                    model=os.getenv('MODEL_NAME', 'gpt-4o-mini'),
                    messages=[
                        {"role": "system", "content": f"Extract CV data in {language}..."},
                        {"role": "user", "content": cv_text}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0
                )

                cv_json = json.loads(response.choices[0].message.content)

                # Cache result
                cache_extraction(content_hash, cv_json)

            # Save JSON to S3
            s3.put_object(
                Bucket=OUTPUTS_BUCKET,
                Key=f'{job_id}/cv_data.json',
                Body=json.dumps(cv_json, ensure_ascii=False, indent=2),
                ContentType='application/json'
            )

            # Update DynamoDB
            table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET step = :step, outputs.cv_json = :url',
                ExpressionAttributeValues={
                    ':step': 'cv_extracted',
                    ':url': f's3://{OUTPUTS_BUCKET}/{job_id}/cv_data.json'
                }
            )

            # Trigger next steps via SNS (fan-out)
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=json.dumps({
                    'jobId': job_id,
                    'language': language,
                    'cv_json_s3': f's3://{OUTPUTS_BUCKET}/{job_id}/cv_data.json'
                })
            )

            print(f"✅ Successfully processed job {job_id}")

        except Exception as e:
            print(f"❌ Error processing job {job_id}: {str(e)}")

            # Update DynamoDB with error
            table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET #status = :status, errorMessage = :error',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'failed',
                    ':error': str(e)
                }
            )

            raise  # Let Lambda retry via SQS DLQ

    return {'statusCode': 200}
```

### 2.3 Deploy Lambda Function

**Build and Push Docker Image**:
```bash
cd lambda_functions/cv-extractor

# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Create ECR repository
aws ecr create-repository --repository-name cv-extractor --region us-east-1

# Build Docker image
docker build -t cv-extractor:latest .

# Tag for ECR
docker tag cv-extractor:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/cv-extractor:latest

# Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/cv-extractor:latest
```

**Create Lambda Function** (Terraform):
```hcl
# infrastructure/terraform/lambda.tf

resource "aws_lambda_function" "cv_extractor" {
  function_name = "cv-extractor-${var.environment}"
  role          = aws_iam_role.lambda_execution.arn

  package_type  = "Image"
  image_uri     = "123456789012.dkr.ecr.us-east-1.amazonaws.com/cv-extractor:latest"

  memory_size = 512
  timeout     = 120

  environment {
    variables = {
      CV_METADATA_TABLE      = aws_dynamodb_table.cv_metadata.name
      CV_UPLOADS_BUCKET      = aws_s3_bucket.cv_uploads.id
      CV_OUTPUTS_BUCKET      = aws_s3_bucket.cv_outputs.id
      CV_EXTRACTED_TOPIC_ARN = aws_sns_topic.cv_extracted.arn
      REDIS_URL              = "redis://${aws_elasticache_cluster.cv_cache.cache_nodes[0].address}:6379"
      MODEL_NAME             = "gpt-4o-mini"
    }
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }
}

# SQS Trigger
resource "aws_lambda_event_source_mapping" "cv_extractor_sqs" {
  event_source_arn = aws_sqs_queue.cv_processing.arn
  function_name    = aws_lambda_function.cv_extractor.arn
  batch_size       = 1
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_execution" {
  name = "cv-lambda-execution-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_policy" "lambda_cv_access" {
  name = "cv-lambda-access-${var.environment}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          "${aws_s3_bucket.cv_uploads.arn}/*",
          "${aws_s3_bucket.cv_outputs.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = aws_dynamodb_table.cv_metadata.arn
      },
      {
        Effect = "Allow"
        Action = "secretsmanager:GetSecretValue"
        Resource = aws_secretsmanager_secret.openai_api_key.arn
      },
      {
        Effect = "Allow"
        Action = "sns:Publish"
        Resource = aws_sns_topic.cv_extracted.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_cv_access" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.lambda_cv_access.arn
}
```

**Deploy**:
```bash
cd infrastructure/terraform
terraform apply
```

---

## Phase 3: API Gateway (Week 5)

### 3.1 Create REST API

**File: `infrastructure/terraform/api_gateway.tf`**
```hcl
resource "aws_api_gateway_rest_api" "cv_api" {
  name        = "cv-generator-api-${var.environment}"
  description = "CV Generator REST API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

# /api/v1/cv/upload
resource "aws_api_gateway_resource" "upload" {
  rest_api_id = aws_api_gateway_rest_api.cv_api.id
  parent_id   = aws_api_gateway_rest_api.cv_api.root_resource_id
  path_part   = "upload"
}

resource "aws_api_gateway_method" "upload_post" {
  rest_api_id   = aws_api_gateway_rest_api.cv_api.id
  resource_id   = aws_api_gateway_resource.upload.id
  http_method   = "POST"
  authorization = "AWS_IAM"  # Use Cognito in production

  request_parameters = {
    "method.request.header.Content-Type" = true
  }
}

resource "aws_api_gateway_integration" "upload_lambda" {
  rest_api_id = aws_api_gateway_rest_api.cv_api.id
  resource_id = aws_api_gateway_resource.upload.id
  http_method = aws_api_gateway_method.upload_post.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.upload_handler.invoke_arn
}

# Deploy API
resource "aws_api_gateway_deployment" "cv_api_deployment" {
  depends_on = [
    aws_api_gateway_integration.upload_lambda
  ]

  rest_api_id = aws_api_gateway_rest_api.cv_api.id
  stage_name  = var.environment
}

output "api_endpoint" {
  value = "${aws_api_gateway_deployment.cv_api_deployment.invoke_url}"
}
```

### 3.2 Create upload-handler Lambda

**File: `lambda_functions/upload-handler/handler.py`**
```python
import json
import uuid
import boto3
from datetime import datetime

s3 = boto3.client('s3')
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

UPLOADS_BUCKET = os.environ['CV_UPLOADS_BUCKET']
SQS_QUEUE_URL = os.environ['CV_PROCESSING_QUEUE_URL']
TABLE_NAME = os.environ['CV_METADATA_TABLE']

def lambda_handler(event, context):
    """
    API Gateway endpoint for CV upload
    """
    # Parse request
    if event.get('isBase64Encoded'):
        import base64
        pdf_content = base64.b64decode(event['body'])
    else:
        pdf_content = event['body'].encode()

    # Validate PDF (basic check)
    if not pdf_content.startswith(b'%PDF'):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid PDF file'})
        }

    # Generate job ID
    job_id = str(uuid.uuid4())
    language = event.get('queryStringParameters', {}).get('language', 'de')

    # Upload to S3
    s3.put_object(
        Bucket=UPLOADS_BUCKET,
        Key=f'{job_id}/input.pdf',
        Body=pdf_content,
        ContentType='application/pdf'
    )

    # Create metadata record
    table = dynamodb.Table(TABLE_NAME)
    table.put_item(Item={
        'jobId': job_id,
        'userId': 'anonymous',  # Replace with Cognito user ID
        'status': 'pending',
        'step': 'uploaded',
        'createdAt': datetime.utcnow().isoformat(),
        'language': language,
        'cvFileName': event.get('headers', {}).get('X-File-Name', 'unknown.pdf')
    })

    # Push to SQS for processing
    sqs.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=json.dumps({
            'jobId': job_id,
            'language': language
        })
    )

    return {
        'statusCode': 202,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'jobId': job_id,
            'status': 'pending',
            'message': 'CV upload successful. Processing started.'
        })
    }
```

---

## Phase 4: Frontend Migration (Week 6-8)

### 4.1 Create Next.js Project

```bash
pnpm create next-app@latest frontend --typescript --tailwind --app
cd frontend
```

### 4.2 Upload Page

**File: `frontend/app/upload/page.tsx`**
```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const router = useRouter();

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);

    const formData = new FormData();
    formData.append('cv', file);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const { jobId } = await response.json();

      // Redirect to status page
      router.push(`/status/${jobId}`);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md w-96">
        <h1 className="text-2xl font-bold mb-4">Upload CV</h1>

        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="hidden"
            id="file-upload"
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <p className="text-gray-600">
              {file ? file.name : 'Click to select PDF'}
            </p>
          </label>
        </div>

        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="mt-4 w-full bg-blue-600 text-white py-2 rounded disabled:bg-gray-400"
        >
          {uploading ? 'Uploading...' : 'Upload CV'}
        </button>
      </div>
    </div>
  );
}
```

### 4.3 Status Page with Real-time Updates

**File: `frontend/app/status/[jobId]/page.tsx`**
```typescript
'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';

interface JobStatus {
  jobId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  step: string;
  progress: number;
  outputs?: {
    cv_word?: string;
    dashboard_html?: string;
  };
}

export default function StatusPage() {
  const params = useParams();
  const jobId = params.jobId as string;

  const [status, setStatus] = useState<JobStatus | null>(null);

  useEffect(() => {
    // Poll API for status updates
    const interval = setInterval(async () => {
      const response = await fetch(`/api/status/${jobId}`);
      const data = await response.json();
      setStatus(data);

      if (data.status === 'completed' || data.status === 'failed') {
        clearInterval(interval);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId]);

  if (!status) return <div>Loading...</div>;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md w-96">
        <h1 className="text-2xl font-bold mb-4">CV Processing</h1>

        <div className="mb-4">
          <p className="text-sm text-gray-600">Job ID: {jobId}</p>
          <p className="text-sm">Status: {status.status}</p>
          <p className="text-sm">Step: {status.step}</p>
        </div>

        <div className="w-full bg-gray-200 rounded-full h-2.5 mb-4">
          <div
            className="bg-blue-600 h-2.5 rounded-full"
            style={{ width: `${status.progress}%` }}
          ></div>
        </div>

        {status.status === 'completed' && (
          <div>
            <a
              href={status.outputs?.cv_word}
              className="block w-full bg-green-600 text-white text-center py-2 rounded mb-2"
            >
              Download CV (Word)
            </a>
            <a
              href={status.outputs?.dashboard_html}
              className="block w-full bg-blue-600 text-white text-center py-2 rounded"
            >
              View Dashboard
            </a>
          </div>
        )}

        {status.status === 'failed' && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            Processing failed. Please try again.
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## Phase 5: Testing & Validation (Week 9-10)

### 5.1 Load Testing with Locust

**File: `tests/load_test.py`**
```python
from locust import HttpUser, task, between

class CVGeneratorUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def upload_cv(self):
        with open('tests/fixtures/sample_cv.pdf', 'rb') as f:
            self.client.post('/api/v1/cv/upload', files={'cv': f})

# Run with:
# locust -f tests/load_test.py --host=https://api.cv-generator.com
```

### 5.2 End-to-End Test

```bash
# Install dependencies
pip install pytest boto3 pytest-asyncio

# Run tests
pytest tests/e2e/test_full_pipeline.py -v
```

**File: `tests/e2e/test_full_pipeline.py`**
```python
import pytest
import boto3
import time
import json

@pytest.fixture
def s3_client():
    return boto3.client('s3')

@pytest.fixture
def dynamodb():
    return boto3.resource('dynamodb')

def test_full_cv_pipeline(s3_client, dynamodb):
    """Test complete pipeline from upload to completion"""

    # 1. Upload PDF to S3 (simulate upload-handler)
    job_id = 'test-' + str(int(time.time()))

    with open('tests/fixtures/sample_cv.pdf', 'rb') as f:
        s3_client.put_object(
            Bucket='cv-generator-uploads-dev',
            Key=f'{job_id}/input.pdf',
            Body=f.read()
        )

    # 2. Create metadata record
    table = dynamodb.Table('cv-metadata-dev')
    table.put_item(Item={
        'jobId': job_id,
        'status': 'pending',
        'step': 'uploaded'
    })

    # 3. Trigger SQS message (would be done by upload-handler)
    sqs = boto3.client('sqs')
    sqs.send_message(
        QueueUrl='https://sqs.us-east-1.amazonaws.com/123/cv-processing-dev',
        MessageBody=json.dumps({'jobId': job_id, 'language': 'de'})
    )

    # 4. Poll DynamoDB for completion (max 3 minutes)
    start_time = time.time()
    while time.time() - start_time < 180:
        response = table.get_item(Key={'jobId': job_id})
        status = response['Item']['status']

        if status == 'completed':
            # 5. Verify outputs in S3
            cv_json = s3_client.get_object(
                Bucket='cv-generator-outputs-dev',
                Key=f'{job_id}/cv_data.json'
            )
            assert cv_json is not None

            cv_word = s3_client.get_object(
                Bucket='cv-generator-outputs-dev',
                Key=f'{job_id}/cv.docx'
            )
            assert cv_word is not None

            print(f"✅ Pipeline completed in {time.time() - start_time:.2f}s")
            return

        elif status == 'failed':
            pytest.fail(f"Pipeline failed: {response['Item'].get('errorMessage')}")

        time.sleep(5)

    pytest.fail("Pipeline timeout (exceeded 3 minutes)")
```

---

## Phase 6: Production Deployment (Week 11-12)

### 6.1 Blue-Green Deployment

```bash
# Create production environment
terraform workspace new prod
terraform workspace select prod

# Deploy infrastructure
terraform apply -var="environment=prod"

# Deploy Lambda functions (all at once)
./scripts/deploy_lambdas.sh prod
```

**File: `scripts/deploy_lambdas.sh`**
```bash
#!/bin/bash
ENV=$1

FUNCTIONS=(
  "cv-extractor"
  "cv-generator"
  "matcher"
  "feedback"
  "offer-generator"
  "dashboard-builder"
)

for FUNCTION in "${FUNCTIONS[@]}"; do
  echo "Deploying $FUNCTION to $ENV..."

  cd lambda_functions/$FUNCTION

  # Build Docker image
  docker build -t $FUNCTION:latest .

  # Push to ECR
  docker tag $FUNCTION:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/$FUNCTION:$ENV
  docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/$FUNCTION:$ENV

  # Update Lambda
  aws lambda update-function-code \
    --function-name $FUNCTION-$ENV \
    --image-uri 123456789012.dkr.ecr.us-east-1.amazonaws.com/$FUNCTION:$ENV

  cd ../..
done

echo "✅ All Lambda functions deployed to $ENV"
```

### 6.2 DNS Migration

```bash
# Update Route53 to point to CloudFront
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123ABC \
  --change-batch file://dns-migration.json

# dns-migration.json
{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "cv-generator.com",
      "Type": "A",
      "AliasTarget": {
        "HostedZoneId": "Z2FDTNDATAQYW2",
        "DNSName": "d111111abcdef8.cloudfront.net",
        "EvaluateTargetHealth": false
      }
    }
  }]
}
```

### 6.3 Monitoring Setup

```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name cv-generator-prod \
  --dashboard-body file://cloudwatch-dashboard.json
```

---

## Rollback Plan

If production issues occur:

```bash
# 1. Revert DNS to old VM
aws route53 change-resource-record-sets --hosted-zone-id Z123ABC --change-batch file://dns-rollback.json

# 2. Monitor for 5 minutes (ensure traffic shifted)
watch -n 5 'aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Invocations --dimensions Name=FunctionName,Value=cv-extractor-prod --start-time $(date -u -d "10 minutes ago" +%Y-%m-%dT%H:%M:%S) --end-time $(date -u +%Y-%m-%dT%H:%M:%S) --period 60 --statistics Sum'

# 3. If stable, destroy serverless infrastructure
terraform workspace select prod
terraform destroy
```

---

## Success Criteria

- [ ] API Gateway returns 200 for health check
- [ ] Upload endpoint processes 100 concurrent CVs without errors
- [ ] Average processing time <2 minutes per CV
- [ ] Error rate <1% over 24 hours
- [ ] Cost <$50/month for 1000 CVs
- [ ] Zero data loss (all uploads tracked in DynamoDB)

---

## Next Steps After Migration

1. **Add Authentication**: Integrate AWS Cognito for user management
2. **Multi-region Deployment**: Deploy to eu-west-1 for European users
3. **Cost Optimization**: Implement Lambda reserved concurrency
4. **Advanced Monitoring**: Add X-Ray tracing for debugging
5. **A/B Testing**: Test different prompts to reduce API costs

---

**Support**: For questions, see [TECH_DEBT.md](./TECH_DEBT.md) and [SERVERLESS_ARCHITECTURE.md](./SERVERLESS_ARCHITECTURE.md)
