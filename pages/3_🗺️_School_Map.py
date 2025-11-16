"""
Streamlit app for interactive U.S. Schools Map.
Displays postsecondary schools on a Folium map with clustering and filtering by state.
"""

import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import MarkerCluster
import json
import os

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
    st.markdown("""
    Explore postsecondary schools across the United States on an interactive map.
    - **Filter by state** using the dropdown below
    - **Click on clusters** to zoom in and see individual schools
    - **Click on markers** to view detailed information about each school
    """)

    st.divider()

    # Read the GeoJSON data
    map_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "map")
    geojson_path = os.path.join(map_dir, "schools.geojson")

    with open(geojson_path, "r") as f:
        geojson_data = json.load(f)

    # Get all unique states
    all_states = set()
    for feature in geojson_data.get('features', []):
        state = feature.get('properties', {}).get('STATE')
        if state:
            all_states.add(state)

    state_list = sorted(list(all_states))

    # State filter dropdown
    col1, col2 = st.columns([1, 3])

    with col1:
        selected_state = st.selectbox(
            "Filter by State",
            options=["All States"] + state_list,
            index=0
        )

    # Filter data based on selection
    if selected_state == "All States":
        filtered_features = geojson_data['features']
    else:
        filtered_features = [
            feature for feature in geojson_data['features']
            if feature.get('properties', {}).get('STATE') == selected_state
        ]

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

    # Add marker cluster
    marker_cluster = MarkerCluster().add_to(m)

    # Add markers for each school
    for feature in filtered_features:
        props = feature.get('properties', {})
        coords = feature.get('geometry', {}).get('coordinates', [])

        if coords:
            lon, lat = coords[0], coords[1]

            # Create popup content
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; width: 250px;">
                <h4 style="margin: 0 0 10px 0; color: #1f77b4;">{props.get('NAME', 'Unnamed School')}</h4>
                <p style="margin: 5px 0;">
                    <b>Address:</b><br>
                    {props.get('ADDRESS', 'N/A')}<br>
                    {props.get('CITY', 'N/A')}, {props.get('STATE', 'N/A')} {props.get('ZIP', 'N/A')}
                </p>
                <p style="margin: 5px 0;">
                    <b>Type:</b> {props.get('TYPE_DESC', 'N/A')}
                </p>
            """

            if props.get('WEBSITE'):
                popup_html += f'<p style="margin: 5px 0;"><a href="http://{props.get("WEBSITE")}" target="_blank">Visit Website</a></p>'

            popup_html += "</div>"

            # Add marker to cluster
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=props.get('NAME', 'School'),
                icon=folium.Icon(color='blue', icon='graduation-cap', prefix='fa')
            ).add_to(marker_cluster)

    # Display the map
    with col2:
        st.info(f"Showing {len(filtered_features):,} schools")

    st_folium(m, width=None, height=600, use_container_width=True)

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
        st.metric("Total Schools", f"{total_schools:,}")

    with col2:
        st.metric("States Represented", len(state_counts))

    with col3:
        if state_counts:
            top_state = max(state_counts.items(), key=lambda x: x[1])
            st.metric("Most Schools", f"{top_state[0]} ({top_state[1]:,})")

    # Show current filter info
    if selected_state != "All States":
        st.info(f"📍 Currently showing **{len(filtered_features):,}** schools in **{selected_state}**")

    # Optional: Show state breakdown
    with st.expander("📍 Schools by State (Full List)"):
        # Sort states by count
        sorted_states = sorted(state_counts.items(), key=lambda x: x[1], reverse=True)

        # Create columns for display
        cols = st.columns(4)
        for idx, (state, count) in enumerate(sorted_states):
            col_idx = idx % 4
            with cols[col_idx]:
                st.write(f"**{state}:** {count:,}")


if __name__ == "__main__":
    main()
