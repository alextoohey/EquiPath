"""
Enhanced Streamlit Chat App for EquiPath with Voice Support

Comprehensive conversational interface with:
- Extended profile questions covering all new dimensions
- Support for enhanced indices (Support, Academic Fit, Environment)
- LLM-powered explanations using all available features
- Filter options and customizable weights
- Voice input/output using ElevenLabs
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import sys
import os
import io
import contextlib
import base64
import re

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.enhanced_feature_engineering import build_enhanced_featured_college_df
from src.enhanced_user_profile import EnhancedUserProfile
from src.enhanced_scoring import rank_colleges_for_user, get_personalized_weights
from src.config import get_anthropic_api_key
from src.data_loading import load_merged_data

# Import ElevenLabs for voice
try:
    from elevenlabs import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

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


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_enhanced_data(earnings_ceiling=30000.0, zip_code=None, max_distance=None):
    """
    Load and cache enhanced college data.
    
    Args:
        earnings_ceiling: Maximum earnings value to include
        zip_code: Optional zip code for distance filtering (part of cache key)
        max_distance: Optional max distance in miles (part of cache key)
    """
    # Load the data
    df = build_enhanced_featured_college_df(earnings_ceiling=earnings_ceiling)
    
    # Filter by distance if zip code and max_distance are provided
    if zip_code and max_distance:
        from src.distance_utils import filter_by_radius
        try:
            # Convert to string and strip any whitespace
            zip_str = str(zip_code).strip()
            # Filter by radius
            df = filter_by_radius(
                df=df,
                zip_code=zip_str,
                radius_miles=float(max_distance)
            )
        except Exception as e:
            print(f"Error filtering by distance: {e}")
    
    return df


@st.cache_data
def load_pathway_data():
    """Load merged data for pathway analysis (includes transfer rates)."""
    return load_merged_data()


def analyze_pathway_options(profile, df_merged):
    """
    Analyze community college transfer pathway vs direct 4-year enrollment.

    Args:
        profile: EnhancedUserProfile with student information
        df_merged: DataFrame with merged college and affordability data

    Returns:
        dict with pathway analysis results
    """
    # Filter by state if specified
    if profile.home_state and profile.in_state_only:
        df_filtered = df_merged[df_merged['State of Institution'] == profile.home_state].copy()
    else:
        df_filtered = df_merged.copy()

    # Debug logging
    print(f"\n[DEBUG] Zip Code Filtering Debug Info:")
    print(f"  - Profile zip_code: {profile.zip_code}")
    print(f"  - Profile max_distance_from_home: {profile.max_distance_from_home}")
    print(f"  - DataFrame shape before filtering: {df_filtered.shape}")
    print(f"  - Available columns: {', '.join(sorted(df_filtered.columns))}")
    
    # Check for required columns
    has_lat = 'Latitude' in df_filtered.columns
    has_lon = 'Longitude' in df_filtered.columns
    print(f"  - Has Latitude column: {has_lat}")
    print(f"  - Has Longitude column: {has_lon}")
    
    if has_lat and has_lon:
        print("  - Sample coordinates:")
        print(df_filtered[['Institution Name', 'State of Institution', 'Latitude', 'Longitude']].head(2).to_string())

    # Filter by zip code radius BEFORE income filtering
    if profile.zip_code and profile.max_distance_from_home:
        from src.distance_utils import filter_by_radius
        print(f"\n[DEBUG] Attempting to filter by radius: {profile.max_distance_from_home} miles from zip {profile.zip_code}")
        try:
            df_filtered = filter_by_radius(df_filtered, profile.zip_code, profile.max_distance_from_home)
            print(f"[DEBUG] After radius filter: {len(df_filtered)} institutions remaining")
            if 'distance_miles' in df_filtered.columns:
                print(f"[DEBUG] Distance range: {df_filtered['distance_miles'].min():.1f} to {df_filtered['distance_miles'].max():.1f} miles")
        except Exception as e:
            print(f"[ERROR] Error in filter_by_radius: {str(e)}")
            import traceback
            traceback.print_exc()
    elif profile.zip_code:
        print(f"\n[DEBUG] Adding distance column for zip code: {profile.zip_code}")
        try:
            from src.distance_utils import add_distance_column
            df_filtered = add_distance_column(df_filtered, profile.zip_code)
            if 'distance_miles' in df_filtered.columns:
                print(f"[DEBUG] Added distance column. Range: {df_filtered['distance_miles'].min():.1f} to {df_filtered['distance_miles'].max():.1f} miles")
        except Exception as e:
            print(f"[ERROR] Error adding distance column: {str(e)}")
            import traceback
            traceback.print_exc()

    # Filter by income bracket using earnings_ceiling_match from profile
    if 'Student Family Earnings Ceiling' in df_filtered.columns:
        df_income = df_filtered[df_filtered['Student Family Earnings Ceiling'] == profile.earnings_ceiling_match].copy()

        # If still not enough community colleges, don't filter by income
        cc_test = df_income[df_income['Sector Name'] == 'Public, 2-year']
        if len(cc_test) < 10:
            df_income = df_filtered
    else:
        df_income = df_filtered

    # Separate by sector
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

    # Get top schools
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
    """Get Anthropic client if available."""
    api_key = get_anthropic_api_key()
    if api_key and ANTHROPIC_AVAILABLE:
        return Anthropic(api_key=api_key)
    return None


def generate_audio(text):
    """Generate audio from text using ElevenLabs."""
    if not ELEVENLABS_AVAILABLE:
        return None

    eleven_api_key = os.getenv("ELEVENLABS_API_KEY")
    if not eleven_api_key or eleven_api_key == "your-api-key-here":
        return None

    try:
        eleven_client = ElevenLabs(api_key=eleven_api_key)
        audio_generator = eleven_client.text_to_speech.convert(
            voice_id="pNInz6obpgDQGcFmaJgB",  # Adam voice
            text=text,
            model_id="eleven_turbo_v2_5"
        )
        return b"".join(audio_generator)
    except Exception as e:
        st.error(f"TTS error: {e}")
        return None


def transcribe_audio(audio_file):
    """Transcribe audio to text using ElevenLabs."""
    if not ELEVENLABS_AVAILABLE:
        st.warning("⚠️ ElevenLabs not installed. Voice features are disabled.")
        return None

    eleven_api_key = os.getenv("ELEVENLABS_API_KEY")
    if not eleven_api_key or eleven_api_key == "your-api-key-here":
        st.warning("⚠️ ElevenLabs API key not configured.")
        return None

    try:
        eleven_client = ElevenLabs(api_key=eleven_api_key)

        # Handle both file objects and bytes
        if hasattr(audio_file, 'getvalue'):
            audio_bytes = audio_file.getvalue()
            # Save to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name

            with open(tmp_path, 'rb') as f:
                transcript = eleven_client.speech_to_text.convert(
                    file=f,
                    model_id="scribe_v2"
                )

            # Clean up temp file
            os.unlink(tmp_path)
        else:
            transcript = eleven_client.speech_to_text.convert(
                file=audio_file,
                model_id="scribe_v2"
            )

        return transcript.text.strip() if transcript.text else None
    except Exception as e:
        error_msg = str(e)
        if 'quota_exceeded' in error_msg or '401' in error_msg:
            st.error("❌ **ElevenLabs quota exceeded** - Your API key has run out of credits. Please switch to text mode or upgrade your ElevenLabs plan.")
        else:
            st.error(f"Transcription error: {e}")
        return None


# ============================================================================
# NUMBER PARSING HELPERS
# ============================================================================

_NUMBER_WORDS = {
    "zero": 0,
    "oh": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}

_SCALE_WORDS = {
    "hundred": 100,
    "thousand": 1_000,
    "million": 1_000_000,
}

_ALLOWED_NUMBER_TOKENS = set(_NUMBER_WORDS.keys()) | set(_SCALE_WORDS.keys()) | {
    "and",
    "point",
    "dot",
    "decimal",
}


def _words_to_int(tokens):
    if not tokens:
        return 0

    total = 0
    current = 0

    for token in tokens:
        if token in _NUMBER_WORDS:
            current += _NUMBER_WORDS[token]
        elif token in _SCALE_WORDS:
            scale = _SCALE_WORDS[token]
            if current == 0:
                current = 1
            current *= scale
            if scale >= 1000:
                total += current
                current = 0
        elif token == "and":
            continue
        else:
            return None

    return total + current


def parse_spoken_number(text: str, allow_float: bool = True):
    if not text:
        return None

    # Quick path: direct numeric input
    try:
        value = float(text)
        return value if allow_float else int(value)
    except ValueError:
        pass

    # Remove punctuation except decimal point and digits for earlier handling
    cleaned = text.lower().replace("-", " ")
    cleaned = re.sub(r"[^a-z\s]", " ", cleaned)
    tokens = [tok for tok in cleaned.split() if tok]

    tokens = [tok for tok in tokens if tok in _ALLOWED_NUMBER_TOKENS]
    if not tokens:
        return None

    # Handle decimal separators
    for sep in ("point", "dot", "decimal"):
        if sep in tokens:
            if not allow_float:
                return None
            sep_index = tokens.index(sep)
            int_tokens = tokens[:sep_index]
            frac_tokens = tokens[sep_index + 1 :]

            integer_part = _words_to_int(int_tokens) if int_tokens else 0
            if integer_part is None:
                return None

            digit_map = {word: str(num) for word, num in _NUMBER_WORDS.items() if num < 10}
            frac_digits = [digit_map[token] for token in frac_tokens if token in digit_map]

            if len(frac_digits) == len(frac_tokens) and frac_digits:
                fractional_value = float(f"0.{''.join(frac_digits)}")
                return integer_part + fractional_value

            fractional_number = _words_to_int(frac_tokens) if frac_tokens else 0
            if fractional_number is None:
                return None
            fractional_number = int(fractional_number)
            if fractional_number == 0:
                return float(integer_part)

            divisor = 10 ** len(str(abs(fractional_number)))
            return integer_part + (fractional_number / divisor)

    number = _words_to_int(tokens)
    if number is None:
        return None

    return float(number) if allow_float else int(number)


# ============================================================================
# CHAT INTERFACE
# ============================================================================

def enhanced_chat_collect_profile():
    """
    Enhanced interactive chat to collect comprehensive user profile with voice support.

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

    # Voice mode toggle
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("""
        I'll ask you a series of questions to understand your needs and preferences.
        **All questions are optional** - you can skip any question by typing 'skip' or 'pass'.
        """)
    with col2:
        if 'profile_use_voice' not in st.session_state:
            st.session_state.profile_use_voice = False
        if st.button("🎤 Voice" if not st.session_state.profile_use_voice else "⌨️ Text",
                    use_container_width=True, key="profile_voice_btn"):
            st.session_state.profile_use_voice = not st.session_state.profile_use_voice
            # Reset chat when switching modes
            st.session_state.chat_messages = []
            st.session_state.chat_step = 0
            st.session_state.profile_data = {}
            st.session_state.question_asked_for_step = -1
            st.rerun()

    # Initialize session state
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
        st.session_state.profile_data = {}
        st.session_state.chat_step = 0
        st.session_state.profile_complete = False

    # Initialize question tracking separately to ensure it exists
    if 'question_asked_for_step' not in st.session_state:
        st.session_state.question_asked_for_step = -1  # Track which step we've asked a question for

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
        {
            "key": "zip_code",
            "question": "Do you want to search for colleges near you? Enter your 5-digit zip code, or type 'skip' to search all locations:",
            "type": "text"
        },
        {
            "key": "max_distance_from_home",
            "question": "How many miles away are you willing to travel for college? (e.g., 50, 100, 200, or 'any' for no limit)",
            "type": "float",
            "condition": lambda: st.session_state.profile_data.get('zip_code')
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
            "question": "Almost done! Rank these priorities from most to least important (or type 'default' for balanced):\n1. Affordability (cost and financial aid)\n2. Support Services (academic and non-academic support)\n3. Return on Investment (ROI) - earnings and graduation rates\n4. Equity & Diversity (support for diverse populations)\n5. Academic Fit (programs and rigor)\n6. Campus Environment (size, location, culture)\n7. Admission Likelihood (your chances of getting in)\n\nExample: 'Affordability, ROI, Support, Admission Likelihood'",
            "type": "text"
        }
    ]

    # Display chat history
    for idx, message in enumerate(st.session_state.chat_messages):
        with st.chat_message(message["role"]):
            st.write(message["content"])
            # Show audio player for assistant messages in voice mode
            if (message["role"] == "assistant" and
                "audio" in message and
                message["audio"] and
                st.session_state.profile_use_voice):
                if idx == len(st.session_state.chat_messages) - 1:
                    audio_b64 = base64.b64encode(message["audio"]).decode()
                    audio_id = f"profile_chat_audio_{idx}"
                    audio_html = f"""
                        <audio id="{audio_id}" autoplay>
                            <source src="data:audio/mpeg;base64,{audio_b64}" type="audio/mpeg">
                        </audio>
                        <script>
                            (function() {{
                                const audioEl = document.getElementById('{audio_id}');
                                if (!audioEl) return;
                                window.__equPathLatestAudio = audioEl;
                                if (!window.__equPathSpaceHandler) {{
                                    window.__equPathSpaceHandler = true;
                                    document.addEventListener('keydown', function(event) {{
                                        const tag = event.target.tagName;
                                        if (event.code === 'Space' && tag !== 'INPUT' && tag !== 'TEXTAREA' && !event.target.isContentEditable) {{
                                            event.preventDefault();
                                            const target = window.__equPathLatestAudio;
                                            if (target) {{
                                                target.currentTime = 0;
                                                target.play();
                                            }}
                                        }}
                                    }});
                                }}
                            }})();
                        </script>
                    """
                    st.markdown(audio_html, unsafe_allow_html=True)

    # Check if profile is complete
    if st.session_state.chat_step >= len(questions):
        if not st.session_state.profile_complete:
            # Build profile
            try:
                profile = build_profile_from_data(st.session_state.profile_data)
                st.session_state.user_profile = profile
                st.session_state.profile_complete = True

                with st.chat_message("assistant"):
                    completion_msg = "✅ Profile complete! Click 'Get Recommendations' in the sidebar to see your matches!"
                    st.success(completion_msg)

                    # Generate audio for completion
                    if st.session_state.profile_use_voice:
                        audio = generate_audio(completion_msg)
                        if audio:
                            st.audio(audio, format="audio/mpeg", autoplay=True)

                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": completion_msg,
                        "audio": generate_audio(completion_msg) if st.session_state.profile_use_voice else None
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

    # Check if we need to show the question (only once per step)
    if st.session_state.question_asked_for_step != st.session_state.chat_step:
        # Generate audio for question if in voice mode
        question_audio = None
        if st.session_state.profile_use_voice:
            with st.spinner("🔊 Generating voice..."):
                question_audio = generate_audio(current_q["question"])

        # Add question to chat history
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": current_q["question"],
            "audio": question_audio
        })
        st.session_state.question_asked_for_step = st.session_state.chat_step
        st.rerun()

    # User input - Voice or Text
    user_input = None

    # Check for pending voice input (from previous rerun)
    if 'pending_profile_input' in st.session_state and st.session_state.pending_profile_input:
        user_input = st.session_state.pending_profile_input
        st.session_state.pending_profile_input = None

    elif st.session_state.profile_use_voice:
        # Voice mode - show audio recorder
        st.markdown("**🎤 Click to start recording, then click stop when done:**")
        audio_value = st.audio_input("Record your answer", key="profile_audio")

        if audio_value:
            # Check if this audio was already processed
            if 'last_profile_audio' not in st.session_state:
                st.session_state.last_profile_audio = None

            # Only process if it's new audio
            if audio_value != st.session_state.last_profile_audio:
                st.session_state.last_profile_audio = audio_value

                with st.spinner("🎧 Transcribing your voice..."):
                    transcribed_text = transcribe_audio(audio_value)

                    if transcribed_text:
                        st.info(f"📝 You said: {transcribed_text}")
                        # Store in session state and rerun
                        st.session_state.pending_profile_input = transcribed_text
                        st.rerun()
                    else:
                        st.warning("⚠️ Could not transcribe audio - please try again")
    else:
        # Text mode
        user_input = st.chat_input("Your answer (or type 'skip' to skip optional questions)...")

    if user_input:
        # Add user message
        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_input
        })

        # Process answer
        processed_value = process_user_answer(user_input, current_q, st.session_state.profile_data)

        if processed_value is not None or user_input.lower().strip() in ['skip', 'pass']:
            # Store value
            if processed_value is not None:
                st.session_state.profile_data[current_q['key']] = processed_value

                # Update shared profile immediately with each answer
                from src.shared_profile_state import update_profile_from_data
                update_profile_from_data({current_q['key']: processed_value})

            # Move to next question
            st.session_state.chat_step += 1
            st.rerun()
        else:
            # Invalid answer, ask again with more helpful message
            q_type = current_q.get('type', 'text')

            if q_type == 'choice':
                options_list = ", ".join(current_q.get('options', []))
                error_msg = f"I didn't quite understand '{user_input}'.\n\n**Please choose from:** {options_list}\n\nOr type 'skip' to skip this question."
            elif q_type == 'float' or q_type == 'int':
                error_msg = f"I didn't quite understand '{user_input}'.\n\nPlease enter a **number**, or type 'skip' to skip this question."
            elif q_type == 'bool':
                error_msg = f"I didn't quite understand '{user_input}'.\n\nPlease answer **'yes' or 'no'**, or type 'skip' to skip this question."
            else:
                error_msg = "I didn't quite understand that. Could you try again, or type 'skip' to skip this question?"

            # Generate audio for error message if in voice mode
            error_audio = None
            if st.session_state.profile_use_voice:
                error_audio = generate_audio(error_msg)

            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": error_msg,
                "audio": error_audio
            })

            # Keep showing the same question - don't advance the step
            # The question won't be re-added because question_asked_for_step already equals chat_step
            st.rerun()


def process_user_answer(user_input, question_config, profile_data):
    """Process user answer based on question type."""
    user_input = user_input.strip()

    # Skip handling
    if user_input.lower() in ['skip', 'pass'] and not question_config.get('required'):
        return None

    q_type = question_config.get('type', 'text')

    try:
        if q_type == 'float':
            cleaned = ''.join(c for c in user_input if c.isdigit() or c == '.')
            if cleaned:
                try:
                    return float(cleaned)
                except ValueError:
                    pass
            spoken_value = parse_spoken_number(user_input, allow_float=True)
            return spoken_value

        elif q_type == 'int':
            cleaned = ''.join(c for c in user_input if c.isdigit())
            if cleaned:
                try:
                    return int(cleaned)
                except ValueError:
                    pass
            spoken_value = parse_spoken_number(user_input, allow_float=False)
            return spoken_value

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

            # Special handling for common variations
            # Use IF (not ELIF) so we only check relevant ones based on what options exist

            # Urbanization preferences
            if 'urban' in [opt.lower() for opt in options] or 'suburban' in [opt.lower() for opt in options]:
                if user_lower in ['city', 'big city', 'urban area']:
                    if 'urban' in [opt.lower() for opt in options]:
                        return 'urban'
                elif user_lower in ['suburb', 'suburbs', 'near city']:
                    if 'suburban' in [opt.lower() for opt in options]:
                        return 'suburban'
                elif user_lower in ['small town', 'town']:
                    if 'town' in [opt.lower() for opt in options]:
                        return 'town'
                elif user_lower in ['countryside', 'country', 'remote']:
                    if 'rural' in [opt.lower() for opt in options]:
                        return 'rural'

            # Size preferences
            if 'small' in [opt.lower() for opt in options] and 'medium' in [opt.lower() for opt in options]:
                if user_lower in ['tiny', 'very small']:
                    return 'small'
                elif user_lower in ['mid-size', 'medium-sized', 'moderate']:
                    return 'medium'
                elif user_lower in ['big', 'huge', 'very large']:
                    return 'large'

            # Institution type preferences
            if 'public' in [opt.lower() for opt in options] or 'private_nonprofit' in [opt.lower() for opt in options]:
                if user_lower in ['state', 'state school', 'public university']:
                    return 'public'
                elif user_lower in ['private', 'private school']:
                    return 'private_nonprofit'

            # MSI preferences
            if 'HBCU' in options or 'HSI' in options:
                if user_lower in ['historically black', 'black college']:
                    return 'HBCU'
                elif user_lower in ['hispanic serving', 'latino serving']:
                    return 'HSI'
                elif user_lower in ['tribal', 'native american']:
                    return 'Tribal'
                elif user_lower in ['any msi', 'minority serving']:
                    return 'any_MSI'

            # Major/field preferences
            if 'STEM' in options or 'Business' in options or 'Health' in options:
                if user_lower in ['science', 'technology', 'engineering', 'math', 'computer science', 'cs']:
                    return 'STEM'
                elif user_lower in ['business', 'finance', 'marketing', 'management', 'accounting']:
                    return 'Business'
                elif user_lower in ['medicine', 'nursing', 'healthcare', 'health']:
                    return 'Health'
                elif user_lower in ['social sciences', 'sociology', 'psychology', 'political science', 'economics']:
                    return 'Social Sciences'
                elif user_lower in ['liberal arts', 'humanities', 'arts', 'art', 'arts & humanities']:
                    return 'Arts & Humanities'
                elif user_lower in ['education', 'teaching']:
                    return 'Education'
                elif user_lower in ['not sure', 'unsure', 'don\'t know', "i don't know"]:
                    return 'Undecided'

            # Race/ethnicity preferences
            if 'BLACK' in options or 'HISPANIC' in options or 'ASIAN' in options:
                if user_lower in ['african american', 'black']:
                    return 'BLACK'
                elif user_lower in ['latino', 'latina', 'latinx', 'chicano', 'hispanic']:
                    return 'HISPANIC'
                elif user_lower in ['asian american', 'asian']:
                    return 'ASIAN'
                elif user_lower in ['native', 'indigenous', 'american indian']:
                    return 'NATIVE'
                elif user_lower in ['pacific islander', 'hawaiian']:
                    return 'PACIFIC'
                elif user_lower in ['multiracial', 'mixed', 'biracial']:
                    return 'TWO_OR_MORE'
                elif user_lower in ['skip', 'pass', 'rather not say']:
                    return 'PREFER_NOT_TO_SAY'

            # Test status
            if 'yes' in [opt.lower() for opt in options] and 'no' in [opt.lower() for opt in options]:
                if user_lower in ['took it', 'yes i have', 'submitted', 'yeah', 'yup', 'yep']:
                    return 'yes'
                elif user_lower in ['haven\'t taken', 'didn\'t take', 'no test', 'nope', 'nah']:
                    return 'no'
                elif user_lower in ['will take', 'plan to', 'going to', 'planning to']:
                    return 'planning'

            # Generic "no preference" variations
            if user_lower in ['any', 'either', 'no preference', "don't care", "doesn't matter", 'both']:
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

            # State name to code mapping
            state_map = {
                'california': 'CA', 'oregon': 'OR', 'washington': 'WA', 'texas': 'TX',
                'new york': 'NY', 'florida': 'FL', 'illinois': 'IL', 'pennsylvania': 'PA',
                'ohio': 'OH', 'georgia': 'GA', 'north carolina': 'NC', 'michigan': 'MI',
                'new jersey': 'NJ', 'virginia': 'VA', 'massachusetts': 'MA', 'arizona': 'AZ',
                'tennessee': 'TN', 'indiana': 'IN', 'missouri': 'MO', 'maryland': 'MD',
                'wisconsin': 'WI', 'colorado': 'CO', 'minnesota': 'MN', 'south carolina': 'SC',
                'alabama': 'AL', 'louisiana': 'LA', 'kentucky': 'KY', 'oklahoma': 'OK',
                'connecticut': 'CT', 'utah': 'UT', 'iowa': 'IA', 'nevada': 'NV',
                'arkansas': 'AR', 'mississippi': 'MS', 'kansas': 'KS', 'new mexico': 'NM',
                'nebraska': 'NE', 'west virginia': 'WV', 'idaho': 'ID', 'hawaii': 'HI',
                'new hampshire': 'NH', 'maine': 'ME', 'montana': 'MT', 'rhode island': 'RI',
                'delaware': 'DE', 'south dakota': 'SD', 'north dakota': 'ND', 'alaska': 'AK',
                'vermont': 'VT', 'wyoming': 'WY'
            }

            # Split by comma and "and"
            items = []
            for part in user_input.split(','):
                # Further split by "and"
                for subpart in part.split(' and '):
                    cleaned = subpart.strip().lower()
                    if cleaned:
                        # Check if it's a state name
                        if cleaned in state_map:
                            items.append(state_map[cleaned])
                        # Check if it's already a 2-letter code
                        elif len(cleaned) == 2:
                            items.append(cleaned.upper())
                        # Otherwise just take it as-is (uppercase)
                        else:
                            items.append(cleaned.upper())

            return items if items else []

        else:  # text
            return user_input

    except:
        return None


def build_profile_from_data(profile_data):
    """Build EnhancedUserProfile from collected data and update shared state."""
    from src.shared_profile_state import update_profile_from_data, build_profile_from_shared_state, mark_profile_complete

    # Map priorities to weights
    priorities_text = profile_data.get('priorities', 'default').lower()

    if 'default' in priorities_text:
        weights = {
            'weight_roi': 0.20,
            'weight_affordability': 0.25,
            'weight_equity': 0.18,
            'weight_support': 0.13,
            'weight_academic_fit': 0.13,
            'weight_environment': 0.06,
            'weight_access': 0.05
        }
    else:
        # Parse custom priorities with position-based weighting
        # Map matches the profile editor's weight fields exactly
        priority_map = {
            # ROI first since it was being underweighted
            'roi': 'weight_roi',
            'return on investment': 'weight_roi',
            'earnings': 'weight_roi',
            
            # Affordability
            'affordability': 'weight_affordability',
            'cost': 'weight_affordability',
            'financial aid': 'weight_affordability',
            
            # Equity & Diversity
            'equity': 'weight_equity',
            'diversity': 'weight_equity',
            'inclusion': 'weight_equity',
            
            # Student Support
            'support': 'weight_support',
            'student support': 'weight_support',
            'mentoring': 'weight_support',
            
            # Academic Fit
            'academic': 'weight_academic_fit',
            'major': 'weight_academic_fit',
            'program': 'weight_academic_fit',
            'rigor': 'weight_academic_fit',
            
            # Campus Environment
            'environment': 'weight_environment',
            'campus': 'weight_environment',
            'location': 'weight_environment',
            'culture': 'weight_environment',
            
            # Admission Likelihood
            'admission': 'weight_access',
            'access': 'weight_access',
            'likelihood': 'weight_access',
            'chance': 'weight_access',
            'getting in': 'weight_access'
        }

        # Start with equal base weights that match the profile editor's default distribution
        weights = {
            'weight_roi': 0.20,
            'weight_affordability': 0.25,
            'weight_equity': 0.18,
            'weight_support': 0.13,
            'weight_academic_fit': 0.13,
            'weight_environment': 0.06,
            'weight_access': 0.05
        }

        # Split and clean priorities
        priorities = [p.strip().lower() for p in priorities_text.split(',')]
        priorities = [p for p in priorities if p]  # Remove empty strings
        
        # Calculate weights based on position (earlier = higher weight)
        total_priority_weight = 0.0
        for i, priority in enumerate(priorities):
            # Higher weight for earlier positions (1.0, 0.5, 0.33, etc.)
            position_weight = 1.0 / (i + 1)
            total_priority_weight += position_weight
            
            # Find matching weight field
            for keyword, weight_field in priority_map.items():
                if keyword in priority:
                    weights[weight_field] += position_weight * 0.25  # Scale factor
        
        # Normalize to ensure weights sum to 1.0
        if total_priority_weight > 0:
            total = sum(weights.values())
            if total > 0:
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

    # Prepare data for shared state
    shared_data = {
        # Academic
        'gpa': profile_data.get('gpa', 3.0),
        'test_score_status': test_status,
        'sat_score': profile_data.get('sat_score'),
        'act_score': profile_data.get('act_score'),
        'intended_major': profile_data.get('intended_major', 'Undecided'),

        # Financial
        'annual_budget': profile_data.get('annual_budget', 20000),
        'family_income': family_income,
        'earnings_ceiling_match': earnings_ceiling,
        'work_study_needed': profile_data.get('work_study_needed', False),

        # Demographics
        'race_ethnicity': profile_data.get('race_ethnicity', 'PREFER_NOT_TO_SAY'),
        'age': profile_data.get('age'),

        # Special populations
        'is_first_gen': profile_data.get('is_first_gen', False),
        'is_student_parent': profile_data.get('is_student_parent', False),
        'is_international': profile_data.get('is_international', False),

        # Geographic
        'home_state': profile_data.get('home_state'),
        'in_state_only': profile_data.get('in_state_only', False),
        'preferred_states': profile_data.get('preferred_states', []),
        'zip_code': profile_data.get('zip_code'),
        'max_distance_from_home': profile_data.get('max_distance_from_home'),

        # Environment
        'urbanization_pref': profile_data.get('urbanization_pref', 'no_preference'),
        'size_pref': profile_data.get('size_pref', 'no_preference'),
        'institution_type_pref': profile_data.get('institution_type_pref', 'either'),
        'msi_preference': profile_data.get('msi_preference', 'no_preference'),

        # Academic priorities
        'research_opportunities': profile_data.get('research_opportunities', False),
        'small_class_sizes': profile_data.get('small_class_sizes', False),
        'strong_support_services': profile_data.get('strong_support_services', False),

        # Weights
        **weights
    }

    # Update shared profile state
    update_profile_from_data(shared_data)
    mark_profile_complete()

    # Build and return profile from shared state
    profile = build_profile_from_shared_state()

    return profile


def generate_college_summary(row, profile, client):
    """Generate AI summary for a specific college."""
    if not client:
        return None

    # Helper function to safely get values
    def safe_get(series, key, default='N/A'):
        try:
            if key in series.index:
                val = series[key]
                if pd.isna(val):
                    return default
                return val
            return default
        except:
            return default

    # Try different possible column names
    inst_name = (
        safe_get(row, 'Institution Name', None) or
        safe_get(row, 'Institution Name_CR', None) or
        safe_get(row, 'Institution Name_AG', None) or
        safe_get(row, 'INSTNM', 'Unknown')
    )

    state = (
        safe_get(row, 'State of Institution', None) or
        safe_get(row, 'State of Institution_CR', None) or
        safe_get(row, 'State of Institution_AG', 'N/A')
    )

    college_data = {
        "name": inst_name,
        "state": state,
        "match_score": float(safe_get(row, 'composite_score', 0)),
        "net_price": float(pd.to_numeric(safe_get(row, 'Net Price', 0), errors='coerce')),
        "median_debt": float(pd.to_numeric(safe_get(row, 'Median Debt of Completers', 0), errors='coerce')),
        "median_earnings": float(pd.to_numeric(safe_get(row, 'Median Earnings of Students Working and Not Enrolled 10 Years After Entry', 0), errors='coerce')),
    }

    prompt = f"""As a college advisor, write a brief 2-3 sentence summary of why {college_data['name']} is a good match for this student:

Student: {profile.race_ethnicity}, {'student-parent' if profile.is_student_parent else 'non-parent'}, {'first-generation' if profile.is_first_gen else 'continuing-generation'}, {profile.annual_budget:,.0f} budget, {profile.gpa} GPA

College:
- Match Score: {college_data['match_score']:.3f}
- Net Price: {college_data['net_price']:,.0f}
- Median Earnings (10yr): {college_data['median_earnings']:,.0f}

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


# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

def display_recommendations(recommendations, profile, df, client, df_merged=None):
    """Display ranked recommendations with enhanced details and Q&A chatbot."""

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

            # Generate AI summary for this college
            if client:
                with st.spinner("Generating college summary..."):
                    college_summary = generate_college_summary(college, profile, client)
                    if college_summary:
                        st.info(f"💡 **Why this college?** {college_summary}")
                        st.divider()

            # Key metrics at the top
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Match Score", f"{safe_get(college, 'composite_score', 0):.3f}")

            with col2:
                net_price = (safe_get(college, 'Net Price', None) or safe_get(college, 'Average Net Price', None))
                st.metric("Net Price", format_currency(net_price))

            with col3:
                earnings = safe_get(college, 'Median Earnings of Students Working and Not Enrolled 10 Years After Entry', None)
                st.metric("10-Year Earnings", format_currency(earnings))

            with col4:
                debt = (safe_get(college, 'Median Debt of Completers', None) or
                       safe_get(college, 'Median Debt of Completers_CR', None))
                st.metric("Median Debt", format_currency(debt))

            # Personalized scores
            st.markdown("**Your Personalized Fit Scores:**")
            col1, col2, col3, col4, col5, col6 = st.columns(6)

            with col1:
                st.metric("Affordability", f"{safe_get(college, 'personalized_affordability', 0):.2f}")
            with col2:
                st.metric("ROI", f"{safe_get(college, 'roi_score', 0):.2f}")
            with col3:
                st.metric("Equity", f"{safe_get(college, 'personalized_equity', 0):.2f}")
            with col4:
                st.metric("Support", f"{safe_get(college, 'personalized_support', 0):.2f}")
            with col5:
                st.metric("Academic", f"{safe_get(college, 'personalized_academic_fit', 0):.2f}")
            with col6:
                st.metric("Environment", f"{safe_get(college, 'personalized_environment', 0):.2f}")

            # Details
            st.markdown("### 📊 Additional Details")
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**📍 Location & Environment**")
                # Try both with and without suffixes
                city = (safe_get(college, 'City', None) or
                       safe_get(college, 'City_CR', None) or
                       safe_get(college, 'City_AG', 'N/A'))
                state = (safe_get(college, 'State of Institution', None) or
                        safe_get(college, 'State of Institution_CR', None) or
                        safe_get(college, 'STABBR', 'N/A'))
                st.write(f"**Location:** {city}, {state}")

                # Get control/type properly
                control = safe_get(college, 'Control of Institution', None) or safe_get(college, 'Control of Institution_CR', None)
                if pd.notna(control):
                    # Map numeric codes to text if needed
                    control_map = {1: 'Public', 2: 'Private nonprofit', 3: 'Private for-profit'}
                    if isinstance(control, (int, float)):
                        control = control_map.get(int(control), 'Unknown')
                    st.write(f"**Type:** {control}")
                # Show distance if available
                distance = safe_get(college, 'distance_miles', None)
                if distance and not pd.isna(distance):
                    st.write(f"**Distance:** {distance:.1f} miles from you")

                size_val = (safe_get(college, 'Institution Size Category_CR', None) or
                           safe_get(college, 'size_category', None) or
                           safe_get(college, 'Institution Size Category', None))
                st.write(f"**Size:** {format_size(size_val)}")

                urban_val = (safe_get(college, 'Degree of Urbanization', None) or
                            safe_get(college, 'urbanization', None))
                st.write(f"**Setting:** {format_urbanization(urban_val)}")

                # Total enrollment
                enrollment = safe_get(college, 'Undergraduate Enrollment', None)
                if enrollment and pd.notna(enrollment):
                    st.write(f"**Enrollment:** {int(enrollment):,} students")

                # Distance from home (if available)
                distance = safe_get(college, 'Distance from Home', None)
                if distance and pd.notna(distance):
                    st.write(f"**Distance:** {int(distance)} miles")

            with col2:
                st.markdown("**🎓 Academic Success & Value**")

                grad_rate = (
                    safe_get(college, "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total", None) or
                    safe_get(college, "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total_CR", None) or
                    safe_get(college, "Bachelor's Degree Graduation Rate Within 6 Years - Total", None) or
                    safe_get(college, "Bachelor's Degree Graduation Rate Within 6 Years - Total_CR", None)
                )
                st.write(f"**Graduation Rate:** {format_percentage(grad_rate)}")

                selectivity = safe_get(college, 'selectivity_bucket', 'Unknown')
                st.write(f"**Selectivity:** {selectivity}")

                admit_rate = safe_get(college, 'Total Percent of Applicants Admitted', None)
                st.write(f"**Admission Rate:** {format_percentage(admit_rate)}")

                st.write(f"**10-Year Earnings:** {format_currency(earnings)}")
                st.write(f"**Median Debt:** {format_currency(debt)}")

                # Calculate simple earnings/debt ratio if both available
                if earnings and debt and not pd.isna(earnings) and not pd.isna(debt) and debt > 0:
                    ratio = earnings / debt
                    st.write(f"**Earnings/Debt Ratio:** {ratio:.1f}x")

    # Visualization
    st.divider()
    st.subheader("📈 Visual Comparison")

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
        title="Affordability vs. Equity"
    )
    # Prepare data for visualization with fallback columns
    viz_data = recommendations.head(10).copy()

    # Determine which columns to use based on availability
    x_col = 'personalized_affordability' if 'personalized_affordability' in viz_data.columns else 'composite_score'
    y_col = 'personalized_equity' if 'personalized_equity' in viz_data.columns else 'composite_score'
    size_col = 'personalized_roi' if 'personalized_roi' in viz_data.columns else None
    color_col = 'composite_score' if 'composite_score' in viz_data.columns else None
    name_col = 'Institution Name' if 'Institution Name' in viz_data.columns else ('Institution Name_CR' if 'Institution Name_CR' in viz_data.columns else 'INSTNM')

    # Create scatter plot
    if size_col and size_col in viz_data.columns and color_col and color_col in viz_data.columns:
        fig = px.scatter(
            viz_data,
            x=x_col,
            y=y_col,
            size=size_col,
            color=color_col,
            hover_name=name_col if name_col in viz_data.columns else None,
            labels={
                x_col: 'Affordability',
                y_col: 'Equity',
                color_col: 'Match Score',
                size_col: 'ROI'
            },
            title="Affordability vs. Equity"
        )
    else:
        # Fallback version with just x, y, and color
        fig = px.scatter(
            viz_data,
            x=x_col,
            y=y_col,
            color=color_col if color_col and color_col in viz_data.columns else None,
            hover_name=name_col if name_col in viz_data.columns else None,
            labels={
                x_col: 'Affordability',
                y_col: 'Equity',
            },
            title="College Comparison"
        )
    st.plotly_chart(fig, use_container_width=True)

    # Community College Pathway Comparison
    if df_merged is not None:
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

    # Voice mode toggle
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("Have questions about these schools or want to know about other colleges? Ask me anything!")
    with col2:
        if 'use_voice_qa' not in st.session_state:
            st.session_state.use_voice_qa = False
        if st.button("🎤 Voice" if not st.session_state.use_voice_qa else "⌨️ Text",
                    use_container_width=True, key="qa_voice_btn"):
            st.session_state.use_voice_qa = not st.session_state.use_voice_qa
            st.rerun()

    # Initialize Q&A chat history
    if 'qa_messages' not in st.session_state:
        st.session_state.qa_messages = []

    # Display Q&A chat history
    for idx, msg in enumerate(st.session_state.qa_messages):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            # Show audio player for assistant messages in voice mode
            if (msg["role"] == "assistant" and
                "audio" in msg and
                msg["audio"] and
                st.session_state.use_voice_qa):
                if idx == len(st.session_state.qa_messages) - 1:
                    audio_b64 = base64.b64encode(msg["audio"]).decode()
                    audio_id = f"qa_chat_audio_{idx}"
                    audio_html = f"""
                        <audio id="{audio_id}" autoplay>
                            <source src="data:audio/mpeg;base64,{audio_b64}" type="audio/mpeg">
                        </audio>
                        <script>
                            (function() {{
                                const audioEl = document.getElementById('{audio_id}');
                                if (!audioEl) return;
                                window.__equPathLatestAudio = audioEl;
                                if (!window.__equPathSpaceHandler) {{
                                    window.__equPathSpaceHandler = true;
                                    document.addEventListener('keydown', function(event) {{
                                        const tag = event.target.tagName;
                                        if (event.code === 'Space' && tag !== 'INPUT' && tag !== 'TEXTAREA' && !event.target.isContentEditable) {{
                                            event.preventDefault();
                                            const target = window.__equPathLatestAudio;
                                            if (target) {{
                                                target.currentTime = 0;
                                                target.play();
                                            }}
                                        }}
                                    }});
                                }}
                            }})();
                        </script>
                    """
                    st.markdown(audio_html, unsafe_allow_html=True)

    # Q&A input
    if client:
        user_question = None

        # Check for pending voice input
        if 'pending_qa_input' in st.session_state and st.session_state.pending_qa_input:
            user_question = st.session_state.pending_qa_input
            st.session_state.pending_qa_input = None

        # Voice input
        if st.session_state.use_voice_qa and not user_question:
            st.markdown("**🎤 Click to start recording, then click stop when done:**")
            audio_value = st.audio_input("Record your question", key="qa_audio")

            if audio_value:
                # Check if this audio was already processed
                if 'last_qa_audio' not in st.session_state:
                    st.session_state.last_qa_audio = None

                # Only process if it's new audio
                if audio_value != st.session_state.last_qa_audio:
                    st.session_state.last_qa_audio = audio_value

                    with st.spinner("🎧 Transcribing your voice..."):
                        transcribed_text = transcribe_audio(audio_value)
                        if transcribed_text:
                            st.info(f"📝 You asked: {transcribed_text}")
                            st.session_state.pending_qa_input = transcribed_text
                            st.rerun()
                        else:
                            st.warning("⚠️ Could not transcribe audio - please try again")
        elif not st.session_state.use_voice_qa and not user_question:
            # Text input
            user_question = st.chat_input("Ask about colleges, compare schools, or request more information...")

        if user_question:
            # Add user message
            st.session_state.qa_messages.append({"role": "user", "content": user_question})

            # Build context with profile and recommendations
            context = f"""
Student Profile:
- Budget: {profile.annual_budget:,.0f}
- GPA: {profile.gpa}
- State: {profile.home_state or 'Not specified'}
- Preferences: {'In-state only, ' if profile.in_state_only else ''}{'Public only, ' if profile.institution_type_pref == 'public' else ''}{profile.size_pref or 'Any size'}

Recommended Colleges:
{chr(10).join([f"{i+1}. {row.get('Institution Name', row.get('INSTNM', 'Unknown'))} (State: {row.get('State of Institution', 'N/A')}, Match Score: {row.get('composite_score', 0):.3f})" for i, (_, row) in enumerate(recommendations.head(10).iterrows())])}

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

                    # Generate audio if in voice mode
                    response_audio = None
                    if st.session_state.use_voice_qa:
                        with st.spinner("🔊 Generating voice response..."):
                            response_audio = generate_audio(ai_response)

                    st.session_state.qa_messages.append({
                        "role": "assistant",
                        "content": ai_response,
                        "audio": response_audio
                    })

                    # Trigger rerun to show the message with audio
                    st.rerun()

                except Exception as e:
                    st.error(f"Error generating response: {str(e)}")
    else:
        st.info("💡 Chat requires an API key. Add your Anthropic API key to enable this feature.")


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    st.set_page_config(page_title="EquiPath - Enhanced", layout="wide", page_icon="🎓")

    st.title("🎓 EquiPath - Your Personalized College Guide")
    st.markdown("**Enhanced Edition** - Comprehensive equity-aware college matching with voice support")

    # Check for required packages
    if not ANTHROPIC_AVAILABLE:
        st.error("⚠️ Anthropic package not installed. Install with: pip install anthropic")
        st.stop()

    # Sidebar
    st.sidebar.header("Navigation")
    mode = st.sidebar.radio("Choose Mode:", ["Build Profile (Chat)", "Get Recommendations", "About"])

    if st.sidebar.button("🔄 Reset / Start Over"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    client = get_anthropic_client()

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
                # Load data with zip code and distance filtering if provided
                colleges_df = load_enhanced_data(
                    earnings_ceiling=profile.earnings_ceiling_match,
                    zip_code=profile.zip_code,
                    max_distance=profile.max_distance_from_home
                )
                df_merged = load_pathway_data()
                recommendations = rank_colleges_for_user(colleges_df, profile, top_k=15)

        if len(recommendations) > 0:
            display_recommendations(recommendations, profile, colleges_df, client, df_merged)
        else:
            st.error("❌ No colleges match your criteria.")
            st.warning("**Try these adjustments:**")
            st.markdown("""
            1. **Increase your budget** - Current: ${:,.0f}
            2. **Remove geographic restrictions** - Try expanding beyond your current region/state preferences
            3. **Set preferences to 'no preference'** - Urbanization, size, institution type
            4. **Include more selectivity levels** - Make sure you're including reach, target, safety, AND open admission schools

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

        ### The Team
        Built for the Educational Equity Datathon 2025
        """)


if __name__ == "__main__":
    main()
