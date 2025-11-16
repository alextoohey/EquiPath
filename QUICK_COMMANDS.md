# Quick Commands - Enhanced EquiPath

## 🚀 Run the Enhanced System

```bash
# Launch enhanced Streamlit chat app
streamlit run src/enhanced_app_streamlit_chat.py

# OR run original app (basic features only)
streamlit run src/app_streamlit_chat.py
```

---

## 🧪 Test Individual Modules

```bash
# Test enhanced feature engineering
python src/enhanced_feature_engineering.py

# Test enhanced scoring
python src/enhanced_scoring.py

# Test enhanced user profile
python src/enhanced_user_profile.py

# Test data loading (with granularity)
python src/data_loading.py
```

---

## 📊 Quick Python Usage

### **Load Enhanced Data**
```python
from src.enhanced_feature_engineering import build_enhanced_featured_college_df

# Load for lowest income bracket
colleges = build_enhanced_featured_college_df(earnings_ceiling=30000.0)

# Available indices:
# - support_infrastructure_score
# - environment_diversity_score
# - academic_offerings_score
# - selectivity_bucket
# - stem_strength, business_strength, etc.
# Plus all original: roi_score, afford_score_std, equity_parity, access_score_base
```

### **Create User Profile**
```python
from src.enhanced_user_profile import EnhancedUserProfile

profile = EnhancedUserProfile(
    # Required
    gpa=3.5,
    annual_budget=20000,

    # Optional but recommended
    family_income=35000,  # Auto-sets earnings_ceiling_match
    is_first_gen=True,
    intended_major="STEM",
    home_state="CA",
    strong_support_services=True,

    # Custom weights
    weight_affordability=0.30,  # Prioritize affordability
    weight_support=0.25,
    weight_equity=0.20,
    weight_roi=0.15,
    weight_academic_fit=0.10,
    weight_environment=0.00
)
```

### **Get Recommendations**
```python
from src.enhanced_scoring import rank_colleges_for_user

recommendations = rank_colleges_for_user(
    df=colleges,
    profile=profile,
    top_k=15
)

# View results
print(recommendations[[
    'Institution Name',
    'State of Institution',
    'selectivity_bucket',
    'composite_score',
    'personalized_affordability',
    'personalized_support'
]])
```

---

## 📁 Key Files

| What | Where |
|------|-------|
| **Run enhanced app** | `src/enhanced_app_streamlit_chat.py` |
| **All new indices** | `src/enhanced_feature_engineering.py` |
| **Profile schema** | `src/enhanced_user_profile.py` |
| **Matching logic** | `src/enhanced_scoring.py` |
| **Data loading** | `src/data_loading.py` |
| **Complete docs** | `ENHANCED_FEATURES_GUIDE.md` |
| **Quick start** | `QUICK_START_ENHANCED_FEATURES.md` |
| **Integration guide** | `INTEGRATION_COMPLETE.md` |

---

## 🎯 Example Profiles

```python
from src.enhanced_user_profile import EXAMPLE_PROFILES

# Three ready-made personas:
low_income_parent = EXAMPLE_PROFILES['low_income_parent']
international_stem = EXAMPLE_PROFILES['international_stem']
first_gen_hsi = EXAMPLE_PROFILES['first_gen_hsi']

# Use directly:
recommendations = rank_colleges_for_user(colleges, low_income_parent, top_k=10)
```

---

## 🔧 Common Tasks

### **Filter to Specific Earnings Ceiling**
```python
# Load data for middle-income students
colleges_mid = build_enhanced_featured_college_df(earnings_ceiling=75000.0)
```

### **Get All Field Strength Scores**
```python
field_scores = colleges[[
    'Institution Name',
    'stem_strength',
    'business_strength',
    'health_strength',
    'social_sciences_strength',
    'arts_and_humanities_strength',
    'education_strength'
]]
```

### **Filter by Selectivity**
```python
# Get only safety and target schools
realistic = colleges[colleges['selectivity_bucket'].isin(['Safety', 'Target'])]
```

### **Find Top STEM Schools in California**
```python
ca_stem = colleges[
    (colleges['State of Institution'] == 'CA') &
    (colleges['stem_strength'] > 0.7)
].nlargest(10, 'stem_strength')
```

---

## ⚡ One-Liners

```python
# Quick recommendations with example profile
from src.enhanced_user_profile import EXAMPLE_PROFILES
from src.enhanced_feature_engineering import build_enhanced_featured_college_df
from src.enhanced_scoring import rank_colleges_for_user

recs = rank_colleges_for_user(
    build_enhanced_featured_college_df(30000.0),
    EXAMPLE_PROFILES['low_income_parent'],
    top_k=10
)
```

---

## 📊 Data Info

**Earnings Ceiling Values:**
- 30000.0 - Lowest income bracket (4,933 rows)
- 48000.0 - Lower-middle (4,332 rows)
- 75000.0 - Middle (4,103 rows)
- 110000.0 - Upper-middle (3,538 rows)
- 150000.0 - Higher income (2,971 rows)

**Total Institutions:** ~6,256
**Total Rows (all brackets):** ~21,299

---

## 🐛 Quick Fixes

```python
# If you get "No colleges match"
profile.exclude_for_profit = False  # Try including for-profit
profile.in_state_only = False       # Try out-of-state
profile.annual_budget *= 1.5        # Increase budget tolerance

# If earnings ceiling error
profile.earnings_ceiling_match = 30000.0  # Valid: 30k, 48k, 75k, 110k, 150k

# If missing columns error
# Check you're using build_enhanced_featured_college_df(), not build_featured_college_df()
```

---

## 🎨 Streamlit App Flow

1. **Build Profile (Chat)** - Answer 25 questions conversationally
2. **Get Recommendations** - See top 15 personalized matches
3. **View Details** - Explore each college's scores and info

---

## 📖 More Help

- Complete documentation: `ENHANCED_FEATURES_GUIDE.md`
- Quick start guide: `QUICK_START_ENHANCED_FEATURES.md`
- Integration details: `INTEGRATION_COMPLETE.md`

---

**Ready to go!** Run: `streamlit run src/enhanced_app_streamlit_chat.py`
