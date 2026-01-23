"""
Command-line interface for the cleanup system.

Usage:
    python scripts/cleanup/cleanup.py              # Analyze mode (safe, no changes)
    python scripts/cleanup/cleanup.py apply        # Apply mode (may delete files)
    python scripts/cleanup/cleanup.py --help       # Show help
    
Or as Python module:
    python -m scripts.cleanup.cleanup
"""

import sys
from pathlib import Path


def main():
    """Main entry point."""
    mode = "analyze"  # Default
    
    # Parse arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["apply", "delete"]:
            mode = "apply"
        elif arg in ["--help", "-h"]:
            print(__doc__)
            return 0
        elif arg in ["analyze", "check"]:
            mode = "analyze"
        else:
            print(f"Unknown argument: {arg}")
            print("Valid arguments: analyze, apply, --help")
            return 1
    
    # Import after checking help (faster startup)
    from scripts.cleanup import run_cleanup
    
    print("")
    print("🧹 CV Generator Cleanup System")
    print("")
    
    try:
        report = run_cleanup(mode=mode, verbose=True)
        
        # Show key stats
        summary = report.summary
        if summary["delete_safe"] > 0:
            print(f"💡 {summary['delete_safe']} files are safe to delete")
            if mode == "analyze":
                print("   Run: python scripts/cleanup/cleanup.py apply")
                print("   to actually delete them.")
        
        if summary["review_required"] > 0:
            print(f"⚠️  {summary['review_required']} files need review")
            print("   See cleanup_report.md in the run folder")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
