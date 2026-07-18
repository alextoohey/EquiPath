"""
Smoke tests for the EquiPath recommendation pipeline.

Run with: python -m pytest tests/

These exercise the full path from raw data to ranked recommendations, so the
first run builds the Parquet caches (~30s); later runs take a few seconds.
"""

import pandas as pd
import pytest

from src.clustering import add_clusters
from src.features import build_college_features
from src.profile import UserProfile, EXAMPLE_PROFILES, normalize_state
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


def test_normalize_state():
    assert normalize_state("California") == "CA"
    assert normalize_state("  new york ") == "NY"
    assert normalize_state("tx") == "TX"
    assert normalize_state("CA") == "CA"
    assert normalize_state("Narnia") is None
    assert normalize_state("") is None
    assert normalize_state(None) is None


def test_normalize_state_tolerates_typos():
    assert normalize_state("Califrnia") == "CA"
    assert normalize_state("Massachusets") == "MA"
    assert normalize_state("west virgina") == "WV"
    assert normalize_state("Zzzz") is None


def test_equity_uses_overall_grad_rate_when_race_unspecified(colleges):
    """Without a race, equity should reflect the school's overall graduation
    rate — not a flat constant that makes a 97%-graduation school and a
    20%-graduation school look identical."""
    profile = UserProfile(gpa=3.5, annual_budget=30000)  # race defaults to PREFER_NOT_TO_SAY
    recs = rank_colleges_for_user(colleges, profile, top_k=len(colleges))

    harvard = recs[recs['Institution Name'] == 'Harvard University']
    assert len(harvard) == 1
    row = harvard.iloc[0]
    # 0.7 * grad_rate_total_norm (0.97) + 0.3 * parity — far above the old 0.35 + 0.3*parity floor
    assert row['personalized_equity'] > 0.8

    # A strong default profile should now surface high-graduation institutions
    top_names = set(recs.head(10)['Institution Name'])
    assert top_names & {'Harvard University', 'Stanford University', 'Princeton University',
                        'Williams College', 'Johns Hopkins University'}


def test_multiselect_size_filter_matches_any(colleges):
    profile = UserProfile(gpa=3.0, annual_budget=40000, size_pref=["small", "medium"])
    filtered = filter_colleges_for_user(colleges, profile)

    assert len(filtered) > 0
    sizes = pd.to_numeric(filtered['size_category'], errors='coerce')
    # Only small (1), medium (2), or missing sizes survive
    assert sizes.dropna().isin([1, 2]).all()
    # And both selected sizes are actually represented
    assert {1, 2} <= set(sizes.dropna().unique())


def test_multiselect_msi_filter_matches_any(colleges):
    profile = UserProfile(gpa=3.0, annual_budget=40000, msi_preference=["HBCU", "HSI"])
    filtered = filter_colleges_for_user(colleges, profile)

    assert len(filtered) > 0
    hbcu = pd.to_numeric(filtered.get('HBCU'), errors='coerce').fillna(0) == 1
    hsi = pd.to_numeric(filtered.get('HSI'), errors='coerce').fillna(0) == 1
    assert (hbcu | hsi).all()
    # Both MSI types should be represented, not just one
    assert hbcu.any() and hsi.any()


def test_empty_preferences_mean_no_filtering(colleges):
    open_profile = UserProfile(gpa=3.0, annual_budget=40000)
    pref_profile = UserProfile(gpa=3.0, annual_budget=40000,
                               size_pref=[], urbanization_pref=[], msi_preference=[])
    a = filter_colleges_for_user(colleges, open_profile)
    b = filter_colleges_for_user(colleges, pref_profile)
    assert len(a) == len(b)


def test_clustering_produces_five_labeled_archetypes(colleges):
    clustered, centroids, labels = add_clusters(colleges, n_clusters=5)
    assert clustered['cluster_label'].notna().all()
    assert clustered['cluster_label'].nunique() == 5
    assert len(centroids) == 5
    # Labels are human-readable archetypes, not raw cluster ids
    assert all(isinstance(v, str) and v for v in labels.values())
