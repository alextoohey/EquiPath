"""
Streamlit app for interactive U.S. Schools Map.
Displays postsecondary schools on a Folium map with clustering and filtering by state.
Can show all schools or only recommended schools based on user profile.
"""

import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import MarkerCluster, FastMarkerCluster
import json
import os
import sys
import pandas as pd

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.feature_engineering import build_featured_college_df
from src.clustering import add_clusters
from src.user_profile import UserProfile
from src.scoring import rank_colleges_for_user


def main():
    """Main Streamlit app function for the interactive map."""

    # Page configuration
    st.set_page_config(
        page_title="U.S. Schools Interactive Map",
        page_icon="🗺️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Title and description
    st.title("🗺️ U.S. Postsecondary Schools Interactive Map")

    # Check if user has a saved profile from other pages
    has_profile = 'saved_profile' in st.session_state and st.session_state.saved_profile is not None
    has_recommendations = (
        ('saved_recommendations' in st.session_state and st.session_state.saved_recommendations is not None) or
        ('recommended_colleges' in st.session_state and st.session_state.recommended_colleges is not None)
    )

    if has_profile or has_recommendations:
        st.markdown("""
        Explore postsecondary schools across the United States on an interactive map.
        - **Toggle between all schools or your recommended schools**
        - **Filter by state** using the dropdown below
        - **Click on clusters** to zoom in and see individual schools
        - **Click on markers** to view detailed information about each school
        """)
    else:
        st.markdown("""
        Explore postsecondary schools across the United States on an interactive map.
        - **Filter by state** using the dropdown below
        - **Click on clusters** to zoom in and see individual schools
        - **Click on markers** to view detailed information about each school

        💡 **Tip:** Create a profile in the College Finder or AI Chat pages to see your recommended schools on the map!
        """)

    st.divider()

    # Read the GeoJSON data
    map_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "map")
    geojson_path = os.path.join(map_dir, "schools.geojson")

    with open(geojson_path, "r") as f:
        geojson_data = json.load(f)

    # Create filter options row
    filter_cols = st.columns([1, 1, 2])

    # Show profile/recommendations toggle if available
    show_mode = "all"
    recommended_schools = set()

    if has_profile or has_recommendations:
        # Check if we should default to showing only recommended colleges
        default_index = 1 if st.session_state.get('show_only_recommended', False) else 0

        with filter_cols[0]:
            show_mode = st.radio(
                "Show Schools",
                options=["all", "recommended"],
                format_func=lambda x: "🌎 All Schools" if x == "all" else "⭐ My Recommendations",
                index=default_index
            )

        # Get recommendations if in recommended mode
        if show_mode == "recommended":
            recommendations_df = None

            # Check for recommendations from My Profile page first
            if 'recommended_colleges' in st.session_state and st.session_state.recommended_colleges is not None:
                recommendations_df = st.session_state.recommended_colleges
            elif 'saved_recommendations' in st.session_state and st.session_state.saved_recommendations is not None:
                # Use saved recommendations from other pages
                recommendations_df = st.session_state.saved_recommendations
            elif has_profile and 'saved_profile' in st.session_state:
                # Generate recommendations from profile
                with st.spinner("Loading your recommended schools..."):
                    # Load data
                    df = build_featured_college_df()
                    df_clustered, centroids, labels = add_clusters(df, n_clusters=5)

                    # Get recommendations
                    profile = st.session_state.saved_profile
                    recommendations_df = rank_colleges_for_user(df_clustered, profile, top_k=50)

                    # Save for future use
                    st.session_state.saved_recommendations = recommendations_df

            # Get set of recommended school names if we have recommendations
            if recommendations_df is not None and len(recommendations_df) > 0:
                recommended_schools = set(recommendations_df['Institution Name'].tolist())
                st.info(f"📍 Showing {len(recommended_schools)} recommended schools on the map")
            else:
                st.warning("⚠️ No recommendations found. Showing all schools instead.")
                show_mode = "all"

            # Reset the flag after first use
            if 'show_only_recommended' in st.session_state:
                st.session_state.show_only_recommended = False

    # Get all unique states
    all_states = set()
    for feature in geojson_data.get('features', []):
        state = feature.get('properties', {}).get('STATE')
        if state:
            all_states.add(state)

    state_list = sorted(list(all_states))

    # State filter dropdown
    with filter_cols[1]:
        selected_state = st.selectbox(
            "Filter by State",
            options=["All States"] + state_list,
            index=0
        )

    # Filter data based on state selection
    if selected_state == "All States":
        filtered_features = geojson_data['features']
    else:
        filtered_features = [
            feature for feature in geojson_data['features']
            if feature.get('properties', {}).get('STATE') == selected_state
        ]

    # Filter by recommendations if in recommended mode
    if show_mode == "recommended" and recommended_schools:
        filtered_features = [
            feature for feature in filtered_features
            if feature.get('properties', {}).get('NAME') in recommended_schools
        ]

    # Show count
    with filter_cols[2]:
        if show_mode == "recommended":
            st.metric("Schools Displayed", f"{len(filtered_features):,}",
                     delta=f"{len(filtered_features) - len(geojson_data['features']):,} from total")
        else:
            st.metric("Schools Displayed", f"{len(filtered_features):,}")

    # Create the map
    # Center on USA or selected state
    if selected_state == "All States":
        m = folium.Map(
            location=[39.8283, -98.5795],  # Center of USA
            zoom_start=4,
            tiles='OpenStreetMap'
        )
    else:
        # Calculate center of filtered schools
        if filtered_features:
            lats = []
            lons = []
            for feature in filtered_features:
                coords = feature.get('geometry', {}).get('coordinates', [])
                if coords:
                    lons.append(coords[0])
                    lats.append(coords[1])

            if lats and lons:
                center_lat = sum(lats) / len(lats)
                center_lon = sum(lons) / len(lons)
                m = folium.Map(
                    location=[center_lat, center_lon],
                    zoom_start=7,
                    tiles='OpenStreetMap'
                )
            else:
                m = folium.Map(
                    location=[39.8283, -98.5795],
                    zoom_start=4,
                    tiles='OpenStreetMap'
                )
        else:
            m = folium.Map(
                location=[39.8283, -98.5795],
                zoom_start=4,
                tiles='OpenStreetMap'
            )

    # Use FastMarkerCluster for better performance with lots of markers
    # Create a lookup dict for detailed college data
    # Load the full college database for all schools
    college_details_lookup = {}

    # If we have recommendations, use that data
    if has_recommendations:
        # Get recommendations from whichever source has them
        recommendations_df = None
        if 'recommended_colleges' in st.session_state and st.session_state.recommended_colleges is not None:
            recommendations_df = st.session_state.recommended_colleges
        elif 'saved_recommendations' in st.session_state and st.session_state.saved_recommendations is not None:
            recommendations_df = st.session_state.saved_recommendations

        if recommendations_df is not None:
            for _, row in recommendations_df.iterrows():
                college_details_lookup[row['Institution Name']] = row

    # For all schools view, load the full database
    if show_mode == "all" or not college_details_lookup:
        try:
            with st.spinner("Loading college details..."):
                from src.feature_engineering import build_featured_college_df
                from src.clustering import add_clusters

                # Cache this in session state to avoid reloading
                if 'full_college_data' not in st.session_state:
                    df = build_featured_college_df()
                    df_clustered, _, _ = add_clusters(df, n_clusters=5)
                    st.session_state.full_college_data = df_clustered

                full_df = st.session_state.full_college_data

                # Add all colleges to lookup
                for _, row in full_df.iterrows():
                    if row['Institution Name'] not in college_details_lookup:
                        college_details_lookup[row['Institution Name']] = row
        except Exception as e:
            st.warning(f"Could not load detailed college data: {e}")

    # Prepare data for FastMarkerCluster
    marker_data = []
    for feature in filtered_features:
        props = feature.get('properties', {})
        coords = feature.get('geometry', {}).get('coordinates', [])

        if coords:
            lon, lat = coords[0], coords[1]
            school_name = props.get('NAME', 'Unnamed School')

            # Create popup content
            is_recommended = school_name in recommended_schools if recommended_schools else False

            # Get detailed data if available
            college_data = college_details_lookup.get(school_name, None)

            popup_html = f"""
            <div style="font-family: Arial, sans-serif; width: 280px;">
                <h4 style="margin: 0 0 10px 0; color: {'#FFD700' if is_recommended else '#1f77b4'};">
                    {'⭐ ' if is_recommended else ''}{school_name}
                </h4>
            """

            # If we have detailed college data, show that instead of basic info
            if college_data is not None:
                # Show detailed information from recommendations
                # Use Sector Name or Institution Type for text description
                sector_name = college_data.get('Sector Name', None)
                if pd.notna(sector_name):
                    sector_str = str(sector_name)
                else:
                    sector_str = str(college_data.get('Institution Type', 'N/A'))

                if 'Public' in sector_str:
                    institution_type = 'Public'
                    icon = '🏛️'
                elif 'Private' in sector_str:
                    institution_type = 'Private'
                    icon = '🏢'
                else:
                    institution_type = 'N/A'
                    icon = '🎓'

                popup_html += f'<p style="margin: 5px 0;"><b>{icon} {institution_type}</b></p>'

                # Admission Rate
                admit_rate = pd.to_numeric(college_data.get('Total Percent of Applicants Admitted', None), errors='coerce')
                if pd.notna(admit_rate):
                    popup_html += f'<p style="margin: 5px 0;"><b>Admission Rate:</b> {admit_rate:.1f}%</p>'

                # Net Price
                net_price = pd.to_numeric(college_data.get('Net Price', None), errors='coerce')
                if pd.notna(net_price):
                    popup_html += f'<p style="margin: 5px 0;"><b>Net Price:</b> ${net_price:,.0f}/year</p>'

                # Median Earnings
                earnings = pd.to_numeric(college_data.get('Median Earnings of Students Working and Not Enrolled 10 Years After Entry', None), errors='coerce')
                if pd.notna(earnings):
                    popup_html += f'<p style="margin: 5px 0;"><b>Median Earnings (10yr):</b> ${earnings:,.0f}</p>'

                # Match Score
                if 'user_score' in college_data:
                    popup_html += f'<p style="margin: 5px 0;"><b>Match Score:</b> {college_data["user_score"]:.3f}</p>'

            else:
                # Show basic GeoJSON information
                popup_html += f"""
                <p style="margin: 5px 0;">
                    <b>Location:</b><br>
                    {props.get('CITY', 'N/A')}, {props.get('STATE', 'N/A')}
                </p>
                <p style="margin: 5px 0;">
                    <b>Type:</b> {props.get('TYPE_DESC', 'N/A') if props.get('TYPE_DESC') else 'N/A'}
                </p>
                """

            # Website link
            if college_data is not None:
                # Try to get website from college data first
                website = None
            else:
                website = props.get('WEBSITE')

            if website:
                popup_html += f'<p style="margin: 5px 0;"><a href="http://{website}" target="_blank">🔗 Visit Website</a></p>'

            if is_recommended:
                popup_html += '<p style="margin: 8px 0 0 0; padding: 5px; background: #FFF9E6; border-left: 3px solid #FFD700;"><b>✨ Recommended for you!</b></p>'

            popup_html += "</div>"

            marker_data.append([lat, lon, popup_html, school_name])

    # Add markers using MarkerCluster for popups support
    marker_cluster = MarkerCluster(
        name='Schools',
        overlay=True,
        control=False,
        icon_create_function=None
    ).add_to(m)

    # Add markers to cluster
    for lat, lon, popup, tooltip in marker_data:
        is_recommended = show_mode == "recommended"

        if is_recommended:
            # Use custom icon with graduation cap for recommended schools
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup, max_width=300),
                tooltip=tooltip,
                icon=folium.Icon(color='orange', icon='graduation-cap', prefix='fa')
            ).add_to(marker_cluster)
        else:
            # Use simple circle markers for regular schools
            folium.CircleMarker(
                location=[lat, lon],
                radius=5,
                popup=folium.Popup(popup, max_width=300),
                tooltip=tooltip,
                color='#3388ff',
                fill=True,
                fillColor='#3388ff',
                fillOpacity=0.7,
                weight=2
            ).add_to(marker_cluster)

    # Display the map
    st_folium(m, width=None, height=600, use_container_width=True, returned_objects=[])

    # Add statistics below the map
    st.divider()

    # Display statistics
    st.subheader("📊 Dataset Statistics")

    total_schools = len(geojson_data.get('features', []))

    # Count schools by state
    state_counts = {}
    for feature in geojson_data.get('features', []):
        state = feature.get('properties', {}).get('STATE', 'Unknown')
        state_counts[state] = state_counts.get(state, 0) + 1

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Schools in Database", f"{total_schools:,}")

    with col2:
        st.metric("States Represented", len(state_counts))

    with col3:
        if state_counts:
            top_state = max(state_counts.items(), key=lambda x: x[1])
            st.metric("Most Schools", f"{top_state[0]} ({top_state[1]:,})")

    # Show current filter info
    if selected_state != "All States":
        st.info(f"📍 Currently filtered to **{selected_state}** - showing **{len(filtered_features):,}** schools")

    if show_mode == "recommended":
        st.success(f"⭐ Showing your **top {len(recommended_schools)}** recommended schools" +
                  (f" in **{selected_state}**" if selected_state != "All States" else ""))

    # Optional: Show state breakdown
    with st.expander("📍 Schools by State (Full Database)"):
        # Sort states by count
        sorted_states = sorted(state_counts.items(), key=lambda x: x[1], reverse=True)

        # Create columns for display
        cols = st.columns(4)
        for idx, (state, count) in enumerate(sorted_states):
            col_idx = idx % 4
            with cols[col_idx]:
                st.write(f"**{state}:** {count:,}")

    # Show profile summary if available
    if has_profile:
        with st.expander("👤 Your Profile Settings"):
            prof = st.session_state.saved_profile
            st.write(f"**Budget:** ${prof.budget:,.0f}")
            st.write(f"**GPA:** {prof.gpa}")
            st.write(f"**State:** {prof.state or 'Not specified'}")
            st.write(f"**In-state only:** {'Yes' if prof.in_state_only else 'No'}")
            st.write(f"**Public only:** {'Yes' if prof.public_only else 'No'}")
            if st.button("🔄 Update Profile"):
                st.info("Go to the College Finder or AI Chat page to update your profile")


if __name__ == "__main__":
    main()
