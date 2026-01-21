-- Migration: 001_initial_schema
-- Purpose: Create initial database schema for CV Generator with English standardization
-- Database Layer: English (language-neutral) | UI Layer: Translated via translations.json
-- IMPORTANT: This migration is IDEMPOTENT - safe to run multiple times

-- Job Profiles table
CREATE TABLE IF NOT EXISTS job_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    customer VARCHAR(255),
    description TEXT,
    required_skills TEXT,
    level TEXT,
    status TEXT,
    current_workflow_state TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    metadata TEXT
);

-- Candidates table (English field names)
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    cv_json TEXT,
    primary_role_title VARCHAR(255),
    summary TEXT,
    status TEXT,
    workflow_state TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);

-- Job Profile - Candidate relationship
CREATE TABLE IF NOT EXISTS job_profile_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_profile_id INTEGER NOT NULL,
    candidate_id INTEGER NOT NULL,
    matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    match_score REAL,
    notes TEXT,
    status TEXT,
    workflow_state TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    FOREIGN KEY (job_profile_id) REFERENCES job_profiles(id),
    FOREIGN KEY (candidate_id) REFERENCES candidates(id)
);

-- File attachments (cloud-ready)
CREATE TABLE IF NOT EXISTS attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    file_name VARCHAR(255),
    file_path VARCHAR(512),
    file_type VARCHAR(50),
    file_size INTEGER,
    storage_backend TEXT,
    remote_path VARCHAR(512),
    cloud_url VARCHAR(512),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);

-- Workflow audit trail
CREATE TABLE IF NOT EXISTS workflow_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    old_state VARCHAR(50),
    new_state VARCHAR(50),
    action VARCHAR(255),
    performed_by VARCHAR(255),
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    metadata TEXT
);

-- Job Profile Comments (English)
CREATE TABLE IF NOT EXISTS job_profile_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_profile_id INTEGER NOT NULL,
    username VARCHAR(255),
    comment_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_profile_id) REFERENCES job_profiles(id) ON DELETE CASCADE
);

-- Database metadata (version, sync status, etc.)
CREATE TABLE IF NOT EXISTS db_metadata (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_job_profiles_status ON job_profiles(status);
CREATE INDEX IF NOT EXISTS idx_job_profiles_workflow_state ON job_profiles(current_workflow_state);
CREATE INDEX IF NOT EXISTS idx_job_profile_comments_profile ON job_profile_comments(job_profile_id);
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_job_profile_candidates_profile ON job_profile_candidates(job_profile_id);
CREATE INDEX IF NOT EXISTS idx_job_profile_candidates_candidate ON job_profile_candidates(candidate_id);
CREATE INDEX IF NOT EXISTS idx_workflow_history_entity ON workflow_history(entity_type, entity_id);

