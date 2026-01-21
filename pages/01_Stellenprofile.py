"""
Streamlit page for managing job profiles
Handles creation, editing, deletion, and archiving of job profiles
"""

import streamlit as st
import os
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
from core.database.translations import initialize_translations, t as get_translation
from core.ui.sidebar_init import render_sidebar_in_page

# Set current page for sidebar
st.session_state.current_page = "pages/01_Stellenprofile.py"

# --- Page Configuration ---
st.set_page_config(
    page_title="Stellenprofile | CV Generator",
    page_icon="📋",
    layout="wide"
)

# --- Import get_text from app for translations ---
try:
    from app import get_text
except ImportError:
    def get_text(section, key, lang="de"):
        """Fallback if app import fails"""
        return key

# --- Helper Functions ---
def get_translations_manager():
    """Get or initialize translations manager"""
    if "translations_manager" not in st.session_state:
        db = get_database()
        st.session_state.translations_manager = initialize_translations(db)
    return st.session_state.translations_manager

def t(section, key, lang="de"):
    """Get translated text using database-backed translations"""
    try:
        tm = get_translations_manager()
        return tm.get(section, key, lang) or key
    except Exception as e:
        print(f"⚠️ Translation error: {e}, falling back to key: {key}")
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

def format_status(status_value):
    """Format status with color and translated text"""
    # Extract just the value part if it's an Enum representation
    if isinstance(status_value, str):
        status = status_value.split('.')[-1].lower() if '.' in status_value else status_value.lower()
    else:
        status = str(status_value).split('.')[-1].lower()
    
    # Emoji config
    emoji_map = {
        "draft": "🔵",
        "published": "🟡",
        "active": "🟠",
        "closed": "🟢",
        "archived": "⚫",
        "rejected": "⚪",
    }
    
    emoji = emoji_map.get(status, "⚪")
    # Get translated text from database
    translated_text = get_text("status_values", status, st.session_state.language)
    return f"{emoji} {translated_text}"

def format_workflow(workflow_value):
    """Format workflow with color and translated text"""
    # Extract just the value part if it's an Enum representation
    if isinstance(workflow_value, str):
        workflow = workflow_value.split('.')[-1].lower() if '.' in workflow_value else workflow_value.lower()
    else:
        workflow = str(workflow_value).split('.')[-1].lower()
    
    # Emoji config
    emoji_map = {
        "draft": "🔵",
        "published": "🟡",
        "closed": "🟢",
    }
    
    emoji = emoji_map.get(workflow, "⚪")
    # Get translated text from database
    translated_text = get_text("workflow_values", workflow, st.session_state.language)
    return f"{emoji} {translated_text}"

def load_profile_for_edit(profile_id: int):
    """Load profile data for editing"""
    db = get_database()
    profile = db.get_job_profile(profile_id)
    
    if profile:
        st.session_state.form_mode = "edit"
        st.session_state.form_profile_id = profile_id
        
        # Format timestamps
        created_at_str = profile.created_at.strftime('%d.%m.%Y %H:%M') if profile.created_at else "—"
        updated_at_str = profile.updated_at.strftime('%d.%m.%Y %H:%M') if profile.updated_at else "—"
        
        st.session_state.form_data = {
            "name": profile.name,
            "customer": profile.customer or "",
            "description": profile.description,
            "required_skills": profile.required_skills if isinstance(profile.required_skills, list) else [],
            "level": profile.level,
            "status": profile.status,
            "workflow_state": profile.current_workflow_state,
            "created_at": created_at_str,
            "updated_at": updated_at_str,
            "attachment_blob": profile.attachment_blob,
            "attachment_filename": profile.attachment_filename
        }
        st.rerun()

def is_profile_aged(created_at):
    """Check if profile is older than 10 days"""
    if not created_at:
        return False
    
    # Handle string datetime from database
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return False
    
    age = datetime.now() - created_at
    return age > timedelta(days=10)

# Initialize session state variables
if 'language' not in st.session_state:
    st.session_state.language = "de"

# Set current page for sidebar active state detection
st.session_state.current_page = "pages/01_Stellenprofile.py"

# --- Render Sidebar ---
if st.session_state.get("authentication_status"):
    try:
        from app import get_text, authenticator, config, name, username
        render_sidebar_in_page(
            get_text_func=get_text,
            language=st.session_state.language,
            authenticator=authenticator,
            name=name,
            username=username,
            config=config
        )
    except ImportError:
        st.sidebar.warning("Sidebar konnte nicht geladen werden")

# --- Main Content ---
st.title("📋 Stellenprofile verwalten")
st.markdown("Erstellen, bearbeiten, archivieren und löschen Sie Stellenprofile für Ihre Kandidatensuche.")

st.divider()

# Initialize session state
if "form_mode" not in st.session_state:
    st.session_state.form_mode = None

# Choose view based on form_mode
if st.session_state.form_mode == "edit":
    # Direct Edit View
    view_mode = "edit"
else:
    # Tab View (Übersicht + Neues)
    view_mode = "tabs"

# =============================================================================
# TAB VIEW: Show Tabs (Übersicht + Neues)
# =============================================================================
if view_mode == "tabs":
    # --- Tabs for different views ---
    tab_overview, tab_new = st.tabs(["📊 Übersicht", "➕ Neues Profil anlegen"])
    
    # TAB 1: Overview
    with tab_overview:
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
            
            # Sorting options
            sort_col1, sort_col2 = st.columns([2, 1])
            with sort_col1:
                sort_by = st.selectbox(
                    "Sortieren nach:",
                    options=["ID", "Name", "Kunde", "Status", "Workflow", "Erstellt", "Zuletzt bearbeitet"],
                    index=6,
                    key="sort_by"
                )
            with sort_col2:
                sort_order = st.selectbox(
                    "Reihenfolge:",
                    options=["↑ Aufsteigend", "↓ Absteigend"],
                    index=1,
                    key="sort_order"
                )
            
            # Apply sorting
            reverse_sort = sort_order.startswith("↓")
            
            if sort_by == "ID":
                filtered_profiles.sort(key=lambda p: p.id, reverse=reverse_sort)
            elif sort_by == "Name":
                filtered_profiles.sort(key=lambda p: p.name.lower(), reverse=reverse_sort)
            elif sort_by == "Kunde":
                filtered_profiles.sort(key=lambda p: (p.customer or "").lower(), reverse=reverse_sort)
            elif sort_by == "Status":
                filtered_profiles.sort(key=lambda p: p.status, reverse=reverse_sort)
            elif sort_by == "Workflow":
                filtered_profiles.sort(key=lambda p: p.current_workflow_state, reverse=reverse_sort)
            elif sort_by == "Erstellt":
                filtered_profiles.sort(key=lambda p: p.created_at or "", reverse=reverse_sort)
            elif sort_by == "Zuletzt bearbeitet":
                filtered_profiles.sort(key=lambda p: p.updated_at or "", reverse=reverse_sort)
            
            st.divider()
            
            if not filtered_profiles:
                st.warning("⚠️ Keine Profile entsprechen den Filterkriterien.")
            else:
                # Display table headers
                col0, col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.5, 2, 1.5, 2, 1, 1, 1, 1, 1], gap="small")
                
                with col0:
                    st.write(f"**{get_text('ui', 'job_profile_attr_id', st.session_state.language)}**")
                with col1:
                    st.write(f"**{get_text('ui', 'job_profile_column_name', st.session_state.language)}**")
                with col2:
                    st.write(f"**{get_text('ui', 'job_profile_column_customer', st.session_state.language)}**")
                with col3:
                    st.write(f"**{get_text('ui', 'job_profile_column_skills', st.session_state.language)}**")
                with col4:
                    st.write(f"**{get_text('ui', 'job_profile_column_status', st.session_state.language)}**")
                with col5:
                    st.write(f"**{get_text('ui', 'job_profile_column_workflow', st.session_state.language)}**")
                with col6:
                    st.write(f"**{get_text('ui', 'job_profile_column_created', st.session_state.language)}**")
                with col7:
                    st.write(f"**{get_text('ui', 'job_profile_column_modified', st.session_state.language)}**")
                with col8:
                    st.write(f"**{get_text('ui', 'job_profile_column_action', st.session_state.language)}**")
                
                st.divider()
                
                # Display interactive rows for each profile
                for idx, profile in enumerate(filtered_profiles):
                    # Create interactive row for each profile
                    col0, col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.5, 2, 1.5, 2, 1, 1, 1, 1, 1], gap="small")
                    
                    # ID
                    with col0:
                        st.write(f"{profile.id}")
                    
                    # Name
                    with col1:
                        st.write(f"{profile.name}")
                    
                    # Customer
                    with col2:
                        st.write(profile.customer or "-")
                    
                    # Skills
                    with col3:
                        skills_display = ""
                        if profile.required_skills:
                            skills = profile.required_skills if isinstance(profile.required_skills, list) else []
                            skills_display = ", ".join(skills[:2])
                            if len(skills) > 2:
                                skills_display += f", +{len(skills)-2}"
                        else:
                            skills_display = "-"
                        
                        # Check for attachments in BLOB field
                        if profile.attachment_blob and profile.attachment_filename:
                            st.write(f"{skills_display} 📎")
                        else:
                            st.write(skills_display)
                    
                    # Status
                    with col4:
                        status_options = [s.value for s in JobProfileStatus]
                        status_display = [format_status(s) for s in status_options]
                        current_index = status_options.index(profile.status)
                        selected_display = st.selectbox(
                            "Status",
                            options=status_display,
                            index=current_index,
                            key=f"status_select_{profile.id}",
                            label_visibility="collapsed"
                        )
                        new_status = status_options[status_display.index(selected_display)]
                        if new_status != profile.status:
                            profile.status = JobProfileStatus(new_status)
                            db.update_job_profile(profile)
                            st.rerun()
                    
                    # Workflow
                    with col5:
                        workflow_options = [w.value for w in JobProfileWorkflowState]
                        workflow_display = [format_workflow(w) for w in workflow_options]
                        current_index = workflow_options.index(profile.current_workflow_state)
                        selected_display = st.selectbox(
                            "Workflow",
                            options=workflow_display,
                            index=current_index,
                            key=f"workflow_select_{profile.id}",
                            label_visibility="collapsed"
                        )
                        new_workflow = workflow_options[workflow_display.index(selected_display)]
                        if new_workflow != profile.current_workflow_state:
                            profile.current_workflow_state = JobProfileWorkflowState(new_workflow)
                            db.update_job_profile(profile)
                            st.rerun()
                    
                    # Created date
                    with col6:
                        created_text = profile.created_at.strftime('%d.%m.%Y %H:%M') if profile.created_at else "-"
                        st.write(created_text)
                    
                    # Modified date
                    with col7:
                        modified_text = profile.updated_at.strftime('%d.%m.%Y %H:%M') if profile.updated_at else (profile.created_at.strftime('%d.%m.%Y %H:%M') if profile.created_at else "-")
                        st.write(modified_text)
                    
                    # Actions
                    with col8:
                        col_edit, col_delete = st.columns(2, gap="small")
                        with col_edit:
                            if st.button(f"✏️", key=f"edit_{profile.id}", help=get_text('ui', 'edit', st.session_state.language), use_container_width=True):
                                load_profile_for_edit(profile.id)
                        with col_delete:
                            if st.button(f"🗑️", key=f"delete_{profile.id}", help=get_text('ui', 'delete', st.session_state.language), use_container_width=True):
                                st.session_state.confirm_delete = True
                                st.session_state.delete_profile_id = profile.id
            
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
        # TAB 2: Create New Profile
        # =============================================================================
    with tab_new:
        db = get_database()
        workflow = get_workflow()
        
        st.subheader("➕ Neues Stellenprofil erstellen")
        profile_id = None  # No profile ID for new profiles
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
                                # Save file to database as BLOB
                                file_blob = uploaded_file.getbuffer()
                                
                                # Update profile with attachment blob
                                profile_to_save = db.get_job_profile(profile_id)
                                if profile_to_save:
                                    profile_to_save.attachment_blob = file_blob.tobytes()
                                    profile_to_save.attachment_filename = uploaded_file.name
                                    db.update_job_profile(profile_to_save)
                                    st.success(f"📎 {uploaded_file.name} gespeichert")
                        
                        st.session_state.form_mode = None
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
        
        with col_cancel:
            if st.button("❌ Abbrechen", use_container_width=True, key="btn_cancel"):
                reset_form()
                st.rerun()

# =============================================================================
# EDIT VIEW: Direct Edit Form
# =============================================================================
elif view_mode == "edit":
    db = get_database()
    workflow = get_workflow()
    
    profile_id = st.session_state.form_profile_id
    form_data = st.session_state.form_data
    is_edit = True
    
    # Back button
    if st.button("← Zurück zur Übersicht"):
        reset_form()
        st.rerun()
    
    st.subheader("✏️ Stellenprofil bearbeiten")
    st.divider()
    
    # ROW 1: Status / Workflow / Created / Modified / Alter
    profile = db.get_job_profile(profile_id)
    if profile:
        # Calculate age (days since creation)
        from datetime import datetime, timedelta
        if profile.created_at:
            age_days = (datetime.now() - profile.created_at).days
            age_text = f"{age_days}d"
        else:
            age_text = "-"
        
        # METADATA SECTION HEADER
        st.write(f"**{get_text('ui', 'job_profile_metadata_section', st.session_state.language)}**")
        
        col0, col1, col2, col3, col4, col5 = st.columns([0.8, 1, 1, 1, 1, 1], gap="small")
        
        with col0:
            st.caption(f"{get_text('ui', 'job_profile_attr_id', st.session_state.language)}")
            st.write(f"**{profile_id}**")
        
        with col1:
            st.caption(f"{get_text('ui', 'job_profile_attr_status', st.session_state.language)}")
            status_value = form_data.get("status", "active")
            status_options = [s.value for s in JobProfileStatus]
            status_display = [format_status(s) for s in status_options]
            current_index = status_options.index(status_value)
            selected_display = st.selectbox(
                "Status",
                options=status_display,
                index=current_index,
                key="input_status_edit",
                label_visibility="collapsed"
            )
            st.session_state.input_status_edit_value = status_options[status_display.index(selected_display)]
        
        with col2:
            st.caption(f"{get_text('ui', 'job_profile_attr_workflow', st.session_state.language)}")
            workflow_value = form_data.get("workflow_state", "draft")
            workflow_options = [w.value for w in JobProfileWorkflowState]
            workflow_display = [format_workflow(w) for w in workflow_options]
            current_index = workflow_options.index(workflow_value)
            selected_display = st.selectbox(
                "Workflow",
                options=workflow_display,
                index=current_index,
                key="input_workflow_edit",
                label_visibility="collapsed"
            )
            st.session_state.input_workflow_edit_value = workflow_options[workflow_display.index(selected_display)]
        
        with col3:
            st.caption(f"{get_text('ui', 'job_profile_attr_created_at', st.session_state.language)}")
            st.write(f"{form_data.get('created_at', '—')}")
        
        with col4:
            st.caption(f"{get_text('ui', 'job_profile_attr_updated_at', st.session_state.language)}")
            st.write(f"{form_data.get('updated_at', '—')}")
        
        with col5:
            st.caption(f"{get_text('ui', 'job_profile_attr_age', st.session_state.language)}")
            st.write(f"{age_text}")
        
        # DETAILS SECTION HEADER
        st.write(f"**{get_text('ui', 'job_profile_details_section', st.session_state.language)}**")
        
        # ROW 2: Name / Customer / Level / Anhang
        col1b, col2b, col3b, col4b = st.columns(4, gap="small")
        
        with col1b:
            st.caption(f"{get_text('ui', 'job_profile_attr_name', st.session_state.language)}")
            profile_name = st.text_input(
                "Stellenbezeichnung",
                value=form_data.get("name", ""),
                placeholder="z.B. Senior Python Developer",
                key="input_name_edit",
                label_visibility="collapsed"
            )
        
        with col2b:
            st.caption(f"{get_text('ui', 'job_profile_attr_customer', st.session_state.language)}")
            customer = st.text_input(
                "Kunde",
                value=form_data.get("customer", ""),
                placeholder="z.B. Acme Corp",
                key="input_customer_edit",
                label_visibility="collapsed"
            )
        
        with col3b:
            st.caption(f"{get_text('ui', 'job_profile_attr_level', st.session_state.language)}")
            level = st.selectbox(
                "Level",
                options=["junior", "intermediate", "senior", "lead"],
                index=["junior", "intermediate", "senior", "lead"].index(form_data.get("level", "intermediate")),
                key="input_level_edit",
                label_visibility="collapsed"
            )
        
        with col4b:
            st.caption(f"{get_text('ui', 'job_profile_attr_attachment', st.session_state.language)}")
            
            # Show existing attachment if present
            if form_data.get("attachment_blob") and form_data.get("attachment_filename"):
                col_dl, col_del = st.columns([0.9, 0.1], gap="small")
                with col_dl:
                    st.download_button(
                        label=f"⬇️ {form_data.get('attachment_filename')}",
                        data=form_data.get("attachment_blob"),
                        file_name=form_data.get("attachment_filename"),
                        use_container_width=True,
                        key=f"download_attachment_{profile_id}",
                        help=f"Downloaden: {form_data.get('attachment_filename')}"
                    )
                with col_del:
                    if st.button(f"🗑️", key=f"delete_attachment_{profile_id}", help="Anhang löschen"):
                        # Clear attachment
                        profile_to_clear = db.get_job_profile(profile_id)
                        if profile_to_clear:
                            profile_to_clear.attachment_blob = None
                            profile_to_clear.attachment_filename = None
                            db.update_job_profile(profile_to_clear)
                            st.success("📎 Anhang gelöscht")
                            st.rerun()
                st.caption("💡 Max. 1 Anhang pro Profil. Löschen um neuen hochzuladen.")
            else:
                st.file_uploader(
                    "Anhang",
                    accept_multiple_files=False,
                    key="input_attachments_edit",
                    label_visibility="collapsed"
                )
        
        st.divider()
        
        # DESCRIPTION SECTION HEADER
        st.write(f"**{get_text('ui', 'job_profile_description_section', st.session_state.language)}**")
        
        st.caption(f"{get_text('ui', 'job_profile_attr_description', st.session_state.language)}")
        # Description
        description = st.text_area(
            "Stellenbeschreibung",
            value=form_data.get("description", ""),
            height=150,
            placeholder="Beschreiben Sie die Position, Anforderungen und Erwartungen...",
            key="input_description_edit",
            label_visibility="collapsed"
        )
        
        # SKILLS SECTION HEADER
        st.write(f"**{get_text('ui', 'job_profile_skills_section', st.session_state.language)}**")
        
        st.caption(f"{get_text('ui', 'job_profile_attr_skills', st.session_state.language)}")
        # Required Skills
        skills_input = st.text_area(
            "Skills (eine pro Zeile)",
            value="\n".join(form_data.get("required_skills", [])),
            height=150,
            placeholder="Python\nDjango\nPostgreSQL\nDocker\nGit",
            key="input_skills_edit",
            label_visibility="collapsed"
        )
        
        skills = [s.strip() for s in skills_input.split("\n") if s.strip()]
        
        st.divider()
        
        # Action buttons
        col_save, col_cancel = st.columns(2)
        
        with col_save:
            if st.button("💾 Speichern", use_container_width=True, type="primary", key="btn_save_edit"):
                # Validation
                if not profile_name or not profile_name.strip():
                    st.error("❌ Stellenbezeichnung ist erforderlich")
                elif not description or not description.strip():
                    st.error("❌ Stellenbeschreibung ist erforderlich")
                elif not skills:
                    st.error("❌ Mindestens ein Skill ist erforderlich")
                else:
                    # Update existing profile
                    from core.database.models import JobProfile
                    profile_to_update = db.get_job_profile(profile_id)
                    if profile_to_update:
                        profile_to_update.name = profile_name
                        profile_to_update.customer = customer
                        profile_to_update.description = description
                        profile_to_update.required_skills = skills
                        profile_to_update.level = level
                        profile_to_update.status = JobProfileStatus(st.session_state.get("input_status_edit_value", form_data.get("status", "active")))
                        profile_to_update.current_workflow_state = JobProfileWorkflowState(st.session_state.get("input_workflow_edit_value", form_data.get("workflow_state", "draft")))
                        
                        # Handle file uploads (only new files from st.file_uploader)
                        uploaded_files = st.session_state.get("input_attachments_edit")
                        if uploaded_files and not form_data.get("attachment_blob"):
                            # Only upload if no existing attachment
                            uploaded_file = uploaded_files
                            if hasattr(uploaded_file, 'getbuffer'):
                                file_blob = uploaded_file.getbuffer()
                                profile_to_update.attachment_blob = file_blob.tobytes()
                                profile_to_update.attachment_filename = uploaded_file.name
                        
                        success = db.update_job_profile(profile_to_update)
                        if success:
                            st.success(f"✅ Stellenprofil '{profile_name}' aktualisiert")
                            if uploaded_files and not form_data.get("attachment_blob"):
                                st.success(f"📎 Anhang gespeichert")
                            reset_form()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ Fehler beim Speichern")
        
        with col_cancel:
            if st.button("❌ Abbrechen", use_container_width=True, key="btn_cancel_edit"):
                reset_form()
                st.rerun()
    else:
        st.error("Profil nicht gefunden")
