"""
Claude integration for EquiPath.

The scoring algorithm decides which colleges to recommend; Claude only explains
those recommendations in plain language. This module builds a structured
summary of a student's ranked matches and asks Claude for per-college
explanations grounded in that data.
"""

import json
from typing import Optional

import pandas as pd

from src.config import get_anthropic_api_key, get_anthropic_model


def build_recommendation_summary(profile, ranked_df, top_k=5):
    """
    Build a structured summary of the profile + top recommendations for Claude.

    Parameters
    ----------
    profile : UserProfile
        Student profile.
    ranked_df : pd.DataFrame
        Ranked colleges from `scoring.rank_colleges_for_user`.
    top_k : int
        Number of top colleges to include.

    Returns
    -------
    dict
    """
    summary = {
        "student_profile": {
            "race": profile.race_ethnicity,
            "is_parent": profile.is_student_parent,
            "first_gen": profile.is_first_gen,
            "budget": profile.annual_budget,
            "income_bracket": profile.family_income,
            "gpa": profile.gpa,
            "intended_major": profile.intended_major,
            "preferences": {
                "in_state_only": profile.in_state_only,
                "state": profile.home_state,
                "public_only": profile.institution_type_pref == "public",
                "school_size_pref": profile.size_pref,
                "urbanization_pref": profile.urbanization_pref,
            },
        },
        "recommendations": [],
    }

    for idx, (_, row) in enumerate(ranked_df.head(top_k).iterrows(), 1):
        college = {
            "rank": idx,
            "name": row.get('Institution Name', 'Unknown'),
            "state": row.get('State of Institution', 'N/A'),
            "sector": row.get('Sector of Institution', 'N/A'),
            "composite_score": float(row.get('composite_score', 0)),
            "metrics": {
                "roi_score": float(row.get('roi_score', 0)),
                "affordability_score": float(row.get('personalized_affordability', 0)),
                "equity_score": float(row.get('personalized_equity', 0)),
                "support_score": float(row.get('personalized_support', 0)),
                "academic_fit": float(row.get('personalized_academic_fit', 0)),
                "access_score": float(row.get('personalized_access', 0)),
            },
            "financials": {
                "net_price": float(pd.to_numeric(
                    row.get('Net Price', 0), errors='coerce') or 0),
                "median_debt": float(pd.to_numeric(
                    row.get('Median Debt of Completers', 0), errors='coerce') or 0),
                "median_earnings_10yr": float(pd.to_numeric(
                    row.get('Median Earnings of Students Working and Not Enrolled 10 Years After Entry', 0),
                    errors='coerce') or 0),
            },
            "admission_rate": float(pd.to_numeric(
                row.get('Total Percent of Applicants Admitted', 50), errors='coerce') or 50),
            "selectivity": row.get('selectivity_bucket', 'Unknown'),
            "archetype": row.get('cluster_label', 'Unknown'),
        }
        summary["recommendations"].append(college)

    return summary


def generate_explanations(summary: dict, api_key: Optional[str] = None):
    """
    Ask Claude for a per-college explanation of the recommendations.

    Parameters
    ----------
    summary : dict
        Output of `build_recommendation_summary`.
    api_key : str, optional
        Anthropic API key; falls back to the ANTHROPIC_API_KEY env var.

    Returns
    -------
    dict
        {"overview": str, "recommendations": [{"name", "why_good_fit"}, ...]}
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        return {
            "overview": "AI explanations require the 'anthropic' package "
                        "(pip install anthropic).",
            "recommendations": [],
        }

    if api_key is None:
        api_key = get_anthropic_api_key()

    if not api_key:
        return {
            "overview": "AI explanations are disabled: no Anthropic API key found. "
                        "Set ANTHROPIC_API_KEY in your .env file to enable them.",
            "recommendations": [],
        }

    client = Anthropic(api_key=api_key)

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

    income_display = profile.get('income_bracket') or 'Not specified'
    if isinstance(income_display, (int, float)):
        income_display = f"${income_display:,.0f}"

    user_prompt = f"""
Student Profile:
- Race/Ethnicity: {profile.get('race', 'Not specified')}
- Intended Major: {profile.get('intended_major', 'Undecided')}
- Student-Parent: {profile.get('is_parent', False)}
- First-Generation: {profile.get('first_gen', False)}
- Budget: ${profile.get('budget', 0):,.0f}
- Income: {income_display}
- GPA: {profile.get('gpa', 'Not specified')}

Top {len(recs)} Recommended Colleges:
{json.dumps(recs, indent=2)}

Please provide a JSON response with the following structure:
{{
  "overview": "A brief paragraph explaining how these recommendations were personalized for this student",
  "recommendations": [
    {{
      "name": "College Name",
      "why_good_fit": "2-3 sentences explaining why this college is a good fit for this specific student, focusing on their unique circumstances, affordability, career outcomes, and support services"
    }}
  ]
}}

IMPORTANT:
1. Return ONLY valid JSON (no markdown code blocks, no extra text)
2. Write dollar amounts WITHOUT the dollar sign (e.g., "33,000" instead of "$33,000")
3. Provide explanations for ALL {len(recs)} colleges in the recommendations list"""

    try:
        response = client.messages.create(
            model=get_anthropic_model(),
            max_tokens=3000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        content = response.content[0].text.strip()

        # Strip markdown code fences if the model added them anyway
        if content.startswith("```"):
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1:
                content = content[start:end + 1]

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"overview": content, "recommendations": []}

    except Exception as e:
        return {
            "overview": f"Error generating AI explanations: {e}",
            "recommendations": [],
        }


if __name__ == "__main__":
    from src.features import build_college_features
    from src.profile import EXAMPLE_PROFILES
    from src.scoring import rank_colleges_for_user

    profile = EXAMPLE_PROFILES['low_income_parent']

    print("Loading data and ranking colleges...")
    df = build_college_features()
    recommendations = rank_colleges_for_user(df, profile, top_k=5)

    summary = build_recommendation_summary(profile, recommendations, top_k=5)
    print("\nSummary sent to Claude:")
    print(json.dumps(summary, indent=2))

    print("\nGenerated explanations:")
    print(json.dumps(generate_explanations(summary), indent=2))
