"""
Streamlit page for advanced job profile status management
Handles workflow transitions, status changes, and decision making
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
from core.database.workflows import JobProfileWorkflow
from core.database.models import JobProfileStatus, JobProfileWorkflowState
from core.database.translations import initialize_translations, t as get_translation
from core.ui.sidebar_init import render_sidebar_in_page

# Set current page for sidebar
st.session_state.current_page = "pages/03_Stellenprofil-Status.py"

# --- Page Configuration ---
st.set_page_config(
    page_title="Stellenprofil-Status | CV Generator",
    page_icon="⚙️",
    layout="wide"
)

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

def get_status_color(status: str) -> str:
    """Get color code for status"""
    color_map = {
        "draft": "🔵",
        "published": "🟢",
        "active": "🟡",
        "closed": "🔴",
        "archived": "⚫",
        "rejected": "⚪"
    }
    return color_map.get(status, "⚪")

def get_workflow_color(state: str) -> str:
    """Get color code for workflow state"""
    color_map = {
        "draft": "🔵",
        "published": "🟢",
        "closed": "🔴"
    }
    return color_map.get(state, "⚪")

def format_status_badge(status: str) -> str:
    """Format status as a badge"""
    emoji = get_status_color(status)
    return f"{emoji} **{status.upper()}**"

def format_workflow_badge(state: str) -> str:
    """Format workflow state as a badge"""
    emoji = get_workflow_color(state)
    return f"{emoji} **{state.upper()}**"

def get_available_transitions(current_state: str) -> list:
    """Get available state transitions for current workflow state"""
    transitions_map = {
        "draft": [
            {"target": "published", "label": "📤 Veröffentlichen", "description": "Profil wird für Kandidaten sichtbar"},
            {"target": "closed", "label": "🔒 Schließen", "description": "Position wird nicht mehr besetzt"}
        ],
        "published": [
            {"target": "closed", "label": "🔒 Schließen", "description": "Position ist besetzt oder wird nicht mehr besetzt"}
        ],
        "closed": []
    }
    return transitions_map.get(current_state, [])

def get_available_status_changes(current_status: str) -> list:
    """Get available status changes for current status"""
    # Status transitions can be more flexible than workflow states
    # workflow_state controls the main flow, status can change independently
    transitions_map = {
        "draft": [
            {"target": "published", "label": "📤 Zur Veröffentlichung freigeben"},
        ],
        "published": [
            {"target": "active", "label": "✅ Aktiv"},
            {"target": "archived", "label": "📦 Archivieren"},
            {"target": "rejected", "label": "❌ Abgelehnt"},
        ],
        "active": [
            {"target": "closed", "label": "🔒 Schließen"},
            {"target": "archived", "label": "📦 Archivieren"},
        ],
        "closed": [
            {"target": "archived", "label": "📦 Archivieren"},
        ],
        "archived": [],
        "rejected": []
    }
    return transitions_map.get(current_status, [])

# Initialize session state variables
if 'language' not in st.session_state:
    st.session_state.language = "de"

# Set current page for sidebar active state detection
st.session_state.current_page = "pages/03_Stellenprofil-Status.py"

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

# --- Sidebar Navigation ---
tm = get_translations_manager()

# --- Main Content ---
st.title("⚙️ Stellenprofil-Status verwalten")
st.markdown("Verwalten Sie Workflow-Status und Zustandsübergänge für Ihre Stellenprofile.")

st.divider()

# Initialize session state
if "status_detail_view" not in st.session_state:
    st.session_state.status_detail_view = False
if "selected_profile_id" not in st.session_state:
    st.session_state.selected_profile_id = None

db = get_database()
workflow = get_workflow()

# --- Main View: Status Overview Table ---
if not st.session_state.status_detail_view:
    all_profiles = db.get_all_job_profiles()
    
    if not all_profiles:
        st.info("📭 Keine Stellenprofile vorhanden. Erstellen Sie erst ein Profil unter 'Stellenprofile'.")
    else:
        # Filter section
        col_filter1, col_filter2, col_filter3 = st.columns(3)
        
        with col_filter1:
            status_filter = st.multiselect(
                "Nach Status filtern:",
                options=[s.value for s in JobProfileStatus],
                default=[s.value for s in JobProfileStatus],
                key="filter_status"
            )
        
        with col_filter2:
            workflow_filter = st.multiselect(
                "Nach Workflow-Status filtern:",
                options=[s.value for s in JobProfileWorkflowState],
                default=[s.value for s in JobProfileWorkflowState],
                key="filter_workflow"
            )
        
        with col_filter3:
            search_term = st.text_input("Nach Name suchen:", key="filter_search")
        
        st.divider()
        
        # Filter profiles
        filtered_profiles = [
            p for p in all_profiles
            if p.status in status_filter
            and p.current_workflow_state in workflow_filter
            and (not search_term or search_term.lower() in p.name.lower())
        ]
        
        if not filtered_profiles:
            st.warning("⚠️ Keine Profile entsprechen den Filterkriterien.")
        else:
            # Display as table
            table_data = []
            for profile in filtered_profiles:
                table_data.append({
                    "id": profile.id,
                    "Name": profile.name,
                    "Kunde": profile.customer or "-",
                    "Status": f"{get_status_color(profile.status)} {profile.status}",
                    "Workflow": f"{get_workflow_color(profile.current_workflow_state)} {profile.current_workflow_state}",
                    "Level": profile.level,
                    "Erstellt": profile.created_at.strftime("%d.%m.%Y") if profile.created_at else "-",
                    "Skills": len(profile.required_skills)
                })
            
            st.subheader(f"📊 {len(filtered_profiles)} Profil(e) gefunden")
            
            # Create interactive table with expandable rows
            for i, profile in enumerate(filtered_profiles):
                with st.container(border=True):
                    col_main, col_actions = st.columns([3, 1])
                    
                    with col_main:
                        st.markdown(f"### {profile.name}")
                        col_info1, col_info2, col_info3 = st.columns(3)
                        
                        with col_info1:
                            st.markdown(f"**Kunde:** {profile.customer or '-'}")
                            st.markdown(f"**Level:** {profile.level}")
                        
                        with col_info2:
                            st.markdown(f"**Status:** {format_status_badge(profile.status)}")
                            st.markdown(f"**Erstellt:** {profile.created_at.strftime('%d.%m.%Y') if profile.created_at else '-'}")
                        
                        with col_info3:
                            st.markdown(f"**Workflow:** {format_workflow_badge(profile.current_workflow_state)}")
                            st.markdown(f"**Skills:** {len(profile.required_skills)}")
                    
                    with col_actions:
                        if st.button("📋 Details", key=f"detail_btn_{profile.id}", use_container_width=True):
                            st.session_state.status_detail_view = True
                            st.session_state.selected_profile_id = profile.id
                            st.rerun()
                    
                    # Available transitions info
                    transitions = get_available_transitions(profile.current_workflow_state)
                    if transitions:
                        st.caption(f"🔄 **Mögliche Übergänge:** {', '.join([t['label'] for t in transitions])}")
                    else:
                        st.caption("🔒 Keine Übergänge möglich")

# --- Detail View: Status Management ---
else:
    profile_id = st.session_state.selected_profile_id
    profile = db.get_job_profile(profile_id)
    
    if not profile:
        st.error("❌ Profil nicht gefunden")
        if st.button("← Zurück zur Übersicht"):
            st.session_state.status_detail_view = False
            st.rerun()
    else:
        # Back button
        if st.button("← Zurück zur Übersicht"):
            st.session_state.status_detail_view = False
            st.rerun()
        
        st.divider()
        
        # Profile header
        st.title(f"📋 {profile.name}")
        col_header1, col_header2, col_header3 = st.columns(3)
        
        with col_header1:
            st.metric("Kunde", profile.customer or "-")
        with col_header2:
            st.metric("Level", profile.level)
        with col_header3:
            st.metric("Skills", len(profile.required_skills))
        
        st.divider()
        
        # --- Current Status Section ---
        st.subheader("📊 Aktueller Status")
        col_status1, col_status2, col_status3 = st.columns(3)
        
        with col_status1:
            st.markdown(f"**Profil-Status**")
            st.markdown(f"{format_status_badge(profile.status)}", unsafe_allow_html=True)
        
        with col_status2:
            st.markdown(f"**Workflow-Status**")
            st.markdown(f"{format_workflow_badge(profile.current_workflow_state)}", unsafe_allow_html=True)
        
        with col_status3:
            st.markdown(f"**Zuletzt aktualisiert**")
            st.caption(profile.updated_at.strftime("%d.%m.%Y %H:%M") if profile.updated_at else "-")
        
        st.divider()
        
        # --- Workflow Transitions ---
        st.subheader("🔄 Workflow-Übergänge")
        
        transitions = get_available_transitions(profile.current_workflow_state)
        
        if not transitions:
            st.info("✅ Keine weiteren Übergänge möglich. Dieses Profil hat seinen finalen Zustand erreicht.")
        else:
            tab_publish, tab_close = st.tabs([t['label'] for t in transitions])
            
            for idx, (tab, transition) in enumerate(zip([tab_publish, tab_close], transitions)):
                with tab:
                    st.markdown(f"**{transition['label']}**")
                    st.write(transition['description'])
                    
                    if transition['target'] == 'published':
                        st.info("Das Profil wird für Kandidaten und Recruiter sichtbar.")
                        
                        if st.button("✅ Veröffentlichen", key="btn_publish_workflow", use_container_width=True, type="primary"):
                            success, msg = workflow.publish_profile(profile_id, performed_by="system")
                            if success:
                                st.success(f"✅ {msg}")
                                time.sleep(1)
                                st.session_state.status_detail_view = False
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")
                    
                    elif transition['target'] == 'closed':
                        reason = st.text_area(
                            "Grund für Schließung (optional)",
                            placeholder="z.B. Position besetzt, nicht mehr gebraucht, ...",
                            height=80,
                            key="close_reason"
                        )
                        
                        if st.button("🔒 Schließen", key="btn_close_workflow", use_container_width=True, type="primary"):
                            success, msg = workflow.close_profile(profile_id, reason=reason, performed_by="system")
                            if success:
                                st.success(f"✅ {msg}")
                                time.sleep(1)
                                st.session_state.status_detail_view = False
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")
        
        st.divider()
        
        # --- Status Changes (Independent) ---
        st.subheader("🎯 Status-Änderungen")
        st.caption("Unabhängige Statusänderungen (parallel zum Workflow)")
        
        status_transitions = get_available_status_changes(profile.status)
        
        if status_transitions:
            col_trans1, col_trans2 = st.columns(2)
            
            with col_trans1:
                st.markdown("**Verfügbare Statusänderungen:**")
                for transition in status_transitions:
                    st.write(f"• {transition['label']}")
            
            with col_trans2:
                selected_new_status = st.selectbox(
                    "Neuer Status",
                    options=[t['target'] for t in status_transitions],
                    format_func=lambda x: next((t['label'] for t in status_transitions if t['target'] == x), x),
                    key="select_new_status"
                )
                
                if st.button("🔄 Status ändern", use_container_width=True, key="btn_change_status"):
                    # Update only the status field, keep workflow state
                    profile.status = selected_new_status
                    success, msg = db.update_job_profile(profile)
                    
                    if success:
                        st.success(f"✅ Status geändert zu: {selected_new_status}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Status-Änderung fehlgeschlagen: {msg}")
        else:
            st.info("✅ Keine Statusänderungen möglich für diesen Status.")
        
        st.divider()
        
        # --- Workflow History ---
        st.subheader("📜 Workflow-Verlauf")
        
        history = workflow.get_workflow_history(profile_id)
        
        if not history:
            st.info("Noch keine Workflow-Events")
        else:
            for event in reversed(history[-10:]):  # Show last 10 events
                with st.container(border=True):
                    col_h1, col_h2, col_h3 = st.columns([2, 1, 1])
                    
                    with col_h1:
                        st.markdown(f"**{event.action}**")
                        st.caption(event.notes or "-")
                    
                    with col_h2:
                        if event.old_state and event.new_state:
                            st.caption(f"{event.old_state} → {event.new_state}")
                        elif event.new_state:
                            st.caption(f"→ {event.new_state}")
                    
                    with col_h3:
                        st.caption(f"{event.created_at.strftime('%d.%m.%Y %H:%M') if event.created_at else '-'}")
        
        st.divider()
        
        # --- Profile Description ---
        st.subheader("📝 Profil-Beschreibung")
        st.write(profile.description)
