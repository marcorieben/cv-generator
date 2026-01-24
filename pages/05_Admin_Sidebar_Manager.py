import streamlit as st
import yaml
import os
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
import sys
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Initialize session state
if 'language' not in st.session_state:
    st.session_state.language = "de"

# Set current page for sidebar active state detection
st.session_state.current_page = "pages/05_Admin_Sidebar_Manager.py"

# Auth check
from core.database.db import Database
from core.database.translations import initialize_translations
from core.utils.session import get_database, get_translations_manager, get_text

# --- Import render_simple_sidebar from app ---
try:
    from app import render_simple_sidebar
except ImportError:
    def render_simple_sidebar():
        """Fallback if sidebar rendering fails"""
        pass


# Check if authenticated - if not, redirect to main app
if "authentication_status" not in st.session_state or not st.session_state.get("authentication_status"):
    st.info("👤 Bitte melden Sie sich zuerst an!")
    st.markdown("Klick [hier](/) um dich einzuloggen.")
    st.stop()

# --- Simple Sidebar with Logo and Navigation ---
render_simple_sidebar()

# ============ MAIN CONTENT ============

st.title("⚙️ Admin - Sidebar Manager")
st.markdown("Verwalte die Sidebar-Struktur einfach über die Tabelle unten.")

# Config file path
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "scripts", "sidebar_config.yaml")

# ============ LOAD & SAVE ============

def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        st.error(f"Fehler beim Laden: {e}")
        return None

def save_config(data):
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return True
    except Exception as e:
        st.error(f"Fehler beim Speichern: {e}")
        return False

def flatten_items(items, parent_idx="", level=1):
    """Flattens nested items for table display"""
    flat = []
    for idx, item in enumerate(items):
        item_id = f"{parent_idx}-{idx}" if parent_idx else str(idx)
        
        flat.append({
            "ID": item_id,
            "Level": level,
            "Icon": item.get("icon", ""),
            "Label": item.get("label_key", item.get("component", "")),
            "Type": item.get("type", ""),
            "Order": item.get("order", ""),
            "Hidden": "🚫" if item.get("hidden", False) else "✅",
            "Children": len(item.get("children", [])),
            "object": item
        })
        
        # Recursively add children
        if "children" in item:
            flat.extend(flatten_items(item["children"], item_id, level + 1))
    
    return flat

# ============ MAIN TABLE ============

config = load_config()

if config and "sidebar_structure" in config:
    items = config["sidebar_structure"]
    flat_items = flatten_items(items)
    
    # Create display dataframe
    df_display = pd.DataFrame([
        {
            "🔗 ID": f["ID"],
            "📍 Level": f["Level"],
            "🎨 Icon": f["Icon"],
            "📝 Label": f["Label"],
            "⚙️ Type": f["Type"],
            "#️⃣ Order": f["Order"],
            "👁️ Status": f["Hidden"],
            "👶 Sub-Items": f["Children"]
        }
        for f in flat_items
    ])
    
    # Display table
    st.subheader("📊 Sidebar Items")
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # ============ ACTIONS ============
    
    st.subheader("🛠️ Bearbeitung")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Item bearbeiten:**")
        selected_idx = st.selectbox(
            "Wähle ein Item:",
            range(len(flat_items)),
            format_func=lambda i: f"{flat_items[i]['Icon']} {flat_items[i]['Label']} (Order: {flat_items[i]['Order']})"
        )
        
        if selected_idx is not None:
            selected_item = flat_items[selected_idx]["object"]
            
            st.write("**Eigenschaften bearbeiten:**")
            
            # Icon
            new_icon = st.text_input("Icon:", value=selected_item.get("icon", ""))
            
            # Order
            new_order = st.number_input("Order:", value=float(selected_item.get("order", 0)), step=0.1)
            
            # Hidden toggle
            new_hidden = st.checkbox("Verstecken?", value=selected_item.get("hidden", False))
            
            # Type info
            st.caption(f"Type: {selected_item.get('type', 'unknown')}")
            
            if st.button("💾 Speichern", use_container_width=True, type="primary"):
                selected_item["icon"] = new_icon
                selected_item["order"] = new_order
                selected_item["hidden"] = new_hidden
                if save_config(config):
                    st.success("✅ Gespeichert! Bitte Browser neuladen für Sidebar-Aktualisierung")
                    # Clear config cache
                    if "sidebar_config_cache" in st.session_state:
                        del st.session_state.sidebar_config_cache
                    st.rerun()
    
    with col2:
        st.write("**Schnellaktionen:**")
        
        if st.button("🚫 Verstecken", use_container_width=True):
            flat_items[selected_idx]["object"]["hidden"] = True
            if save_config(config):
                st.success("✅ Versteckt! Bitte Browser neuladen")
                if "sidebar_config_cache" in st.session_state:
                    del st.session_state.sidebar_config_cache
                st.rerun()
        
        if st.button("✅ Anzeigen", use_container_width=True):
            flat_items[selected_idx]["object"]["hidden"] = False
            if save_config(config):
                st.success("✅ Angezeigt! Bitte Browser neuladen")
                if "sidebar_config_cache" in st.session_state:
                    del st.session_state.sidebar_config_cache
                st.rerun()
        
        if st.button("⬆️ Order +1", use_container_width=True):
            current_order = flat_items[selected_idx]["object"].get("order", 0)
            flat_items[selected_idx]["object"]["order"] = current_order + 1
            if save_config(config):
                st.success("✅ Regeordnet! Bitte Browser neuladen")
                if "sidebar_config_cache" in st.session_state:
                    del st.session_state.sidebar_config_cache
                st.rerun()
        
        if st.button("⬇️ Order -1", use_container_width=True):
            current_order = flat_items[selected_idx]["object"].get("order", 0)
            flat_items[selected_idx]["object"]["order"] = current_order - 1
            if save_config(config):
                st.success("✅ Regeordnet! Bitte Browser neuladen")
                if "sidebar_config_cache" in st.session_state:
                    del st.session_state.sidebar_config_cache
                st.rerun()
    
    with col3:
        st.write("**App-Kontrolle:**")
        
        if st.button("🔄 Config neu laden", use_container_width=True):
            st.rerun()
        
        st.divider()
        
        # Statistics
        total_items = len(flat_items)
        hidden_items = sum(1 for f in flat_items if f["Hidden"] == "🚫")
        visible_items = total_items - hidden_items
        
        st.metric("📊 Gesamt Items", total_items)
        st.metric("✅ Sichtbar", visible_items)
        st.metric("🚫 Versteckt", hidden_items)
    
    st.divider()
    
    # ============ ADVANCED: RAW YAML ============
    
    with st.expander("🔧 Erweitert - Raw YAML editieren"):
        st.warning("⚠️ Vorsicht: Hier kann man die YAML direkt editieren!")
        
        yaml_content = yaml.dump(config, default_flow_style=False, allow_unicode=True, sort_keys=False)
        edited_yaml = st.text_area(
            "Raw YAML:",
            value=yaml_content,
            height=400,
            key="yaml_editor"
        )
        
        if st.button("💾 Raw YAML Speichern", type="primary"):
            try:
                new_config = yaml.safe_load(edited_yaml)
                if "sidebar_structure" not in new_config:
                    st.error("❌ YAML muss 'sidebar_structure' enthalten!")
                else:
                    if save_config(new_config):
                        st.success("✅ Gespeichert! Bitte Browser neuladen für Sidebar-Aktualisierung")
                        if "sidebar_config_cache" in st.session_state:
                            del st.session_state.sidebar_config_cache
                        st.rerun()
            except yaml.YAMLError as e:
                st.error(f"❌ YAML Error: {e}")

# ============ FOOTER ============
st.divider()
st.caption("💡 Tipps: Wähle ein Item aus und nutze die Buttons oben um es zu bearbeiten. Order höher = weiter unten in der Sidebar.")
