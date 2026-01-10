"""
Streamlit UI Component: Model Selector
Drop-in component for AI model selection with cost estimates
"""
import streamlit as st
from scripts.model_registry import ModelRegistry

def render_model_selector(language: str = "de") -> str:
    """
    Renders a model selection dropdown with cost estimates.

    Returns:
        str: Selected model ID (e.g., "gpt-4o-mini")
    """

    # Translations
    labels = {
        "de": {
            "title": "🤖 KI-Modell Auswahl",
            "select": "Wähle KI-Modell:",
            "help": "Verschiedene Modelle haben unterschiedliche Kosten und Qualität",
            "provider": "Anbieter",
            "cost_cv": "Kosten pro CV",
            "speed": "Geschwindigkeit",
            "quality": "Qualität",
            "estimate_title": "💰 Kosten-Schätzung",
            "monthly_cvs": "Geschätzte CVs pro Monat:",
            "monthly_cost": "Monatliche Kosten",
            "note": "Hinweis"
        },
        "en": {
            "title": "🤖 AI Model Selection",
            "select": "Select AI Model:",
            "help": "Different models have different costs and quality trade-offs",
            "provider": "Provider",
            "cost_cv": "Cost per CV",
            "speed": "Speed",
            "quality": "Quality",
            "estimate_title": "💰 Cost Estimate",
            "monthly_cvs": "Estimated CVs per month:",
            "monthly_cost": "Monthly Cost",
            "note": "Note"
        },
        "fr": {
            "title": "🤖 Sélection du modèle IA",
            "select": "Sélectionner le modèle IA:",
            "help": "Différents modèles ont des coûts et une qualité différents",
            "provider": "Fournisseur",
            "cost_cv": "Coût par CV",
            "speed": "Vitesse",
            "quality": "Qualité",
            "estimate_title": "💰 Estimation des coûts",
            "monthly_cvs": "CVs estimés par mois:",
            "monthly_cost": "Coût mensuel",
            "note": "Remarque"
        }
    }

    t = labels.get(language, labels["de"])

    # Get available models
    models = ModelRegistry.get_available_models()

    # Create dropdown options (sorted by cost)
    sorted_models = sorted(
        models.items(),
        key=lambda x: x[1]['cost_per_cv']
    )

    model_options = {}
    for model_id, info in sorted_models:
        display_text = f"{info['display_name']} - ${info['cost_per_cv']:.3f}/CV"
        model_options[display_text] = model_id

    # Render dropdown
    st.subheader(t["title"])

    # Find default (recommended model)
    default_model = next(
        (idx for idx, (_, model_id) in enumerate(model_options.items())
         if models[model_id].get('recommended')),
        0
    )

    selected_display = st.selectbox(
        t["select"],
        options=list(model_options.keys()),
        index=default_model,
        help=t["help"]
    )

    selected_model_id = model_options[selected_display]
    model_info = models[selected_model_id]

    # Display model details in columns
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(t["provider"], model_info['provider'])

    with col2:
        st.metric(t["cost_cv"], f"${model_info['cost_per_cv']:.3f}")

    with col3:
        st.metric(t["quality"], model_info['quality'])

    # Speed indicator
    st.caption(f"{t['speed']}: {model_info['speed']}")

    # Show note if exists
    if model_info.get('note'):
        st.info(f"ℹ️ {t['note']}: {model_info['note']}")

    # Cost estimator (collapsible)
    with st.expander(t["estimate_title"], expanded=False):
        num_cvs = st.slider(
            t["monthly_cvs"],
            min_value=10,
            max_value=1000,
            value=100,
            step=10
        )

        estimate = ModelRegistry.estimate_cost(selected_model_id, num_cvs)

        st.metric(t["monthly_cost"], estimate['monthly_cost'])

        # Show comparison with other models
        st.caption("Vergleich:")

        comparison_data = []
        for other_id in ["gpt-4o-mini", "claude-3-5-haiku-20241022", "pyresparser"]:
            if other_id in models:
                other_estimate = ModelRegistry.estimate_cost(other_id, num_cvs)
                comparison_data.append({
                    "Modell": models[other_id]['display_name'],
                    "Kosten": other_estimate['monthly_cost']
                })

        import pandas as pd
        st.dataframe(pd.DataFrame(comparison_data), hide_index=True)

    # Store in session state
    st.session_state.selected_model = selected_model_id

    return selected_model_id


def render_cost_tracker(language: str = "de"):
    """
    Renders a cost tracking widget in the sidebar.
    Shows monthly usage and costs.
    """

    labels = {
        "de": {
            "title": "💰 Kosten-Tracker",
            "cvs_processed": "CVs verarbeitet (Monat):",
            "current_model": "Aktuelles Modell",
            "monthly_cost": "Monatliche Kosten",
            "budget": "Budget",
            "budget_exceeded": "⚠️ Budget überschritten!",
            "within_budget": "✅ Im Budget"
        },
        "en": {
            "title": "💰 Cost Tracker",
            "cvs_processed": "CVs processed (month):",
            "current_model": "Current Model",
            "monthly_cost": "Monthly Cost",
            "budget": "Budget",
            "budget_exceeded": "⚠️ Budget exceeded!",
            "within_budget": "✅ Within budget"
        },
        "fr": {
            "title": "💰 Suivi des coûts",
            "cvs_processed": "CVs traités (mois):",
            "current_model": "Modèle actuel",
            "monthly_cost": "Coût mensuel",
            "budget": "Budget",
            "budget_exceeded": "⚠️ Budget dépassé!",
            "within_budget": "✅ Dans le budget"
        }
    }

    t = labels.get(language, labels["de"])

    st.sidebar.header(t["title"])

    # Get usage from session state (or initialize)
    if 'monthly_cv_count' not in st.session_state:
        st.session_state.monthly_cv_count = 0

    # Display current count
    monthly_cvs = st.sidebar.number_input(
        t["cvs_processed"],
        min_value=0,
        max_value=10000,
        value=st.session_state.monthly_cv_count,
        step=1,
        disabled=True  # Read-only display
    )

    # Get current model
    selected_model = st.session_state.get('selected_model', 'gpt-4o-mini')
    models = ModelRegistry.get_available_models()
    model_name = models[selected_model]['display_name']

    st.sidebar.text(f"{t['current_model']}: {model_name}")

    # Calculate costs
    if monthly_cvs > 0:
        estimate = ModelRegistry.estimate_cost(selected_model, monthly_cvs)

        st.sidebar.metric(t["monthly_cost"], estimate['monthly_cost'])

        # Budget alert
        budget = st.sidebar.number_input(
            f"{t['budget']} (USD):",
            min_value=1,
            max_value=1000,
            value=10,
            step=5
        )

        cost_value = float(estimate['monthly_cost'].replace('$', ''))

        if cost_value > budget:
            st.sidebar.error(f"{t['budget_exceeded']} (${cost_value:.2f} > ${budget})")
        else:
            remaining = budget - cost_value
            st.sidebar.success(f"{t['within_budget']} (${remaining:.2f} übrig)")

    else:
        st.sidebar.info("Keine CVs verarbeitet diesen Monat")


def increment_cv_count():
    """Helper function to increment monthly CV count after successful generation"""
    if 'monthly_cv_count' not in st.session_state:
        st.session_state.monthly_cv_count = 0

    st.session_state.monthly_cv_count += 1


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    st.set_page_config(page_title="Model Selector Demo", layout="wide")

    # Demo of model selector
    st.title("AI Model Selector - Demo")

    # Sidebar cost tracker
    render_cost_tracker(language="de")

    # Main content
    selected_model = render_model_selector(language="de")

    st.write(f"**Selected Model ID**: `{selected_model}`")

    # Simulate CV upload
    if st.button("Simulate CV Processing"):
        st.success(f"CV processed with {selected_model}")
        increment_cv_count()
        st.rerun()  # Refresh to update cost tracker
