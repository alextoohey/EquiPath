"""
Enhanced Streamlit Chat App for EquiPath

Comprehensive conversational interface with:
- Extended profile questions covering all new dimensions
- Support for enhanced indices (Support, Academic Fit, Environment)
- LLM-powered explanations using all available features
- Filter options and customizable weights
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import json
import sys
import os
import io
import contextlib

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.enhanced_feature_engineering import build_enhanced_featured_college_df
from src.enhanced_user_profile import EnhancedUserProfile
from src.enhanced_scoring import rank_colleges_for_user, get_personalized_weights
from src.config import get_anthropic_api_key

# Import Anthropic
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_currency(value):
    """Format value as currency."""
    if pd.isna(value) or value == 0:
        return "N/A"
    return f"${value:,.0f}"


def format_percentage(value):
    """Format value as percentage."""
    if pd.isna(value):
        return "N/A"
    return f"{value:.1f}%"


def format_urbanization(value):
    """Convert urbanization code to readable label."""
    if pd.isna(value):
        return "N/A"

    value = int(value) if not pd.isna(value) else 0

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

    value = int(value) if not pd.isna(value) else 0

    # 1 = Small, 2 = Medium, 3-5 = Large
    size_map = {
        1: "Small",
        2: "Medium",
        3: "Large",
        4: "Large",
        5: "Large"
    }

    return size_map.get(value, "N/A")


@st.cache_data
def load_enhanced_data(earnings_ceiling=30000.0):
    """Load and cache enhanced college data."""
    # Load silently - no console output
    return build_enhanced_featured_college_df(earnings_ceiling=earnings_ceiling)


def get_anthropic_client():
    """Get Anthropic client if available."""
    api_key = get_anthropic_api_key()
    if api_key and ANTHROPIC_AVAILABLE:
        return Anthropic(api_key=api_key)
    return None


# ============================================================================
# CHAT INTERFACE
# ============================================================================

def enhanced_chat_collect_profile():
    """
    Enhanced interactive chat to collect comprehensive user profile.

    Covers all EnhancedUserProfile dimensions:
    - Academic background (GPA, test scores, major)
    - Financial situation (budget, income, Pell eligibility)
    - Demographics (race, gender, age - handled sensitively)
    - Special populations (first-gen, student-parent, international, nontraditional)
    - Geographic preferences
    - Environment preferences (size, urbanization, MSI interest)
    - Academic priorities (research, class size, support)
    - Scoring weight preferences
    """
    st.subheader("💬 Chat with EquiPath - Enhanced Profile Builder")
    st.markdown("""
    I'll ask you a series of questions to understand your needs and preferences.
    **All questions are optional** - you can skip any question by typing 'skip' or 'pass'.
    """)

    # Initialize session state
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
        st.session_state.profile_data = {}
        st.session_state.chat_step = 0
        st.session_state.profile_complete = False

    # Enhanced questions flow
    questions = [
        # Academic Background
        {
            "key": "gpa",
            "question": "Hi! Let's find your perfect college. What's your current GPA on a 4.0 scale?",
            "type": "float",
            "required": True
        },
        {
            "key": "test_status",
            "question": "Have you taken the SAT or ACT? (yes/no/planning to)",
            "type": "choice",
            "options": ["yes", "no", "planning"]
        },
        {
            "key": "sat_score",
            "question": "What's your SAT score? (400-1600, or 'skip' if you took ACT)",
            "type": "int",
            "condition": lambda: st.session_state.profile_data.get('test_status') == 'yes'
        },
        {
            "key": "act_score",
            "question": "What's your ACT score? (1-36, or 'skip' if you provided SAT)",
            "type": "int",
            "condition": lambda: st.session_state.profile_data.get('test_status') == 'yes' and not st.session_state.profile_data.get('sat_score')
        },
        {
            "key": "intended_major",
            "question": "What field are you interested in studying? Options:\n- STEM\n- Business\n- Health\n- Social Sciences\n- Arts & Humanities\n- Education\n- Undecided",
            "type": "choice",
            "options": ["STEM", "Business", "Health", "Social Sciences", "Arts & Humanities", "Education", "Undecided"]
        },

        # Financial Situation
        {
            "key": "annual_budget",
            "question": "What's your approximate annual budget for college? (Just the number, like 20000)",
            "type": "float",
            "required": True
        },
        {
            "key": "family_income",
            "question": "What's your estimated family income? (Optional - helps match affordability data. Enter amount or 'skip')",
            "type": "float"
        },
        {
            "key": "work_study_needed",
            "question": "Do you need work-study opportunities to help pay for college? (yes/no)",
            "type": "bool"
        },

        # Demographics & Background (handled sensitively)
        {
            "key": "race_ethnicity",
            "question": "How would you describe your race/ethnicity? (Optional - used ONLY to show relevant graduation rates)\nOptions: Black, Hispanic, White, Asian, Native American, Pacific Islander, Two or More, Prefer not to say",
            "type": "choice",
            "options": ["BLACK", "HISPANIC", "WHITE", "ASIAN", "NATIVE", "PACIFIC", "TWO_OR_MORE", "PREFER_NOT_TO_SAY"]
        },
        {
            "key": "age",
            "question": "How old are you? (Optional)",
            "type": "int"
        },

        # Special Populations
        {
            "key": "is_first_gen",
            "question": "Are you a first-generation college student (neither parent completed a 4-year degree)? (yes/no)",
            "type": "bool"
        },
        {
            "key": "is_student_parent",
            "question": "Are you a student-parent (do you have dependent children)? (yes/no)",
            "type": "bool"
        },
        {
            "key": "is_international",
            "question": "Are you an international student? (yes/no)",
            "type": "bool"
        },

        # Geographic Preferences
        {
            "key": "home_state",
            "question": "What state are you from? (2-letter code like CA, NY, TX, or 'skip' if international)",
            "type": "text"
        },
        {
            "key": "in_state_only",
            "question": "Do you want to only consider in-state schools? (yes/no)",
            "type": "bool",
            "condition": lambda: st.session_state.profile_data.get('home_state')
        },
        {
            "key": "preferred_states",
            "question": "Any other specific states you're interested in? (Comma-separated like CA,NY,TX or 'none')",
            "type": "list",
            "condition": lambda: not st.session_state.profile_data.get('in_state_only')
        },

        # Environment Preferences
        {
            "key": "urbanization_pref",
            "question": "What kind of setting do you prefer?\n- Urban (big city)\n- Suburban (near city)\n- Town (small town)\n- Rural (countryside)\n- No preference",
            "type": "choice",
            "options": ["urban", "suburban", "town", "rural", "no_preference"]
        },
        {
            "key": "size_pref",
            "question": "What school size do you prefer?\n- Small (under 2,000)\n- Medium (2,000-10,000)\n- Large (over 10,000)\n- No preference",
            "type": "choice",
            "options": ["small", "medium", "large", "no_preference"]
        },
        {
            "key": "institution_type_pref",
            "question": "Do you prefer public or private schools, or either? (public/private_nonprofit/either)",
            "type": "choice",
            "options": ["public", "private_nonprofit", "either"]
        },
        {
            "key": "msi_preference",
            "question": "Are you interested in Minority-Serving Institutions?\nOptions:\n- HBCU (Historically Black)\n- HSI (Hispanic-Serving)\n- Tribal College\n- Any MSI\n- No preference",
            "type": "choice",
            "options": ["HBCU", "HSI", "Tribal", "any_MSI", "no_preference"]
        },

        # Academic Priorities
        {
            "key": "research_opportunities",
            "question": "Are research opportunities important to you? (yes/no)",
            "type": "bool"
        },
        {
            "key": "small_class_sizes",
            "question": "Do you prefer small class sizes? (yes/no)",
            "type": "bool"
        },
        {
            "key": "strong_support_services",
            "question": "Are strong student support services important to you? (especially helpful for first-gen students) (yes/no)",
            "type": "bool"
        },

        # Priorities
        {
            "key": "priorities",
            "question": "Almost done! What matters most to you? Rank these (or type 'default' for balanced):\n1. Affordability\n2. Support Services\n3. Academic Quality/ROI\n4. Equity/Diversity\n5. Environment Fit\n\nExample: 'Affordability, Support, ROI'",
            "type": "text"
        }
    ]

    # Display chat history
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Check if profile is complete
    if st.session_state.chat_step >= len(questions):
        if not st.session_state.profile_complete:
            # Build profile
            try:
                profile = build_profile_from_data(st.session_state.profile_data)
                st.session_state.user_profile = profile
                st.session_state.profile_complete = True

                with st.chat_message("assistant"):
                    st.success("✅ Profile complete! Click 'Get Recommendations' in the sidebar to see your matches!")
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": "✅ Profile complete! Click 'Get Recommendations' in the sidebar."
                    })
            except Exception as e:
                with st.chat_message("assistant"):
                    st.error(f"Error creating profile: {e}")
                    st.info("Please check your answers and try again.")
        return

    # Show current question
    current_q = questions[st.session_state.chat_step]

    # Check condition if exists
    if 'condition' in current_q and not current_q['condition']():
        # Skip this question
        st.session_state.chat_step += 1
        st.rerun()
        return

    # Check if we need to show the question
    assistant_msg_count = sum(1 for msg in st.session_state.chat_messages if msg["role"] == "assistant")

    if assistant_msg_count <= st.session_state.chat_step:
        with st.chat_message("assistant"):
            st.write(current_q["question"])
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": current_q["question"]
            })

    # User input
    user_input = st.chat_input("Your answer (or type 'skip' to skip optional questions)...")

    if user_input:
        # Add user message
        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_input
        })

        # Process answer
        processed_value = process_user_answer(user_input, current_q, st.session_state.profile_data)

        if processed_value is not None or user_input.lower() in ['skip', 'pass']:
            # Store value
            if processed_value is not None:
                st.session_state.profile_data[current_q['key']] = processed_value

            # Move to next question
            st.session_state.chat_step += 1
            st.rerun()
        else:
            # Invalid answer, ask again
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": "I didn't quite understand that. Could you try again?"
            })
            st.rerun()  # Rerun to show the error message and keep chat active


def process_user_answer(user_input, question_config, profile_data):
    """Process user answer based on question type."""
    user_input = user_input.strip()

    # Skip handling
    if user_input.lower() in ['skip', 'pass'] and not question_config.get('required'):
        return None

    q_type = question_config.get('type', 'text')

    try:
        if q_type == 'float':
            # Extract number
            cleaned = ''.join(c for c in user_input if c.isdigit() or c == '.')
            return float(cleaned)

        elif q_type == 'int':
            # Extract integer
            cleaned = ''.join(c for c in user_input if c.isdigit())
            return int(cleaned) if cleaned else None

        elif q_type == 'bool':
            return 'yes' in user_input.lower() or 'y' == user_input.lower()

        elif q_type == 'choice':
            # Match to one of the options
            options = question_config.get('options', [])
            user_lower = user_input.lower().strip()

            # Exact match first
            for option in options:
                if option.lower() == user_lower:
                    return option

            # Special handling for common variations (BEFORE generic matching)
            # Urbanization preferences
            if user_lower in ['city', 'big city', 'urban area']:
                if 'urban' in [opt.lower() for opt in options]:
                    return 'urban'
            elif user_lower in ['suburb', 'suburbs', 'near city']:
                if 'suburban' in [opt.lower() for opt in options]:
                    return 'suburban'
            elif user_lower in ['small town', 'town']:  # Added 'town' alone
                if 'town' in [opt.lower() for opt in options]:
                    return 'town'
            elif user_lower in ['countryside', 'country', 'remote']:
                if 'rural' in [opt.lower() for opt in options]:
                    return 'rural'

            # Size preferences
            elif user_lower in ['tiny', 'very small']:
                if 'small' in [opt.lower() for opt in options]:
                    return 'small'
            elif user_lower in ['mid-size', 'medium-sized', 'moderate']:
                if 'medium' in [opt.lower() for opt in options]:
                    return 'medium'
            elif user_lower in ['big', 'huge', 'very large']:
                if 'large' in [opt.lower() for opt in options]:
                    return 'large'

            # Institution type preferences
            elif user_lower in ['state', 'state school', 'public university']:
                if 'public' in [opt.lower() for opt in options]:
                    return 'public'
            elif user_lower in ['private', 'private school']:
                if 'private_nonprofit' in [opt.lower() for opt in options]:
                    return 'private_nonprofit'

            # MSI preferences
            elif user_lower in ['historically black', 'black college']:
                if 'hbcu' in [opt.lower() for opt in options]:
                    return 'HBCU'
            elif user_lower in ['hispanic serving', 'latino serving']:
                if 'hsi' in [opt.lower() for opt in options]:
                    return 'HSI'
            elif user_lower in ['tribal', 'native american']:
                if 'tribal' in [opt.lower() for opt in options]:
                    return 'Tribal'
            elif user_lower in ['any msi', 'minority serving']:
                if 'any_msi' in [opt.lower() for opt in options]:
                    return 'any_MSI'

            # Major/field preferences
            elif user_lower in ['science', 'technology', 'engineering', 'math']:
                if 'stem' in [opt.lower() for opt in options]:
                    return 'STEM'
            elif user_lower in ['medicine', 'nursing', 'healthcare']:
                if 'health' in [opt.lower() for opt in options]:
                    return 'Health'
            elif user_lower in ['liberal arts', 'humanities']:
                if 'arts & humanities' in [opt.lower() for opt in options]:
                    return 'Arts & Humanities'
            elif user_lower in ['not sure', 'unsure', 'don\'t know']:
                if 'undecided' in [opt.lower() for opt in options]:
                    return 'Undecided'

            # Race/ethnicity preferences
            elif user_lower in ['african american', 'black']:
                if 'black' in [opt.lower() for opt in options]:
                    return 'BLACK'
            elif user_lower in ['latino', 'latina', 'latinx', 'chicano']:
                if 'hispanic' in [opt.lower() for opt in options]:
                    return 'HISPANIC'
            elif user_lower in ['asian american', 'asian']:
                if 'asian' in [opt.lower() for opt in options]:
                    return 'ASIAN'
            elif user_lower in ['native', 'indigenous', 'american indian']:
                if 'native' in [opt.lower() for opt in options]:
                    return 'NATIVE'
            elif user_lower in ['pacific islander', 'hawaiian']:
                if 'pacific' in [opt.lower() for opt in options]:
                    return 'PACIFIC'
            elif user_lower in ['multiracial', 'mixed', 'biracial']:
                if 'two_or_more' in [opt.lower() for opt in options]:
                    return 'TWO_OR_MORE'
            elif user_lower in ['skip', 'pass', 'rather not say']:
                if 'prefer_not_to_say' in [opt.lower() for opt in options]:
                    return 'PREFER_NOT_TO_SAY'

            # Test status
            elif user_lower in ['took it', 'yes i have', 'submitted']:
                if 'yes' in [opt.lower() for opt in options]:
                    return 'yes'
            elif user_lower in ['haven\'t taken', 'didn\'t take', 'no test']:
                if 'no' in [opt.lower() for opt in options]:
                    return 'no'
            elif user_lower in ['will take', 'plan to', 'going to']:
                if 'planning' in [opt.lower() for opt in options]:
                    return 'planning'

            # Generic "no preference" variations
            elif user_lower in ['any', 'either', 'no preference', "don't care", "doesn't matter", 'both']:
                for opt in options:
                    if 'no_preference' in opt.lower() or 'either' in opt.lower():
                        return opt

            # Fallback: Check if option is in user input or vice versa
            for option in options:
                if option.lower() in user_lower or user_lower in option.lower():
                    return option

            # Fallback: Try word-based partial match
            for option in options:
                if any(word in user_lower for word in option.lower().split()):
                    return option

            return None

        elif q_type == 'list':
            # Recognize various ways of saying "no" or "none"
            negative_responses = [
                'none', 'no', 'skip', 'nope', 'nah', 'pass',
                'not really', "don't have any", "don't have",
                'no preference', 'no preferences', "doesn't matter",
                'anywhere', 'any', 'all'
            ]
            if user_input.lower().strip() in negative_responses:
                return []
            # Split by comma and filter out empty/whitespace items
            items = [item.strip().upper() for item in user_input.split(',') if item.strip()]
            return items

        else:  # text
            return user_input

    except:
        return None


def build_profile_from_data(profile_data):
    """Build EnhancedUserProfile from collected data."""

    # Map priorities to weights
    priorities_text = profile_data.get('priorities', 'default').lower()

    if 'default' in priorities_text:
        weights = {
            'weight_roi': 0.20,
            'weight_affordability': 0.25,
            'weight_equity': 0.20,
            'weight_support': 0.15,
            'weight_academic_fit': 0.15,
            'weight_environment': 0.05
        }
    else:
        # Parse custom priorities
        priority_map = {
            'affordability': 'weight_affordability',
            'support': 'weight_support',
            'roi': 'weight_roi',
            'academic': 'weight_academic_fit',
            'equity': 'weight_equity',
            'diversity': 'weight_equity',
            'environment': 'weight_environment',
            'fit': 'weight_environment'
        }

        # Start with equal weights
        weights = {
            'weight_roi': 0.1,
            'weight_affordability': 0.1,
            'weight_equity': 0.1,
            'weight_support': 0.1,
            'weight_academic_fit': 0.1,
            'weight_environment': 0.1
        }

        # Boost mentioned priorities
        mentioned_count = 0
        for key_word, weight_key in priority_map.items():
            if key_word in priorities_text:
                weights[weight_key] += 0.15
                mentioned_count += 1

        # Normalize
        total = sum(weights.values())
        weights = {k: v/total for k, v in weights.items()}

    # Determine test score status
    test_status = "test_optional"
    if profile_data.get('test_status') == 'yes':
        if profile_data.get('sat_score') or profile_data.get('act_score'):
            test_status = "submitted"
    elif profile_data.get('test_status') == 'no':
        test_status = "no_test"

    # Determine earnings ceiling from income
    family_income = profile_data.get('family_income')
    if family_income:
        if family_income <= 30000:
            earnings_ceiling = 30000.0
        elif family_income <= 48000:
            earnings_ceiling = 48000.0
        elif family_income <= 75000:
            earnings_ceiling = 75000.0
        elif family_income <= 110000:
            earnings_ceiling = 110000.0
        else:
            earnings_ceiling = 150000.0
    else:
        # Default to lowest
        earnings_ceiling = 30000.0

    # Build profile
    profile = EnhancedUserProfile(
        # Required
        gpa=profile_data.get('gpa', 3.0),
        annual_budget=profile_data.get('annual_budget', 20000),

        # Academic
        test_score_status=test_status,
        sat_score=profile_data.get('sat_score'),
        act_score=profile_data.get('act_score'),
        intended_major=profile_data.get('intended_major', 'Undecided'),

        # Financial
        family_income=family_income,
        earnings_ceiling_match=earnings_ceiling,
        work_study_needed=profile_data.get('work_study_needed', False),

        # Demographics
        race_ethnicity=profile_data.get('race_ethnicity', 'PREFER_NOT_TO_SAY'),
        age=profile_data.get('age'),

        # Special populations
        is_first_gen=profile_data.get('is_first_gen', False),
        is_student_parent=profile_data.get('is_student_parent', False),
        is_international=profile_data.get('is_international', False),

        # Geographic
        home_state=profile_data.get('home_state'),
        in_state_only=profile_data.get('in_state_only', False),
        preferred_states=profile_data.get('preferred_states', []),

        # Environment
        urbanization_pref=profile_data.get('urbanization_pref', 'no_preference'),
        size_pref=profile_data.get('size_pref', 'no_preference'),
        institution_type_pref=profile_data.get('institution_type_pref', 'either'),
        msi_preference=profile_data.get('msi_preference', 'no_preference'),

        # Academic priorities
        research_opportunities=profile_data.get('research_opportunities', False),
        small_class_sizes=profile_data.get('small_class_sizes', False),
        strong_support_services=profile_data.get('strong_support_services', False),

        # Weights
        **weights
    )

    return profile


# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

def display_recommendations(recommendations, profile):
    """Display ranked recommendations with enhanced details."""

    st.header("🎓 Your Personalized College Recommendations")

    # Show profile summary
    with st.expander("📋 Your Profile Summary", expanded=False):
        st.text(str(profile))

    # Display each recommendation
    for idx, (_, college) in enumerate(recommendations.iterrows(), 1):
        # Helper function to safely get values from Series
        def safe_get(series, key, default='N/A'):
            try:
                if key in series.index:
                    val = series[key]
                    # Handle NaN/None
                    if pd.isna(val):
                        return default
                    return val
                return default
            except:
                return default

        # Try different possible column names for institution name
        # After merge with suffixes ('_CR', '_AG'), column might be renamed
        inst_name = (
            safe_get(college, 'Institution Name', None) or
            safe_get(college, 'Institution Name_CR', None) or
            safe_get(college, 'Institution Name_AG', None) or
            safe_get(college, 'INSTNM', None) or
            safe_get(college, 'INSTNM_CR', None) or
            safe_get(college, 'institution_name', None) or
            'Unknown Institution'
        )

        with st.expander(f"#{idx}: {inst_name}", expanded=(idx == 1)):

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Composite Score", f"{safe_get(college, 'composite_score', 0):.3f}")
                st.metric("Selectivity", safe_get(college, 'selectivity_bucket', 'Unknown'))

            with col2:
                st.metric("Affordability", f"{safe_get(college, 'personalized_affordability', 0):.3f}")
                st.metric("Support", f"{safe_get(college, 'personalized_support', 0):.3f}")

            with col3:
                st.metric("Academic Fit", f"{safe_get(college, 'personalized_academic_fit', 0):.3f}")
                st.metric("Equity", f"{safe_get(college, 'personalized_equity', 0):.3f}")

            # Details
            st.markdown("### Details")
            col1, col2 = st.columns(2)

            with col1:
                # Try both with and without suffixes
                city = (safe_get(college, 'City', None) or
                       safe_get(college, 'City_CR', None) or
                       safe_get(college, 'City_AG', 'N/A'))
                state = (safe_get(college, 'State of Institution', None) or
                        safe_get(college, 'State of Institution_CR', None) or
                        safe_get(college, 'State of Institution_AG', 'N/A'))
                st.write(f"**Location:** {city}, {state}")

                # Size - check actual column names from data
                size_val = (safe_get(college, 'Institution Size Category_CR', None) or
                           safe_get(college, 'size_category', None) or
                           safe_get(college, 'Institution Size Category', None))
                st.write(f"**Size:** {format_size(size_val)}")

                # Urbanization - check actual column names from data
                urban_val = (safe_get(college, 'Degree of Urbanization', None) or
                            safe_get(college, 'urbanization', None))
                st.write(f"**Urbanization:** {format_urbanization(urban_val)}")

            with col2:
                # Net Price and Affordability Gap columns are from AG dataset
                net_price = (safe_get(college, 'Net Price', None) or
                           safe_get(college, 'Net Price_AG', None))
                st.write(f"**Net Price:** {format_currency(net_price)}")

                # Graduation rate - 6 year total (note the duplicate "Bachelor Degree" in column name)
                grad_rate = (
                    safe_get(college, "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total", None) or
                    safe_get(college, "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total_CR", None) or
                    safe_get(college, "Bachelor's Degree Graduation Rate Within 6 Years - Total", None) or
                    safe_get(college, "Bachelor's Degree Graduation Rate Within 6 Years - Total_CR", None)
                )
                st.write(f"**Graduation Rate:** {format_percentage(grad_rate)}")

                # Median debt is from CR dataset
                debt = (safe_get(college, 'Median Debt of Completers', None) or
                       safe_get(college, 'Median Debt of Completers_CR', None))
                st.write(f"**Median Debt:** {format_currency(debt)}")


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    st.set_page_config(page_title="EquiPath - Enhanced", layout="wide", page_icon="🎓")

    st.title("🎓 EquiPath - Your Personalized College Guide")
    st.markdown("**Enhanced Edition** - Comprehensive equity-aware college matching")

    # Sidebar
    st.sidebar.header("Navigation")
    mode = st.sidebar.radio("Choose Mode:", ["Build Profile (Chat)", "Get Recommendations", "About"])

    if mode == "Build Profile (Chat)":
        enhanced_chat_collect_profile()

    elif mode == "Get Recommendations":
        if 'user_profile' not in st.session_state or not st.session_state.profile_complete:
            st.warning("Please complete your profile first using the chat interface!")
            return

        profile = st.session_state.user_profile

        # Load data and rank (suppress console output)
        with st.spinner("Finding your perfect college matches..."):
            # Redirect stdout to suppress print statements
            with contextlib.redirect_stdout(io.StringIO()):
                colleges_df = load_enhanced_data(earnings_ceiling=profile.earnings_ceiling_match)
                recommendations = rank_colleges_for_user(colleges_df, profile, top_k=15)

        if len(recommendations) > 0:
            display_recommendations(recommendations, profile)
        else:
            st.error("❌ No colleges match your criteria.")
            st.warning("**Try these adjustments:**")
            st.markdown("""
            1. **Increase your budget** - Current: ${:,.0f}
            2. **Remove geographic restrictions** - Try expanding beyond your current region/state preferences
            3. **Set preferences to 'no preference'** - Urbanization, size, institution type
            4. **Include more selectivity levels** - Make sure you're including reach, target, safety, AND open admission schools
            5. **Check the console output** (if running locally) for details on which filter eliminated colleges

            **Your current profile:**
            - Budget: ${:,.0f}
            - In-state only: {}
            - Preferred states: {}
            - Institution type: {}
            - Urbanization: {}
            - Size: {}
            - MSI preference: {}
            """.format(
                profile.annual_budget,
                profile.annual_budget,
                profile.in_state_only,
                profile.preferred_states if profile.preferred_states else "None",
                profile.institution_type_pref,
                profile.urbanization_pref,
                profile.size_pref,
                profile.msi_preference
            ))

    else:  # About
        st.markdown("""
        ## About EquiPath Enhanced

        EquiPath helps students find colleges that match their unique needs and circumstances.

        ### What Makes This Enhanced?

        **Comprehensive Indices:**
        - 📚 **Support Infrastructure** - Student support services
        - 📖 **Academic Offerings** - Field-specific program strength
        - 🏫 **Environment Fit** - Campus culture and setting
        - Plus ROI, Affordability, Equity, and Access

        **Equity-Focused:**
        - Race/ethnicity used ONLY for relevant graduation rates and MSI identification
        - Special support for first-gen, student-parents, and nontraditional students
        - Excludes predatory for-profit institutions by default

        **Fully Personalized:**
        - Custom scoring weights based on YOUR priorities
        - Selectivity bucketing (Reach/Target/Safety)
        - Field-specific matching for your intended major

        ### The Team
        Built for the Educational Equity Datathon 2025
        """)


if __name__ == "__main__":
    main()
