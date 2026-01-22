-- Migration: 003_add_attachment_blob
-- Purpose: Add BLOB field for storing attachment files directly in database
-- Date: 2026-01-21

ALTER TABLE job_profiles ADD COLUMN attachment_blob BLOB DEFAULT NULL;
ALTER TABLE job_profiles ADD COLUMN attachment_filename VARCHAR(255) DEFAULT NULL;

-- Note: Existing attachments stay in file system; new uploads will use BLOB storage
