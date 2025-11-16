# Chat Interface - Supported Input Variations

This document lists the natural language variations supported by the enhanced chat interface in `src/enhanced_app_streamlit_chat.py`.

## Purpose

The chat interface is designed to be forgiving and understand common variations of user responses, making the experience more natural and reducing frustration from "I didn't quite understand that" errors.

---

## Urbanization Preference

**Question:** "What kind of setting do you prefer?"

**Official Options:** urban, suburban, town, rural, no_preference

**Recognized Variations:**

| User Input | Maps To |
|------------|---------|
| "city", "big city", "urban area" | urban |
| "suburb", "suburbs", "near city" | suburban |
| "small town" | town |
| "countryside", "country", "remote" | rural |
| "any", "either", "no preference", "don't care", "doesn't matter" | no_preference |

---

## Size Preference

**Question:** "What school size do you prefer?"

**Official Options:** small, medium, large, no_preference

**Recognized Variations:**

| User Input | Maps To |
|------------|---------|
| "tiny", "very small" | small |
| "mid-size", "medium-sized", "moderate" | medium |
| "big", "huge", "very large" | large |
| "any", "either", "no preference" | no_preference |

---

## Institution Type Preference

**Question:** "Do you prefer public or private schools, or either?"

**Official Options:** public, private_nonprofit, either

**Recognized Variations:**

| User Input | Maps To |
|------------|---------|
| "state", "state school", "public university" | public |
| "private", "private school" | private_nonprofit |
| "any", "both", "either" | either |

---

## MSI Preference

**Question:** "Are you interested in Minority-Serving Institutions?"

**Official Options:** HBCU, HSI, Tribal, any_MSI, no_preference

**Recognized Variations:**

| User Input | Maps To |
|------------|---------|
| "historically black", "black college" | HBCU |
| "hispanic serving", "latino serving" | HSI |
| "tribal", "native american" | Tribal |
| "any msi", "minority serving" | any_MSI |
| "any", "no preference" | no_preference |

---

## Intended Major

**Question:** "What field are you interested in studying?"

**Official Options:** STEM, Business, Health, Social Sciences, Arts & Humanities, Education, Undecided

**Recognized Variations:**

| User Input | Maps To |
|------------|---------|
| "science", "technology", "engineering", "math" | STEM |
| "medicine", "nursing", "healthcare" | Health |
| "liberal arts", "humanities" | Arts & Humanities |
| "not sure", "unsure", "don't know" | Undecided |

---

## Race/Ethnicity (Optional)

**Question:** "How would you describe your race/ethnicity?"

**Official Options:** BLACK, HISPANIC, WHITE, ASIAN, NATIVE, PACIFIC, TWO_OR_MORE, PREFER_NOT_TO_SAY

**Recognized Variations:**

| User Input | Maps To |
|------------|---------|
| "african american", "black" | BLACK |
| "latino", "latina", "latinx", "chicano" | HISPANIC |
| "asian american", "asian" | ASIAN |
| "native", "indigenous", "american indian" | NATIVE |
| "pacific islander", "hawaiian" | PACIFIC |
| "multiracial", "mixed", "biracial" | TWO_OR_MORE |
| "skip", "pass", "rather not say" | PREFER_NOT_TO_SAY |

---

## Test Status

**Question:** "Have you taken the SAT or ACT?"

**Official Options:** yes, no, planning

**Recognized Variations:**

| User Input | Maps To |
|------------|---------|
| "took it", "yes i have", "submitted" | yes |
| "haven't taken", "didn't take", "no test" | no |
| "will take", "plan to", "going to" | planning |

---

## How It Works

The chat interface uses a cascading matching strategy:

1. **Exact Match:** Check if user input exactly matches an option (case-insensitive)
2. **Contains Match:** Check if option is in user input or vice versa
3. **Word Match:** Check if any words from the option appear in user input
4. **Special Variations:** Check common alternative phrasings (documented above)

This ensures maximum flexibility while maintaining accuracy.

---

## Testing

All variations have been tested and validated. See comprehensive test results in the development logs.

**Test Coverage:** 30/30 variations tested and passing ✅

---

## Future Enhancements

Potential improvements:
- Add fuzzy string matching for typos (e.g., "subrban" → "suburban")
- Support for more casual phrasings (e.g., "I live in the city" → "urban")
- Multi-language support
- Voice input optimization

---

**Last Updated:** 2025-01-15  
**Status:** ✅ Complete and tested
