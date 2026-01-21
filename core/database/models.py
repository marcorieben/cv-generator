"""
Database models for CV Generator
Cloud-agnostic models compatible with SQLite, PostgreSQL, etc.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
import json


class JobProfileStatus(str, Enum):
    """Job profile statuses"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"
    REJECTED = "rejected"


class JobProfileWorkflowState(str, Enum):
    """Job profile workflow states"""
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"


class CandidateStatus(str, Enum):
    """Candidate statuses (per job profile)"""
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    REJECTED = "rejected"
    HIRED = "hired"
    ARCHIVED = "archived"


class CandidateWorkflowState(str, Enum):
    """Candidate workflow states (per job profile)"""
    INITIAL = "initial"
    SCREENING = "screening"
    INTERVIEW = "interview"
    DECISION = "decision"


class SkillLevel(str, Enum):
    """Required skill levels for job profiles"""
    JUNIOR = "junior"
    INTERMEDIATE = "intermediate"
    SENIOR = "senior"
    LEAD = "lead"
    EXPERT = "expert"


@dataclass
class JobProfile:
    """
    Job Profile model - represents an open position
    Integrates with workflow state management for structured hiring process
    """
    id: Optional[int] = None
    name: str = ""
    customer: Optional[str] = None
    description: str = ""
    required_skills: List[str] = field(default_factory=list)
    level: SkillLevel = SkillLevel.INTERMEDIATE
    status: JobProfileStatus = JobProfileStatus.DRAFT
    current_workflow_state: JobProfileWorkflowState = JobProfileWorkflowState.DRAFT
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        data = asdict(self)
        data['status'] = self.status.value if hasattr(self.status, 'value') else self.status
        data['level'] = self.level.value if hasattr(self.level, 'value') else self.level
        data['current_workflow_state'] = self.current_workflow_state.value
        data['metadata'] = json.dumps(self.metadata)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobProfile':
        """Create from database dictionary"""
        if isinstance(data.get('metadata'), str):
            data['metadata'] = json.loads(data['metadata'])
        
        data['status'] = JobProfileStatus(data.get('status', 'draft'))
        data['level'] = SkillLevel(data.get('level', 'intermediate'))
        data['current_workflow_state'] = JobProfileWorkflowState(
            data.get('current_workflow_state', 'draft')
        )
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Candidate:
    """
    Candidate model - represents a person applying for positions
    Integrates with existing CV schema (cv_json field)
    
    Database Layer: English field names for language-neutral storage
    UI Layer: Translations handled in Streamlit pages via translations.json
    """
    id: Optional[int] = None
    first_name: str = ""
    last_name: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    cv_json: Dict[str, Any] = field(default_factory=dict)
    primary_role_title: Optional[str] = None
    summary: Optional[str] = None
    status: CandidateStatus = CandidateStatus.APPLIED
    workflow_state: CandidateWorkflowState = CandidateWorkflowState.INITIAL
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def full_name(self) -> str:
        """Return full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        data = asdict(self)
        data['status'] = self.status.value
        data['workflow_state'] = self.workflow_state.value
        data['cv_json'] = json.dumps(self.cv_json) if isinstance(self.cv_json, dict) else self.cv_json
        data['metadata'] = json.dumps(self.metadata)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Candidate':
        """Create from database dictionary"""
        if isinstance(data.get('cv_json'), str):
            data['cv_json'] = json.loads(data['cv_json'])
        if isinstance(data.get('metadata'), str):
            data['metadata'] = json.loads(data['metadata'])
        
        data['status'] = CandidateStatus(data.get('status', 'applied'))
        data['workflow_state'] = CandidateWorkflowState(data.get('workflow_state', 'initial'))
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class JobProfileCandidate:
    """
    Relationship between job profile and candidate
    Tracks individual workflow state and match information
    """
    id: Optional[int] = None
    job_profile_id: int = 0
    candidate_id: int = 0
    matched_at: Optional[datetime] = None
    match_score: Optional[float] = None  # 0-100
    notes: str = ""
    status: str = "pending"  # pending, accepted, rejected
    workflow_state: CandidateWorkflowState = CandidateWorkflowState.INITIAL
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        data = asdict(self)
        data['workflow_state'] = self.workflow_state.value
        data['metadata'] = json.dumps(self.metadata)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobProfileCandidate':
        """Create from database dictionary"""
        if isinstance(data.get('metadata'), str):
            data['metadata'] = json.loads(data['metadata'])
        
        data['workflow_state'] = CandidateWorkflowState(
            data.get('workflow_state', 'initial')
        )
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Attachment:
    """
    File attachment model - cloud-migration ready
    Supports local file storage (dev) and cloud backends (prod)
    """
    id: Optional[int] = None
    entity_type: str = "candidate"  # 'candidate', 'job_profile'
    entity_id: int = 0
    file_name: str = ""
    file_path: str = ""  # Local path (development)
    file_type: str = ""  # pdf, docx, xlsx, etc.
    file_size: int = 0  # bytes
    uploaded_at: Optional[datetime] = None
    
    # Cloud storage fields
    storage_backend: str = "local"  # 'local', 'azure', 'aws', 'gcp'
    remote_path: Optional[str] = None  # Cloud path (production)
    cloud_url: Optional[str] = None  # Pre-signed or public URL
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        data = asdict(self)
        data['metadata'] = json.dumps(self.metadata)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Attachment':
        """Create from database dictionary"""
        if isinstance(data.get('metadata'), str):
            data['metadata'] = json.loads(data['metadata'])
        
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class WorkflowHistory:
    """
    Audit trail for workflow state transitions
    Tracks all changes for transparency and debugging
    """
    id: Optional[int] = None
    entity_type: str = ""  # 'job_profile', 'candidate'
    entity_id: int = 0
    old_state: Optional[str] = None
    new_state: str = ""
    action: str = ""  # 'created', 'moved_to_screening', etc.
    performed_by: Optional[str] = None
    performed_at: Optional[datetime] = None
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        data = asdict(self)
        data['metadata'] = json.dumps(self.metadata)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowHistory':
        """Create from database dictionary"""
        if isinstance(data.get('metadata'), str):
            data['metadata'] = json.loads(data['metadata'])
        
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class JobProfileComment:
    """
    Comment on a job profile
    Stores notes from users about the position
    """
    id: Optional[int] = None
    job_profile_id: int = 0
    username: Optional[str] = None
    comment_text: str = ""
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobProfileComment':
        """Create from database dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
