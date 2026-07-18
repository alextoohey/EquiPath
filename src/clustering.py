"""
K-means clustering module for EquiPath project.
Groups institutions into archetypes based on their characteristics.
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def add_clusters(df, n_clusters=5, random_state=42):
    """
    Add cluster labels to institutions using K-means clustering.

    Features used for clustering:
    - roi_score
    - afford_score_std
    - equity_parity
    - access_score_base (admission rate)

    Parameters:
    -----------
    df : pd.DataFrame
        Featured college DataFrame
    n_clusters : int
        Number of clusters to create
    random_state : int
        Random seed for reproducibility

    Returns:
    --------
    pd.DataFrame
        DataFrame with added cluster_id and cluster_label columns
    """

    # Select features for clustering
    feature_cols = [
        'roi_score',
        'afford_score_std',
        'equity_parity',
        'access_score_base'
    ]

    # Check if all features are present
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for clustering: {missing_cols}")

    # Extract features and handle missing values
    X = df[feature_cols].fillna(df[feature_cols].median())

    # Standardize features (important for K-means)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Perform K-means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    cluster_ids = kmeans.fit_predict(X_scaled)

    # Add cluster IDs to dataframe
    df = df.copy()
    df['cluster_id'] = cluster_ids

    # Compute cluster centroids in original scale
    centroids = pd.DataFrame(
        scaler.inverse_transform(kmeans.cluster_centers_),
        columns=feature_cols
    )

    # Assign human-readable labels based on centroid characteristics
    cluster_labels = label_clusters(centroids)

    # Map cluster IDs to labels
    df['cluster_label'] = df['cluster_id'].map(cluster_labels)

    counts = df['cluster_label'].value_counts()
    print("K-means archetypes: " + ", ".join(
        f"{label} ({count})" for label, count in counts.items()))

    return df, centroids, cluster_labels


# One-line meanings for each archetype, shown wherever the labels appear.
# Keyed by label; unknown labels fall back to a generic explanation.
ARCHETYPE_DESCRIPTIONS = {
    "Equity Champions":
        "Strong earnings outcomes, affordable, and equitable graduation rates "
        "across racial groups, but selective: treat these as reach schools.",
    "Equity-Focused Access":
        "Strong earnings outcomes and equitable graduation rates with high "
        "admission rates: good odds and good outcomes.",
    "High ROI, Uneven Outcomes":
        "Graduates earn well on average, but graduation rates differ sharply "
        "across racial groups; check the rate for students like you.",
    "Affordable & Accessible":
        "Low cost and high admission rates, with moderate earnings outcomes.",
    "High Access, Lower ROI":
        "Easy to get into, but weaker earnings-versus-debt outcomes and less "
        "generous pricing; compare against the affordable cluster.",
}

_GENERIC_DESCRIPTION = ("Named for its two strongest traits relative to the "
                        "average institution.")


def get_archetype_description(label):
    """One-sentence meaning for an archetype label (numbered variants share it)."""
    base = label.rstrip("0123456789 ")
    return ARCHETYPE_DESCRIPTIONS.get(label,
           ARCHETYPE_DESCRIPTIONS.get(base, _GENERIC_DESCRIPTION))


def label_clusters(centroids):
    """
    Assign human-readable labels to clusters based on centroid characteristics.

    The named rules cover the recurring shapes in this dataset (see
    ARCHETYPE_DESCRIPTIONS); anything else is named for its two largest
    deviations from the mean centroid, so no cluster gets a vague
    "Balanced" label.

    Parameters:
    -----------
    centroids : pd.DataFrame
        Cluster centroids

    Returns:
    --------
    dict
        Mapping from cluster_id to cluster_label
    """
    labels = {}
    feature_names = {
        'roi_score': 'ROI',
        'afford_score_std': 'Affordability',
        'equity_parity': 'Equity',
        'access_score_base': 'Access',
    }
    col_means = centroids[list(feature_names)].mean()

    for idx, row in centroids.iterrows():
        roi = row['roi_score']
        afford = row['afford_score_std']
        equity = row['equity_parity']
        access = row['access_score_base']

        if roi >= 0.7 and equity < 0.35:
            labels[idx] = "High ROI, Uneven Outcomes"
        elif roi >= 0.7 and equity >= 0.6 and access < 0.5:
            labels[idx] = "Equity Champions"
        elif roi >= 0.7 and equity >= 0.6:
            labels[idx] = "Equity-Focused Access"
        elif afford >= 0.75 and access >= 0.7:
            labels[idx] = "Affordable & Accessible"
        elif roi < 0.4 and access >= 0.7:
            labels[idx] = "High Access, Lower ROI"
        else:
            # Fallback: name the two largest deviations from the mean centroid
            devs = {col: row[col] - col_means[col] for col in feature_names}
            top_two = sorted(devs, key=lambda c: abs(devs[c]), reverse=True)[:2]
            parts = [f"{'High' if devs[c] > 0 else 'Lower'} {feature_names[c]}"
                     for c in top_two]
            labels[idx] = ", ".join(parts)

    # Ensure unique labels
    label_counts = {}
    for idx, label in labels.items():
        if label in label_counts:
            label_counts[label] += 1
            labels[idx] = f"{label} {label_counts[label]}"
        else:
            label_counts[label] = 1

    return labels


def get_cluster_summary(df):
    """
    Generate a summary of each cluster's characteristics.

    Parameters:
    -----------
    df : pd.DataFrame
        Clustered DataFrame

    Returns:
    --------
    pd.DataFrame
        Summary statistics for each cluster
    """
    if 'cluster_label' not in df.columns:
        raise ValueError("DataFrame must have cluster_label column. Run add_clusters() first.")

    summary_cols = [
        'roi_score',
        'afford_score_std',
        'afford_score_parent',
        'equity_parity',
        'access_score_base'
    ]

    summary = df.groupby('cluster_label')[summary_cols].agg(['mean', 'median', 'std']).round(3)

    return summary


def recommend_cluster_for_profile(profile, cluster_labels_dict):
    """
    Recommend which cluster archetype might be best for a given user profile.

    Parameters:
    -----------
    profile : UserProfile
        Student profile
    cluster_labels_dict : dict
        Mapping from cluster_id to cluster_label

    Returns:
    --------
    list
        Recommended cluster labels (in order of preference)
    """
    recommendations = []

    # Reverse the dict to get label -> ids
    label_to_ids = {}
    for cid, label in cluster_labels_dict.items():
        if label not in label_to_ids:
            label_to_ids[label] = []
        label_to_ids[label].append(cid)

    # Prioritize based on user profile
    if profile.income_bracket == "LOW" or profile.is_parent:
        recommendations.extend([
            "Accessible & Affordable",
            "Good Value Options",
            "Equity Champions"
        ])
    elif profile.first_gen or profile.race in ["BLACK", "HISPANIC", "NATIVE"]:
        recommendations.extend([
            "Equity Champions",
            "Equity-Focused Access",
            "Accessible & Affordable"
        ])
    else:
        recommendations.extend([
            "Equity Champions",
            "Good Value Options",
            "Balanced Options"
        ])

    # Filter to only labels that exist
    existing_labels = set(cluster_labels_dict.values())
    recommendations = [label for label in recommendations if label in existing_labels]

    return recommendations[:3]  # Top 3


if __name__ == "__main__":
    # Test clustering
    from src.features import build_college_features

    print("Building featured dataset...")
    df = build_college_features()

    print("\n" + "="*60)
    print("TESTING K-MEANS CLUSTERING")
    print("="*60)

    # Add clusters
    df_clustered, centroids, labels = add_clusters(df, n_clusters=5)

    # Get summary
    print("\n" + "="*60)
    print("CLUSTER SUMMARY STATISTICS")
    print("="*60)
    summary = get_cluster_summary(df_clustered)
    print(summary)

    # Show sample institutions from each cluster
    print("\n" + "="*60)
    print("SAMPLE INSTITUTIONS BY CLUSTER")
    print("="*60)

    display_cols = ['Institution Name', 'State of Institution', 'cluster_label',
                   'roi_score', 'afford_score_std', 'equity_parity']
    display_cols = [col for col in display_cols if col in df_clustered.columns]

    for label in sorted(df_clustered['cluster_label'].unique()):
        print(f"\n{label}:")
        print("-" * 60)
        sample = df_clustered[df_clustered['cluster_label'] == label][display_cols].head(3)
        print(sample.to_string(index=False))
