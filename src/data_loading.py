3

"""
Data loading module for EquiPath project.
Handles loading and merging of College Results 2021 and Affordability Gap datasets.
"""

import pandas as pd
import os


def load_college_results(data_dir='data'):
    """
    Load the College Results 2021 dataset.

    Parameters:
    -----------
    data_dir : str
        Directory containing the data files

    Returns:
    --------
    pd.DataFrame
        College Results dataset
    """
    file_path = os.path.join(data_dir, 'College Results View 2021 Data Dump for Export.xlsx')
    print(f"Loading College Results from: {file_path}")
    df = pd.read_excel(file_path)
    print(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df


def load_affordability_gap(data_dir='data'):
    """
    Load the Affordability Gap AY2022-23 dataset.

    Parameters:
    -----------
    data_dir : str
        Directory containing the data files

    Returns:
    --------
    pd.DataFrame
        Affordability Gap dataset
    """
    file_path = os.path.join(data_dir, 'Affordability Gap Data AY2022-23 2.17.25.xlsx')
    print(f"Loading Affordability Gap data from: {file_path}")
    df = pd.read_excel(file_path)
    print(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df


def load_merged_data(data_dir='data', join_key='UNITID', deduplicate=True):
    """
    Load and merge both datasets using UNITID for best match quality.

    Parameters:
    -----------
    data_dir : str
        Directory containing the data files
    join_key : str
        Join strategy: 'UNITID' (recommended) or 'Institution Name'
    deduplicate : bool
        Whether to deduplicate by keeping first occurrence of each UNITID

    Returns:
    --------
    pd.DataFrame
        Merged dataset with columns from both sources
    """
    print("="*60)
    print("Loading datasets...")
    print("="*60)

    # Load both datasets
    college_results = load_college_results(data_dir)
    affordability_gap = load_affordability_gap(data_dir)

    print("\n" + "="*60)
    print("Merging datasets...")
    print("="*60)

    if join_key == 'UNITID':
        # Use ID-based merge (recommended)
        cr_id_col = 'UNIQUE_IDENTIFICATION_NUMBER_OF_THE_INSTITUTION'
        ag_id_col = 'Unit ID'

        print(f"\nMerging on UNITID columns:")
        print(f"  College Results: {cr_id_col}")
        print(f"  Affordability Gap: {ag_id_col}")

        # Ensure numeric type
        college_results[cr_id_col] = pd.to_numeric(college_results[cr_id_col], errors='coerce')
        affordability_gap[ag_id_col] = pd.to_numeric(affordability_gap[ag_id_col], errors='coerce')

        merged_df = pd.merge(
            college_results,
            affordability_gap,
            left_on=cr_id_col,
            right_on=ag_id_col,
            how='inner',
            suffixes=('_CR', '_AG')
        )

        # Deduplicate if requested
        if deduplicate:
            initial_rows = len(merged_df)
            # Keep first occurrence of each UNITID (from College Results perspective)
            merged_df = merged_df.drop_duplicates(subset=[cr_id_col], keep='first')
            print(f"\nDeduplication: {initial_rows} → {len(merged_df)} rows")

    else:
        # Fall back to name-based merge
        print(f"\nMerging on: Institution Name")
        merged_df = pd.merge(
            college_results,
            affordability_gap,
            on='Institution Name',
            how='inner',
            suffixes=('_CR', '_AG')
        )

        if deduplicate:
            initial_rows = len(merged_df)
            merged_df = merged_df.drop_duplicates(subset=['Institution Name'], keep='first')
            print(f"\nDeduplication: {initial_rows} → {len(merged_df)} rows")

    print(f"\n✓ Merge successful!")
    print(f"Final dataset: {len(merged_df)} rows, {len(merged_df.columns)} columns")
    print(f"Match rate: {len(merged_df)/len(college_results)*100:.1f}% of College Results rows")

    return merged_df


def explore_join_options(data_dir='data'):
    """
    Helper function to explore potential join keys between the datasets.

    Parameters:
    -----------
    data_dir : str
        Directory containing the data files

    Returns:
    --------
    dict
        Dictionary with information about potential join keys
    """
    college_results = load_college_results(data_dir)
    affordability_gap = load_affordability_gap(data_dir)

    # Find common columns
    common_cols = set(college_results.columns) & set(affordability_gap.columns)

    print("\n" + "="*60)
    print("Common columns between datasets:")
    print("="*60)
    for col in sorted(common_cols):
        print(f"  - {col}")

    # Check for institution identifier columns
    id_keywords = ['UNITID', 'OPEID', 'INST', 'NAME', 'COLLEGE', 'UNIVERSITY', 'STATE']

    print("\n" + "="*60)
    print("Potential identifier columns:")
    print("="*60)
    print("\nIn College Results:")
    for col in college_results.columns:
        if any(keyword in col.upper() for keyword in id_keywords):
            print(f"  - {col}")

    print("\nIn Affordability Gap:")
    for col in affordability_gap.columns:
        if any(keyword in col.upper() for keyword in id_keywords):
            print(f"  - {col}")

    return {
        'common_columns': list(common_cols),
        'college_results_cols': college_results.columns.tolist(),
        'affordability_gap_cols': affordability_gap.columns.tolist()
    }


if __name__ == "__main__":
    # Test the data loading functions
    print("Testing data loading...")
    explore_join_options()
