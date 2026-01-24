"""
Module description

Purpose: analyzed as source_code
Expected Lifetime: permanent
Category: SOURCE_CODE
Created: 2026-01-23
Last Updated: 2026-01-24
"""
from typing import Optional, List, Tuple
from datetime import datetime
from enum import Enum

from .db import Database
from .models import (
    JobProfile, Candidate, JobProfileCandidate, WorkflowHistory,
    JobProfileStatus, JobProfileWorkflowState,
    CandidateStatus, CandidateWorkflowState
)


class JobProfileWorkflow:
    """Manages job profile workflow state transitions"""
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        JobProfileWorkflowState.DRAFT: [
            JobProfileWorkflowState.PUBLISHED,
            JobProfileWorkflowState.CLOSED
        ],
        JobProfileWorkflowState.PUBLISHED: [
            JobProfileWorkflowState.CLOSED,
        ],
        JobProfileWorkflowState.CLOSED: []
    }
    
    def __init__(self, db: Database):
        self.db = db
    
    def create_profile(self, name: str, description: str, 
                      required_skills: List[str],
                      level: str = "intermediate",
                      created_by: Optional[str] = None) -> Tuple[bool, int, str]:
        """
        Create new job profile in draft state
        
        Returns: (success, profile_id, message)
        """
        try:
            profile = JobProfile(
                name=name,
                description=description,
                required_skills=required_skills,
                level=level,
                status=JobProfileStatus.DRAFT,
                current_workflow_state=JobProfileWorkflowState.DRAFT,
                created_by=created_by,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            profile_id = self.db.create_job_profile(profile)
            
            # Log creation
            self.db.log_workflow_transition(WorkflowHistory(
                entity_type='job_profile',
                entity_id=profile_id,
                new_state=JobProfileWorkflowState.DRAFT.value,
                action='created',
                performed_by=created_by,
                notes=f'Created job profile: {name}'
            ))
            
            return True, profile_id, f"Profile '{name}' created successfully"
        
        except Exception as e:
            return False, 0, f"Error creating profile: {str(e)}"
    
    def publish_profile(self, profile_id: int, 
                       performed_by: Optional[str] = None) -> Tuple[bool, str]:
        """Publish job profile (draft → published)"""
        profile = self.db.get_job_profile(profile_id)
        if not profile:
            return False, "Profile not found"
        
        # Validate transition
        if not self._can_transition(profile.current_workflow_state, 
                                   JobProfileWorkflowState.PUBLISHED):
            return False, f"Cannot transition from {profile.current_workflow_state.value} to published"
        
        # Update profile
        profile.current_workflow_state = JobProfileWorkflowState.PUBLISHED
        profile.status = JobProfileStatus.PUBLISHED
        
        if self.db.update_job_profile(profile):
            # Log transition
            self.db.log_workflow_transition(WorkflowHistory(
                entity_type='job_profile',
                entity_id=profile_id,
                old_state=JobProfileWorkflowState.DRAFT.value,
                new_state=JobProfileWorkflowState.PUBLISHED.value,
                action='published',
                performed_by=performed_by,
                notes=f'Profile published: {profile.name}'
            ))
            return True, f"Profile '{profile.name}' published"
        
        return False, "Failed to update profile"
    
    def close_profile(self, profile_id: int, reason: str = "",
                     performed_by: Optional[str] = None) -> Tuple[bool, str]:
        """Close job profile"""
        profile = self.db.get_job_profile(profile_id)
        if not profile:
            return False, "Profile not found"
        
        # Validate transition
        if profile.current_workflow_state == JobProfileWorkflowState.CLOSED:
            return False, "Profile is already closed"
        
        # Update profile
        profile.current_workflow_state = JobProfileWorkflowState.CLOSED
        profile.status = JobProfileStatus.CLOSED
        
        if self.db.update_job_profile(profile):
            # Log transition
            self.db.log_workflow_transition(WorkflowHistory(
                entity_type='job_profile',
                entity_id=profile_id,
                old_state=profile.current_workflow_state.value,
                new_state=JobProfileWorkflowState.CLOSED.value,
                action='closed',
                performed_by=performed_by,
                notes=f'Profile closed. Reason: {reason}'
            ))
            return True, f"Profile '{profile.name}' closed"
        
        return False, "Failed to update profile"
    
    def _can_transition(self, from_state: JobProfileWorkflowState, 
                       to_state: JobProfileWorkflowState) -> bool:
        """Check if state transition is valid"""
        valid_targets = self.VALID_TRANSITIONS.get(from_state, [])
        return to_state in valid_targets
    
    def get_workflow_history(self, profile_id: int) -> List[WorkflowHistory]:
        """Get workflow state history for profile"""
        return self.db.get_workflow_history('job_profile', profile_id)


class CandidateWorkflow:
    """Manages candidate workflow state transitions per job profile"""
    
    # Valid state transitions for candidates
    VALID_TRANSITIONS = {
        CandidateWorkflowState.INITIAL: [
            CandidateWorkflowState.SCREENING,
        ],
        CandidateWorkflowState.SCREENING: [
            CandidateWorkflowState.INTERVIEW,
        ],
        CandidateWorkflowState.INTERVIEW: [
            CandidateWorkflowState.DECISION,
        ],
        CandidateWorkflowState.DECISION: []
    }
    
    def __init__(self, db: Database):
        self.db = db
    
    def add_candidate(self, candidate: Candidate) -> Tuple[bool, int, str]:
        """Add new candidate to system"""
        try:
            if not candidate.first_name or not candidate.last_name:
                return False, 0, "Candidate must have first and last name"
            
            candidate_id = self.db.create_candidate(candidate)
            
            # Log creation
            self.db.log_workflow_transition(WorkflowHistory(
                entity_type='candidate',
                entity_id=candidate_id,
                new_state=CandidateStatus.APPLIED.value,
                action='created',
                notes=f'Added candidate: {candidate.full_name()}'
            ))
            
            return True, candidate_id, f"Candidate '{candidate.full_name()}' added"
        
        except Exception as e:
            return False, 0, f"Error adding candidate: {str(e)}"
    
    def apply_to_profile(self, candidate_id: int, job_profile_id: int) -> Tuple[bool, str]:
        """Add candidate to job profile"""
        candidate = self.db.get_candidate(candidate_id)
        profile = self.db.get_job_profile(job_profile_id)
        
        if not candidate:
            return False, "Candidate not found"
        if not profile:
            return False, "Job profile not found"
        
        try:
            self.db.add_candidate_to_profile(job_profile_id, candidate_id)
            
            # Log application
            self.db.log_workflow_transition(WorkflowHistory(
                entity_type='job_profile_candidate',
                entity_id=job_profile_id,
                new_state=CandidateWorkflowState.INITIAL.value,
                action='applied',
                notes=f'{candidate.full_name()} applied for {profile.name}'
            ))
            
            return True, f"Candidate '{candidate.full_name()}' added to profile '{profile.name}'"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def move_to_screening(self, candidate_id: int, job_profile_id: int,
                         notes: str = "", performed_by: Optional[str] = None) -> Tuple[bool, str]:
        """Move candidate from initial to screening"""
        return self._transition_workflow_state(
            candidate_id, job_profile_id,
            CandidateWorkflowState.INITIAL,
            CandidateWorkflowState.SCREENING,
            'moved_to_screening',
            notes, performed_by
        )
    
    def move_to_interview(self, candidate_id: int, job_profile_id: int,
                         notes: str = "", performed_by: Optional[str] = None) -> Tuple[bool, str]:
        """Move candidate from screening to interview"""
        return self._transition_workflow_state(
            candidate_id, job_profile_id,
            CandidateWorkflowState.SCREENING,
            CandidateWorkflowState.INTERVIEW,
            'moved_to_interview',
            notes, performed_by
        )
    
    def move_to_decision(self, candidate_id: int, job_profile_id: int,
                        notes: str = "", performed_by: Optional[str] = None) -> Tuple[bool, str]:
        """Move candidate from interview to decision"""
        return self._transition_workflow_state(
            candidate_id, job_profile_id,
            CandidateWorkflowState.INTERVIEW,
            CandidateWorkflowState.DECISION,
            'moved_to_decision',
            notes, performed_by
        )
    
    def make_decision(self, candidate_id: int, job_profile_id: int,
                     hired: bool = False, notes: str = "",
                     performed_by: Optional[str] = None) -> Tuple[bool, str]:
        """Make hiring decision for candidate"""
        candidate = self.db.get_candidate(candidate_id)
        profile = self.db.get_job_profile(job_profile_id)
        
        if not candidate or not profile:
            return False, "Candidate or profile not found"
        
        # Update candidate status
        candidate.status = CandidateStatus.HIRED if hired else CandidateStatus.REJECTED
        
        if self.db.update_candidate(candidate):
            # Log decision
            decision = 'hired' if hired else 'rejected'
            self.db.log_workflow_transition(WorkflowHistory(
                entity_type='candidate',
                entity_id=candidate_id,
                old_state=CandidateWorkflowState.DECISION.value,
                new_state=decision,
                action=decision,
                performed_by=performed_by,
                notes=f'{candidate.full_name()} {decision} for {profile.name}. {notes}'
            ))
            
            return True, f"Decision recorded: {candidate.full_name()} {decision}"
        
        return False, "Failed to record decision"
    
    def _transition_workflow_state(self, candidate_id: int, job_profile_id: int,
                                  from_state: CandidateWorkflowState,
                                  to_state: CandidateWorkflowState,
                                  action: str, notes: str = "",
                                  performed_by: Optional[str] = None) -> Tuple[bool, str]:
        """Generic workflow state transition"""
        candidate = self.db.get_candidate(candidate_id)
        profile = self.db.get_job_profile(job_profile_id)
        
        if not candidate or not profile:
            return False, "Candidate or profile not found"
        
        # Validate transition
        if not self._can_transition(from_state, to_state):
            return False, f"Cannot transition from {from_state.value} to {to_state.value}"
        
        # Log transition
        self.db.log_workflow_transition(WorkflowHistory(
            entity_type='candidate',
            entity_id=candidate_id,
            old_state=from_state.value,
            new_state=to_state.value,
            action=action,
            performed_by=performed_by,
            notes=f'{candidate.full_name()} - {profile.name}: {notes}'
        ))
        
        return True, f"{candidate.full_name()} moved to {to_state.value}"
    
    def _can_transition(self, from_state: CandidateWorkflowState,
                       to_state: CandidateWorkflowState) -> bool:
        """Check if state transition is valid"""
        valid_targets = self.VALID_TRANSITIONS.get(from_state, [])
        return to_state in valid_targets
    
    def get_workflow_history(self, candidate_id: int) -> List[WorkflowHistory]:
        """Get workflow history for candidate"""
        return self.db.get_workflow_history('candidate', candidate_id)
