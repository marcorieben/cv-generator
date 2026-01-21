"""
SQLite database implementation for CV Generator
Cloud-agnostic design - can be replaced with PostgreSQL, etc.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from .models import (
    JobProfile, Candidate, JobProfileCandidate, Attachment, WorkflowHistory,
    JobProfileStatus, CandidateStatus, JobProfileWorkflowState, CandidateWorkflowState
)


class DatabaseConfig:
    """Database configuration"""
    def __init__(self, db_path: str = "data/cv_generator.db"):
        self.db_path = db_path
        self.ensure_data_dir()
    
    def ensure_data_dir(self):
        """Ensure data directory exists"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)


class Database:
    """
    SQLite database interface for CV Generator
    All tables store metadata as JSON for cloud migration flexibility
    """
    
    SCHEMA_VERSION = 1
    
    def __init__(self, db_path: str):
        # Accept both config object and string path
        if isinstance(db_path, DatabaseConfig):
            self.config = db_path
        else:
            self.config = DatabaseConfig(db_path)
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.config.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def init_db(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create tables
            cursor.executescript("""
                -- Job Profiles
                CREATE TABLE IF NOT EXISTS job_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    required_skills TEXT,
                    level TEXT DEFAULT 'intermediate',
                    status TEXT DEFAULT 'draft',
                    current_workflow_state TEXT DEFAULT 'draft',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(255),
                    metadata TEXT DEFAULT '{}'
                );
                
                -- Candidates
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vorname VARCHAR(100) NOT NULL,
                    nachname VARCHAR(100) NOT NULL,
                    email VARCHAR(255),
                    phone VARCHAR(20),
                    cv_json TEXT NOT NULL,
                    hauptrolle_titel VARCHAR(255),
                    kurzprofil TEXT,
                    status TEXT DEFAULT 'applied',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                );
                
                -- Job Profile - Candidate Relationship
                CREATE TABLE IF NOT EXISTS job_profile_candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_profile_id INTEGER NOT NULL,
                    candidate_id INTEGER NOT NULL,
                    matched_at TIMESTAMP,
                    match_score REAL,
                    notes TEXT,
                    status TEXT DEFAULT 'pending',
                    workflow_state TEXT DEFAULT 'initial',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (job_profile_id) REFERENCES job_profiles(id) ON DELETE CASCADE,
                    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
                    UNIQUE(job_profile_id, candidate_id)
                );
                
                -- Attachments
                CREATE TABLE IF NOT EXISTS attachments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type VARCHAR(50),
                    entity_id INTEGER,
                    file_name VARCHAR(255) NOT NULL,
                    file_path VARCHAR(512),
                    file_type VARCHAR(50),
                    file_size INTEGER,
                    storage_backend TEXT DEFAULT 'local',
                    remote_path VARCHAR(512),
                    cloud_url VARCHAR(512),
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                );
                
                -- Workflow History
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
                    metadata TEXT DEFAULT '{}'
                );
                
                -- Metadata table for versioning
                CREATE TABLE IF NOT EXISTS db_metadata (
                    key VARCHAR(100) PRIMARY KEY,
                    value TEXT
                );
                
                -- Insert schema version if not exists
                INSERT OR IGNORE INTO db_metadata (key, value) VALUES ('schema_version', '1');
            """)
    
    # Job Profile operations
    
    def create_job_profile(self, profile: JobProfile) -> int:
        """Create new job profile"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            data = profile.to_dict()
            
            cursor.execute("""
                INSERT INTO job_profiles 
                (name, description, required_skills, level, status, current_workflow_state, 
                 created_by, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['name'], data['description'], json.dumps(data['required_skills']),
                data['level'], data['status'], data['current_workflow_state'],
                data['created_by'], json.dumps(data['metadata'])
            ))
            return cursor.lastrowid
    
    def get_job_profile(self, profile_id: int) -> Optional[JobProfile]:
        """Get job profile by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM job_profiles WHERE id = ?", (profile_id,))
            row = cursor.fetchone()
            
            if row:
                data = dict(row)
                if isinstance(data['required_skills'], str):
                    data['required_skills'] = json.loads(data['required_skills'])
                return JobProfile.from_dict(data)
            return None
    
    def get_all_job_profiles(self, status: Optional[str] = None) -> List[JobProfile]:
        """Get all job profiles, optionally filtered by status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute(
                    "SELECT * FROM job_profiles WHERE status = ? ORDER BY created_at DESC",
                    (status,)
                )
            else:
                cursor.execute("SELECT * FROM job_profiles ORDER BY created_at DESC")
            
            profiles = []
            for row in cursor.fetchall():
                data = dict(row)
                if isinstance(data['required_skills'], str):
                    data['required_skills'] = json.loads(data['required_skills'])
                profiles.append(JobProfile.from_dict(data))
            
            return profiles
    
    def update_job_profile(self, profile: JobProfile) -> bool:
        """Update existing job profile"""
        if not profile.id:
            return False
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            profile.updated_at = datetime.now()
            data = profile.to_dict()
            
            cursor.execute("""
                UPDATE job_profiles SET
                name = ?, description = ?, required_skills = ?, level = ?,
                status = ?, current_workflow_state = ?, metadata = ?, updated_at = ?
                WHERE id = ?
            """, (
                data['name'], data['description'], json.dumps(data['required_skills']),
                data['level'], data['status'], data['current_workflow_state'],
                json.dumps(data['metadata']), data['updated_at'], profile.id
            ))
            return cursor.rowcount > 0
    
    # Candidate operations
    
    def create_candidate(self, candidate: Candidate) -> int:
        """Create new candidate"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            data = candidate.to_dict()
            
            cursor.execute("""
                INSERT INTO candidates
                (vorname, nachname, email, phone, cv_json, hauptrolle_titel,
                 kurzprofil, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['vorname'], data['nachname'], data['email'], data['phone'],
                data['cv_json'], data['hauptrolle_titel'], data['kurzprofil'],
                data['status'], data['metadata']
            ))
            return cursor.lastrowid
    
    def get_candidate(self, candidate_id: int) -> Optional[Candidate]:
        """Get candidate by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,))
            row = cursor.fetchone()
            
            if row:
                return Candidate.from_dict(dict(row))
            return None
    
    def get_all_candidates(self, status: Optional[str] = None) -> List[Candidate]:
        """Get all candidates, optionally filtered by status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute(
                    "SELECT * FROM candidates WHERE status = ? ORDER BY created_at DESC",
                    (status,)
                )
            else:
                cursor.execute("SELECT * FROM candidates ORDER BY created_at DESC")
            
            candidates = []
            for row in cursor.fetchall():
                candidates.append(Candidate.from_dict(dict(row)))
            
            return candidates
    
    def update_candidate(self, candidate: Candidate) -> bool:
        """Update existing candidate"""
        if not candidate.id:
            return False
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            candidate.updated_at = datetime.now()
            data = candidate.to_dict()
            
            cursor.execute("""
                UPDATE candidates SET
                vorname = ?, nachname = ?, email = ?, phone = ?, cv_json = ?,
                hauptrolle_titel = ?, kurzprofil = ?, status = ?,
                metadata = ?, updated_at = ?
                WHERE id = ?
            """, (
                data['vorname'], data['nachname'], data['email'], data['phone'],
                json.dumps(data['cv_json']), data['hauptrolle_titel'], data['kurzprofil'],
                data['status'], json.dumps(data['metadata']), data['updated_at'], candidate.id
            ))
            return cursor.rowcount > 0
    
    # Job Profile - Candidate relationship operations
    
    def add_candidate_to_profile(self, job_profile_id: int, candidate_id: int) -> int:
        """Add candidate to job profile"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO job_profile_candidates
                (job_profile_id, candidate_id, workflow_state, status)
                VALUES (?, ?, ?, ?)
            """, (job_profile_id, candidate_id, 'initial', 'pending'))
            return cursor.lastrowid
    
    def get_job_profile_candidates(self, job_profile_id: int) -> List[JobProfileCandidate]:
        """Get all candidates for a job profile"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM job_profile_candidates
                WHERE job_profile_id = ?
                ORDER BY created_at DESC
            """, (job_profile_id,))
            
            candidates = []
            for row in cursor.fetchall():
                candidates.append(JobProfileCandidate.from_dict(dict(row)))
            
            return candidates
    
    # Workflow operations
    
    def log_workflow_transition(self, history: WorkflowHistory) -> int:
        """Log workflow state transition"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            data = history.to_dict()
            
            cursor.execute("""
                INSERT INTO workflow_history
                (entity_type, entity_id, old_state, new_state, action,
                 performed_by, notes, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['entity_type'], data['entity_id'], data['old_state'],
                data['new_state'], data['action'], data['performed_by'],
                data['notes'], data['metadata']
            ))
            return cursor.lastrowid
    
    def get_workflow_history(self, entity_type: str, entity_id: int) -> List[WorkflowHistory]:
        """Get workflow history for an entity"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM workflow_history
                WHERE entity_type = ? AND entity_id = ?
                ORDER BY performed_at DESC
            """, (entity_type, entity_id))
            
            history = []
            for row in cursor.fetchall():
                history.append(WorkflowHistory.from_dict(dict(row)))
            
            return history
