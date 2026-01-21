"""
Commit Metadata Manager - Access structured commit documentation in the app
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime


class CommitMetadataManager:
    """Manages access to structured commit metadata"""

    METADATA_FILE = 'scripts/commit_metadata.json'

    @classmethod
    def load(cls) -> Optional[Dict]:
        """Load commit metadata"""
        if not os.path.exists(cls.METADATA_FILE):
            return None

        try:
            with open(cls.METADATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    @classmethod
    def get_recent_changes(cls, limit: int = 10) -> List[Dict]:
        """Get recent commits with metadata"""
        metadata = cls.load()
        if not metadata:
            return []

        changes = metadata.get('changes', [])
        return changes[:limit]

    @classmethod
    def get_by_type(cls, change_type: str) -> List[Dict]:
        """Get all changes of a specific type"""
        metadata = cls.load()
        if not metadata:
            return []

        index = metadata.get('index_by_type', {})
        return index.get(change_type, [])

    @classmethod
    def get_by_feature_name(cls, name: str) -> Optional[Dict]:
        """Find a specific feature by name"""
        metadata = cls.load()
        if not metadata:
            return None

        for change in metadata.get('changes', []):
            if change.get('feature_name') == name:
                return change

        return None

    @classmethod
    def get_statistics(cls) -> Dict:
        """Get statistics about commits"""
        metadata = cls.load()
        if not metadata:
            return {
                'total': 0,
                'by_type': {},
                'last_update': None
            }

        index = metadata.get('index_by_type', {})
        stats = {
            'total': metadata.get('total_changes', 0),
            'by_type': {k: len(v) for k, v in index.items()},
            'last_update': metadata.get('generated_at'),
            'icon_map': {
                'feature': '✨',
                'bug': '🐛',
                'docs': '📝',
                'refactor': '♻️',
                'test': '🧪',
                'chore': '🔧',
                'performance': '⚡',
                'security': '🔒',
                'dependencies': '⬆️',
            }
        }
        return stats

    @classmethod
    def get_changelog_html(cls) -> str:
        """Generate HTML changelog from metadata"""
        metadata = cls.load()
        if not metadata:
            return "<p>No commit history available</p>"

        changes = metadata.get('changes', [])
        icon_map = {
            'feature': '✨',
            'bug': '🐛',
            'docs': '📝',
            'refactor': '♻️',
            'test': '🧪',
            'chore': '🔧',
            'performance': '⚡',
            'security': '🔒',
        }

        html = '<div class="changelog">'
        for change in changes[:50]:  # Last 50
            icon = icon_map.get(change.get('icon', 'other'), '📝')
            feature = change.get('feature_name', 'Unnamed')
            details = change.get('feature_details', '')
            timestamp = change.get('timestamp', '')

            html += f"""
            <div class="changelog-entry">
                <span class="icon">{icon}</span>
                <div class="content">
                    <h4>{feature}</h4>
                    <p>{details}</p>
                    <small>{timestamp}</small>
                </div>
            </div>
            """

        html += '</div>'
        return html

    @classmethod
    def print_summary(cls):
        """Print summary to console"""
        stats = cls.get_statistics()

        print("\n" + "=" * 60)
        print("📋 COMMIT HISTORY SUMMARY")
        print("=" * 60)
        print(f"\n📊 Total commits tracked: {stats['total']}")
        print(f"🕐 Last updated: {stats['last_update']}")

        print("\n📈 Breakdown by type:")
        for ctype, count in stats['by_type'].items():
            icon = stats['icon_map'].get(ctype, '📝')
            print(f"  {icon} {ctype.capitalize()}: {count}")

        print("\n🚀 Recent changes (last 5):")
        recent = cls.get_recent_changes(5)
        for change in recent:
            icon = stats['icon_map'].get(change.get('icon'), '📝')
            feature = change.get('feature_name', 'Unnamed')
            print(f"  {icon} {feature}")

        print("\n" + "=" * 60)


# Streamlit helper functions
def display_commit_history_streamlit(st_module):
    """Display commit history in Streamlit app"""
    import streamlit as st

    st.subheader("📋 Commit History")

    # Statistics
    stats = CommitMetadataManager.get_statistics()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Commits", stats['total'])
    with col2:
        st.metric("Features", stats['by_type'].get('feature', 0))
    with col3:
        st.metric("Bug Fixes", stats['by_type'].get('bug', 0))

    # Recent changes
    st.markdown("#### Recent Changes")
    recent = CommitMetadataManager.get_recent_changes(10)

    if recent:
        for change in recent:
            icon_map = {
                'feature': '✨',
                'bug': '🐛',
                'docs': '📝',
                'refactor': '♻️',
            }
            icon = icon_map.get(change.get('icon'), '📝')
            feature = change.get('feature_name', 'Unnamed')
            details = change.get('feature_details', '')
            ts = change.get('timestamp', '')[:10]  # Date only

            st.markdown(f"""
            **{icon} {feature}**  
            {details}  
            *{ts}*
            """)
    else:
        st.info("No commit history available yet")

    # Breakdown
    st.markdown("#### Breakdown by Type")
    breakdown = stats['by_type']
    if breakdown:
        st.bar_chart(breakdown)


# Command line usage
if __name__ == '__main__':
    CommitMetadataManager.print_summary()
