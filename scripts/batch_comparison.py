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
from scripts.naming_conventions import extract_job_profile_name, get_output_folder_path


def run_batch_comparison(
    cv_files: List[Any],
    job_file: Any,
    api_key: str,
    custom_styles: Optional[Dict] = None,
    custom_logo_path: Optional[str] = None,
    pipeline_mode: str = "Batch Comparison",
    language: str = "de",
    progress_callback: Optional[callable] = None
) -> List[Dict[str, Any]]:
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
        List of result dicts, each containing:
        {
            "success": bool,
            "candidate_name": str,
            "cv_file": UploadedFile,
            "job_profile": dict (stellenprofil_json),
            "cv_json": dict,
            "word_file": str (path),
            "json_file": str (path),
            "match_result": dict,
            "feedback_result": dict,
            "dashboard_html": str (path),
            "error": str (if failed)
        }
    """
    
    batch_results = []
    base_dir = os.getcwd()
    
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
        print(f"\n📋 Processing Stellenprofil PDF...", file=sys.stderr)
        
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
            return [{
                "success": False,
                "error": "Failed to extract Stellenprofil from PDF. Check file format and content."
            }]
        
        print(f"✅ Stellenprofil extracted successfully", file=sys.stderr)
    
    except Exception as e:
        error_details = f"{str(e)}"
        tb_str = traceback.format_exc()
        print(f"❌ Failed to extract Stellenprofil:\n{tb_str}", file=sys.stderr)
        return [{
            "success": False,
            "error": f"Stellenprofil extraction failed: {error_details}"
        }]
    
    # Create batch output folder with unified naming convention
    # Format: jobprofileName_batch-comparison_timestamp
    job_profile_name = extract_job_profile_name(stellenprofil_data)
    batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_output = os.path.join(base_dir, "output")
    batch_output_dir = get_output_folder_path(base_output, job_profile_name, "batch-comparison", batch_timestamp)
    
    print(f"📂 Batch folder created: {batch_output_dir}", file=sys.stderr)
    
    if progress_callback:
        progress_callback(10, "Stellenprofil verarbeitet, beginne mit CVs...", "running")
    
    # PHASE 2: Process each CV with Stellenprofil context
    for idx, cv_file in enumerate(cv_files):
        result = {
            "success": False,
            "candidate_name": cv_file.name.replace(".pdf", ""),
            "cv_file": cv_file,
            "job_profile": stellenprofil_data,
            "error": None
        }
        
        progress_pct = int(10 + (idx / len(cv_files)) * 80)
        if progress_callback:
            progress_callback(progress_pct, f"Verarbeite {cv_file.name}...", "running")
        
        try:
            print(f"\n📄 Processing CV {idx+1}/{len(cv_files)}: {cv_file.name}", file=sys.stderr)
            
            # Initialize the generator for this CV
            generator = StreamlitCVGenerator(base_dir)
            
            # Run the standard pipeline with Stellenprofil context
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
                job_profile_context=stellenprofil_data  # Pass extracted Stellenprofil as context
            )
            
            print(f"Generator result: success={cv_result.get('success')}, error={cv_result.get('error')}", file=sys.stderr)
            
            # Extract relevant data from cv_result
            if cv_result.get("success"):
                result["success"] = True
                result["cv_json_path"] = cv_result.get("cv_json")  # JSON file path
                result["word_file"] = cv_result.get("word_path")   # Word doc path
                result["match_result"] = cv_result.get("match_json")  # Match JSON path
                result["dashboard_html"] = cv_result.get("dashboard_path")  # Dashboard HTML path
                result["stellenprofil_json"] = cv_result.get("stellenprofil_json")  # Job profile JSON path
                result["vorname"] = cv_result.get("vorname")
                result["nachname"] = cv_result.get("nachname")
                result["match_score"] = cv_result.get("match_score")
                print(f"✅ Successfully processed: {cv_file.name}", file=sys.stderr)
            else:
                result["success"] = False
                error_msg = cv_result.get("error", "Unknown error during processing")
                result["error"] = f"Pipeline error: {error_msg}"
                print(f"❌ Processing failed: {cv_file.name} - {error_msg}", file=sys.stderr)
        
        except Exception as e:
            error_details = f"{str(e)}"
            tb_str = traceback.format_exc()
            result["success"] = False
            result["error"] = error_details
            print(f"❌ Exception processing {cv_file.name}:\n{tb_str}", file=sys.stderr)
        
        batch_results.append(result)
    
    if progress_callback:
        progress_callback(100, "Batch verarbeitet", "complete")
    
    return batch_results
