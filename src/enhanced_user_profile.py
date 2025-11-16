"""
Enhanced User Profile Schema for EquiPath Project

Extends the base UserProfile with comprehensive student dimensions including:
- Demographic information (handled sensitively for equity)
- Academic background and goals
- Financial situation
- Geographic preferences
- Environment and campus culture preferences
- Special populations (international, nontraditional, etc.)
"""

from dataclasses import dataclass, field
from typing import Literal, Optional, List


@dataclass
class EnhancedUserProfile:
    """
    Comprehensive student profile for personalized, equitable college matching.

    Designed to capture all relevant dimensions while being sensitive to:
    - First-generation students
    - Low-income students
    - Student-parents
    - Nontraditional/older students
    - International students
    - Underrepresented minorities

    Core Attributes:
    ----------------
    # Academic Background
    gpa : float
        Student's GPA (0.0 - 4.0 scale)
    test_score_status : str
        SAT/ACT status: "submitted", "test_optional", "no_test"
    sat_score : Optional[int]
        SAT score if available (400-1600)
    act_score : Optional[int]
        ACT score if available (1-36)
    intended_major : Optional[str]
        Field of study: "STEM", "Business", "Health", "Social Sciences",
        "Arts & Humanities", "Education", "Undecided"

    # Financial Situation
    annual_budget : float
        Total annual budget available (USD)
    family_income : Optional[float]
        Family income (optional, for better affordability matching)
    earnings_ceiling_match : float
        Which affordability gap earnings ceiling to use
        (30000.0, 48000.0, 75000.0, 110000.0, 150000.0)
    work_study_needed : bool
        Whether student needs work-study opportunities
    is_pell_eligible : bool
        Whether student is Pell Grant eligible (typically family income < $60k)

    # Demographics (handled sensitively for equity)
    race_ethnicity : Optional[str]
        Race/ethnicity: "BLACK", "HISPANIC", "WHITE", "ASIAN", "NATIVE",
        "PACIFIC", "TWO_OR_MORE", "PREFER_NOT_TO_SAY"
        Used ONLY to:
        - Show race-specific graduation rates
        - Identify MSI institutions
        - Calculate equity metrics
    gender : Optional[str]
        Gender: "Male", "Female", "Non-binary", "Prefer not to say"
        (Currently informational only - may use for women's colleges)

    # Special Populations
    is_first_gen : bool
        First-generation college student
    is_student_parent : bool
        Student with dependent children
    is_international : bool
        International student
    is_nontraditional : bool
        Age 25 or older / nontraditional student
    age : Optional[int]
        Student's age (used to identify nontraditional status)

    # Geographic Preferences
    home_state : Optional[str]
        Student's home state (two-letter code)
    in_state_only : bool
        Limit search to in-state schools
    preferred_regions : List[int]
        Preferred region numbers (0-9 based on dataset)
    preferred_states : List[str]
        Specific preferred states (two-letter codes)
    zip_code : Optional[str]
        Student's 5-digit zip code for distance-based filtering
    max_distance_from_home : Optional[float]
        Maximum distance from home in miles (requires zip_code)

    # Environment & Campus Culture Preferences
    urbanization_pref : Optional[str]
        "urban", "suburban", "town", "rural", "no_preference"
    size_pref : Optional[str]
        "small", "medium", "large", "no_preference"
    institution_type_pref : Optional[str]
        "public", "private_nonprofit", "either" (never recommend for-profit)
    carnegie_pref : Optional[List[str]]
        Preferred Carnegie types: "doctoral", "masters", "baccalaureate",
        "associate"
    msi_preference : Optional[str]
        Interest in MSI: "HBCU", "HSI", "Tribal", "AANAPII", "any_MSI",
        "no_preference"

    # Academic Environment Preferences
    research_opportunities : bool
        Wants research opportunities (favors doctoral institutions)
    small_class_sizes : bool
        Prefers small class sizes (favors low student-faculty ratio)
    strong_support_services : bool
        Needs strong support services (favors high support infrastructure)

    # Selectivity Preferences
    include_reach_schools : bool
        Include highly selective reach schools
    include_target_schools : bool
        Include target schools (admission rate 30-60%)
    include_safety_schools : bool
        Include safety schools (admission rate > 60%)
    include_open_admission : bool
        Include open admission schools

    # Filtering Preferences
    exclude_for_profit : bool
        Exclude for-profit institutions (recommended: True)
    min_graduation_rate : Optional[float]
        Minimum acceptable graduation rate (percent)
    require_data_completeness : bool
        Only show schools with complete data

    Weights for Composite Scoring:
    -------------------------------
    weight_roi : float
        Weight for ROI score (default: 0.20)
    weight_affordability : float
        Weight for affordability (default: 0.25)
    weight_equity : float
        Weight for equity/outcomes (default: 0.20)
    weight_support : float
        Weight for support infrastructure (default: 0.15)
    weight_academic_fit : float
        Weight for academic offerings (default: 0.15)
    weight_environment : float
        Weight for environment fit (default: 0.06)
    weight_access : float
        Weight for admission likelihood/access (default: 0.05)
    """

    # ============ REQUIRED FIELDS (no defaults) ============

    # Academic
    gpa: float

    # Financial
    annual_budget: float

    # ============ FIELDS WITH DEFAULTS ============

    # Academic
    test_score_status: Literal["submitted", "test_optional", "no_test"] = "test_optional"
    earnings_ceiling_match: float = 30000.0  # Default to lowest income bracket

    # Core Demographics
    is_first_gen: bool = False
    is_student_parent: bool = False

    # ============ OPTIONAL FIELDS ============

    # Test Scores
    sat_score: Optional[int] = None
    act_score: Optional[int] = None

    # Academic Goals
    intended_major: Optional[str] = "Undecided"  # STEM, Business, Health, etc.

    # Financial Details
    family_income: Optional[float] = None
    work_study_needed: bool = False
    is_pell_eligible: bool = False

    # Demographics (optional but recommended for equity-aware matching)
    race_ethnicity: Optional[str] = "PREFER_NOT_TO_SAY"
    gender: Optional[str] = "Prefer not to say"

    # Special Populations
    is_international: bool = False
    is_nontraditional: bool = False
    age: Optional[int] = None

    # Geographic
    home_state: Optional[str] = None
    in_state_only: bool = False
    preferred_regions: List[int] = field(default_factory=list)
    preferred_states: List[str] = field(default_factory=list)
    zip_code: Optional[str] = None  # 5-digit zip code for distance calculations
    max_distance_from_home: Optional[float] = None  # Renamed from radius_miles for clarity

    # Environment Preferences
    urbanization_pref: Optional[str] = "no_preference"
    size_pref: Optional[str] = "no_preference"
    institution_type_pref: Optional[str] = "either"
    carnegie_pref: Optional[List[str]] = None
    msi_preference: Optional[str] = "no_preference"

    # Academic Environment
    research_opportunities: bool = False
    small_class_sizes: bool = False
    strong_support_services: bool = False

    # Selectivity
    include_reach_schools: bool = True
    include_target_schools: bool = True
    include_safety_schools: bool = True
    include_open_admission: bool = True

    # Filtering
    exclude_for_profit: bool = True  # Strongly recommended
    min_graduation_rate: Optional[float] = None
    require_data_completeness: bool = False

    # Scoring Weights (must sum to ~1.0)
    weight_roi: float = 0.20
    weight_affordability: float = 0.25
    weight_equity: float = 0.18
    weight_support: float = 0.13
    weight_academic_fit: float = 0.13
    weight_environment: float = 0.06
    weight_access: float = 0.05

    def __post_init__(self):
        """Validate profile after initialization."""
        # Validate GPA
        if not 0.0 <= self.gpa <= 4.0:
            raise ValueError(f"GPA must be between 0.0 and 4.0, got {self.gpa}")

        # Validate budget
        if self.annual_budget < 0:
            raise ValueError(f"Budget must be non-negative, got {self.annual_budget}")

        # Validate test scores
        if self.test_score_status == "submitted":
            if self.sat_score is None and self.act_score is None:
                raise ValueError("Must provide SAT or ACT score if test_score_status is 'submitted'")

        if self.sat_score is not None and not (400 <= self.sat_score <= 1600):
            raise ValueError(f"SAT score must be between 400 and 1600, got {self.sat_score}")

        if self.act_score is not None and not (1 <= self.act_score <= 36):
            raise ValueError(f"ACT score must be between 1 and 36, got {self.act_score}")

        # Validate state requirement
        if self.in_state_only and not self.home_state:
            raise ValueError("home_state must be provided if in_state_only is True")

        # Validate zip code format (if provided)
        if self.zip_code is not None:
            # Remove any non-digit characters and validate length
            zip_digits = ''.join(filter(str.isdigit, self.zip_code))
            if len(zip_digits) != 5:
                raise ValueError(f"zip_code must be a 5-digit string, got {self.zip_code}")
            self.zip_code = zip_digits  # Normalize to digits only

        # Validate max_distance requirement
        if self.max_distance_from_home is not None:
            if not self.zip_code:
                raise ValueError("zip_code must be provided if max_distance_from_home is set")
            if self.max_distance_from_home <= 0:
                raise ValueError(f"max_distance_from_home must be positive, got {self.max_distance_from_home}")

        # Validate earnings ceiling
        valid_ceilings = [30000.0, 48000.0, 75000.0, 110000.0, 150000.0]
        if self.earnings_ceiling_match not in valid_ceilings:
            raise ValueError(f"earnings_ceiling_match must be one of {valid_ceilings}")

        # Validate weights sum to 1.0 (with small tolerance)
        weight_sum = (
            self.weight_roi +
            self.weight_affordability +
            self.weight_equity +
            self.weight_support +
            self.weight_academic_fit +
            self.weight_environment +
            self.weight_access
        )
        if not (0.99 <= weight_sum <= 1.01):
            raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")

        # Auto-detect nontraditional if age provided
        if self.age is not None and self.age >= 25:
            self.is_nontraditional = True

        # Auto-match earnings ceiling to income if provided
        if self.family_income is not None:
            if self.family_income <= 30000:
                self.earnings_ceiling_match = 30000.0
            elif self.family_income <= 48000:
                self.earnings_ceiling_match = 48000.0
            elif self.family_income <= 75000:
                self.earnings_ceiling_match = 75000.0
            elif self.family_income <= 110000:
                self.earnings_ceiling_match = 110000.0
            else:
                self.earnings_ceiling_match = 150000.0

        # Auto-detect Pell eligibility from income
        if self.family_income is not None and self.family_income < 60000:
            self.is_pell_eligible = True

    def get_selectivity_preferences(self) -> List[str]:
        """Get list of selectivity buckets to include."""
        buckets = []
        if self.include_reach_schools:
            buckets.append('Reach')
        if self.include_target_schools:
            buckets.append('Target')
        if self.include_safety_schools:
            buckets.append('Safety')
        if self.include_open_admission:
            buckets.append('Open')
        return buckets

    def get_composite_weight_dict(self) -> dict:
        """Get dictionary of scoring weights for composite calculations."""
        return {
            'roi': self.weight_roi,
            'affordability': self.weight_affordability,
            'equity': self.weight_equity,
            'support': self.weight_support,
            'academic_fit': self.weight_academic_fit,
            'environment': self.weight_environment,
            'access': self.weight_access
        }

    def __str__(self):
        """String representation of enhanced user profile."""
        lines = [
            "=" * 60,
            "ENHANCED USER PROFILE",
            "=" * 60,
            "",
            "ACADEMIC BACKGROUND",
            f"  GPA: {self.gpa:.2f}",
            f"  Test Scores: {self.test_score_status}",
        ]

        if self.sat_score:
            lines.append(f"    SAT: {self.sat_score}")
        if self.act_score:
            lines.append(f"    ACT: {self.act_score}")

        lines.extend([
            f"  Intended Major: {self.intended_major}",
            "",
            "FINANCIAL SITUATION",
            f"  Annual Budget: ${self.annual_budget:,.2f}",
        ])

        if self.family_income:
            lines.append(f"  Family Income: ${self.family_income:,.2f}")

        lines.extend([
            f"  Earnings Ceiling Match: ${self.earnings_ceiling_match:,.0f}",
            f"  Pell Eligible: {self.is_pell_eligible}",
            f"  Work-Study Needed: {self.work_study_needed}",
            "",
            "STUDENT BACKGROUND",
            f"  First-Generation: {self.is_first_gen}",
            f"  Student-Parent: {self.is_student_parent}",
            f"  International: {self.is_international}",
            f"  Nontraditional (Age 25+): {self.is_nontraditional}",
        ])

        if self.age:
            lines.append(f"  Age: {self.age}")

        lines.extend([
            "",
            "GEOGRAPHIC PREFERENCES",
            f"  Home State: {self.home_state or 'Not specified'}",
            f"  In-State Only: {self.in_state_only}",
        ])

        if self.preferred_states:
            lines.append(f"  Preferred States: {', '.join(self.preferred_states)}")

        lines.extend([
            "",
            "ENVIRONMENT PREFERENCES",
            f"  Urbanization: {self.urbanization_pref}",
            f"  Size: {self.size_pref}",
            f"  Institution Type: {self.institution_type_pref}",
            f"  MSI Interest: {self.msi_preference}",
            "",
            "ACADEMIC PRIORITIES",
            f"  Research Opportunities: {self.research_opportunities}",
            f"  Small Class Sizes: {self.small_class_sizes}",
            f"  Strong Support Services: {self.strong_support_services}",
            "",
            "SELECTIVITY",
            f"  Include: {', '.join(self.get_selectivity_preferences())}",
            "",
            "SCORING WEIGHTS",
            f"  ROI: {self.weight_roi:.0%}",
            f"  Affordability: {self.weight_affordability:.0%}",
            f"  Equity: {self.weight_equity:.0%}",
            f"  Support: {self.weight_support:.0%}",
            f"  Academic Fit: {self.weight_academic_fit:.0%}",
            f"  Environment: {self.weight_environment:.0%}",
            "=" * 60
        ])

        return "\n".join(lines)


# ============================================================================
# EXAMPLE PROFILES
# ============================================================================

# Example 1: Low-income, first-gen student-parent
LOW_INCOME_PARENT = EnhancedUserProfile(
    # Academic
    gpa=3.2,
    test_score_status="test_optional",
    intended_major="Health",

    # Financial
    annual_budget=15000,
    family_income=25000,
    work_study_needed=True,
    is_pell_eligible=True,

    # Background
    is_first_gen=True,
    is_student_parent=True,
    race_ethnicity="BLACK",
    age=28,
    is_nontraditional=True,

    # Geographic
    home_state="CA",
    in_state_only=True,

    # Preferences
    institution_type_pref="public",
    strong_support_services=True,

    # Weights - emphasize affordability and support
    weight_affordability=0.30,  # Reduced from 0.35 to make total 1.0
    weight_support=0.25,
    weight_equity=0.20,
    weight_roi=0.15,
    weight_academic_fit=0.05,
    weight_environment=0.00,
    weight_access=0.05  # Added to match the default weight
)

# Example 2: International STEM student
INTERNATIONAL_STEM = EnhancedUserProfile(
    # Academic
    gpa=3.8,
    test_score_status="submitted",
    sat_score=1450,
    intended_major="STEM",

    # Financial
    annual_budget=45000,
    family_income=85000,

    # Background
    is_international=True,
    race_ethnicity="ASIAN",
    age=18,

    # Geographic - no location preference
    preferred_regions=[],

    # Preferences
    research_opportunities=True,
    carnegie_pref=["doctoral", "masters"],
    include_reach_schools=True,

    # Weights - emphasize ROI and academic fit
    weight_roi=0.25,  # Reduced from 0.30 to make total 1.0
    weight_academic_fit=0.25,
    weight_affordability=0.20,
    weight_support=0.10,
    weight_equity=0.10,
    weight_environment=0.05,
    weight_access=0.05  # Added to match the default weight
)

# Example 3: First-gen student interested in MSI
FIRST_GEN_HSI_INTEREST = EnhancedUserProfile(
    # Academic
    gpa=3.5,
    test_score_status="test_optional",
    intended_major="Business",

    # Financial
    annual_budget=20000,
    family_income=40000,
    is_pell_eligible=True,

    # Background
    is_first_gen=True,
    race_ethnicity="HISPANIC",
    age=19,

    # Geographic
    home_state="TX",
    preferred_states=["TX", "CA", "AZ", "NM"],

    # Preferences
    msi_preference="HSI",
    strong_support_services=True,
    institution_type_pref="either",

    # Weights - balanced with emphasis on equity and support
    weight_equity=0.25,
    weight_support=0.20,
    weight_affordability=0.20,  # Reduced from 0.25 to make room for weight_access
    weight_roi=0.15,
    weight_academic_fit=0.10,
    weight_environment=0.05,
    weight_access=0.05  # Added to match the default weight
)

# Collection for easy access
EXAMPLE_PROFILES = {
    "low_income_parent": LOW_INCOME_PARENT,
    "international_stem": INTERNATIONAL_STEM,
    "first_gen_hsi": FIRST_GEN_HSI_INTEREST
}


if __name__ == "__main__":
    # Test profiles
    print("Testing Enhanced User Profiles\n")

    for name, profile in EXAMPLE_PROFILES.items():
        print(f"\n{name.upper().replace('_', ' ')}")
        print(profile)
        print("\n")
