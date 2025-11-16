# EquiPath - Streamlit Multi-Page App Guide

## Overview

EquiPath is now a multi-page Streamlit application with three main features accessible through the sidebar navigation.

## Project Structure

```
7th Datathon/
├── app.py                          # Main landing page
├── pages/                          # Multi-page app pages
│   ├── 1_🔍_College_Finder.py     # Form-based college search
│   ├── 2_💬_AI_Chat_Assistant.py  # AI-powered conversational search
│   └── 3_🗺️_School_Map.py         # Interactive geographic map
├── src/                            # Source modules
│   ├── clustering.py
│   ├── feature_engineering.py
│   ├── llm_integration.py
│   ├── scoring.py
│   ├── user_profile.py
│   └── ...
└── map/                            # Map assets
    ├── schools.geojson
    ├── index.html
    ├── script.js
    └── style.css
```

## How to Run

### Start the Application

```bash
cd "/Users/andrelee/Desktop/7th Datathon"
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Navigation

Once the app is running:

1. **Main Page**: Landing page with overview and instructions
2. **Sidebar Navigation**: Click on any page to navigate:
   - 🔍 **College Finder**: Quick form-based search
   - 💬 **AI Chat Assistant**: Interactive conversational interface
   - 🗺️ **School Map**: Geographic exploration of schools

## Features

### 🔍 College Finder
- Fill out a form with your profile
- Get instant personalized recommendations
- View detailed metrics and visualizations
- Compare colleges side-by-side

### 💬 AI Chat Assistant
- Chat naturally to build your profile
- Get AI-generated explanations for recommendations
- Ask follow-up questions about colleges
- Conversational Q&A about your matches

### 🗺️ School Map
- Interactive Leaflet map of all U.S. postsecondary schools
- Filter by state using the dropdown
- Click markers to view school details
- Explore schools geographically

## Original Apps (Still Available)

The original standalone apps are still in the `src/` directory:
- `src/app_streamlit.py` - Original College Finder
- `src/app_streamlit_chat.py` - Original AI Chat
- `src/app_map.py` - Original Map

You can run them individually if needed:
```bash
streamlit run src/app_streamlit.py
streamlit run src/app_streamlit_chat.py
streamlit run src/app_map.py
```

## Requirements

All dependencies are in `requirements.txt`:
```bash
pip install -r requirements.txt
```

Key packages:
- streamlit >= 1.28.0
- pandas >= 2.0.0
- plotly >= 5.17.0
- anthropic >= 0.39.0 (for AI features)

## Tips

- Use the **AI Chat Assistant** for first-time users
- Use the **College Finder** for quick searches
- Use the **School Map** to explore schools in specific regions
- All pages share the same data and models
- Your profile in chat mode persists during the session
