"""
Shared cached data loading module for Streamlit apps.
Centralizes data loading to avoid duplication and ensure consistent caching.
"""

import streamlit as st
from src.feature_engineering import build_featured_college_df
from src.clustering import add_clusters


@st.cache_data(show_spinner=False)
def load_featured_data_with_clusters(data_dir='data', n_clusters=5):
    """
    Load and cache the featured college data with cluster labels.

    This function is cached by Streamlit, so it will only run once
    per session (or when data_dir/n_clusters changes).

    Uses Parquet caching underneath for 10-100x faster loading.

    Parameters:
    -----------
    data_dir : str
        Directory containing the data files
    n_clusters : int
        Number of clusters for K-means clustering

    Returns:
    --------
    tuple
        (df_clustered, centroids, cluster_labels)
        - df_clustered: Full featured DataFrame with cluster labels
        - centroids: Cluster centroids DataFrame
        - cluster_labels: Dict mapping cluster_id to cluster_label
    """
    print("Loading featured college data with clusters...")

    # Load featured data (uses Parquet cache)
    df = build_featured_college_df(data_dir=data_dir)

    # Add clusters
    df_clustered, centroids, cluster_labels = add_clusters(df, n_clusters=n_clusters)

    print(f"✓ Data loaded: {len(df_clustered)} colleges, {n_clusters} clusters")

    return df_clustered, centroids, cluster_labels


@st.cache_data(show_spinner=False)
def load_featured_data(data_dir='data'):
    """
    Load and cache just the featured college data (without clustering).

    This is faster than load_featured_data_with_clusters if you don't
    need cluster labels.

    Parameters:
    -----------
    data_dir : str
        Directory containing the data files

    Returns:
    --------
    pd.DataFrame
        Featured college DataFrame
    """
    print("Loading featured college data...")
    df = build_featured_college_df(data_dir=data_dir)
    print(f"✓ Data loaded: {len(df)} colleges")
    return df


def clear_cache():
    """
    Clear Streamlit cache for data loading.

    Call this if you want to force reload data (e.g., after updating source files).
    """
    st.cache_data.clear()
    print("✓ Streamlit data cache cleared")
