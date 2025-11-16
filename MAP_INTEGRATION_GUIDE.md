# School Map Integration Guide

## Overview

The interactive School Map has been fully integrated with your EquiPath recommendation system! Users can now view their recommended schools on a map.

## New Features

### 🗺️ School Map Page

#### For All Users:
- **View all 6,812+ postsecondary schools** across the United States
- **Filter by state** using the dropdown
- **Cluster visualization** - schools group together at higher zoom levels
- **Click markers** to view school details (address, type, website)
- **Interactive navigation** - zoom, pan, and explore

#### For Users with Profiles:
- **Toggle View Mode:**
  - 🌎 **All Schools** - See all schools in the database
  - ⭐ **My Recommendations** - See only your recommended schools

- **Profile Integration:**
  - Your profile from College Finder or AI Chat automatically syncs
  - View your profile settings in the expandable section
  - Recommendations persist across pages

- **Visual Distinction:**
  - Recommended schools shown in **gold color** (⭐)
  - Regular schools shown in blue
  - Popups indicate "✨ Recommended for you!"

### 🔍 College Finder Integration

- After finding matches, a tip appears: "View your recommended schools on the interactive map!"
- Profile and recommendations automatically save to session state
- Navigate to School Map to see your matches geographically

### 💬 AI Chat Assistant Integration

- Same integration as College Finder
- Your conversational profile syncs with the map
- Recommended schools from chat appear on the map

## How It Works

### User Flow:

1. **Create a Profile**
   - Go to College Finder or AI Chat Assistant
   - Fill out your preferences (budget, GPA, state, etc.)
   - Click "Find My Matches"

2. **View Recommendations**
   - See your personalized college list
   - Read detailed information about each school

3. **Explore on Map**
   - Navigate to 🗺️ School Map page
   - Toggle to "⭐ My Recommendations"
   - See your schools plotted geographically
   - Filter by state to focus on specific regions
   - Click markers for school details

### Technical Implementation:

```python
# Profile and recommendations saved to session state
st.session_state.saved_profile = profile
st.session_state.saved_recommendations = recommendations

# Map page checks for saved data
has_profile = 'saved_profile' in st.session_state
has_recommendations = 'saved_recommendations' in st.session_state

# Filter GeoJSON features by recommended schools
if show_mode == "recommended":
    recommended_schools = set(recommendations_df['Institution Name'].tolist())
    filtered_features = [
        feature for feature in filtered_features
        if feature.get('properties', {}).get('NAME') in recommended_schools
    ]
```

## Map Features

### Performance Optimizations:
- **MarkerCluster** - Groups nearby schools for better performance
- **CircleMarkers** - Lightweight markers instead of custom icons
- **On-demand loading** - Recommendations only loaded when needed
- **Session caching** - Profile and recommendations persist

### Visualization:
- **Gold markers (⭐)** for recommended schools
- **Blue markers** for all other schools
- **Auto-centering** on selected state
- **Zoom levels** adjust based on view (all states vs. single state)

## Files Modified

1. **pages/3_🗺️_School_Map.py**
   - Added profile/recommendations integration
   - Added toggle between all schools and recommendations
   - Added visual distinction for recommended schools
   - Added profile summary display

2. **pages/1_🔍_College_Finder.py**
   - Save profile and recommendations to session state
   - Added tip to view schools on map

3. **pages/2_💬_AI_Chat_Assistant.py**
   - Save profile and recommendations to session state
   - Added tip to view schools on map

## Usage Examples

### Example 1: Budget-Conscious Student in California

1. Create profile: Budget $20,000, California, In-state only
2. Get 15 recommendations
3. Go to School Map
4. Toggle to "My Recommendations"
5. See all 15 schools plotted in California
6. Filter by "CA" to zoom in
7. Click markers to explore each school

### Example 2: First-Gen Student Exploring Options

1. Use AI Chat to create profile conversationally
2. Get personalized recommendations
3. Go to School Map
4. Toggle between "All Schools" and "My Recommendations"
5. Compare recommended schools to all schools in the region
6. Use state filter to explore different regions

## Benefits

### For Students:
- **Geographic context** - See where recommended schools are located
- **Regional comparison** - Compare schools in your area vs. recommendations
- **Visual exploration** - Discover schools you might not have considered
- **Easy filtering** - Quick state-based filtering

### For Advisors:
- **Visual presentation** - Show students their options geographically
- **Contextual understanding** - Help students understand school distribution
- **Interactive exploration** - Students can explore at their own pace

## Next Steps

Potential future enhancements:
- Add distance calculations from home location
- Show school details in sidebar on marker click
- Add comparison mode (side-by-side schools)
- Export recommended schools to PDF with map
- Add heatmap view for density visualization
- Integration with Google Maps for directions

## Running the App

```bash
python -m streamlit run app.py
```

Navigate between pages using the sidebar!
