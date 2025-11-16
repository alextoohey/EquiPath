"""
Feature engineering module for EquiPath project.
Computes institution-level metrics: ROI, affordability, equity, and access scores.
"""

import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loading import load_merged_data


def min_max_normalize(series, inverse=False):
    """
    Min-max normalization to scale values between 0 and 1.

    Parameters:
    -----------
    series : pd.Series
        Series to normalize
    inverse : bool
        If True, invert the normalization (1 - normalized value)
        Use for metrics where lower is better (e.g., debt)

    Returns:
    --------
    pd.Series
        Normalized series
    """
    min_val = series.min()
    max_val = series.max()

    if max_val == min_val:
        return pd.Series([0.5] * len(series), index=series.index)

    normalized = (series - min_val) / (max_val - min_val)

    if inverse:
        normalized = 1 - normalized

    return normalized


def add_roi_score(df):
    """
    Add ROI score based on earnings and debt.

    Uses:
    - Median Earnings of Students Working and Not Enrolled 10 Years After Entry
    - Median Debt of Completers

    ROI score = 0.6 * normalized_earnings - 0.4 * normalized_debt

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with earnings and debt columns

    Returns:
    --------
    pd.DataFrame
        DataFrame with added roi_score, earnings_norm, debt_norm columns
    """
    print("Adding ROI scores...")

    # Identify columns
    earnings_col = 'Median Earnings of Students Working and Not Enrolled 10 Years After Entry'
    debt_col = 'Median Debt of Completers'

    # Handle missing values and convert to numeric
    df[earnings_col] = pd.to_numeric(df[earnings_col], errors='coerce')
    df[debt_col] = pd.to_numeric(df[debt_col], errors='coerce')

    # Normalize earnings (higher is better)
    df['earnings_norm'] = min_max_normalize(df[earnings_col].fillna(df[earnings_col].median()))

    # Normalize debt (lower is better, so inverse=True)
    df['debt_norm'] = min_max_normalize(df[debt_col].fillna(df[debt_col].median()), inverse=True)

    # Calculate ROI score
    df['roi_score'] = 0.6 * df['earnings_norm'] + 0.4 * df['debt_norm']

    print(f"  ROI score range: [{df['roi_score'].min():.3f}, {df['roi_score'].max():.3f}]")
    print(f"  Mean ROI score: {df['roi_score'].mean():.3f}")

    return df


def add_affordability_scores(df):
    """
    Add affordability scores for standard students and student-parents.

    Uses:
    - Net Price (from Affordability Gap dataset)
    - Affordability Gap (standard students)
    - Student Parent Affordability Gap: Center-Based Care

    Lower gap and price are better.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with affordability columns

    Returns:
    --------
    pd.DataFrame
        DataFrame with added affordability scores
    """
    print("Adding affordability scores...")

    # Identify columns
    net_price_col = 'Net Price'
    gap_std_col = 'Affordability Gap (net price minus income earned working 10 hrs at min wage)'
    gap_parent_col = 'Student Parent Affordability Gap: Center-Based Care'

    # Handle missing values and convert to numeric
    df[net_price_col] = pd.to_numeric(df[net_price_col], errors='coerce')
    df[gap_std_col] = pd.to_numeric(df[gap_std_col], errors='coerce')
    df[gap_parent_col] = pd.to_numeric(df[gap_parent_col], errors='coerce')

    # Normalize (inverse because lower is better)
    df['net_price_norm'] = min_max_normalize(
        df[net_price_col].fillna(df[net_price_col].median()),
        inverse=True
    )
    df['gap_std_norm'] = min_max_normalize(
        df[gap_std_col].fillna(df[gap_std_col].median()),
        inverse=True
    )
    df['gap_parent_norm'] = min_max_normalize(
        df[gap_parent_col].fillna(df[gap_parent_col].median()),
        inverse=True
    )

    # Calculate affordability scores
    # Weight: 60% gap, 40% net price
    df['afford_score_std'] = 0.6 * df['gap_std_norm'] + 0.4 * df['net_price_norm']
    df['afford_score_parent'] = 0.6 * df['gap_parent_norm'] + 0.4 * df['net_price_norm']

    print(f"  Standard affordability score range: [{df['afford_score_std'].min():.3f}, {df['afford_score_std'].max():.3f}]")
    print(f"  Parent affordability score range: [{df['afford_score_parent'].min():.3f}, {df['afford_score_parent'].max():.3f}]")

    return df


def add_equity_scores(df):
    """
    Add equity scores based on race-specific graduation rates and parity.

    Uses graduation rate columns for:
    - Black/African American
    - Hispanic/Latino
    - White
    - Asian
    - Native American/Alaska Native

    Computes:
    - Normalized graduation rate for each race
    - Equity parity = 1 - (max_grad_rate - min_grad_rate) / 100

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with graduation rate columns

    Returns:
    --------
    pd.DataFrame
        DataFrame with added equity scores
    """
    print("Adding equity scores...")

    # Map race to graduation rate columns
    race_grad_cols = {
        'BLACK': "Bachelor's Degree Graduation Rate Within 6 Years - Black, Non-Latino",
        'WHITE': "Bachelor's Degree Graduation Rate Within 6 Years - White Non-Latino",
        'ASIAN': "Bachelor's Degree Graduation Rate Within 6 Years - Asian",
        'NATIVE': "Bachelor's Degree Graduation Rate Within 6 Years - American Indian or Alaska Native",
        'PACIFIC': "Bachelor's Degree Graduation Rate Within 6 Years - Native Hawaiian or Other Pacific Islander"
    }

    # Convert to numeric and handle missing values
    for race, col in race_grad_cols.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Calculate median for each race
    race_medians = {}
    for race, col in race_grad_cols.items():
        if col in df.columns:
            race_medians[race] = df[col].median()

    # Normalize each race-specific graduation rate
    for race, col in race_grad_cols.items():
        if col in df.columns:
            norm_col = f'grad_rate_{race.lower()}_norm'
            df[norm_col] = min_max_normalize(
                df[col].fillna(race_medians.get(race, 50))
            )

    # Calculate equity parity across races
    # Parity = 1 - (disparity between highest and lowest grad rates)
    grad_cols_present = [col for col in race_grad_cols.values() if col in df.columns]

    if grad_cols_present:
        # For each row, calculate parity
        def calculate_parity(row):
            rates = [row[col] for col in grad_cols_present if pd.notna(row[col])]
            if len(rates) < 2:
                return 0.5  # neutral if not enough data
            disparity = (max(rates) - min(rates)) / 100
            return max(0, 1 - disparity)

        df['equity_parity'] = df.apply(calculate_parity, axis=1)

        print(f"  Equity parity range: [{df['equity_parity'].min():.3f}, {df['equity_parity'].max():.3f}]")
        print(f"  Mean equity parity: {df['equity_parity'].mean():.3f}")
    else:
        print("  Warning: No graduation rate columns found for equity calculation")
        df['equity_parity'] = 0.5

    return df


def add_access_score(df):
    """
    Add access score based on admission rate.

    Uses:
    - Total Percent of Applicants Admitted

    Higher admission rate = easier access

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with admission rate column

    Returns:
    --------
    pd.DataFrame
        DataFrame with added access scores
    """
    print("Adding access scores...")

    admit_col = 'Total Percent of Applicants Admitted'

    # Handle missing values and convert to numeric
    df[admit_col] = pd.to_numeric(df[admit_col], errors='coerce')

    # Normalize admission rate (higher is better for access)
    df['admit_rate_norm'] = min_max_normalize(
        df[admit_col].fillna(df[admit_col].median())
    )

    # For now, access score is just the normalized admission rate
    # Can be refined later with additional factors
    df['access_score_base'] = df['admit_rate_norm']

    print(f"  Access score range: [{df['access_score_base'].min():.3f}, {df['access_score_base'].max():.3f}]")
    print(f"  Mean access score: {df['access_score_base'].mean():.3f}")

    return df


def build_featured_college_df(data_dir='data', earnings_ceiling=30000.0):
    """
    Main function to build the featured college DataFrame.

    Loads merged data and applies all feature engineering functions.

    IMPORTANT: Since the affordability data has multiple rows per institution
    (one for each earnings ceiling), we filter to a specific earnings ceiling
    to get one row per institution for feature engineering.

    Parameters:
    -----------
    data_dir : str
        Directory containing the data files
    earnings_ceiling : float
        Which earnings ceiling scenario to use for affordability metrics.
        Default: 30000.0 (lowest income bracket)
        Valid values: 30000.0, 48000.0, 75000.0, 110000.0, 150000.0
        Each represents the upper bound of the student family earnings bracket.

    Returns:
    --------
    pd.DataFrame
        Fully featured DataFrame with all computed metrics.
        One row per institution.
    """
    print("="*60)
    print("BUILDING FEATURED COLLEGE DATAFRAME")
    print("="*60)

    # Load merged data filtered to specific earnings ceiling
    # This gives us one row per institution for the target income bracket
    df = load_merged_data(
        data_dir=data_dir,
        join_key='Institution Name',
        earnings_ceiling=earnings_ceiling
    )

    print(f"\nStarting with {len(df)} institutions")
    print(f"Starting with {len(df.columns)} columns")

    # Apply all feature engineering steps
    df = add_roi_score(df)
    df = add_affordability_scores(df)
    df = add_equity_scores(df)
    df = add_access_score(df)

    print(f"\n✓ Feature engineering complete!")
    print(f"Final dataset: {len(df)} rows, {len(df.columns)} columns")

    # Display summary of key scores
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)

    score_cols = ['roi_score', 'afford_score_std', 'afford_score_parent',
                  'equity_parity', 'access_score_base']
    print(df[score_cols].describe())

    return df


if __name__ == "__main__":
    # Test the feature engineering
    featured_df = build_featured_college_df()

    # Save sample output
    sample_cols = [
        'Institution Name',
        'State of Institution',
        'Sector of Institution',
        'roi_score',
        'afford_score_std',
        'afford_score_parent',
        'equity_parity',
        'access_score_base'
    ]

    # Filter to columns that exist
    sample_cols_present = [col for col in sample_cols if col in featured_df.columns]

    print("\n" + "="*60)
    print("SAMPLE OUTPUT (Top 10 by ROI)")
    print("="*60)
    print(featured_df.nlargest(10, 'roi_score')[sample_cols_present])
