"""
Comprehensive test script for EquiPath.
Tests all example personas and validates the entire pipeline.
"""

import sys
sys.path.append('.')

from src.feature_engineering import build_featured_college_df
from src.clustering import add_clusters
from src.user_profile import EXAMPLE_PROFILES
from src.scoring import rank_colleges_for_user
import pandas as pd

def test_pipeline():
    """Test the complete EquiPath pipeline with all example profiles."""

    print("="*80)
    print("EQUIPATH - COMPREHENSIVE PIPELINE TEST")
    print("="*80)

    # Step 1: Load and feature engineer data
    print("\n[1/4] Loading and engineering features...")
    df = build_featured_college_df()
    print(f"✓ Loaded {len(df)} institutions with features")

    # Step 2: Add clusters
    print("\n[2/4] Adding cluster archetypes...")
    df_clustered, centroids, labels = add_clusters(df, n_clusters=5)
    print(f"✓ Added {len(labels)} cluster archetypes")

    # Step 3: Test each example profile
    print("\n[3/4] Testing all example profiles...")
    print("="*80)

    results = {}

    for profile_name, profile in EXAMPLE_PROFILES.items():
        print(f"\n{'='*80}")
        print(f"TESTING: {profile_name.upper()}")
        print(f"{'='*80}")

        try:
            # Get recommendations
            recommendations = rank_colleges_for_user(df_clustered, profile, top_k=5)

            if len(recommendations) == 0:
                print(f"\n⚠️  WARNING: No recommendations for {profile_name}")
                results[profile_name] = {
                    'status': 'no_results',
                    'count': 0
                }
            else:
                print(f"\n✓ Found {len(recommendations)} recommendations")

                # Display top 3
                print(f"\nTop 3 Recommendations:")
                display_cols = [
                    'Institution Name',
                    'State of Institution',
                    'user_score',
                    'roi_score',
                    'Net Price',
                    'cluster_label'
                ]
                display_cols = [col for col in display_cols if col in recommendations.columns]

                for idx, (_, row) in enumerate(recommendations.head(3).iterrows(), 1):
                    print(f"\n{idx}. {row.get('Institution Name', 'Unknown')}")
                    print(f"   State: {row.get('State of Institution', 'N/A')}")
                    print(f"   Match Score: {row.get('user_score', 0):.3f}")
                    print(f"   ROI Score: {row.get('roi_score', 0):.3f}")
                    net_price = pd.to_numeric(row.get('Net Price', 0), errors='coerce')
                    print(f"   Net Price: ${net_price:,.0f}")
                    print(f"   Archetype: {row.get('cluster_label', 'N/A')}")

                results[profile_name] = {
                    'status': 'success',
                    'count': len(recommendations),
                    'top_match': recommendations.iloc[0]['Institution Name'] if len(recommendations) > 0 else None,
                    'top_score': recommendations.iloc[0]['user_score'] if len(recommendations) > 0 else None
                }

        except Exception as e:
            print(f"\n❌ ERROR testing {profile_name}: {str(e)}")
            results[profile_name] = {
                'status': 'error',
                'error': str(e)
            }

    # Step 4: Summary report
    print("\n" + "="*80)
    print("[4/4] TEST SUMMARY")
    print("="*80)

    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    total_count = len(results)

    print(f"\nProfiles Tested: {total_count}")
    print(f"Successful: {success_count}")
    print(f"Failed/No Results: {total_count - success_count}")

    print("\nDetailed Results:")
    print("-" * 80)
    for profile_name, result in results.items():
        status_emoji = "✓" if result['status'] == 'success' else "⚠️" if result['status'] == 'no_results' else "❌"
        print(f"{status_emoji} {profile_name:30s} | Status: {result['status']:12s} | Count: {result.get('count', 0)}")
        if result['status'] == 'success' and result.get('top_match'):
            print(f"  → Top match: {result['top_match']} (score: {result.get('top_score', 0):.3f})")

    print("\n" + "="*80)
    if success_count == total_count:
        print("✅ ALL TESTS PASSED!")
    else:
        print(f"⚠️  {total_count - success_count} test(s) had issues")
    print("="*80)

    return results


def test_data_quality():
    """Test data quality and coverage."""

    print("\n" + "="*80)
    print("DATA QUALITY CHECKS")
    print("="*80)

    df = build_featured_college_df()

    # Check key columns
    required_cols = [
        'Institution Name',
        'roi_score',
        'afford_score_std',
        'afford_score_parent',
        'equity_parity',
        'access_score_base'
    ]

    print("\nKey Column Coverage:")
    for col in required_cols:
        if col in df.columns:
            non_null = df[col].notna().sum()
            pct = non_null / len(df) * 100
            print(f"  ✓ {col:30s} | {non_null:5d}/{len(df)} ({pct:5.1f}%)")
        else:
            print(f"  ❌ {col:30s} | MISSING")

    # Check value ranges
    print("\nScore Value Ranges:")
    score_cols = ['roi_score', 'afford_score_std', 'equity_parity', 'access_score_base']
    for col in score_cols:
        if col in df.columns:
            print(f"  {col:30s} | [{df[col].min():.3f}, {df[col].max():.3f}] (mean: {df[col].mean():.3f})")

    # Check for duplicates
    print("\nDuplicate Check:")
    if 'Institution Name' in df.columns:
        dupes = df['Institution Name'].duplicated().sum()
        print(f"  Duplicate institution names: {dupes}")

    print("\n" + "="*80)


if __name__ == "__main__":
    print("\n🎓 EQUIPATH - COMPLETE SYSTEM TEST\n")

    # Run data quality checks
    test_data_quality()

    # Run pipeline tests
    results = test_pipeline()

    print("\n✅ Testing complete!")
    print("\nNext steps:")
    print("  1. Run Streamlit app: streamlit run src/app_streamlit.py")
    print("  2. Test with real user profiles in the web interface")
    print("  3. Review recommendations for quality and relevance")
