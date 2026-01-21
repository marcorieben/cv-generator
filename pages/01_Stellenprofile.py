"""
Streamlit page for managing job profiles
Handles creation, editing, deletion, and archiving of job profiles
"""

import streamlit as st
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
import sys
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core.database.db import Database
from core.database.workflows import JobProfileWorkflow
from core.database.models import JobProfileStatus, JobProfileWorkflowState

# --- Page Configuration ---
st.set_page_config(
    page_title="Stellenprofile | CV Generator",
    page_icon="📋",
    layout="wide"
)

# --- Helper Functions ---
def load_translations():
    """Load translation file"""
    paths = [
        os.path.join(os.path.dirname(__file__), "..", "scripts", "translations.json"),
        os.path.join("..", "scripts", "translations.json"),
        "scripts/translations.json"
    ]
    
    for trans_path in paths:
        if os.path.exists(trans_path):
            try:
                with open(trans_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading translations: {e}")
                continue
    
    return {"ui": {}, "cv": {}, "offer": {}, "job_profile": {}}

# Global translations
translations = load_translations()

def t(section, key, lang="de"):
    """Get translated text"""
    try:
        return translations.get(section, {}).get(key, {}).get(lang, key)
    except:
        return key

def get_database():
    """Get or create database instance"""
    if "db_instance" not in st.session_state:
        db_path = os.path.join(os.path.dirname(__file__), "..", "data", "cv_generator.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        st.session_state.db_instance = Database(db_path)
    return st.session_state.db_instance

def get_workflow():
    """Get or create workflow instance"""
    if "workflow_instance" not in st.session_state:
        db = get_database()
        st.session_state.workflow_instance = JobProfileWorkflow(db)
    return st.session_state.workflow_instance

def reset_form():
    """Reset form fields"""
    if "form_mode" in st.session_state:
        del st.session_state.form_mode
    if "form_profile_id" in st.session_state:
        del st.session_state.form_profile_id
    if "form_data" in st.session_state:
        del st.session_state.form_data

def load_profile_for_edit(profile_id: int):
    """Load profile data for editing"""
    db = get_database()
    profile = db.get_job_profile(profile_id)
    
    if profile:
        st.session_state.form_mode = "edit"
        st.session_state.form_profile_id = profile_id
        st.session_state.form_data = {
            "name": profile.name,
            "customer": profile.customer or "",
            "description": profile.description,
            "required_skills": profile.required_skills if isinstance(profile.required_skills, list) else [],
            "level": profile.level,
            "status": profile.status,
            "workflow_state": profile.current_workflow_state
        }
        st.rerun()

def is_profile_aged(created_at):
    """Check if profile is older than 10 days"""
    if not created_at:
        return False
    age = datetime.now() - created_at
    return age > timedelta(days=10)

# --- Main Content ---
st.title("📋 Stellenprofile verwalten")
st.markdown("Erstellen, bearbeiten, archivieren und löschen Sie Stellenprofile für Ihre Kandidatensuche.")

st.divider()

# Initialize session state
if "form_mode" not in st.session_state:
    st.session_state.form_mode = None

# --- Tabs for different views ---
tab_list, tab_form = st.tabs(["📊 Übersicht", "➕ Neues Profil / Bearbeiten"])

# =============================================================================
# TAB 1: List View
# =============================================================================
with tab_list:
    db = get_database()
    
    # Get all job profiles
    all_profiles = db.get_all_job_profiles()
    
    if not all_profiles:
        st.info("📭 Keine Stellenprofile vorhanden. Erstellen Sie das erste Profil im Tab 'Neues Profil'.")
    else:
        # Filter options
        col_filter1, col_filter2, col_filter3 = st.columns(3)
        
        with col_filter1:
            status_filter = st.multiselect(
                "Status filtern:",
                options=[s.value for s in JobProfileStatus],
                default=[s.value for s in JobProfileStatus]
            )
        
        with col_filter2:
            workflow_filter = st.multiselect(
                "Workflow-Status filtern:",
                options=[s.value for s in JobProfileWorkflowState],
                default=[s.value for s in JobProfileWorkflowState]
            )
        
        with col_filter3:
            search_term = st.text_input("Nach Name/Kunde suchen:")
        
        st.divider()
        
        # Filter profiles
        filtered_profiles = [
            p for p in all_profiles
            if p.status in status_filter
            and p.current_workflow_state in workflow_filter
            and (not search_term or 
                 search_term.lower() in p.name.lower() or
                 (p.customer and search_term.lower() in p.customer.lower()))
        ]
        
        if not filtered_profiles:
            st.warning("⚠️ Keine Profile entsprechen den Filterkriterien.")
        else:
            # Display profiles in a table-like format
            for profile in filtered_profiles:
                with st.container(border=True):
                    # Age warning
                    if is_profile_aged(profile.created_at):
                        st.warning(f"⏰ Profil älter als 10 Tage (erstellt: {profile.created_at.strftime('%d.%m.%Y')})")
                    
                    col_info, col_meta, col_actions = st.columns([2, 1.5, 1.5])
                    
                    # Profile Info
                    with col_info:
                        st.markdown(f"### {profile.name}")
                        if profile.customer:
                            st.caption(f"👤 Kunde: **{profile.customer}**")
                        st.caption(profile.description[:100] + ("..." if len(profile.description) > 100 else ""))
                        
                        # Skills display
                        if profile.required_skills:
                            skills = profile.required_skills if isinstance(profile.required_skills, list) else []
                            skill_text = ", ".join(skills[:3])
                            if len(skills) > 3:
                                skill_text += f", +{len(skills)-3} mehr"
                            st.caption(f"🔧 Skills: {skill_text}")
                    
                    # Metadata
                    with col_meta:
                        st.metric("Status", profile.status)
                        st.metric("Workflow", profile.current_workflow_state)
                        st.caption(f"Erstellt: {profile.created_at.strftime('%d.%m.%Y')}")
                    
                    # Actions
                    with col_actions:
                        col_edit, col_delete = st.columns(2)
                        
                        with col_edit:
                            if st.button("✏️ Bearbeiten", key=f"edit_{profile.id}"):
                                load_profile_for_edit(profile.id)
                        
                        with col_delete:
                            if st.button("🗑️ Löschen", key=f"delete_{profile.id}"):
                                st.session_state.confirm_delete = True
                                st.session_state.delete_profile_id = profile.id
                        
                        # Workflow state buttons
                        st.divider()
                        
                        workflow = get_workflow()
                        
                        if profile.current_workflow_state == JobProfileWorkflowState.DRAFT.value:
                            if st.button("📤 Veröffentlichen", key=f"publish_{profile.id}", use_container_width=True):
                                success, msg = workflow.publish_profile(profile.id)
                                if success:
                                    st.success(f"✅ {msg}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {msg}")
                        
                        if profile.current_workflow_state == JobProfileWorkflowState.PUBLISHED.value:
                            if st.button("🔒 Schließen", key=f"close_{profile.id}", use_container_width=True):
                                success, msg = workflow.close_profile(profile.id)
                                if success:
                                    st.success(f"✅ {msg}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {msg}")
        
        # Delete confirmation dialog
        if st.session_state.get("confirm_delete"):
            st.divider()
            st.error("⚠️ Profil wirklich löschen?")
            col_confirm_yes, col_confirm_no = st.columns(2)
            
            with col_confirm_yes:
                if st.button("✅ Ja, löschen", use_container_width=True, key="confirm_delete_yes"):
                    db = get_database()
                    success, msg = db.delete_job_profile(st.session_state.delete_profile_id)
                    if success:
                        st.success(f"✅ {msg}")
                        st.session_state.confirm_delete = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
            
            with col_confirm_no:
                if st.button("❌ Abbrechen", use_container_width=True, key="confirm_delete_no"):
                    st.session_state.confirm_delete = False
                    st.rerun()

# =============================================================================
# TAB 2: Create/Edit Form
# =============================================================================
with tab_form:
    db = get_database()
    workflow = get_workflow()
    
    if st.session_state.form_mode == "edit":
        st.subheader("✏️ Stellenprofil bearbeiten")
        profile_id = st.session_state.form_profile_id
        form_data = st.session_state.form_data
        is_edit = True
    else:
        st.subheader("➕ Neues Stellenprofil erstellen")
        form_data = {
            "name": "",
            "customer": "",
            "description": "",
            "required_skills": [],
            "level": "intermediate",
            "status": "active",
            "workflow_state": "draft"
        }
        is_edit = False
    
    st.divider()
    
    # Form fields
    col_name, col_customer = st.columns(2)
    
    with col_name:
        profile_name = st.text_input(
            "Stellenbezeichnung",
            value=form_data.get("name", ""),
            placeholder="z.B. Senior Python Developer",
            key="input_name"
        )
    
    with col_customer:
        customer = st.text_input(
            "Kunde",
            value=form_data.get("customer", ""),
            placeholder="z.B. Acme Corp",
            key="input_customer"
        )
    
    col_level, col_status = st.columns(2)
    
    with col_level:
        level = st.selectbox(
            "Level",
            options=["junior", "intermediate", "senior", "lead"],
            index=["junior", "intermediate", "senior", "lead"].index(form_data.get("level", "intermediate")),
            key="input_level"
        )
    
    # Description
    description = st.text_area(
        "Stellenbeschreibung",
        value=form_data.get("description", ""),
        height=150,
        placeholder="Beschreiben Sie die Position, Anforderungen und Erwartungen...",
        key="input_description"
    )
    
    # Required Skills
    st.subheader("Erforderliche Skills")
    skills_input = st.text_area(
        "Skills (eine pro Zeile)",
        value="\n".join(form_data.get("required_skills", [])),
        height=150,
        placeholder="Python\nDjango\nPostgreSQL\nDocker\nGit",
        key="input_skills"
    )
    
    skills = [s.strip() for s in skills_input.split("\n") if s.strip()]
    
    st.divider()
    
    # Attachments section
    st.subheader("📎 Anhänge")
    uploaded_files = st.file_uploader(
        "PDF-Dateien hochladen",
        type=["pdf"],
        accept_multiple_files=True,
        key="input_attachments"
    )
    
    # Comments section
    st.subheader("💬 Kommentare & Notizen")
    
    if is_edit:
        # Show existing comments
        comments = db.get_comments(profile_id)
        if comments:
            st.write(f"**{len(comments)} Kommentar(e)**")
            for comment in comments:
                with st.container(border=True):
                    st.caption(f"👤 {comment.username} • {comment.created_at.strftime('%d.%m.%Y %H:%M')}")
                    st.write(comment.comment_text)
        
        # Add new comment
        new_comment = st.text_area(
            "Neuer Kommentar hinzufügen",
            placeholder="Geben Sie eine Notiz ein...",
            key="input_new_comment",
            height=100
        )
        
        if st.button("💬 Kommentar hinzufügen", key="btn_add_comment"):
            if new_comment.strip():
                success, msg = db.add_comment(profile_id, "system", new_comment)
                if success:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
            else:
                st.warning("⚠️ Bitte geben Sie einen Kommentar ein")
    
    st.divider()
    
    # Display current metadata if editing
    if is_edit:
        col_status, col_workflow = st.columns(2)
        
        with col_status:
            st.metric("Status", form_data.get("status", "active"))
        
        with col_workflow:
            st.metric("Workflow-Status", form_data.get("workflow_state", "draft"))
    
    st.divider()
    
    # Action buttons
    col_save, col_cancel = st.columns(2)
    
    with col_save:
        if st.button("💾 Speichern", use_container_width=True, type="primary", key="btn_save"):
            # Validation
            if not profile_name or not profile_name.strip():
                st.error("❌ Stellenbezeichnung ist erforderlich")
            elif not description or not description.strip():
                st.error("❌ Stellenbeschreibung ist erforderlich")
            elif not skills:
                st.error("❌ Mindestens ein Skill ist erforderlich")
            else:
                # Save profile
                if is_edit:
                    # Update existing profile
                    from core.database.models import JobProfile
                    profile_to_update = db.get_job_profile(profile_id)
                    if profile_to_update:
                        profile_to_update.name = profile_name
                        profile_to_update.customer = customer if customer else None
                        profile_to_update.description = description
                        profile_to_update.required_skills = skills
                        profile_to_update.level = level
                        success = db.update_job_profile(profile_to_update)
                        msg = f"Stellenprofil '{profile_name}' aktualisiert"
                    else:
                        success = False
                        msg = "Profil nicht gefunden"
                else:
                    # Create new profile
                    from core.database.models import JobProfile
                    new_profile = JobProfile(
                        name=profile_name,
                        customer=customer if customer else None,
                        description=description,
                        required_skills=skills,
                        level=level
                    )
                    profile_id = db.create_job_profile(new_profile)
                    success = profile_id > 0
                    msg = f"Stellenprofil '{profile_name}' erstellt"
                
                if success:
                    st.success(f"✅ {msg}")
                    
                    # Handle file uploads
                    if uploaded_files:
                        for uploaded_file in uploaded_files:
                            # Save file to attachments directory
                            attachments_dir = os.path.join(
                                os.path.dirname(__file__), "..",
                                "data", "attachments", f"job_profile_{profile_id}"
                            )
                            os.makedirs(attachments_dir, exist_ok=True)
                            
                            file_path = os.path.join(attachments_dir, uploaded_file.name)
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            st.success(f"📎 {uploaded_file.name} hochgeladen")
                    
                    st.session_state.form_mode = None
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
    
    with col_cancel:
        if st.button("❌ Abbrechen", use_container_width=True, key="btn_cancel"):
            reset_form()
            st.rerun()
