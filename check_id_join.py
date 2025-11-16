"""
Check if we can join on UNITID columns for better merge quality.
"""

import sys
sys.path.append('.')

from src.data_loading import load_college_results, load_affordability_gap
import pandas as pd

# Load datasets
print("Loading datasets...")
college_results = load_college_results()
affordability_gap = load_affordability_gap()

print("\n" + "="*80)
print("CHECKING ID COLUMNS FOR JOIN")
print("="*80)

# Check College Results ID column
cr_id_col = 'UNIQUE_IDENTIFICATION_NUMBER_OF_THE_INSTITUTION'
ag_id_col = 'Unit ID'

print(f"\nCollege Results ID column: {cr_id_col}")
print(f"Sample values:")
print(college_results[cr_id_col].head(10))
print(f"Data type: {college_results[cr_id_col].dtype}")
print(f"Unique values: {college_results[cr_id_col].nunique()}")
print(f"Null values: {college_results[cr_id_col].isnull().sum()}")

print(f"\n{'-'*80}")
print(f"\nAffordability Gap ID column: {ag_id_col}")
print(f"Sample values:")
print(affordability_gap[ag_id_col].head(10))
print(f"Data type: {affordability_gap[ag_id_col].dtype}")
print(f"Unique values: {affordability_gap[ag_id_col].nunique()}")
print(f"Null values: {affordability_gap[ag_id_col].isnull().sum()}")

# Try joining on these IDs
print("\n" + "="*80)
print("TESTING MERGE ON ID COLUMNS")
print("="*80)

# Convert to same type for comparison
college_results[cr_id_col] = pd.to_numeric(college_results[cr_id_col], errors='coerce')
affordability_gap[ag_id_col] = pd.to_numeric(affordability_gap[ag_id_col], errors='coerce')

# Attempt merge
merged_on_id = pd.merge(
    college_results,
    affordability_gap,
    left_on=cr_id_col,
    right_on=ag_id_col,
    how='inner'
)

print(f"\nMerge on ID columns:")
print(f"  College Results rows: {len(college_results)}")
print(f"  Affordability Gap rows: {len(affordability_gap)}")
print(f"  Merged rows: {len(merged_on_id)}")
print(f"  Match rate: {len(merged_on_id)/len(college_results)*100:.1f}% of College Results")
print(f"  Unique institutions in merge: {merged_on_id['Institution Name'].nunique()}")

# Compare with name-based merge
merged_on_name = pd.merge(
    college_results,
    affordability_gap,
    on='Institution Name',
    how='inner'
)

print(f"\nMerge on Institution Name:")
print(f"  Merged rows: {len(merged_on_name)}")
print(f"  Match rate: {len(merged_on_name)/len(college_results)*100:.1f}% of College Results")
print(f"  Unique institutions in merge: {merged_on_name['Institution Name'].nunique()}")

# Check for duplicates
print(f"\n{'-'*80}")
print(f"Duplicate analysis:")
print(f"  Duplicates in ID-based merge: {merged_on_id.duplicated(subset=[cr_id_col]).sum()}")
print(f"  Duplicates in name-based merge: {merged_on_name.duplicated(subset=['Institution Name']).sum()}")

print("\n" + "="*80)
print("RECOMMENDATION:")
print("="*80)
if len(merged_on_id) > 0 and merged_on_id.duplicated(subset=[cr_id_col]).sum() == 0:
    print("✓ USE ID-BASED MERGE - Clean, no duplicates!")
    print(f"  Join on: {cr_id_col} = {ag_id_col}")
else:
    print("✓ USE NAME-BASED MERGE")
    print(f"  Join on: Institution Name")
    print(f"  Note: May have duplicates - consider deduplication strategy")

# Show sample of matched data
print(f"\n{'-'*80}")
print("Sample of matched institutions (ID-based):")
print(merged_on_id[['Institution Name', cr_id_col, ag_id_col, 'State of Institution']].head(10))
