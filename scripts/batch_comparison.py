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
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import traceback
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

from scripts.streamlit_pipeline import StreamlitCVGenerator
from scripts.pdf_to_json import pdf_to_json
from scripts.naming_conventions import (
    extract_job_profile_name_from_file,
    extract_job_profile_name,
    extract_candidate_name,
    extract_candidate_name_from_file,
    get_output_folder_path,
    get_candidate_subfolder_path,
    get_stellenprofil_json_filename,
    build_output_path
)


def pdf_to_json_with_retry(pdf_file, output_path=None, schema_path=None, target_language="de", max_retries=3):
    """
    PDF to JSON extraction with exponential backoff retry logic.
    
    Handles transient API failures (timeouts, rate limits) with automatic retries.
    Each retry waits: 2s, 4s, 8s (exponential backoff).
    
    Args:
        pdf_file: File object to extract
        output_path: Optional output path for JSON
        schema_path: Schema file path
        target_language: Target language (de, en, fr)
        max_retries: Number of retry attempts (default 3)
        
    Returns:
        Dict with extracted data or raises exception if all retries fail
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            print(f"[RETRY] Extraction attempt {attempt + 1}/{max_retries}", file=sys.stderr)
            result = pdf_to_json(
                pdf_file, 
                output_path=output_path,
                schema_path=schema_path,
                target_language=target_language
            )
            if result:
                print(f"[OK] Extraction succeeded on attempt {attempt + 1}", file=sys.stderr)
                return result
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 2s, 4s, 8s
                print(f"[WARN] Extraction failed (attempt {attempt + 1}): {str(e)}", file=sys.stderr)
                print(f"[RETRY] Waiting {wait_time}s before retry...", file=sys.stderr)
                time.sleep(wait_time)
            else:
                print(f"[ERROR] All {max_retries} extraction attempts failed", file=sys.stderr)
    
    # All retries exhausted
    raise last_error if last_error else Exception("PDF extraction failed after all retries")


def _process_single_cv(
    cv_file,
    idx: int,
    total_cvs: int,
    base_dir: str,
    base_output: str,
    batch_timestamp: str,
    batch_output_dir: str,
    stellenprofil_data: Dict,
    job_profile_name: str,
    api_key: str,
    custom_styles: Optional[Dict],
    custom_logo_path: Optional[str],
    pipeline_mode: str,
    language: str
) -> Tuple[int, Dict[str, Any]]:
    """
    Process a single CV in the batch.
    
    This function is designed to run in parallel via ThreadPoolExecutor.
    Returns: (index, result_dict) for ordered result collection
    
    Args:
        cv_file: CV File object to process
        idx: Index of this CV in the batch (0-based)
        total_cvs: Total number of CVs in batch (for progress indication)
        base_dir: Base directory of the project
        base_output: Base output directory path
        batch_timestamp: Timestamp of the batch (YYYYMMDD_HHMMSS)
        batch_output_dir: Path to the batch output folder
        stellenprofil_data: Pre-extracted Stellenprofil data
        job_profile_name: Normalized job profile name
        api_key: OpenAI API key
        custom_styles: Custom styling dict
        custom_logo_path: Custom logo path
        pipeline_mode: Pipeline mode identifier
        language: Language code (de, en, fr)
        
    Returns:
        Tuple[index, result_dict] where result_dict contains success/error info
    """
    candidate_name = extract_candidate_name(None)
    candidate_name_fallback = cv_file.name.replace(".pdf", "").replace(".PDF", "")
    
    result = {
        "success": False,
        "candidate_name": candidate_name_fallback,
        "cv_filename": cv_file.name,
        "error": None
    }
    
    try:
        print(f"\n[PARALLEL] Processing CV {idx+1}/{total_cvs}: {cv_file.name}", file=sys.stderr)
        
        # Create candidate subfolder
        candidate_name_normalized = extract_candidate_name_from_file(cv_file.name)
        
        candidate_naming = build_output_path(
            mode='professional_analysis',
            candidate_name=candidate_name_normalized,
            job_profile_name=job_profile_name,
            artifact_type='cv',
            is_batch=True,
            timestamp=batch_timestamp,
            base_output_dir=base_output
        )
        
        candidate_subfolder = candidate_naming['candidate_subfolder_path']
        os.makedirs(candidate_subfolder, exist_ok=True)
        
        print(f"[FOLDER] CV {idx+1} folder: {candidate_subfolder}", file=sys.stderr)
        
        # Initialize generator and run pipeline
        generator = StreamlitCVGenerator(base_dir)
        
        cv_result = generator.run(
            cv_file=cv_file,
            job_file=None,
            api_key=api_key,
            custom_styles=custom_styles,
            custom_logo_path=custom_logo_path,
            pipeline_mode=pipeline_mode,
            language=language,
            job_profile_context=stellenprofil_data,
            output_dir=candidate_subfolder,
            job_profile_name=job_profile_name
        )
        
        print(f"[PARALLEL] CV {idx+1} result: success={cv_result.get('success')}", file=sys.stderr)
        
        # Extract data from result
        if cv_result.get("success"):
            result["success"] = True
            result["cv_json_path"] = cv_result.get("cv_json")
            result["word_file"] = cv_result.get("word_path")
            result["match_result"] = cv_result.get("match_json")
            result["dashboard_path"] = cv_result.get("dashboard_path")
            result["stellenprofil_json"] = cv_result.get("stellenprofil_json")
            result["vorname"] = cv_result.get("vorname")
            result["nachname"] = cv_result.get("nachname")
            result["match_score"] = cv_result.get("match_score")
            
            # Update candidate name with actual data
            if cv_result.get("vorname") and cv_result.get("nachname"):
                candidate_name = extract_candidate_name({
                    "Vorname": cv_result.get("vorname"),
                    "Nachname": cv_result.get("nachname")
                })
                result["candidate_name"] = candidate_name
            
            print(f"[OK] CV {idx+1} succeeded: {cv_file.name}", file=sys.stderr)
        else:
            result["success"] = False
            error_msg = cv_result.get("error", "Unknown error during processing")
            result["error"] = f"Pipeline error: {error_msg}"
            print(f"[ERROR] CV {idx+1} failed: {cv_file.name} - {error_msg}", file=sys.stderr)
    
    except Exception as e:
        error_details = f"{str(e)}"
        tb_str = traceback.format_exc()
        result["success"] = False
        result["error"] = error_details
        print(f"[ERROR] CV {idx+1} exception: {cv_file.name}: {error_details}", file=sys.stderr)
        print(f"Full traceback:\n{tb_str}", file=sys.stderr)
    
    return (idx, result)


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
    script_dir = os.path.dirname(os.path.abspath(__file__))  # /path/to/scripts/
    base_dir = os.path.dirname(script_dir)  # /path/to/cv_generator/ (parent of scripts)
    print(f"[START] Starting batch_comparison with base_dir: {base_dir}", file=sys.stderr)
    print(f"   Script dir: {script_dir}", file=sys.stderr)
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
        
        # Extract Stellenprofil from PDF using LLM with retry logic
        stellenprofil_data = pdf_to_json_with_retry(
            job_file, 
            output_path=None, 
            schema_path=job_schema_path,
            target_language=language,
            max_retries=3
        )
        
        if not stellenprofil_data:
            return {
                "batch_results": [{
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
            "batch_results": [{
                "success": False,
                "error": f"Stellenprofil extraction failed: {error_details}"
            }],
            "batch_folder": "",
            "job_profile_name": "jobprofile",
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
        }
    
    # Create batch output folder with unified naming convention
    # Use build_output_path with is_batch=True
    job_profile_name_from_file = extract_job_profile_name_from_file(job_file.name if hasattr(job_file, 'name') else "")
    job_profile_name = extract_job_profile_name(stellenprofil_data)
    if job_profile_name == "jobprofile" and job_profile_name_from_file != "jobprofile":
        job_profile_name = job_profile_name_from_file
    
    batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_output = os.path.join(base_dir, "output")
    
    # Generate batch folder structure using new build_output_path
    batch_naming = build_output_path(
        mode='professional_analysis',
        candidate_name='',  # Not used at batch root level
        job_profile_name=job_profile_name,
        artifact_type='batch',
        is_batch=True,
        timestamp=batch_timestamp,
        base_output_dir=base_output
    )
    
    batch_output_dir = batch_naming['batch_folder_path']
    os.makedirs(batch_output_dir, exist_ok=True)
    
    print(f"[FOLDER] Batch folder created: {batch_output_dir}", file=sys.stderr)
    
    # Save Stellenprofil JSON at batch folder root
    try:
        job_profile_filename = batch_naming['job_profile_file_name'] + '.json'
        job_profile_path = os.path.join(batch_output_dir, job_profile_filename)
        with open(job_profile_path, 'w', encoding='utf-8') as f:
            json.dump(stellenprofil_data, f, ensure_ascii=False, indent=2)
        print(f"[SAVE] Saved Job Profile: {job_profile_path}", file=sys.stderr)
    except Exception as e:
        print(f"[WARN] Warning: Could not save Job Profile JSON: {str(e)}", file=sys.stderr)
    
    if progress_callback:
        progress_callback(10, "Stellenprofil verarbeitet, starte parallele CV-Verarbeitung...", "running")
    
    # PHASE 2: Process CVs in parallel with Stellenprofil context
    # Calculate optimal number of workers: CPU count or 4, whichever is smaller (to avoid API rate limits)
    max_workers = min(max(1, multiprocessing.cpu_count() - 1), 4)
    print(f"[PARALLEL] Starting parallel CV processing with {max_workers} workers", file=sys.stderr)
    print(f"[PARALLEL] Total CVs to process: {len(cv_files)}", file=sys.stderr)
    
    # Dictionary to collect results in order
    cv_results_dict: Dict[int, Dict] = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all CV processing tasks
        futures = {}
        for idx, cv_file in enumerate(cv_files):
            future = executor.submit(
                _process_single_cv,
                cv_file=cv_file,
                idx=idx,
                total_cvs=len(cv_files),
                base_dir=base_dir,
                base_output=base_output,
                batch_timestamp=batch_timestamp,
                batch_output_dir=batch_output_dir,
                stellenprofil_data=stellenprofil_data,
                job_profile_name=job_profile_name,
                api_key=api_key,
                custom_styles=custom_styles,
                custom_logo_path=custom_logo_path,
                pipeline_mode=pipeline_mode,
                language=language
            )
            futures[future] = idx
        
        # Collect results as they complete
        completed = 0
        for future in as_completed(futures):
            idx = futures[future]  # Get the original index
            try:
                result_idx, result = future.result()
                cv_results_dict[result_idx] = result
                completed += 1
                progress_pct = int(10 + (completed / len(cv_files)) * 80)
                status_msg = f"CVs verarbeitet: {completed}/{len(cv_files)}"
                if progress_callback:
                    progress_callback(progress_pct, status_msg, "running")
                print(f"[PARALLEL] Completed {completed}/{len(cv_files)} CVs", file=sys.stderr)
            except Exception as e:
                print(f"[ERROR] Task exception for CV {idx}: {str(e)}", file=sys.stderr)
                # Important: Add error result for this index so we don't have missing indices
                cv_results_dict[idx] = {
                    "success": False,
                    "candidate_name": f"CV_{idx}",
                    "cv_filename": cv_files[idx].name if idx < len(cv_files) else "Unknown",
                    "error": f"Task execution failed: {str(e)}"
                }
                completed += 1
                progress_pct = int(10 + (completed / len(cv_files)) * 80)
                if progress_callback:
                    progress_callback(progress_pct, f"Fehler bei CV {idx+1}", "running")
    
    # Rebuild results list in original order - now guaranteed to have all indices
    batch_results = []
    for i in range(len(cv_files)):
        if i in cv_results_dict:
            batch_results.append(cv_results_dict[i])
        else:
            # Fallback (should not happen now, but defensive programming)
            batch_results.append({
                "success": False,
                "candidate_name": f"CV_{i}",
                "cv_filename": cv_files[i].name if i < len(cv_files) else "Unknown",
                "error": "No result received for this CV (possible thread crash)"
            })
    
    print(f"[PARALLEL] All CV processing complete. {len([r for r in batch_results if r.get('success')])} successful, {len([r for r in batch_results if not r.get('success')])} failed", file=sys.stderr)
    
    if progress_callback:
        progress_callback(100, "Batch verarbeitet", "complete")
    
    return {
        "batch_results": batch_results,
        "batch_folder": batch_output_dir,
        "job_profile_name": job_profile_name,
        "timestamp": batch_timestamp
    }
