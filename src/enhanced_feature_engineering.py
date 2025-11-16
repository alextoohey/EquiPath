"""
Enhanced Feature Engineering Module for EquiPath Project

This module extends the base feature engineering with additional comprehensive indices:
1. Support Infrastructure Index - student support resources
2. Environment & Personalization Index - campus environment fit
3. Academic Offerings Index - program strength and availability
4. Enhanced versions of existing indices
5. Selectivity bucketing (Reach/Target/Safety)

Addresses educational equity by incorporating factors that matter to:
- First-generation students
- Student-parents
- Nontraditional/older students
- International students
- Students from underrepresented groups
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
        Use for metrics where lower is better

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


# ============================================================================
# SUPPORT INFRASTRUCTURE INDEX
# ============================================================================

def add_support_infrastructure_index(df):
    """
    Create Support Infrastructure Index based on institutional resources
    and support systems.

    This index helps identify schools that provide strong support,
    especially important for:
    - First-generation students
    - Low-income students
    - Nontraditional students
    - Student-parents

    Components:
    -----------
    1. Student-faculty ratio (lower is better - more individual attention)
    2. Endowment per student (higher is better - more resources)
    3. Instructional expenditure per student (higher is better)
    4. Pell Grant percentage (indicates experience supporting low-income)
    5. Transfer-out rate (lower suggests better support/retention)
    6. Percent of older students (indicates support for nontraditional)

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with institutional data

    Returns:
    --------
    pd.DataFrame
        DataFrame with added support_infrastructure_score and component columns
    """
    print("Adding Support Infrastructure Index...")

    # Component 1: Student-Faculty Ratio
    faculty_col = 'Student-to-Faculty Ratio'
    if faculty_col in df.columns:
        df[faculty_col] = pd.to_numeric(df[faculty_col], errors='coerce')
        # Lower ratio is better (inverse normalization)
        df['student_faculty_norm'] = min_max_normalize(
            df[faculty_col].fillna(df[faculty_col].median()),
            inverse=True
        )
    else:
        print(f"  Warning: {faculty_col} not found, using default")
        df['student_faculty_norm'] = 0.5

    # Component 2: Endowment per student
    # Try both GASB (public) and FASB (private) endowment columns
    gasb_endow = 'Public Institution GASB Endowment Assets'
    fasb_endow = 'Private not-for-profit or Public Institution FASB Endowment Assets'
    enrollment_col = 'Number of Undergraduates'  # or total enrollment

    if gasb_endow in df.columns and fasb_endow in df.columns:
        df[gasb_endow] = pd.to_numeric(df[gasb_endow], errors='coerce')
        df[fasb_endow] = pd.to_numeric(df[fasb_endow], errors='coerce')

        # Combine endowments (use whichever is available)
        df['total_endowment'] = df[[gasb_endow, fasb_endow]].max(axis=1)

        # Get enrollment for per-student calculation
        if enrollment_col in df.columns:
            df[enrollment_col] = pd.to_numeric(df[enrollment_col], errors='coerce')
            df['endowment_per_student'] = df['total_endowment'] / df[enrollment_col].replace(0, np.nan)
            df['endowment_norm'] = min_max_normalize(
                df['endowment_per_student'].fillna(0)
            )
        else:
            df['endowment_norm'] = min_max_normalize(
                df['total_endowment'].fillna(0)
            )
    else:
        print(f"  Warning: Endowment columns not found, using default")
        df['endowment_norm'] = 0.5

    # Component 3: Instructional Expenditure per student
    instruct_exp_col = 'Instructional Expenditures per Full-Time Equivalent Student'
    if instruct_exp_col in df.columns:
        df[instruct_exp_col] = pd.to_numeric(df[instruct_exp_col], errors='coerce')
        df['instructional_exp_norm'] = min_max_normalize(
            df[instruct_exp_col].fillna(df[instruct_exp_col].median())
        )
    else:
        print(f"  Warning: {instruct_exp_col} not found, using default")
        df['instructional_exp_norm'] = 0.5

    # Component 4: Pell Grant percentage (proxy for low-income support experience)
    pell_col = 'Percent Receiving Pell Grants'
    if pell_col in df.columns:
        df[pell_col] = pd.to_numeric(df[pell_col], errors='coerce')
        # Higher Pell percentage suggests experience supporting low-income students
        df['pell_support_norm'] = min_max_normalize(
            df[pell_col].fillna(df[pell_col].median())
        )
    else:
        print(f"  Warning: {pell_col} not found, using default")
        df['pell_support_norm'] = 0.5

    # Component 5: Transfer-out rate (lower suggests better retention/support)
    transfer_col = 'Transfer-Out Rate'
    if transfer_col in df.columns:
        df[transfer_col] = pd.to_numeric(df[transfer_col], errors='coerce')
        df['retention_norm'] = min_max_normalize(
            df[transfer_col].fillna(df[transfer_col].median()),
            inverse=True  # Lower transfer-out is better
        )
    else:
        print(f"  Warning: {transfer_col} not found, using default")
        df['retention_norm'] = 0.5

    # Component 6: Support for nontraditional/older students
    age_col = 'Percent of Undergraduates Age 25 and Older'
    if age_col in df.columns:
        df[age_col] = pd.to_numeric(df[age_col], errors='coerce')
        # Higher percentage suggests more experience with nontraditional students
        df['nontraditional_support_norm'] = min_max_normalize(
            df[age_col].fillna(0)
        )
    else:
        print(f"  Warning: {age_col} not found, using default")
        df['nontraditional_support_norm'] = 0.5

    # Calculate composite Support Infrastructure Score
    # Weights:
    # - 25% student-faculty ratio (individual attention)
    # - 20% endowment per student (resources)
    # - 20% instructional expenditure (academic investment)
    # - 15% Pell support (low-income experience)
    # - 10% retention (student success)
    # - 10% nontraditional support
    df['support_infrastructure_score'] = (
        0.25 * df['student_faculty_norm'] +
        0.20 * df['endowment_norm'] +
        0.20 * df['instructional_exp_norm'] +
        0.15 * df['pell_support_norm'] +
        0.10 * df['retention_norm'] +
        0.10 * df['nontraditional_support_norm']
    )

    print(f"  Support Infrastructure score range: [{df['support_infrastructure_score'].min():.3f}, {df['support_infrastructure_score'].max():.3f}]")
    print(f"  Mean: {df['support_infrastructure_score'].mean():.3f}")

    return df


# ============================================================================
# ENVIRONMENT & PERSONALIZATION INDEX
# ============================================================================

def add_environment_personalization_index(df):
    """
    Create Environment & Personalization Index based on campus characteristics.

    Helps students find schools that match their preferences for:
    - Institution size
    - Urban/rural setting
    - Geographic location
    - Student body composition

    This is NOT a scored index but rather categorical/informational features
    that can be used for filtering and matching.

    Components:
    -----------
    1. Institution size category
    2. Degree of urbanization
    3. Region and state
    4. Carnegie classification
    5. Control (public/private/for-profit)
    6. Religious affiliation (if identifiable)

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with institutional data

    Returns:
    --------
    pd.DataFrame
        DataFrame with environment features encoded
    """
    print("Adding Environment & Personalization features...")

    # Size category
    size_col = 'Institution Size Category'
    if size_col in df.columns:
        df['size_category'] = df[size_col]
        # Create readable labels (map numeric codes if needed)
        df['size_small'] = (df[size_col] == 1).astype(int) if df[size_col].dtype in ['int64', 'float64'] else 0
        df['size_medium'] = (df[size_col] == 2).astype(int) if df[size_col].dtype in ['int64', 'float64'] else 0
        df['size_large'] = (df[size_col] >= 3).astype(int) if df[size_col].dtype in ['int64', 'float64'] else 0
    else:
        print(f"  Warning: {size_col} not found")
        df['size_category'] = np.nan

    # Urbanization
    urban_col = 'Degree of Urbanization'
    if urban_col in df.columns:
        df['urbanization'] = df[urban_col]
        # Create binary flags for common preferences
        # Assuming: 11-13 = city, 21-23 = suburb, 31-33 = town, 41-43 = rural
        df['is_urban'] = df[urban_col].isin([11, 12, 13]).astype(int) if urban_col in df.columns else 0
        df['is_suburban'] = df[urban_col].isin([21, 22, 23]).astype(int) if urban_col in df.columns else 0
        df['is_rural'] = df[urban_col].isin([41, 42, 43]).astype(int) if urban_col in df.columns else 0
    else:
        print(f"  Warning: {urban_col} not found")
        df['urbanization'] = np.nan

    # Region
    region_col = 'Region #'
    if region_col in df.columns:
        df['region'] = df[region_col]
    else:
        print(f"  Warning: {region_col} not found")
        df['region'] = np.nan

    # State
    state_col = 'State of Institution'
    if state_col in df.columns:
        df['state'] = df[state_col]
    else:
        print(f"  Warning: {state_col} not found")
        df['state'] = np.nan

    # Carnegie Classification (use most recent: 2021)
    carnegie_col = '2021 Carnegie Classification'
    if carnegie_col in df.columns:
        df['carnegie_2021'] = df[carnegie_col]
        # Create flags for major types
        # Doctoral: 15-17, Master's: 18-20, Baccalaureate: 21-23, Associate's: 1-9
        df['is_doctoral'] = df[carnegie_col].isin([15, 16, 17]).astype(int)
        df['is_masters'] = df[carnegie_col].isin([18, 19, 20]).astype(int)
        df['is_baccalaureate'] = df[carnegie_col].isin([21, 22, 23]).astype(int)
        df['is_associate'] = (df[carnegie_col] >= 1) & (df[carnegie_col] <= 9).astype(int)
    else:
        print(f"  Warning: {carnegie_col} not found")
        df['carnegie_2021'] = np.nan

    # Control (public/private/for-profit)
    control_col = 'Control of Institution'
    if control_col in df.columns:
        df['control'] = df[control_col]
        # 1 = public, 2 = private nonprofit, 3 = private for-profit
        df['is_public'] = (df[control_col] == 1).astype(int)
        df['is_private_nonprofit'] = (df[control_col] == 2).astype(int)
        df['is_for_profit'] = (df[control_col] == 3).astype(int)
    else:
        print(f"  Warning: {control_col} not found")
        df['control'] = np.nan

    # Create a simple "environment fit score" based on diversity of student body
    # This helps identify welcoming, diverse campuses
    diversity_score_components = []

    # International students
    intl_col = 'Percent International Students'
    if intl_col in df.columns:
        df[intl_col] = pd.to_numeric(df[intl_col], errors='coerce')
        df['intl_presence_norm'] = min_max_normalize(df[intl_col].fillna(0))
        diversity_score_components.append(df['intl_presence_norm'])

    # Older students (nontraditional)
    if 'nontraditional_support_norm' in df.columns:
        diversity_score_components.append(df['nontraditional_support_norm'])

    # Pell students (economic diversity)
    if 'pell_support_norm' in df.columns:
        diversity_score_components.append(df['pell_support_norm'])

    # Calculate environment diversity score
    if diversity_score_components:
        df['environment_diversity_score'] = pd.concat(diversity_score_components, axis=1).mean(axis=1)
        print(f"  Environment diversity score range: [{df['environment_diversity_score'].min():.3f}, {df['environment_diversity_score'].max():.3f}]")
    else:
        df['environment_diversity_score'] = 0.5

    print("  Environment features added (categorical for filtering)")

    return df


# ============================================================================
# ACADEMIC OFFERINGS INDEX
# ============================================================================

def add_academic_offerings_index(df):
    """
    Create Academic Offerings Index based on program strength and breadth.

    Helps students find schools strong in their intended field of study.

    Components:
    -----------
    1. Highest degree offered (research capacity)
    2. Carnegie classification (academic mission)
    3. Institution level (2-year vs 4-year)
    4. Field-specific degree production (STEM, Business, Health, etc.)
    5. Overall degree completion volume

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with institutional data

    Returns:
    --------
    pd.DataFrame
        DataFrame with academic offerings scores
    """
    print("Adding Academic Offerings Index...")

    # Component 1: Highest degree offered
    degree_col = 'Highest Degree Offered'
    if degree_col in df.columns:
        df[degree_col] = pd.to_numeric(df[degree_col], errors='coerce')
        # 0=non-degree, 1=certificate, 2=associate, 3=bachelor, 4=postbac cert,
        # 5=master, 6=post-master cert, 7=doctoral, 8=first professional
        df['degree_level_norm'] = min_max_normalize(df[degree_col].fillna(3))
    else:
        print(f"  Warning: {degree_col} not found")
        df['degree_level_norm'] = 0.5

    # Component 2: Carnegie research intensity
    # Higher Carnegie codes for doctoral = more research
    if 'carnegie_2021' in df.columns:
        # For doctoral universities (15-17), give higher scores
        carnegie_score = df['carnegie_2021'].fillna(0).copy()
        carnegie_score = carnegie_score.apply(lambda x:
            1.0 if x in [15, 16, 17] else  # Doctoral
            0.7 if x in [18, 19, 20] else  # Master's
            0.5 if x in [21, 22, 23] else  # Baccalaureate
            0.3 if x in range(1, 10) else  # Associate
            0.5  # Default
        )
        df['research_intensity_norm'] = carnegie_score
    else:
        df['research_intensity_norm'] = 0.5

    # Component 3: Bachelor's degree production (volume)
    bach_total_col = 'Number of Bachelor Degrees Grand Total'
    if bach_total_col in df.columns:
        df[bach_total_col] = pd.to_numeric(df[bach_total_col], errors='coerce')
        df['degree_production_norm'] = min_max_normalize(
            df[bach_total_col].fillna(0)
        )
    else:
        print(f"  Warning: {bach_total_col} not found")
        df['degree_production_norm'] = 0.5

    # Component 4: Field-specific strength indicators
    # Look for bachelor's degrees in major fields
    # Note: Column names may vary - adjust based on actual dataset

    field_columns = {
        'STEM': [
            'Number of Bachelor Degrees Biological And Biomedical Sciences',
            'Number of Bachelor Degrees Computer And Information Sciences And Support Services',
            'Number of Bachelor Degrees Engineering',
            'Number of Bachelor Degrees Mathematics And Statistics',
            'Number of Bachelor Degrees Physical Sciences'
        ],
        'Business': [
            'Number of Bachelor Degrees Business, Management, Marketing, And Related Support Services'
        ],
        'Health': [
            'Number of Bachelor Degrees Health Professions And Related Programs'
        ],
        'Social Sciences': [
            'Number of Bachelor Degrees Social Sciences'
        ],
        'Arts & Humanities': [
            'Number of Bachelor Degrees Visual And Performing Arts',
            'Number of Bachelor Degrees English Language And Literature/Letters'
        ],
        'Education': [
            'Number of Bachelor Degrees Education'
        ]
    }

    # Calculate field strengths
    for field, cols in field_columns.items():
        field_total = pd.Series(0, index=df.index)
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                field_total += df[col].fillna(0)

        # Store field volume
        df[f'{field.lower().replace(" ", "_").replace("&", "and")}_degrees'] = field_total

        # Normalize
        if field_total.sum() > 0:
            df[f'{field.lower().replace(" ", "_").replace("&", "and")}_strength'] = min_max_normalize(field_total)
        else:
            df[f'{field.lower().replace(" ", "_").replace("&", "and")}_strength'] = 0.0

    # Component 5: Overall academic offerings score
    # Equal weight to degree level, research intensity, and production
    df['academic_offerings_score'] = (
        0.35 * df['degree_level_norm'] +
        0.35 * df['research_intensity_norm'] +
        0.30 * df['degree_production_norm']
    )

    print(f"  Academic Offerings score range: [{df['academic_offerings_score'].min():.3f}, {df['academic_offerings_score'].max():.3f}]")
    print(f"  Mean: {df['academic_offerings_score'].mean():.3f}")

    return df


# ============================================================================
# SELECTIVITY BUCKETING (REACH/TARGET/SAFETY)
# ============================================================================

def add_selectivity_bucketing(df):
    """
    Categorize schools into Reach/Target/Safety buckets based on admission rate.

    This helps students build balanced college lists.

    Buckets:
    --------
    - Safety: Admission rate > 60%
    - Target: Admission rate 30-60%
    - Reach: Admission rate < 30%
    - Open: Open admissions policy
    - Unknown: Missing data

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with admission rate

    Returns:
    --------
    pd.DataFrame
        DataFrame with selectivity_bucket column
    """
    print("Adding selectivity bucketing...")

    admit_col = 'Total Percent of Applicants Admitted'
    open_policy_col = 'Open Admissions Policy'

    def categorize_selectivity(row):
        # Check for open admissions first
        if open_policy_col in df.columns and row[open_policy_col] == 1:
            return 'Open'

        # Use admission rate
        if admit_col in df.columns and pd.notna(row[admit_col]):
            rate = row[admit_col]
            if rate > 60:
                return 'Safety'
            elif rate >= 30:
                return 'Target'
            else:
                return 'Reach'

        return 'Unknown'

    df['selectivity_bucket'] = df.apply(categorize_selectivity, axis=1)

    print("  Selectivity distribution:")
    print(df['selectivity_bucket'].value_counts())

    return df


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def build_enhanced_featured_college_df(data_dir='data', earnings_ceiling=30000.0):
    """
    Main function to build enhanced featured college DataFrame.

    Combines all feature engineering including:
    - Base indices (ROI, Affordability, Equity, Access)
    - Support Infrastructure Index
    - Environment & Personalization features
    - Academic Offerings Index
    - Selectivity bucketing

    Parameters:
    -----------
    data_dir : str
        Directory containing data files
    earnings_ceiling : float
        Earnings ceiling for affordability data (default: 30000.0)

    Returns:
    --------
    pd.DataFrame
        Fully enhanced featured DataFrame
    """
    print("="*80)
    print("BUILDING ENHANCED FEATURED COLLEGE DATAFRAME")
    print("="*80)

    # Load merged data with specific earnings ceiling
    df = load_merged_data(
        data_dir=data_dir,
        join_key='UNITID',  # Use UNITID for better match quality
        earnings_ceiling=earnings_ceiling
    )

    print(f"\nStarting with {len(df)} institutions")
    print(f"Columns: {len(df.columns)}")

    # Add all feature engineering
    df = add_support_infrastructure_index(df)
    df = add_environment_personalization_index(df)
    df = add_academic_offerings_index(df)
    df = add_selectivity_bucketing(df)

    # Import and add base indices from original feature_engineering
    from src.feature_engineering import (
        add_roi_score,
        add_affordability_scores,
        add_equity_scores,
        add_access_score
    )

    df = add_roi_score(df)
    df = add_affordability_scores(df)
    df = add_equity_scores(df)
    df = add_access_score(df)

    print(f"\n✓ Enhanced feature engineering complete!")
    print(f"Final dataset: {len(df)} rows, {len(df.columns)} columns")

    # Display summary
    print("\n" + "="*80)
    print("SUMMARY STATISTICS - ALL INDICES")
    print("="*80)

    score_cols = [
        'roi_score',
        'afford_score_std',
        'afford_score_parent',
        'equity_parity',
        'access_score_base',
        'support_infrastructure_score',
        'environment_diversity_score',
        'academic_offerings_score'
    ]

    available_scores = [col for col in score_cols if col in df.columns]
    if available_scores:
        print(df[available_scores].describe())

    return df


if __name__ == "__main__":
    # Test enhanced feature engineering
    featured_df = build_enhanced_featured_college_df()

    # Show sample with key scores
    sample_cols = [
        'Institution Name',
        'State of Institution',
        'selectivity_bucket',
        'roi_score',
        'afford_score_std',
        'support_infrastructure_score',
        'academic_offerings_score',
        'environment_diversity_score'
    ]

    sample_cols_present = [col for col in sample_cols if col in featured_df.columns]

    print("\n" + "="*80)
    print("SAMPLE OUTPUT (Top 10 by Combined Score)")
    print("="*80)

    # Create combined score for demo
    score_components = []
    for col in ['roi_score', 'afford_score_std', 'support_infrastructure_score', 'academic_offerings_score']:
        if col in featured_df.columns:
            score_components.append(featured_df[col])

    if score_components:
        featured_df['combined_score'] = pd.concat(score_components, axis=1).mean(axis=1)
        print(featured_df.nlargest(10, 'combined_score')[sample_cols_present + ['combined_score']])
