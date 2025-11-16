3

"""
Data loading module for EquiPath project.
Handles loading and merging of College Results 2021 and Affordability Gap datasets.
Implements Parquet caching for 10-100x faster loading.
"""

import pandas as pd
import os
from pathlib import Path


def _get_cache_dir(data_dir='data'):
    """Get or create cache directory for Parquet files."""
    cache_dir = os.path.join(data_dir, '.cache')
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def _should_rebuild_cache(excel_path, parquet_path):
    """
    Check if cache should be rebuilt.

    Returns True if:
    - Parquet file doesn't exist
    - Excel file is newer than Parquet file
    """
    if not os.path.exists(parquet_path):
        return True

    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Source data file not found: {excel_path}")

    # Check modification times
    excel_mtime = os.path.getmtime(excel_path)
    parquet_mtime = os.path.getmtime(parquet_path)

    return excel_mtime > parquet_mtime


def load_college_results(data_dir='data', force_reload=False):
    """
    Load the College Results 2021 dataset with Parquet caching.

    First load converts Excel to Parquet (slow, ~10-30s).
    Subsequent loads use Parquet (fast, ~0.5-2s).

    Parameters:
    -----------
    data_dir : str
        Directory containing the data files
    force_reload : bool
        If True, ignore cache and reload from Excel

    Returns:
    --------
    pd.DataFrame
        College Results dataset
    """
    excel_file = 'College Results View 2021 Data Dump for Export.xlsx'
    excel_path = os.path.join(data_dir, excel_file)

    cache_dir = _get_cache_dir(data_dir)
    parquet_path = os.path.join(cache_dir, 'college_results.parquet')

    # Check if we should use cache
    if not force_reload and not _should_rebuild_cache(excel_path, parquet_path):
        print(f"Loading College Results from cache: {parquet_path}")
        df = pd.read_parquet(parquet_path)
        print(f"✓ Loaded {len(df)} rows and {len(df.columns)} columns from cache")
        return df

    # Load from Excel and cache
    print(f"Loading College Results from Excel: {excel_path}")
    print("  (This may take 10-30 seconds on first load...)")

    if not os.path.exists(excel_path):
        raise FileNotFoundError(
            f"Excel file not found: {excel_path}\n"
            f"Please ensure the data file exists in the {data_dir} directory."
        )

    df = pd.read_excel(excel_path)
    print(f"  Loaded {len(df)} rows and {len(df.columns)} columns")

    # Save to Parquet cache
    print(f"  Saving to cache for faster future loads...")
    # Convert object columns to string to avoid mixed type issues
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str)
    df.to_parquet(parquet_path, engine='pyarrow', compression='snappy')
    print(f"  ✓ Cache saved to: {parquet_path}")

    return df


def load_affordability_gap(data_dir='data', force_reload=False):
    """
    Load the Affordability Gap AY2022-23 dataset with Parquet caching.

    First load converts Excel to Parquet (slow, ~10-30s).
    Subsequent loads use Parquet (fast, ~0.5-2s).

    Parameters:
    -----------
    data_dir : str
        Directory containing the data files
    force_reload : bool
        If True, ignore cache and reload from Excel

    Returns:
    --------
    pd.DataFrame
        Affordability Gap dataset
    """
    excel_file = 'Affordability Gap Data AY2022-23 2.17.25.xlsx'
    excel_path = os.path.join(data_dir, excel_file)

    cache_dir = _get_cache_dir(data_dir)
    parquet_path = os.path.join(cache_dir, 'affordability_gap.parquet')

    # Check if we should use cache
    if not force_reload and not _should_rebuild_cache(excel_path, parquet_path):
        print(f"Loading Affordability Gap from cache: {parquet_path}")
        df = pd.read_parquet(parquet_path)
        print(f"✓ Loaded {len(df)} rows and {len(df.columns)} columns from cache")
        return df

    # Load from Excel and cache
    print(f"Loading Affordability Gap from Excel: {excel_path}")
    print("  (This may take 10-30 seconds on first load...)")

    if not os.path.exists(excel_path):
        raise FileNotFoundError(
            f"Excel file not found: {excel_path}\n"
            f"Please ensure the data file exists in the {data_dir} directory."
        )

    df = pd.read_excel(excel_path)
    print(f"  Loaded {len(df)} rows and {len(df.columns)} columns")

    # Save to Parquet cache
    print(f"  Saving to cache for faster future loads...")
    # Convert object columns to string to avoid mixed type issues
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str)
    df.to_parquet(parquet_path, engine='pyarrow', compression='snappy')
    print(f"  ✓ Cache saved to: {parquet_path}")

    return df


def load_merged_data(data_dir='data', join_key='UNITID', deduplicate=True, force_reload=False):
    """
    Load and merge both datasets using UNITID for best match quality.

    Uses Parquet caching for the merged result for maximum performance.

    Parameters:
    -----------
    data_dir : str
        Directory containing the data files
    join_key : str
        Join strategy: 'UNITID' (recommended) or 'Institution Name'
    deduplicate : bool
        Whether to deduplicate by keeping first occurrence of each UNITID
    force_reload : bool
        If True, ignore cache and reload/re-merge data

    Returns:
    --------
    pd.DataFrame
        Merged dataset with columns from both sources
    """
    # Check for cached merged data
    cache_dir = _get_cache_dir(data_dir)
    cache_filename = f'merged_data_{join_key.lower().replace(" ", "_")}_dedup{deduplicate}.parquet'
    merged_cache_path = os.path.join(cache_dir, cache_filename)

    if not force_reload and os.path.exists(merged_cache_path):
        print("="*60)
        print("Loading merged data from cache...")
        print("="*60)
        df = pd.read_parquet(merged_cache_path)
        print(f"✓ Loaded {len(df)} rows and {len(df.columns)} columns from cache")
        return df

    print("="*60)
    print("Loading datasets...")
    print("="*60)

    # Load both datasets (these will use their own Parquet caches)
    college_results = load_college_results(data_dir, force_reload=force_reload)
    affordability_gap = load_affordability_gap(data_dir, force_reload=force_reload)

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

        # Create canonical Institution Name column (prefer College Results version)
        if 'Institution Name_CR' in merged_df.columns:
            merged_df['Institution Name'] = merged_df['Institution Name_CR']
        elif 'Institution Name_AG' in merged_df.columns:
            merged_df['Institution Name'] = merged_df['Institution Name_AG']

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

    # Cache the merged data for future use
    print(f"\nSaving merged data to cache...")
    merged_df.to_parquet(merged_cache_path, engine='pyarrow', compression='snappy')
    print(f"✓ Cache saved to: {merged_cache_path}")

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
