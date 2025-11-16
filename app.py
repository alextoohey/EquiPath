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

**✏️ My Profile & Matches**
- View and edit your profile
- Get personalized college recommendations
- Compare colleges based on affordability, ROI, equity, and more
- Visual comparison tools

**🤖 AI Chat Assistant**
- Build your profile through conversation
- Get AI-generated explanations for recommendations
- Ask questions about colleges and get personalized insights
- Voice input and output support

**🗺️ Interactive School Map**
- Explore postsecondary schools across the United States
- Filter schools by state
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

    - **My Profile**: Edit your profile and get matches
    - **AI Chat Assistant**: Build profile through conversation
    - **School Map**: Explore schools geographically
    """)

    st.markdown("### 💡 Tips")
    st.markdown("""
    - Start with the **AI Chat Assistant** for a conversational experience
    - Use **My Profile** to edit your profile and get recommendations
    - Your profile is shared across all pages - build it once, use it everywhere!
    - Explore the **School Map** to see schools in specific regions
    """)
