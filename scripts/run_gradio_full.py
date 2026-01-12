#!/usr/bin/env python3
"""
Full-Featured Gradio UI for CV Generator

Professional interface with sidebar configuration matching original Streamlit design.
Fully branded with CI/CD colors from styles.json.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import gradio as gr

# Import original pipeline logic
from scripts.streamlit_pipeline import StreamlitCVGenerator


def load_brand_colors():
    """Load brand colors from styles.json"""
    try:
        styles_path = Path(__file__).parent / "styles.json"
        with open(styles_path, 'r') as f:
            styles = json.load(f)

        # Extract primary color (orange)
        primary_rgb = styles.get("heading1", {}).get("color", [255, 121, 0])
        primary_hex = f"#{primary_rgb[0]:02x}{primary_rgb[1]:02x}{primary_rgb[2]:02x}"

        # Extract secondary color (dark gray)
        secondary_rgb = styles.get("heading2", {}).get("color", [68, 68, 68])
        secondary_hex = f"#{secondary_rgb[0]:02x}{secondary_rgb[1]:02x}{secondary_rgb[2]:02x}"

        return primary_hex, secondary_hex
    except:
        return "#ff7900", "#444444"  # Fallback colors


def load_translations():
    """Load UI translations from translations.json"""
    try:
        translations_path = Path(__file__).parent / "translations.json"
        with open(translations_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def t(translations: dict, key: str, lang: str = "en", **kwargs) -> str:
    """
    Get translated string.

    Args:
        translations: Translations dictionary
        key: Translation key (e.g., "ui.app_title")
        lang: Language code (de, en, fr)
        **kwargs: Format variables

    Returns:
        Translated string
    """
    keys = key.split('.')
    value = translations
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k, key)
        else:
            return key

    if isinstance(value, dict):
        value = value.get(lang, value.get('en', key))

    # Format with variables if provided
    if kwargs:
        try:
            value = value.format(**kwargs)
        except:
            pass

    return value


def get_git_history(limit=20):
    """Fetch recent git commit history with detailed body."""
    try:
        import subprocess
        # Use unique delimiter for commits to handle multi-line bodies
        cmd = [
            "git", "log", f"-n{limit}",
            "--pretty=format:COMMIT_START%h|%cd|%an|%s|%bCOMMIT_END",
            "--date=short"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8', cwd=Path(__file__).parent.parent)

        commits = []
        raw_commits = result.stdout.split("COMMIT_START")
        for raw in raw_commits:
            if not raw.strip():
                continue

            content = raw.replace("COMMIT_END", "").strip()
            parts = content.split("|", 4)
            if len(parts) >= 4:
                commits.append({
                    "hash": parts[0],
                    "date": parts[1],
                    "author": parts[2],
                    "message": parts[3],
                    "body": parts[4] if len(parts) > 4 else ""
                })
        return commits
    except Exception as e:
        return [{"hash": "-", "date": "-", "author": "System", "message": f"Could not load git history: {str(e)}", "body": ""}]


class GradioFullUI:
    """Full-featured Gradio UI with sidebar and CI/CD branding."""

    def __init__(self):
        """Initialize UI."""
        self.base_dir = Path(__file__).parent.parent
        self.pipeline = StreamlitCVGenerator(base_dir=str(self.base_dir))
        self.current_results = None
        self.history_file = self.base_dir / "output" / "run_history.json"
        self.history = self._load_history()  # Load from file
        self.primary_color, self.secondary_color = load_brand_colors()
        self.translations = load_translations()
        self.current_language = "de"  # Default language

    def t(self, key: str, **kwargs) -> str:
        """Get translated string in current language."""
        return t(self.translations, key, self.current_language, **kwargs)

    def _load_history(self) -> list:
        """Load history from JSON file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_history(self):
        """Save history to JSON file."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def add_to_history(self, job_info: dict):
        """Add job to history and save to file."""
        self.history.insert(0, job_info)  # Most recent first
        if len(self.history) > 50:  # Keep last 50
            self.history = self.history[:50]
        self._save_history()

    def _generate_changelog_html(self) -> str:
        """Generate HTML for git changelog with expandable commit details."""
        commits = get_git_history(20)

        relevant_types = {
            "feat": ("✨", "New Feature"),
            "fix": ("🐛", "Bug Fix"),
            "ui": ("🎨", "UI/Design"),
            "perf": ("⚡", "Performance"),
            "docs": ("📚", "Documentation"),
            "refactor": ("♻️", "Refactoring")
        }

        changelog_html = []
        visible_count = 0

        for commit in commits:
            msg = commit['message']
            category_icon = "📝"
            category_name = "General"
            clean_msg = msg
            is_relevant = False

            # Parse Conventional Commits
            if ":" in msg:
                parts = msg.split(":", 1)
                type_scope = parts[0].lower()
                # Handle scopes like feat(ui):
                if "(" in type_scope:
                    type_key = type_scope.split("(")[0]
                else:
                    type_key = type_scope.strip()

                if type_key in relevant_types:
                    category_icon, category_name = relevant_types[type_key]
                    clean_msg = parts[1].strip()
                    is_relevant = True
                elif type_key in ["chore", "test", "ci", "build"]:
                    is_relevant = False  # Skip technical commits
            else:
                # Show non-conventional commits unless they look like merges
                if not msg.startswith("Merge"):
                    is_relevant = True

            if is_relevant:
                visible_count += 1

                # Create expandable entry
                body_preview = ""
                if commit.get('body'):
                    body_cleaned = commit['body'].strip()
                    if body_cleaned:
                        # Show first line or 100 chars
                        first_line = body_cleaned.split('\n')[0][:100]
                        body_preview = f"<div style='font-size: 0.85em; color: #666; margin-top: 5px; font-style: italic;'>{first_line}...</div>"

                changelog_html.append(f"""
                <details style='margin-bottom: 10px; border: 1px solid #ddd; border-radius: 5px; padding: 10px; background: white;'>
                    <summary style='cursor: pointer; font-weight: 500;'>
                        <span style='font-size: 1.1em;'>{category_icon}</span>
                        {commit['date']} | {category_name} | {clean_msg}
                    </summary>
                    <div style='margin-top: 10px; padding-left: 10px; border-left: 3px solid {self.primary_color};'>
                        <div style='font-size: 0.9em; color: #666; margin-bottom: 5px;'>
                            <strong>Commit:</strong> <code>{commit['hash']}</code> | <strong>Author:</strong> {commit['author']}
                        </div>
                        {f"<div style='margin-top: 8px; padding: 10px; background: #f8f9fa; border-radius: 4px; font-size: 0.9em;'>{commit['body'].strip()}</div>" if commit.get('body') and commit['body'].strip() else "<div style='color: #999; font-size: 0.85em; font-style: italic;'>No additional details available.</div>"}
                    </div>
                </details>
                """)

        if visible_count == 0:
            return "<p style='color: #666; font-style: italic;'>No relevant changes found in recent commits.</p>"

        return "\n".join(changelog_html)

    def get_history_display(self, lang: str = None) -> str:
        """Format history for display with match score bars and file links."""
        if lang is None:
            lang = self.current_language

        if not self.history:
            return "<p style='color: #666; font-style: italic;'>No previous runs yet.</p>"

        history_html = []
        for i, job in enumerate(self.history):
            timestamp = job.get('timestamp', 'Unknown')
            # Format timestamp nicely
            try:
                if len(timestamp) == 15:  # Format: YYYYMMDD_HHMMSS
                    dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    display_time = dt.strftime("%d.%m. %H:%M")
                else:
                    display_time = timestamp
            except:
                display_time = timestamp

            name = job.get('candidate_name') or job.get('name', 'Unknown')
            mode = job.get('mode', 'Unknown')
            model = job.get('model_name') or job.get('model', 'Unknown')
            status = "✅" if job.get('success') else "❌"
            match_score = job.get('match_score')

            # Start entry HTML
            entry_html = f"""
            <div style='border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin-bottom: 12px; background: white;'>
                <div style='font-weight: bold; margin-bottom: 5px;'>{status} {name}</div>
                <div style='font-size: 0.85em; color: #666; margin-bottom: 8px;'>
                    {display_time} | {mode} | {model}
                </div>
            """

            # Add match score bar if available
            if match_score is not None:
                try:
                    score_val = float(match_score)
                    if score_val >= 80:
                        bar_color = "#27ae60"  # Green
                    elif score_val >= 60:
                        bar_color = "#f39c12"  # Orange
                    else:
                        bar_color = "#c0392b"  # Red

                    entry_html += f"""
                    <div style='margin-bottom: 8px;'>
                        <div style='font-size: 0.8em; color: #666; margin-bottom: 3px;'>Match Score: {score_val}%</div>
                        <div style='background-color: #eee; border-radius: 4px; height: 8px; width: 100%;'>
                            <div style='background-color: {bar_color}; width: {score_val}%; height: 100%; border-radius: 4px;'></div>
                        </div>
                    </div>
                    """
                except:
                    pass

            # Add file links if available
            files = []
            if job.get('word_path'):
                files.append(('📄 CV Word', job['word_path']))
            if job.get('cv_json'):
                files.append(('📋 CV JSON', job['cv_json']))
            if job.get('dashboard_path'):
                files.append(('📊 Dashboard', job['dashboard_path']))
            if job.get('match_json'):
                files.append(('🎯 Match', job['match_json']))
            if job.get('offer_word_path'):
                files.append(('📜 Offer', job['offer_word_path']))

            if files:
                entry_html += "<div style='margin-top: 8px;'>"
                for label, path in files:
                    if path and os.path.exists(path):
                        filename = os.path.basename(path)
                        entry_html += f"<div style='font-size: 0.8em; margin: 2px 0;'>→ {label}: <code>{filename}</code></div>"
                entry_html += "</div>"

            entry_html += "</div>"
            history_html.append(entry_html)

        return "\n".join(history_html)

    def process_cv(
        self,
        cv_file,
        job_file,
        pipeline_mode: str,
        model: str,
        language: str,
        cache_enabled: bool,
        progress=gr.Progress()
    ) -> Tuple[str, str, str, str, str, str, str, bool, str, str]:
        """
        Process CV with selected pipeline mode.

        Returns:
            (status_msg, cv_json, word_file, dashboard_html, matchmaking_json,
             feedback_json, offer_word, show_offer_button, match_score_display, history_display)
        """
        try:
            # Debug: Print model value
            print(f"[DEBUG] Model value received: '{model}' (type: {type(model)})")

            # In mock mode, files are optional (uses test data)
            # Check if model contains 'mock' (case insensitive) to handle different formats
            is_mock = model and ('mock' in model.lower() if isinstance(model, str) else False)

            if not is_mock:
                if cv_file is None:
                    return ("❌ Please upload a CV PDF", None, None, None, None, None, None, False, "", self.get_history_display())

                # Validate inputs
                if pipeline_mode in ["Analysis", "Full"] and job_file is None:
                    return (f"❌ {pipeline_mode} mode requires a job profile PDF",
                            None, None, None, None, None, None, False, "", self.get_history_display())

            # Set model environment variable (extract just the model name if it's a full label)
            model_name = model.lower() if model else 'mock'
            if 'mock' in model_name:
                model_name = 'mock'
            elif 'gpt-4o-mini' in model_name:
                model_name = 'gpt-4o-mini'
            elif 'gpt-4o' in model_name and 'mini' not in model_name:
                model_name = 'gpt-4o'
            elif 'claude' in model_name or 'haiku' in model_name:
                model_name = 'claude-3-5-haiku'

            os.environ['MODEL_NAME'] = model_name
            print(f"[DEBUG] Set MODEL_NAME to: '{model_name}'")

            # Update model variable for subsequent checks
            model = model_name

            # Mock mode indicator
            if model == "mock":
                progress(0.05, desc="🧪 Mock Mode - Using test data (no API costs)")

            # Progress callback
            def progress_callback(pct: int, status: str, state: str):
                if model == "mock":
                    progress(pct / 100.0, desc=f"🧪 MOCK: {status}")
                else:
                    progress(pct / 100.0, desc=status)

            # Run pipeline
            # In mock mode, pass None for files to use test data
            results = self.pipeline.run(
                cv_file=cv_file.name if cv_file and hasattr(cv_file, 'name') else (cv_file if cv_file else None),
                job_file=job_file.name if job_file and hasattr(job_file, 'name') else (job_file if job_file else None),
                progress_callback=progress_callback,
                pipeline_mode="Analysis" if pipeline_mode in ["Analysis", "Full"] else "Basic",
                language=language
            )

            if not results["success"]:
                error_msg = results.get("error", "Unknown error occurred")
                return (f"❌ Error: {error_msg}", None, None, None, None, None, None, False, "", self.get_history_display())

            # Store results
            self.current_results = results

            # Extract results
            cv_json_path = results.get("cv_json")
            word_path = results.get("word_path")
            dashboard_path = results.get("dashboard_path")
            match_json_path = results.get("match_json")
            match_score = results.get("match_score")

            # Read dashboard HTML
            dashboard_html = None
            if dashboard_path and os.path.exists(dashboard_path):
                with open(dashboard_path, 'r', encoding='utf-8') as f:
                    dashboard_html = f.read()

            # Build success message
            files_generated = []
            if cv_json_path:
                files_generated.append(f"✅ CV JSON: {os.path.basename(cv_json_path)}")
            if word_path:
                files_generated.append(f"✅ CV Word: {os.path.basename(word_path)}")
            if dashboard_path:
                files_generated.append(f"✅ Dashboard: {os.path.basename(dashboard_path)}")
            if match_json_path:
                files_generated.append(f"✅ Matchmaking: {os.path.basename(match_json_path)}")

            # Add mock mode indicator
            if model == "mock":
                success_msg = "🎉 Pipeline completed! 🧪 **Mock Mode - Test Data**\n\n" + "\n".join(files_generated)
                success_msg += "\n\n💡 **Note:** Mock data used. No API costs incurred."
            else:
                success_msg = "🎉 Pipeline completed successfully!\n\n" + "\n".join(files_generated)

            # Get output directory
            output_dir = ""
            if cv_json_path:
                output_dir = os.path.dirname(cv_json_path)
                success_msg += f"\n\n📁 Output: {output_dir}"

            # Show match score
            show_offer_btn = False
            match_score_display = ""

            if pipeline_mode in ["Analysis", "Full"] and match_score is not None:
                match_score_display = f"### Match Score: {match_score}%\n\n"
                if match_score >= 70:
                    match_score_display += "✅ **Excellent match!** "
                elif match_score >= 50:
                    match_score_display += "⚠️ **Good match with gaps.** "
                else:
                    match_score_display += "❌ **Low match.** "

                if pipeline_mode == "Full":
                    show_offer_btn = True
                    match_score_display += "\n\nClick 'Generate Offer' to create offer document."

            # Add to history with all file paths
            name = results.get("vorname", "Unknown") + " " + results.get("nachname", "")
            self.add_to_history({
                'timestamp': self.pipeline.timestamp,  # Use pipeline timestamp for consistency
                'candidate_name': name.strip(),
                'name': name.strip(),  # Keep for backwards compatibility
                'mode': pipeline_mode,
                'model_name': model,
                'model': model,  # Keep for backwards compatibility
                'success': True,
                'match_score': match_score if match_score else None,
                'word_path': word_path,
                'cv_json': cv_json_path,
                'dashboard_path': dashboard_html,
                'match_json': match_json_path if match_json_path and os.path.exists(match_json_path) else None,
                'stellenprofil_json': stellenprofil_json_path if stellenprofil_json_path and os.path.exists(stellenprofil_json_path) else None,
                'offer_word_path': None  # Will be updated when offer is generated
            })

            return (
                success_msg,
                cv_json_path,
                word_path,
                dashboard_html,
                match_json_path if match_json_path and os.path.exists(match_json_path) else None,
                None,  # feedback in dashboard
                None,  # offer generated separately
                show_offer_btn,
                match_score_display,
                self.get_history_display()
            )

        except Exception as e:
            import traceback
            error_msg = f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"

            # Add failed job to history
            self.add_to_history({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'name': 'Failed Job',
                'mode': pipeline_mode,
                'model': model,
                'success': False
            })

            return (error_msg, None, None, None, None, None, None, False, "", self.get_history_display())

    def generate_offer(self, progress=gr.Progress()) -> Tuple[str, str, str]:
        """Generate offer document after reviewing match score."""
        try:
            if not self.current_results:
                return ("❌ Please run the pipeline first", None, self.get_history_display())

            if not self.current_results.get("match_json"):
                return ("❌ No match analysis available", None, self.get_history_display())

            progress(0.5, desc="Generating offer document...")

            from scripts.generate_angebot import generate_angebot_json
            from scripts.generate_angebot_word import generate_angebot_word

            # Get paths
            cv_json_path = self.current_results["cv_json"]
            stellenprofil_json_path = self.current_results.get("stellenprofil_json")
            match_json_path = self.current_results["match_json"]
            output_dir = os.path.dirname(cv_json_path)

            # Extract name and timestamp
            cv_filename = os.path.basename(cv_json_path)
            parts = cv_filename.replace("cv_", "").replace(".json", "").split("_")
            if len(parts) >= 3:
                vorname, nachname = parts[0], parts[1]
                timestamp = "_".join(parts[2:])
            else:
                vorname, nachname = "Unknown", ""
                timestamp = self.pipeline.timestamp

            language = self.current_results.get("language", "de")

            # Generate offer JSON
            angebot_json_path = os.path.join(output_dir, f"Angebot_{vorname}_{nachname}_{timestamp}.json")
            generate_angebot_json(cv_json_path, stellenprofil_json_path, match_json_path,
                                angebot_json_path, language=language)

            progress(0.8, desc="Creating Word document...")

            # Generate Word
            angebot_word_path = os.path.join(output_dir, f"Angebot_{vorname}_{nachname}_{timestamp}.docx")
            generate_angebot_word(angebot_json_path, angebot_word_path, language=language)

            success_msg = f"✅ Offer generated!\n\n📄 {os.path.basename(angebot_word_path)}"

            return (success_msg, angebot_word_path, self.get_history_display())

        except Exception as e:
            import traceback
            error_msg = f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
            return (error_msg, None, self.get_history_display())

    def create_interface(self):
        """Create Gradio interface with sidebar."""

        # Custom CSS with CI/CD branding and collapsible sidebar
        custom_css = f"""
        /* CI/CD Brand Colors */
        :root {{
            --primary-color: {self.primary_color};
            --secondary-color: {self.secondary_color};
        }}

        /* Sidebar styling with collapse functionality */
        .sidebar {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-right: 3px solid var(--primary-color);
            padding: 20px;
            transition: all 0.3s ease;
            position: relative;
        }}

        .sidebar.collapsed {{
            width: 60px !important;
            min-width: 60px !important;
            padding: 10px !important;
        }}

        .sidebar.collapsed .sidebar-content {{
            display: none;
        }}

        .sidebar-toggle {{
            position: absolute;
            top: 10px;
            right: -15px;
            background: var(--primary-color);
            color: white;
            border: none;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            z-index: 100;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}

        .sidebar-toggle:hover {{
            background: {self.secondary_color};
        }}

        /* Primary buttons */
        .primary-btn {{
            background: var(--primary-color) !important;
            border: none !important;
            font-weight: bold !important;
        }}

        /* Headers */
        h1, h2, h3 {{
            color: var(--secondary-color);
            font-family: 'Aptos', 'Segoe UI', sans-serif;
        }}

        h1 {{
            color: var(--primary-color);
            border-bottom: 3px solid var(--primary-color);
            padding-bottom: 10px;
        }}

        /* Sidebar sections */
        .sidebar-section {{
            background: white;
            border-left: 4px solid var(--primary-color);
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .sidebar-header {{
            color: var(--primary-color);
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 10px;
            text-transform: uppercase;
        }}

        /* Status messages */
        .success {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .error {{ color: #dc3545; }}
        """

        # JavaScript for sidebar toggle
        custom_js = """
        <script>
        function toggleSidebar() {
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) {
                sidebar.classList.toggle('collapsed');
            }
        }
        </script>
        """

        with gr.Blocks(css=custom_css, title="CV Generator Pro", theme=gr.themes.Soft(), head=custom_js) as demo:

            # Sidebar toggle state
            sidebar_visible = gr.State(True)

            # Header with logo simulation
            with gr.Row():
                gr.Markdown(f"""
                # <span style="color: {self.primary_color};">🎯 CV Generator Pro</span>
                **Professional AI-Powered CV Processing & Job Matching**
                """)

            with gr.Row():
                # SIDEBAR - Collapsible (click toggle button to show/hide)
                with gr.Column(scale=1, elem_classes="sidebar", elem_id="sidebar-column", visible=True) as sidebar_column:
                    # Toggle button at top of sidebar
                    sidebar_toggle_btn = gr.Button(
                        "<<",
                        size="sm",
                        elem_id="sidebar-toggle-btn",
                        variant="secondary"
                    )

                    gr.HTML("""
                    <div style="text-align: center; padding: 5px; background: linear-gradient(90deg, #ff7900, #ff9933);
                                color: white; font-weight: bold; border-radius: 5px; margin-bottom: 10px;">
                        ⚙️ CONFIGURATION PANEL
                    </div>
                    """)
                    with gr.Accordion("📋 Pipeline & Model Settings", open=True):
                        # Pipeline Mode
                        with gr.Group():
                            gr.Markdown("**Pipeline Mode**")
                            pipeline_mode = gr.Radio(
                                choices=[
                                    ("📄 Basic - CV Only", "Basic"),
                                    ("🎯 Analysis - CV + Matching", "Analysis"),
                                    ("📜 Full - CV + Matching + Offer", "Full")
                                ],
                                value="Basic",
                                label="",
                                info="Choose your workflow"
                            )

                        # Model Selection
                        with gr.Group():
                            gr.Markdown("**🤖 AI Model**")
                            model = gr.Dropdown(
                                choices=[
                                    ("GPT-4o Mini ($0.01/CV)", "gpt-4o-mini"),
                                    ("GPT-4o ($0.15/CV)", "gpt-4o"),
                                    ("Claude Haiku ($0.03/CV)", "claude-3-5-haiku"),
                                    ("Mock (Free)", "mock")
                                ],
                                value="gpt-4o-mini",
                                label="",
                                info="Select LLM model"
                            )

                        # Language
                        language_header = gr.Markdown("**🌍 Language**")
                        with gr.Group():
                            language = gr.Dropdown(
                                choices=[
                                    ("🇩🇪 Deutsch", "de"),
                                    ("🇬🇧 English", "en"),
                                    ("🇫🇷 Français", "fr")
                                ],
                                value="de",
                                label="",
                                info="All documents in this language"
                            )
                            language_info = gr.Markdown(
                                "📝 All documents generated in selected language",
                                visible=True
                            )

                        # Settings
                        with gr.Group():
                            gr.Markdown("**⚡ Settings**")
                            cache_enabled = gr.Checkbox(
                                value=True,
                                label="Enable Caching",
                                info="Save API costs"
                            )

                    gr.Markdown("---")

                    # Application Info Button
                    app_info_btn = gr.Button("ℹ️ Application Info", variant="secondary", size="sm")

                    # History
                    with gr.Accordion("📜 History", open=False):
                        # Hidden component for backwards compatibility with existing returns
                        history_display = gr.HTML(value="", visible=False)

                        if self.history:
                            # Create radio choices from history
                            history_choices = []
                            for i, job in enumerate(self.history[:10]):  # Show last 10
                                timestamp = job.get('timestamp', 'Unknown')
                                try:
                                    if len(timestamp) == 15:
                                        dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                                        display_time = dt.strftime("%d.%m %H:%M")
                                    else:
                                        display_time = timestamp
                                except:
                                    display_time = timestamp

                                name = job.get('candidate_name') or job.get('name', 'Unknown')
                                status = "✅" if job.get('success') else "❌"
                                score = job.get('match_score')
                                score_str = f" | {score}%" if score else ""

                                label = f"{status} {display_time} - {name}{score_str}"
                                history_choices.append((label, str(i)))

                            history_selector = gr.Radio(
                                choices=history_choices,
                                label="Select a past run to view details",
                                value=None
                            )

                            # Details section (initially hidden)
                            with gr.Group(visible=False) as history_details:
                                history_info = gr.Markdown("Select a run to see details")
                                with gr.Row():
                                    hist_cv_word = gr.File(label="📄 CV Word", visible=False)
                                    hist_cv_json = gr.File(label="📋 CV JSON", visible=False)
                                with gr.Row():
                                    hist_dashboard = gr.File(label="📊 Dashboard", visible=False)
                                    hist_match = gr.File(label="🎯 Match JSON", visible=False)
                                hist_offer = gr.File(label="📜 Offer", visible=False)
                        else:
                            gr.Markdown("_No previous runs yet._")
                            history_selector = gr.Radio(choices=[], visible=False)
                            history_details = gr.Group(visible=False)
                            history_info = gr.Markdown("")
                            hist_cv_word = gr.File(visible=False)
                            hist_cv_json = gr.File(visible=False)
                            hist_dashboard = gr.File(visible=False)
                            hist_match = gr.File(visible=False)
                            hist_offer = gr.File(visible=False)

                # Show sidebar button (visible when sidebar is hidden)
                with gr.Column(scale=0, min_width=40, visible=False) as show_sidebar_column:
                    show_sidebar_btn = gr.Button(
                        ">>",
                        size="sm",
                        elem_id="show-sidebar-btn",
                        variant="secondary"
                    )

                # MAIN CONTENT
                with gr.Column(scale=3):
                    # App Info Modal (hidden by default)
                    with gr.Group(visible=False) as app_info_modal:
                        with gr.Row():
                            gr.Markdown("# ℹ️ Application Information")
                            close_info_btn = gr.Button("✖ Close", size="sm", variant="secondary")

                        gr.Markdown(f"""
                        ### 🏢 CV Generator & Matchmaking Suite

                        **Version:** 2.0.0 | **Brand Color:** {self.primary_color.upper()}

                        **Core Features:**
                        - 🤖 AI-powered CV extraction & parsing
                        - 📄 Standardized Word document generation
                        - 🎯 Intelligent job profile matching
                        - 💡 Quality assurance & feedback
                        - 📜 Automated offer generation
                        - 📊 Interactive dashboards
                        - 🌍 Multi-language support (DE/EN/FR)

                        **Available Models:**
                        - GPT-4o Mini (~$0.01/CV) ✅ Recommended
                        - GPT-4o (~$0.15/CV) 💎 Premium
                        - Claude 3.5 Haiku (~$0.03/CV)
                        - Mock (Free) 🧪 Testing only

                        ---

                        ### 📜 Changelog (Recent Updates)
                        """)

                        # Generate changelog HTML
                        changelog_html = self._generate_changelog_html()
                        gr.HTML(value=changelog_html)

                    with gr.Tabs() as main_tabs:
                        with gr.Tab("📄 Generate CV"):
                            gr.Markdown("### Upload Files")

                            with gr.Row():
                                cv_file = gr.File(
                                    label="📎 CV (PDF)",
                                    file_types=[".pdf"],
                                    type="filepath"
                                )
                                job_file = gr.File(
                                    label="📋 Job Profile (PDF) - Optional",
                                    file_types=[".pdf"],
                                    type="filepath"
                                )

                            # File upload status indicators
                            cv_upload_status = gr.Markdown(value="", visible=False)
                            job_upload_status = gr.Markdown(value="", visible=False)

                            generate_btn = gr.Button(
                                "🚀 Start Processing",
                                variant="primary",
                                size="lg",
                                elem_classes="primary-btn"
                            )

                            gr.Markdown("### Results")

                            status_output = gr.Textbox(
                                label="Status",
                                lines=8,
                                interactive=False
                            )

                            match_score_output = gr.Markdown(
                                value="",
                                visible=False
                            )

                            offer_button = gr.Button(
                                "📜 Generate Offer Document",
                                variant="secondary",
                                visible=False
                            )

                            offer_status = gr.Textbox(
                                label="Offer Status",
                                lines=3,
                                visible=False,
                                interactive=False
                            )

                            # Downloads and Dashboard - Initially hidden until successful run
                            results_section = gr.Group(visible=False)
                            with results_section:
                                with gr.Tabs():
                                    with gr.Tab("📥 Downloads"):
                                        cv_json_output = gr.File(label="CV JSON")
                                        word_output = gr.File(label="📄 CV Word")
                                        matchmaking_output = gr.File(label="🎯 Matchmaking", visible=False)
                                        feedback_output = gr.File(label="💡 Feedback", visible=False)
                                        offer_output = gr.File(label="📜 Offer", visible=False)

                                    with gr.Tab("📊 Dashboard"):
                                        # Match score gauge (if available)
                                        match_score_gauge = gr.HTML(value="", visible=False)
                                        dashboard_output = gr.HTML(label="Interactive Dashboard")

                        with gr.Tab("ℹ️ Help"):
                            gr.Markdown(f"""
                            ## Pipeline Modes

                            ### 📄 Basic - CV Only
                            - Extracts CV data
                            - Generates Word document
                            - Creates dashboard
                            - **No job profile needed**

                            ### 🎯 Analysis - CV + Job Matching
                            - Everything in Basic
                            - Job matching analysis
                            - **Shows match score first**
                            - Skill gap analysis
                            - **Requires job profile**

                            ### 📜 Full - Complete Suite
                            - Everything in Analysis
                            - **Review match score → Generate offer**
                            - Two-step process saves tokens
                            - Personalized offer document
                            - **Requires job profile**

                            ## Multilingual Support

                            All documents generated in selected language:
                            - CV Word document
                            - Dashboard HTML
                            - Matchmaking analysis
                            - Feedback suggestions
                            - Offer document

                            ## Output Structure

                            Files saved in timestamped folders:
                            ```
                            output/FirstName_LastName_YYYYMMDD_HHMMSS/
                            ├── cv_FirstName_LastName_TIMESTAMP.json
                            ├── cv_FirstName_LastName_TIMESTAMP.docx
                            ├── Dashboard_FirstName_LastName_TIMESTAMP.html
                            ├── Match_FirstName_LastName_TIMESTAMP.json
                            └── Angebot_FirstName_LastName_TIMESTAMP.docx
                            ```

                            ## Brand Colors

                            - **Primary:** <span style="color: {self.primary_color}; font-weight: bold;">{self.primary_color.upper()}</span>
                            - **Secondary:** <span style="color: {self.secondary_color}; font-weight: bold;">{self.secondary_color.upper()}</span>

                            From `styles.json` - Applied to all Word documents
                            """)

            # Event handlers
            def on_cv_upload(file, model):
                """Show upload status when CV is uploaded."""
                if file:
                    filename = Path(file).name if isinstance(file, str) else file.name
                    return gr.update(
                        value=f"✅ <span style='color: #28a745;'>**CV uploaded:** {filename}</span>",
                        visible=True
                    )
                elif model == "mock":
                    return gr.update(
                        value="🧪 <span style='color: #28a745;'>**Mock Mode:** Using test CV data</span>",
                        visible=True
                    )
                return gr.update(value="", visible=False)

            def on_job_upload(file, model):
                """Show upload status when job profile is uploaded."""
                if file:
                    filename = Path(file).name if isinstance(file, str) else file.name
                    return gr.update(
                        value=f"✅ <span style='color: #28a745;'>**Job Profile uploaded:** {filename}</span>",
                        visible=True
                    )
                elif model == "mock":
                    return gr.update(
                        value="🧪 <span style='color: #28a745;'>**Mock Mode:** Using test job profile</span>",
                        visible=True
                    )
                return gr.update(value="", visible=False)

            def on_model_change(model, cv_file, job_file):
                """Update upload status when model changes to/from mock."""
                cv_status = on_cv_upload(cv_file, model)
                job_status = on_job_upload(job_file, model)
                return cv_status, job_status

            def create_gauge_chart(score: int, label: str = "Match Score") -> str:
                """Create HTML gauge chart for match score."""
                # Color based on score
                if score >= 80:
                    color = "#28a745"
                    rating = "Excellent"
                elif score >= 60:
                    color = "#ffc107"
                    rating = "Good"
                else:
                    color = "#dc3545"
                    rating = "Critical"

                return f"""
                <div style="text-align: center; padding: 20px;">
                    <h3>{label}</h3>
                    <div style="position: relative; width: 200px; height: 200px; margin: 0 auto;">
                        <svg viewBox="0 0 200 200" style="transform: rotate(-90deg);">
                            <!-- Background circle -->
                            <circle cx="100" cy="100" r="80" fill="none" stroke="#e0e0e0" stroke-width="20"/>
                            <!-- Progress circle -->
                            <circle cx="100" cy="100" r="80" fill="none" stroke="{color}" stroke-width="20"
                                    stroke-dasharray="{score * 5.024} 502.4" stroke-linecap="round"/>
                        </svg>
                        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);">
                            <div style="font-size: 48px; font-weight: bold; color: {color};">{score}%</div>
                            <div style="font-size: 18px; color: #666;">{rating}</div>
                        </div>
                    </div>
                </div>
                """

            def process_and_update(cv_file, job_file, pipeline_mode, model, language, cache_enabled):
                status, cv_json, word, dashboard, match, feedback, offer, show_btn, match_display, hist = self.process_cv(
                    cv_file, job_file, pipeline_mode, model, language, cache_enabled
                )
                # Show results section if processing was successful
                show_results = bool(cv_json or word or dashboard)

                # Conditional visibility based on pipeline mode
                # Basic: Only CV, no matching/feedback/offer
                # Analysis: CV + matching/feedback, no offer
                # Full: Everything
                show_matching = pipeline_mode in ["Analysis", "Full"] and match
                show_feedback = pipeline_mode in ["Analysis", "Full"] and feedback
                show_offer_file = pipeline_mode == "Full" and offer

                # Extract match score for gauge if available
                gauge_html = ""
                if match and show_matching:
                    try:
                        import json as json_lib
                        match_data = json_lib.load(open(match, 'r', encoding='utf-8'))
                        score = match_data.get('match_score', {}).get('score_gesamt', 0)
                        if score > 0:
                            gauge_html = create_gauge_chart(score, "Match Score")
                    except:
                        pass

                return {
                    status_output: status,
                    cv_json_output: cv_json,
                    word_output: word,
                    dashboard_output: dashboard,
                    matchmaking_output: gr.update(value=match, visible=show_matching),
                    feedback_output: gr.update(value=feedback, visible=show_feedback),
                    offer_output: gr.update(value=offer, visible=show_offer_file),
                    match_score_output: gr.update(value=match_display, visible=bool(match_display)),
                    match_score_gauge: gr.update(value=gauge_html, visible=bool(gauge_html)),
                    offer_button: gr.update(visible=show_btn),
                    offer_status: gr.update(visible=False),
                    results_section: gr.update(visible=show_results),
                    history_display: hist
                }

            # Sidebar toggle handler
            def toggle_sidebar(visible):
                """Toggle sidebar visibility."""
                new_visible = not visible
                button_text = ">>" if not new_visible else "<<"
                # When sidebar is hidden, show the "show sidebar" button
                show_btn_visible = not new_visible
                return (
                    new_visible,
                    gr.update(visible=new_visible),
                    gr.update(value=button_text),
                    gr.update(visible=show_btn_visible)
                )

            sidebar_toggle_btn.click(
                fn=toggle_sidebar,
                inputs=[sidebar_visible],
                outputs=[sidebar_visible, sidebar_column, sidebar_toggle_btn, show_sidebar_column]
            )

            # Show sidebar button click handler
            show_sidebar_btn.click(
                fn=toggle_sidebar,
                inputs=[sidebar_visible],
                outputs=[sidebar_visible, sidebar_column, sidebar_toggle_btn, show_sidebar_column]
            )

            # App Info modal handlers
            def show_app_info():
                return {
                    app_info_modal: gr.update(visible=True),
                    main_tabs: gr.update(visible=False)
                }

            def hide_app_info():
                return {
                    app_info_modal: gr.update(visible=False),
                    main_tabs: gr.update(visible=True)
                }

            app_info_btn.click(
                fn=show_app_info,
                outputs=[app_info_modal, main_tabs]
            )

            close_info_btn.click(
                fn=hide_app_info,
                outputs=[app_info_modal, main_tabs]
            )

            # File upload handlers
            cv_file.change(
                fn=on_cv_upload,
                inputs=[cv_file, model],
                outputs=cv_upload_status
            )

            job_file.change(
                fn=on_job_upload,
                inputs=[job_file, model],
                outputs=job_upload_status
            )

            # Language change handler
            def on_language_change(lang):
                """Handle language change."""
                self.current_language = lang
                return gr.update(value=f"📝 {t(self.translations, 'ui.language_changed', lang) or 'Language changed. New runs will use this language.'}")

            language.change(
                fn=on_language_change,
                inputs=[language],
                outputs=[language_info]
            )

            model.change(
                fn=on_model_change,
                inputs=[model, cv_file, job_file],
                outputs=[cv_upload_status, job_upload_status]
            )

            def on_language_change(lang):
                """Update UI language and update current language setting."""
                self.current_language = lang

                # Update language info text
                lang_texts = {
                    "de": "📝 Alle Dokumente werden auf Deutsch erstellt",
                    "en": "📝 All documents generated in English",
                    "fr": "📝 Tous les documents générés en français"
                }

                return gr.update(value=lang_texts.get(lang, lang_texts["en"]))

            language.change(
                fn=on_language_change,
                inputs=[language],
                outputs=[language_info]
            )

            generate_btn.click(
                fn=process_and_update,
                inputs=[cv_file, job_file, pipeline_mode, model, language, cache_enabled],
                outputs=[status_output, cv_json_output, word_output, dashboard_output,
                        matchmaking_output, feedback_output, offer_output,
                        match_score_output, match_score_gauge, offer_button, offer_status,
                        results_section, history_display]
            )

            def generate_and_show_offer():
                msg, offer_file, hist = self.generate_offer()
                return {
                    offer_status: gr.update(value=msg, visible=True),
                    offer_output: offer_file,
                    history_display: hist
                }

            offer_button.click(
                fn=generate_and_show_offer,
                outputs=[offer_status, offer_output, history_display]
            )

            # History selector handler
            def on_history_select(selected_index):
                """Load and display selected history item."""
                if selected_index is None:
                    return {
                        history_details: gr.update(visible=False),
                        history_info: "",
                        hist_cv_word: gr.update(value=None, visible=False),
                        hist_cv_json: gr.update(value=None, visible=False),
                        hist_dashboard: gr.update(value=None, visible=False),
                        hist_match: gr.update(value=None, visible=False),
                        hist_offer: gr.update(value=None, visible=False)
                    }

                idx = int(selected_index)
                if idx >= len(self.history):
                    return {history_details: gr.update(visible=False)}

                job = self.history[idx]

                # Build info markdown
                timestamp = job.get('timestamp', 'Unknown')
                try:
                    if len(timestamp) == 15:
                        dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                        display_time = dt.strftime("%d.%m.%Y %H:%M:%S")
                    else:
                        display_time = timestamp
                except:
                    display_time = timestamp

                name = job.get('candidate_name') or job.get('name', 'Unknown')
                mode = job.get('mode', 'Unknown')
                model = job.get('model_name') or job.get('model', 'Unknown')
                score = job.get('match_score')

                info_md = f"""
### {name}

**Date:** {display_time}
**Mode:** {mode}
**Model:** {model}
"""
                if score:
                    info_md += f"**Match Score:** {score}%\n"

                # Prepare file outputs
                cv_word = job.get('word_path') if job.get('word_path') and os.path.exists(job.get('word_path', '')) else None
                cv_json = job.get('cv_json') if job.get('cv_json') and os.path.exists(job.get('cv_json', '')) else None
                dashboard = job.get('dashboard_path') if job.get('dashboard_path') and os.path.exists(job.get('dashboard_path', '')) else None
                match = job.get('match_json') if job.get('match_json') and os.path.exists(job.get('match_json', '')) else None
                offer = job.get('offer_word_path') if job.get('offer_word_path') and os.path.exists(job.get('offer_word_path', '')) else None

                return {
                    history_details: gr.update(visible=True),
                    history_info: info_md,
                    hist_cv_word: gr.update(value=cv_word, visible=cv_word is not None),
                    hist_cv_json: gr.update(value=cv_json, visible=cv_json is not None),
                    hist_dashboard: gr.update(value=dashboard, visible=dashboard is not None),
                    hist_match: gr.update(value=match, visible=match is not None),
                    hist_offer: gr.update(value=offer, visible=offer is not None)
                }

            if self.history:
                history_selector.change(
                    fn=on_history_select,
                    inputs=[history_selector],
                    outputs=[history_details, history_info, hist_cv_word, hist_cv_json, hist_dashboard, hist_match, hist_offer]
                )

        return demo


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="CV Generator Gradio UI")
    parser.add_argument("--port", type=int, default=7860, help="Port to run on")
    parser.add_argument("--share", action="store_true", help="Create public link")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload on file changes")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("  CV Generator Pro - Gradio Interface")
    print("="*60)
    print(f"  Port: {args.port}")
    print(f"  Share: {args.share}")
    print(f"  Auto-reload: {not args.no_reload}")
    print("="*60 + "\n")

    ui = GradioFullUI()
    demo = ui.create_interface()

    # Enable auto-reload in development mode (like Streamlit's hot-reload)
    # This watches for file changes and automatically reloads
    demo.launch(
        server_name="0.0.0.0",
        server_port=args.port,
        share=args.share,
        show_error=True,
        inbrowser=False,  # Don't auto-open browser on reload
        # Gradio's built-in live reload - watches Python files and auto-reloads
        # Just save your changes and refresh the browser (F5)
        debug=not args.no_reload  # Enable debug mode for auto-reload
    )


if __name__ == '__main__':
    main()
