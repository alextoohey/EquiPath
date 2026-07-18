"""
Feature engineering for EquiPath.

Computes every institution-level index used by the recommender from the merged
College Results + Affordability Gap dataset:

Base indices
    - ROI (earnings vs. debt)
    - Affordability (net price + affordability gap, with a student-parent variant
      that accounts for childcare costs)
    - Equity (race-specific graduation rates + cross-race parity)
    - Access (admission rate)

Extended indices
    - Support infrastructure (student-faculty ratio, endowment, instructional
      spend, Pell experience, retention, nontraditional-student presence)
    - Environment (size/urbanization/control flags + student-body diversity)
    - Academic offerings (degree level, research intensity, field strength)
    - Selectivity buckets (Reach / Target / Safety / Open)

Entry point: `build_college_features()` — returns one row per institution with
all indices computed, cached to Parquet for fast reloads.
"""

import os

import numpy as np
import pandas as pd

from src.data_loading import load_merged_data, _get_cache_dir


def min_max_normalize(series, inverse=False):
    """Scale a series to [0, 1]. Set inverse=True when lower raw values are better."""
    min_val = series.min()
    max_val = series.max()

    if max_val == min_val:
        return pd.Series([0.5] * len(series), index=series.index)

    normalized = (series - min_val) / (max_val - min_val)
    return 1 - normalized if inverse else normalized


# ============================================================================
# BASE INDICES
# ============================================================================

def add_roi_score(df):
    """ROI = 0.6 * normalized 10-year earnings + 0.4 * normalized (inverse) debt."""
    earnings_col = 'Median Earnings of Students Working and Not Enrolled 10 Years After Entry'
    debt_col = 'Median Debt of Completers'

    df[earnings_col] = pd.to_numeric(df[earnings_col], errors='coerce')
    df[debt_col] = pd.to_numeric(df[debt_col], errors='coerce')

    df['earnings_norm'] = min_max_normalize(df[earnings_col].fillna(df[earnings_col].median()))
    df['debt_norm'] = min_max_normalize(df[debt_col].fillna(df[debt_col].median()), inverse=True)
    df['roi_score'] = 0.6 * df['earnings_norm'] + 0.4 * df['debt_norm']

    return df


def add_affordability_scores(df):
    """
    Affordability = 0.6 * (inverse) affordability gap + 0.4 * (inverse) net price.

    Two variants: `afford_score_std` uses the standard gap, `afford_score_parent`
    uses the student-parent gap that includes center-based childcare costs.
    """
    net_price_col = 'Net Price'
    gap_std_col = 'Affordability Gap (net price minus income earned working 10 hrs at min wage)'
    gap_parent_col = 'Student Parent Affordability Gap: Center-Based Care'

    for col in (net_price_col, gap_std_col, gap_parent_col):
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df['net_price_norm'] = min_max_normalize(
        df[net_price_col].fillna(df[net_price_col].median()), inverse=True)
    df['gap_std_norm'] = min_max_normalize(
        df[gap_std_col].fillna(df[gap_std_col].median()), inverse=True)
    df['gap_parent_norm'] = min_max_normalize(
        df[gap_parent_col].fillna(df[gap_parent_col].median()), inverse=True)

    df['afford_score_std'] = 0.6 * df['gap_std_norm'] + 0.4 * df['net_price_norm']
    df['afford_score_parent'] = 0.6 * df['gap_parent_norm'] + 0.4 * df['net_price_norm']

    return df


def add_equity_scores(df):
    """
    Normalize race-specific 6-year graduation rates and compute equity parity.

    Parity = 1 - (max grad rate - min grad rate) / 100 across races: 1.0 means
    every group graduates at the same rate, 0.0 means maximum disparity.
    """
    race_grad_cols = {
        'BLACK': "Bachelor's Degree Graduation Rate Within 6 Years - Black, Non-Latino",
        'WHITE': "Bachelor's Degree Graduation Rate Within 6 Years - White Non-Latino",
        'ASIAN': "Bachelor's Degree Graduation Rate Within 6 Years - Asian",
        'NATIVE': "Bachelor's Degree Graduation Rate Within 6 Years - American Indian or Alaska Native",
        'PACIFIC': "Bachelor's Degree Graduation Rate Within 6 Years - Native Hawaiian or Other Pacific Islander",
    }

    for col in race_grad_cols.values():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    for race, col in race_grad_cols.items():
        if col in df.columns:
            fill_value = df[col].median()
            df[f'grad_rate_{race.lower()}_norm'] = min_max_normalize(
                df[col].fillna(fill_value if pd.notna(fill_value) else 50))

    grad_cols_present = [col for col in race_grad_cols.values() if col in df.columns]

    if grad_cols_present:
        def calculate_parity(row):
            rates = [row[col] for col in grad_cols_present if pd.notna(row[col])]
            if len(rates) < 2:
                return 0.5  # neutral when there isn't enough data to compare
            return max(0, 1 - (max(rates) - min(rates)) / 100)

        df['equity_parity'] = df.apply(calculate_parity, axis=1)
    else:
        df['equity_parity'] = 0.5

    return df


def add_access_score(df):
    """Access = normalized admission rate (higher admission rate = easier access)."""
    admit_col = 'Total Percent of Applicants Admitted'
    df[admit_col] = pd.to_numeric(df[admit_col], errors='coerce')
    df['admit_rate_norm'] = min_max_normalize(df[admit_col].fillna(df[admit_col].median()))
    df['access_score_base'] = df['admit_rate_norm']
    return df


# ============================================================================
# SUPPORT INFRASTRUCTURE INDEX
# ============================================================================

def add_support_infrastructure_index(df):
    """
    Support infrastructure — how well an institution can support students who
    need it most (first-gen, low-income, nontraditional, student-parents).

    Weighted components:
        25% student-faculty ratio (lower = more individual attention)
        20% endowment per student
        20% instructional expenditure per student
        15% Pell share (experience supporting low-income students)
        10% transfer-out rate (lower = better retention)
        10% share of students age 25+ (nontraditional-student experience)
    """
    faculty_col = 'Student-to-Faculty Ratio'
    if faculty_col in df.columns:
        df[faculty_col] = pd.to_numeric(df[faculty_col], errors='coerce')
        df['student_faculty_norm'] = min_max_normalize(
            df[faculty_col].fillna(df[faculty_col].median()), inverse=True)
    else:
        df['student_faculty_norm'] = 0.5

    gasb_endow = 'Public Institution GASB Endowment Assets'
    fasb_endow = 'Private not-for-profit or Public Institution FASB Endowment Assets'
    enrollment_col = 'Number of Undergraduates'

    if gasb_endow in df.columns and fasb_endow in df.columns:
        df[gasb_endow] = pd.to_numeric(df[gasb_endow], errors='coerce')
        df[fasb_endow] = pd.to_numeric(df[fasb_endow], errors='coerce')
        df['total_endowment'] = df[[gasb_endow, fasb_endow]].max(axis=1)

        if enrollment_col in df.columns:
            df[enrollment_col] = pd.to_numeric(df[enrollment_col], errors='coerce')
            df['endowment_per_student'] = (
                df['total_endowment'] / df[enrollment_col].replace(0, np.nan))
            df['endowment_norm'] = min_max_normalize(df['endowment_per_student'].fillna(0))
        else:
            df['endowment_norm'] = min_max_normalize(df['total_endowment'].fillna(0))
    else:
        df['endowment_norm'] = 0.5

    instruct_exp_col = 'Instructional Expenditures per Full-Time Equivalent Student'
    if instruct_exp_col in df.columns:
        df[instruct_exp_col] = pd.to_numeric(df[instruct_exp_col], errors='coerce')
        df['instructional_exp_norm'] = min_max_normalize(
            df[instruct_exp_col].fillna(df[instruct_exp_col].median()))
    else:
        df['instructional_exp_norm'] = 0.5

    pell_col = 'Percent Receiving Pell Grants'
    if pell_col in df.columns:
        df[pell_col] = pd.to_numeric(df[pell_col], errors='coerce')
        df['pell_support_norm'] = min_max_normalize(df[pell_col].fillna(df[pell_col].median()))
    else:
        df['pell_support_norm'] = 0.5

    transfer_col = 'Transfer-Out Rate'
    if transfer_col in df.columns:
        df[transfer_col] = pd.to_numeric(df[transfer_col], errors='coerce')
        df['retention_norm'] = min_max_normalize(
            df[transfer_col].fillna(df[transfer_col].median()), inverse=True)
    else:
        df['retention_norm'] = 0.5

    age_col = 'Percent of Undergraduates Age 25 and Older'
    if age_col in df.columns:
        df[age_col] = pd.to_numeric(df[age_col], errors='coerce')
        df['nontraditional_support_norm'] = min_max_normalize(df[age_col].fillna(0))
    else:
        df['nontraditional_support_norm'] = 0.5

    df['support_infrastructure_score'] = (
        0.25 * df['student_faculty_norm'] +
        0.20 * df['endowment_norm'] +
        0.20 * df['instructional_exp_norm'] +
        0.15 * df['pell_support_norm'] +
        0.10 * df['retention_norm'] +
        0.10 * df['nontraditional_support_norm']
    )

    return df


# ============================================================================
# ENVIRONMENT & PERSONALIZATION FEATURES
# ============================================================================

def add_environment_features(df):
    """
    Campus-environment features used for filtering and environment-fit scoring:
    size/urbanization/Carnegie/control flags plus a student-body diversity score.
    """
    # The size column appears in both source datasets, so the merge suffixes
    # it — resolve whichever variant is present (values are codes 1-5)
    size_col = next(
        (c for c in ('Institution Size Category', 'Institution Size Category_CR',
                     'Institution Size Category_AG') if c in df.columns),
        None,
    )
    if size_col:
        size_numeric = pd.to_numeric(df[size_col], errors='coerce')
        df['size_category'] = size_numeric
        df['size_small'] = (size_numeric == 1).astype(int)
        df['size_medium'] = (size_numeric == 2).astype(int)
        df['size_large'] = (size_numeric >= 3).astype(int)
    else:
        df['size_category'] = np.nan

    urban_col = 'Degree of Urbanization'
    if urban_col in df.columns:
        # IPEDS locale codes: 11-13 city, 21-23 suburb, 31-33 town, 41-43 rural
        df['urbanization'] = df[urban_col]
        df['is_urban'] = df[urban_col].isin([11, 12, 13]).astype(int)
        df['is_suburban'] = df[urban_col].isin([21, 22, 23]).astype(int)
        df['is_rural'] = df[urban_col].isin([41, 42, 43]).astype(int)
    else:
        df['urbanization'] = np.nan

    region_col = 'Region #'
    df['region'] = df[region_col] if region_col in df.columns else np.nan

    state_col = 'State of Institution'
    df['state'] = df[state_col] if state_col in df.columns else np.nan

    carnegie_col = '2021 Carnegie Classification'
    if carnegie_col in df.columns:
        # Carnegie codes: 15-17 doctoral, 18-20 master's, 21-23 baccalaureate, 1-9 associate
        df['carnegie_2021'] = df[carnegie_col]
        df['is_doctoral'] = df[carnegie_col].isin([15, 16, 17]).astype(int)
        df['is_masters'] = df[carnegie_col].isin([18, 19, 20]).astype(int)
        df['is_baccalaureate'] = df[carnegie_col].isin([21, 22, 23]).astype(int)
        df['is_associate'] = df[carnegie_col].isin(range(1, 10)).astype(int)
    else:
        df['carnegie_2021'] = np.nan

    control_col = 'Control of Institution'
    if control_col in df.columns:
        # 1 = public, 2 = private nonprofit, 3 = private for-profit
        df['control'] = df[control_col]
        df['is_public'] = (df[control_col] == 1).astype(int)
        df['is_private_nonprofit'] = (df[control_col] == 2).astype(int)
        df['is_for_profit'] = (df[control_col] == 3).astype(int)
    else:
        df['control'] = np.nan

    # Diversity score: international presence + nontraditional share + Pell share
    diversity_components = []

    intl_col = 'Percent International Students'
    if intl_col in df.columns:
        df[intl_col] = pd.to_numeric(df[intl_col], errors='coerce')
        df['intl_presence_norm'] = min_max_normalize(df[intl_col].fillna(0))
        diversity_components.append(df['intl_presence_norm'])

    for col in ('nontraditional_support_norm', 'pell_support_norm'):
        if col in df.columns:
            diversity_components.append(df[col])

    if diversity_components:
        df['environment_diversity_score'] = (
            pd.concat(diversity_components, axis=1).mean(axis=1))
    else:
        df['environment_diversity_score'] = 0.5

    return df


# ============================================================================
# ACADEMIC OFFERINGS INDEX
# ============================================================================

def add_academic_offerings_index(df):
    """
    Academic offerings — program strength and breadth:
        35% highest degree offered
        35% research intensity (Carnegie classification)
        30% bachelor's degree production volume
    plus per-field strength scores (STEM, Business, Health, ...) used when the
    student declares an intended major.
    """
    degree_col = 'Highest Degree Offered'
    if degree_col in df.columns:
        df[degree_col] = pd.to_numeric(df[degree_col], errors='coerce')
        df['degree_level_norm'] = min_max_normalize(df[degree_col].fillna(3))
    else:
        df['degree_level_norm'] = 0.5

    if 'carnegie_2021' in df.columns:
        df['research_intensity_norm'] = df['carnegie_2021'].fillna(0).apply(
            lambda x:
            1.0 if x in [15, 16, 17] else   # doctoral
            0.7 if x in [18, 19, 20] else   # master's
            0.5 if x in [21, 22, 23] else   # baccalaureate
            0.3 if x in range(1, 10) else   # associate
            0.5
        )
    else:
        df['research_intensity_norm'] = 0.5

    bach_total_col = 'Number of Bachelor Degrees Grand Total'
    if bach_total_col in df.columns:
        df[bach_total_col] = pd.to_numeric(df[bach_total_col], errors='coerce')
        df['degree_production_norm'] = min_max_normalize(df[bach_total_col].fillna(0))
    else:
        df['degree_production_norm'] = 0.5

    field_columns = {
        'STEM': [
            'Number of Bachelor Degrees Biological And Biomedical Sciences',
            'Number of Bachelor Degrees Computer And Information Sciences And Support Services',
            'Number of Bachelor Degrees Engineering',
            'Number of Bachelor Degrees Mathematics And Statistics',
            'Number of Bachelor Degrees Physical Sciences',
        ],
        'Business': [
            'Number of Bachelor Degrees Business, Management, Marketing, And Related Support Services',
        ],
        'Health': [
            'Number of Bachelor Degrees Health Professions And Related Programs',
        ],
        'Social Sciences': [
            'Number of Bachelor Degrees Social Sciences',
        ],
        'Arts & Humanities': [
            'Number of Bachelor Degrees Visual And Performing Arts',
            'Number of Bachelor Degrees English Language And Literature/Letters',
        ],
        'Education': [
            'Number of Bachelor Degrees Education',
        ],
    }

    for field, cols in field_columns.items():
        field_total = pd.Series(0, index=df.index)
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                field_total += df[col].fillna(0)

        slug = field.lower().replace(' ', '_').replace('&', 'and')
        df[f'{slug}_degrees'] = field_total
        df[f'{slug}_strength'] = (
            min_max_normalize(field_total) if field_total.sum() > 0 else 0.0)

    df['academic_offerings_score'] = (
        0.35 * df['degree_level_norm'] +
        0.35 * df['research_intensity_norm'] +
        0.30 * df['degree_production_norm']
    )

    return df


# ============================================================================
# SELECTIVITY BUCKETING
# ============================================================================

def add_selectivity_buckets(df):
    """
    Bucket schools by admission rate so students can build balanced lists:
    Open (open admissions), Safety (>60%), Target (30-60%), Reach (<30%).
    """
    admit_col = 'Total Percent of Applicants Admitted'
    open_policy_col = 'Open Admissions Policy'

    def categorize(row):
        if open_policy_col in df.columns and row[open_policy_col] == 1:
            return 'Open'
        if admit_col in df.columns and pd.notna(row[admit_col]):
            rate = row[admit_col]
            if rate > 60:
                return 'Safety'
            if rate >= 30:
                return 'Target'
            return 'Reach'
        return 'Unknown'

    df['selectivity_bucket'] = df.apply(categorize, axis=1)
    return df


# ============================================================================
# ENTRY POINT
# ============================================================================

def build_college_features(data_dir='data', earnings_ceiling=30000.0, force_reload=False):
    """
    Build the fully-featured college DataFrame: one row per institution with
    every base and extended index computed.

    Parameters
    ----------
    data_dir : str
        Directory containing the source data files.
    earnings_ceiling : float
        Which affordability-gap income scenario to use. One of
        30000.0, 48000.0, 75000.0, 110000.0, 150000.0.
        (The affordability dataset has one row per institution per bracket;
        filtering to one bracket yields one row per institution.)
    force_reload : bool
        Rebuild features from the source data instead of the Parquet cache.

    Returns
    -------
    pd.DataFrame
    """
    cache_dir = _get_cache_dir(data_dir)
    cache_path = os.path.join(
        cache_dir, f'college_features_{int(earnings_ceiling)}.parquet')

    if not force_reload and os.path.exists(cache_path):
        df = pd.read_parquet(cache_path)
        print(f"Loaded {len(df)} institutions from feature cache")
        return df

    df = load_merged_data(
        data_dir=data_dir,
        join_key='UNITID',
        earnings_ceiling=earnings_ceiling,
        force_reload=force_reload,
    )

    print(f"Computing features for {len(df)} institutions...")
    df = add_roi_score(df)
    df = add_affordability_scores(df)
    df = add_equity_scores(df)
    df = add_access_score(df)
    df = add_support_infrastructure_index(df)
    df = add_environment_features(df)
    df = add_academic_offerings_index(df)
    df = add_selectivity_buckets(df)

    df.to_parquet(cache_path, engine='pyarrow', compression='snappy')
    print(f"Feature engineering complete: {len(df)} institutions, "
          f"{len(df.columns)} columns (cached to {cache_path})")

    return df


if __name__ == "__main__":
    featured_df = build_college_features(force_reload=True)

    score_cols = [
        'roi_score', 'afford_score_std', 'afford_score_parent', 'equity_parity',
        'access_score_base', 'support_infrastructure_score',
        'environment_diversity_score', 'academic_offerings_score',
    ]
    print("\nIndex summary statistics:")
    print(featured_df[score_cols].describe().round(3))

    print("\nSelectivity distribution:")
    print(featured_df['selectivity_bucket'].value_counts())
