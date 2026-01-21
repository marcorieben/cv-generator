"""
Database integration layer for CV Generator
Provides models, operations, and workflow management
"""

from .models import (
    JobProfile,
    Candidate,
    JobProfileCandidate,
    Attachment,
    WorkflowHistory,
    JobProfileComment,
    JobProfileStatus,
    JobProfileWorkflowState,
    CandidateStatus,
    CandidateWorkflowState,
    SkillLevel,
)

from .db import Database, DatabaseConfig

from .workflows import JobProfileWorkflow, CandidateWorkflow

__all__ = [
    # Models
    'JobProfile',
    'Candidate',
    'JobProfileCandidate',
    'Attachment',
    'WorkflowHistory',
    # Enums
    'JobProfileStatus',
    'JobProfileWorkflowState',
    'CandidateStatus',
    'CandidateWorkflowState',
    'SkillLevel',
    # Database
    'Database',
    'DatabaseConfig',
    # Workflows
    'JobProfileWorkflow',
    'CandidateWorkflow',
]
