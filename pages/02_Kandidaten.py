"""
Streamlit page for managing candidates
Handles candidate profiles and applications to job profiles
"""

import streamlit as st
import os
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
import sys
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core.database.db import Database
from core.database.workflows import CandidateWorkflow
from core.database.models import CandidateStatus, CandidateWorkflowState
from core.database.translations import initialize_translations, t as get_translation
from core.utils.session import get_database, get_translations_manager, get_text

# Set current page for sidebar
st.session_state.current_page = "pages/02_Kandidaten.py"

# --- Import render_simple_sidebar from app ---
try:
    from app import render_simple_sidebar
except ImportError:
    def render_simple_sidebar():
        """Fallback if sidebar rendering fails"""
        pass


# --- Helper Functions ---
def t(section, key, lang="de"):
    """Get translated text using database-backed translations"""
    return get_text(section, key, lang)


def get_workflow():
    """Get or create workflow instance"""
    if "candidate_workflow_instance" not in st.session_state:
        db = get_database()
        st.session_state.candidate_workflow_instance = CandidateWorkflow(db)
    return st.session_state.candidate_workflow_instance

def reset_form():
    """Reset form fields"""
    if "form_mode" in st.session_state:
        del st.session_state.form_mode
    if "form_candidate_id" in st.session_state:
        del st.session_state.form_candidate_id
    if "form_data" in st.session_state:
        del st.session_state.form_data

def load_candidate_for_edit(candidate_id: int):
    """Load candidate data for editing"""
    db = get_database()
    candidate = db.get_candidate(candidate_id)
    
    if candidate:
        st.session_state.form_mode = "edit"
        st.session_state.form_candidate_id = candidate_id
        st.session_state.form_data = {
            "first_name": candidate.first_name,
            "last_name": candidate.last_name,
            "email": candidate.email,
            "phone": candidate.phone or "",
            "summary": candidate.summary or "",
            "status": candidate.status,
            "workflow_state": candidate.workflow_state
        }
        st.rerun()

# Initialize session state variables
if 'language' not in st.session_state:
    st.session_state.language = "de"

# --- Simple Sidebar with Logo and Navigation ---
render_simple_sidebar()

# --- Sidebar Navigation ---
tm = get_translations_manager()

# --- Main Content ---
st.title("👥 Kandidaten verwalten")
st.markdown("Verwalten Sie Kandidatenprofile und deren Bewerbungen zu Stellenprofilen.")

st.divider()

# Initialize session state
if "form_mode" not in st.session_state:
    st.session_state.form_mode = None

# --- Tabs for different views ---
tab_list, tab_form = st.tabs(["📊 Übersicht", "➕ Neuen Kandidaten / Bearbeiten"])

# =============================================================================
# TAB 1: List View
# =============================================================================
with tab_list:
    db = get_database()
    
    # Get all candidates
    all_candidates = db.get_all_candidates()
    
    if not all_candidates:
        st.info("📭 Keine Kandidaten vorhanden. Erstellen Sie den ersten Kandidaten im Tab 'Neuen Kandidaten'.")
    else:
        # Filter options
        col_filter1, col_filter2, col_filter3 = st.columns(3)
        
        with col_filter1:
            status_filter = st.multiselect(
                "Status filtern:",
                options=[s.value for s in CandidateStatus],
                default=[s.value for s in CandidateStatus]
            )
        
        with col_filter2:
            workflow_filter = st.multiselect(
                "Workflow-Status filtern:",
                options=[s.value for s in CandidateWorkflowState],
                default=[s.value for s in CandidateWorkflowState]
            )
        
        with col_filter3:
            search_term = st.text_input("Nach Name/Email suchen:")
        
        st.divider()
        
        # Filter candidates
        filtered_candidates = [
            c for c in all_candidates
            if c.status in status_filter
            and c.workflow_state in workflow_filter
            and (not search_term or 
                 search_term.lower() in c.first_name.lower() or
                 search_term.lower() in c.last_name.lower() or
                 search_term.lower() in c.email.lower())
        ]
        
        if not filtered_candidates:
            st.warning("⚠️ Keine Kandidaten entsprechen den Filterkriterien.")
        else:
            # Display candidates
            for candidate in filtered_candidates:
                with st.container(border=True):
                    col_info, col_meta, col_actions = st.columns([2, 1.5, 1.5])
                    
                    # Candidate Info
                    with col_info:
                        st.markdown(f"### {candidate.first_name} {candidate.last_name}")
                        st.caption(f"📧 {candidate.email}")
                        if candidate.phone:
                            st.caption(f"📞 {candidate.phone}")
                        if candidate.summary:
                            st.caption(f"📝 {candidate.summary[:100]}...")
                    
                    # Metadata
                    with col_meta:
                        st.metric("Status", candidate.status)
                        st.metric("Workflow", candidate.workflow_state)
                        st.caption(f"Erstellt: {candidate.created_at.strftime('%d.%m.%Y')}")
                    
                    # Actions
                    with col_actions:
                        col_edit, col_delete = st.columns(2)
                        
                        with col_edit:
                            if st.button("✏️ Bearbeiten", key=f"edit_cand_{candidate.id}"):
                                load_candidate_for_edit(candidate.id)
                        
                        with col_delete:
                            if st.button("🗑️ Löschen", key=f"delete_cand_{candidate.id}"):
                                st.session_state.confirm_delete = True
                                st.session_state.delete_candidate_id = candidate.id
        
        # Delete confirmation dialog
        if st.session_state.get("confirm_delete"):
            st.divider()
            st.error("⚠️ Kandidat wirklich löschen?")
            col_confirm_yes, col_confirm_no = st.columns(2)
            
            with col_confirm_yes:
                if st.button("✅ Ja, löschen", use_container_width=True, key="confirm_delete_cand_yes"):
                    db = get_database()
                    success, msg = db.delete_candidate(st.session_state.delete_candidate_id)
                    if success:
                        st.success(f"✅ {msg}")
                        st.session_state.confirm_delete = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
            
            with col_confirm_no:
                if st.button("❌ Abbrechen", use_container_width=True, key="confirm_delete_cand_no"):
                    st.session_state.confirm_delete = False
                    st.rerun()

# =============================================================================
# TAB 2: Create/Edit Form
# =============================================================================
with tab_form:
    db = get_database()
    workflow = get_workflow()
    
    if st.session_state.form_mode == "edit":
        st.subheader("✏️ Kandidat bearbeiten")
        candidate_id = st.session_state.form_candidate_id
        form_data = st.session_state.form_data
        is_edit = True
    else:
        st.subheader("➕ Neuen Kandidaten erstellen")
        form_data = {
            "first_name": "",
            "last_name": "",
            "email": "",
            "phone": "",
            "summary": "",
            "status": "active",
            "workflow_state": "new"
        }
        is_edit = False
    
    st.divider()
    
    # Form fields
    col_first, col_last = st.columns(2)
    
    with col_first:
        first_name = st.text_input(
            "Vorname",
            value=form_data.get("first_name", ""),
            placeholder="z.B. Hans",
            key="input_first_name"
        )
    
    with col_last:
        last_name = st.text_input(
            "Nachname",
            value=form_data.get("last_name", ""),
            placeholder="z.B. Müller",
            key="input_last_name"
        )
    
    # Contact info
    col_email, col_phone = st.columns(2)
    
    with col_email:
        email = st.text_input(
            "E-Mail",
            value=form_data.get("email", ""),
            placeholder="hans.mueller@example.com",
            key="input_email"
        )
    
    with col_phone:
        phone = st.text_input(
            "Telefon (optional)",
            value=form_data.get("phone", ""),
            placeholder="+41 79 123 45 67",
            key="input_phone"
        )
    
    # Summary
    summary = st.text_area(
        "Kurzbeschreibung / Zusammenfassung",
        value=form_data.get("summary", ""),
        height=100,
        placeholder="Beschreiben Sie die Kandidatenprofil kurz...",
        key="input_summary"
    )
    
    st.divider()
    
    # Display current metadata if editing
    if is_edit:
        col_status, col_workflow = st.columns(2)
        
        with col_status:
            st.metric("Status", form_data.get("status", "active"))
        
        with col_workflow:
            st.metric("Workflow-Status", form_data.get("workflow_state", "new"))
    
    st.divider()
    
    # Action buttons
    col_save, col_cancel = st.columns(2)
    
    with col_save:
        if st.button("💾 Speichern", use_container_width=True, type="primary", key="btn_save_cand"):
            # Validation
            if not first_name or not first_name.strip():
                st.error("❌ Vorname ist erforderlich")
            elif not last_name or not last_name.strip():
                st.error("❌ Nachname ist erforderlich")
            elif not email or not email.strip():
                st.error("❌ E-Mail ist erforderlich")
            elif "@" not in email:
                st.error("❌ Gültige E-Mail erforderlich")
            else:
                # Save candidate
                if is_edit:
                    # Update existing candidate
                    success, msg = db.update_candidate(
                        candidate_id,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        phone=phone if phone else None,
                        summary=summary if summary else None
                    )
                else:
                    # Create new candidate
                    success, candidate_id, msg = workflow.add_candidate(
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        phone=phone if phone else None,
                        summary=summary if summary else None
                    )
                
                if success:
                    st.success(f"✅ {msg}")
                    st.session_state.form_mode = None
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
    
    with col_cancel:
        if st.button("❌ Abbrechen", use_container_width=True, key="btn_cancel_cand"):
            reset_form()
            st.rerun()
