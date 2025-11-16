"""
Distance calculation utilities for EquiPath.
Handles zip code lookups and distance filtering for college searches.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional
from math import radians, cos, sin, asin, sqrt

try:
    from uszipcode import SearchEngine
    USZIPCODE_AVAILABLE = True
except (ImportError, AttributeError) as e:
    # AttributeError can occur with version incompatibilities
    USZIPCODE_AVAILABLE = False

# Fallback to pgeocode if uszipcode is not available
try:
    import pgeocode
    PGEOCODE_AVAILABLE = True
except ImportError:
    PGEOCODE_AVAILABLE = False

# Initialize geocoder lazily (don't initialize at import time to avoid SSL issues)
_nomi = None
_nomi_initialized = False

def _get_nomi():
    """Lazily initialize pgeocode Nominatim."""
    global _nomi, _nomi_initialized
    if _nomi_initialized:
        return _nomi

    _nomi_initialized = True
    if PGEOCODE_AVAILABLE and not USZIPCODE_AVAILABLE:
        try:
            _nomi = pgeocode.Nominatim('us')
        except Exception as e:
            print(f"Warning: Could not initialize pgeocode: {e}")
            _nomi = None
    return _nomi


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.

    Uses the Haversine formula to calculate distance in miles.

    Parameters:
    -----------
    lat1, lon1 : float
        Latitude and longitude of first point (in degrees)
    lat2, lon2 : float
        Latitude and longitude of second point (in degrees)

    Returns:
    --------
    float
        Distance in miles

    Examples:
    ---------
    >>> # Distance from New York to Los Angeles
    >>> haversine_distance(40.7128, -74.0060, 34.0522, -118.2437)
    2451.0
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    # Radius of earth in miles
    miles = 3959 * c
    return miles


def get_zip_coordinates(zip_code: str) -> Optional[Tuple[float, float]]:
    """
    Get latitude and longitude for a given zip code.

    Parameters:
    -----------
    zip_code : str
        5-digit US zip code

    Returns:
    --------
    tuple or None
        (latitude, longitude) if found, None otherwise

    Examples:
    ---------
    >>> coords = get_zip_coordinates("10001")  # New York, NY
    >>> if coords:
    ...     lat, lon = coords
    ...     print(f"Coordinates: {lat:.2f}, {lon:.2f}")
    Coordinates: 40.75, -73.99
    """
    # Try uszipcode first
    if USZIPCODE_AVAILABLE:
        try:
            search = SearchEngine()
            zipcode = search.by_zipcode(zip_code)

            if zipcode and zipcode.lat and zipcode.lng:
                return (zipcode.lat, zipcode.lng)
        except Exception as e:
            print(f"uszipcode error for {zip_code}: {e}")

    # Fallback to pgeocode
    nomi = _get_nomi()
    if nomi is not None:
        try:
            result = nomi.query_postal_code(zip_code)
            if result is not None and not pd.isna(result.latitude) and not pd.isna(result.longitude):
                return (float(result.latitude), float(result.longitude))
        except Exception as e:
            print(f"pgeocode error for {zip_code}: {e}")

    print(f"Warning: Could not find coordinates for zip code {zip_code}")
    return None


def filter_by_radius(
    df: pd.DataFrame,
    zip_code: str,
    radius_miles: float,
    lat_col: str = 'Latitude',
    lon_col: str = 'Longitude'
) -> pd.DataFrame:
    """
    Filter colleges within a certain radius of a zip code.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with college data including latitude and longitude
    zip_code : str
        5-digit US zip code to search from
    radius_miles : float
        Maximum distance in miles
    lat_col : str
        Name of latitude column in DataFrame (default: 'Latitude')
    lon_col : str
        Name of longitude column in DataFrame (default: 'Longitude')

    Returns:
    --------
    pd.DataFrame
        Filtered DataFrame with colleges within radius, with added 'distance_miles' column

    Examples:
    ---------
    >>> # Find colleges within 50 miles of 90210 (Beverly Hills, CA)
    >>> nearby = filter_by_radius(colleges_df, "90210", 50)
    >>> print(f"Found {len(nearby)} colleges within 50 miles")
    """
    # Get coordinates for zip code
    zip_coords = get_zip_coordinates(zip_code)
    if zip_coords is None:
        print(f"Could not find coordinates for zip code {zip_code}. Returning unfiltered data.")
        return df

    zip_lat, zip_lon = zip_coords

    # Make a copy to avoid modifying original
    df_copy = df.copy()

    # Try to find lat/lon columns - check multiple possible names
    possible_lat_names = [lat_col, 'Latitude', 'LATITUDE', 'lat', 'latitude']
    possible_lon_names = [lon_col, 'Longitude', 'LONGITUDE', 'lon', 'longitude']

    actual_lat_col = None
    actual_lon_col = None

    for name in possible_lat_names:
        if name in df_copy.columns:
            actual_lat_col = name
            break

    for name in possible_lon_names:
        if name in df_copy.columns:
            actual_lon_col = name
            break

    if actual_lat_col is None or actual_lon_col is None:
        print(f"Warning: Could not find latitude/longitude columns. Tried: {possible_lat_names}, {possible_lon_names}")
        print(f"Available columns: {[c for c in df_copy.columns if 'lat' in c.lower() or 'lon' in c.lower()]}")
        return df

    # Use the found column names
    lat_col = actual_lat_col
    lon_col = actual_lon_col

    # Filter out rows with missing coordinates
    df_with_coords = df_copy[
        df_copy[lat_col].notna() & df_copy[lon_col].notna()
    ].copy()

    if len(df_with_coords) == 0:
        print("Warning: No schools have coordinate data. Returning empty DataFrame.")
        return df_with_coords

    # Calculate distance for each college
    distances = []
    for _, row in df_with_coords.iterrows():
        try:
            distance = haversine_distance(
                zip_lat, zip_lon,
                float(row[lat_col]), float(row[lon_col])
            )
            distances.append(distance)
        except (ValueError, TypeError):
            distances.append(np.nan)

    df_with_coords['distance_miles'] = distances

    # Filter to within radius
    df_filtered = df_with_coords[
        df_with_coords['distance_miles'] <= radius_miles
    ].copy()

    # Sort by distance
    df_filtered = df_filtered.sort_values('distance_miles')

    print(f"Found {len(df_filtered)} colleges within {radius_miles} miles of {zip_code}")

    return df_filtered


def add_distance_column(
    df: pd.DataFrame,
    zip_code: str,
    lat_col: str = 'Latitude',
    lon_col: str = 'Longitude'
) -> pd.DataFrame:
    """
    Add a distance column to the DataFrame without filtering.

    Useful for showing distances in results while applying other filters.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with college data
    zip_code : str
        5-digit US zip code to measure distance from
    lat_col : str
        Name of latitude column (default: 'Latitude')
    lon_col : str
        Name of longitude column (default: 'Longitude')

    Returns:
    --------
    pd.DataFrame
        DataFrame with added 'distance_miles' column
    """
    # Get coordinates for zip code
    zip_coords = get_zip_coordinates(zip_code)
    if zip_coords is None:
        df['distance_miles'] = np.nan
        return df

    zip_lat, zip_lon = zip_coords
    df_copy = df.copy()

    # Try to find lat/lon columns - check multiple possible names
    possible_lat_names = [lat_col, 'Latitude', 'LATITUDE', 'lat', 'latitude']
    possible_lon_names = [lon_col, 'Longitude', 'LONGITUDE', 'lon', 'longitude']

    actual_lat_col = None
    actual_lon_col = None

    for name in possible_lat_names:
        if name in df_copy.columns:
            actual_lat_col = name
            break

    for name in possible_lon_names:
        if name in df_copy.columns:
            actual_lon_col = name
            break

    if actual_lat_col is None or actual_lon_col is None:
        print(f"Warning: Could not find latitude/longitude columns. Tried: {possible_lat_names}, {possible_lon_names}")
        df_copy['distance_miles'] = np.nan
        return df_copy

    # Use the found column names
    lat_col = actual_lat_col
    lon_col = actual_lon_col

    # Calculate distance for each row
    distances = []
    for _, row in df_copy.iterrows():
        if pd.notna(row.get(lat_col)) and pd.notna(row.get(lon_col)):
            try:
                distance = haversine_distance(
                    zip_lat, zip_lon,
                    float(row[lat_col]), float(row[lon_col])
                )
                distances.append(distance)
            except (ValueError, TypeError):
                distances.append(np.nan)
        else:
            distances.append(np.nan)

    df_copy['distance_miles'] = distances
    return df_copy


if __name__ == "__main__":
    # Test the functions
    print("Testing distance utilities...\n")

    # Test 1: Haversine distance
    print("Test 1: Haversine distance")
    print("-" * 40)
    ny_lat, ny_lon = 40.7128, -74.0060  # New York
    la_lat, la_lon = 34.0522, -118.2437  # Los Angeles
    distance = haversine_distance(ny_lat, ny_lon, la_lat, la_lon)
    print(f"New York to Los Angeles: {distance:.1f} miles")

    # Test 2: Zip code lookup
    print("\nTest 2: Zip code lookup")
    print("-" * 40)
    test_zips = ["10001", "90210", "60601", "02101"]
    for zip_code in test_zips:
        coords = get_zip_coordinates(zip_code)
        if coords:
            print(f"Zip {zip_code}: ({coords[0]:.4f}, {coords[1]:.4f})")

    # Test 3: Distance filtering
    print("\nTest 3: Distance filtering with sample data")
    print("-" * 40)
    sample_colleges = pd.DataFrame({
        'Institution Name': ['UCLA', 'USC', 'Berkeley', 'Stanford'],
        'Latitude': [34.0689, 34.0224, 37.8719, 37.4275],
        'Longitude': [-118.4452, -118.2851, -122.2585, -122.1697]
    })

    nearby = filter_by_radius(sample_colleges, "90210", 50)  # Beverly Hills
    print(f"\nColleges within 50 miles of 90210:")
    if not nearby.empty:
        for _, row in nearby.iterrows():
            print(f"  {row['Institution Name']}: {row['distance_miles']:.1f} miles")

    print("\n✓ All tests complete!")
