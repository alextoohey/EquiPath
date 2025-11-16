"""
Test script for AI features (requires OpenAI API key).
"""

import sys
import os
sys.path.append('.')

from src.feature_engineering import build_featured_college_df
from src.user_profile import UserProfile
from src.scoring import rank_colleges_for_user
from src.llm_integration import generate_explanations, build_recommendation_summary

def test_ai_summaries():
    """Test AI summary generation."""

    print("="*80)
    print("TESTING AI FEATURES")
    print("="*80)

    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("\n❌ Error: OPENAI_API_KEY not set")
        print("\nTo test AI features:")
        print("  export OPENAI_API_KEY='your-key-here'")
        print("  python test_ai_features.py")
        return

    print("\n✅ API key found")

    # Load data
    print("\n[1/3] Loading data...")
    df = build_featured_college_df()
    print(f"✅ Loaded {len(df)} institutions")

    # Create test profile
    print("\n[2/3] Creating test profile...")
    profile = UserProfile(
        race="HISPANIC",
        is_parent=True,
        first_gen=True,
        budget=18000,
        income_bracket="LOW",
        gpa=3.4,
        in_state_only=True,
        state="CA",
        public_only=True
    )
    print("✅ Profile created:")
    print(profile)

    # Get recommendations
    print("\n[3/3] Getting recommendations...")
    recommendations = rank_colleges_for_user(df, profile, top_k=5)
    print(f"✅ Found {len(recommendations)} matches")

    if len(recommendations) == 0:
        print("\n⚠️  No matches found for this profile")
        return

    # Generate AI summary
    print("\n" + "="*80)
    print("GENERATING AI SUMMARY")
    print("="*80)

    summary = build_recommendation_summary(profile, recommendations, top_k=5)

    print("\nSummary data structure:")
    print(f"  - Student profile: {summary['student_profile']['race']}, "
          f"{'parent' if summary['student_profile']['is_parent'] else 'non-parent'}")
    print(f"  - Recommendations: {len(summary['recommendations'])} colleges")

    print("\n" + "-"*80)
    print("Calling OpenAI API...")
    print("-"*80)

    explanation = generate_explanations(summary, api_key=api_key)

    print("\n" + "="*80)
    print("AI-GENERATED EXPLANATION")
    print("="*80)
    print(explanation)

    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80)

    print("\nNext steps:")
    print("  1. Review the AI explanation above")
    print("  2. Check if it's personalized and helpful")
    print("  3. Run the Streamlit app: streamlit run src/app_streamlit_chat.py")

if __name__ == "__main__":
    test_ai_summaries()
