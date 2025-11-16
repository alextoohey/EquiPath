# 🎓 EquiPath: Equity-Centered College Advising Tool

**Track 2: Educational Equity | 7th Annual Datathon**

EquiPath is an equity-centered college matching platform that personalizes recommendations using a comprehensive **Student Success & Equity Score**. Unlike traditional college finders that prioritize prestige or rankings, EquiPath centers the needs of underserved students—including first-generation students, student-parents, and students from historically marginalized communities.

---

## 🌟 Key Features

### 1. **Personalized Student Success & Equity Score**
Our proprietary algorithm combines four key dimensions:
- **💰 Affordability** - Net price, affordability gap, childcare costs (for student-parents)
- **📈 ROI** - Median earnings 10 years post-graduation vs. median debt
- **⚖️ Equity** - Race-specific graduation rates and equity parity across demographics
- **🚪 Access** - Admission selectivity and student GPA fit

### 2. **Dynamic Weight Adjustment**
The scoring weights automatically adjust based on your profile:
- **Low-income students**: Affordability weight increases
- **Student-parents**: Both affordability and equity weights increase
- **First-gen/marginalized students**: Equity weight increases

### 3. **Institution Archetypes**
Colleges are clustered into meaningful archetypes:
- **Equity Champions** - High ROI, high equity, affordable
- **Accessible & Affordable** - Low barriers, good value
- **Good Value Options** - Balanced affordability and outcomes
- **Equity-Focused Access** - Strong support for diverse students
- **Balanced Options** - Well-rounded institutions

### 4. **Data-Driven, Transparent**
- Uses official federal datasets (College Scorecard, Affordability Gap data)
- All scoring logic is transparent and auditable
- LLM used only for explanations, NOT decision-making

---

## 📊 Data Sources

1. **College Results View 2021** (6,289 institutions)
   - Graduation rates by race/ethnicity
   - Median earnings and debt
   - Admission rates
   - Institution characteristics

2. **Affordability Gap AY2022-23** (21,299 records)
   - Net price data
   - Affordability gaps (standard students & student-parents)
   - Childcare cost adjustments
   - State-specific wage data

**Merge Strategy**: Institutions are joined on UNITID for maximum accuracy, with deduplication to ensure one record per institution.

---

## 🏗️ Architecture

### Directory Structure
```
equipath/
├── data/
│   ├── College Results View 2021 Data Dump for Export.xlsx
│   └── Affordability Gap Data AY2022-23 2.17.25.xlsx
├── notebooks/
│   └── 01_eda_and_cleaning.ipynb
├── src/
│   ├── data_loading.py          # Load and merge datasets
│   ├── feature_engineering.py   # Compute institution-level metrics
│   ├── user_profile.py          # UserProfile schema
│   ├── scoring.py               # Personalized scoring logic
│   ├── clustering.py            # K-means clustering for archetypes
│   ├── llm_integration.py       # Optional LLM explanations
│   └── app_streamlit.py         # Streamlit web interface
├── requirements.txt
└── README.md
```

### Technical Stack
- **Python 3.11**
- **Pandas** - Data manipulation
- **scikit-learn** - K-means clustering, normalization
- **Streamlit** - Interactive web app
- **Plotly** - Interactive visualizations
- **OpenAI API** (optional) - Natural language explanations

---

## 🚀 Getting Started

### 1. Installation

```bash
# Clone the repository
cd equipath

# Create a conda environment (recommended)
conda create --prefix .conda python=3.11
conda activate ./.conda

# Or use an existing environment
# Install dependencies
pip install -r requirements.txt
```

### 2. Running the Streamlit App

```bash
streamlit run src/app_streamlit.py
```

Then open your browser to `http://localhost:8501`

### 3. Using the App

1. **Fill out your profile** in the sidebar:
   - Race/ethnicity
   - Student-parent status
   - First-generation status
   - Budget and income
   - GPA
   - Preferences (location, school type, size)

2. **Click "Find My Matches"**

3. **Review recommendations**:
   - See your personalized match scores
   - Compare colleges visually
   - Explore detailed metrics for each school

---

## 🧮 Scoring Algorithm

### Feature Engineering

For each institution, we compute:

**1. ROI Score**
```python
roi_score = 0.6 * normalized_earnings - 0.4 * normalized_debt
```

**2. Affordability Score**
```python
# For standard students
afford_score_std = 0.6 * normalized_gap + 0.4 * normalized_net_price

# For student-parents (includes childcare costs)
afford_score_parent = 0.6 * normalized_gap_with_childcare + 0.4 * normalized_net_price
```

**3. Equity Score**
```python
# Race-specific graduation rate + overall equity parity
equity_parity = 1 - (max_grad_rate - min_grad_rate) / 100
equity_score = 0.7 * race_specific_grad_rate + 0.3 * equity_parity
```

**4. Access Score**
```python
# Based on admission rate and GPA fit
access_score = normalized_admit_rate * fit_multiplier
```

### Personalized Scoring

```python
# Base weights
alpha (ROI) = 0.25
beta (Affordability) = 0.30
gamma (Equity) = 0.25
delta (Access) = 0.20

# Adjustments based on user profile
if income == "LOW" or budget < 20000:
    beta += 0.15, alpha -= 0.05

if is_parent:
    beta += 0.10, gamma += 0.05

if first_gen or race in ["BLACK", "HISPANIC", "NATIVE"]:
    gamma += 0.10

# Normalize to sum to 1.0
weights = normalize(weights)

# Final score
user_score = alpha*ROI + beta*Affordability + gamma*Equity + delta*Access
```

---

## 📈 Clustering Methodology

We use K-means clustering (k=5) on four normalized features:
- ROI score
- Affordability score (standard)
- Equity parity
- Access score

Clusters are labeled based on centroid characteristics:
- **High ROI + High Equity + Affordable** → "Equity Champions"
- **Affordable + High Access** → "Accessible & Affordable"
- **High Equity + High Access** → "Equity-Focused Access"
- etc.

---

## 🔬 Example Use Cases

### Case 1: Low-Income Student-Parent
```python
UserProfile(
    race="BLACK",
    is_parent=True,
    first_gen=True,
    budget=15000,
    income_bracket="LOW",
    gpa=3.2,
    in_state_only=True,
    state="CA"
)
```
**Weights**: Affordability (55%), Equity (25%), ROI (15%), Access (5%)
**Focus**: Affordable institutions with strong support for parents

### Case 2: First-Gen Student with Medium Income
```python
UserProfile(
    race="HISPANIC",
    is_parent=False,
    first_gen=True,
    budget=25000,
    income_bracket="MEDIUM",
    gpa=3.6
)
```
**Weights**: Equity (35%), Affordability (30%), ROI (20%), Access (15%)
**Focus**: Institutions with strong equity outcomes and reasonable costs

### Case 3: High-Achieving, Higher-Income Student
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
**Weights**: ROI (25%), Affordability (30%), Equity (25%), Access (20%)
**Focus**: Balanced search across all dimensions

---

## 🧪 Testing

### Run Feature Engineering
```bash
python src/feature_engineering.py
```

### Run Clustering Analysis
```bash
python src/clustering.py
```

### Test Scoring with Example Profiles
```bash
python src/scoring.py
```

### Test LLM Integration (requires OpenAI API key)
```bash
export OPENAI_API_KEY="your-key-here"
python src/llm_integration.py
```

---

## 📊 Key Metrics & Insights

### Dataset Coverage
- **6,000+** unique institutions
- **50+** states represented
- **5** distinct institution archetypes

### Equity Focus
- Race-specific graduation rates for 5+ demographic groups
- Affordability gap data including student-parent adjustments
- First-generation and low-income student considerations

### Outcomes Measured
- **10-year earnings** - Real career outcomes
- **Median debt** - True cost of attendance
- **Graduation rates** - Success metrics by demographic

---

## 🎯 Design Principles

1. **Equity First**: Center the needs of historically underserved students
2. **Transparency**: All scoring logic is auditable and explainable
3. **Data-Driven**: Use official federal data, not opinions or rankings
4. **Personalization**: Every student gets unique recommendations
5. **Actionable**: Provide clear, practical information for decision-making
6. **Honest**: Show tradeoffs, not just "best matches"

---

## 🔮 Future Enhancements

1. **Expanded Data Sources**
   - Student support services data
   - Financial aid generosity metrics
   - Campus climate surveys

2. **Additional Filters**
   - Intended major/field of study
   - Specific MSI (Minority-Serving Institution) types
   - Geographic regions
   - Campus characteristics (urban/rural, size, etc.)

3. **Advanced Features**
   - Net price calculator integration
   - Application timeline tracking
   - Peer comparison tools
   - Mobile app

4. **Machine Learning Enhancements**
   - Collaborative filtering (students like you chose...)
   - Outcome prediction models
   - Dynamic weight learning from user feedback

---

## 🤝 Contributing

This project was built for the 7th Annual Datathon (Track 2: Educational Equity).

**Contributors**: [Alex Toohey, Andre Lee, Davyn Paringkoan, Leo Zhang]

---

## 📝 License

This project uses publicly available federal education data. The code and methodology are provided for educational and non-commercial use.

---

## 🙏 Acknowledgments

- **Data Sources**: U.S. Department of Education College Scorecard, Affordability Gap dataset
- **Inspiration**: The millions of students navigating higher education with limited resources
- **Mission**: Making college advising more equitable and accessible for all

---

**Built with ❤️ for educational equity**
