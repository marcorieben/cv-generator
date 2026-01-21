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
    JobProfileComment,
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
    
    SCHEMA_VERSION = 3  # Updated to include translations table for multilingual UI
    
    def __init__(self, db_path: str):
        # Accept both config object and string path
        if isinstance(db_path, DatabaseConfig):
            self.config = db_path
        else:
            self.config = DatabaseConfig(db_path)
        self.init_db()
        self.apply_migrations()
    
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
        """Initialize database - setup migration infrastructure"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Only create schema_migrations table - all other tables created via migrations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255) UNIQUE,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS db_metadata (
                    key VARCHAR(100) PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # Insert schema version metadata if not exists
            cursor.execute("""
                INSERT OR IGNORE INTO db_metadata (key, value) 
                VALUES ('schema_version', '2')
            """)
    
    def apply_migrations(self):
        """Apply pending database migrations"""
        migrations_dir = Path(__file__).parent.parent.parent / "data" / "migrations"
        if not migrations_dir.exists():
            return
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create migrations table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255) UNIQUE,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            
            # Get list of migration files
            migration_files = sorted(migrations_dir.glob("*.sql"))
            
            for migration_file in migration_files:
                migration_name = migration_file.name
                
                # Check if migration already applied
                cursor.execute(
                    "SELECT id FROM schema_migrations WHERE name = ?",
                    (migration_name,)
                )
                if cursor.fetchone():
                    continue  # Migration already applied
                
                # Read and execute migration
                try:
                    migration_sql = migration_file.read_text()
                    # Execute the entire migration script as one (SQLite supports multiple statements)
                    cursor.executescript(migration_sql)
                    
                    # Mark migration as applied
                    cursor.execute(
                        "INSERT INTO schema_migrations (name) VALUES (?)",
                        (migration_name,)
                    )
                    conn.commit()
                except Exception as e:
                    print(f"Error applying migration {migration_name}: {e}")
                    conn.rollback()
                    raise
    
    # Job Profile operations
    
    def create_job_profile(self, profile: JobProfile) -> int:
        """Create new job profile"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            data = profile.to_dict()
            
            cursor.execute("""
                INSERT INTO job_profiles 
                (name, customer, description, required_skills, level, status, current_workflow_state, 
                 created_by, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['name'], data.get('customer'), data['description'], json.dumps(data['required_skills']),
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
                name = ?, customer = ?, description = ?, required_skills = ?, level = ?,
                status = ?, current_workflow_state = ?, metadata = ?, updated_at = ?
                WHERE id = ?
            """, (
                data['name'], data.get('customer'), data['description'], json.dumps(data['required_skills']),
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
                (first_name, last_name, email, phone, cv_json, primary_role_title,
                 summary, status, workflow_state, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['first_name'], data['last_name'], data['email'], data['phone'],
                data['cv_json'], data['primary_role_title'], data['summary'],
                data['status'], data['workflow_state'], data['metadata']
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
                first_name = ?, last_name = ?, email = ?, phone = ?, cv_json = ?,
                primary_role_title = ?, summary = ?, status = ?, workflow_state = ?,
                metadata = ?, updated_at = ?
                WHERE id = ?
            """, (
                data['first_name'], data['last_name'], data['email'], data['phone'],
                data['cv_json'], data['primary_role_title'], data['summary'],
                data['status'], data['workflow_state'], data['metadata'], 
                data['updated_at'], candidate.id
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
    
    # --- Job Profile Comments ---
    def add_comment(self, job_profile_id: int, username: Optional[str], comment_text: str) -> Tuple[bool, str]:
        """Add a comment to a job profile"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO job_profile_comments (job_profile_id, username, comment_text, created_at)
                    VALUES (?, ?, ?, ?)
                """, (job_profile_id, username, comment_text, datetime.now()))
                conn.commit()
            return True, "Kommentar hinzugefügt"
        except Exception as e:
            return False, f"Fehler beim Hinzufügen des Kommentars: {str(e)}"
    
    def get_comments(self, job_profile_id: int) -> List[JobProfileComment]:
        """Get all comments for a job profile"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, job_profile_id, username, comment_text, created_at
                FROM job_profile_comments
                WHERE job_profile_id = ?
                ORDER BY created_at DESC
            """, (job_profile_id,))
            
            comments = []
            for row in cursor.fetchall():
                comments.append(JobProfileComment.from_dict(dict(row)))
            
            return comments
    
    def delete_comment(self, comment_id: int) -> Tuple[bool, str]:
        """Delete a comment"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM job_profile_comments WHERE id = ?", (comment_id,))
                conn.commit()
            return True, "Kommentar gelöscht"
        except Exception as e:
            return False, f"Fehler beim Löschen des Kommentars: {str(e)}"
