"""
Enhanced Streamlit app for EquiPath with LLM-powered chat interface.
Allows students to create profiles conversationally and get detailed AI explanations.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
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
        "What school size do you prefer? (Small, Medium, Large, or 'any' if no preference)"
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
                school_size_pref=st.session_state.profile_data.get('school_size_pref')
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
        df, centroids, cluster_labels = load_data()

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

                submitted = st.form_submit_button("Find My Matches")

                if submitted:
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
                        school_size_pref=school_size if school_size != "Any" else None
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

            fig = px.scatter(
                recommendations.head(10),
                x='afford_score_std',
                y='equity_parity',
                size='roi_score',
                color='user_score',
                hover_name='Institution Name',
                labels={
                    'afford_score_std': 'Affordability',
                    'equity_parity': 'Equity',
                    'user_score': 'Match Score'
                },
                title="Affordability vs. Equity"
            )
            st.plotly_chart(fig, use_container_width=True)

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
