"""
Batch Comparison Results Display & Dashboard Module

Handles visualization of batch comparison results including:
- Comparison dashboard with 3-panel layout
- Per-candidate result expanders
- Criteria table from job profile
- File persistence with naming conventions
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px


def get_batch_output_dir(job_profile_name: str, timestamp: str) -> str:
    """
    Generate batch output directory path following convention:
    jobprofile_batch-comparison_timestamp
    """
    # Extract job profile name without extension
    job_name = os.path.splitext(job_profile_name)[0] if '.' in job_profile_name else job_profile_name
    
    base_output = os.path.join(os.getcwd(), "output", "batch_comparison")
    os.makedirs(base_output, exist_ok=True)
    
    # Create batch folder with naming convention
    batch_folder = f"{job_name}_batch-comparison_{timestamp}"
    batch_path = os.path.join(base_output, batch_folder)
    os.makedirs(batch_path, exist_ok=True)
    
    return batch_path


def get_candidate_output_dir(batch_dir: str, candidate_name: str, timestamp: str) -> str:
    """
    Generate candidate output directory within batch folder:
    batch_dir/jobprofile_candidateName_timestamp
    """
    # Extract base job name from batch folder
    batch_basename = os.path.basename(batch_dir)
    job_name = batch_basename.split("_batch-comparison_")[0]
    
    # Create candidate subfolder
    candidate_folder = f"{job_name}_{candidate_name}_{timestamp}"
    candidate_path = os.path.join(batch_dir, candidate_folder)
    os.makedirs(candidate_path, exist_ok=True)
    
    return candidate_path


def move_candidate_files_to_batch(results: Dict[str, Any], batch_dir: str, candidate_name: str, timestamp: str) -> Dict[str, str]:
    """
    Move all candidate result files to the batch directory structure.
    Returns dict mapping file types to their new paths.
    """
    candidate_dir = get_candidate_output_dir(batch_dir, candidate_name, timestamp)
    
    file_mapping = {}
    
    # Define files to move and their target names
    files_to_move = {
        "word_path": "cv.docx",
        "cv_json": "cv_data.json",
        "dashboard_path": "dashboard.html",
        "match_json": "match_result.json",
        "stellenprofil_json": "job_profile.json",
        # "feedback_path" if it exists
    }
    
    for source_key, target_name in files_to_move.items():
        if source_key in results and results[source_key]:
            source_path = results[source_key]
            if os.path.exists(source_path):
                target_path = os.path.join(candidate_dir, target_name)
                try:
                    # Copy file to batch directory
                    import shutil
                    shutil.copy2(source_path, target_path)
                    file_mapping[source_key] = target_path
                except Exception as e:
                    print(f"Warning: Could not copy {source_key}: {e}")
    
    return file_mapping


def parse_job_profile_criteria(job_profile_json_path: str) -> Optional[Dict[str, List[str]]]:
    """
    Parse job profile to extract Muss (must-have) and Soll (nice-to-have) criteria.
    Returns dict with keys: "Muss" and "Soll", each containing lists of criteria.
    """
    if not job_profile_json_path or not os.path.exists(job_profile_json_path):
        return None
    
    try:
        with open(job_profile_json_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)
        
        muss = []
        soll = []
        
        # Extract from common fields in job profile
        if isinstance(profile, dict):
            # Look for requirements/criteria sections
            for key in ["Anforderungen", "Requirements", "Kriterien", "Criteria"]:
                if key in profile:
                    req_data = profile[key]
                    if isinstance(req_data, dict):
                        muss.extend(req_data.get("Muss", req_data.get("Required", [])))
                        soll.extend(req_data.get("Soll", req_data.get("Nice_to_have", [])))
        
        return {"Muss": muss, "Soll": soll} if (muss or soll) else None
    except Exception as e:
        print(f"Error parsing job profile criteria: {e}")
        return None


def create_criteria_table(criteria: Optional[Dict[str, List[str]]], language: str = "de"):
    """
    Display criteria table from job profile with Muss/Soll clustering.
    """
    if not criteria:
        st.info("📋 Job profile criteria could not be extracted")
        return
    
    st.subheader("📋 Anforderungen" if language == "de" else "📋 Requirements")
    
    # Create columns for Muss and Soll
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔴 Muss (Required)**")
        if criteria.get("Muss"):
            for item in criteria["Muss"]:
                st.write(f"• {item}")
        else:
            st.write("(keine)")
    
    with col2:
        st.markdown("**🟡 Soll (Nice-to-have)**")
        if criteria.get("Soll"):
            for item in criteria["Soll"]:
                st.write(f"• {item}")
        else:
            st.write("(keine)")


def create_match_score_chart(results: List[Dict[str, Any]], language: str = "de") -> go.Figure:
    """
    Create vertical bar chart for match scores (best=green, others=grey).
    Frame 1: Total Match Score
    """
    candidate_names = []
    match_scores = []
    colors = []
    
    # Get max score to determine color (best=green)
    max_score = max([r.get("match_score", 0) for r in results], default=0)
    
    for result in results:
        if result.get("success"):
            name = f"{result.get('vorname', 'Unknown')} {result.get('nachname', '')}".strip()
            score = result.get("match_score", 0)
            
            candidate_names.append(name)
            match_scores.append(score)
            
            # Color: green if best, grey otherwise
            if score == max_score and max_score > 0:
                colors.append("rgba(76, 175, 80, 0.8)")  # Green
            else:
                colors.append("rgba(158, 158, 158, 0.8)")  # Grey
    
    fig = go.Figure(data=go.Bar(
        x=candidate_names,
        y=match_scores,
        marker=dict(color=colors),
        text=[f"{s}%" for s in match_scores],
        textposition="auto",
    ))
    
    title = "Gesamtübereinstimmung (%)" if language == "de" else "Total Match Score (%)"
    fig.update_layout(
        title=title,
        xaxis_title="Kandidat" if language == "de" else "Candidate",
        yaxis_title="Match Score (%)",
        height=300,
        template="plotly_white",
        showlegend=False
    )
    
    return fig


def create_must_soll_chart(results: List[Dict[str, Any]], language: str = "de") -> go.Figure:
    """
    Create stacked bar chart for Muss/Soll coverage per candidate.
    Frame 2: Muss/Soll Coverage
    """
    candidate_names = []
    muss_coverage = []
    soll_coverage = []
    
    for result in results:
        if result.get("success"):
            name = f"{result.get('vorname', 'Unknown')} {result.get('nachname', '')}".strip()
            
            # Extract coverage from match results
            match_data = result.get("match_json")
            muss = 0
            soll = 0
            
            if match_data and os.path.exists(match_data):
                try:
                    with open(match_data, 'r', encoding='utf-8') as f:
                        match = json.load(f)
                        muss = match.get("Muss_coverage", 0)
                        soll = match.get("Soll_coverage", 0)
                except:
                    pass
            
            candidate_names.append(name)
            muss_coverage.append(muss)
            soll_coverage.append(soll)
    
    fig = go.Figure(data=[
        go.Bar(name="Muss" if language == "de" else "Must-have", x=candidate_names, y=muss_coverage, marker_color="rgba(244, 67, 54, 0.8)"),
        go.Bar(name="Soll" if language == "de" else "Nice-to-have", x=candidate_names, y=soll_coverage, marker_color="rgba(255, 193, 7, 0.8)")
    ])
    
    title = "Anforderungsabdeckung (%)" if language == "de" else "Requirements Coverage (%)"
    fig.update_layout(
        title=title,
        xaxis_title="Kandidat" if language == "de" else "Candidate",
        yaxis_title="Coverage (%)",
        barmode="stack",
        height=300,
        template="plotly_white"
    )
    
    return fig


def create_quality_chart(results: List[Dict[str, Any]], language: str = "de") -> go.Figure:
    """
    Create bar chart for CV quality/critical points.
    Frame 3: CV Quality
    """
    candidate_names = []
    quality_scores = []
    
    for result in results:
        if result.get("success"):
            name = f"{result.get('vorname', 'Unknown')} {result.get('nachname', '')}".strip()
            
            # Quality score could be derived from match score or feedback
            quality = result.get("match_score", 0)
            
            candidate_names.append(name)
            quality_scores.append(quality)
    
    fig = go.Figure(data=go.Bar(
        x=candidate_names,
        y=quality_scores,
        marker=dict(color="rgba(33, 150, 243, 0.8)"),
        text=[f"{s}%" for s in quality_scores],
        textposition="auto",
    ))
    
    title = "CV-Qualität (%)" if language == "de" else "CV Quality (%)"
    fig.update_layout(
        title=title,
        xaxis_title="Kandidat" if language == "de" else "Candidate",
        yaxis_title="Quality Score (%)",
        height=300,
        template="plotly_white",
        showlegend=False
    )
    
    return fig


def display_batch_comparison_dashboard(results: List[Dict[str, Any]], job_profile_json: Optional[str], language: str = "de"):
    """
    Display the 3-panel batch comparison dashboard.
    """
    st.subheader("📊 Vergleichs-Dashboard" if language == "de" else "📊 Comparison Dashboard")
    
    # Create 3 columns for the 3 panels
    col1, col2, col3 = st.columns(3)
    
    with col1:
        try:
            fig1 = create_match_score_chart(results, language)
            st.plotly_chart(fig1, width='stretch')
        except Exception as e:
            st.error(f"Error creating match score chart: {e}")
    
    with col2:
        try:
            fig2 = create_must_soll_chart(results, language)
            st.plotly_chart(fig2, width='stretch')
        except Exception as e:
            st.error(f"Error creating Muss/Soll chart: {e}")
    
    with col3:
        try:
            fig3 = create_quality_chart(results, language)
            st.plotly_chart(fig3, width='stretch')
        except Exception as e:
            st.error(f"Error creating quality chart: {e}")
    
    st.divider()
    
    # Display criteria table
    if job_profile_json:
        criteria = parse_job_profile_criteria(job_profile_json)
        create_criteria_table(criteria, language)


def display_candidate_expander(result: Dict[str, Any], batch_dir: str, language: str = "de"):
    """
    Display per-candidate expander with Mode 2/3 dashboard (identical HTML).
    """
    if not result.get("success"):
        st.error(f"❌ {result.get('cv_file', 'Unknown')} - {result.get('error', 'Processing failed')}")
        return
    
    candidate_name = f"{result.get('vorname', 'Unknown')} {result.get('nachname', '')}".strip()
    match_score = result.get("match_score", 0)
    
    # Determine color based on score
    score_color = "#4CAF50" if match_score >= 70 else "#FF9800" if match_score >= 50 else "#F44336"
    badge_text = f"📊 {candidate_name} - {match_score}%"
    
    with st.expander(badge_text, expanded=False):
        # Embedded Mode 2/3 Dashboard (identical HTML)
        dashboard_html_path = result.get("dashboard_path")
        if dashboard_html_path and os.path.exists(dashboard_html_path):
            with open(dashboard_html_path, "r", encoding="utf-8") as f:
                dashboard_html = f.read()
                st.components.v1.html(dashboard_html, height=1200, scrolling=True)
        else:
            st.warning("Dashboard not available")
        
        st.divider()
        
        # Downloads
        st.markdown("### 📥 Downloads")
        download_cols = st.columns(3)
        
        with download_cols[0]:
            if result.get("word_path") and os.path.exists(result["word_path"]):
                with open(result["word_path"], "rb") as f:
                    st.download_button(
                        "📄 CV",
                        f,
                        file_name=os.path.basename(result["word_path"]),
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"cv_download_{candidate_name}"
                    )
        
        with download_cols[1]:
            if result.get("cv_json") and os.path.exists(result["cv_json"]):
                with open(result["cv_json"], "rb") as f:
                    st.download_button(
                        "📋 JSON",
                        f,
                        file_name=os.path.basename(result["cv_json"]),
                        mime="application/json",
                        key=f"json_download_{candidate_name}"
                    )
        
        with download_cols[2]:
            if result.get("offer_word_path") and os.path.exists(result.get("offer_word_path", "")):
                with open(result["offer_word_path"], "rb") as f:
                    st.download_button(
                        "💼 Offer",
                        f,
                        file_name=os.path.basename(result["offer_word_path"]),
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary",
                        key=f"offer_download_{candidate_name}"
                    )
        
        st.divider()
        
        # Offer creation button (if not already created)
        col_offer, col_reprocess = st.columns(2)
        
        with col_offer:
            if not (result.get("offer_word_path") and os.path.exists(result.get("offer_word_path", ""))):
                if st.button(f"✨ Create Offer", key=f"offer_{candidate_name}", width='stretch'):
                    st.info("📌 Offer generation would be integrated here with generate_angebot_word module")
            else:
                st.success("✅ Offer created")
        
        with col_reprocess:
            if st.button("🔄 Re-process", key=f"reprocess_{candidate_name}", width='stretch'):
                st.info("📌 Re-processing would be integrated with batch runner")


def display_batch_results(batch_results: List[Dict[str, Any]], job_profile_json: Optional[str], language: str = "de"):
    """
    Main function to display all batch comparison results.
    """
    st.subheader("🎉 Batch Comparison Results" if language == "en" else "🎉 Batch-Vergleich Ergebnisse")
    
    # Count successes
    successful = [r for r in batch_results if r.get("success")]
    failed = [r for r in batch_results if not r.get("success")]
    
    st.metric("Processed", f"{len(successful)}/{len(batch_results)}")
    
    if failed:
        with st.expander(f"❌ Failed ({len(failed)})", expanded=False):
            for result in failed:
                st.error(f"**{result.get('cv_file', 'Unknown')}**: {result.get('error', 'Unknown error')}")
    
    st.divider()
    
    # Display comparison dashboard
    if successful:
        display_batch_comparison_dashboard(successful, job_profile_json, language)
        
        st.divider()
        
        # Display per-candidate results
        st.subheader("👥 Kandidaten" if language == "de" else "👥 Candidates")
        
        for result in successful:
            display_candidate_expander(result, "", language)
