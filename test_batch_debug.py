#!/usr/bin/env python3
"""
Quick batch processing test with debugging
"""
import os
import sys
from io import BytesIO
from pathlib import Path

# Add scripts to path
sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))

def test_batch_processing():
    """Test batch processing with real PDF files from archive"""
    print("\n" + "="*60)
    print("TEST: Testing Batch Processing")
    print("="*60)
    
    # Check for available PDFs in archive
    cv_archive = os.path.join(os.getcwd(), "input", "cv", "pdf")
    job_archive = os.path.join(os.getcwd(), "input", "stellenprofil", "pdf")
    
    print(f"\nLooking for PDFs...")
    print(f"   CV archive: {cv_archive}")
    print(f"   Job archive: {job_archive}")
    
    # Get available files
    cv_files_list = [f for f in os.listdir(cv_archive) if f.lower().endswith(".pdf")] if os.path.exists(cv_archive) else []
    job_files_list = [f for f in os.listdir(job_archive) if f.lower().endswith(".pdf")] if os.path.exists(job_archive) else []
    
    print(f"\nAvailable PDFs:")
    print(f"   CVs: {len(cv_files_list)} found")
    for f in cv_files_list[:3]:
        print(f"      - {f}")
    print(f"   Job Profiles: {len(job_files_list)} found")
    for f in job_files_list[:3]:
        print(f"      - {f}")
    
    if not cv_files_list:
        print("\nWARNING: No CV PDF files found in input/cv/pdf/")
        # Try to find any PDFs
        for root, dirs, files in os.walk(os.path.join(os.getcwd(), "input", "cv")):
            pdfs = [f for f in files if f.endswith(".pdf")]
            if pdfs:
                print(f"   Found in {root}: {pdfs[:2]}")
                cv_files_list = pdfs[:1]  # Use first one found
                cv_archive = root
                break
    
    if not job_files_list:
        print("\nWARNING: No Job Profile PDF files found in input/stellenprofil/pdf/")
        # Create a dummy or skip
        return None
    
    # Create file objects from real files
    print(f"\nOpening PDFs...")
    
    class FileObj:
        def __init__(self, path):
            self.path = path
            self.name = os.path.basename(path)
            with open(path, 'rb') as f:
                self.data = f.read()
            self.position = 0
        
        def read(self, size=-1):
            if size == -1:
                result = self.data[self.position:]
                self.position = len(self.data)
            else:
                result = self.data[self.position:self.position + size]
                self.position += size
            return result
        
        def seek(self, pos):
            self.position = pos
        
        def tell(self):
            return self.position
    
    # Use first 2 CVs available
    cv_file_objs = []
    for cv_name in cv_files_list[:2]:
        cv_path = os.path.join(cv_archive, cv_name)
        if os.path.exists(cv_path):
            cv_file_objs.append(FileObj(cv_path))
            print(f"   - {cv_name[:50]}")
    
    # Use first job profile
    job_file_obj = FileObj(os.path.join(job_archive, job_files_list[0]))
    print(f"   - {job_files_list[0][:50]}")
    
    if not cv_file_objs:
        print("\nNo CVs could be opened!")
        return None
    
    # Run batch comparison
    print(f"\nStarting batch_comparison()...")
    from batch_comparison import run_batch_comparison
    
    try:
        result = run_batch_comparison(
            cv_files=cv_file_objs,
            job_file=job_file_obj,
            api_key=os.environ.get("OPENAI_API_KEY", "test-key"),
            pipeline_mode="Advanced (Full Matching)",
            language="de"
        )
        
        print("\nBatch processing completed!")
        print(f"\nResult structure:")
        print(f"  - success: {result.get('success')}")
        print(f"  - batch_folder: {result.get('batch_folder')}")
        print(f"  - job_profile_name: {result.get('job_profile_name')}")
        print(f"  - timestamp: {result.get('timestamp')}")
        
        if "results" in result:
            success_count = sum(1 for r in result['results'] if r.get('success'))
            fail_count = len(result['results']) - success_count
            print(f"\nResults: {success_count} successful, {fail_count} failed")
            
            for idx, res in enumerate(result['results']):
                status = "OK" if res.get('success') else "FAIL"
                print(f"\n  [{status}] CV {idx+1}: {res.get('candidate_name')}")
                if res.get('success'):
                    print(f"     - CV JSON: {res.get('cv_json_path')}")
                    print(f"     - Word: {res.get('word_file')}")
                else:
                    print(f"     - Error: {res.get('error')}")
        
        return result
        
    except Exception as e:
        print(f"\nException during batch processing:")
        print(f"   {str(e)}")
        import traceback
        print(f"\nFull traceback:")
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    result = test_batch_processing()
    
    # Check output folder
    output_path = os.path.join(os.getcwd(), "output")
    if os.path.exists(output_path):
        print(f"\nOutput folder structure (latest batch):")
        # Get most recent batch folder
        batch_folders = [d for d in os.listdir(output_path) if "batch-comparison" in d]
        if batch_folders:
            latest_batch = sorted(batch_folders)[-1]
            batch_path = os.path.join(output_path, latest_batch)
            print(f"Batch: {latest_batch}")
            
            for item in os.listdir(batch_path):
                item_path = os.path.join(batch_path, item)
                if os.path.isdir(item_path):
                    files = os.listdir(item_path)
                    print(f"  {item}/")
                    for f in files[:5]:
                        print(f"    - {f}")
                    if len(files) > 5:
                        print(f"    ... and {len(files) - 5} more")
    
    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)
