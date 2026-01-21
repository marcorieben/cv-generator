# Database Integration Design

## Overview

Workflow-basierte Datenbank zur Verwaltung von Stellenprofilen und Kandidaten mit lokaler SQLite-Basis und Cloud-Migration-Vorbereitung.

## Architecture

```
┌─────────────────────────────────────┐
│   Streamlit Web App (UI Layer)      │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   WorkflowManager Classes           │
│  - JobProfileWorkflow               │
│  - CandidateWorkflow                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Database Layer (cloud-agnostic)   │
│  - Base Models                      │
│  - CRUD Operations                  │
│  - Migrations                       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Storage Backends (Pluggable)      │
│  - SQLite (Local Development)       │
│  - PostgreSQL (Cloud Ready)         │
│  - File Storage (Attachments)       │
└─────────────────────────────────────┘
```

## Database Schema

### Core Tables

#### 1. job_profiles
```sql
CREATE TABLE job_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    required_skills JSON,           -- Array of skill requirements
    level TEXT,                      -- Junior, Senior, Lead, etc.
    status VARCHAR(50),              -- open, closed, filled, archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    
    -- Workflow tracking
    current_workflow_state VARCHAR(50),  -- draft, published, closed
    metadata JSON                    -- Additional fields for cloud migration
);
```

#### 2. candidates
```sql
CREATE TABLE candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vorname VARCHAR(100) NOT NULL,
    nachname VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    
    -- CV Data (JSON compatible with existing CV schema)
    cv_json JSON NOT NULL,          -- Full CV structure
    hauptrolle_titel VARCHAR(255),
    kurzprofil TEXT,
    
    status VARCHAR(50),             -- applied, screening, interview, rejected, hired
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Workflow tracking
    current_workflow_state VARCHAR(50),  -- initial, screening, interview, decision
    metadata JSON
);
```

#### 3. job_profile_candidates (M2M)
```sql
CREATE TABLE job_profile_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_profile_id INTEGER NOT NULL,
    candidate_id INTEGER NOT NULL,
    
    -- Relationship metadata
    matched_at TIMESTAMP,
    match_score FLOAT,              -- 0-100
    notes TEXT,
    status VARCHAR(50),             -- pending, accepted, rejected
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_profile_id) REFERENCES job_profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    UNIQUE(job_profile_id, candidate_id)
);
```

#### 4. attachments
```sql
CREATE TABLE attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER,
    job_profile_id INTEGER,
    
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(512),         -- Local path (development)
    file_type VARCHAR(50),          -- pdf, docx, xlsx, etc.
    file_size INTEGER,              -- bytes
    
    storage_backend VARCHAR(50),    -- 'local', 'azure', 'aws', etc.
    remote_path VARCHAR(512),       -- Cloud path (production)
    
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Cloud metadata
    cloud_url VARCHAR(512),         -- Pre-signed URL
    metadata JSON,
    
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    FOREIGN KEY (job_profile_id) REFERENCES job_profiles(id) ON DELETE CASCADE
);
```

#### 5. workflow_history
```sql
CREATE TABLE workflow_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type VARCHAR(50),        -- 'job_profile', 'candidate'
    entity_id INTEGER,
    
    old_state VARCHAR(50),
    new_state VARCHAR(50),
    action VARCHAR(255),            -- 'created', 'moved_to_screening', etc.
    
    performed_by VARCHAR(255),
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    
    metadata JSON
);
```

## Workflow States

### Job Profile Workflow
```
draft → published → active → closed/archived
         ↓
      rejected (closed without filling)
```

### Candidate Workflow (per Job Profile)
```
initial → screening → interview → decision → hired/rejected
            ↓                        ↓
        rejected              hired/rejected
```

## Python Models Structure

### core/database/models.py
```python
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class JobProfile:
    """Job Profile model"""
    id: Optional[int]
    name: str
    description: str
    required_skills: List[str]
    level: str
    status: str
    current_workflow_state: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict

@dataclass
class Candidate:
    """Candidate model - integrates with existing CV schema"""
    id: Optional[int]
    vorname: str
    nachname: str
    email: Optional[str]
    cv_json: Dict  # Full CV structure
    status: str
    current_workflow_state: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict

@dataclass
class Attachment:
    """File attachment model - cloud-migration ready"""
    id: Optional[int]
    entity_type: str  # 'candidate', 'job_profile'
    entity_id: int
    file_name: str
    file_path: str  # Local path (development)
    remote_path: Optional[str]  # Cloud path (production)
    storage_backend: str  # 'local', 'azure', 'aws'
    metadata: Dict
```

## Workflow Classes

### JobProfileWorkflow
- create_profile(data) → draft state
- publish_profile(profile_id) → published
- open_for_applications() → active
- close_profile(reason) → closed
- archive_profile(profile_id) → archived
- get_workflow_history(profile_id) → List[HistoryEntry]

### CandidateWorkflow  
- add_candidate_to_profile(candidate_id, profile_id)
- move_to_screening(candidate_id, profile_id, notes)
- move_to_interview(candidate_id, profile_id, notes)
- make_decision(candidate_id, profile_id, decision, notes)
- get_workflow_history(candidate_id, profile_id) → List[HistoryEntry]

## Cloud Migration Path

### Local Development (Current)
- SQLite database: `data/cv_generator.db`
- File attachments: `data/attachments/`
- Configuration: environment variables in `.env`

### Production (Future)
1. **Phase 1**: PostgreSQL with local file storage
2. **Phase 2**: Add Azure Blob Storage / AWS S3
3. **Phase 3**: Multi-tenant support, audit logging

### Migration Strategy
- All models use abstract `StorageBackend` interface
- Connection strings configurable via environment
- Schema versioning with Alembic migrations
- No hardcoded paths or database specifics

## Implementation Priority

1. **MVP (Iteration 1)**
   - Core models (JobProfile, Candidate)
   - SQLite setup
   - Basic CRUD operations
   - Simple workflow state management

2. **Enhancement (Iteration 2)**
   - File attachment support
   - Workflow history tracking
   - Search and filtering

3. **Future (Cloud Ready)**
   - Multiple storage backends
   - Cloud migration scripts
   - Performance optimization

