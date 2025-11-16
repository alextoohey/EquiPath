"""
LLM integration module for EquiPath project.
Provides natural language explanations and optional free-text profile parsing.
Uses Anthropic's Claude API.
"""

import json
import os
from typing import Optional
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.user_profile import UserProfile


def build_recommendation_summary(profile: UserProfile, ranked_df, top_k=5):
    """
    Build a summary of recommendations for LLM input.

    Parameters:
    -----------
    profile : UserProfile
        Student profile
    ranked_df : pd.DataFrame
        Ranked colleges DataFrame
    top_k : int
        Number of top colleges to include

    Returns:
    --------
    dict
        Summary dictionary for LLM
    """
    import pandas as pd

    summary = {
        "student_profile": {
            "race": profile.race,
            "is_parent": profile.is_parent,
            "first_gen": profile.first_gen,
            "budget": profile.budget,
            "income_bracket": profile.income_bracket,
            "gpa": profile.gpa,
            "preferences": {
                "in_state_only": profile.in_state_only,
                "state": profile.state,
                "public_only": profile.public_only,
                "school_size_pref": profile.school_size_pref
            }
        },
        "recommendations": []
    }

    for idx, (_, row) in enumerate(ranked_df.head(top_k).iterrows(), 1):
        college = {
            "rank": idx,
            "name": row.get('Institution Name', 'Unknown'),
            "state": row.get('State of Institution', 'N/A'),
            "sector": row.get('Sector of Institution', 'N/A'),
            "user_score": float(row.get('user_score', 0)),
            "metrics": {
                "roi_score": float(row.get('roi_score', 0)),
                "affordability_score": float(row.get('afford_score_parent' if profile.is_parent else 'afford_score_std', 0)),
                "equity_parity": float(row.get('equity_parity', 0)),
                "access_score": float(row.get('access_score_base', 0))
            },
            "financials": {
                "net_price": float(pd.to_numeric(row.get('Net Price', 0), errors='coerce')),
                "median_debt": float(pd.to_numeric(row.get('Median Debt of Completers', 0), errors='coerce')),
                "median_earnings_10yr": float(pd.to_numeric(row.get('Median Earnings of Students Working and Not Enrolled 10 Years After Entry', 0), errors='coerce'))
            },
            "admission_rate": float(pd.to_numeric(row.get('Total Percent of Applicants Admitted', 50), errors='coerce')),
            "cluster_archetype": row.get('cluster_label', 'N/A')
        }
        summary["recommendations"].append(college)

    return summary


def generate_explanations(summary: dict, api_key: Optional[str] = None):
    """
    Generate natural language explanations using Anthropic's Claude API.

    Parameters:
    -----------
    summary : dict
        Recommendation summary from build_recommendation_summary()
    api_key : str, optional
        Anthropic API key. If None, will try to get from environment variable.

    Returns:
    --------
    str
        Natural language explanation
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        return "LLM explanations require the 'anthropic' package. Install with: pip install anthropic"

    # Get API key
    if api_key is None:
        api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        return """
LLM explanations are disabled: No Anthropic API key found.

To enable:
1. Set ANTHROPIC_API_KEY environment variable, or
2. Pass api_key parameter to generate_explanations()

For now, here's a template explanation based on the data:
- We found colleges that match your budget and preferences
- Each recommendation is personalized based on your profile
- Higher match scores indicate better overall fit
        """.strip()

    # Initialize client
    client = Anthropic(api_key=api_key)

    # Build prompt
    profile = summary['student_profile']
    recs = summary['recommendations']

    system_prompt = """You are an expert college advising assistant for EquiPath,
an equity-centered college matching tool. Your role is to explain personalized
college recommendations in a warm, supportive, and actionable way.

Focus on:
1. Why these colleges are good matches for this specific student
2. Highlighting equity, affordability, and career outcomes
3. Being honest about tradeoffs (e.g., selectivity vs. affordability)
4. Empowering the student with information

Keep explanations concise but meaningful. Use a supportive, encouraging tone."""

    user_prompt = f"""
Student Profile:
- Race/Ethnicity: {profile['race']}
- Student-Parent: {profile['is_parent']}
- First-Generation: {profile['first_gen']}
- Budget: ${profile['budget']:,}
- Income: {profile['income_bracket']}
- GPA: {profile['gpa']}

Top {len(recs)} Recommended Colleges:
{json.dumps(recs, indent=2)}

Please provide:
1. A brief intro paragraph explaining how these recommendations were personalized
2. For each of the top 3-4 colleges, provide 2-3 bullet points explaining why it's a good fit
3. A concluding thought about next steps

Keep it warm, supportive, and actionable.

IMPORTANT: When mentioning dollar amounts, write them WITHOUT the dollar sign (e.g., "33,000" instead of "$33,000") to avoid formatting issues."""

    try:
        response = client.messages.create(
            model=os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
            max_tokens=1500,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        return response.content[0].text

    except Exception as e:
        return f"Error generating LLM explanation: {str(e)}\n\nPlease check your API key and try again."


def parse_user_text_to_profile(text: str, api_key: Optional[str] = None):
    """
    Parse free-text user description into a structured UserProfile.

    Example input: "I'm a first-gen Black student from California with a 3.4 GPA.
                    I have a baby and can afford about $15,000 per year."

    Parameters:
    -----------
    text : str
        Free-text user description
    api_key : str, optional
        Anthropic API key

    Returns:
    --------
    dict or None
        Profile dictionary that can be used to create a UserProfile,
        or None if parsing failed
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        return None

    # Get API key
    if api_key is None:
        api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        return None

    # Initialize client
    client = Anthropic(api_key=api_key)

    system_prompt = """You are a helpful assistant that extracts student profile
information from natural language text.

Extract the following fields and return ONLY valid JSON (no markdown, no code blocks):
{
  "race": one of ["BLACK", "HISPANIC", "WHITE", "ASIAN", "NATIVE", "PACIFIC", "OTHER"],
  "is_parent": boolean,
  "first_gen": boolean,
  "budget": number (annual budget in dollars),
  "income_bracket": one of ["LOW", "MEDIUM", "HIGH"],
  "gpa": number (0.0-4.0),
  "in_state_only": boolean,
  "state": string (2-letter code) or null,
  "public_only": boolean,
  "school_size_pref": one of ["Small", "Medium", "Large", null]
}

If information is not provided, use reasonable defaults:
- race: "OTHER"
- is_parent: false
- first_gen: false
- budget: 25000
- income_bracket: "MEDIUM"
- gpa: 3.0
- in_state_only: false
- state: null
- public_only: false
- school_size_pref: null"""

    try:
        response = client.messages.create(
            model=os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
            max_tokens=500,
            temperature=0.3,
            system=system_prompt,
            messages=[
                {"role": "user", "content": text}
            ]
        )

        # Parse JSON response
        content = response.content[0].text.strip()

        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        profile_dict = json.loads(content)
        return profile_dict

    except Exception as e:
        print(f"Error parsing user text: {e}")
        return None


if __name__ == "__main__":
    # Test the LLM integration
    from src.user_profile import EXAMPLE_PROFILES
    from src.feature_engineering import build_featured_college_df
    from src.scoring import rank_colleges_for_user

    print("Testing LLM Integration...")
    print("="*60)

    # Use example profile
    profile = EXAMPLE_PROFILES['low_income_parent']

    # Get recommendations
    print("Loading data and getting recommendations...")
    df = build_featured_college_df()
    recommendations = rank_colleges_for_user(df, profile, top_k=5)

    # Build summary
    summary = build_recommendation_summary(profile, recommendations, top_k=5)

    print("\n" + "="*60)
    print("SUMMARY FOR LLM")
    print("="*60)
    print(json.dumps(summary, indent=2))

    print("\n" + "="*60)
    print("GENERATED EXPLANATION")
    print("="*60)

    # Generate explanation
    explanation = generate_explanations(summary)
    print(explanation)

    # Test free-text parsing
    print("\n" + "="*60)
    print("TEST: FREE-TEXT PROFILE PARSING")
    print("="*60)

    test_text = """I'm a Hispanic first-generation student from Texas with a 3.6 GPA.
    I have a child and can afford about $18,000 per year. I prefer public schools."""

    parsed = parse_user_text_to_profile(test_text)
    if parsed:
        print("Parsed profile:")
        print(json.dumps(parsed, indent=2))
    else:
        print("Free-text parsing requires Anthropic API key")
