-- Migration 002: Create translations table for multilingual UI support
-- This table stores all UI translations for multiple languages (de, en, fr)
-- Translations are deployed across instances and NOT excluded from Git

CREATE TABLE IF NOT EXISTS translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section TEXT NOT NULL,
    key TEXT NOT NULL,
    language TEXT NOT NULL CHECK(language IN ('de', 'en', 'fr')),
    value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint to prevent duplicate translations
    UNIQUE(section, key, language),
    
    -- Foreign key constraints for referential integrity
    CONSTRAINT valid_section CHECK(section IN ('ui', 'cv', 'offer', 'job_profile', 'status_values', 'workflow_values'))
);

-- Index for fast lookups by section and language
CREATE INDEX IF NOT EXISTS idx_translations_section_lang ON translations(section, language);

-- Index for fast lookups by key
CREATE INDEX IF NOT EXISTS idx_translations_key ON translations(key);

-- Trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS translations_update_timestamp
AFTER UPDATE ON translations
FOR EACH ROW
BEGIN
    UPDATE translations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

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
