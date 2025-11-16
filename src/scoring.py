"""
Personalized scoring logic for EquiPath project.
Maps (college, user_profile) to a personalized Student Success & Equity Score.
"""

import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.user_profile import UserProfile
from src.distance_utils import filter_by_radius, add_distance_column


def choose_weights(profile: UserProfile) -> dict:
    """
    Choose personalized weights for the scoring function based on user profile.

    Base weights:
    - alpha (ROI): 0.25
    - beta (Affordability): 0.30
    - gamma (Equity): 0.25
    - delta (Access): 0.20

    Adjustments:
    - Low income or small budget → increase beta, slightly reduce alpha
    - Student-parent → increase beta and gamma
    - First-gen or marginalized race → increase gamma

    Parameters:
    -----------
    profile : UserProfile
        Student profile

    Returns:
    --------
    dict
        Dictionary with weights: {'alpha', 'beta', 'gamma', 'delta'}
    """
    # Start with default weights
    weights = {
        'alpha': 0.25,  # ROI
        'beta': 0.30,   # Affordability
        'gamma': 0.25,  # Equity
        'delta': 0.20   # Access
    }

    # Adjust for low income or low budget
    if profile.income_bracket == "LOW" or profile.budget < 20000:
        weights['beta'] += 0.15  # Increase affordability weight
        weights['alpha'] -= 0.05  # Reduce ROI weight slightly

    # Adjust for student-parents
    if profile.is_parent:
        weights['beta'] += 0.10  # Affordability is critical
        weights['gamma'] += 0.05  # Equity matters more

    # Adjust for first-gen or historically marginalized students
    if profile.first_gen or profile.race in ["BLACK", "HISPANIC", "NATIVE"]:
        weights['gamma'] += 0.10  # Equity support is important

    # Normalize weights to sum to 1.0
    total = sum(weights.values())
    weights = {k: v / total for k, v in weights.items()}

    return weights


def filter_colleges_for_user(df: pd.DataFrame, profile: UserProfile) -> pd.DataFrame:
    """
    Filter colleges based on user constraints.

    Filters:
    - Budget constraint (net price <= 1.5x budget)
    - Public only (if specified)
    - In-state only (if specified)
    - School size preference (if specified)

    Parameters:
    -----------
    df : pd.DataFrame
        Featured college DataFrame
    profile : UserProfile
        Student profile

    Returns:
    --------
    pd.DataFrame
        Filtered DataFrame
    """
    filtered = df.copy()
    initial_count = len(filtered)

    # Filter by budget (net price <= 1.5x budget)
    net_price_col = 'Net Price'
    if net_price_col in filtered.columns:
        max_price = profile.budget * 1.5
        filtered = filtered[pd.to_numeric(filtered[net_price_col], errors='coerce') <= max_price]
        print(f"  Budget filter: {initial_count} → {len(filtered)} institutions")

    # Filter by public only
    if profile.public_only:
        sector_col = 'Sector of Institution'
        if sector_col in filtered.columns:
            # Sector codes: 1 = Public 4-year, 4 = Public 2-year
            # Convert to numeric and filter for public sectors
            sector_numeric = pd.to_numeric(filtered[sector_col], errors='coerce')
            filtered = filtered[sector_numeric.isin([1, 4])]
            print(f"  Public only filter: {len(filtered)} institutions")

    # Filter by in-state
    if profile.in_state_only and profile.state:
        state_col = 'State of Institution'
        if state_col in filtered.columns:
            # Convert to string and filter
            filtered = filtered[filtered[state_col].astype(str).str.upper() == profile.state.upper()]
            print(f"  In-state filter ({profile.state}): {len(filtered)} institutions")

    # Filter by school size (if preference specified)
    if profile.school_size_pref:
        size_col = 'Institution Size Category'
        if size_col in filtered.columns:
            # Convert to string and filter
            filtered = filtered[filtered[size_col].astype(str).str.contains(profile.school_size_pref, case=False, na=False)]
            print(f"  Size filter ({profile.school_size_pref}): {len(filtered)} institutions")

    # Filter by zip code radius (if specified)
    if profile.zip_code and profile.radius_miles:
        print(f"  Applying radius filter: {profile.radius_miles} miles from zip {profile.zip_code}")
        filtered = filter_by_radius(filtered, profile.zip_code, profile.radius_miles)
        print(f"  Radius filter: {len(filtered)} institutions within {profile.radius_miles} miles")
    elif profile.zip_code:
        # Add distance column even if not filtering
        filtered = add_distance_column(filtered, profile.zip_code)

    print(f"  Final filtered set: {len(filtered)} institutions")
    return filtered


def affordability_for_user(row: pd.Series, profile: UserProfile) -> float:
    """
    Calculate personalized affordability score for a user.

    Uses afford_score_parent if is_parent, else afford_score_std.
    Applies penalty if net price exceeds budget.

    Parameters:
    -----------
    row : pd.Series
        College row from DataFrame
    profile : UserProfile
        Student profile

    Returns:
    --------
    float
        Personalized affordability score (0-1)
    """
    # Choose base affordability score
    if profile.is_parent:
        base_score = row.get('afford_score_parent', 0.5)
    else:
        base_score = row.get('afford_score_std', 0.5)

    # Apply penalty if net price exceeds budget
    net_price = pd.to_numeric(row.get('Net Price', 0), errors='coerce')
    if pd.notna(net_price) and net_price > profile.budget:
        excess_pct = (net_price - profile.budget) / profile.budget
        penalty = min(0.3, excess_pct * 0.2)  # Max 30% penalty
        base_score = max(0, base_score - penalty)

    return base_score


def equity_for_user(row: pd.Series, profile: UserProfile) -> float:
    """
    Calculate personalized equity score for a user.

    Uses race-specific graduation rate + overall equity parity.
    Formula: 0.7 * race_specific_grad_rate_norm + 0.3 * equity_parity

    Parameters:
    -----------
    row : pd.Series
        College row from DataFrame
    profile : UserProfile
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

    # Get race-specific grad rate
    grad_col = race_to_col.get(profile.race)
    if grad_col and grad_col in row.index:
        race_specific_norm = row.get(grad_col, 0.5)
    else:
        # Fallback: use average of available rates
        race_specific_norm = 0.5

    # Get equity parity
    parity = row.get('equity_parity', 0.5)

    # Combine: 70% race-specific, 30% parity
    equity_score = 0.7 * race_specific_norm + 0.3 * parity

    return equity_score


def access_for_user(row: pd.Series, profile: UserProfile) -> float:
    """
    Calculate personalized access score for a user.

    Considers admission rate and GPA fit:
    - Safety schools (high admit rate, student above avg): boost
    - Reach schools (low admit rate, student below avg): reduce
    - Target schools: neutral

    Parameters:
    -----------
    row : pd.Series
        College row from DataFrame
    profile : UserProfile
        Student profile

    Returns:
    --------
    float
        Personalized access score (0-1)
    """
    base_access = row.get('access_score_base', 0.5)

    # Get admission rate
    admit_rate = pd.to_numeric(row.get('Total Percent of Applicants Admitted', 50), errors='coerce')

    # Classify school type based on admission rate
    if admit_rate >= 70:
        school_type = 'Safety'
        multiplier = 1.1 if profile.gpa >= 3.0 else 1.0
    elif admit_rate <= 30:
        school_type = 'Reach'
        multiplier = 1.2 if profile.gpa >= 3.7 else 0.8
    else:
        school_type = 'Target'
        multiplier = 1.0

    access_score = min(1.0, base_access * multiplier)

    return access_score


def score_college_for_user(row: pd.Series, profile: UserProfile, weights: dict) -> float:
    """
    Calculate the personalized Student Success & Equity Score.

    Score = alpha * ROI + beta * Affordability + gamma * Equity + delta * Access

    Parameters:
    -----------
    row : pd.Series
        College row from DataFrame
    profile : UserProfile
        Student profile
    weights : dict
        Personalized weights from choose_weights()

    Returns:
    --------
    float
        Final personalized score (0-1)
    """
    # Get component scores
    roi = row.get('roi_score', 0.5)
    affordability = affordability_for_user(row, profile)
    equity = equity_for_user(row, profile)
    access = access_for_user(row, profile)

    # Calculate weighted score
    score = (
        weights['alpha'] * roi +
        weights['beta'] * affordability +
        weights['gamma'] * equity +
        weights['delta'] * access
    )

    return score


def rank_colleges_for_user(df: pd.DataFrame, profile: UserProfile, top_k: int = 10) -> pd.DataFrame:
    """
    Rank and return top colleges for a user based on personalized scoring.

    Parameters:
    -----------
    df : pd.DataFrame
        Featured college DataFrame
    profile : UserProfile
        Student profile
    top_k : int
        Number of top colleges to return

    Returns:
    --------
    pd.DataFrame
        Top-k colleges with user_score column
    """
    print("\n" + "="*60)
    print(f"RANKING COLLEGES FOR USER")
    print("="*60)
    print(profile)
    print("\n" + "="*60)

    # Filter colleges
    print("\nFiltering colleges...")
    filtered_df = filter_colleges_for_user(df, profile)

    if len(filtered_df) == 0:
        print("\n⚠ WARNING: No colleges match the filters!")
        return pd.DataFrame()

    # Choose weights
    weights = choose_weights(profile)
    print(f"\nPersonalized weights:")
    print(f"  ROI (alpha):          {weights['alpha']:.3f}")
    print(f"  Affordability (beta): {weights['beta']:.3f}")
    print(f"  Equity (gamma):       {weights['gamma']:.3f}")
    print(f"  Access (delta):       {weights['delta']:.3f}")

    # Calculate personalized scores
    print(f"\nCalculating personalized scores for {len(filtered_df)} colleges...")
    filtered_df = filtered_df.copy()
    filtered_df['user_score'] = filtered_df.apply(
        lambda row: score_college_for_user(row, profile, weights),
        axis=1
    )

    # Sort by score
    ranked_df = filtered_df.sort_values('user_score', ascending=False)

    # Return top k
    top_colleges = ranked_df.head(top_k)

    print(f"\n✓ Top {min(top_k, len(top_colleges))} colleges identified!")
    print("="*60)

    return top_colleges


if __name__ == "__main__":
    # Test the scoring system
    from src.feature_engineering import build_featured_college_df
    from src.user_profile import EXAMPLE_PROFILES

    print("Loading featured college data...")
    df = build_featured_college_df()

    # Test with one example profile
    profile = EXAMPLE_PROFILES['low_income_parent']

    # Rank colleges
    top_colleges = rank_colleges_for_user(df, profile, top_k=10)

    # Display results
    if len(top_colleges) > 0:
        display_cols = [
            'Institution Name',
            'State of Institution',
            'user_score',
            'roi_score',
            'afford_score_parent',
            'equity_parity',
            'access_score_base',
            'Net Price'
        ]
        display_cols = [col for col in display_cols if col in top_colleges.columns]

        print("\n" + "="*60)
        print("TOP 10 RECOMMENDED COLLEGES")
        print("="*60)
        print(top_colleges[display_cols].to_string(index=False))
