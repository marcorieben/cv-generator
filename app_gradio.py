"""
CV Generator - Gradio UI
Better UX than Streamlit: Real-time progress, multi-user queuing, modern design
"""
import gradio as gr
import os
import tempfile
import json
from datetime import datetime
from pathlib import Path

# Import existing pipeline logic
from scripts.model_registry import ModelRegistry
from scripts.pdf_to_json import pdf_to_json
from scripts.generate_cv import generate_cv
from scripts.generate_matchmaking import generate_matchmaking_json
from scripts.generate_cv_feedback import generate_cv_feedback_json
from scripts.generate_angebot import generate_angebot_json
from scripts.visualize_results import generate_dashboard

# Load translations
def load_translations():
    with open("scripts/translations.json", "r", encoding="utf-8") as f:
        return json.load(f)

translations = load_translations()

def get_text(section, key, lang="de"):
    try:
        return translations.get(section, {}).get(key, {}).get(lang, key)
    except:
        return key

# ============================================================================
# MAIN PROCESSING FUNCTION
# ============================================================================

def process_cv_pipeline(
    cv_pdf,
    job_pdf,
    selected_model,
    language,
    mode,
    progress=gr.Progress()
):
    """
    Main CV processing pipeline with real-time progress updates

    Returns: (word_file, dashboard_html, summary_text)
    """

    if not cv_pdf:
        return None, None, "❌ Please upload a CV PDF first!"

    try:
        progress(0, desc="🚀 Starting pipeline...")

        # Get model ID from display name
        models = ModelRegistry.get_available_models()
        model_id = None
        for mid, info in models.items():
            if info['display_name'] in selected_model:
                model_id = mid
                break

        if not model_id:
            model_id = "gpt-4o-mini"  # Fallback

        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("output") / f"gradio_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        # ====================================================================
        # STEP 1: Extract CV from PDF
        # ====================================================================
        progress(0.1, desc="📄 Extracting CV data with AI...")

        job_profile_context = None
        if job_pdf and mode == "full":
            # Extract job profile first for context
            schema_path = "scripts/pdf_to_json_struktur_stellenprofil.json"
            job_profile_context = pdf_to_json(
                job_pdf.name,
                output_path=None,
                schema_path=schema_path,
                target_language=language
            )

        # Extract CV
        provider = ModelRegistry.get_provider(model_id)

        # Read PDF text
        from pypdf import PdfReader
        reader = PdfReader(cv_pdf.name)
        cv_text = ""
        for page in reader.pages:
            cv_text += page.extract_text()

        # Load CV schema
        with open("scripts/pdf_to_json_struktur.json", "r", encoding="utf-8") as f:
            cv_schema = json.load(f)

        cv_data = provider.extract_cv(cv_text, cv_schema, language)

        # Save CV JSON
        cv_json_path = output_dir / f"cv_{timestamp}.json"
        with open(cv_json_path, "w", encoding="utf-8") as f:
            json.dump(cv_data, f, ensure_ascii=False, indent=2)

        vorname = cv_data.get("Vorname", "Unknown")
        nachname = cv_data.get("Nachname", "User")

        progress(0.3, desc=f"✅ CV extracted: {vorname} {nachname}")

        # ====================================================================
        # STEP 2: Generate Word CV
        # ====================================================================
        progress(0.4, desc="📝 Generating Word document...")

        word_path = generate_cv(
            str(cv_json_path),
            output_dir=str(output_dir),
            language=language,
            interactive=False
        )

        progress(0.5, desc="✅ Word document created")

        # ====================================================================
        # STEP 3: Job Matching (if enabled)
        # ====================================================================
        matchmaking_json_path = None
        angebot_json_path = None

        if job_pdf and mode == "full":
            progress(0.6, desc="🎯 Analyzing job match...")

            # Save job profile JSON
            job_json_path = output_dir / f"job_{timestamp}.json"
            with open(job_json_path, "w", encoding="utf-8") as f:
                json.dump(job_profile_context, f, ensure_ascii=False, indent=2)

            # Generate matchmaking
            matchmaking_json_path = output_dir / f"match_{timestamp}.json"
            schema_path = "scripts/matchmaking_json_schema.json"

            generate_matchmaking_json(
                str(cv_json_path),
                str(job_json_path),
                str(matchmaking_json_path),
                schema_path,
                language=language
            )

            progress(0.7, desc="✅ Job matching completed")

            # Generate offer
            if mode == "full":
                progress(0.75, desc="📋 Generating offer document...")

                angebot_json_path = output_dir / f"offer_{timestamp}.json"
                offer_schema = "scripts/angebot_json_schema.json"

                generate_angebot_json(
                    str(cv_json_path),
                    str(job_json_path),
                    str(matchmaking_json_path),
                    str(angebot_json_path),
                    offer_schema,
                    language=language
                )

                progress(0.8, desc="✅ Offer document created")

        # ====================================================================
        # STEP 4: Quality Feedback
        # ====================================================================
        progress(0.85, desc="🔍 Running quality checks...")

        feedback_json_path = output_dir / f"feedback_{timestamp}.json"
        feedback_schema = "scripts/cv_feedback_json_schema.json"

        generate_cv_feedback_json(
            str(cv_json_path),
            str(feedback_json_path),
            feedback_schema,
            str(job_json_path) if job_pdf else None,
            language=language
        )

        progress(0.9, desc="✅ Quality check completed")

        # ====================================================================
        # STEP 5: Dashboard
        # ====================================================================
        progress(0.95, desc="📊 Creating dashboard...")

        dashboard_path = generate_dashboard(
            cv_json_path=str(cv_json_path),
            match_json_path=str(matchmaking_json_path) if matchmaking_json_path else None,
            feedback_json_path=str(feedback_json_path),
            output_dir=str(output_dir),
            model_name=model_id,
            pipeline_mode="Gradio UI",
            cv_filename=cv_pdf.name,
            job_filename=job_pdf.name if job_pdf else None,
            angebot_json_path=str(angebot_json_path) if angebot_json_path else None,
            language=language
        )

        progress(1.0, desc="✅ Pipeline completed!")

        # Read dashboard HTML
        with open(dashboard_path, "r", encoding="utf-8") as f:
            dashboard_html = f.read()

        # Create summary
        summary = f"""
## ✅ CV Processing Complete!

**Candidate**: {vorname} {nachname}
**Model**: {selected_model}
**Language**: {language.upper()}
**Mode**: {mode}

### Generated Files:
- 📝 Word CV: `{Path(word_path).name}`
- 📊 Dashboard: `{Path(dashboard_path).name}`
- 📋 CV Data: `{cv_json_path.name}`
"""

        if matchmaking_json_path:
            # Get match score
            with open(matchmaking_json_path, "r") as f:
                match_data = json.load(f)
                score = match_data.get("match_score", {}).get("score_gesamt", "N/A")

            summary += f"- 🎯 Match Score: **{score}%**\n"

        summary += f"\n**Output Directory**: `{output_dir}`"

        return word_path, dashboard_html, summary

    except Exception as e:
        import traceback
        error_msg = f"❌ Error: {str(e)}\n\n```\n{traceback.format_exc()}\n```"
        return None, None, error_msg

# ============================================================================
# COST CALCULATOR
# ============================================================================

def calculate_cost(model_choice, num_cvs):
    """Calculate monthly cost estimate"""

    models = ModelRegistry.get_available_models()
    model_id = None
    for mid, info in models.items():
        if info['display_name'] in model_choice:
            model_id = mid
            break

    if not model_id:
        return "Model not found"

    estimate = ModelRegistry.estimate_cost(model_id, num_cvs)

    return f"""
### 💰 Cost Estimate

**Model**: {model_choice}
**CVs per month**: {num_cvs}

**Monthly Cost**: {estimate['monthly_cost']}
**Yearly Cost**: {estimate['yearly_cost']}
"""

# ============================================================================
# GRADIO UI
# ============================================================================

# Custom CSS
custom_css = """
.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.progress-bar {
    border-radius: 8px !important;
}

footer {
    display: none !important;
}

.tab-nav button {
    font-weight: 600;
}
"""

# Create UI
with gr.Blocks(theme=gr.themes.Soft(), css=custom_css, title="CV Generator") as demo:

    gr.Markdown("""
    # 🎯 CV Generator (Gradio Edition)
    **AI-powered CV processing with real-time progress**

    Upload a CV PDF, select your AI model, and generate professional Word documents + analytics dashboard.
    """)

    with gr.Tabs():
        # ====================================================================
        # TAB 1: MAIN PROCESSING
        # ====================================================================
        with gr.Tab("📄 Generate CV"):

            with gr.Row():
                # Left Column: Inputs
                with gr.Column(scale=1):
                    gr.Markdown("### Upload Files")

                    cv_upload = gr.File(
                        label="CV PDF (Required)",
                        file_types=[".pdf"],
                        file_count="single"
                    )

                    job_upload = gr.File(
                        label="Job Profile PDF (Optional)",
                        file_types=[".pdf"],
                        file_count="single"
                    )

                    gr.Markdown("### Configuration")

                    # Model selector
                    models = ModelRegistry.get_available_models()
                    model_options = [
                        f"{info['display_name']} ({info['speed']})"
                        for _, info in sorted(models.items(), key=lambda x: x[1]['cost_per_cv'])
                    ]

                    model_select = gr.Dropdown(
                        choices=model_options,
                        value=model_options[0],  # GPT-4o-mini by default
                        label="AI Model",
                        info="Different models have different costs and quality"
                    )

                    language_select = gr.Radio(
                        choices=["de", "en", "fr"],
                        value="de",
                        label="Output Language"
                    )

                    mode_select = gr.Radio(
                        choices=["cv_only", "full"],
                        value="full",
                        label="Processing Mode",
                        info="Full mode includes job matching and offer generation"
                    )

                    process_btn = gr.Button(
                        "🚀 Generate CV",
                        variant="primary",
                        size="lg"
                    )

                # Right Column: Outputs
                with gr.Column(scale=1):
                    gr.Markdown("### Results")

                    summary_output = gr.Markdown(
                        value="Upload a CV and click 'Generate CV' to start...",
                        label="Summary"
                    )

                    word_output = gr.File(
                        label="📝 Generated Word CV",
                        interactive=False
                    )

                    dashboard_output = gr.HTML(
                        label="📊 Dashboard Preview"
                    )

            # Connect button
            process_btn.click(
                fn=process_cv_pipeline,
                inputs=[
                    cv_upload,
                    job_upload,
                    model_select,
                    language_select,
                    mode_select
                ],
                outputs=[
                    word_output,
                    dashboard_output,
                    summary_output
                ]
            )

        # ====================================================================
        # TAB 2: COST CALCULATOR
        # ====================================================================
        with gr.Tab("💰 Cost Calculator"):
            gr.Markdown("### Estimate your monthly AI costs")

            with gr.Row():
                calc_model = gr.Dropdown(
                    choices=model_options,
                    value=model_options[0],
                    label="Select Model"
                )

            with gr.Row():
                calc_cvs = gr.Slider(
                    minimum=10,
                    maximum=1000,
                    value=100,
                    step=10,
                    label="CVs per Month"
                )

            calc_btn = gr.Button("Calculate", variant="primary")

            calc_output = gr.Markdown()

            calc_btn.click(
                fn=calculate_cost,
                inputs=[calc_model, calc_cvs],
                outputs=calc_output
            )

        # ====================================================================
        # TAB 3: MODEL COMPARISON
        # ====================================================================
        with gr.Tab("🤖 Model Comparison"):
            gr.Markdown("### Available AI Models")

            models_data = []
            for model_id, info in sorted(models.items(), key=lambda x: x[1]['cost_per_cv']):
                models_data.append([
                    info['display_name'],
                    info['provider'],
                    f"${info['cost_per_cv']:.3f}",
                    info['speed'],
                    info['quality'],
                    info.get('note', '-')
                ])

            gr.Dataframe(
                headers=["Model", "Provider", "Cost/CV", "Speed", "Quality", "Note"],
                datatype=["str", "str", "str", "str", "str", "str"],
                value=models_data,
                interactive=False
            )

            gr.Markdown("""
            ### Recommendations:

            - **Testing (5-10 CVs)**: Use **PyResParser** (FREE) for basic extraction
            - **Production (<1000 CVs/month)**: Use **GPT-4o-mini** (best value)
            - **High Quality**: Use **Claude 3.7 Sonnet** or **GPT-4o**
            - **Fast Processing**: Use **Claude 3.5 Haiku**
            """)

        # ====================================================================
        # TAB 4: ABOUT
        # ====================================================================
        with gr.Tab("ℹ️ About"):
            gr.Markdown(f"""
            ## CV Generator - Gradio Edition

            **Version**: 2.0 (Gradio UI)
            **Multi-Language**: German, English, French
            **AI Models**: 8 models supported (OpenAI, Anthropic, PyResParser)

            ### Features:

            ✅ **Real-time Progress**: See exactly what's happening during processing
            ✅ **Multi-User Queuing**: Handle multiple simultaneous users
            ✅ **Model Flexibility**: Choose from 8 different AI models
            ✅ **Cost Transparency**: Calculate costs before processing
            ✅ **Professional Output**: Word CVs + HTML Dashboard

            ### Tech Stack:

            - **Frontend**: Gradio (Python)
            - **AI**: OpenAI GPT / Anthropic Claude / PyResParser
            - **Document**: python-docx
            - **Hosting**: Railway.app ($6/month)

            ### Documentation:

            - [Tech Debt Report](docs/TECH_DEBT.md)
            - [Serverless Architecture](docs/SERVERLESS_ARCHITECTURE.md)
            - [Deployment Guide](docs/LEAN_DEPLOYMENT.md)

            ---

            **Built with ❤️ by Marco Rieben**
            **Powered by**: {os.getenv('MODEL_NAME', 'gpt-4o-mini')}
            """)

# ============================================================================
# LAUNCH
# ============================================================================

if __name__ == "__main__":
    # Enable queuing for multi-user support
    demo.queue(
        concurrency_count=5,  # 5 simultaneous users
        max_size=20  # Queue size
    )

    # Launch
    demo.launch(
        server_name="0.0.0.0",  # Listen on all interfaces
        server_port=int(os.getenv("PORT", 7860)),  # Railway uses PORT env var
        share=False,  # No public Gradio link (use Railway URL)
        auth=None,  # Add auth if needed: auth=("admin", "password")
        show_error=True,
        favicon_path="templates/logo.png" if os.path.exists("templates/logo.png") else None
    )
