"""
Shared Profile State Management for EquiPath

This module manages the user profile across all Streamlit pages/tabs,
ensuring consistency and allowing the profile to be built incrementally
through the chat interface and edited manually.
"""

import streamlit as st
from src.enhanced_user_profile import EnhancedUserProfile


def initialize_shared_profile():
    """
    Initialize the shared profile in session state if it doesn't exist.
    This should be called at the start of each page.
    """
    if 'shared_profile' not in st.session_state:
        st.session_state.shared_profile = None

    if 'shared_profile_data' not in st.session_state:
        # Store raw profile data that can be edited
        st.session_state.shared_profile_data = {
            # Academic
            'gpa': 3.0,
            'sat_score': None,
            'act_score': None,
            'test_score_status': 'test_optional',
            'intended_major': 'Undecided',

            # Financial
            'annual_budget': 25000,
            'family_income': None,
            'earnings_ceiling_match': 30000.0,
            'work_study_needed': False,

            # Demographics
            'race_ethnicity': 'PREFER_NOT_TO_SAY',
            'age': None,

            # Special populations
            'is_first_gen': False,
            'is_student_parent': False,
            'is_international': False,

            # Geographic
            'home_state': None,
            'in_state_only': False,
            'preferred_states': [],

            # Environment
            'urbanization_pref': 'no_preference',
            'size_pref': 'no_preference',
            'institution_type_pref': 'either',
            'msi_preference': 'no_preference',

            # Academic priorities
            'research_opportunities': False,
            'small_class_sizes': False,
            'strong_support_services': False,

            # Weights
            'weight_roi': 0.20,
            'weight_affordability': 0.25,
            'weight_equity': 0.18,
            'weight_support': 0.13,
            'weight_academic_fit': 0.13,
            'weight_environment': 0.06,
            'weight_access': 0.05
        }

    if 'profile_complete' not in st.session_state:
        st.session_state.profile_complete = False


def update_profile_from_data(profile_data):
    """
    Update the shared profile data with new values from the chat interface.

    Parameters:
    -----------
    profile_data : dict
        Dictionary of profile fields and values
    """
    initialize_shared_profile()

    # Update only the fields that are provided
    for key, value in profile_data.items():
        if key in st.session_state.shared_profile_data:
            st.session_state.shared_profile_data[key] = value


def build_profile_from_shared_state():
    """
    Build an EnhancedUserProfile object from the shared state.

    Returns:
    --------
    EnhancedUserProfile
        Profile object built from current shared state
    """
    initialize_shared_profile()

    data = st.session_state.shared_profile_data

    try:
        profile = EnhancedUserProfile(
            # Required
            gpa=data['gpa'],
            annual_budget=data['annual_budget'],

            # Academic
            test_score_status=data['test_score_status'],
            sat_score=data['sat_score'],
            act_score=data['act_score'],
            intended_major=data['intended_major'],

            # Financial
            family_income=data['family_income'],
            earnings_ceiling_match=data['earnings_ceiling_match'],
            work_study_needed=data['work_study_needed'],

            # Demographics
            race_ethnicity=data['race_ethnicity'],
            age=data['age'],

            # Special populations
            is_first_gen=data['is_first_gen'],
            is_student_parent=data['is_student_parent'],
            is_international=data['is_international'],

            # Geographic
            home_state=data['home_state'],
            in_state_only=data['in_state_only'],
            preferred_states=data['preferred_states'],

            # Environment
            urbanization_pref=data['urbanization_pref'],
            size_pref=data['size_pref'],
            institution_type_pref=data['institution_type_pref'],
            msi_preference=data['msi_preference'],

            # Academic priorities
            research_opportunities=data['research_opportunities'],
            small_class_sizes=data['small_class_sizes'],
            strong_support_services=data['strong_support_services'],

            # Weights
            weight_roi=data['weight_roi'],
            weight_affordability=data['weight_affordability'],
            weight_equity=data['weight_equity'],
            weight_support=data['weight_support'],
            weight_academic_fit=data['weight_academic_fit'],
            weight_environment=data['weight_environment'],
            weight_access=data['weight_access']
        )

        st.session_state.shared_profile = profile
        return profile

    except Exception as e:
        st.error(f"Error building profile: {e}")
        return None


def get_shared_profile():
    """
    Get the current shared profile, building it from state if needed.

    Returns:
    --------
    EnhancedUserProfile or None
        Current profile object
    """
    initialize_shared_profile()

    if st.session_state.shared_profile is None:
        return build_profile_from_shared_state()

    return st.session_state.shared_profile


def mark_profile_complete():
    """Mark the profile as complete."""
    st.session_state.profile_complete = True


def is_profile_complete():
    """Check if the profile is complete (all questions answered)."""
    return st.session_state.get('profile_complete', False)


def has_minimum_profile():
    """Check if we have enough profile data for basic recommendations."""
    if 'shared_profile_data' not in st.session_state:
        return False

    data = st.session_state.shared_profile_data

    # Minimum required: GPA and budget
    has_gpa = data.get('gpa') is not None and data.get('gpa') > 0
    has_budget = data.get('annual_budget') is not None and data.get('annual_budget') > 0

    return has_gpa and has_budget


def reset_shared_profile():
    """Reset the shared profile to default values."""
    if 'shared_profile' in st.session_state:
        del st.session_state.shared_profile
    if 'shared_profile_data' in st.session_state:
        del st.session_state.shared_profile_data
    if 'profile_complete' in st.session_state:
        del st.session_state.profile_complete
    initialize_shared_profile()
