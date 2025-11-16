"""
EquiPath - My Profile & College Matches

This page allows users to:
1. View and edit their profile (built via chat or manually)
2. Get personalized college recommendations
3. Visualize and compare matches
"""

import contextlib
import io
import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.shared_profile_state import (
    initialize_shared_profile,
    get_shared_profile,
    is_profile_complete,
    has_minimum_profile,
    build_profile_from_shared_state
)
from src.profile_editor import render_profile_editor
from src.enhanced_scoring import rank_colleges_for_user, get_personalized_weights
from src.enhanced_feature_engineering import build_enhanced_featured_college_df


def format_currency(value):
    """Format a value as currency, handling NaN gracefully."""
    if pd.isna(value) or value == 0:
        return "Data not available"
    return f"${value:,.0f}"


def format_percentage(value):
    """Format a value as percentage, handling NaN gracefully."""
    if pd.isna(value):
        return "Data not available"
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
        page_title="EquiPath - My Profile",
        page_icon="✏️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize shared profile state
    initialize_shared_profile()

    # Title
    st.title("✏️ My Profile & College Matches")
    st.markdown("""
    **Build or edit your profile, then get personalized college recommendations.**

    Your profile persists across all pages - edit here or build it through the AI Chat Assistant.
    """)

    st.divider()

    # Sidebar - Mode Selection
    st.sidebar.header("Navigation")

    if has_minimum_profile():
        if is_profile_complete():
            st.sidebar.success("✅ Full profile complete!")
        else:
            st.sidebar.info("ℹ️ Partial profile - complete more in chat for better matches!")

        mode = st.sidebar.radio(
            "What would you like to do?",
            ["View/Edit Profile", "Get Recommendations"],
            help="Edit your profile or see college matches"
        )
    else:
        st.sidebar.warning("⚠️ No profile yet")
        st.sidebar.markdown("**Get started:**")
        st.sidebar.markdown("1. Go to AI Chat Assistant to build your profile through conversation")
        st.sidebar.markdown("2. Or edit your profile manually below")
        mode = "View/Edit Profile"

    # Reset button
    if st.sidebar.button("🔄 Reset Profile"):
        from src.shared_profile_state import reset_shared_profile
        reset_shared_profile()
        st.rerun()

    # Main content
    if mode == "View/Edit Profile":
        st.subheader("📝 Your Profile")

        if not has_minimum_profile():
            st.info("👋 **Welcome!** Start by filling out your profile below, or go to the AI Chat Assistant for a conversational experience.")

        # Render the profile editor
        render_profile_editor()

        # Removed Get My College Matches button as requested

    else:  # Get Recommendations mode
        st.subheader("🎯 Your Personalized College Matches")

        # Number of results slider
        top_k = st.slider(
            "Number of recommendations",
            min_value=5,
            max_value=25,
            value=15,
            step=5
        )

        # Get recommendations button
        if st.button("🔍 Find My Matches", type="primary"):
            try:
                # Build profile from current state
                profile = get_shared_profile()

                if not profile:
                    st.error("Error building profile. Please check your profile data.")
                    return

                # Get recommendations
                with st.spinner("Finding your best matches..."):
                    colleges_df = build_enhanced_featured_college_df(
                        earnings_ceiling=profile.earnings_ceiling_match
                    )
                    recommendations = rank_colleges_for_user(colleges_df, profile, top_k=top_k)

                if len(recommendations) == 0:
                    st.error("❌ No colleges match your criteria. Try adjusting your filters in your profile.")
                else:
                    # Show personalized weights
                    weights = get_personalized_weights(profile)

                    st.markdown("### Your Personalized Scoring Weights")
                    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
                    with col1:
                        st.metric("Affordability", f"{weights['affordability']:.1%}")
                    with col2:
                        st.metric("ROI", f"{weights['roi']:.1%}")
                    with col3:
                        st.metric("Equity", f"{weights['equity']:.1%}")
                    with col4:
                        st.metric("Support", f"{weights['support']:.1%}")
                    with col5:
                        st.metric("Academic", f"{weights['academic_fit']:.1%}")
                    with col6:
                        st.metric("Environment", f"{weights['environment']:.1%}")
                    with col7:
                        st.metric("Access", f"{weights['access']:.1%}")

                    st.divider()

                    # Display recommendations
                    st.markdown(f"### 🎓 Top {len(recommendations)} Colleges For You")

                    for idx, (_, row) in enumerate(recommendations.iterrows(), 1):
                        inst_name = row.get('Institution Name', row.get('INSTNM', 'Unknown'))
                        composite = row.get('composite_score', 0)

                        with st.expander(f"**{idx}. {inst_name}** - Match Score: {composite:.3f}"):
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
                            st.markdown("**Your Personalized Fit Scores:**")
                            col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
                            with col1:
                                st.metric("Affordability", f"{safe_get(row, 'personalized_affordability', 0):.2f}")
                            with col2:
                                st.metric("ROI", f"{safe_get(row, 'roi_score', 0):.2f}")
                            with col3:
                                st.metric("Equity", f"{safe_get(row, 'personalized_equity', 0):.2f}")
                            with col4:
                                st.metric("Support", f"{safe_get(row, 'personalized_support', 0):.2f}")
                            with col5:
                                st.metric("Academic", f"{safe_get(row, 'personalized_academic_fit', 0):.2f}")
                            with col6:
                                st.metric("Environment", f"{safe_get(row, 'personalized_environment', 0):.2f}")
                            with col7:
                                st.metric("Access", f"{safe_get(row, 'personalized_access', 0):.2f}")

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

                                size_val = safe_get(row, 'Institution Size Category', None) or safe_get(row, 'Institution Size Category_CR', None)
                                if pd.notna(size_val):
                                    st.write(f"**Size:** {size_val}")

                                urban_val = safe_get(row, 'Degree of Urbanization', None)
                                if pd.notna(urban_val):
                                    st.write(f"**Setting:** {urban_val}")

                                enrollment = safe_get(row, 'Undergraduate Enrollment', None)
                                if enrollment and pd.notna(enrollment):
                                    st.write(f"**Enrollment:** {int(enrollment):,} students")

                            with col_b:
                                st.markdown("**🎓 Academic Success & Value**")

                                grad_rate = (safe_get(row, "Bachelor's Degree Graduation Rate Within 6 Years - Total", None) or
                                           safe_get(row, "Bachelor's Degree Graduation Rate Within 6 Years - Total_CR", None))
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

            except ValueError as e:
                st.error(f"❌ Error: {str(e)}")
            except Exception as e:
                st.error(f"❌ An unexpected error occurred: {str(e)}")
                st.exception(e)

    # Info box at bottom
    if mode == "View/Edit Profile":
        st.divider()
        st.info("""
        💡 **Tip:** Your profile is shared across all pages. You can:
        - Build it conversationally using the AI Chat Assistant
        - Edit it here anytime
        - Get updated recommendations instantly
        """)


# Handle session state flag for switching modes
if 'switch_to_recommendations' in st.session_state and st.session_state.switch_to_recommendations:
    st.session_state.switch_to_recommendations = False
    # Mode will already be set to "Get Recommendations" via the radio button


if __name__ == "__main__":
    main()
