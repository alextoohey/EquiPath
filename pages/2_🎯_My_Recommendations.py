"""
EquiPath - My Recommendations Page

Comprehensive recommendations hub that works with shared profile
(created via My Profile editor OR Chat Assistant).

Features:
- Personalized college recommendations with detailed metrics
- AI-generated summaries for each college
- Visual comparison charts
- Q&A chatbot for questions about recommendations
- Direct link to view recommended schools on map
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.profile_state import (
    initialize_shared_profile,
    get_shared_profile,
    has_minimum_profile
)
from src.scoring import rank_colleges_for_user, get_personalized_weights
from src.features import build_college_features
from src.llm import build_recommendation_summary, generate_explanations
from src.config import get_anthropic_api_key, get_anthropic_model


def format_urbanization(value):
    """Convert urbanization code to readable label."""
    if pd.isna(value):
        return "N/A"

    try:
        value = int(value) if not pd.isna(value) else 0
    except (ValueError, TypeError):
        return str(value) if value else "N/A"

    # Based on IPEDS codes: 11-13 = City, 21-23 = Suburb, 31-33 = Town, 41-43 = Rural
    if value in [11, 12, 13]:
        return "City"
    elif value in [21, 22, 23]:
        return "Suburb"
    elif value in [31, 32, 33]:
        return "Town"
    elif value in [41, 42, 43]:
        return "Rural"
    else:
        return "N/A"


def format_size(value):
    """Convert size category code to readable label."""
    if pd.isna(value):
        return "N/A"

    try:
        value = int(value) if not pd.isna(value) else 0
    except (ValueError, TypeError):
        return str(value) if value else "N/A"

    # 1 = Small, 2 = Medium, 3-5 = Large
    if value == 1:
        return "Small"
    elif value == 2:
        return "Medium"
    elif value in [3, 4, 5]:
        return "Large"
    else:
        return "N/A"


def format_currency(value):
    """Format a value as currency, handling NaN gracefully."""
    if pd.isna(value) or value == 0:
        return "Data not available"
    return f"${value:,.0f}"


def format_percentage(value):
    """Format a value as percentage, handling NaN gracefully."""
    if pd.isna(value):
        return "Data not available"
    # If value is between 0 and 1, assume it's a decimal and convert to percentage
    if 0 <= value <= 1:
        return f"{value * 100:.1f}%"
    # Otherwise assume it's already a percentage
    return f"{value:.1f}%"


def safe_get(row, key, default="N/A"):
    """Safely get a value from a row, handling NaN."""
    value = row.get(key, default)
    if pd.isna(value):
        return default
    return value


def main():
    """Main page function."""

    # Page configuration
    st.set_page_config(
        page_title="EquiPath - My Recommendations",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize shared profile state
    initialize_shared_profile()

    # Title
    st.title("🎯 My College Recommendations")
    st.markdown("""
    **Get personalized college recommendations based on your profile.**

    Your profile persists across all pages - build it through the Chat Assistant or edit it in My Profile.
    """)

    st.divider()

    # Sidebar - Settings
    st.sidebar.header("Settings")

    # AI features toggle
    use_ai_summaries = st.sidebar.checkbox(
        "Include AI Summaries",
        value=True,
        help="Generate AI explanations for each recommendation"
    )

    # Check if profile exists
    if not has_minimum_profile():
        st.warning("⚠️ **No profile found!**")
        st.markdown("""
        To get personalized recommendations, you need to create a profile first.

        **Choose one:**
        - 📝 **My Profile** - Fill out your profile manually
        - 💬 **Chat Assistant** - Build your profile through conversation
        """)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Go to My Profile", use_container_width=True, type="primary"):
                st.switch_page("pages/1_✏️_My_Profile.py")
        with col2:
            if st.button("💬 Go to Chat Assistant", use_container_width=True):
                st.switch_page("pages/3_💬_Chat_Assistant.py")
        return

    # Main recommendation controls
    st.subheader("Find Your Matches")

    # Number of results slider
    top_k = st.slider(
        "Number of colleges to recommend",
        min_value=5,
        max_value=50,
        value=15,
        step=5,
        help="Choose how many college recommendations you want to see"
    )

    # Get recommendations button
    if st.button("🔍 Find My Matches", type="primary", use_container_width=True):
        try:
            # New recommendations invalidate cached AI summaries and any Q&A
            # conversation about the previous list
            keys_to_delete = [key for key in st.session_state.keys() if key.startswith('ai_summaries_')]
            for key in keys_to_delete:
                del st.session_state[key]
            st.session_state.qa_chat_history = []

            # Build profile from current state
            profile = get_shared_profile()

            if not profile:
                st.error("Error building profile. Please check your profile data.")
                return

            # Get recommendations
            with st.spinner("Finding your best matches..."):
                colleges_df = build_college_features(
                    earnings_ceiling=profile.earnings_ceiling_match
                )
                recommendations = rank_colleges_for_user(colleges_df, profile, top_k=top_k)

                # Store in session state so it persists across reruns
                st.session_state.current_recommendations = recommendations
                st.session_state.recommendation_profile = profile

        except ValueError as e:
            st.error(f"❌ Error: {str(e)}")
            return
        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {str(e)}")
            st.exception(e)
            return

    # Display stored recommendations if they exist
    if 'current_recommendations' in st.session_state and st.session_state.current_recommendations is not None:
        recommendations = st.session_state.current_recommendations
        profile = st.session_state.get('recommendation_profile')

        if len(recommendations) == 0:
            st.error("❌ No colleges match your criteria. Try adjusting your filters in your profile.")
            return

        # Show personalized weights
        if profile:
            weights = get_personalized_weights(profile)

            st.markdown("### 📊 Your Personalized Scoring Weights")
            col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
            with col1:
                st.metric("Affordability", f"{weights['affordability']:.1%}",
                          help="How much cost counts in your ranking. Lower this if budget isn't a constraint for you.")
            with col2:
                st.metric("ROI", f"{weights['roi']:.1%}",
                          help="How much earnings-vs-debt outcomes count in your ranking.")
            with col3:
                st.metric("Equity", f"{weights['equity']:.1%}",
                          help="How much graduation outcomes (for your demographic group, if provided) count in your ranking.")
            with col4:
                st.metric("Support", f"{weights['support']:.1%}",
                          help="How much student-support infrastructure counts in your ranking.")
            with col5:
                st.metric("Academic", f"{weights['academic_fit']:.1%}",
                          help="How much program strength in your intended major counts in your ranking.")
            with col6:
                st.metric("Environment", f"{weights['environment']:.1%}",
                          help="How much campus size/setting fit counts in your ranking.")
            with col7:
                st.metric("Access", f"{weights['access']:.1%}",
                          help="How much your admission odds count in your ranking.")

            with st.expander("ℹ️ How to read these scores"):
                st.markdown("""
                Each college gets seven **fit scores from 0 to 1** (higher = better fit for *you*),
                and your match score is the weighted average using the percentages above.

                - **Affordability** — how cheap the school is for a family like yours (net price and
                  affordability gap; childcare-adjusted if you're a student-parent). This is an
                  *absolute* cost score: raising your budget widens which schools pass the filter,
                  but doesn't make expensive schools score better. If cost matters less to you,
                  lower the **Affordability weight** in My Profile instead.
                - **ROI** — graduates' median earnings 10 years out vs. median debt.
                - **Equity** — the school's graduation rate for students like you (your group's rate
                  if you shared race/ethnicity, the overall rate otherwise), plus how equal outcomes
                  are across groups.
                - **Support** — student-faculty ratio, instructional spending, and experience
                  supporting low-income and nontraditional students.
                - **Academic** — strength in your intended major and research intensity.
                - **Environment** — how well size/setting match your preferences.
                - **Access** — your *odds of getting in*, based on the admission rate and your GPA.
                  Highly selective schools score near 0 here for everyone — a 4% admit rate is a
                  long shot even with a 4.0. That's honesty, not an error; it's also why Access
                  carries only ~5% weight by default.
                """)

        st.divider()

        # Display recommendations
        st.markdown(f"### 🎓 Top {len(recommendations)} Colleges For You")

        # Generate AI summaries if enabled
        ai_summaries = {}
        if use_ai_summaries and profile:
            # Cache key covers the whole ranked list, so any change in the
            # recommendations (not just the #1 school) regenerates summaries
            names = tuple(recommendations['Institution Name']) if len(recommendations) > 0 else ()
            cache_key = f"ai_summaries_{hash(names)}"

            if cache_key in st.session_state:
                ai_summaries = st.session_state[cache_key]
                st.info(f"ℹ️ Using cached AI summaries for {len(ai_summaries)} colleges")
            else:
                with st.spinner("Generating AI summaries for your matches..."):
                    try:
                        # Build summary for LLM - include ALL recommendations for context
                        summary = build_recommendation_summary(profile, recommendations, top_k=len(recommendations))

                        # Generate explanations
                        api_key = get_anthropic_api_key()
                        if api_key:
                            explanations = generate_explanations(summary, api_key=api_key)
                            if explanations and isinstance(explanations, dict) and 'recommendations' in explanations:
                                for rec in explanations['recommendations']:
                                    ai_summaries[rec['name']] = rec.get('why_good_fit', '')
                                if ai_summaries:
                                    # Cache the summaries
                                    st.session_state[cache_key] = ai_summaries
                                    st.success(f"✅ Generated AI summaries for {len(ai_summaries)} colleges")
                            else:
                                st.warning("⚠️ AI summaries are enabled but no explanations were generated. Check your API key.")
                        else:
                            st.warning("⚠️ AI summaries are enabled but no Anthropic API key found. Set ANTHROPIC_API_KEY in your .env file.")
                    except Exception as e:
                        st.warning(f"⚠️ Could not generate AI summaries: {str(e)}")
                        import traceback
                        with st.expander("Debug Info (click to expand)"):
                            st.code(traceback.format_exc())

        for idx, (_, row) in enumerate(recommendations.iterrows(), 1):
            inst_name = row.get('Institution Name', row.get('INSTNM', 'Unknown'))
            composite = row.get('composite_score', 0)

            with st.expander(f"**{idx}. {inst_name}** - Match Score: {composite:.3f}", expanded=(idx <= 3)):
                # AI Summary if available
                if inst_name in ai_summaries and ai_summaries[inst_name]:
                    st.info(f"**🤖 AI Summary:** {ai_summaries[inst_name]}")
                    st.divider()

                # Key metrics
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Match Score", f"{composite:.3f}")
                with col2:
                    net_price = safe_get(row, 'Net Price', None) or safe_get(row, 'Average Net Price', None)
                    st.metric("Net Price", format_currency(net_price))
                with col3:
                    earnings = safe_get(row, 'Median Earnings of Students Working and Not Enrolled 10 Years After Entry', None)
                    st.metric("10-Year Earnings", format_currency(earnings))
                with col4:
                    debt = safe_get(row, 'Median Debt of Completers', None) or safe_get(row, 'Median Debt of Completers_CR', None)
                    st.metric("Median Debt", format_currency(debt))

                # Fit scores
                st.markdown("**Your Personalized Fit Scores** (0-1, higher = better fit for you):")
                col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
                with col1:
                    st.metric("Affordability", f"{safe_get(row, 'personalized_affordability', 0):.2f}",
                              help="How affordable this school is for a family like yours (absolute cost, not relative to your budget).")
                with col2:
                    st.metric("ROI", f"{safe_get(row, 'roi_score', 0):.2f}",
                              help="Graduates' median earnings 10 years out vs. median debt.")
                with col3:
                    st.metric("Equity", f"{safe_get(row, 'personalized_equity', 0):.2f}",
                              help="Graduation rate for students like you, plus outcome parity across groups.")
                with col4:
                    st.metric("Support", f"{safe_get(row, 'personalized_support', 0):.2f}",
                              help="Student-support infrastructure: faculty ratio, instructional spend, low-income and nontraditional-student experience.")
                with col5:
                    st.metric("Academic", f"{safe_get(row, 'personalized_academic_fit', 0):.2f}",
                              help="Program strength in your intended major and research intensity.")
                with col6:
                    st.metric("Environment", f"{safe_get(row, 'personalized_environment', 0):.2f}",
                              help="How well the campus size and setting match your preferences.")
                with col7:
                    st.metric("Access", f"{safe_get(row, 'personalized_access', 0):.2f}",
                              help="Your odds of admission. Highly selective schools score near 0 for everyone — a 4% admit rate is a long shot even with a 4.0 GPA.")

                # Details
                st.markdown("### 📊 Additional Details")
                col_a, col_b = st.columns(2)

                with col_a:
                    st.markdown("**📍 Location & Environment**")

                    city = safe_get(row, 'City', None) or safe_get(row, 'City_CR', None) or safe_get(row, 'City_AG', 'N/A')
                    state = safe_get(row, 'State of Institution', None) or safe_get(row, 'STABBR', 'N/A')
                    st.write(f"**Location:** {city}, {state}")

                    control = safe_get(row, 'Control of Institution', None) or safe_get(row, 'Control of Institution_CR', None)
                    if pd.notna(control):
                        control_map = {1: 'Public', 2: 'Private nonprofit', 3: 'Private for-profit'}
                        if isinstance(control, (int, float)):
                            control = control_map.get(int(control), 'Unknown')
                        st.write(f"**Type:** {control}")

                    size_val = (safe_get(row, 'Institution Size Category', None) or
                               safe_get(row, 'Institution Size Category_CR', None) or
                               safe_get(row, 'size_category', None))
                    st.write(f"**Size:** {format_size(size_val)}")

                    urban_val = (safe_get(row, 'Degree of Urbanization', None) or
                                safe_get(row, 'urbanization', None))
                    st.write(f"**Setting:** {format_urbanization(urban_val)}")

                    enrollment = safe_get(row, 'Undergraduate Enrollment', None)
                    if enrollment and pd.notna(enrollment):
                        st.write(f"**Enrollment:** {int(enrollment):,} students")

                with col_b:
                    st.markdown("**🎓 Academic Success & Value**")

                    grad_rate = (
                        safe_get(row, "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total", None) or
                        safe_get(row, "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total_CR", None) or
                        safe_get(row, "Bachelor's Degree Graduation Rate Within 6 Years - Total", None) or
                        safe_get(row, "Bachelor's Degree Graduation Rate Within 6 Years - Total_CR", None)
                    )
                    st.write(f"**Graduation Rate:** {format_percentage(grad_rate)}")

                    selectivity = safe_get(row, 'selectivity_bucket', 'Unknown')
                    st.write(f"**Selectivity:** {selectivity}")

                    admit_rate = safe_get(row, 'Total Percent of Applicants Admitted', None)
                    st.write(f"**Admission Rate:** {format_percentage(admit_rate)}")

                    st.write(f"**10-Year Earnings:** {format_currency(earnings)}")
                    st.write(f"**Median Debt:** {format_currency(debt)}")

                    if earnings and debt and not pd.isna(earnings) and not pd.isna(debt) and debt > 0:
                        ratio = earnings / debt
                        st.write(f"**Earnings/Debt Ratio:** {ratio:.1f}x")

        # Visualization
        st.divider()
        st.subheader("📈 Visual Comparison of Your Matches")

        fig = px.scatter(
            recommendations.head(10),
            x='personalized_affordability',
            y='personalized_equity',
            size='roi_score',
            color='composite_score',
            hover_name='Institution Name' if 'Institution Name' in recommendations.columns else 'INSTNM',
            labels={
                'personalized_affordability': 'Affordability',
                'personalized_equity': 'Equity',
                'composite_score': 'Match Score',
                'roi_score': 'ROI'
            },
            title="Affordability vs. Equity (bubble size = ROI)",
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Add "View on Map" button
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🗺️ View Recommended Colleges on Map",
                       use_container_width=True,
                       type="primary",
                       key="view_recommendations_on_map"):
                # Map reads current_recommendations; just default it to the
                # recommended view
                st.session_state.show_only_recommended = True
                st.switch_page("pages/4_🗺️_School_Map.py")

        # Q&A Chatbot Section
        st.divider()
        st.subheader("💬 Ask Questions About Your Recommendations")

        st.markdown("""
        Ask me anything about your recommended colleges! For example:
        - "Which of these schools has the best ROI?"
        - "Tell me more about the schools in California"
        - "Which schools are best for STEM majors?"
        """)

        # Check for API key
        api_key = get_anthropic_api_key()
        if not api_key:
            st.warning("⚠️ Anthropic API key not found. Set ANTHROPIC_API_KEY in your .env file to use the Q&A feature.")
        else:
            # Initialize chat history
            if 'qa_chat_history' not in st.session_state:
                st.session_state.qa_chat_history = []

            # All messages render inside this container, which sits above
            # the chat input — including the live-streamed reply below
            chat_area = st.container()
            with chat_area:
                for msg in st.session_state.qa_chat_history:
                    with st.chat_message(msg["role"]):
                        st.write(msg["content"])

            if question := st.chat_input("Ask a question about your recommendations..."):
                st.session_state.qa_chat_history.append({"role": "user", "content": question})

                with chat_area:
                    with st.chat_message("user"):
                        st.write(question)

                    with st.chat_message("assistant"):
                        try:
                            import anthropic

                            client = anthropic.Anthropic(api_key=api_key)

                            # System prompt carries the student profile and
                            # per-school metrics; the chat history goes in
                            # messages so follow-ups keep their context
                            import json
                            summary = build_recommendation_summary(
                                profile, recommendations,
                                top_k=min(10, len(recommendations)))
                            context = (
                                "You are EquiPath's advisor, helping a student understand "
                                f"their {len(recommendations)} personalized college recommendations. "
                                "Below is their profile and the detailed metrics behind their "
                                "top matches (all scores are 0-1, higher = better fit). Use this "
                                "data to answer specifically; be warm, honest, and concise. "
                                "Write dollar amounts without the dollar sign (e.g., 2,895 "
                                "per year) — the chat display renders '$' as math notation.\n\n"
                                + json.dumps(summary, indent=2)
                            )

                            # Stream tokens into the page as they arrive
                            with client.messages.stream(
                                model=get_anthropic_model(),
                                max_tokens=1000,
                                system=context,
                                messages=[
                                    {"role": m["role"], "content": m["content"]}
                                    for m in st.session_state.qa_chat_history
                                ]
                            ) as stream:
                                answer = st.write_stream(stream.text_stream)

                        except Exception as e:
                            answer = f"Error generating response: {str(e)}"
                            st.error(answer)

                st.session_state.qa_chat_history.append({"role": "assistant", "content": answer})

    # Info box at bottom
    st.divider()
    st.info("""
    💡 **Tips:**
    - Adjust your profile in **My Profile** to refine recommendations
    - Use **Chat Assistant** to build your profile conversationally
    - Click **View on Map** to see where these schools are located
    - Enable **AI Summaries** in the sidebar for personalized explanations
    """)


if __name__ == "__main__":
    main()
