"""
EquiPath - My Profile

This page allows users to:
1. View and edit their profile (built via chat or manually)
2. Profile is shared across all pages and can be used for recommendations
"""

import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.shared_profile_state import (
    initialize_shared_profile,
    is_profile_complete,
    has_minimum_profile
)
from src.profile_editor import render_profile_editor


def main():
    """Main page function."""

    # Page configuration
    st.set_page_config(
        page_title="EquiPath - My Profile",
        page_icon="✏️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize shared profile state
    initialize_shared_profile()

    # Title
    st.title("✏️ My Profile")
    st.markdown("""
    **Build and edit your profile for personalized college recommendations.**

    Your profile persists across all pages - edit here or build it through the AI Chat Assistant,
    then get recommendations on the **My Recommendations** page.
    """)

    st.divider()

    # Sidebar - Profile Status
    st.sidebar.header("Profile Status")

    if has_minimum_profile():
        if is_profile_complete():
            st.sidebar.success("✅ Full profile complete!")
        else:
            st.sidebar.info("ℹ️ Partial profile - complete more for better matches!")
    else:
        st.sidebar.warning("⚠️ No profile yet")
        st.sidebar.markdown("**Get started:**")
        st.sidebar.markdown("1. Fill out the form below")
        st.sidebar.markdown("2. Or use the AI Chat Assistant")

    # Reset button
    st.sidebar.divider()
    if st.sidebar.button("🔄 Reset Profile"):
        from src.shared_profile_state import reset_shared_profile
        reset_shared_profile()
        st.rerun()

    # Main content
    st.subheader("📝 Your Profile")

    if not has_minimum_profile():
        st.info("👋 **Welcome!** Start by filling out your profile below, or go to the AI Chat Assistant for a conversational experience.")

    # Render the profile editor
    render_profile_editor()

    # Get Recommendations button
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎯 Get My Recommendations",
                   use_container_width=True,
                   type="primary",
                   disabled=not has_minimum_profile()):
            st.switch_page("pages/2_🎯_My_Recommendations.py")

    # Info box at bottom
    st.divider()
    st.info("""
    💡 **Next Steps:**
    - Your profile is automatically saved and shared across all pages
    - Build it here or conversationally using the **AI Chat Assistant**
    - Click **Get My Recommendations** to see personalized college matches
    - Visit **School Map** to explore colleges geographically
    """)


if __name__ == "__main__":
    main()
