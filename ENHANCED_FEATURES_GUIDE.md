# Enhanced Feature Engineering Guide for EquiPath

## Overview

This guide documents the comprehensive enhanced feature engineering system built for the Educational Equity track. The system extends beyond basic college rankings to provide **equity-aware, personalized college recommendations** that account for the full complexity of student needs.

## Table of Contents
1. [New Indices](#new-indices)
2. [Data Column Mapping](#data-column-mapping)
3. [User Profile Enhancements](#user-profile-enhancements)
4. [Fairness & Ethics](#fairness--ethics)
5. [Usage Examples](#usage-examples)

---

## New Indices

### 1. **Support Infrastructure Index** 📚

**Purpose**: Identifies schools with strong support systems, critical for first-generation, low-income, student-parent, and nontraditional students.

**Components** (weighted):
- **Student-Faculty Ratio** (25%) - Lower is better (more individual attention)
- **Endowment per Student** (20%) - Higher indicates more resources
- **Instructional Expenditure per Student** (20%) - Investment in academic quality
- **Pell Grant Percentage** (15%) - Experience supporting low-income students
- **Retention** (10%) - Based on inverse of transfer-out rate
- **Nontraditional Student Support** (10%) - Percentage of students age 25+

**Data Sources**:
```python
# From College Results 2021 dataset:
- 'Student-to-Faculty Ratio'
- 'Public Institution GASB Endowment Assets'
- 'Private not-for-profit or Public Institution FASB Endowment Assets'
- 'Number of Undergraduates'
- 'Instructional Expenditures per Full-Time Equivalent Student'
- 'Percent Receiving Pell Grants'
- 'Transfer-Out Rate'
- 'Percent of Undergraduates Age 25 and Older'
```

**Why It Matters**:
- First-gen students need schools experienced with their needs
- Student-parents need flexible, supportive environments
- Low-income students benefit from schools with strong financial aid offices (Pell experience)
- Older/nontraditional students need schools that understand their unique circumstances

---

### 2. **Environment & Personalization Index** 🏫

**Purpose**: Helps students find campuses where they'll feel comfortable and belong, rather than treating all students as interchangeable.

**Components**:

**Categorical Features** (for filtering, not scoring):
- **Size**: Small / Medium / Large
- **Urbanization**: Urban / Suburban / Town / Rural
- **Region**: Geographic region (1-9)
- **Carnegie Classification**: Doctoral / Master's / Baccalaureate / Associate's
- **Control**: Public / Private Nonprofit / For-Profit
- **State & City**: Geographic location

**Diversity Score** (composite metric):
- International student presence
- Nontraditional student presence
- Economic diversity (Pell percentage)

**Data Sources**:
```python
# From College Results 2021:
- 'Institution Size Category'
- 'Degree of Urbanization'
- 'Region #'
- 'State of Institution'
- 'City'
- '2021 Carnegie Classification'
- 'Control of Institution'
- 'Percent International Students'
- 'Percent of Undergraduates Age 25 and Older'
- 'Percent Receiving Pell Grants'
```

**Why It Matters**:
- Students from rural areas may prefer similar settings (or want to experience urban life)
- LGBTQ+ students may prefer certain regions or urban areas
- International students benefit from campuses with existing international communities
- Students of color may prefer diverse campuses

---

### 3. **Academic Offerings Index** 📖

**Purpose**: Matches students to schools strong in their intended field, rather than using generic rankings.

**Components** (weighted):
- **Degree Level Offered** (35%) - Certificate → Doctoral scale
- **Research Intensity** (35%) - Based on Carnegie classification
- **Degree Production Volume** (30%) - Number of bachelor's degrees awarded

**Field-Specific Strength Indicators**:
- STEM (Biology, CS, Engineering, Math, Physical Sciences)
- Business
- Health Professions
- Social Sciences
- Arts & Humanities
- Education

**Data Sources**:
```python
# From College Results 2021:
- 'Highest Degree Offered'
- '2021 Carnegie Classification'
- 'Number of Bachelor Degrees Grand Total'
- 'Number of Bachelor Degrees [Field Name]' (for each field)
```

**Why It Matters**:
- A student interested in Engineering should see schools strong in Engineering
- Students interested in research need doctoral institutions
- Community colleges serve important role for associate's degrees and transfer pathways

---

### 4. **Selectivity Bucketing** (Reach/Target/Safety)

**Purpose**: Helps students build balanced college lists with realistic expectations.

**Buckets**:
- **Reach**: Admission rate < 30% (highly selective)
- **Target**: Admission rate 30-60% (moderately selective)
- **Safety**: Admission rate > 60% (less selective)
- **Open**: Open admissions policy

**Data Sources**:
```python
- 'Total Percent of Applicants Admitted'
- 'Open Admissions Policy'
```

**Why It Matters**:
- Prevents students from applying only to reach schools
- Encourages realistic planning
- Identifies safety schools for students

---

## Enhanced Existing Indices

### **ROI Index** (Enhanced)

**Original Components**:
- Median earnings 10 years after entry (60%)
- Median debt of completers (40%)

**Potential Enhancements** (if columns available):
- Loan default rate (lower is better)
- Employment rate
- Earnings by field of study

---

### **Equity Index** (Enhanced)

**Original Components**:
- Race-specific graduation rates
- Graduation rate parity (disparity between highest and lowest)

**Enhancements**:
- MSI flags (HBCU, HSI, Tribal, AANAPII, PBI, NANTI)
  - Used to identify institutions serving specific populations
  - Not used to penalize institutions
- First-generation student outcomes (if available)

**Critical Ethical Note**:
Race/ethnicity is used **ONLY** to:
1. Show students graduation rates for their own demographic group
2. Identify MSI institutions
3. Calculate equity parity (disparity measure)

Race is **NEVER** used to:
- Downweight schools serving underrepresented minorities
- Make assumptions about student capabilities
- Exclude students from opportunities

---

### **Affordability Index** (Enhanced)

**Now Accounts For**:
- Multiple earnings ceiling scenarios (30k, 48k, 75k, 110k, 150k)
- Student-parent affordability (child care costs)
- Weekly hours needed to close affordability gap
- State minimum wage differences

**Data Sources**:
```python
# From Affordability Gap dataset:
- 'Student Family Earnings Ceiling'
- 'Net Price'
- 'Affordability Gap (net price minus income earned working 10 hrs at min wage)'
- 'Weekly Hours to Close Gap'
- 'Student Parent Affordability Gap: Center-Based Care'
- 'Student Parent Affordability Gap: Home-Based Care'
- '100% TTD Affordability Gap'
- '150% TTD Affordability Gap'
```

---

## Data Column Mapping

### Complete List of Used Columns

#### From **College Results View 2021**:

**Academic Outcomes**:
- `Median Earnings of Students Working and Not Enrolled 10 Years After Entry`
- `Median Debt of Completers`
- `Bachelor's Degree Graduation Rate Within 6 Years - [Race]`
  - Available for: Black Non-Latino, White Non-Latino, Hispanic, Asian, Native American, Pacific Islander

**Admissions & Access**:
- `Total Percent of Applicants Admitted`
- `Open Admissions Policy`
- `SAT Reading 25th Percentile Score` (if available)
- `SAT Math 25th Percentile Score` (if available)
- `ACT Composite 25th Percentile Score` (if available)

**Institution Characteristics**:
- `UNIQUE_IDENTIFICATION_NUMBER_OF_THE_INSTITUTION` (Unit ID)
- `Institution Name`
- `Sector of Institution`
- `Control of Institution`
- `Institutional Category`
- `Institution Level`
- `Institution Size Category`

**Support Infrastructure**:
- `Student-to-Faculty Ratio`
- `Public Institution GASB Endowment Assets`
- `Private not-for-profit or Public Institution FASB Endowment Assets`
- `Instructional Expenditures per Full-Time Equivalent Student`
- `Percent Receiving Pell Grants`
- `Transfer-Out Rate`
- `Percent of Undergraduates Age 25 and Older`
- `Number of Undergraduates`

**Location & Environment**:
- `State of Institution`
- `City`
- `Region #`
- `Sub Region #`
- `Degree of Urbanization`
- `Latitude`
- `Longitude`
- `County Name`
- `Zip Code`

**Academic Offerings**:
- `Highest Degree Offered`
- `2021 Carnegie Classification`
- `2018 Carnegie Classification`
- `2015 Carnegie Classification`
- `2000 Carnegie Classification`
- `Number of Bachelor Degrees Grand Total`
- `Number of Bachelor Degrees [Field]` for fields:
  - Biological And Biomedical Sciences
  - Computer And Information Sciences
  - Engineering
  - Mathematics And Statistics
  - Physical Sciences
  - Business, Management, Marketing
  - Health Professions And Related Programs
  - Social Sciences
  - Visual And Performing Arts
  - English Language And Literature/Letters
  - Education

**Diversity & MSI Status**:
- `MSI Status`
- `MSI Type`
- `HBCU`
- `PBI` (Predominantly Black Institution)
- `ANNHI` (Alaska Native/Native Hawaiian-Serving Institution)
- `TRIBAL` (Tribal College or University)
- `AANAPII` (Asian American and Native American Pacific Islander-Serving Institution)
- `HSI` (Hispanic-Serving Institution)
- `NANTI` (Native American Non-Tribal Institution)
- `Percent International Students` (if available)

#### From **Affordability Gap Data AY2022-23**:

**Financial Aid**:
- `Unit ID`
- `Institution Name`
- `Student Family Earnings Ceiling` (30k, 48k, 75k, 110k, 150k)
- `Net Price`
- `Cost of Attendance: In State, On Campus`
- `Cost of Attendance: Out of State`
- `Average Work Study Award`

**Affordability Metrics**:
- `Affordability Gap (net price minus income earned working 10 hrs at min wage)`
- `Weekly Hours to Close Gap`
- `100% TTD Affordability Gap`
- `150% TTD Affordability Gap`

**Student-Parent Metrics**:
- `Student Parent Affordability Gap: Center-Based Care`
- `Student Parent Affordability Gap: Home-Based Care`
- `Monthly Center-Based Child Care Cost`
- `Monthly Home-Based Child Care Cost`
- `Annual Center-Based Child Care Cost`
- `Annual Home-Based Child Care Cost`

**Economic Context**:
- `State Minimum Wage`
- `Annual Income Estimate`
- `Income Earned from Working 10 Hours a Week at State's Minimum Wage`

---

## User Profile Enhancements

### New `EnhancedUserProfile` Fields

**Academic Background**:
- `test_score_status`: "submitted", "test_optional", "no_test"
- `sat_score`: Optional SAT score (400-1600)
- `act_score`: Optional ACT score (1-36)
- `intended_major`: Field of study interest

**Financial Details**:
- `family_income`: For better affordability matching
- `earnings_ceiling_match`: Which income bracket data to use
- `work_study_needed`: Boolean flag
- `is_pell_eligible`: Auto-detected from income

**Special Populations**:
- `is_international`: International student status
- `is_nontraditional`: Age 25+ or other factors
- `age`: Student's age

**Geographic Preferences**:
- `preferred_regions`: List of region numbers
- `preferred_states`: List of state codes
- `max_distance_from_home`: Distance constraint in miles

**Environment Preferences**:
- `urbanization_pref`: urban, suburban, town, rural
- `carnegie_pref`: Preferred institution types
- `msi_preference`: Interest in specific MSI types

**Academic Priorities**:
- `research_opportunities`: Boolean
- `small_class_sizes`: Boolean
- `strong_support_services`: Boolean

**Selectivity Control**:
- `include_reach_schools`: Boolean
- `include_target_schools`: Boolean
- `include_safety_schools`: Boolean
- `include_open_admission`: Boolean

**Customizable Weights**:
Users can adjust importance of each index:
- `weight_roi` (default: 0.20)
- `weight_affordability` (default: 0.25)
- `weight_equity` (default: 0.20)
- `weight_support` (default: 0.15)
- `weight_academic_fit` (default: 0.15)
- `weight_environment` (default: 0.05)

---

## Fairness & Ethics

### How Race/Ethnicity is Used

**✅ Appropriate Uses**:
1. **Show race-specific outcomes**: Students see graduation rates for their own demographic group
2. **Identify MSI institutions**: Flag schools serving specific populations (HBCUs, HSIs, etc.)
3. **Calculate equity parity**: Measure disparities between groups at an institution
4. **Upweight equitable institutions**: Favor schools with smaller racial outcome gaps

**❌ Inappropriate Uses** (Explicitly Avoided):
1. ~~Assume student capabilities based on race~~
2. ~~Downweight institutions serving underrepresented minorities~~
3. ~~Use race as a proxy for academic preparedness~~
4. ~~Limit student options based on race~~

### Gender Usage

**Current Approach**: Gender is collected but **not heavily used** in scoring because:
- Most institutions don't report gender-specific graduation rates
- Using gender could reinforce stereotypes
- Focus should be on outcome equity, not gender matching

**Potential Use**: Identifying women's colleges or highlighting STEM programs with strong women's support

### Age & Nontraditional Students

**Approach**: Age 25+ students have different needs:
- Use `Percent of Undergraduates Age 25 and Older` to identify supportive schools
- Upweight support infrastructure for nontraditional students
- Consider evening/online program availability (if data available)

### International Students

**Approach**:
- Use `Percent International Students` as a proxy for international support
- International students may benefit from campuses with existing international communities
- Consider visa support (data not currently available)

### For-Profit Institutions

**Recommendation**: **Exclude by default** (`exclude_for_profit=True`)

**Rationale**:
- Often have poor outcomes for low-income students
- Higher debt burdens
- Lower graduation rates
- History of predatory practices

**Exception**: Users can override if they have specific reasons

---

## Usage Examples

### Example 1: Low-Income Student-Parent

```python
from src.enhanced_user_profile import EnhancedUserProfile
from src.enhanced_feature_engineering import build_enhanced_featured_college_df

# Create profile
profile = EnhancedUserProfile(
    # Academic
    gpa=3.2,
    test_score_status="test_optional",
    intended_major="Health",

    # Financial - emphasize affordability
    annual_budget=15000,
    family_income=25000,  # Auto-sets earnings_ceiling_match to 30000.0
    work_study_needed=True,
    is_pell_eligible=True,  # Auto-detected

    # Background
    is_first_gen=True,
    is_student_parent=True,
    race_ethnicity="BLACK",
    age=28,  # Auto-sets is_nontraditional=True

    # Location
    home_state="CA",
    in_state_only=True,

    # Preferences
    institution_type_pref="public",
    strong_support_services=True,

    # Custom weights - prioritize affordability and support
    weight_affordability=0.35,  # Increased from 0.25
    weight_support=0.25,        # Increased from 0.15
    weight_equity=0.20,
    weight_roi=0.15,            # Decreased from 0.20
    weight_academic_fit=0.05,   # Decreased from 0.15
    weight_environment=0.00
)

# Load enhanced data with matching earnings ceiling
colleges_df = build_enhanced_featured_college_df(
    earnings_ceiling=profile.earnings_ceiling_match  # 30000.0
)

# Filter to profile preferences
filtered = colleges_df[
    (colleges_df['State of Institution'] == profile.home_state) &
    (colleges_df['is_public'] == 1) &
    (colleges_df['exclude_for_profit'] == False)  # Not for-profit
]

# Calculate composite score with custom weights
weights = profile.get_composite_weight_dict()
filtered['composite_score'] = (
    weights['affordability'] * filtered['afford_score_parent'] +  # Use parent score!
    weights['support'] * filtered['support_infrastructure_score'] +
    weights['equity'] * filtered['equity_parity'] +
    weights['roi'] * filtered['roi_score'] +
    weights['academic_fit'] * filtered['health_strength'] +  # Field-specific
    weights['environment'] * filtered['environment_diversity_score']
)

# Get top recommendations
top_10 = filtered.nlargest(10, 'composite_score')
```

### Example 2: International STEM Student

```python
profile = EnhancedUserProfile(
    # Academic
    gpa=3.8,
    test_score_status="submitted",
    sat_score=1450,
    intended_major="STEM",

    # Financial
    annual_budget=45000,
    family_income=85000,  # Sets earnings_ceiling_match to 110000.0

    # Background
    is_international=True,
    race_ethnicity="ASIAN",
    age=18,

    # Preferences - wants research universities
    research_opportunities=True,
    carnegie_pref=["doctoral", "masters"],
    include_reach_schools=True,

    # Weights - emphasize ROI and academic fit
    weight_roi=0.30,
    weight_academic_fit=0.25,  # Increased for STEM focus
    weight_affordability=0.20,
    weight_support=0.10,
    weight_equity=0.10,
    weight_environment=0.05
)

# Calculate composite with STEM field strength
filtered['composite_score'] = (
    weights['roi'] * filtered['roi_score'] +
    weights['academic_fit'] * filtered['stem_strength'] +  # STEM-specific!
    weights['affordability'] * filtered['afford_score_std'] +
    weights['support'] * filtered['support_infrastructure_score'] +
    weights['equity'] * filtered['equity_parity'] +
    weights['environment'] * filtered['intl_presence_norm']  # International presence!
)
```

### Example 3: First-Gen Student Interested in HSI

```python
profile = EnhancedUserProfile(
    # Academic
    gpa=3.5,
    intended_major="Business",

    # Financial
    annual_budget=20000,
    family_income=40000,

    # Background
    is_first_gen=True,
    race_ethnicity="HISPANIC",

    # Preferences - interested in Hispanic-Serving Institutions
    msi_preference="HSI",
    preferred_states=["TX", "CA", "AZ", "NM"],
    strong_support_services=True,

    # Weights - balanced with emphasis on equity and support
    weight_equity=0.25,
    weight_support=0.20,
    weight_affordability=0.25,
    weight_roi=0.15,
    weight_academic_fit=0.10,
    weight_environment=0.05
)

# Filter to HSI institutions
filtered = colleges_df[
    (colleges_df['HSI'] == 1) &  # Hispanic-Serving Institution flag
    (colleges_df['State of Institution'].isin(profile.preferred_states))
]
```

---

## Implementation Checklist

- [x] Create Support Infrastructure Index
- [x] Create Environment & Personalization features
- [x] Create Academic Offerings Index
- [x] Add Selectivity Bucketing
- [x] Create Enhanced User Profile
- [x] Document all features and data sources
- [ ] Integrate with scoring module
- [ ] Update Streamlit app to use enhanced features
- [ ] Add LLM explanation generation for recommendations
- [ ] Create Tableau dashboard with enhanced indices
- [ ] Write fairness audit notebook
- [ ] Test with diverse user profiles

---

## Next Steps

1. **Integration**: Update `scoring.py` to use enhanced indices
2. **UI Updates**: Add new preference questions to Streamlit
3. **LLM Enhancement**: Generate personalized explanations using all indices
4. **Visualization**: Create Tableau dashboard showing:
   - Support Infrastructure vs Affordability scatter
   - Equity parity vs Institution type
   - Field strength by geographic region
   - MSI distribution map
5. **Testing**: Validate with diverse personas
6. **Ethics Report**: Document fairness considerations and limitations

---

## Contact & Questions

For questions about this enhanced feature system, refer to:
- `src/enhanced_feature_engineering.py` - All index calculations
- `src/enhanced_user_profile.py` - User profile schema
- `src/data_loading.py` - Data loading with earnings ceiling handling

**Remember**: This system is designed to **democratize access** to quality higher education advice, especially for students from vulnerable populations. Every feature should be evaluated through an equity lens.
