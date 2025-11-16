"""
EquiPath - AI Chat Assistant

Build your profile through natural conversation with AI assistance.
Your profile is automatically saved and shared across all pages.
"""

import streamlit as st

from src.enhanced_app_streamlit_chat import (
    ANTHROPIC_AVAILABLE,
    enhanced_chat_collect_profile,
)
from src.shared_profile_state import (
    initialize_shared_profile,
    is_profile_complete,
    has_minimum_profile
)


def main():
    """Main page function."""

    st.set_page_config(
        page_title="EquiPath - AI Chat Assistant",
        page_icon="🤖",
        layout="wide",
    )

    # Initialize shared profile state
    initialize_shared_profile()

    # Title
    st.title("🤖 AI Chat Assistant")
    st.markdown("""
    **Build your profile through natural conversation with AI.**

    Your profile persists across all pages - build it here, then get recommendations
    on the **My Recommendations** page.
    """)

    st.divider()

    if not ANTHROPIC_AVAILABLE:
        st.error("⚠️ Anthropic package not installed. Install with: pip install anthropic")
        st.stop()

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
        st.sidebar.markdown("Start chatting below to build your profile!")

    # Reset button
    st.sidebar.divider()
    if st.sidebar.button("🔄 Reset Chat & Start Over"):
        from src.shared_profile_state import reset_shared_profile
        reset_shared_profile()
        # Clear chat-specific session state
        for key in list(st.session_state.keys()):
            if key not in ['shared_profile', 'shared_profile_data', 'profile_complete']:
                del st.session_state[key]
        st.rerun()

    # Main content - Chat interface
    st.subheader("💬 Build Your Profile")

    # Show welcome and tips only at the start
    if not has_minimum_profile():
        st.info("""
        👋 **Welcome!** Start chatting below to build your profile.

        I'll ask you questions about:
        - Your academic background (GPA, test scores, intended major)
        - Your financial situation (budget, family income)
        - Your preferences (location, school size, campus environment)
        - Your priorities (what matters most to you in a college)
        """)

        with st.expander("💡 Tips & Features", expanded=False):
            st.markdown("""
            **Tips:**
            - Your profile is automatically saved and shared across all pages
            - You can edit your profile manually on the **My Profile** page
            - Once you complete your profile, you can get personalized recommendations

            **Features:**
            - 🎤 **Voice Input** - Click the microphone to speak your answers
            - 🔊 **Voice Output** - Hear responses read aloud (if ElevenLabs is configured)
            - 💾 **Auto-save** - Your answers are saved automatically as you chat
            """)

    # Render the chat interface
    enhanced_chat_collect_profile()

    # Get Recommendations button (appears only after profile is complete)
    if is_profile_complete():
        st.divider()
        st.success("🎉 **Profile Complete!** You're ready to get personalized college recommendations.")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🎯 Get My Recommendations",
                       use_container_width=True,
                       type="primary"):
                st.switch_page("pages/2_🎯_My_Recommendations.py")


if __name__ == "__main__":
    main()
