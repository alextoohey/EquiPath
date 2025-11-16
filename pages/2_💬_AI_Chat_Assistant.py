"""Streamlit page integrating the enhanced AI chat assistant."""

import contextlib
import io

import streamlit as st

from src.enhanced_app_streamlit_chat import (
    ANTHROPIC_AVAILABLE,
    display_recommendations,
    enhanced_chat_collect_profile,
    get_anthropic_client,
    load_enhanced_data,
)
from src.enhanced_scoring import rank_colleges_for_user


def render_about_section():
    st.markdown(
        """
## About EquiPath Enhanced

EquiPath helps students find colleges that match their unique needs and circumstances.

### What Makes This Enhanced?

**Comprehensive Indices:**
- 📚 **Support Infrastructure** - Student support services
- 📖 **Academic Offerings** - Field-specific program strength
- 🏫 **Environment Fit** - Campus culture and setting
- Plus ROI, Affordability, Equity, and Access

**Voice Support:**
- 🎤 **Voice Input** - Answer questions by speaking
- 🔊 **Voice Output** - Hear responses read aloud
- Powered by ElevenLabs AI

**Equity-Focused:**
- Race/ethnicity used ONLY for relevant graduation rates and MSI identification
- Special support for first-gen, student-parents, and nontraditional students
- Excludes predatory for-profit institutions by default

**Fully Personalized:**
- Custom scoring weights based on YOUR priorities
- Selectivity bucketing (Reach/Target/Safety)
- Field-specific matching for your intended major
        """
    )


def main():
    st.set_page_config(
        page_title="EquiPath - Enhanced Chat",
        page_icon="🎓",
        layout="wide",
    )

    st.title("🎓 EquiPath: Enhanced AI Chat Assistant")
    st.markdown(
        "Build a comprehensive profile through conversation, explore equity-centered recommendations, and ask follow-up questions with voice support."
    )

    if not ANTHROPIC_AVAILABLE:
        st.error("⚠️ Anthropic package not installed. Install with: pip install anthropic")
        st.stop()

    st.sidebar.header("Navigation")
    mode = st.sidebar.radio(
        "Choose Mode:",
        ["Build Profile (Chat)", "Get Recommendations", "About"],
    )

    if st.sidebar.button("🔄 Reset / Start Over"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    client = get_anthropic_client()

    if mode == "Build Profile (Chat)":
        enhanced_chat_collect_profile()
        return

    if mode == "About":
        render_about_section()
        return

    if "user_profile" not in st.session_state or not st.session_state.get("profile_complete"):
        st.warning("Please complete your profile first using the chat interface!")
        return

    profile = st.session_state.user_profile

    with st.spinner("Finding your perfect college matches..."):
        with contextlib.redirect_stdout(io.StringIO()):
            colleges_df = load_enhanced_data(earnings_ceiling=profile.earnings_ceiling_match)
            recommendations = rank_colleges_for_user(colleges_df, profile, top_k=15)

    if len(recommendations) == 0:
        st.error("❌ No colleges match your criteria.")
        st.warning(
            """
**Try these adjustments:**
1. Increase your budget or set more flexible affordability priorities.
2. Remove geographic restrictions by broadening preferred regions or states.
3. Set environment preferences (size, urbanization, institution type) to “no preference.”
4. Include more selectivity levels such as reach, target, safety, and open admission schools.

**Your current profile:**
- Budget: ${:,.0f}
- In-state only: {}
- Preferred states: {}
- Institution type preference: {}
- Urbanization preference: {}
- Size preference: {}
- MSI preference: {}
            """.format(
                profile.annual_budget,
                profile.in_state_only,
                profile.preferred_states if profile.preferred_states else "None",
                profile.institution_type_pref,
                profile.urbanization_pref,
                profile.size_pref,
                profile.msi_preference,
            )
        )
        return

    display_recommendations(recommendations, profile, colleges_df, client)


if __name__ == "__main__":
    main()
