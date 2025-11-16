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

**✏️ My Profile**
- Build and edit your profile
- Set your preferences and priorities
- Your profile is automatically saved and shared across all pages

**🎯 My Recommendations**
- Get personalized college recommendations based on your profile
- View AI-generated explanations for each recommendation
- Compare colleges based on affordability, ROI, equity, and more
- Visual comparison tools and interactive charts
- Ask questions with our Q&A chatbot

**🤖 AI Chat Assistant**
- Build your profile through natural conversation
- Get personalized insights and guidance
- Voice input and output support

**🗺️ Interactive School Map**
- Explore colleges across the United States geographically
- Filter by state and view your recommended schools
- View detailed information for each institution

### How EquiPath Works

EquiPath uses a comprehensive **personalized scoring system** across 7 dimensions:

- 💰 **Affordability** - Net price and financial accessibility
- 📈 **ROI** - Earnings potential vs. debt burden
- ⚖️ **Equity** - Graduation outcomes for students like you
- 🎯 **Support Services** - Student support infrastructure
- 📚 **Academic Fit** - Program strength in your field
- 🏫 **Environment** - Campus culture and setting match
- 🚪 **Access** - Your likelihood of admission (GPA, test scores, selectivity)

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

    - **My Profile**: Build and edit your profile
    - **My Recommendations**: Get personalized college matches
    - **AI Chat Assistant**: Build profile through conversation
    - **School Map**: Explore schools geographically
    """)

    st.markdown("### 💡 Tips")
    st.markdown("""
    1. Start by building your profile (**My Profile** or **AI Chat Assistant**)
    2. Get personalized recommendations (**My Recommendations**)
    3. Ask questions with the Q&A chatbot on the recommendations page
    4. Explore recommended schools on the **School Map**
    5. Your profile is shared across all pages - build it once, use it everywhere!
    """)
