# 🚀 EquiPath - Quick Start Guide

Get EquiPath running in 5 minutes!

---

## ✅ Prerequisites

- Python 3.11 (already set up in `.conda/`)
- Data files in `data/` directory (already present)
- All dependencies installed (already done)

---

## 🏃 Quick Start

### Option 1: Run the Streamlit App (Recommended)

```bash
# From the project root directory
.conda/bin/streamlit run src/app_streamlit.py
```

Then open your browser to: **http://localhost:8501**

### Option 2: Test the Pipeline

```bash
# Run comprehensive tests
.conda/bin/python test_all_personas.py
```

### Option 3: Python API Usage

```python
from src.feature_engineering import build_featured_college_df
from src.clustering import add_clusters
from src.user_profile import UserProfile
from src.scoring import rank_colleges_for_user

# Load data
df = build_featured_college_df()
df, centroids, labels = add_clusters(df)

# Create user profile
profile = UserProfile(
    race="BLACK",
    is_parent=True,
    first_gen=True,
    budget=15000,
    income_bracket="LOW",
    gpa=3.2,
    in_state_only=True,
    state="CA"
)

# Get recommendations
recommendations = rank_colleges_for_user(df, profile, top_k=10)

# View results
print(recommendations[['Institution Name', 'State of Institution', 'user_score']])
```

---

## 📱 Using the Streamlit App

1. **Fill out your profile** in the sidebar (left):
   - Select your race/ethnicity
   - Check student-parent if applicable
   - Check first-generation if applicable
   - Enter your annual budget
   - Select income bracket
   - Set your GPA
   - Add any preferences (location, school type, etc.)

2. **Click "Find My Matches"**

3. **Review your recommendations**:
   - See personalized match scores
   - Expand each college for details
   - Compare visually with the chart

---

## 🧪 Testing Different Scenarios

### Low-Income Student-Parent
```python
UserProfile(
    race="BLACK",
    is_parent=True,
    first_gen=True,
    budget=15000,
    income_bracket="LOW",
    gpa=3.2,
    public_only=True
)
```
**Expected**: Affordable institutions with strong equity support

### High-Achieving Student
```python
UserProfile(
    race="ASIAN",
    is_parent=False,
    first_gen=False,
    budget=50000,
    income_bracket="HIGH",
    gpa=3.9
)
```
**Expected**: Mix of selective and accessible schools, balanced recommendations

### First-Gen, Medium Income
```python
UserProfile(
    race="HISPANIC",
    is_parent=False,
    first_gen=True,
    budget=25000,
    income_bracket="MEDIUM",
    gpa=3.5
)
```
**Expected**: Institutions with strong equity outcomes

---

## 📊 Understanding Your Results

### Match Score
- **Range**: 0.0 to 1.0
- **Higher is better**
- Combines: ROI, Affordability, Equity, Access
- **Personalized** based on your profile

### Component Scores

**ROI Score**: Earnings potential vs. debt burden
- Based on median earnings 10 years after graduation
- Considers median debt at completion

**Affordability Score**: Financial accessibility
- Net price relative to your budget
- Affordability gap (for standard students)
- Childcare-adjusted gap (for student-parents)

**Equity Score**: Outcomes for students like you
- Graduation rate for your racial/ethnic group
- Overall equity parity across demographics

**Access Score**: Admission fit
- Admission rate
- Your GPA relative to admitted students
- Safety/Target/Reach classification

---

## 🎯 Interpreting Cluster Archetypes

| Archetype | Characteristics | Good For |
|-----------|----------------|----------|
| **Equity Champions** | High ROI + Equity + Affordable | Most students, especially equity-focused |
| **Accessible & Affordable** | High access + Low cost | Budget-constrained, lower GPA |
| **Good Value Options** | Balanced affordability + ROI | Most students looking for value |
| **Equity-Focused Access** | Strong equity + High access | First-gen, marginalized students |
| **Balanced Options** | Well-rounded across all metrics | Flexible students |

---

## 🔧 Troubleshooting

**No recommendations returned?**
- Try increasing your budget
- Remove location/type filters
- Check that your state code is valid (if using in-state filter)

**App loading slowly?**
- First load takes 10-15 seconds (data loading)
- Subsequent queries are instant (data is cached)

**Want LLM explanations?**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

---

## 📁 Project Structure

```
/
├── data/                    # Excel data files
├── src/                     # All Python modules
│   ├── app_streamlit.py    # ← START HERE (web app)
│   ├── scoring.py          # Core matching logic
│   └── ...
├── test_all_personas.py    # Comprehensive tests
├── QUICKSTART.md           # ← YOU ARE HERE
├── README.md               # Full documentation
└── IMPLEMENTATION_SUMMARY.md  # Technical details
```

---

## 🎓 Example Session

```bash
# 1. Start the app
$ .conda/bin/streamlit run src/app_streamlit.py

  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501

# 2. In the browser:
#    - Fill out profile
#    - Click "Find My Matches"
#    - Review 10 personalized recommendations
#    - Explore detailed metrics
#    - Compare visually

# 3. Try different profiles to see how recommendations change!
```

---

## 💡 Pro Tips

1. **Budget**: Set realistic - this is annual net price, not total cost
2. **Filters**: Start broad, narrow down if too many results
3. **GPA**: Be honest - it affects Safety/Target/Reach classification
4. **In-State**: Can save significantly, especially for public schools
5. **Archetypes**: Look for patterns in your top recommendations

---

## 📞 Need Help?

- Check [README.md](README.md) for detailed documentation
- Review [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for technical details
- Inspect example profiles in `src/user_profile.py`
- Read docstrings in any module

---

## 🎉 Ready to Explore!

You're all set! Launch the app and discover colleges that support your success.

**Remember**: EquiPath centers equity. Every recommendation is personalized for YOU.

---

*Happy college searching! 🎓*
