"""
Enhanced Personalized Scoring Logic for EquiPath Project

Extends the base scoring with comprehensive indices:
- Support Infrastructure
- Academic Offerings (field-specific)
- Environment fit
- Selectivity matching

Maps (college, enhanced_user_profile) to a personalized composite score.
"""

import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.enhanced_user_profile import EnhancedUserProfile


def get_personalized_weights(profile: EnhancedUserProfile) -> dict:
    """
    Get personalized scoring weights from Enhanced User Profile.

    The profile already contains customizable weights set by the user.
    This function can further adjust them based on special circumstances.

    Parameters:
    -----------
    profile : EnhancedUserProfile
        Enhanced student profile with preset weights

    Returns:
    --------
    dict
        Dictionary with weights for all indices
    """
    weights = profile.get_composite_weight_dict()

    # Optional: Apply automatic adjustments based on extreme needs
    # (Profile weights are already customized, so minimal adjustment)

    # Ensure weights sum to 1.0
    total = sum(weights.values())
    if total > 0:
        weights = {k: v / total for k, v in weights.items()}

    return weights


def filter_colleges_for_user(df: pd.DataFrame, profile: EnhancedUserProfile) -> pd.DataFrame:
    """
    Filter colleges based on enhanced user constraints.

    Filters:
    - Budget constraint (net price <= budget with small tolerance)
    - Institution type (public/private/for-profit)
    - Geographic (in-state, preferred states, preferred regions)
    - Selectivity buckets (reach/target/safety)
    - Environment (size, urbanization, Carnegie type)
    - MSI preference
    - Data completeness (if required)

    Parameters:
    -----------
    df : pd.DataFrame
        Enhanced featured college DataFrame
    profile : EnhancedUserProfile
        Enhanced student profile

    Returns:
    --------
    pd.DataFrame
        Filtered DataFrame
    """
    filtered = df.copy()
    initial_count = len(filtered)

    print("\n" + "="*60)
    print("APPLYING USER FILTERS")
    print("="*60)
    print(f"Starting with: {initial_count} institutions")

    # 1. BUDGET FILTER
    net_price_col = 'Net Price'
    if net_price_col in filtered.columns:
        # Allow generous buffer (50%) over budget to be more permissive
        max_price = profile.annual_budget * 1.50
        before_count = len(filtered)
        filtered = filtered[
            pd.to_numeric(filtered[net_price_col], errors='coerce').isna() |
            (pd.to_numeric(filtered[net_price_col], errors='coerce') <= max_price)
        ]
        print(f"  After budget filter (≤${max_price:,.0f} or missing data): {len(filtered)} institutions (removed {before_count - len(filtered)})")

    # 2. EXCLUDE FOR-PROFIT (strongly recommended)
    if profile.exclude_for_profit:
        control_col = 'Control of Institution'
        if control_col in filtered.columns:
            # Control: 1=public, 2=private nonprofit, 3=for-profit
            filtered = filtered[pd.to_numeric(filtered[control_col], errors='coerce') != 3]
            print(f"  After excluding for-profit: {len(filtered)} institutions")

    # 3. INSTITUTION TYPE PREFERENCE
    if profile.institution_type_pref != "either":
        control_col = 'Control of Institution'
        if control_col in filtered.columns:
            if profile.institution_type_pref == "public":
                filtered = filtered[pd.to_numeric(filtered[control_col], errors='coerce') == 1]
            elif profile.institution_type_pref == "private_nonprofit":
                filtered = filtered[pd.to_numeric(filtered[control_col], errors='coerce') == 2]
            print(f"  After {profile.institution_type_pref} filter: {len(filtered)} institutions")

    # 4. GEOGRAPHIC FILTERS
    state_col = 'State of Institution'

    # In-state only
    if profile.in_state_only and profile.home_state and state_col in filtered.columns:
        filtered = filtered[filtered[state_col].astype(str).str.upper() == profile.home_state.upper()]
        print(f"  After in-state filter ({profile.home_state}): {len(filtered)} institutions")

    # Preferred states
    elif profile.preferred_states and state_col in filtered.columns:
        preferred_upper = [s.upper() for s in profile.preferred_states]
        filtered = filtered[filtered[state_col].astype(str).str.upper().isin(preferred_upper)]
        print(f"  After preferred states filter: {len(filtered)} institutions")

    # Preferred regions
    if profile.preferred_regions:
        region_col = 'Region #'
        if region_col in filtered.columns:
            filtered = filtered[pd.to_numeric(filtered[region_col], errors='coerce').isin(profile.preferred_regions)]
            print(f"  After preferred regions filter: {len(filtered)} institutions")

    # 5. SELECTIVITY BUCKETS
    # Note: We don't filter by selectivity - we include all levels and let users see
    # the full range (Reach/Target/Safety/Open). Selectivity is shown in results for context.
    # This ensures students see a balanced college list.
    selectivity_buckets = profile.get_selectivity_preferences()
    if selectivity_buckets and len(selectivity_buckets) < 4:  # Only filter if user explicitly excluded some
        if 'selectivity_bucket' in filtered.columns:
            before_count = len(filtered)
            # Include rows where selectivity bucket matches OR is missing (to be more permissive)
            filtered = filtered[
                filtered['selectivity_bucket'].isin(selectivity_buckets) |
                filtered['selectivity_bucket'].isna()
            ]
            print(f"  After selectivity filter ({', '.join(selectivity_buckets)} + missing): {len(filtered)} institutions (removed {before_count - len(filtered)})")

    # 6. SIZE PREFERENCE
    if profile.size_pref and profile.size_pref != "no_preference":
        if 'size_category' in filtered.columns:
            # Map preference to category
            size_map = {
                "small": 1,
                "medium": 2,
                "large": [3, 4, 5]
            }
            if profile.size_pref.lower() in size_map:
                before_count = len(filtered)
                target_sizes = size_map[profile.size_pref.lower()]
                if not isinstance(target_sizes, list):
                    target_sizes = [target_sizes]
                # Include schools with matching size OR missing size data
                filtered = filtered[
                    pd.to_numeric(filtered['size_category'], errors='coerce').isin(target_sizes) |
                    pd.to_numeric(filtered['size_category'], errors='coerce').isna()
                ]
                print(f"  After size filter ({profile.size_pref} + missing): {len(filtered)} institutions (removed {before_count - len(filtered)})")

    # 7. URBANIZATION PREFERENCE
    if profile.urbanization_pref and profile.urbanization_pref != "no_preference":
        # Use binary flags created in environment features
        urban_map = {
            "urban": "is_urban",
            "suburban": "is_suburban",
            "rural": "is_rural"
        }
        flag_col = urban_map.get(profile.urbanization_pref.lower())
        if flag_col and flag_col in filtered.columns:
            before_count = len(filtered)
            # Include matching urbanization OR missing data
            filtered = filtered[
                (filtered[flag_col] == 1) |
                pd.to_numeric(filtered[flag_col], errors='coerce').isna()
            ]
            print(f"  After urbanization filter ({profile.urbanization_pref} + missing): {len(filtered)} institutions (removed {before_count - len(filtered)})")

    # 8. CARNEGIE TYPE PREFERENCE
    if profile.carnegie_pref:
        has_match = pd.Series(False, index=filtered.index)
        carnegie_flags = {
            "doctoral": "is_doctoral",
            "masters": "is_masters",
            "baccalaureate": "is_baccalaureate",
            "associate": "is_associate"
        }
        for pref in profile.carnegie_pref:
            flag_col = carnegie_flags.get(pref.lower())
            if flag_col and flag_col in filtered.columns:
                has_match |= (filtered[flag_col] == 1)

        if has_match.any():
            filtered = filtered[has_match]
            print(f"  After Carnegie type filter: {len(filtered)} institutions")

    # 9. MSI PREFERENCE
    if profile.msi_preference and profile.msi_preference != "no_preference":
        msi_flags = {
            "HBCU": "HBCU",
            "HSI": "HSI",
            "Tribal": "TRIBAL",
            "AANAPII": "AANAPII",
            "PBI": "PBI"
        }

        if profile.msi_preference.upper() in msi_flags:
            flag_col = msi_flags[profile.msi_preference.upper()]
            if flag_col in filtered.columns:
                filtered = filtered[pd.to_numeric(filtered[flag_col], errors='coerce') == 1]
                print(f"  After MSI filter ({profile.msi_preference}): {len(filtered)} institutions")
        elif profile.msi_preference.lower() == "any_msi":
            # Include any MSI
            msi_match = pd.Series(False, index=filtered.index)
            for flag_col in msi_flags.values():
                if flag_col in filtered.columns:
                    msi_match |= (pd.to_numeric(filtered[flag_col], errors='coerce') == 1)
            if msi_match.any():
                filtered = filtered[msi_match]
                print(f"  After any MSI filter: {len(filtered)} institutions")

    # 10. MINIMUM GRADUATION RATE
    if profile.min_graduation_rate:
        # Use overall graduation rate if available
        grad_col = "Bachelor's Degree Graduation Rate Within 6 Years - Total"
        if grad_col in filtered.columns:
            filtered = filtered[pd.to_numeric(filtered[grad_col], errors='coerce') >= profile.min_graduation_rate]
            print(f"  After min graduation rate filter (>={profile.min_graduation_rate}%): {len(filtered)} institutions")

    print(f"\n✓ Final filtered set: {len(filtered)} institutions")
    print("="*60)

    if len(filtered) == 0:
        print("\n⚠️  WARNING: No colleges match your criteria!")
        print("Suggestions:")
        print("  1. Increase your annual budget")
        print("  2. Remove geographic restrictions (in-state only, preferred states)")
        print("  3. Set preferences to 'no_preference' or 'either'")
        print("  4. Include more selectivity buckets (reach, target, safety, open)")
        print("  5. Remove MSI preference filter if set")
        print()

    return filtered


def calculate_personalized_affordability(row: pd.Series, profile: EnhancedUserProfile) -> float:
    """
    Calculate personalized affordability score.

    Uses parent-specific score if student-parent, otherwise standard.
    Applies additional penalty if significantly over budget.

    Parameters:
    -----------
    row : pd.Series
        College row
    profile : EnhancedUserProfile
        Student profile

    Returns:
    --------
    float
        Personalized affordability score (0-1)
    """
    # Choose appropriate affordability score
    if profile.is_student_parent:
        base_score = row.get('afford_score_parent', 0.5)
    else:
        base_score = row.get('afford_score_std', 0.5)

    # Additional penalty for exceeding budget
    net_price = pd.to_numeric(row.get('Net Price', 0), errors='coerce')
    if pd.notna(net_price) and net_price > profile.annual_budget:
        excess_pct = (net_price - profile.annual_budget) / profile.annual_budget
        # Steeper penalty for significant excess
        penalty = min(0.4, excess_pct * 0.3)
        base_score = max(0, base_score - penalty)

    return base_score


def calculate_personalized_equity(row: pd.Series, profile: EnhancedUserProfile) -> float:
    """
    Calculate personalized equity score.

    Uses race-specific graduation rate + overall equity parity.
    Bonus for MSI match if applicable.

    Parameters:
    -----------
    row : pd.Series
        College row
    profile : EnhancedUserProfile
        Student profile

    Returns:
    --------
    float
        Personalized equity score (0-1)
    """
    # Map race to normalized grad rate column
    race_to_col = {
        'BLACK': 'grad_rate_black_norm',
        'WHITE': 'grad_rate_white_norm',
        'ASIAN': 'grad_rate_asian_norm',
        'NATIVE': 'grad_rate_native_norm',
        'PACIFIC': 'grad_rate_pacific_norm'
    }

    # Get race-specific grad rate if available
    if profile.race_ethnicity and profile.race_ethnicity != "PREFER_NOT_TO_SAY":
        grad_col = race_to_col.get(profile.race_ethnicity)
        if grad_col and grad_col in row.index:
            race_specific_norm = row.get(grad_col, 0.5)
        else:
            race_specific_norm = 0.5
    else:
        # Use overall equity parity if no race specified
        race_specific_norm = 0.5

    # Get equity parity (disparity measure)
    parity = row.get('equity_parity', 0.5)

    # Combine: 70% race-specific, 30% parity
    equity_score = 0.7 * race_specific_norm + 0.3 * parity

    # Small bonus for MSI match (if applicable)
    if profile.msi_preference and profile.msi_preference != "no_preference":
        msi_flags = {"HBCU": "HBCU", "HSI": "HSI", "Tribal": "TRIBAL", "AANAPII": "AANAPII"}
        if profile.msi_preference.upper() in msi_flags:
            flag_col = msi_flags[profile.msi_preference.upper()]
            if flag_col in row.index and pd.to_numeric(row.get(flag_col, 0), errors='coerce') == 1:
                equity_score = min(1.0, equity_score * 1.1)  # 10% bonus

    return equity_score


def calculate_personalized_support(row: pd.Series, profile: EnhancedUserProfile) -> float:
    """
    Calculate personalized support infrastructure score.

    Applies bonus for students who need strong support (first-gen, nontraditional, etc.)

    Parameters:
    -----------
    row : pd.Series
        College row
    profile : EnhancedUserProfile
        Student profile

    Returns:
    --------
    float
        Personalized support score (0-1)
    """
    base_score = row.get('support_infrastructure_score', 0.5)

    # Bonus multiplier for students who particularly need support
    if profile.strong_support_services or profile.is_first_gen or profile.is_nontraditional:
        # Amplify differences - reward high support schools more
        if base_score > 0.6:
            base_score = min(1.0, base_score * 1.15)

    return base_score


def calculate_personalized_academic_fit(row: pd.Series, profile: EnhancedUserProfile) -> float:
    """
    Calculate personalized academic offerings score.

    Uses field-specific strength if major is specified, otherwise base score.
    Bonus for research opportunities if desired.

    Parameters:
    -----------
    row : pd.Series
        College row
    profile : EnhancedUserProfile
        Student profile

    Returns:
    --------
    float
        Personalized academic fit score (0-1)
    """
    # Start with base academic offerings score
    base_score = row.get('academic_offerings_score', 0.5)

    # Use field-specific strength if major specified
    if profile.intended_major and profile.intended_major != "Undecided":
        field_map = {
            "STEM": "stem_strength",
            "Business": "business_strength",
            "Health": "health_strength",
            "Social Sciences": "social_sciences_strength",
            "Arts & Humanities": "arts_and_humanities_strength",
            "Education": "education_strength"
        }

        strength_col = field_map.get(profile.intended_major)
        if strength_col and strength_col in row.index:
            field_strength = row.get(strength_col, 0.5)
            # Weight: 70% field-specific, 30% overall
            base_score = 0.7 * field_strength + 0.3 * base_score

    # Bonus for research opportunities at doctoral institutions
    if profile.research_opportunities:
        if row.get('is_doctoral', 0) == 1:
            base_score = min(1.0, base_score * 1.2)  # 20% bonus

    return base_score


def calculate_personalized_environment_fit(row: pd.Series, profile: EnhancedUserProfile) -> float:
    """
    Calculate personalized environment fit score.

    Checks match on size, urbanization, and diversity.

    Parameters:
    -----------
    row : pd.Series
        College row
    profile : EnhancedUserProfile
        Student profile

    Returns:
    --------
    float
        Environment fit score (0-1)
    """
    # Start with diversity score
    base_score = row.get('environment_diversity_score', 0.5)

    # Check matches on preferences
    matches = 0
    checks = 0

    # Size match
    if profile.size_pref and profile.size_pref != "no_preference":
        checks += 1
        size_flags = {
            "small": "size_small",
            "medium": "size_medium",
            "large": "size_large"
        }
        flag_col = size_flags.get(profile.size_pref.lower())
        if flag_col and row.get(flag_col, 0) == 1:
            matches += 1

    # Urbanization match
    if profile.urbanization_pref and profile.urbanization_pref != "no_preference":
        checks += 1
        urban_flags = {
            "urban": "is_urban",
            "suburban": "is_suburban",
            "rural": "is_rural"
        }
        flag_col = urban_flags.get(profile.urbanization_pref.lower())
        if flag_col and row.get(flag_col, 0) == 1:
            matches += 1

    # Calculate match bonus
    if checks > 0:
        match_rate = matches / checks
        # Boost base score based on preference matches
        base_score = base_score * 0.5 + match_rate * 0.5

    # Special boost for international students at international-friendly schools
    if profile.is_international:
        intl_presence = row.get('intl_presence_norm', 0)
        if intl_presence > 0.6:  # School has significant international presence
            base_score = min(1.0, base_score * 1.15)

    return base_score


def calculate_personalized_access(row: pd.Series, profile: EnhancedUserProfile) -> float:
    """
    Calculate personalized access score based on selectivity match.

    Parameters:
    -----------
    row : pd.Series
        College row
    profile : EnhancedUserProfile
        Student profile

    Returns:
    --------
    float
        Personalized access score (0-1)
    """
    base_access = row.get('access_score_base', 0.5)

    # Get selectivity bucket
    bucket = row.get('selectivity_bucket', 'Unknown')

    # Adjust based on GPA and bucket match
    if bucket == 'Safety' and profile.gpa >= 3.0:
        multiplier = 1.2  # Good fit - boost
    elif bucket == 'Target' and 2.5 <= profile.gpa <= 3.8:
        multiplier = 1.1  # Reasonable fit
    elif bucket == 'Reach' and profile.gpa >= 3.7:
        multiplier = 1.0  # Worth trying
    elif bucket == 'Reach' and profile.gpa < 3.3:
        multiplier = 0.7  # May be too difficult
    elif bucket == 'Open':
        multiplier = 1.3  # Easy access
    else:
        multiplier = 1.0

    # Consider test scores if submitted
    if profile.test_score_status == "submitted":
        # Boost slightly for strong test scores
        if profile.sat_score and profile.sat_score >= 1400:
            multiplier *= 1.1
        elif profile.act_score and profile.act_score >= 31:
            multiplier *= 1.1

    access_score = min(1.0, base_access * multiplier)

    return access_score


def score_college_for_user(row: pd.Series, profile: EnhancedUserProfile, weights: dict) -> float:
    """
    Calculate the comprehensive personalized score.

    Score = weighted sum of all component scores

    Parameters:
    -----------
    row : pd.Series
        College row
    profile : EnhancedUserProfile
        Student profile
    weights : dict
        Personalized weights

    Returns:
    --------
    float
        Final personalized composite score (0-1)
    """
    # Get all component scores
    roi = row.get('roi_score', 0.5)
    affordability = calculate_personalized_affordability(row, profile)
    equity = calculate_personalized_equity(row, profile)
    support = calculate_personalized_support(row, profile)
    academic_fit = calculate_personalized_academic_fit(row, profile)
    environment = calculate_personalized_environment_fit(row, profile)

    # Calculate weighted composite score
    score = (
        weights['roi'] * roi +
        weights['affordability'] * affordability +
        weights['equity'] * equity +
        weights['support'] * support +
        weights['academic_fit'] * academic_fit +
        weights['environment'] * environment
    )

    return score


def rank_colleges_for_user(df: pd.DataFrame, profile: EnhancedUserProfile, top_k: int = 20) -> pd.DataFrame:
    """
    Rank and return top colleges for a user using enhanced scoring.

    Parameters:
    -----------
    df : pd.DataFrame
        Enhanced featured college DataFrame
    profile : EnhancedUserProfile
        Enhanced student profile
    top_k : int
        Number of top colleges to return

    Returns:
    --------
    pd.DataFrame
        Ranked DataFrame with top_k colleges and their scores
    """
    print("\n" + "="*60)
    print("RANKING COLLEGES FOR USER")
    print("="*60)

    # Get personalized weights
    weights = get_personalized_weights(profile)

    print("\nPersonalized Weights:")
    for key, value in weights.items():
        print(f"  {key}: {value:.1%}")

    # Filter colleges
    filtered = filter_colleges_for_user(df, profile)

    if len(filtered) == 0:
        print("\n⚠️  No colleges match your filters. Try relaxing some constraints.")
        return pd.DataFrame()

    # Calculate personalized scores
    print("\nCalculating personalized scores...")
    filtered = filtered.copy()

    # Calculate all component scores
    filtered['personalized_affordability'] = filtered.apply(
        lambda row: calculate_personalized_affordability(row, profile), axis=1
    )
    filtered['personalized_equity'] = filtered.apply(
        lambda row: calculate_personalized_equity(row, profile), axis=1
    )
    filtered['personalized_support'] = filtered.apply(
        lambda row: calculate_personalized_support(row, profile), axis=1
    )
    filtered['personalized_academic_fit'] = filtered.apply(
        lambda row: calculate_personalized_academic_fit(row, profile), axis=1
    )
    filtered['personalized_environment'] = filtered.apply(
        lambda row: calculate_personalized_environment_fit(row, profile), axis=1
    )
    filtered['personalized_access'] = filtered.apply(
        lambda row: calculate_personalized_access(row, profile), axis=1
    )

    # Calculate composite score
    filtered['composite_score'] = filtered.apply(
        lambda row: score_college_for_user(row, profile, weights), axis=1
    )

    # Rank by composite score
    ranked = filtered.sort_values('composite_score', ascending=False).head(top_k)

    print(f"\n✓ Ranked top {len(ranked)} colleges")
    print("="*60)

    return ranked


if __name__ == "__main__":
    # Test enhanced scoring
    from src.enhanced_feature_engineering import build_enhanced_featured_college_df
    from src.enhanced_user_profile import EXAMPLE_PROFILES

    print("Testing Enhanced Scoring System\n")

    # Load enhanced data
    colleges_df = build_enhanced_featured_college_df(earnings_ceiling=30000.0)

    # Test with example profile
    profile = EXAMPLE_PROFILES['low_income_parent']

    print("\nUser Profile:")
    print(profile)

    # Rank colleges
    recommendations = rank_colleges_for_user(colleges_df, profile, top_k=10)

    # Display results
    if len(recommendations) > 0:
        print("\n" + "="*60)
        print("TOP 10 RECOMMENDATIONS")
        print("="*60)

        display_cols = [
            'Institution Name',
            'State of Institution',
            'selectivity_bucket',
            'composite_score',
            'personalized_affordability',
            'personalized_support',
            'personalized_equity'
        ]

        available_cols = [col for col in display_cols if col in recommendations.columns]
        print(recommendations[available_cols].to_string(index=False))
