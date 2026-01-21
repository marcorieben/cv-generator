"""
Database Consistency Tests

Tests to ensure:
1. All database layer uses English (language-neutral)
2. UI layer handles translations via translations.json
3. Schema is consistent across all instances

Design Principle:
- Database Layer: English only (customer, description, status, etc)
- UI Layer: Multilingual translations (German "Kunde", French "Client", etc)
- Result: Single source of truth with flexible UI

Example:
  DB stores: status="draft", customer="Acme Corp", level="senior"
  UI translates: "Entwurf", "Acme Corp", "Leitend" (German) or "Draft", "Acme Corp", "Senior" (English)
"""

import pytest
import sqlite3
import json
import os
import tempfile
import shutil
from datetime import datetime
from core.database.db import Database
from core.database.models import (
    JobProfile, Candidate, JobProfileCandidate,
    JobProfileStatus, CandidateStatus, SkillLevel,
    JobProfileWorkflowState, CandidateWorkflowState,
    JobProfileComment
)


class TestDatabaseLanguageConsistency:
    """
    Verify all database layer uses English for language-neutral storage.
    
    Rationale:
    - Database values in English enable portability and cloud migration
    - UI translations (via translations.json) handle user language preferences
    - Single database instance can serve multiple language interfaces
    
    Testing Strategy:
    1. Verify enum values are English
    2. Verify model field names are English
    3. Verify SQL column names are English
    
    Translation Example:
    ```
    # Database (English):
    status = "draft"
    customer = "Tech Corp"
    level = "senior"
    
    # German UI (via translations.json):
    "status.draft" → "Entwurf"
    "level.senior" → "Leitend"
    
    # English UI:
    "status.draft" → "Draft"
    "level.senior" → "Senior"
    ```
    """
    
    def test_all_enum_values_are_english(self):
        """Verify all enum values are lowercase English"""
        
        # Check JobProfileStatus
        status_values = {s.value for s in JobProfileStatus}
        expected_status = {"draft", "published", "active", "closed", "archived", "rejected"}
        assert status_values == expected_status, \
            f"JobProfileStatus values should be English. Got: {status_values}"
        
        # Check CandidateStatus
        candidate_status_values = {s.value for s in CandidateStatus}
        expected_candidate_status = {"applied", "screening", "interview", "rejected", "hired", "archived"}
        assert candidate_status_values == expected_candidate_status, \
            f"CandidateStatus values should be English. Got: {candidate_status_values}"
        
        # Check SkillLevel
        skill_levels = {s.value for s in SkillLevel}
        expected_levels = {"junior", "intermediate", "senior", "lead", "expert"}
        assert skill_levels == expected_levels, \
            f"SkillLevel values should be English. Got: {skill_levels}"
        
        # Verify no German enum values exist
        all_values = status_values | candidate_status_values | skill_levels
        german_words = {"entwurf", "veröffentlicht", "abgelehnt", "archiviert"}
        assert not german_words.intersection(all_values), \
            f"German enum values found: {german_words.intersection(all_values)}"
    
    def test_model_field_names_are_english(self):
        """
        Verify all model field names are in English

        Database field names are English for:
        - Code readability
        - International collaboration
        - Framework/ORM compatibility

        UI labels are translated separately in Streamlit pages
        """

        # Check JobProfile fields
        profile_fields = JobProfile.__dataclass_fields__.keys()
        expected_profile_fields = {
            'id', 'name', 'customer', 'description', 'required_skills',
            'level', 'status', 'current_workflow_state', 'created_at',
            'updated_at', 'created_by', 'metadata', 'attachment_blob', 'attachment_filename'
        }
        assert set(profile_fields) == expected_profile_fields, \
            f"JobProfile fields mismatch. Got: {set(profile_fields)}"

        # Verify no German field names exist
        assert 'kunde' not in profile_fields, "Field 'kunde' should be renamed to 'customer'"

        # Check Candidate fields
        candidate_fields = Candidate.__dataclass_fields__.keys()
        expected_candidate_fields = {
            'id', 'first_name', 'last_name', 'email', 'phone', 'cv_json',
            'primary_role_title', 'summary', 'status', 'workflow_state', 
            'created_at', 'updated_at', 'metadata'
        }
        assert set(candidate_fields) == expected_candidate_fields, \
            f"Candidate fields mismatch. Got: {set(candidate_fields)}"
        
        # Verify no German field names exist
        german_fields = {'vorname', 'nachname', 'kurzprofil', 'hauptrolle_titel'}
        assert not german_fields.intersection(candidate_fields), \
            f"German fields found in Candidate: {german_fields.intersection(candidate_fields)}"
    
    def test_database_column_names_are_english(self):
        """
        Verify all SQL column names are in English

        All database columns are in English to:
        - Ensure consistency across all instances
        - Enable safe migrations
        - Support multiple UI languages without DB changes

        Examples:
          'customer' (not 'kunde')
          'description' (not 'beschreibung')
          'status' (works for all languages)
          'comment_text' (not 'kommentar_text')
        """
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")

        try:
            db = Database(db_path)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check job_profiles columns
            cursor.execute("PRAGMA table_info(job_profiles)")
            columns = [row[1] for row in cursor.fetchall()]

            assert 'customer' in columns, "job_profiles should have 'customer' column"
            assert 'kunde' not in columns, "job_profiles should not have 'kunde' column"
            assert 'name' in columns
            assert 'description' in columns
            assert 'required_skills' in columns
            assert 'status' in columns
            assert 'current_workflow_state' in columns
            
            # Check candidates columns
            cursor.execute("PRAGMA table_info(candidates)")
            candidate_columns = [row[1] for row in cursor.fetchall()]
            
            assert 'first_name' in candidate_columns, "candidates should have 'first_name' column"
            assert 'last_name' in candidate_columns, "candidates should have 'last_name' column"
            assert 'vorname' not in candidate_columns, "candidates should not have 'vorname' column"
            assert 'nachname' not in candidate_columns, "candidates should not have 'nachname' column"
            assert 'primary_role_title' in candidate_columns
            assert 'summary' in candidate_columns
            assert 'workflow_state' in candidate_columns

            conn.close()
            
        finally:
            try:
                if os.path.exists(db_path):
                    os.remove(db_path)
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except:
                pass


class TestDatabaseSchemaConsistency:
    """Ensure database schema is consistent and complete"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")
        db = Database(db_path)
        
        yield db
        
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except:
            pass
    
    def test_all_required_tables_exist(self, temp_db):
        """Verify all required tables are created"""
        conn = sqlite3.connect(temp_db.config.db_path)
        cursor = conn.cursor()

        # Check for required tables
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        tables = [row[0] for row in cursor.fetchall()]

        required_tables = [
            'job_profiles',
            'candidates',
            'job_profile_candidates',
            'job_profile_comments',
            'attachments',
            'workflow_history',
            'db_metadata'
        ]

        for table in required_tables:
            assert table in tables, f"Missing required table: {table}"
        
        conn.close()

    def test_job_profiles_has_required_columns(self, temp_db):
        """Verify job_profiles table has all required columns"""
        conn = sqlite3.connect(temp_db.config.db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(job_profiles)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}  # name: type

        required_columns = {
            'id': 'INTEGER',
            'name': 'VARCHAR',
            'customer': 'VARCHAR',
            'description': 'TEXT',
            'required_skills': 'TEXT',
            'level': 'TEXT',
            'status': 'TEXT',
            'current_workflow_state': 'TEXT',
            'created_at': 'TIMESTAMP',
            'updated_at': 'TIMESTAMP',
            'created_by': 'VARCHAR',
            'metadata': 'TEXT'
        }

        for col_name, col_type in required_columns.items():
            assert col_name in columns, f"Missing column: {col_name}"
        
        conn.close()

    def test_candidates_has_required_columns(self, temp_db):
        """Verify candidates table has all required columns"""
        conn = sqlite3.connect(temp_db.config.db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(candidates)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}  # name: type

        required_columns = {
            'id': 'INTEGER',
            'first_name': 'VARCHAR',
            'last_name': 'VARCHAR',
            'email': 'VARCHAR',
            'phone': 'VARCHAR',
            'cv_json': 'TEXT',
            'primary_role_title': 'VARCHAR',
            'summary': 'TEXT',
            'status': 'TEXT',
            'workflow_state': 'TEXT',
            'created_at': 'TIMESTAMP'
        }

        for col_name, col_type in required_columns.items():
            assert col_name in columns, f"Missing column: {col_name}"
        
        # Verify no German column names exist
        german_columns = {'vorname', 'nachname', 'kurzprofil', 'hauptrolle_titel'}
        columns_set = set(columns.keys())
        assert not german_columns.intersection(columns_set), \
            f"German columns found: {german_columns.intersection(columns_set)}"
        
        conn.close()

    def test_job_profile_comments_has_required_columns(self, temp_db):
        """Verify job_profile_comments table has all required columns"""
        conn = sqlite3.connect(temp_db.config.db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(job_profile_comments)")
        columns = {row[1] for row in cursor.fetchall()}

        required_columns = {
            'id', 'job_profile_id', 'username', 'comment_text', 'created_at'
        }

        assert required_columns.issubset(columns), \
            f"Missing columns in job_profile_comments: {required_columns - columns}"
        
        conn.close()

    def test_indexes_exist(self, temp_db):
        """Verify performance indexes are created"""
        conn = sqlite3.connect(temp_db.config.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name LIKE 'idx_%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]

        required_indexes = [
            'idx_job_profiles_status',
            'idx_candidates_email',
            'idx_job_profile_comments_profile'
        ]

        for idx in required_indexes:
            assert idx in indexes, f"Missing required index: {idx}"
        
        conn.close()

    def test_foreign_key_relationships(self, temp_db):
        """Verify foreign key relationships are properly defined"""
        conn = sqlite3.connect(temp_db.config.db_path)
        cursor = conn.cursor()

        # Check job_profile_candidates foreign keys
        cursor.execute("PRAGMA foreign_key_list(job_profile_candidates)")
        fks = cursor.fetchall()
        fk_tables = [fk[2] for fk in fks]

        assert 'job_profiles' in fk_tables, \
            "job_profile_candidates should reference job_profiles"
        assert 'candidates' in fk_tables, \
            "job_profile_candidates should reference candidates"

        # Check job_profile_comments foreign keys
        cursor.execute("PRAGMA foreign_key_list(job_profile_comments)")
        comment_fks = cursor.fetchall()
        comment_fk_tables = [fk[2] for fk in comment_fks]

        assert 'job_profiles' in comment_fk_tables, \
            "job_profile_comments should reference job_profiles"
        
        conn.close()


class TestDatabaseDataConsistency:
    """Verify data stored in database is consistent and valid"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")
        db = Database(db_path)
        
        yield db
        
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except:
            pass

    def test_json_fields_are_valid_json(self, temp_db):
        """Verify JSON fields contain valid JSON"""
        profile = JobProfile(
            name="Test",
            description="Test",
            required_skills=["Python", "Django"]
        )
        profile_id = temp_db.create_job_profile(profile)
        
        conn = sqlite3.connect(temp_db.config.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT required_skills, metadata FROM job_profiles WHERE id = ?", (profile_id,))
        row = cursor.fetchone()
        
        if row:
            try:
                json.loads(row[0])  # required_skills
                json.loads(row[1])  # metadata
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in database: {e}")
        
        conn.close()

    def test_timestamps_are_consistent(self, temp_db):
        """Verify timestamps are properly set and consistent"""
        profile = JobProfile(
            name="Test",
            description="Test",
            required_skills=["Skill"]
        )
        profile_id = temp_db.create_job_profile(profile)
        
        retrieved = temp_db.get_job_profile(profile_id)
        
        assert retrieved.created_at is not None, "created_at should be set"
        assert retrieved.updated_at is not None, "updated_at should be set"

    def test_status_values_are_valid(self, temp_db):
        """Verify status fields only contain valid enum values"""
        profile = JobProfile(
            name="Test",
            description="Test",
            required_skills=["Skill"],
            status="active"
        )
        profile_id = temp_db.create_job_profile(profile)
        
        retrieved = temp_db.get_job_profile(profile_id)
        
        # Verify status is from the enum
        valid_statuses = {s.value for s in JobProfileStatus}
        assert retrieved.status in valid_statuses or retrieved.status.value in valid_statuses, \
            f"Invalid status: {retrieved.status}"

    def test_workflow_state_values_are_valid(self, temp_db):
        """Verify workflow_state fields only contain valid enum values"""
        profile = JobProfile(
            name="Test",
            description="Test",
            required_skills=["Skill"]
        )
        profile_id = temp_db.create_job_profile(profile)
        
        retrieved = temp_db.get_job_profile(profile_id)
        
        # Verify workflow state is from the enum
        valid_states = {s.value for s in JobProfileWorkflowState}
        actual_state = retrieved.current_workflow_state
        if hasattr(actual_state, 'value'):
            actual_state = actual_state.value
        assert actual_state in valid_states, \
            f"Invalid workflow state: {actual_state}"
