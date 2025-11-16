"""
EquiPath - Main Streamlit Application
Multi-page app for equity-centered college advising.
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="EquiPath - College Advising",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main page content
st.title("🎓 EquiPath: Equity-Centered College Advising")

st.markdown("""
## Welcome to EquiPath!

EquiPath is a comprehensive college advising tool designed to help students find colleges that match their unique needs and support their success.

### Features

Our platform offers multiple tools to help you in your college search:

**🔍 College Recommendation Tool**
- Get personalized college recommendations based on your profile
- Simple form-based interface
- Compare colleges based on affordability, ROI, equity, and access

**💬 AI-Powered Chat Assistant**
- Interactive chat interface to build your profile conversationally
- Get AI-generated explanations for recommendations
- Ask questions about colleges and get personalized insights

**🗺️ Interactive School Map**
- Explore postsecondary schools across the United States
- Filter schools by state
- View detailed information for each institution

### How EquiPath Works

EquiPath uses a personalized **Student Success & Equity Score** that considers:

- 💰 **Affordability** - Net price and financial accessibility
- 📈 **ROI** - Earnings potential vs. debt burden
- ⚖️ **Equity** - Graduation outcomes for students like you
- 🚪 **Access** - Admission selectivity and fit

### Get Started

Choose a tool from the sidebar to begin your college search journey!

---

*Use the navigation menu on the left to explore different features.*
""")

# Add some helpful information in the sidebar
with st.sidebar:
    st.markdown("### 📚 Navigation")
    st.info("""
    Use the pages in the sidebar above to:

    - **College Finder**: Get personalized recommendations
    - **AI Chat Assistant**: Interactive college search
    - **School Map**: Explore schools geographically
    """)

    st.markdown("### 💡 Tips")
    st.markdown("""
    - Start with the **AI Chat Assistant** for a guided experience
    - Use the **College Finder** if you prefer quick form-based search
    - Explore the **School Map** to see schools in specific regions
    """)
