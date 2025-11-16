# Profile System Update - Implementation Guide

## Overview

The EquiPath app now has a **unified profile system** that persists across all tabs and can be:
1. Built incrementally through the AI Chat Assistant
2. Edited manually at any time
3. Shared across all pages/tabs in the session

## New Files Created

### 1. `src/shared_profile_state.py`
Central profile state management that:
- Maintains profile data in `st.session_state.shared_profile_data`
- Provides functions to initialize, update, and retrieve the profile
- Ensures profile consistency across all tabs

**Key Functions:**
- `initialize_shared_profile()` - Initialize profile in session state
- `update_profile_from_data(profile_data)` - Update profile with new data
- `build_profile_from_shared_state()` - Build EnhancedUserProfile from current state
- `get_shared_profile()` - Get current profile object
- `mark_profile_complete()` - Mark profile as complete
- `is_profile_complete()` - Check if profile is complete
- `reset_shared_profile()` - Reset to defaults

### 2. `src/profile_editor.py`
Interactive profile editor component that:
- Displays all profile fields in organized expandable sections
- Allows editing any field with appropriate input widgets
- Automatically saves changes to shared state
- Normalizes weights to sum to 1.0

**Usage:**
```python
from src.profile_editor import render_profile_editor

# In your Streamlit page:
render_profile_editor()
```

## Updated Files

### `src/enhanced_app_streamlit_chat.py`
Modified `build_profile_from_data()` to:
- Save all profile data to shared state
- Mark profile as complete when chat finishes
- Use `build_profile_from_shared_state()` instead of creating profile directly

## How to Use

### In Any Page

```python
from src.shared_profile_state import initialize_shared_profile, get_shared_profile, is_profile_complete

# At the start of your page
initialize_shared_profile()

# Check if profile exists
if is_profile_complete():
    profile = get_shared_profile()
    # Use the profile for recommendations
else:
    st.warning("Please complete your profile in the AI Chat Assistant first!")
```

### Adding Profile Editor to a Page

```python
from src.profile_editor import render_profile_editor
from src.shared_profile_state import initialize_shared_profile

initialize_shared_profile()

# Add a tab or expander for editing
with st.expander("✏️ Edit Profile"):
    render_profile_editor()

# Profile is automatically updated when user makes changes
```

### Building Recommendations

```python
from src.shared_profile_state import get_shared_profile
from src.enhanced_scoring import rank_colleges_for_user
from src.enhanced_feature_engineering import build_enhanced_featured_college_df

# Get profile
profile = get_shared_profile()

# Load data
colleges_df = build_enhanced_featured_college_df(
    earnings_ceiling=profile.earnings_ceiling_match
)

# Get recommendations
recommendations = rank_colleges_for_user(colleges_df, profile, top_k=15)
```

## Benefits

1. **Persistence**: Profile survives page navigation within the session
2. **Incremental Building**: Chat can build profile step-by-step
3. **Editability**: Users can modify any field at any time
4. **Consistency**: All pages use the same profile data
5. **Flexibility**: Easy to add new profile fields

## Profile Data Structure

The shared profile data includes:

**Academic Background:**
- `gpa` (float)
- `sat_score` (int or None)
- `act_score` (int or None)
- `test_score_status` (str: 'submitted'/'no_test'/'test_optional')
- `intended_major` (str)

**Financial:**
- `annual_budget` (float)
- `family_income` (float or None)
- `earnings_ceiling_match` (float)
- `work_study_needed` (bool)

**Demographics:**
- `race_ethnicity` (str)
- `age` (int or None)

**Special Populations:**
- `is_first_gen` (bool)
- `is_student_parent` (bool)
- `is_international` (bool)

**Geographic:**
- `home_state` (str or None, 2-letter code)
- `in_state_only` (bool)
- `preferred_states` (list of str)

**Environment Preferences:**
- `urbanization_pref` (str: 'urban'/'suburban'/'town'/'rural'/'no_preference')
- `size_pref` (str: 'small'/'medium'/'large'/'no_preference')
- `institution_type_pref` (str: 'public'/'private_nonprofit'/'either')
- `msi_preference` (str: 'HBCU'/'HSI'/'Tribal'/'any_MSI'/'no_preference')

**Academic Priorities:**
- `research_opportunities` (bool)
- `small_class_sizes` (bool)
- `strong_support_services` (bool)

**Scoring Weights:**
- `weight_roi` (float, 0.0-1.0)
- `weight_affordability` (float, 0.0-1.0)
- `weight_equity` (float, 0.0-1.0)
- `weight_support` (float, 0.0-1.0)
- `weight_academic_fit` (float, 0.0-1.0)
- `weight_environment` (float, 0.0-1.0)

## Next Steps

To complete the integration:

1. ✅ Created shared profile state management
2. ✅ Created profile editor component
3. ✅ Updated chat to save to shared state
4. ⏳ Update College Finder page to use shared profile
5. ⏳ Update AI Chat Assistant page to show profile editor
6. ⏳ Test profile persistence across all tabs

## Testing Checklist

- [ ] Build profile through chat, verify it saves to shared state
- [ ] Navigate to College Finder, verify profile persists
- [ ] Edit profile manually, verify changes apply immediately
- [ ] Reset profile, verify it clears across all tabs
- [ ] Complete profile in chat, edit later, get new recommendations
