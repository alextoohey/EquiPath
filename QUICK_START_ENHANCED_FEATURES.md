# Quick Start: Enhanced Features for EquiPath

## What's New? 🎉

Your EquiPath project now has **3 powerful new indices** plus enhanced user profiling to provide truly personalized, equity-aware college recommendations!

---

## The Three New Indices

### 1. 📚 **Support Infrastructure Index**
**Helps**: First-gen students, student-parents, low-income students, nontraditional students

**Measures**: Student-faculty ratio, endowment per student, instructional spending, Pell support experience, retention

**Why it matters**: Shows which schools actually **support** students to success, not just admit them

---

### 2. 🏫 **Environment & Personalization Index**
**Helps**: All students find where they'll feel comfortable and belong

**Measures**: Size, urban/rural setting, region, Carnegie type, campus diversity

**Why it matters**: A "good" school is only good if it's a **good fit** for YOU

---

### 3. 📖 **Academic Offerings Index**
**Helps**: Students match to schools strong in their intended field

**Measures**: Degree level, research capacity, field-specific program strength (STEM, Business, Health, etc.)

**Why it matters**: Not all schools are equally strong in all fields

---

## Quick Usage

### Option 1: Use Enhanced Feature Engineering

```python
from src.enhanced_feature_engineering import build_enhanced_featured_college_df

# Load data with all new indices
colleges_df = build_enhanced_featured_college_df(
    data_dir='data',
    earnings_ceiling=30000.0  # Lowest income bracket
)

# Now you have these scores for every college:
# - support_infrastructure_score
# - environment_diversity_score
# - academic_offerings_score
# - selectivity_bucket (Reach/Target/Safety/Open)
# Plus all original scores (ROI, affordability, equity, access)
```

### Option 2: Use Enhanced User Profile

```python
from src.enhanced_user_profile import EnhancedUserProfile

profile = EnhancedUserProfile(
    # Required
    gpa=3.5,
    annual_budget=20000,

    # Background
    is_first_gen=True,
    is_student_parent=False,
    race_ethnicity="HISPANIC",

    # Preferences
    intended_major="STEM",
    home_state="CA",
    strong_support_services=True,
    msi_preference="HSI",

    # Custom weights (must sum to 1.0)
    weight_affordability=0.30,  # Prioritize affordability
    weight_support=0.25,        # Prioritize support
    weight_equity=0.20,
    weight_roi=0.15,
    weight_academic_fit=0.10,
    weight_environment=0.00
)

print(profile)  # See full profile summary
```

---

## Key Files

| File | Purpose |
|------|---------|
| `src/enhanced_feature_engineering.py` | All new index calculations |
| `src/enhanced_user_profile.py` | Comprehensive user profile schema |
| `ENHANCED_FEATURES_GUIDE.md` | Complete documentation |
| `src/data_loading.py` | Updated to handle earnings ceiling granularity |

---

## What Changed in Data Loading?

**Important**: The Affordability Gap dataset has **5 rows per institution** (one for each family income bracket: 30k, 48k, 75k, 110k, 150k).

**New behavior**:
```python
from src.data_loading import load_merged_data

# Default: Keeps ALL rows (granular by earnings ceiling)
data_all = load_merged_data()  # ~21k rows for ~6k institutions

# Filter to specific income bracket (recommended for feature engineering)
data_low_income = load_merged_data(earnings_ceiling=30000.0)  # ~6k rows

# Aggregate across all income brackets (alternative)
from src.data_loading import aggregate_by_institution
data_aggregated = aggregate_by_institution(data_all)  # ~6k rows
```

---

## Selectivity Bucketing (Reach/Target/Safety)

Every college now has a `selectivity_bucket`:

- **Reach**: Admission rate < 30% (highly selective)
- **Target**: Admission rate 30-60%
- **Safety**: Admission rate > 60%
- **Open**: Open admissions policy

Use this to help students build **balanced** college lists!

```python
# Filter by selectivity
reach_schools = colleges_df[colleges_df['selectivity_bucket'] == 'Reach']
safety_schools = colleges_df[colleges_df['selectivity_bucket'] == 'Safety']
```

---

## Field-Specific Strength Scores

Now you can match students to schools strong in their field:

```python
# Available field strength scores:
- stem_strength
- business_strength
- health_strength
- social_sciences_strength
- arts_and_humanities_strength
- education_strength

# Example: Find top STEM schools
top_stem = colleges_df.nlargest(20, 'stem_strength')
```

---

## Example: Complete Matching Pipeline

```python
from src.enhanced_user_profile import EnhancedUserProfile
from src.enhanced_feature_engineering import build_enhanced_featured_college_df

# 1. Create student profile
student = EnhancedUserProfile(
    gpa=3.2,
    annual_budget=18000,
    family_income=28000,  # Auto-sets earnings_ceiling_match = 30000.0
    is_first_gen=True,
    is_student_parent=True,
    race_ethnicity="BLACK",
    age=26,
    home_state="TX",
    intended_major="Health",
    strong_support_services=True,

    # Prioritize affordability and support
    weight_affordability=0.35,
    weight_support=0.25,
    weight_equity=0.20,
    weight_roi=0.15,
    weight_academic_fit=0.05
)

# 2. Load enhanced college data
colleges = build_enhanced_featured_college_df(
    earnings_ceiling=student.earnings_ceiling_match  # 30000.0
)

# 3. Apply filters
filtered = colleges[
    (colleges['State of Institution'] == student.home_state) &
    (colleges['is_for_profit'] == 0) &  # Exclude for-profit
    (colleges['selectivity_bucket'].isin(['Target', 'Safety', 'Open']))  # Realistic
]

# 4. Calculate personalized composite score
weights = student.get_composite_weight_dict()
filtered['composite_score'] = (
    weights['affordability'] * filtered['afford_score_parent'] +  # Parent score!
    weights['support'] * filtered['support_infrastructure_score'] +
    weights['equity'] * filtered['equity_parity'] +
    weights['roi'] * filtered['roi_score'] +
    weights['academic_fit'] * filtered['health_strength']  # Health field!
)

# 5. Get top 10 recommendations
recommendations = filtered.nlargest(10, 'composite_score')[[
    'Institution Name',
    'City',
    'selectivity_bucket',
    'composite_score',
    'afford_score_parent',
    'support_infrastructure_score',
    'health_strength'
]]

print(recommendations)
```

---

## Integration with Existing Code

### Update `scoring.py`:
```python
# Add to imports
from src.enhanced_feature_engineering import (
    add_support_infrastructure_index,
    add_environment_personalization_index,
    add_academic_offerings_index,
    add_selectivity_bucketing
)

# Add to scoring function
df = add_support_infrastructure_index(df)
df = add_environment_personalization_index(df)
df = add_academic_offerings_index(df)
df = add_selectivity_bucketing(df)
```

### Update Streamlit App:
```python
# Add new questions
intended_major = st.selectbox(
    "Intended Major",
    ["Undecided", "STEM", "Business", "Health", "Social Sciences",
     "Arts & Humanities", "Education"]
)

msi_interest = st.selectbox(
    "Interest in Minority-Serving Institutions",
    ["No preference", "HBCU", "HSI", "Tribal College", "Any MSI"]
)

# Add weight sliders
weight_support = st.slider("Support Infrastructure Importance", 0.0, 1.0, 0.15)
weight_academic_fit = st.slider("Academic Fit Importance", 0.0, 1.0, 0.15)
```

---

## Fairness & Ethics Notes

### ✅ What We DO:
- Show students graduation rates for **their own demographic group**
- Identify schools serving **specific populations** (HBCUs, HSIs, etc.)
- Measure **equity gaps** at institutions
- Upweight schools with **smaller racial disparities**

### ❌ What We DON'T DO:
- ~~Make assumptions about student capabilities based on race~~
- ~~Downweight schools serving underrepresented minorities~~
- ~~Use demographics to limit student options~~
- ~~Treat all students as interchangeable~~

**Principle**: Use demographic data to **empower** students with relevant information, not to **constrain** their opportunities.

---

## Next Steps

1. ✅ **Done**: Created enhanced indices
2. ✅ **Done**: Created enhanced user profile
3. ✅ **Done**: Updated data loading to handle granularity
4. **TODO**: Integrate with existing `scoring.py`
5. **TODO**: Update Streamlit app with new questions
6. **TODO**: Add LLM explanations for recommendations
7. **TODO**: Create Tableau visualizations
8. **TODO**: Write fairness audit notebook

---

## Testing

Test with the example profiles:

```python
from src.enhanced_user_profile import EXAMPLE_PROFILES

# Three ready-to-use profiles:
low_income_parent = EXAMPLE_PROFILES['low_income_parent']
international_stem = EXAMPLE_PROFILES['international_stem']
first_gen_hsi = EXAMPLE_PROFILES['first_gen_hsi']

print(low_income_parent)
```

---

## Questions?

See `ENHANCED_FEATURES_GUIDE.md` for complete documentation including:
- Full data column mapping
- Detailed index formulas
- Ethics considerations
- Advanced usage examples

**Remember**: The goal is to **democratize access** to high-quality college advice for students from all backgrounds, especially those historically underserved by traditional college counseling.
