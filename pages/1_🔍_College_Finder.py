"""
Streamlit app for EquiPath - Equity-Centered College Advising Tool.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.user_profile import UserProfile
from src.scoring import rank_colleges_for_user, choose_weights
from src.cached_data import load_featured_data_with_clusters


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
    """Main Streamlit app function."""

    # Page configuration
    st.set_page_config(
        page_title="EquiPath - College Advising",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Title and description
    st.title("🎓 EquiPath: Equity-Centered College Advising")
    st.markdown("""
    **Find colleges that match your unique needs and support your success.**

    EquiPath uses a personalized Student Success & Equity Score that considers:
    - 💰 **Affordability** - Net price and financial accessibility
    - 📈 **ROI** - Earnings potential vs. debt burden
    - ⚖️ **Equity** - Graduation outcomes for students like you
    - 🚪 **Access** - Admission selectivity and fit
    """)

    st.divider()

    # Load data (uses shared cached module)
    with st.spinner("Loading college data..."):
        df, centroids, cluster_labels = load_featured_data_with_clusters()

    # Sidebar - User Profile Input
    st.sidebar.header("📋 Your Profile")
    st.sidebar.markdown("Tell us about yourself to get personalized recommendations:")

    # Race/Ethnicity
    race = st.sidebar.selectbox(
        "Race/Ethnicity",
        options=["BLACK", "HISPANIC", "WHITE", "ASIAN", "NATIVE", "PACIFIC", "OTHER"],
        help="We use this to show you graduation rates for students like you"
    )

    # Student-Parent Status
    is_parent = st.sidebar.checkbox(
        "I am a student-parent",
        help="We'll prioritize affordability including childcare costs"
    )

    # First-Generation Status
    first_gen = st.sidebar.checkbox(
        "I am a first-generation college student",
        help="We'll emphasize equity and support systems"
    )

    # Budget
    budget = st.sidebar.number_input(
        "Annual Budget for College ($)",
        min_value=0,
        max_value=100000,
        value=25000,
        step=1000,
        help="Maximum you can afford to pay per year"
    )

    # Income Bracket
    income_bracket = st.sidebar.selectbox(
        "Household Income Bracket",
        options=["LOW", "MEDIUM", "HIGH"],
        index=1,
        help="General income level"
    )

    # GPA
    gpa = st.sidebar.slider(
        "GPA (4.0 scale)",
        min_value=0.0,
        max_value=4.0,
        value=3.5,
        step=0.1,
        help="Your current grade point average"
    )

    st.sidebar.divider()
    st.sidebar.subheader("🎯 Preferences (Optional)")

    # Location Preferences
    in_state_only = st.sidebar.checkbox("In-state schools only")
    state = None
    if in_state_only:
        state = st.sidebar.text_input(
            "Your State (2-letter code)",
            value="CA",
            help="e.g., CA, NY, TX (enter 2 letters)"
        ).upper()
        # Validate length
        if len(state) > 2:
            state = state[:2]

    # Public Only
    public_only = st.sidebar.checkbox("Public institutions only")

    # School Size
    school_size_pref = st.sidebar.selectbox(
        "Preferred School Size",
        options=[None, "Small", "Medium", "Large"],
        format_func=lambda x: "Any" if x is None else x
    )

    # Number of results
    top_k = st.sidebar.slider(
        "Number of recommendations",
        min_value=5,
        max_value=25,
        value=10,
        step=5
    )

    # Find Matches Button
    st.sidebar.divider()
    find_matches = st.sidebar.button("🔍 Find My Matches", type="primary", use_container_width=True)

    # Main content area
    if find_matches:
        try:
            # Create user profile
            profile = UserProfile(
                race=race,
                is_parent=is_parent,
                first_gen=first_gen,
                budget=budget,
                income_bracket=income_bracket,
                gpa=gpa,
                in_state_only=in_state_only,
                state=state,
                public_only=public_only,
                school_size_pref=school_size_pref
            )

            # Get recommendations
            with st.spinner("Finding your best matches..."):
                recommendations = rank_colleges_for_user(df, profile, top_k=top_k)

            if len(recommendations) == 0:
                st.error("❌ No colleges match your criteria. Try adjusting your filters.")
            else:
                # Show personalized weights
                weights = choose_weights(profile)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("ROI Weight", f"{weights['alpha']:.1%}")
                with col2:
                    st.metric("Affordability Weight", f"{weights['beta']:.1%}")
                with col3:
                    st.metric("Equity Weight", f"{weights['gamma']:.1%}")
                with col4:
                    st.metric("Access Weight", f"{weights['delta']:.1%}")

                st.divider()

                # Display recommendations
                st.subheader(f"🎯 Your Top {len(recommendations)} College Matches")

                for idx, (_, row) in enumerate(recommendations.iterrows(), 1):
                    with st.expander(f"**{idx}. {row.get('Institution Name', 'Unknown')}** - Match Score: {row['user_score']:.3f}"):
                        col_a, col_b = st.columns(2)

                        with col_a:
                            st.markdown("**📍 Location & Type**")
                            state_val = row.get('State of Institution', 'N/A')
                            st.write(f"State: {state_val if pd.notna(state_val) else 'N/A'}")
                            sector_val = row.get('Sector of Institution', 'N/A')
                            st.write(f"Sector: {sector_val if pd.notna(sector_val) else 'N/A'}")
                            size_val = row.get('Institution Size Category', 'N/A')
                            st.write(f"Size: {size_val if pd.notna(size_val) else 'N/A'}")
                            if 'cluster_label' in row and pd.notna(row['cluster_label']):
                                st.write(f"Archetype: {row['cluster_label']}")

                            st.markdown("**💰 Financial**")
                            net_price = pd.to_numeric(row.get('Net Price', None), errors='coerce')
                            if pd.notna(net_price):
                                st.write(f"Net Price: ${net_price:,.0f}")
                            else:
                                st.write("Net Price: Data not available")

                            median_debt = pd.to_numeric(row.get('Median Debt of Completers', None), errors='coerce')
                            if pd.notna(median_debt):
                                st.write(f"Median Debt: ${median_debt:,.0f}")
                            else:
                                st.write("Median Debt: Data not available")

                        with col_b:
                            st.markdown("**📊 Your Personalized Scores**")
                            st.write(f"Overall Match: {row['user_score']:.3f}")
                            st.write(f"ROI Score: {row.get('roi_score', 0):.3f}")
                            if is_parent:
                                afford_score = row.get('afford_score_parent', 0)
                            else:
                                afford_score = row.get('afford_score_std', 0)
                            st.write(f"Affordability: {afford_score:.3f}")
                            st.write(f"Equity Parity: {row.get('equity_parity', 0):.3f}")

                            st.markdown("**🎓 Outcomes**")
                            earnings = pd.to_numeric(row.get('Median Earnings of Students Working and Not Enrolled 10 Years After Entry', None), errors='coerce')
                            if pd.notna(earnings):
                                st.write(f"Median Earnings (10yr): ${earnings:,.0f}")
                            else:
                                st.write("Median Earnings (10yr): Data not available")

                            admit_rate = pd.to_numeric(row.get('Total Percent of Applicants Admitted', None), errors='coerce')
                            if pd.notna(admit_rate):
                                st.write(f"Admission Rate: {admit_rate:.1f}%")
                            else:
                                st.write("Admission Rate: Data not available")

                # Visualization
                st.divider()
                st.subheader("📈 Visual Comparison of Your Matches")

                # Create scatter plot
                fig = px.scatter(
                    recommendations.head(10),
                    x='afford_score_std' if not is_parent else 'afford_score_parent',
                    y='equity_parity',
                    size='roi_score',
                    color='user_score',
                    hover_name='Institution Name',
                    hover_data={
                        'user_score': ':.3f',
                        'roi_score': ':.3f',
                        'Net Price': ':,.0f'
                    },
                    labels={
                        'afford_score_std': 'Affordability Score',
                        'afford_score_parent': 'Affordability Score (w/ Childcare)',
                        'equity_parity': 'Equity Parity',
                        'user_score': 'Match Score',
                        'roi_score': 'ROI Score'
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

    else:
        # Welcome screen
        st.info("👈 **Get started:** Fill out your profile in the sidebar and click 'Find My Matches'")

        # Show some statistics
        st.subheader("📊 Dataset Overview")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Institutions", f"{len(df):,}")
        with col2:
            states = df['State of Institution'].nunique() if 'State of Institution' in df.columns else 0
            st.metric("States Represented", f"{states}")
        with col3:
            st.metric("Cluster Archetypes", f"{df['cluster_label'].nunique()}")

        # Show cluster distribution
        if 'cluster_label' in df.columns:
            st.subheader("🏛️ Institution Archetypes")
            cluster_counts = df['cluster_label'].value_counts()

            fig = px.pie(
                values=cluster_counts.values,
                names=cluster_counts.index,
                title="Distribution of College Archetypes"
            )
            st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
