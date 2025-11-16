"""
Enhanced Streamlit app for EquiPath with LLM-powered chat interface.
Allows students to create profiles conversationally and get detailed AI explanations.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.feature_engineering import build_featured_college_df
from src.clustering import add_clusters
from src.user_profile import UserProfile
from src.scoring import rank_colleges_for_user, choose_weights
from src.llm_integration import parse_user_text_to_profile, generate_explanations, build_recommendation_summary
from src.config import get_anthropic_api_key  # Load API key from .env
from src.data_loading import load_merged_data

# Import Anthropic
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


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


@st.cache_data
def load_data():
    """Load and cache the featured college data with clusters."""
    print("Loading data for Streamlit app...")
    df = build_featured_college_df()
    df_clustered, centroids, labels = add_clusters(df, n_clusters=5)
    return df_clustered, centroids, labels


@st.cache_data
def load_pathway_data():
    """Load merged data for pathway analysis (includes transfer rates)."""
    return load_merged_data()


def analyze_pathway_options(profile, df_merged):
    """
    Analyze community college transfer pathway vs direct 4-year enrollment.

    Args:
        profile: UserProfile with student information
        df_merged: DataFrame with merged college and affordability data

    Returns:
        dict with pathway analysis results
    """
    # Filter by state if specified
    if profile.state and profile.in_state_only:
        df_filtered = df_merged[df_merged['State of Institution'] == profile.state].copy()
    else:
        df_filtered = df_merged.copy()

    # Filter by zip code radius BEFORE income filtering
    if profile.zip_code and profile.radius_miles:
        from src.distance_utils import filter_by_radius
        print(f"  [Pathway] Applying radius filter: {profile.radius_miles} miles from zip {profile.zip_code}")
        df_filtered = filter_by_radius(df_filtered, profile.zip_code, profile.radius_miles)
        print(f"  [Pathway] After radius filter: {len(df_filtered)} institutions")
    elif profile.zip_code:
        from src.distance_utils import add_distance_column
        df_filtered = add_distance_column(df_filtered, profile.zip_code)

    # Filter by income bracket if available
    # Note: The affordability gap data is mostly for low-income ($30k ceiling)
    # For pathway analysis, we'll use the most complete dataset (30k) since
    # it has the most community colleges and public universities
    if 'Student Family Earnings Ceiling' in df_filtered.columns:
        # Try to use 30k data (most complete) first
        df_income = df_filtered[df_filtered['Student Family Earnings Ceiling'] == 30000].copy()

        # If still not enough community colleges, don't filter by income
        cc_test = df_income[df_income['Sector Name'] == 'Public, 2-year']
        if len(cc_test) < 10:
            df_income = df_filtered
    else:
        df_income = df_filtered

    # Separate by sector (use 'Sector Name' column which has the text values)
    cc = df_income[df_income['Sector Name'] == 'Public, 2-year'].copy()
    pub = df_income[df_income['Sector Name'] == 'Public, 4-year or above'].copy()
    priv = df_income[df_income['Sector Name'] == 'Private not-for-profit, 4-year or above'].copy()

    if len(cc) == 0 or len(pub) == 0:
        return None

    # Identify high-transfer community colleges
    HIGH_TRANSFER_THRESHOLD = 9
    cc_high_transfer = cc[
        (cc['Transfer Out Rate'].notna()) &
        (cc['Transfer Out Rate'] >= HIGH_TRANSFER_THRESHOLD)
    ].copy()

    # Use high-transfer CCs if available
    if len(cc_high_transfer) >= 5:
        cc_for_path = cc_high_transfer
        using_transfer_filter = True
    else:
        cc_for_path = cc
        using_transfer_filter = False

    # Calculate pathway costs and outcomes
    cc_price = cc_for_path['Net Price'].median()
    cc_debt = cc['Median Debt of Completers'].median()
    cc_earnings = cc['Median Earnings of Students Working and Not Enrolled 10 Years After Entry'].median()

    pub_price = pub['Net Price'].median()
    pub_debt = pub['Median Debt of Completers'].median()
    pub_earnings = pub['Median Earnings of Students Working and Not Enrolled 10 Years After Entry'].median()

    priv_price = priv['Net Price'].median() if len(priv) > 0 else 0
    priv_debt = priv['Median Debt of Completers'].median() if len(priv) > 0 else 0
    priv_earnings = priv['Median Earnings of Students Working and Not Enrolled 10 Years After Entry'].median() if len(priv) > 0 else 0

    # Path A: Community College (2yr) → Public University (2yr)
    path_a_cost = (cc_price * 2) + (pub_price * 2)
    path_a_investment = path_a_cost + pub_debt
    path_a_value = (pub_earnings * 10) - path_a_investment
    path_a_break_even = path_a_investment / pub_earnings if pub_earnings > 0 else 0

    # Path B: Direct Public University (4yr)
    path_b_cost = pub_price * 4
    path_b_investment = path_b_cost + pub_debt
    path_b_value = (pub_earnings * 10) - path_b_investment
    path_b_break_even = path_b_investment / pub_earnings if pub_earnings > 0 else 0

    # Path C: Direct Private University (4yr)
    path_c_cost = priv_price * 4
    path_c_investment = path_c_cost + priv_debt
    path_c_value = (priv_earnings * 10) - path_c_investment
    path_c_break_even = path_c_investment / priv_earnings if priv_earnings > 0 else 0

    # Get top schools (use Institution Name_CR from College Results dataset)
    top_cc = cc_for_path.nsmallest(5, 'Net Price')[['Institution Name_CR', 'City', 'Net Price', 'Transfer Out Rate']].copy()
    top_pub = pub.nsmallest(5, 'Net Price')[['Institution Name_CR', 'City', 'Net Price']].copy()

    # Get best transfer community colleges
    if len(cc) > 0 and cc['Transfer Out Rate'].notna().sum() > 0:
        cc_with_transfer = cc[cc['Transfer Out Rate'].notna()].copy()
        best_transfer_cc = cc_with_transfer.nlargest(min(10, len(cc_with_transfer)), 'Transfer Out Rate')[[
            'Institution Name_CR', 'City', 'Transfer Out Rate', 'Net Price'
        ]].copy()
    else:
        best_transfer_cc = None

    return {
        'path_a': {
            'cost': path_a_cost,
            'debt': pub_debt,
            'investment': path_a_investment,
            'value': path_a_value,
            'earnings': pub_earnings,
            'break_even': path_a_break_even
        },
        'path_b': {
            'cost': path_b_cost,
            'debt': pub_debt,
            'investment': path_b_investment,
            'value': path_b_value,
            'earnings': pub_earnings,
            'break_even': path_b_break_even
        },
        'path_c': {
            'cost': path_c_cost,
            'debt': priv_debt,
            'investment': path_c_investment,
            'value': path_c_value,
            'earnings': priv_earnings,
            'break_even': path_c_break_even
        },
        'using_transfer_filter': using_transfer_filter,
        'high_transfer_count': len(cc_for_path) if using_transfer_filter else 0,
        'avg_transfer_rate': cc_for_path['Transfer Out Rate'].mean() if using_transfer_filter else 0,
        'top_cc': top_cc,
        'top_pub': top_pub,
        'best_transfer_cc': best_transfer_cc,
        'cc_count': len(cc),
        'pub_count': len(pub),
        'priv_count': len(priv),
        'savings': path_b_cost - path_a_cost
    }


def display_pathway_comparison(pathway_results):
    """Display pathway comparison results with visualizations."""
    if not pathway_results:
        st.warning("Not enough data available for pathway comparison. Try expanding your search area.")
        return

    st.header("🛤️ Your Pathway Options")

    # Display institution counts
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Community Colleges", pathway_results['cc_count'])
    with col2:
        st.metric("Public Universities", pathway_results['pub_count'])
    with col3:
        st.metric("Private Universities", pathway_results['priv_count'])

    st.info("""
    📊 **About This Data:**
    - **Net prices** are specific to your income bracket and include financial aid
    - **Earnings** represent graduates 10 years after enrollment
    - **Path A earnings** use public university data since transfer students graduate with the same degree
    - All dollar amounts are medians (middle values)
    """)

    # Display pathways in tabs
    tab1, tab2, tab3 = st.tabs(["Path A: CC → Public", "Path B: Direct Public", "Path C: Direct Private"])

    with tab1:
        st.subheader("🎓 Community College (2yr) → Public University (2yr)")

        if pathway_results['using_transfer_filter']:
            st.success(f"""
            ✅ **Using High-Transfer Community Colleges**
            - {pathway_results['high_transfer_count']} colleges with ≥9% transfer rate
            - Average transfer rate: {pathway_results['avg_transfer_rate']:.1f}%
            - These CCs have strong track records of preparing students for 4-year universities
            """)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total 4-Year Cost", f"${pathway_results['path_a']['cost']:,.0f}")
        with col2:
            st.metric("Expected Debt", f"${pathway_results['path_a']['debt']:,.0f}")
        with col3:
            st.metric("Annual Earnings (10yr)", f"${pathway_results['path_a']['earnings']:,.0f}")
        with col4:
            st.metric("Net 10-Year Value", f"${pathway_results['path_a']['value']:,.0f}")

        st.info(f"⏱️ **Break Even Time:** {pathway_results['path_a']['break_even']:.1f} years")

    with tab2:
        st.subheader("🎓 Public University (4 years)")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total 4-Year Cost", f"${pathway_results['path_b']['cost']:,.0f}")
        with col2:
            st.metric("Expected Debt", f"${pathway_results['path_b']['debt']:,.0f}")
        with col3:
            st.metric("Annual Earnings (10yr)", f"${pathway_results['path_b']['earnings']:,.0f}")
        with col4:
            st.metric("Net 10-Year Value", f"${pathway_results['path_b']['value']:,.0f}")

        st.info(f"⏱️ **Break Even Time:** {pathway_results['path_b']['break_even']:.1f} years")

    with tab3:
        if pathway_results['priv_count'] > 0:
            st.subheader("🎓 Private University (4 years)")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total 4-Year Cost", f"${pathway_results['path_c']['cost']:,.0f}")
            with col2:
                st.metric("Expected Debt", f"${pathway_results['path_c']['debt']:,.0f}")
            with col3:
                st.metric("Annual Earnings (10yr)", f"${pathway_results['path_c']['earnings']:,.0f}")
            with col4:
                st.metric("Net 10-Year Value", f"${pathway_results['path_c']['value']:,.0f}")

            st.info(f"⏱️ **Break Even Time:** {pathway_results['path_c']['break_even']:.1f} years")
        else:
            st.warning("No private universities available in this area.")

    # Comparison chart
    st.subheader("📊 Side-by-Side Comparison")

    comparison_data = {
        'Pathway': ['A: CC→Public', 'B: Direct Public', 'C: Direct Private'],
        'Total Cost': [
            pathway_results['path_a']['cost'],
            pathway_results['path_b']['cost'],
            pathway_results['path_c']['cost']
        ],
        'Expected Debt': [
            pathway_results['path_a']['debt'],
            pathway_results['path_b']['debt'],
            pathway_results['path_c']['debt']
        ],
        '10-Year Net Value': [
            pathway_results['path_a']['value'],
            pathway_results['path_b']['value'],
            pathway_results['path_c']['value']
        ]
    }

    comparison_df = pd.DataFrame(comparison_data)

    # Display as table
    st.dataframe(
        comparison_df.style.format({
            'Total Cost': '${:,.0f}',
            'Expected Debt': '${:,.0f}',
            '10-Year Net Value': '${:,.0f}'
        }),
        use_container_width=True
    )

    # Bar chart comparison
    fig = go.Figure(data=[
        go.Bar(name='Total 4-Year Cost', x=comparison_df['Pathway'], y=comparison_df['Total Cost']),
        go.Bar(name='Expected Debt', x=comparison_df['Pathway'], y=comparison_df['Expected Debt'])
    ])

    fig.update_layout(
        title='Cost and Debt Comparison',
        barmode='group',
        yaxis_title='Amount ($)',
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

    # Recommendation
    st.subheader("💡 Our Recommendation")
    best_idx = comparison_df['10-Year Net Value'].idxmax()
    best_path = comparison_df.loc[best_idx]

    st.success(f"""
    **✅ We recommend: {best_path['Pathway']}**

    - Best 10-year net value: **${best_path['10-Year Net Value']:,.0f}**
    - Path A saves you **${pathway_results['savings']:,.0f}** compared to going straight to a 4-year university
    - You'll break even in just **{pathway_results['path_a']['break_even']:.1f} years**!
    """)

    # Top schools
    st.subheader("🏫 Top Affordable Schools")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Community Colleges**")
        if not pathway_results['top_cc'].empty:
            top_cc_display = pathway_results['top_cc'].copy()
            top_cc_display.columns = ['Institution', 'City', 'Net Price/Year', 'Transfer Rate']
            st.dataframe(
                top_cc_display.style.format({
                    'Net Price/Year': '${:,.0f}',
                    'Transfer Rate': '{:.0f}%'
                }),
                hide_index=True,
                use_container_width=True
            )

    with col2:
        st.markdown("**Public Universities**")
        if not pathway_results['top_pub'].empty:
            top_pub_display = pathway_results['top_pub'].copy()
            top_pub_display.columns = ['Institution', 'City', 'Net Price/Year']
            st.dataframe(
                top_pub_display.style.format({
                    'Net Price/Year': '${:,.0f}'
                }),
                hide_index=True,
                use_container_width=True
            )

    # Best Community Colleges for Transfer
    if pathway_results['best_transfer_cc'] is not None and not pathway_results['best_transfer_cc'].empty:
        st.subheader("🔄 Best Community Colleges for Transferring")
        st.markdown("""
        These community colleges have the **highest transfer-out rates**, meaning more students
        successfully transfer to 4-year universities. Perfect for Path A!
        """)

        best_transfer_display = pathway_results['best_transfer_cc'].copy()
        best_transfer_display.columns = ['Institution', 'City', 'Transfer Rate', 'Net Price/Year']
        st.dataframe(
            best_transfer_display.style.format({
                'Transfer Rate': '{:.0f}%',
                'Net Price/Year': '${:,.0f}'
            }),
            hide_index=True,
            use_container_width=True
        )


def get_anthropic_client():
    """Get Anthropic client if API key is available."""
    # Get API key from .env (loaded by config module)
    api_key = get_anthropic_api_key()

    if api_key and ANTHROPIC_AVAILABLE:
        return Anthropic(api_key=api_key)
    return None


def chat_collect_profile():
    """Interactive chat interface to collect user profile."""

    st.subheader("💬 Chat with EquiPath")
    st.markdown("Tell me about yourself and I'll help you find the perfect colleges!")

    # Initialize session state for chat
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
        st.session_state.profile_data = {}
        st.session_state.chat_step = 0

    # Chat questions flow
    questions = [
        "Hi! I'm here to help you find colleges. What's your name?",
        "Nice to meet you! How would you describe your racial/ethnic background? (e.g., Black, Hispanic, White, Asian, Native American, Pacific Islander, or Other)",
        "Are you a student-parent (do you have children)?",
        "Are you a first-generation college student (neither parent completed a 4-year degree)?",
        "What's your approximate annual budget for college? (Just a number in dollars, like 20000)",
        "What's your household income level? (LOW, MEDIUM, or HIGH)",
        "What's your current GPA on a 4.0 scale?",
        "Which state are you from? (Enter 2-letter state code like CA, NY, TX, etc.)",
        "Do you want to only consider colleges in your home state? (yes/no)",
        "Do you prefer public schools only? (yes/no)",
        "What school size do you prefer? (Small, Medium, Large, or 'any' if no preference)",
        "Do you want to search for colleges near you? Enter your 5-digit zip code, or type 'skip' to search all locations:",
        "How many miles away are you willing to travel for college? (e.g., 50, 100, 200, or 'any' for no limit)"
    ]

    # Display chat history
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Show current question
    if st.session_state.chat_step < len(questions):
        # Check if we need to show the next question
        # Count assistant messages - should equal chat_step + 1
        assistant_msg_count = sum(1 for msg in st.session_state.chat_messages if msg["role"] == "assistant")

        if assistant_msg_count <= st.session_state.chat_step:
            with st.chat_message("assistant"):
                st.write(questions[st.session_state.chat_step])
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": questions[st.session_state.chat_step]
                })

        # User input
        user_input = st.chat_input("Your answer...")

        if user_input:
            # Add user message
            st.session_state.chat_messages.append({
                "role": "user",
                "content": user_input
            })

            # Process answer
            step = st.session_state.chat_step

            if step == 0:  # Name
                st.session_state.profile_data['name'] = user_input
            elif step == 1:  # Race
                race_map = {
                    'black': 'BLACK', 'african': 'BLACK',
                    'hispanic': 'HISPANIC', 'latino': 'HISPANIC', 'latina': 'HISPANIC',
                    'white': 'WHITE', 'caucasian': 'WHITE',
                    'asian': 'ASIAN',
                    'native': 'NATIVE', 'indigenous': 'NATIVE',
                    'pacific': 'PACIFIC', 'islander': 'PACIFIC'
                }
                race = 'OTHER'
                for key, val in race_map.items():
                    if key in user_input.lower():
                        race = val
                        break
                st.session_state.profile_data['race'] = race
            elif step == 2:  # Student-parent
                st.session_state.profile_data['is_parent'] = 'yes' in user_input.lower() or 'have' in user_input.lower()
            elif step == 3:  # First-gen
                st.session_state.profile_data['first_gen'] = 'yes' in user_input.lower() or 'am' in user_input.lower()
            elif step == 4:  # Budget
                try:
                    budget = float(''.join(filter(str.isdigit, user_input)))
                    st.session_state.profile_data['budget'] = budget
                except:
                    st.session_state.profile_data['budget'] = 25000
            elif step == 5:  # Income
                income = 'MEDIUM'
                if 'low' in user_input.lower():
                    income = 'LOW'
                elif 'high' in user_input.lower():
                    income = 'HIGH'
                st.session_state.profile_data['income_bracket'] = income
            elif step == 6:  # GPA
                try:
                    gpa = float(user_input.replace(',', '.'))
                    st.session_state.profile_data['gpa'] = min(4.0, max(0.0, gpa))
                except:
                    st.session_state.profile_data['gpa'] = 3.0
            elif step == 7:  # State
                # Extract state code (2 letters)
                state_code = ''.join(filter(str.isalpha, user_input.upper()))[:2]
                if len(state_code) == 2:
                    st.session_state.profile_data['state'] = state_code
                else:
                    st.session_state.profile_data['state'] = None
            elif step == 8:  # In-state only
                st.session_state.profile_data['in_state_only'] = 'yes' in user_input.lower() or 'y' == user_input.lower().strip()
            elif step == 9:  # Public only
                st.session_state.profile_data['public_only'] = 'yes' in user_input.lower() or 'y' == user_input.lower().strip()
            elif step == 10:  # School size
                size_input = user_input.lower()
                size = None
                if 'small' in size_input:
                    size = 'Small'
                elif 'medium' in size_input:
                    size = 'Medium'
                elif 'large' in size_input:
                    size = 'Large'
                st.session_state.profile_data['school_size_pref'] = size
            elif step == 11:  # Zip code
                zip_input = user_input.strip().lower()
                if zip_input == 'skip' or zip_input == '':
                    st.session_state.profile_data['zip_code'] = None
                else:
                    # Extract digits only
                    zip_digits = ''.join(filter(str.isdigit, user_input))
                    if len(zip_digits) == 5:
                        st.session_state.profile_data['zip_code'] = zip_digits
                    else:
                        st.session_state.profile_data['zip_code'] = None
            elif step == 12:  # Radius
                # Only ask radius if zip code was provided
                if st.session_state.profile_data.get('zip_code'):
                    radius_input = user_input.strip().lower()
                    if radius_input == 'any' or radius_input == 'skip' or radius_input == '':
                        st.session_state.profile_data['radius_miles'] = None
                    else:
                        try:
                            radius = int(''.join(filter(str.isdigit, user_input)))
                            st.session_state.profile_data['radius_miles'] = radius if radius > 0 else None
                        except:
                            st.session_state.profile_data['radius_miles'] = None
                else:
                    # Skip radius question if no zip code
                    st.session_state.profile_data['radius_miles'] = None

            st.session_state.chat_step += 1
            st.rerun()

    else:
        # Profile complete!
        st.success("✅ Profile complete! Let me find your matches...")

        # Create UserProfile
        try:
            profile = UserProfile(
                race=st.session_state.profile_data.get('race', 'OTHER'),
                is_parent=st.session_state.profile_data.get('is_parent', False),
                first_gen=st.session_state.profile_data.get('first_gen', False),
                budget=st.session_state.profile_data.get('budget', 25000),
                income_bracket=st.session_state.profile_data.get('income_bracket', 'MEDIUM'),
                gpa=st.session_state.profile_data.get('gpa', 3.0),
                in_state_only=st.session_state.profile_data.get('in_state_only', False),
                state=st.session_state.profile_data.get('state'),
                public_only=st.session_state.profile_data.get('public_only', False),
                school_size_pref=st.session_state.profile_data.get('school_size_pref'),
                zip_code=st.session_state.profile_data.get('zip_code'),
                radius_miles=st.session_state.profile_data.get('radius_miles')
            )

            # Save profile to session state for persistence
            st.session_state.saved_profile = profile

            return profile
        except Exception as e:
            st.error(f"Error creating profile: {e}")
            if st.button("Start Over"):
                st.session_state.chat_messages = []
                st.session_state.profile_data = {}
                st.session_state.chat_step = 0
                st.rerun()
            return None


def generate_college_summary(row, profile, client):
    """Generate AI summary for a specific college."""
    if not client:
        return None

    college_data = {
        "name": row.get('Institution Name', 'Unknown'),
        "state": row.get('State of Institution', 'N/A'),
        "sector": row.get('Sector of Institution', 'N/A'),
        "match_score": float(row.get('user_score', 0)),
        "net_price": float(pd.to_numeric(row.get('Net Price', 0), errors='coerce')),
        "median_debt": float(pd.to_numeric(row.get('Median Debt of Completers', 0), errors='coerce')),
        "median_earnings": float(pd.to_numeric(row.get('Median Earnings of Students Working and Not Enrolled 10 Years After Entry', 0), errors='coerce')),
        "admission_rate": float(pd.to_numeric(row.get('Total Percent of Applicants Admitted', 0), errors='coerce')),
        "archetype": row.get('cluster_label', 'N/A')
    }

    prompt = f"""As a college advisor, write a brief 2-3 sentence summary of why {college_data['name']} is a good match for this student:

Student: {profile.race}, {'student-parent' if profile.is_parent else 'non-parent'}, {'first-generation' if profile.first_gen else 'continuing-generation'}, {profile.budget:,.0f} budget, {profile.gpa} GPA

College:
- Match Score: {college_data['match_score']:.3f}
- Net Price: {college_data['net_price']:,.0f}
- Median Earnings (10yr): {college_data['median_earnings']:,.0f}
- Admission Rate: {college_data['admission_rate']:.1f}%
- Type: {college_data['archetype']}

Focus on why this specific college fits this specific student's needs. Be encouraging but honest.

IMPORTANT: Write dollar amounts WITHOUT the dollar sign (e.g., "33,000" not "$33,000") to avoid formatting issues."""

    try:
        response = client.messages.create(
            model=os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
            max_tokens=200,
            temperature=0.7,
            system="You are a supportive college advisor focused on equity and student success.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    except:
        return None


def main():
    """Main app function."""

    st.set_page_config(
        page_title="EquiPath - Chat Mode",
        page_icon="🎓",
        layout="wide"
    )

    st.title("🎓 EquiPath: AI-Powered College Advising")

    # Check for Anthropic package
    if not ANTHROPIC_AVAILABLE:
        st.error("⚠️ Anthropic package not installed. Install with: pip install anthropic")
        st.stop()

    # Sidebar settings
    with st.sidebar:
        st.header("⚙️ Settings")

        # Show saved profile if it exists
        if 'saved_profile' in st.session_state and st.session_state.saved_profile:
            with st.expander("👤 Your Saved Profile", expanded=False):
                prof = st.session_state.saved_profile
                st.write(f"**Budget:** ${prof.budget:,.0f}")
                st.write(f"**GPA:** {prof.gpa}")
                st.write(f"**State:** {prof.state or 'Not specified'}")
                st.write(f"**In-state only:** {'Yes' if prof.in_state_only else 'No'}")
                st.write(f"**Public only:** {'Yes' if prof.public_only else 'No'}")
                if st.button("📝 Edit Profile"):
                    # Clear to restart profile creation
                    st.session_state.chat_messages = []
                    st.session_state.profile_data = {}
                    st.session_state.chat_step = 0
                    st.session_state.saved_profile = None
                    st.rerun()

        mode = st.radio(
            "Choose Mode:",
            ["💬 Chat Mode (AI-Powered)", "📋 Manual Form"],
            index=0
        )

        if st.button("🔄 Reset / Start Over"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Load data
    with st.spinner("Loading college data..."):
        df, _, _ = load_data()
        df_merged = load_pathway_data()

    client = get_anthropic_client()

    # Profile collection
    # Check if we have a saved profile
    profile = st.session_state.get('saved_profile', None)

    # If no saved profile, collect one
    if not profile:
        if "💬 Chat" in mode:
            # Chat mode
            profile = chat_collect_profile()
        else:
            # Manual form (simplified version)
            st.subheader("📋 Manual Profile Entry")
            with st.form("profile_form"):
                col1, col2 = st.columns(2)

                with col1:
                    race = st.selectbox("Race/Ethnicity", ["BLACK", "HISPANIC", "WHITE", "ASIAN", "NATIVE", "PACIFIC", "OTHER"])
                    is_parent = st.checkbox("Student-Parent")
                    first_gen = st.checkbox("First-Generation")
                    budget = st.number_input("Annual Budget ($)", min_value=0, value=25000, step=1000)
                    state_input = st.text_input("Your State (2-letter code)", value="CA", help="e.g., CA, NY, TX")
                    state = state_input.upper()[:2]  # Limit to 2 characters

                with col2:
                    income = st.selectbox("Income Bracket", ["LOW", "MEDIUM", "HIGH"], index=1)
                    gpa = st.slider("GPA", 0.0, 4.0, 3.5, 0.1)
                    in_state_only = st.checkbox("Only show in-state colleges")
                    public_only = st.checkbox("Only show public schools")
                    school_size = st.selectbox("Preferred School Size", ["Any", "Small", "Medium", "Large"], index=0)

                st.markdown("**Location Preferences (Optional)**")
                col3, col4 = st.columns(2)
                with col3:
                    zip_code_input = st.text_input("Your Zip Code (5 digits)", placeholder="90210", help="Leave blank to search all locations")
                with col4:
                    radius = st.number_input("Max Distance (miles)", min_value=0, value=0, step=10, help="0 = no limit")

                submitted = st.form_submit_button("Find My Matches")

                if submitted:
                    # Process zip code
                    zip_code = None
                    if zip_code_input:
                        zip_digits = ''.join(filter(str.isdigit, zip_code_input))
                        if len(zip_digits) == 5:
                            zip_code = zip_digits

                    # Process radius
                    radius_miles = radius if radius > 0 and zip_code else None

                    profile = UserProfile(
                        race=race,
                        is_parent=is_parent,
                        first_gen=first_gen,
                        budget=budget,
                        income_bracket=income,
                        gpa=gpa,
                        in_state_only=in_state_only,
                        state=state if state else None,
                        public_only=public_only,
                        school_size_pref=school_size if school_size != "Any" else None,
                        zip_code=zip_code,
                        radius_miles=radius_miles
                    )
                    # Save profile to session state for persistence
                    st.session_state.saved_profile = profile

    # Show recommendations if profile is complete
    if profile:
        st.divider()

        # Show profile summary for debugging
        with st.expander("📋 Your Profile Settings"):
            st.write(f"**State:** {profile.state or 'Not specified'}")
            st.write(f"**In-state only:** {'Yes' if profile.in_state_only else 'No'}")
            st.write(f"**Public schools only:** {'Yes' if profile.public_only else 'No'}")
            st.write(f"**School size preference:** {profile.school_size_pref or 'Any'}")
            st.write(f"**Budget:** ${profile.budget:,.0f}")
            st.write(f"**GPA:** {profile.gpa}")

        # Get recommendations
        with st.spinner("Finding your best matches..."):
            recommendations = rank_colleges_for_user(df, profile, top_k=10)

        if len(recommendations) == 0:
            st.error("No colleges match your criteria. Try adjusting your filters.")
            st.info("💡 Tip: Try unchecking 'in-state only' or 'public only' filters, or increase your budget.")
        else:
            # Generate overall summary with AI
            if client:
                with st.spinner("Generating personalized insights..."):
                    summary = build_recommendation_summary(profile, recommendations, top_k=5)
                    overall_explanation = generate_explanations(summary)

                    st.subheader("🤖 Your Personalized College Guide")
                    st.markdown(overall_explanation)
                    st.divider()

            # Show recommendations
            st.subheader(f"🎯 Your Top {len(recommendations)} Matches")

            # Personalized weights
            weights = choose_weights(profile)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("ROI Weight", f"{weights['alpha']:.0%}")
            col2.metric("Affordability", f"{weights['beta']:.0%}")
            col3.metric("Equity", f"{weights['gamma']:.0%}")
            col4.metric("Access", f"{weights['delta']:.0%}")

            st.divider()

            # Display each college
            for idx, (_, row) in enumerate(recommendations.iterrows(), 1):
                with st.expander(f"**{idx}. {row.get('Institution Name', 'Unknown')}** - Match Score: {row['user_score']:.3f}"):

                    # Generate AI summary for this college
                    if client:
                        with st.spinner("Generating college summary..."):
                            college_summary = generate_college_summary(row, profile, client)
                            if college_summary:
                                st.info(f"💡 **Why this college?** {college_summary}")
                                st.divider()

                    col_a, col_b = st.columns(2)

                    with col_a:
                        st.markdown("**📍 Location & Type**")
                        st.write(f"State: {row.get('State of Institution', 'N/A')}")
                        # Show distance if available
                        if 'distance_miles' in row.index and pd.notna(row['distance_miles']):
                            st.write(f"Distance: {row['distance_miles']:.1f} miles from you")
                        st.write(f"Sector: {row.get('Sector of Institution', 'N/A')}")
                        st.write(f"Archetype: {row.get('cluster_label', 'N/A')}")

                        st.markdown("**💰 Financial**")
                        net_price = pd.to_numeric(row.get('Net Price', None), errors='coerce')
                        st.write(f"Net Price: {format_currency(net_price)}")
                        median_debt = pd.to_numeric(row.get('Median Debt of Completers', None), errors='coerce')
                        st.write(f"Median Debt: {format_currency(median_debt)}")

                    with col_b:
                        st.markdown("**📊 Scores**")
                        st.write(f"Match Score: {row['user_score']:.3f}")
                        st.write(f"ROI: {row.get('roi_score', 0):.3f}")
                        st.write(f"Affordability: {row.get('afford_score_std', 0):.3f}")
                        st.write(f"Equity: {row.get('equity_parity', 0):.3f}")

                        st.markdown("**🎓 Outcomes**")
                        earnings = pd.to_numeric(row.get('Median Earnings of Students Working and Not Enrolled 10 Years After Entry', None), errors='coerce')
                        st.write(f"10yr Earnings: {format_currency(earnings)}")
                        admit = pd.to_numeric(row.get('Total Percent of Applicants Admitted', None), errors='coerce')
                        st.write(f"Admit Rate: {format_percentage(admit)}")

            # Visualization
            st.divider()
            st.subheader("📈 Visual Comparison")

            # Prepare data for visualization with fallback columns
            viz_data = recommendations.head(10).copy()

            # Determine which columns to use based on availability
            x_col = 'afford_score_std' if 'afford_score_std' in viz_data.columns else 'afford_score_parent'
            y_col = 'equity_parity' if 'equity_parity' in viz_data.columns else 'user_score'
            size_col = 'roi_score' if 'roi_score' in viz_data.columns else None

            # Create scatter plot
            if size_col and size_col in viz_data.columns:
                fig = px.scatter(
                    viz_data,
                    x=x_col,
                    y=y_col,
                    size=size_col,
                    color='user_score',
                    hover_name='Institution Name',
                    labels={
                        x_col: 'Affordability',
                        y_col: 'Equity',
                        'user_score': 'Match Score'
                    },
                    title="Affordability vs. Equity"
                )
            else:
                # Fallback without size parameter
                fig = px.scatter(
                    viz_data,
                    x=x_col,
                    y=y_col,
                    color='user_score',
                    hover_name='Institution Name',
                    labels={
                        x_col: 'Affordability',
                        y_col: 'Equity',
                        'user_score': 'Match Score'
                    },
                    title="Affordability vs. Equity"
                )
            st.plotly_chart(fig, use_container_width=True)

            # Community College Pathway Comparison
            st.divider()
            st.subheader("🔄 Community College Transfer Pathway")
            st.markdown("""
            Interested in starting at a community college and transferring to a 4-year university?
            This can be a great way to save money while still earning the same degree!
            """)

            if st.button("📊 Compare Community College vs. Direct 4-Year Paths", type="primary"):
                st.session_state.show_pathway = True

            if st.session_state.get('show_pathway', False):
                with st.spinner("Analyzing pathway options..."):
                    pathway_results = analyze_pathway_options(profile, df_merged)
                    display_pathway_comparison(pathway_results)

            # Add conversational Q&A chatbot
            st.divider()
            st.subheader("💬 Ask Questions About Your Colleges")
            st.markdown("Have questions about these schools or want to know about other colleges? Ask me anything!")

            # Initialize Q&A chat history
            if 'qa_messages' not in st.session_state:
                st.session_state.qa_messages = []

            # Display Q&A chat history
            for msg in st.session_state.qa_messages:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

            # Q&A input
            if client:
                user_question = st.chat_input("Ask about colleges, compare schools, or request more information...")

                if user_question:
                    # Add user message
                    st.session_state.qa_messages.append({"role": "user", "content": user_question})

                    # Build context with profile and recommendations
                    context = f"""
Student Profile:
- Budget: {profile.budget:,.0f}
- GPA: {profile.gpa}
- State: {profile.state or 'Not specified'}
- Preferences: {'In-state only, ' if profile.in_state_only else ''}{'Public only, ' if profile.public_only else ''}{profile.school_size_pref or 'Any size'}

Recommended Colleges:
{chr(10).join([f"{i+1}. {row['Institution Name']} (State: {row.get('State of Institution', 'N/A')}, Net Price: {format_currency(pd.to_numeric(row.get('Net Price', 0), errors='coerce'))}, Match Score: {row['user_score']:.3f})" for i, (_, row) in enumerate(recommendations.head(10).iterrows())])}

Full Dataset Available: {len(df)} colleges across all states
"""

                    # Generate AI response
                    with st.spinner("Thinking..."):
                        try:
                            response = client.messages.create(
                                model=os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
                                max_tokens=800,
                                temperature=0.7,
                                system="""You are a knowledgeable college advisor helping students explore their college options.
You have access to the student's profile and their recommended colleges, as well as a database of colleges.

Answer questions about:
- The recommended colleges (provide specifics from the data)
- Comparisons between schools
- Other colleges the student might be interested in
- College search strategies and next steps

Be conversational, supportive, and informative. Use the context provided to give specific answers.
When mentioning dollar amounts, write them WITHOUT the dollar sign to avoid formatting issues.""",
                                messages=[
                                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_question}"}
                                ]
                            )

                            ai_response = response.content[0].text
                            st.session_state.qa_messages.append({"role": "assistant", "content": ai_response})

                            # Display the new response immediately
                            with st.chat_message("assistant"):
                                st.write(ai_response)

                        except Exception as e:
                            st.error(f"Error generating response: {str(e)}")
            else:
                st.info("💡 Chat requires an API key. Add your Anthropic API key to enable this feature.")


if __name__ == "__main__":
    main()
