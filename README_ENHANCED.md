# EquiPath - Enhanced Educational Equity Platform

## 🎓 Overview

EquiPath is a comprehensive, equity-aware college recommendation system designed to democratize access to high-quality college advice. Built for the Educational Equity Datathon 2025, it goes far beyond traditional rankings to provide personalized recommendations based on students' unique needs and circumstances.

---

## ✨ Key Features

### **8 Comprehensive Indices**
1. **ROI** - Earnings potential vs. debt burden
2. **Affordability** - Net price, affordability gap (student + student-parent specific)
3. **Equity** - Race-specific graduation rates + equity parity
4. **Access** - Selectivity matching (Reach/Target/Safety)
5. **Support Infrastructure** ⭐ NEW - Student services, resources, faculty ratio
6. **Academic Offerings** ⭐ NEW - Field-specific program strength
7. **Environment Fit** ⭐ NEW - Campus culture, size, location
8. **Selectivity Bucketing** ⭐ NEW - Realistic college list building

### **Comprehensive Student Profiles**
- 50+ attributes covering academic, financial, demographic, and preference dimensions
- Customizable scoring weights (you control what matters most)
- Special support for:
  - First-generation students
  - Student-parents
  - Low-income students
  - Nontraditional/older students
  - International students
  - Students from underrepresented groups

### **Equity-Focused Design**
- Demographics used **only** for relevant information (e.g., race-specific graduation rates)
- Excludes predatory for-profit institutions by default
- Transparent fairness principles
- No discriminatory assumptions based on demographics

---

## 🚀 Quick Start

### **1. Run the Enhanced Streamlit App**

```bash
# From project root
streamlit run src/enhanced_app_streamlit_chat.py
```

This launches the interactive chat interface where you:
1. Answer 25 conversational questions about your background and preferences
2. Get personalized recommendations with detailed scoring
3. Explore top colleges with comprehensive information

### **2. Use Programmatically**

```python
from src.enhanced_feature_engineering import build_enhanced_featured_college_df
from src.enhanced_user_profile import EnhancedUserProfile
from src.enhanced_scoring import rank_colleges_for_user

# Create profile
profile = EnhancedUserProfile(
    gpa=3.5,
    annual_budget=20000,
    is_first_gen=True,
    intended_major="STEM",
    home_state="CA",
    strong_support_services=True
)

# Load data
colleges = build_enhanced_featured_college_df(
    earnings_ceiling=profile.earnings_ceiling_match
)

# Get recommendations
recommendations = rank_colleges_for_user(colleges, profile, top_k=10)
```

### **3. Try Example Profiles**

```python
from src.enhanced_user_profile import EXAMPLE_PROFILES

# Three ready-to-use personas
low_income_parent = EXAMPLE_PROFILES['low_income_parent']
international_stem = EXAMPLE_PROFILES['international_stem']
first_gen_hsi = EXAMPLE_PROFILES['first_gen_hsi']
```

---

## 📊 Data Sources

### **College Results View 2021**
- 6,289 institutions
- 192 columns including:
  - Academic outcomes (earnings, debt, graduation rates)
  - Institution characteristics
  - Support infrastructure metrics
  - Demographic breakdowns
  - MSI status flags

### **Affordability Gap Data AY2022-23**
- 21,299 rows (5 per institution for different income brackets)
- 79 columns including:
  - Net price by income level
  - Affordability gaps
  - Student-parent specific costs
  - State minimum wage context

**Important:** The Affordability Gap dataset has multiple rows per institution (one for each family earnings ceiling: $30k, $48k, $75k, $110k, $150k). Our system properly handles this granularity.

---

## 📁 Project Structure

```
7thDatathon/
├── data/
│   ├── College Results View 2021 Data Dump for Export.xlsx
│   └── Affordability Gap Data AY2022-23 2.17.25.xlsx
│
├── src/
│   ├── enhanced_feature_engineering.py    ⭐ NEW - All new indices
│   ├── enhanced_user_profile.py          ⭐ NEW - Comprehensive profile
│   ├── enhanced_scoring.py               ⭐ NEW - Personalized matching
│   ├── enhanced_app_streamlit_chat.py    ⭐ NEW - Interactive chat UI
│   │
│   ├── data_loading.py                   ✅ Updated - Granularity handling
│   ├── feature_engineering.py            ✅ Updated - Earnings ceiling
│   ├── user_profile.py                   (Original, still works)
│   ├── scoring.py                        (Original, still works)
│   ├── app_streamlit_chat.py             (Original, basic version)
│   └── ...
│
├── notebooks/
│   └── eda.ipynb                         ✅ Updated - Granularity docs
│
└── Documentation/
    ├── ENHANCED_FEATURES_GUIDE.md        - Complete technical docs
    ├── QUICK_START_ENHANCED_FEATURES.md  - Quick reference
    ├── INTEGRATION_COMPLETE.md           - Integration summary
    ├── QUICK_COMMANDS.md                 - Command reference
    └── README_ENHANCED.md                - This file
```

---

## 🎯 Use Cases

### **Example 1: Low-Income Student-Parent**
- **Profile:** First-gen, student-parent, limited budget, needs strong support
- **Emphasizes:** Affordability (35%), Support (25%), Equity (20%)
- **Filters:** In-state public schools, safety/target selectivity
- **Result:** Schools with strong support infrastructure, affordable net price, experience with student-parents

### **Example 2: International STEM Student**
- **Profile:** High test scores, interested in research, flexible location
- **Emphasizes:** ROI (30%), Academic Fit (25%), Affordability (20%)
- **Filters:** Doctoral/research universities, STEM strength
- **Result:** Top STEM programs with research opportunities and international community

### **Example 3: First-Gen HSI Interest**
- **Profile:** Hispanic, first-gen, interested in HSI, Southwest region
- **Emphasizes:** Equity (25%), Support (20%), Affordability (25%)
- **Filters:** HSI institutions, TX/CA/AZ/NM
- **Result:** Hispanic-Serving Institutions with strong equity outcomes

---

## ⚖️ Fairness & Ethics

### **How We Use Demographic Data (Appropriately)**

✅ **Race/Ethnicity:**
- Show students graduation rates for their own demographic group
- Identify Minority-Serving Institutions (HBCUs, HSIs, Tribal Colleges, etc.)
- Calculate equity parity (measure outcome disparities)
- Upweight schools with smaller racial outcome gaps

✅ **Age:**
- Identify schools with experience supporting nontraditional (25+) students
- Use "Percent of Undergraduates Age 25+" as proxy for support

✅ **Student-Parent Status:**
- Use student-parent-specific affordability scores
- Include child care costs in financial calculations

✅ **International Status:**
- Identify schools with existing international communities
- Consider international student support

### **What We DON'T Do**

❌ Make assumptions about student capabilities based on demographics
❌ Downweight institutions serving underrepresented minorities
❌ Use demographics to limit opportunities
❌ Recommend for-profit institutions (excluded by default to protect students)

### **Principle**
Use demographic data to **empower** students with relevant information, not to **constrain** their opportunities.

---

## 🔧 Technical Highlights

### **Data Granularity Handling**
- Properly handles Affordability Gap's 5 rows per institution (one per income bracket)
- Filters to specific earnings ceiling or aggregates as needed
- Preserves granularity for accurate affordability matching

### **Personalized Scoring**
- 6 component scores calculated per college-student pair
- Custom weights based on student priorities
- Field-specific academic matching
- Selectivity-aware access scoring

### **Comprehensive Filtering**
- Budget constraints
- Geographic preferences (state, region)
- Institution type (public/private, exclude for-profit)
- Selectivity buckets
- Size and urbanization preferences
- Carnegie classification
- MSI preferences
- Minimum graduation rate

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| `ENHANCED_FEATURES_GUIDE.md` | Complete technical documentation with data mappings |
| `QUICK_START_ENHANCED_FEATURES.md` | Quick reference and examples |
| `INTEGRATION_COMPLETE.md` | Integration summary and testing guide |
| `QUICK_COMMANDS.md` | Command cheat sheet |
| `README_ENHANCED.md` | This file - project overview |

---

## 🧪 Testing

### **Test Individual Modules**
```bash
python src/enhanced_feature_engineering.py
python src/enhanced_user_profile.py
python src/enhanced_scoring.py
```

### **Run Streamlit App**
```bash
streamlit run src/enhanced_app_streamlit_chat.py
```

### **Use Example Profiles**
```python
from src.enhanced_user_profile import EXAMPLE_PROFILES
from src.enhanced_feature_engineering import build_enhanced_featured_college_df
from src.enhanced_scoring import rank_colleges_for_user

# Test with low-income student-parent profile
profile = EXAMPLE_PROFILES['low_income_parent']
colleges = build_enhanced_featured_college_df(30000.0)
recs = rank_colleges_for_user(colleges, profile, top_k=10)

print(recs[['Institution Name', 'composite_score', 'selectivity_bucket']])
```

---

## 🎨 Streamlit App Features

### **Interactive Chat Interface**
- 25+ adaptive questions
- Natural language processing
- Skip optional questions
- Progress tracking
- Smart defaults and auto-detection

### **Comprehensive Recommendations**
- Top 15 personalized matches (configurable)
- Detailed scoring breakdown for each college
- Key institutional information
- Financial details
- Graduation rates and outcomes

### **Profile Summary**
- View complete profile before recommendations
- Understand how scores are calculated
- See personalized weights

---

## 🏆 Impact & Innovation

### **Goes Beyond Traditional Rankings**
- **Traditional rankings:** One-size-fits-all, prestige-focused
- **EquiPath:** Personalized to individual student needs, equity-focused

### **Serves Vulnerable Populations**
- First-generation students who lack college counseling access
- Student-parents who need child care considerations
- Low-income students who need affordability transparency
- Nontraditional students who need flexible, supportive environments
- International students who need community support

### **Democratizes Quality Advice**
- Free, accessible tool
- Transparent methodology
- Comprehensive data coverage
- No hidden biases toward prestige

---

## 📈 Future Enhancements (Optional)

1. **LLM-Powered Explanations:** Generate natural language explanations for why each college is recommended
2. **Tableau Dashboard:** Interactive visualizations of all indices
3. **Fairness Audit:** Systematic testing across diverse personas
4. **Export Functionality:** Save recommendations as CSV/PDF
5. **Financial Aid Estimator:** Estimate aid eligibility
6. **Application Timeline:** Track application deadlines

---

## 👥 Team

Built for Educational Equity Datathon 2025

---

## 📄 License & Usage

This project is designed for educational and social good purposes. Feel free to use, modify, and extend for similar equity-focused applications.

---

## 🙏 Acknowledgments

- Data provided by Educational Equity Datathon 2025
- Inspired by the need to democratize college counseling
- Built with equity and social justice principles at the core

---

## 🚀 Get Started Now!

```bash
streamlit run src/enhanced_app_streamlit_chat.py
```

**Find your perfect college match with EquiPath!** 🎓✨

---

## 📞 Support

For questions, issues, or suggestions:
- Check documentation in project root
- Review `ENHANCED_FEATURES_GUIDE.md` for technical details
- See `QUICK_COMMANDS.md` for usage examples

**Good luck on your college journey!** 🍀
