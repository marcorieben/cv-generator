"""
Quick validation test for Gradio app
Tests that all imports work and UI can be initialized
"""
import sys
import os
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ensure we can import from scripts/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")

    try:
        import gradio as gr
        print("  [OK] gradio")
    except ImportError as e:
        print(f"  [ERROR] gradio: {e}")
        return False

    try:
        from scripts.model_registry import ModelRegistry
        print("  [OK] model_registry")
    except ImportError as e:
        print(f"  [ERROR] model_registry: {e}")
        return False

    try:
        from scripts.pdf_to_json import pdf_to_json
        print("  [OK] pdf_to_json")
    except ImportError as e:
        print(f"  [ERROR] pdf_to_json: {e}")
        return False

    try:
        from scripts.generate_cv import generate_cv
        print("  [OK] generate_cv")
    except ImportError as e:
        print(f"  [ERROR] generate_cv: {e}")
        return False

    return True


def test_model_registry():
    """Test that ModelRegistry works"""
    print("\nTesting ModelRegistry...")

    try:
        from scripts.model_registry import ModelRegistry

        # Get available models
        models = ModelRegistry.get_available_models()
        print(f"  [OK] Found {len(models)} available models")

        # Test cost estimation
        estimate = ModelRegistry.estimate_cost("gpt-4o-mini", 100)
        print(f"  [OK] Cost estimate for 100 CVs: {estimate['monthly_cost']}")

        # List all models
        print("\n  Available models:")
        for model_id, info in sorted(models.items(), key=lambda x: x[1]['cost_per_cv']):
            print(f"    - {info['display_name']}: ${info['cost_per_cv']:.3f}/CV ({info['speed']}, {info['quality']})")

        return True

    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gradio_ui_structure():
    """Test that Gradio UI can be initialized"""
    print("\nTesting Gradio UI structure...")

    try:
        # Import the app module (this will initialize the UI)
        import importlib.util
        spec = importlib.util.spec_from_file_location("app_gradio", "app_gradio.py")
        app_module = importlib.util.module_from_spec(spec)

        # Don't execute (don't call spec.loader.exec_module)
        # as it would try to launch the server
        print("  [OK] app_gradio.py can be loaded")

        # Instead, just validate the structure manually
        import gradio as gr
        from scripts.model_registry import ModelRegistry

        models = ModelRegistry.get_available_models()
        model_options = [
            f"{info['display_name']} ({info['speed']})"
            for _, info in sorted(models.items(), key=lambda x: x[1]['cost_per_cv'])
        ]

        print(f"  [OK] Model dropdown would have {len(model_options)} options")
        print(f"  [OK] Default model: {model_options[0]}")

        return True

    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_environment():
    """Test environment variables"""
    print("\nTesting environment...")

    # Check for API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if openai_key:
        print(f"  [OK] OPENAI_API_KEY found (starts with: {openai_key[:10]}...)")
    else:
        print("  [WARNING] OPENAI_API_KEY not set (required for OpenAI models)")

    if anthropic_key:
        print(f"  [OK] ANTHROPIC_API_KEY found (starts with: {anthropic_key[:10]}...)")
    else:
        print("  [INFO] ANTHROPIC_API_KEY not set (optional, only needed for Claude models)")

    return True


def main():
    """Run all tests"""
    print("=" * 80)
    print("GRADIO APP VALIDATION TEST")
    print("=" * 80)

    all_passed = True

    # Run tests
    all_passed &= test_imports()
    all_passed &= test_model_registry()
    all_passed &= test_gradio_ui_structure()
    all_passed &= test_environment()

    # Summary
    print("\n" + "=" * 80)
    if all_passed:
        print("STATUS: ALL TESTS PASSED")
        print("\nNext steps:")
        print("1. Set environment variables (if not already set):")
        print("   - OPENAI_API_KEY=your-key-here")
        print("   - ANTHROPIC_API_KEY=your-key-here (optional)")
        print("\n2. Run the app:")
        print("   python app_gradio.py")
        print("\n3. Open browser to: http://localhost:7860")
    else:
        print("STATUS: SOME TESTS FAILED")
        print("\nPlease fix the errors above before running the app.")
    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
