"""
Profile Editor Component for EquiPath

Provides an interactive UI for viewing and editing the user profile.
"""

import streamlit as st
from src.shared_profile_state import initialize_shared_profile, build_profile_from_shared_state


def render_profile_editor():
    """
    Render an interactive profile editor in the Streamlit app.
    Allows users to view and modify all profile fields.
    """
    initialize_shared_profile()
    data = st.session_state.shared_profile_data

    st.subheader("📝 Edit Your Profile")
    st.markdown("Make changes to your profile below. Changes are saved automatically and apply across all tabs.")

    # Academic Background
    with st.expander("🎓 Academic Background", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            data['gpa'] = st.number_input(
                "GPA (0.0-4.0)",
                min_value=0.0,
                max_value=4.0,
                value=float(data['gpa']),
                step=0.1,
                key="edit_gpa"
            )

            data['test_score_status'] = st.selectbox(
                "Test Score Status",
                options=['submitted', 'no_test', 'test_optional'],
                index=['submitted', 'no_test', 'test_optional'].index(data['test_score_status']),
                key="edit_test_status"
            )

        with col2:
            data['intended_major'] = st.selectbox(
                "Intended Major",
                options=['STEM', 'Business', 'Health', 'Social Sciences', 'Arts & Humanities', 'Education', 'Undecided'],
                index=['STEM', 'Business', 'Health', 'Social Sciences', 'Arts & Humanities', 'Education', 'Undecided'].index(data['intended_major']) if data['intended_major'] in ['STEM', 'Business', 'Health', 'Social Sciences', 'Arts & Humanities', 'Education', 'Undecided'] else 6,
                key="edit_major"
            )

        if data['test_score_status'] == 'submitted':
            col1, col2 = st.columns(2)
            with col1:
                sat = st.number_input(
                    "SAT Score (optional, 400-1600)",
                    min_value=400,
                    max_value=1600,
                    value=int(data['sat_score']) if data['sat_score'] else 1000,
                    step=10,
                    key="edit_sat"
                )
                data['sat_score'] = sat if sat > 400 else None

            with col2:
                act = st.number_input(
                    "ACT Score (optional, 1-36)",
                    min_value=1,
                    max_value=36,
                    value=int(data['act_score']) if data['act_score'] else 20,
                    step=1,
                    key="edit_act"
                )
                data['act_score'] = act if act > 1 else None

    # Financial Situation
    with st.expander("💰 Financial Situation", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            data['annual_budget'] = st.number_input(
                "Annual Budget ($)",
                min_value=0,
                max_value=200000,
                value=int(data['annual_budget']),
                step=1000,
                key="edit_budget"
            )

            data['work_study_needed'] = st.checkbox(
                "Need work-study opportunities",
                value=bool(data['work_study_needed']),
                key="edit_work_study"
            )

        with col2:
            family_income = st.number_input(
                "Family Income (optional, $)",
                min_value=0,
                max_value=500000,
                value=int(data['family_income']) if data['family_income'] else 0,
                step=5000,
                key="edit_income"
            )
            data['family_income'] = family_income if family_income > 0 else None

            # Auto-calculate earnings ceiling based on income
            if data['family_income']:
                if data['family_income'] <= 30000:
                    data['earnings_ceiling_match'] = 30000.0
                elif data['family_income'] <= 48000:
                    data['earnings_ceiling_match'] = 48000.0
                elif data['family_income'] <= 75000:
                    data['earnings_ceiling_match'] = 75000.0
                elif data['family_income'] <= 110000:
                    data['earnings_ceiling_match'] = 110000.0
                else:
                    data['earnings_ceiling_match'] = 150000.0

    # Demographics & Background
    with st.expander("👤 Demographics & Background"):
        col1, col2 = st.columns(2)

        with col1:
            data['race_ethnicity'] = st.selectbox(
                "Race/Ethnicity (optional, used for relevant graduation rates)",
                options=['BLACK', 'HISPANIC', 'WHITE', 'ASIAN', 'NATIVE', 'PACIFIC', 'TWO_OR_MORE', 'PREFER_NOT_TO_SAY'],
                index=['BLACK', 'HISPANIC', 'WHITE', 'ASIAN', 'NATIVE', 'PACIFIC', 'TWO_OR_MORE', 'PREFER_NOT_TO_SAY'].index(data['race_ethnicity']) if data['race_ethnicity'] in ['BLACK', 'HISPANIC', 'WHITE', 'ASIAN', 'NATIVE', 'PACIFIC', 'TWO_OR_MORE', 'PREFER_NOT_TO_SAY'] else 7,
                key="edit_race"
            )

            data['is_first_gen'] = st.checkbox(
                "First-generation college student",
                value=bool(data['is_first_gen']),
                key="edit_first_gen"
            )

        with col2:
            age = st.number_input(
                "Age (optional)",
                min_value=14,
                max_value=100,
                value=int(data['age']) if data['age'] else 18,
                step=1,
                key="edit_age"
            )
            data['age'] = age if age > 14 else None

            data['is_student_parent'] = st.checkbox(
                "Student-parent (have dependent children)",
                value=bool(data['is_student_parent']),
                key="edit_parent"
            )

        data['is_international'] = st.checkbox(
            "International student",
            value=bool(data['is_international']),
            key="edit_international"
        )

    # Geographic Preferences
    with st.expander("🗺️ Geographic Preferences"):
        col1, col2 = st.columns(2)

        with col1:
            home_state = st.text_input(
                "Home State (2-letter code, e.g., CA)",
                value=data['home_state'] if data['home_state'] else '',
                max_chars=2,
                key="edit_home_state"
            ).upper()
            data['home_state'] = home_state if home_state else None

            data['in_state_only'] = st.checkbox(
                "Only consider in-state schools",
                value=bool(data['in_state_only']),
                key="edit_in_state",
                disabled=not data['home_state']
            )

        with col2:
            preferred = st.text_input(
                "Preferred States (comma-separated, e.g., CA,NY,TX)",
                value=','.join(data['preferred_states']) if data['preferred_states'] else '',
                key="edit_preferred_states"
            )
            data['preferred_states'] = [s.strip().upper() for s in preferred.split(',') if s.strip()] if preferred else []
            
            # Add zip code for distance-based filtering
            zip_code = st.text_input(
                "ZIP Code (for distance filtering)",
                value=data.get('zip_code', ''),
                key="edit_zip_code"
            )
            data['zip_code'] = zip_code if zip_code.strip() else None
            
            if data['zip_code']:
                data['max_distance_from_home'] = st.slider(
                    "Maximum distance from home (miles)",
                    min_value=10,
                    max_value=500,
                    value=int(data.get('max_distance_from_home', 100)) if data.get('max_distance_from_home') else 100,
                    step=10,
                    key="edit_max_distance"
                )

    # Environment Preferences
    with st.expander("🏫 Environment Preferences"):
        col1, col2 = st.columns(2)

        with col1:
            data['urbanization_pref'] = st.selectbox(
                "Setting Preference",
                options=['urban', 'suburban', 'town', 'rural', 'no_preference'],
                index=['urban', 'suburban', 'town', 'rural', 'no_preference'].index(data['urbanization_pref']) if data['urbanization_pref'] in ['urban', 'suburban', 'town', 'rural', 'no_preference'] else 4,
                key="edit_urban"
            )

            data['size_pref'] = st.selectbox(
                "School Size Preference",
                options=['small', 'medium', 'large', 'no_preference'],
                index=['small', 'medium', 'large', 'no_preference'].index(data['size_pref']) if data['size_pref'] in ['small', 'medium', 'large', 'no_preference'] else 3,
                key="edit_size"
            )

        with col2:
            data['institution_type_pref'] = st.selectbox(
                "Institution Type",
                options=['public', 'private_nonprofit', 'either'],
                index=['public', 'private_nonprofit', 'either'].index(data['institution_type_pref']) if data['institution_type_pref'] in ['public', 'private_nonprofit', 'either'] else 2,
                key="edit_type"
            )

            data['msi_preference'] = st.selectbox(
                "Minority-Serving Institution Preference",
                options=['HBCU', 'HSI', 'Tribal', 'any_MSI', 'no_preference'],
                index=['HBCU', 'HSI', 'Tribal', 'any_MSI', 'no_preference'].index(data['msi_preference']) if data['msi_preference'] in ['HBCU', 'HSI', 'Tribal', 'any_MSI', 'no_preference'] else 4,
                key="edit_msi"
            )

    # Academic Priorities
    with st.expander("🎯 Academic Priorities"):
        data['research_opportunities'] = st.checkbox(
            "Research opportunities important",
            value=bool(data['research_opportunities']),
            key="edit_research"
        )

        data['small_class_sizes'] = st.checkbox(
            "Prefer small class sizes",
            value=bool(data['small_class_sizes']),
            key="edit_class_size"
        )

        data['strong_support_services'] = st.checkbox(
            "Strong student support services important",
            value=bool(data['strong_support_services']),
            key="edit_support"
        )

    # Scoring Weights
    with st.expander("⚖️ Priority Settings", expanded=True):
        st.markdown("""
        ### Set Your Priorities
        Adjust the importance of each factor in your recommendations. The percentages will be automatically normalized to total 100%.
        """)

        # Define all weight fields with descriptions
        weight_fields = [
            ('weight_affordability', "Affordability", "Cost of attendance and financial aid availability"),
            ('weight_roi', "Return on Investment (ROI)", "Graduation rates and post-graduation earnings"),
            ('weight_equity', "Equity & Diversity", "Support for diverse student populations and equitable outcomes"),
            ('weight_support', "Student Support", "Academic and non-academic support services"),
            ('weight_academic_fit', "Academic Fit", "Match with your intended major and academic rigor"),
            ('weight_environment', "Campus Environment", "Campus culture, location, and facilities"),
            ('weight_access', "Access Score", "How much to prioritize schools where you're more likely to be admitted")
        ]

        # Get current weights and normalize to ensure they sum to 1.0
        current_weights = {field: float(data[field]) for field, _, _ in weight_fields}
        total_weight = sum(current_weights.values())
        if abs(total_weight - 1.0) > 0.001:
            current_weights = {k: v/total_weight for k, v in current_weights.items()}
        
        # Display sliders for all weights
        new_weights = {}
        for field, label, help_text in weight_fields:
            # Calculate current percentage (0-100)
            current_percent = current_weights[field] * 100
            
            # Create slider for this weight
            new_percent = st.slider(
                f"{label} (%)",
                0.0, 100.0,
                value=round(current_percent, 1),
                step=0.5,
                format="%.1f%%",
                key=f"edit_{field}",
                help=help_text
            )
            new_weights[field] = new_percent / 100.0
        
        # Normalize the weights to ensure they sum to 1.0
        total = sum(new_weights.values())
        if total > 0:
            new_weights = {k: v/total for k, v in new_weights.items()}
        
        # Display the actual normalized weights to the user
        st.markdown("### Normalized Weights")
        for field, label, _ in weight_fields:
            percent = new_weights[field] * 100
            st.metric(
                label=f"{label} (normalized)",
                value=f"{percent:.1f}%"
            )
        
        # Update all weights in data
        for field in new_weights:
            data[field] = new_weights[field]
            
        st.markdown("""
        **How these weights work:**
        - Higher weights mean this factor will have more influence on your recommendations
        - We'll automatically adjust the weights to ensure they total 100%
        - You can fine-tune individual weights using the sliders above
        """)
        
        # The weights are already normalized in the code above, so we don't need to do it again
        # Just ensure they're properly set in the data dictionary
        for field in new_weights:
            data[field] = new_weights[field]

    # Rebuild profile from updated data
    build_profile_from_shared_state()

    return data
