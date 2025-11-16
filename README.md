# 🎓 EquiPath: Equity-Centered College Advising Platform

**Track 2: Educational Equity | 7th Annual Datathon**

EquiPath is an AI-powered, equity-centered college recommendation system that helps low-income and underserved students find institutions where they're most likely to succeed and graduate. Unlike traditional college search tools that prioritize prestige or rankings, EquiPath uses data-driven personalized scoring to center the needs of first-generation students, student-parents, and students from historically marginalized communities.

**The Problem:** Students from low-income backgrounds graduate at significantly lower rates than their higher-income peers—a gap of over 15 percentage points on average.

**Our Solution:** EquiPath matches students with colleges using a personalized **Student Success & Equity Score** that adapts to each student's unique circumstances, prioritizing affordability, equity outcomes, and student success over prestige.

---

## 🌟 Key Features

### 1. **Multi-Modal User Experience**

EquiPath offers four ways to find your perfect college match:

- **🔍 College Finder** - Quick form-based search with instant recommendations
- **💬 AI Chat Assistant** - Conversational interface powered by Claude AI that explains recommendations in plain language
- **🗺️ Interactive Map** - Geographic exploration with 6,800+ schools, filterable by state and your recommendations
- **📊 Data Insights** - Visualizations showing the income-graduation gap that motivates EquiPath

### 2. **Personalized Student Success & Equity Score**

Our proprietary algorithm combines four key dimensions:
- **💰 Affordability** - Net price, affordability gap, childcare costs (for student-parents)
- **📈 ROI** - Median earnings 10 years post-graduation vs. median debt
- **⚖️ Equity** - Race-specific graduation rates and equity parity across demographics
- **🚪 Access** - Admission selectivity and student GPA fit

### 3. **Dynamic Weight Adjustment**

The scoring weights automatically adjust based on your profile:
- **Low-income students**: Affordability weight increases by 15%
- **Student-parents**: Affordability +10%, Equity +5%
- **First-gen/marginalized students**: Equity weight increases by 10%

### 4. **Geographic Filtering**

- **Zip Code Radius Search**: Find colleges within a specific distance from your location
- **State Filtering**: Focus on in-state schools for lower tuition
- **Interactive Map Visualization**: See all schools geographically with detailed popups

### 5. **Institution Archetypes (K-Means Clustering)**

Colleges are clustered into meaningful archetypes based on their characteristics:
- **Equity Champions** (5.5%) - High ROI, high equity, affordable
- **Balanced Options** (29.4%) - Well-rounded across all dimensions
- **Equity-Focused Access** (20.1%) - Strong support for diverse students
- **Good Value Options** (10.8%) - Balanced affordability and outcomes
- **Balanced Options 2** (34.3%) - Alternative balanced profile

### 6. **Data-Driven, Transparent**

- Uses official federal datasets (IPEDS, College Scorecard, Affordability Gap data)
- All scoring logic is transparent and auditable
- AI (Claude) used only for explanations and chat, NOT for decision-making
- Algorithm is deterministic and reproducible

---

## 📊 Data Sources

1. **College Results View 2021** (6,289 institutions)
   - Graduation rates by race/ethnicity
   - Median earnings and debt
   - Admission rates
   - Institution characteristics

2. **Affordability Gap AY2022-23** (21,299 records)
   - Net price data by family income bracket
   - Affordability gaps (standard students & student-parents)
   - Childcare cost adjustments
   - State-specific minimum wage data

3. **Schools GeoJSON** (6,812 schools)
   - Geographic coordinates for map visualization
   - Institution names and addresses

**Merge Strategy**: Institutions are joined on UNITID for maximum accuracy. We filter to the $30,000 earnings ceiling (lowest income bracket) to ensure one record per institution. Final dataset: **4,933 institutions** with **288 features**.

---

## 🏗️ Architecture

### Directory Structure
```
7th Datathon/
├── app.py                          # Main Streamlit landing page
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── TECHNICAL_DOCUMENTATION.md      # Detailed technical docs
├── data/
│   ├── College Results View 2021 Data Dump for Export.xlsx
│   ├── Affordability Gap Data AY2022-23 2.17.25.xlsx
│   └── .cache/                     # Parquet cache files (auto-generated)
├── map/
│   ├── schools.geojson            # 6,812 school locations
│   └── index.html                 # Original HTML map (deprecated)
├── tableau_exports/               # CSV files for Tableau visualizations
│   ├── income_graduation_data.csv
│   ├── income_categories_summary.csv
│   ├── key_statistics.csv
│   └── TABLEAU_GUIDE.md
├── src/
│   ├── data_loading.py            # Load and merge datasets
│   ├── feature_engineering.py     # Compute institution-level metrics
│   ├── user_profile.py            # UserProfile schema
│   ├── scoring.py                 # Personalized scoring logic
│   ├── clustering.py              # K-means clustering for archetypes
│   ├── llm_integration.py         # Claude AI integration
│   ├── distance_utils.py          # Zip code distance filtering
│   └── config.py                  # Configuration constants
└── pages/                         # Streamlit multi-page app
    ├── 1_🔍_College_Finder.py     # Form-based finder
    ├── 2_💬_AI_Chat_Assistant.py  # AI chat interface
    ├── 3_🗺️_School_Map.py         # Interactive map
    └── 4_📊_Data_Insights.py      # Income/equity visualizations
```

### Technical Stack
- **Python 3.11+**
- **Pandas & NumPy** - Data manipulation
- **scikit-learn** - K-means clustering, StandardScaler
- **Streamlit** - Web application framework
- **Plotly** - Interactive visualizations (Data Insights page)
- **Folium** - Interactive maps
- **Anthropic Claude API** - AI chat assistant
- **PyArrow** - Parquet caching for fast data loading
- **pgeocode & uszipcode** - Geographic distance filtering

---

## 🚀 Getting Started

### 1. Installation

```bash
# Navigate to the project directory
cd "7th Datathon"

# Install dependencies
pip install -r requirements.txt

# Set up your Claude API key (for AI Chat Assistant)
# Create a .env file in the project root:
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
```

### 2. Running the Streamlit App

```bash
# Option 1: Standard way
streamlit run app.py

# Option 2: If streamlit not in PATH
python -m streamlit run app.py
```

Then open your browser to `http://localhost:8501`

### 3. Using the App

#### **College Finder (Form-Based)**

1. Navigate to **🔍 College Finder** in the sidebar
2. Fill out your profile:
   - GPA (0.0-4.0)
   - Annual budget
   - Home state
   - Zip code (optional - enables distance filtering)
   - Search radius in miles (optional)
   - Race/ethnicity
   - Income bracket
   - First-generation status
   - Student-parent status
   - Preferences (public only, in-state only, school size)
3. Click **"Find My Matches"**
4. Review your top 10 personalized recommendations with:
   - Match scores (0-1, higher is better)
   - Distance from your zip code (if provided)
   - Net price, graduation rates, earnings data
   - Detailed breakdowns across all 4 scoring dimensions

#### **AI Chat Assistant**

1. Navigate to **💬 AI Chat Assistant** in the sidebar
2. Chat naturally with Claude AI:
   - "I'm a single mom with a 3.2 GPA and can afford $15k/year. Help me find colleges."
   - "Why was this school recommended for me?"
   - "What makes this college affordable?"
   - "Find me schools within 50 miles of my home"
3. Get personalized explanations and follow-up answers

#### **Interactive Map**

1. Navigate to **🗺️ School Map** in the sidebar
2. Toggle between:
   - **🌎 All Schools** - View all 6,800+ schools (blue circles)
   - **⭐ My Recommendations** - See your recommended schools (orange graduation cap pins)
3. Filter by state using the dropdown
4. Click any school to see detailed information:
   - Institution name and location
   - Public/Private type
   - Admission rate (if available)
   - Net price
   - Median earnings (10 years post-enrollment)
   - Your match score (for recommended schools)

#### **Data Insights**

1. Navigate to **📊 Data Insights** in the sidebar
2. Explore three visualizations showing the income-graduation gap:
   - **Bar Chart** - Average graduation rates by income level
   - **Scatter Plot** - Individual schools showing correlation with trendline
   - **Box Plot** - Distribution of outcomes by income category
3. Understand why EquiPath was created

---

## 🧮 Scoring Algorithm

### Feature Engineering

For each institution, we compute four composite scores:

**1. ROI Score**
```python
roi_score = 0.6 * normalized_earnings + 0.4 * (1 - normalized_debt)
```
- Uses median earnings 10 years after entry
- Uses median debt of completers
- Higher earnings and lower debt = better ROI

**2. Affordability Score**
```python
# For standard students
afford_score_std = 0.6 * (1 - normalized_gap) + 0.4 * (1 - normalized_net_price)

# For student-parents (includes childcare costs)
afford_score_parent = 0.6 * (1 - normalized_gap_with_childcare) + 0.4 * (1 - normalized_net_price)
```
- Lower net price and smaller affordability gap = more affordable
- Student parents face 3× larger affordability gap ($26,931 vs $9,610)

**3. Equity Score**
```python
# Equity parity measures how equal grad rates are across races
equity_parity = 1 - (max_grad_rate - min_grad_rate) / 100

# Personalized equity score uses race-specific graduation rate
equity_score = 0.7 * race_specific_grad_rate_norm + 0.3 * equity_parity
```
- If user is Black → uses Black graduation rate
- If user is Latino → uses Latino graduation rate
- Parity = 1.0: perfect equity; Parity = 0.0: maximum disparity

**4. Access Score**
```python
access_score = normalized_admit_rate * fit_multiplier
```
- Based on admission rate and GPA fit
- Safety schools (admit rate >70%) get boost for qualified students
- Reach schools (admit rate <30%) get penalty unless high GPA

### Personalized Scoring

```python
# Base weights
alpha (ROI) = 0.25
beta (Affordability) = 0.30
gamma (Equity) = 0.25
delta (Access) = 0.20

# Adjustments based on user profile
if income == "LOW" or budget < 20000:
    beta += 0.15    # Affordability matters more
    alpha -= 0.05   # ROI matters less

if is_parent:
    beta += 0.10    # Affordability critical
    gamma += 0.05   # Equity support needed

if first_gen or race in ["BLACK", "HISPANIC", "NATIVE"]:
    gamma += 0.10   # Equity support important

# Normalize weights to sum to 1.0
weights = normalize(weights)

# Final personalized score
user_score = alpha*ROI + beta*Affordability + gamma*Equity + delta*Access
```

### Filtering

Before scoring, colleges are filtered by:
1. **Budget constraint**: Net price ≤ 1.5× user budget
2. **Public only**: If user specified
3. **In-state only**: If user specified and state provided
4. **School size**: If user has preference (Small/Medium/Large)
5. **Geographic radius**: If user provided zip code and radius (e.g., 50 miles)

---

## 📈 Clustering Methodology

We use K-means clustering (k=5) with StandardScaler normalization on four features:
- ROI score
- Affordability score (standard)
- Equity parity
- Access score

Clusters are labeled based on centroid characteristics:
- **High ROI + High Equity + Affordable** → "Equity Champions"
- **Affordable + High Access** → "Accessible & Affordable"
- **High Equity + High Access** → "Equity-Focused Access"
- **Balanced profile** → "Balanced Options" (with numbered variants)

Random state is set to 42 for reproducibility.

---

## 🔬 Example Use Cases

### Case 1: Low-Income Student-Parent
```python
UserProfile(
    gpa=3.2,
    budget=15000,
    state="CA",
    zip_code="90210",
    radius_miles=50,
    race="BLACK",
    income_bracket="LOW",
    first_gen=True,
    is_parent=True,
    in_state_only=True,
    public_only=False
)
```
**Personalized Weights:**
- Affordability: **55%** (base 30% + 15% low income + 10% parent)
- Equity: **30%** (base 25% + 5% parent)
- ROI: **10%** (normalized after adjustments)
- Access: **5%** (normalized)

**Filters Applied:**
- Net price ≤ $22,500 (1.5× budget)
- California schools only
- Within 50 miles of zip code 90210

**Focus**: Affordable institutions with strong support for parents and equity outcomes for Black students

### Case 2: First-Gen Student with Medium Income
```python
UserProfile(
    gpa=3.6,
    budget=25000,
    state="TX",
    race="HISPANIC",
    income_bracket="MEDIUM",
    first_gen=True,
    is_parent=False
)
```
**Personalized Weights:**
- Equity: **35%** (base 25% + 10% first-gen/Hispanic)
- Affordability: **30%** (base, no adjustments)
- ROI: **22%** (normalized)
- Access: **13%** (normalized)

**Focus**: Institutions with strong equity outcomes for Latino students and reasonable costs

### Case 3: High-Achieving Student
```python
UserProfile(
    gpa=3.9,
    budget=50000,
    race="ASIAN",
    income_bracket="HIGH",
    first_gen=False,
    is_parent=False
)
```
**Personalized Weights:**
- All weights remain at base (no adjustments)
- ROI: **25%**
- Affordability: **30%**
- Equity: **25%**
- Access: **20%**

**Focus**: Balanced search across all dimensions

---

## 🧪 Testing & Development

### Run Feature Engineering
```bash
python src/feature_engineering.py
```
- Processes raw data and computes all scores
- Creates Parquet cache for fast loading
- Displays summary statistics

### Run Clustering Analysis
```bash
python src/clustering.py
```
- Performs K-means clustering
- Shows cluster centroids and labels
- Displays sample institutions by cluster

### Test Scoring with Example Profiles
```bash
python src/scoring.py
```
- Tests personalized scoring algorithm
- Uses example profiles (low_income_parent, first_gen_student, etc.)
- Displays top 10 recommendations

### Test AI Chat Integration
```bash
# Requires ANTHROPIC_API_KEY in .env
python src/llm_integration.py
```
- Tests Claude AI integration
- Generates explanations for recommendations

---

## 📊 Key Metrics & Insights

### Dataset Coverage
- **4,933** unique institutions in final dataset
- **6,812** schools on interactive map
- **288** features per institution
- **71.9%** GeoJSON-to-database match rate

### Equity Findings from EDA
- **Income-Graduation Gap**: Schools with 75-100% Pell students graduate at significantly lower rates than schools with 0-25% Pell students
- **Racial Equity Gaps**:
  - White students: 56.5% graduation rate
  - Black students: 44.1% (**12.4% gap**)
  - Latino students: 49.9% (**6.6% gap**)
  - Asian students: 61.3%
- **Student Parent Challenge**: $26,931 median affordability gap (**3× larger** than standard students' $9,610)
- **Completion Timeline**: Only 40% graduate in 4 years; 53.1% in 6 years

### Access Distribution
- **Highly Selective (<25% admission)**: 68 schools (1.4%)
- **Moderately Selective (25-50%)**: 155 schools (3.1%)
- **Open Access (>75%)**: 975 schools (19.8%)
- **Average Admission Rate**: 73.6%

---

## 🎯 Design Principles

1. **Equity First**: Center the needs of historically underserved students
2. **Transparency**: All scoring logic is auditable and explainable
3. **Data-Driven**: Use official federal data, not opinions or rankings
4. **Personalization**: Every student gets unique recommendations based on their profile
5. **Actionable**: Provide clear, practical information for decision-making
6. **Honest**: Show tradeoffs and real outcomes, not just "best matches"
7. **Accessible**: Multiple interfaces (form, chat, map) to meet different user preferences

---

## 🔮 Future Enhancements

### Data
- Add more data sources to increase admission rate coverage (currently 35.4%)
- Include transfer student outcomes and pathways
- Add campus support services data (mental health, childcare availability, etc.)
- Integrate financial aid generosity metrics

### Algorithm
- Train supervised ML model (XGBoost, Random Forest) to predict student success probability
- Add time-to-degree predictions
- Include intended major/career pathway recommendations
- Implement collaborative filtering (students like you chose...)

### Features
- Net price calculator integration
- Application deadline tracking and reminders
- Scholarship matching based on profile
- Peer comparison (outcomes for students like you at this school)
- Save/export recommendations as PDF
- Email integration

### UI/UX
- Mobile app version
- User accounts to save search history and profiles
- Comparison tool (side-by-side school comparison)
- Virtual campus tours integration
- Student testimonials from similar backgrounds

---

## 🤝 Contributors

This project was built for the **7th Annual Datathon - Track 2: Educational Equity**.

**Team Members:**
- Alex Toohey
- Andre Lee
- Davyn Paringkoan
- Leo Zhang

---

## 📝 License

This project uses publicly available federal education data from the U.S. Department of Education. The code and methodology are provided for educational and non-commercial use.

---

## 🙏 Acknowledgments

- **Data Sources**: U.S. Department of Education (College Scorecard, IPEDS), Affordability Gap dataset
- **AI Partner**: Anthropic (Claude API)
- **Inspiration**: The millions of students navigating higher education with limited resources and systemic barriers
- **Mission**: Making college advising more equitable, accessible, and effective for all students, especially those who need it most

---

## 📚 Additional Documentation

- **[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)** - Comprehensive technical documentation with algorithms, data flow, and implementation details
- **[tableau_exports/TABLEAU_GUIDE.md](tableau_exports/TABLEAU_GUIDE.md)** - Guide for recreating visualizations in Tableau

---

**Built with ❤️ for educational equity**

*"Education is the most powerful weapon which you can use to change the world." - Nelson Mandela*
