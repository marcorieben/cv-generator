-- ============================================================================
-- CV Generator Database Schema
-- ============================================================================
-- SINGLE SOURCE OF TRUTH for database structure.
-- All table definitions, columns, indexes, and constraints go here.
-- This file is idempotent and executed on every application startup.
-- 
-- GOLDEN RULE:
-- ✅ Modify this file for ANY database structure change
-- ✅ Add columns, change types, add indexes, create triggers
-- ❌ Do NOT create individual migration files for schema changes
-- ❌ Use data_migrations/ ONLY for data transformations
--
-- Pre-commit hook ensures: Database changes = schema.sql update required!
-- ============================================================================

-- Job Profiles table
-- Stores job position descriptions, requirements, and metadata
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
    metadata TEXT,
    -- Attachment BLOB storage for direct DB persistence
    attachment_blob BLOB,
    attachment_filename VARCHAR(255)
    -- days_since_created is calculated in Python from created_at
    -- 🟢 < 5 days, 🟡 5-10 days, 🔴 > 10 days
);

-- Candidates table (English field names)
-- Stores candidate profiles with CV data
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
-- Links candidates to job profiles with match scoring
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
-- Stores file references for cloud storage integration
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
-- Tracks state changes and actions for audit/compliance
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

-- Job Profile Comments
-- Stores comments and notes for job profiles with full audit trail
CREATE TABLE IF NOT EXISTS job_profile_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_profile_id INTEGER NOT NULL,
    username VARCHAR(255),
    comment_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_profile_id) REFERENCES job_profiles(id) ON DELETE CASCADE
);

-- Multi-language translations
-- Database-backed translations for UI elements (DE/EN/FR)
-- Constraint: language IN ('de', 'en', 'fr')
CREATE TABLE IF NOT EXISTS translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section TEXT NOT NULL,
    key TEXT NOT NULL,
    language TEXT NOT NULL CHECK(language IN ('de', 'en', 'fr')),
    value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(section, key, language),
    CONSTRAINT valid_section CHECK(section IN ('ui', 'cv', 'offer', 'job_profile', 'status_values', 'workflow_values'))
);

-- Database metadata (version, sync status, etc.)
-- Stores system-level configuration and tracking
CREATE TABLE IF NOT EXISTS db_metadata (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Job profiles indexes
CREATE INDEX IF NOT EXISTS idx_job_profiles_status ON job_profiles(status);
CREATE INDEX IF NOT EXISTS idx_job_profiles_workflow ON job_profiles(current_workflow_state);
CREATE INDEX IF NOT EXISTS idx_job_profiles_created_at ON job_profiles(created_at DESC);

-- Candidates indexes
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);

-- Relationship indexes
CREATE INDEX IF NOT EXISTS idx_job_profile_candidates_profile ON job_profile_candidates(job_profile_id);
CREATE INDEX IF NOT EXISTS idx_job_profile_candidates_candidate ON job_profile_candidates(candidate_id);

-- Job Profile Comments indexes
CREATE INDEX IF NOT EXISTS idx_comments_profile ON job_profile_comments(job_profile_id);
CREATE INDEX IF NOT EXISTS idx_comments_created ON job_profile_comments(created_at DESC);

-- Workflow indexes
CREATE INDEX IF NOT EXISTS idx_workflow_history_entity ON workflow_history(entity_type, entity_id);

-- Translations indexes
CREATE INDEX IF NOT EXISTS idx_translations_section_lang ON translations(section, language);
CREATE INDEX IF NOT EXISTS idx_translations_key ON translations(key);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View for easier access to translations by language
CREATE VIEW IF NOT EXISTS translations_by_lang AS
SELECT 
    section,
    key,
    language,
    value,
    created_at,
    updated_at
FROM translations
ORDER BY section, key, language;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger to auto-update translations.updated_at on modification
CREATE TRIGGER IF NOT EXISTS translations_update_timestamp
AFTER UPDATE ON translations
FOR EACH ROW
BEGIN
    UPDATE translations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
