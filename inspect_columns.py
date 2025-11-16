"""
Quick script to inspect key columns for feature engineering.
"""

import sys
sys.path.append('.')

from src.data_loading import load_college_results, load_affordability_gap, load_merged_data

# Load datasets
print("Loading datasets...")
college_results = load_college_results()
affordability_gap = load_affordability_gap()

print("\n" + "="*80)
print("KEY COLUMNS FOR FEATURE ENGINEERING")
print("="*80)

# Search for ROI-related columns
print("\n1. ROI METRICS (Earnings & Debt):")
print("-" * 40)
earnings_keywords = ['EARN', 'SALARY', 'MEDIAN', 'INCOME', 'WAGE']
for col in college_results.columns:
    if any(keyword in col.upper() for keyword in earnings_keywords):
        if '10' in col or 'YEAR' in col.upper() or 'AFTER' in col.upper():
            print(f"   {col}")

print("\nDebt columns:")
debt_keywords = ['DEBT', 'LOAN']
for col in college_results.columns:
    if any(keyword in col.upper() for keyword in debt_keywords):
        if 'MEDIAN' in col.upper() or 'AVERAGE' in col.upper():
            print(f"   {col}")

# Search for affordability columns
print("\n2. AFFORDABILITY METRICS:")
print("-" * 40)
print("\nFrom Affordability Gap dataset:")
for col in affordability_gap.columns:
    if 'GAP' in col.upper() or 'NET PRICE' in col.upper() or 'COST' in col.upper():
        print(f"   {col}")

# Search for graduation rate columns by race
print("\n3. EQUITY METRICS (Graduation Rates by Race):")
print("-" * 40)
race_keywords = ['BLACK', 'HISPANIC', 'WHITE', 'ASIAN', 'NATIVE', 'PACIFIC']
for col in college_results.columns:
    if 'GRAD' in col.upper() and any(keyword in col.upper() for keyword in race_keywords):
        print(f"   {col}")

# Search for admission rate
print("\n4. ACCESS METRICS (Admission Rate):")
print("-" * 40)
for col in college_results.columns:
    if 'ADMIT' in col.upper() or 'ACCEPTANCE' in col.upper():
        print(f"   {col}")

# Check for institution identifiers
print("\n5. INSTITUTION IDENTIFIERS:")
print("-" * 40)
for col in college_results.columns:
    if 'UNITID' in col.upper() or 'OPEID' in col.upper():
        print(f"   {col}")

# Check for location/state columns
print("\n6. LOCATION COLUMNS:")
print("-" * 40)
for col in college_results.columns:
    if 'STATE' in col.upper() and 'ABBREVIATION' not in col.upper():
        if 'OUT' not in col.upper():
            print(f"   {col}")

# Check for sector/type columns
print("\n7. INSTITUTION TYPE/SECTOR:")
print("-" * 40)
for col in college_results.columns:
    if 'SECTOR' in col.upper() or 'TYPE' in col.upper() or 'CONTROL' in col.upper():
        if 'CATEGORY' not in col.upper():
            print(f"   {col}")

# Check for size columns
print("\n8. INSTITUTION SIZE:")
print("-" * 40)
for col in college_results.columns:
    if 'SIZE' in col.upper():
        print(f"   {col}")

print("\n" + "="*80)
