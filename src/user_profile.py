"""
User profile schema for EquiPath project.
Defines the UserProfile dataclass for student information.
"""

from dataclasses import dataclass, field
from typing import Literal, Optional, List


@dataclass
class UserProfile:
    """
    Represents a student's profile for personalized college matching.

    Attributes:
    -----------
    race : str
        Student's race/ethnicity. Options: "BLACK", "HISPANIC", "WHITE", "ASIAN", "NATIVE", "PACIFIC", "OTHER"
    is_parent : bool
        Whether the student is a parent
    first_gen : bool
        Whether the student is first-generation college student
    budget : float
        Annual budget for college (USD)
    income_bracket : str
        Income bracket. Options: "LOW", "MEDIUM", "HIGH"
    gpa : float
        Student's GPA (0.0 - 4.0 scale)
    region_preferences : List[str]
        Preferred regions (optional). E.g., ["Northeast", "West"]
    in_state_only : bool
        Whether to only consider in-state schools
    state : Optional[str]
        Student's home state (required if in_state_only=True)
    public_only : bool
        Whether to only consider public institutions
    school_size_pref : Optional[str]
        Preferred school size. Options: "Small", "Medium", "Large", None
    intended_field : Optional[str]
        Intended field of study (optional, for future enhancement)
    zip_code : Optional[str]
        Student's zip code (5-digit string, for distance filtering)
    radius_miles : Optional[int]
        Maximum distance in miles from zip code (requires zip_code to be set)
    """
    race: Literal["BLACK", "HISPANIC", "WHITE", "ASIAN", "NATIVE", "PACIFIC", "OTHER"]
    is_parent: bool
    first_gen: bool
    budget: float
    income_bracket: Literal["LOW", "MEDIUM", "HIGH"]
    gpa: float

    # Optional preferences
    region_preferences: List[str] = field(default_factory=list)
    in_state_only: bool = False
    state: Optional[str] = None
    public_only: bool = False
    school_size_pref: Optional[str] = None
    intended_field: Optional[str] = None
    zip_code: Optional[str] = None
    radius_miles: Optional[int] = None

    def __post_init__(self):
        """Validate profile after initialization."""
        # Validate GPA
        if not 0.0 <= self.gpa <= 4.0:
            raise ValueError(f"GPA must be between 0.0 and 4.0, got {self.gpa}")

        # Validate budget
        if self.budget < 0:
            raise ValueError(f"Budget must be non-negative, got {self.budget}")

        # Validate state requirement
        if self.in_state_only and not self.state:
            raise ValueError("state must be provided if in_state_only is True")

        # Validate zip code format (if provided)
        if self.zip_code is not None:
            # Remove any non-digit characters and validate length
            zip_digits = ''.join(filter(str.isdigit, self.zip_code))
            if len(zip_digits) != 5:
                raise ValueError(f"zip_code must be a 5-digit string, got {self.zip_code}")
            self.zip_code = zip_digits  # Normalize to digits only

        # Validate radius requirement
        if self.radius_miles is not None:
            if not self.zip_code:
                raise ValueError("zip_code must be provided if radius_miles is set")
            if self.radius_miles <= 0:
                raise ValueError(f"radius_miles must be positive, got {self.radius_miles}")

    def __str__(self):
        """String representation of the user profile."""
        location_info = []
        if self.state:
            location_info.append(f"State: {self.state}")
        if self.zip_code:
            location_info.append(f"Zip Code: {self.zip_code}")
        if self.radius_miles:
            location_info.append(f"Radius: {self.radius_miles} miles")

        return f"""
UserProfile:
  Race/Ethnicity: {self.race}
  Student-Parent: {self.is_parent}
  First-Generation: {self.first_gen}
  Budget: ${self.budget:,.2f}
  Income Bracket: {self.income_bracket}
  GPA: {self.gpa}
  In-State Only: {self.in_state_only}
  {', '.join(location_info) if location_info else 'Location: Not specified'}
  Public Only: {self.public_only}
  School Size Preference: {self.school_size_pref or 'Any'}
  Intended Field: {self.intended_field or 'Undecided'}
        """.strip()


# Example profiles for testing
EXAMPLE_PROFILES = {
    "low_income_parent": UserProfile(
        race="BLACK",
        is_parent=True,
        first_gen=True,
        budget=15000,
        income_bracket="LOW",
        gpa=3.2,
        in_state_only=True,
        state="CA",
        public_only=True
    ),

    "middle_income_standard": UserProfile(
        race="HISPANIC",
        is_parent=False,
        first_gen=False,
        budget=30000,
        income_bracket="MEDIUM",
        gpa=3.7,
        in_state_only=False,
        public_only=False
    ),

    "high_income_non_parent": UserProfile(
        race="ASIAN",
        is_parent=False,
        first_gen=False,
        budget=60000,
        income_bracket="HIGH",
        gpa=3.9,
        in_state_only=False,
        public_only=False
    ),

    "first_gen_low_income": UserProfile(
        race="WHITE",
        is_parent=False,
        first_gen=True,
        budget=12000,
        income_bracket="LOW",
        gpa=3.5,
        in_state_only=False,
        public_only=True,
        school_size_pref="Medium"
    )
}


if __name__ == "__main__":
    # Test the UserProfile class
    print("Testing UserProfile class...\n")
    print("=" * 60)

    for name, profile in EXAMPLE_PROFILES.items():
        print(f"\n{name.upper()}:")
        print("-" * 60)
        print(profile)

    print("\n" + "=" * 60)
    print("✓ UserProfile validation passed!")
