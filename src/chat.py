"""
Conversational profile builder for EquiPath.

Walks the student through a guided chat that fills in every UserProfile
dimension (academics, budget, background, geography, environment preferences,
and scoring priorities), with optional voice input/output via ElevenLabs.
Answers sync to the shared profile state so every page sees the same profile.
"""

import base64
import os
import re

import streamlit as st

from src.profile_state import (
    build_profile_from_shared_state,
    mark_profile_complete,
    update_profile_from_data,
)

try:
    from elevenlabs import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False


# ============================================================================
# VOICE (ElevenLabs)
# ============================================================================

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



def render_chat_profile_builder():
    """
    Interactive chat that collects a comprehensive user profile, with voice support.

    Covers all UserProfile dimensions:
    - Academic background (GPA, test scores, major)
    - Financial situation (budget, income, Pell eligibility)
    - Demographics (race, gender, age - handled sensitively)
    - Special populations (first-gen, student-parent, international, nontraditional)
    - Geographic preferences
    - Environment preferences (size, urbanization, MSI interest)
    - Academic priorities (research, class size, support)
    - Scoring weight preferences
    """
    st.subheader("💬 Chat with EquiPath")

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
    """Build a UserProfile from collected answers and update shared state."""

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
