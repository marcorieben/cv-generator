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
    """Test batch processing with real PDF files from input folder"""
    print("\n" + "="*60)
    print("🧪 Testing Batch Processing with Real Files")
    print("="*60)
    
    # Check for available PDFs
    cv_folder = os.path.join(os.getcwd(), "input", "cv")
    job_folder = os.path.join(os.getcwd(), "input", "stellenprofil")
    
    print(f"\n📁 Looking for files...")
    print(f"   CV folder: {cv_folder}")
    print(f"   Job folder: {job_folder}")
    
    # Get available files
    cv_files = [f for f in os.listdir(cv_folder) if f.lower().endswith(".pdf")] if os.path.exists(cv_folder) else []
    job_files = [f for f in os.listdir(job_folder) if f.lower().endswith(".pdf")] if os.path.exists(job_folder) else []
    
    print(f"\n📄 Available files:")
    print(f"   CVs: {len(cv_files)} found")
    for f in cv_files[:3]:
        print(f"      - {f}")
    print(f"   Job Profiles: {len(job_files)} found")
    for f in job_files[:3]:
        print(f"      - {f}")
    
    if not cv_files or not job_files:
        print("\n⚠️  No PDF files found. Need at least 1 CV and 1 job profile.")
        return None
    
    # Create file objects from real files
    print(f"\n📄 Opening files...")
    
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
    
    cv_file_objs = []
    for cv_name in cv_files[:2]:  # Test with first 2 CVs
        cv_path = os.path.join(cv_folder, cv_name)
        cv_file_objs.append(FileObj(cv_path))
        print(f"   - {cv_name}")
    
    job_file_obj = FileObj(os.path.join(job_folder, job_files[0]))
    print(f"   - {job_files[0]}")
    
    # Run batch comparison
    print(f"\n🚀 Running batch_comparison()...")
    from batch_comparison import run_batch_comparison
    
    try:
        result = run_batch_comparison(
            cv_files=cv_file_objs,
            job_file=job_file_obj,
            api_key=os.environ.get("OPENAI_API_KEY", "test-key"),
            pipeline_mode="Advanced (Full Matching)",
            language="de"
        )
        
        print("\n✅ Batch processing completed!")
        print(f"\nResult structure:")
        print(f"  - success: {result.get('success')}")
        print(f"  - batch_folder: {result.get('batch_folder')}")
        print(f"  - job_profile_name: {result.get('job_profile_name')}")
        print(f"  - timestamp: {result.get('timestamp')}")
        
        if "results" in result:
            print(f"\n📊 Results for {len(result['results'])} CVs:")
            for idx, res in enumerate(result['results']):
                status = "✅" if res.get('success') else "❌"
                print(f"\n  {status} CV {idx+1}: {res.get('candidate_name')}")
                if res.get('success'):
                    print(f"     - CV JSON: {res.get('cv_json_path')}")
                    print(f"     - Word: {res.get('word_file')}")
                else:
                    print(f"     - Error: {res.get('error')}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Exception during batch processing:")
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
        print(f"\n📁 Output folder structure:")
        for root, dirs, files in os.walk(output_path):
            level = root.replace(output_path, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files[:5]:  # Limit to first 5 files
                print(f'{subindent}{file}')
            if len(files) > 5:
                print(f'{subindent}... and {len(files) - 5} more files')
    
    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)
