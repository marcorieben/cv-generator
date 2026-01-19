"""
Batch Comparison Mode - Orchestrates multi-CV processing and batch analysis.

This module handles:
1. Processing multiple CVs against a single job profile
2. Running each CV through the standard pipeline (PDF extraction, analysis, Word generation)
3. Collecting results for comparison dashboard
4. Managing file persistence for batch and per-candidate outputs
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import traceback
import sys

from scripts.streamlit_pipeline import StreamlitCVGenerator
from scripts.pdf_to_json import pdf_to_json
from scripts.naming_conventions import (
    extract_job_profile_name_from_file,
    extract_job_profile_name,
    extract_candidate_name,
    get_output_folder_path,
    get_candidate_subfolder_path,
    get_stellenprofil_json_filename
)


def run_batch_comparison(
    cv_files: List[Any],
    job_file: Any,
    api_key: str,
    custom_styles: Optional[Dict] = None,
    custom_logo_path: Optional[str] = None,
    pipeline_mode: str = "Batch Comparison",
    language: str = "de",
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Process multiple CVs against a single job profile for batch comparison.
    
    Args:
        cv_files: List of uploaded CV files (UploadedFile objects)
        job_file: Single uploaded job profile file (UploadedFile object)
        api_key: OpenAI API key for PDF extraction and analysis
        custom_styles: Optional custom styling dict
        custom_logo_path: Optional path to custom logo
        pipeline_mode: Pipeline mode identifier
        language: UI language (de, en, fr)
        progress_callback: Optional callback function(progress, status, state) for UI updates
    
    Returns:
        Dict containing:
        {
            "results": List of result dicts for each CV processed,
            "batch_folder": str (path to batch output folder),
            "job_profile_name": str (extracted job profile name),
            "timestamp": str (batch timestamp YYYYMMDD_HHMMSS)
        }
        
        Each result dict contains:
        {
            "success": bool,
            "candidate_name": str,
            "cv_filename": str (uploaded filename),
            "job_profile": dict (stellenprofil_json),
            "cv_json": dict,
            "word_path": str (path),
            "cv_json_path": str (path),
            "match_json": str (path),
            "feedback_result": dict,
            "dashboard_path": str (path),
            "stellenprofil_json": str (path),
            "vorname": str,
            "nachname": str,
            "match_score": int,
            "error": str (if failed)
        }
"""
    
    batch_results = []
    base_dir = os.getcwd()
    print(f"[START] Starting batch_comparison with base_dir: {base_dir}", file=sys.stderr)
    print(f"   Number of CVs to process: {len(cv_files)}", file=sys.stderr)
    
    # Ensure job file pointer is at start
    if hasattr(job_file, 'seek'):
        try:
            job_file.seek(0)
        except Exception as e:
            print(f"Warning: Could not seek job_file: {str(e)}", file=sys.stderr)
    
    # PHASE 1: Process Stellenprofil PDF first
    # This is the semantic driver for all CV extractions
    stellenprofil_data = None
    try:
        print(f"\n[PROFILE] Processing Stellenprofil PDF...", file=sys.stderr)
        
        # Use the same Stellenprofil schema as Mode 2/3
        job_schema_path = os.path.join(base_dir, "scripts", "pdf_to_json_struktur_stellenprofil.json")
        
        # Extract Stellenprofil from PDF using LLM
        stellenprofil_data = pdf_to_json(
            job_file, 
            output_path=None, 
            schema_path=job_schema_path,
            target_language=language
        )
        
        if not stellenprofil_data:
            return {
                "results": [{
                    "success": False,
                    "error": "Failed to extract Stellenprofil from PDF. Check file format and content."
                }],
                "batch_folder": "",
                "job_profile_name": "jobprofile",
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
            }
        
        print(f"[OK] Stellenprofil extracted successfully", file=sys.stderr)
    
    except Exception as e:
        error_details = f"{str(e)}"
        tb_str = traceback.format_exc()
        print(f"[ERROR] Failed to extract Stellenprofil:\n{tb_str}", file=sys.stderr)
        return {
            "results": [{
                "success": False,
                "error": f"Stellenprofil extraction failed: {error_details}"
            }],
            "batch_folder": "",
            "job_profile_name": "jobprofile",
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
        }
    
    # Create batch output folder with unified naming convention
    # Format: jobprofileName_batch-comparison_timestamp
    # Try to extract job profile name from uploaded filename first
    job_profile_name_from_file = extract_job_profile_name_from_file(job_file.name if hasattr(job_file, 'name') else "")
    # Then verify/enrich with extracted data
    job_profile_name = extract_job_profile_name(stellenprofil_data)
    if job_profile_name == "jobprofile" and job_profile_name_from_file != "jobprofile":
        job_profile_name = job_profile_name_from_file
    
    batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_output = os.path.join(base_dir, "output")
    batch_output_dir = get_output_folder_path(base_output, job_profile_name, "batch-comparison", batch_timestamp)
    
    print(f"[FOLDER] Batch folder created: {batch_output_dir}", file=sys.stderr)
    
    # Save Stellenprofil JSON at batch folder root
    try:
        stellenprofil_filename = get_stellenprofil_json_filename(job_profile_name, batch_timestamp)
        stellenprofil_path = os.path.join(batch_output_dir, stellenprofil_filename)
        with open(stellenprofil_path, 'w', encoding='utf-8') as f:
            json.dump(stellenprofil_data, f, ensure_ascii=False, indent=2)
        print(f"[SAVE] Saved Stellenprofil: {stellenprofil_path}", file=sys.stderr)
    except Exception as e:
        print(f"[WARN] Warning: Could not save Stellenprofil JSON: {str(e)}", file=sys.stderr)
    
    if progress_callback:
        progress_callback(10, "Stellenprofil verarbeitet, beginne mit CVs...", "running")
    
    # PHASE 2: Process each CV with Stellenprofil context
    for idx, cv_file in enumerate(cv_files):
        # Extract candidate name from CV file
        candidate_name = extract_candidate_name(None)  # Will be updated after CV extraction
        candidate_name_fallback = cv_file.name.replace(".pdf", "").replace(".PDF", "")
        
        result = {
            "success": False,
            "candidate_name": candidate_name_fallback,
            "cv_filename": cv_file.name,  # Store only the filename, not the UploadedFile object
            "error": None
        }
        
        progress_pct = int(10 + (idx / len(cv_files)) * 80)
        if progress_callback:
            progress_callback(progress_pct, f"Verarbeite {cv_file.name}...", "running")
        
        try:
            print(f"\n[FILE] Processing CV {idx+1}/{len(cv_files)}: {cv_file.name}", file=sys.stderr)
            
            # Create candidate subfolder within batch folder
            candidate_subfolder = get_candidate_subfolder_path(
                batch_output_dir,
                candidate_name_fallback,
                batch_timestamp
            )
            print(f"[FOLDER] Candidate folder: {candidate_subfolder}", file=sys.stderr)
            print(f"   Folder exists: {os.path.exists(candidate_subfolder)}", file=sys.stderr)
            print(f"   Batch output dir: {batch_output_dir}", file=sys.stderr)
            
            # Initialize the generator for this CV
            generator = StreamlitCVGenerator(base_dir)
            
            # Run the standard pipeline with Stellenprofil context and custom output directory
            # The CV extraction will be job-profile-aware
            # Note: We don't pass job_file here - Stellenprofil is already extracted
            cv_result = generator.run(
                cv_file=cv_file,
                job_file=None,  # Don't re-extract job profile for each CV
                api_key=api_key,
                custom_styles=custom_styles,
                custom_logo_path=custom_logo_path,
                pipeline_mode=pipeline_mode,
                language=language,
                job_profile_context=stellenprofil_data,  # Pass extracted Stellenprofil as context
                output_dir=candidate_subfolder,  # Override output directory for batch mode
                job_profile_name=job_profile_name  # Pass the consistent job profile name for file naming
            )
            
            print(f"Generator result: success={cv_result.get('success')}, error={cv_result.get('error')}", file=sys.stderr)
            
            # Extract relevant data from cv_result
            if cv_result.get("success"):
                result["success"] = True
                result["cv_json_path"] = cv_result.get("cv_json")  # JSON file path
                result["word_file"] = cv_result.get("word_path")   # Word doc path
                result["match_result"] = cv_result.get("match_json")  # Match JSON path
                result["dashboard_path"] = cv_result.get("dashboard_path")  # Dashboard HTML path
                result["stellenprofil_json"] = cv_result.get("stellenprofil_json")  # Job profile JSON path
                result["vorname"] = cv_result.get("vorname")
                result["nachname"] = cv_result.get("nachname")
                result["match_score"] = cv_result.get("match_score")
                
                # Update candidate name with actual extracted values
                if cv_result.get("vorname") and cv_result.get("nachname"):
                    candidate_name = extract_candidate_name({
                        "Vorname": cv_result.get("vorname"),
                        "Nachname": cv_result.get("nachname")
                    })
                    result["candidate_name"] = candidate_name
                
                print(f"[OK] Successfully processed: {cv_file.name}", file=sys.stderr)
            else:
                result["success"] = False
                error_msg = cv_result.get("error", "Unknown error during processing")
                result["error"] = f"Pipeline error: {error_msg}"
                print(f"[ERROR] Processing failed: {cv_file.name} - {error_msg}", file=sys.stderr)
        
        except Exception as e:
            error_details = f"{str(e)}"
            tb_str = traceback.format_exc()
            result["success"] = False
            result["error"] = error_details
            print(f"[ERROR] Exception processing {cv_file.name}: {error_details}", file=sys.stderr)
            print(f"Full traceback:\n{tb_str}", file=sys.stderr)
        
        batch_results.append(result)
    
    if progress_callback:
        progress_callback(100, "Batch verarbeitet", "complete")
    
    return {
        "results": batch_results,
        "batch_folder": batch_output_dir,
        "job_profile_name": job_profile_name,
        "timestamp": batch_timestamp
    }
