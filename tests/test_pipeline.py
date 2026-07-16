"""
Smoke tests for the EquiPath recommendation pipeline.

Run with: python -m pytest tests/

These exercise the full path from raw data to ranked recommendations, so the
first run builds the Parquet caches (~30s); later runs take a few seconds.
"""

import pandas as pd
import pytest

from src.features import build_college_features
from src.profile import UserProfile, EXAMPLE_PROFILES
from src.scoring import (
    filter_colleges_for_user,
    get_personalized_weights,
    rank_colleges_for_user,
)


@pytest.fixture(scope="session")
def colleges():
    return build_college_features(earnings_ceiling=30000.0)


@pytest.fixture(scope="session")
def low_income_parent():
    return UserProfile(
        gpa=3.2,
        annual_budget=15000,
        race_ethnicity="BLACK",
        is_first_gen=True,
        is_student_parent=True,
        home_state="CA",
        in_state_only=True,
    )


def test_features_build_one_row_per_institution(colleges):
    assert len(colleges) > 4000
    id_col = 'UNIQUE_IDENTIFICATION_NUMBER_OF_THE_INSTITUTION'
    assert colleges[id_col].is_unique


def test_all_indices_are_normalized(colleges):
    index_cols = [
        'roi_score', 'afford_score_std', 'afford_score_parent', 'equity_parity',
        'access_score_base', 'support_infrastructure_score',
        'environment_diversity_score', 'academic_offerings_score',
    ]
    for col in index_cols:
        assert col in colleges.columns, f"missing index column: {col}"
        values = colleges[col].dropna()
        assert values.between(0, 1).all(), f"{col} outside [0, 1]"


def test_selectivity_buckets_present(colleges):
    buckets = set(colleges['selectivity_bucket'].unique())
    assert {'Safety', 'Target', 'Reach'} <= buckets


def test_weights_normalize_to_one(low_income_parent):
    weights = get_personalized_weights(low_income_parent)
    assert abs(sum(weights.values()) - 1.0) < 1e-6
    assert set(weights) == {
        'roi', 'affordability', 'equity', 'support',
        'academic_fit', 'environment', 'access',
    }


def test_filters_respect_hard_constraints(colleges, low_income_parent):
    filtered = filter_colleges_for_user(colleges, low_income_parent)

    assert 0 < len(filtered) < len(colleges)

    # In-state only
    states = filtered['State of Institution'].astype(str).str.upper()
    assert (states == 'CA').all()

    # For-profit institutions excluded
    control = pd.to_numeric(filtered['Control of Institution'], errors='coerce')
    assert (control != 3).all()

    # Budget: net price within 1.5x budget, or missing
    net_price = pd.to_numeric(filtered['Net Price'], errors='coerce')
    assert (net_price.isna() | (net_price <= low_income_parent.annual_budget * 1.5)).all()


def test_ranking_returns_scored_results(colleges, low_income_parent):
    recs = rank_colleges_for_user(colleges, low_income_parent, top_k=10)

    assert len(recs) == 10
    assert recs['composite_score'].between(0, 1).all()
    # Sorted best-first
    assert recs['composite_score'].is_monotonic_decreasing

    component_cols = [
        'personalized_affordability', 'personalized_equity', 'personalized_support',
        'personalized_academic_fit', 'personalized_environment', 'personalized_access',
    ]
    for col in component_cols:
        assert col in recs.columns


def test_example_profiles_all_produce_recommendations(colleges):
    for name, profile in EXAMPLE_PROFILES.items():
        recs = rank_colleges_for_user(colleges, profile, top_k=5)
        assert len(recs) > 0, f"no recommendations for example profile {name}"
