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

from src.features import build_college_features
from src.clustering import add_clusters, ARCHETYPE_DESCRIPTIONS


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

    # Recommendations generated on the My Recommendations page are shared via
    # session state, so the toggle appears however the user navigates here
    has_recommendations = (
        st.session_state.get('current_recommendations') is not None
        and len(st.session_state.current_recommendations) > 0
    )

    if has_recommendations:
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

        💡 **Tip:** Build a profile on the My Profile or Chat Assistant page, generate recommendations, and they will appear here!
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

    if has_recommendations:
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
            recommendations_df = st.session_state.current_recommendations

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

    # Build a compact popup-details lookup once per session.
    # Selecting a handful of columns and converting to plain dicts is far
    # cheaper than iterating full DataFrame rows on every rerun.
    if 'college_popup_details' not in st.session_state:
        try:
            with st.spinner("Loading college details (first visit only)..."):
                if 'full_college_data' not in st.session_state:
                    df = build_college_features()
                    df_clustered, _, _ = add_clusters(df, n_clusters=5)
                    st.session_state.full_college_data = df_clustered

                full_df = st.session_state.full_college_data
                cols = {
                    'name': 'Institution Name',
                    'sector': 'Sector Name',
                    'admit': 'Total Percent of Applicants Admitted',
                    'price': 'Net Price',
                    'earnings': 'Median Earnings of Students Working and Not Enrolled 10 Years After Entry',
                    'archetype': 'cluster_label',
                }
                available = {k: c for k, c in cols.items() if c in full_df.columns}
                slim = full_df[list(available.values())].copy()
                slim.columns = list(available.keys())
                for num_col in ('admit', 'price', 'earnings'):
                    if num_col in slim.columns:
                        slim[num_col] = pd.to_numeric(slim[num_col], errors='coerce')
                st.session_state.college_popup_details = {
                    rec['name']: rec for rec in slim.to_dict('records')
                }
        except Exception as e:
            st.warning(f"Could not load detailed college data: {e}")
            st.session_state.college_popup_details = {}

    details_lookup = st.session_state.college_popup_details

    def popup_fields(school_name):
        """Formatted (type, admit, price, earnings, archetype) strings for a school, '' when unknown."""
        d = details_lookup.get(school_name)
        if not d:
            return '', '', '', '', ''
        sector = str(d.get('sector') or '')
        if 'Public' in sector:
            type_str = 'Public'
        elif 'Private' in sector:
            type_str = 'Private'
        else:
            type_str = ''
        admit = d.get('admit')
        price = d.get('price')
        earnings = d.get('earnings')
        admit_str = f"{admit:.1f}%" if pd.notna(admit) else ''
        price_str = f"${price:,.0f}" if pd.notna(price) else ''
        earn_str = f"${earnings:,.0f}" if pd.notna(earnings) else ''
        archetype = d.get('archetype')
        arch_str = str(archetype) if archetype and pd.notna(archetype) else ''
        return type_str, admit_str, price_str, earn_str, arch_str

    if show_mode == "recommended":
        # Few markers: rich pins with full popups are fine
        import html as html_lib

        marker_cluster = MarkerCluster(name='Schools', overlay=True, control=False).add_to(m)

        for feature in filtered_features:
            props = feature.get('properties', {})
            coords = feature.get('geometry', {}).get('coordinates', [])
            if not coords:
                continue
            lon, lat = coords[0], coords[1]
            school_name = props.get('NAME', 'Unnamed School')
            type_str, admit_str, price_str, earn_str, arch_str = popup_fields(school_name)

            popup_html = f"""
            <div style="font-family: Arial, sans-serif; width: 280px;">
                <h4 style="margin: 0 0 10px 0; color: #FFD700;">⭐ {html_lib.escape(school_name)}</h4>
                <p style="margin: 5px 0;"><b>Location:</b> {html_lib.escape(str(props.get('CITY', 'N/A')))}, {html_lib.escape(str(props.get('STATE', 'N/A')))}</p>
            """
            if type_str:
                popup_html += f'<p style="margin: 5px 0;"><b>Type:</b> {type_str}</p>'
            if admit_str:
                popup_html += f'<p style="margin: 5px 0;"><b>Admission Rate:</b> {admit_str}</p>'
            if price_str:
                popup_html += f'<p style="margin: 5px 0;"><b>Net Price:</b> {price_str}/year</p>'
            if earn_str:
                popup_html += f'<p style="margin: 5px 0;"><b>Median Earnings (10yr):</b> {earn_str}</p>'
            if arch_str:
                popup_html += f'<p style="margin: 5px 0;"><b>Archetype:</b> {arch_str}</p>'
            popup_html += '<p style="margin: 8px 0 0 0; padding: 5px; background: #FFF9E6; border-left: 3px solid #FFD700;"><b>✨ Recommended for you!</b></p></div>'

            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=school_name,
                icon=folium.Icon(color='orange', icon='graduation-cap', prefix='fa')
            ).add_to(marker_cluster)

    else:
        # All-schools view: FastMarkerCluster builds markers client-side from a
        # compact data array — dramatically faster than serializing 6,800
        # individual Marker objects with server-rendered popup HTML.
        rows_key = f"map_rows_{selected_state}"
        if rows_key not in st.session_state:
            rows = []
            for feature in filtered_features:
                props = feature.get('properties', {})
                coords = feature.get('geometry', {}).get('coordinates', [])
                if not coords:
                    continue
                lon, lat = coords[0], coords[1]
                school_name = props.get('NAME', 'Unnamed School')
                type_str, admit_str, price_str, earn_str, arch_str = popup_fields(school_name)
                rows.append([
                    lat, lon, school_name,
                    str(props.get('CITY', 'N/A')), str(props.get('STATE', 'N/A')),
                    type_str, admit_str, price_str, earn_str, arch_str,
                ])
            st.session_state[rows_key] = rows

        marker_callback = """
        function (row) {
            var marker = L.circleMarker(new L.LatLng(row[0], row[1]), {
                radius: 5, color: '#3388ff', fill: true,
                fillColor: '#3388ff', fillOpacity: 0.7, weight: 2
            });
            function esc(t) {
                return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            }
            var html = '<div style="font-family: Arial, sans-serif; width: 240px;">'
                + '<h4 style="margin:0 0 8px 0; color:#1f77b4;">' + esc(row[2]) + '</h4>'
                + '<p style="margin:4px 0;"><b>Location:</b> ' + esc(row[3]) + ', ' + esc(row[4]) + '</p>'
                + (row[5] ? '<p style="margin:4px 0;"><b>Type:</b> ' + esc(row[5]) + '</p>' : '')
                + (row[6] ? '<p style="margin:4px 0;"><b>Admission Rate:</b> ' + esc(row[6]) + '</p>' : '')
                + (row[7] ? '<p style="margin:4px 0;"><b>Net Price:</b> ' + esc(row[7]) + '/year</p>' : '')
                + (row[8] ? '<p style="margin:4px 0;"><b>Median Earnings (10yr):</b> ' + esc(row[8]) + '</p>' : '')
                + (row[9] ? '<p style="margin:4px 0;"><b>Archetype:</b> ' + esc(row[9]) + '</p>' : '')
                + '</div>';
            marker.bindPopup(html, {maxWidth: 300});
            marker.bindTooltip(esc(row[2]));
            return marker;
        }
        """
        FastMarkerCluster(
            data=st.session_state[rows_key],
            callback=marker_callback,
            name='Schools',
            control=False,
        ).add_to(m)

    with st.expander("🏷️ What do the school archetypes mean?"):
        st.markdown(
            "Every institution is assigned one of five archetypes via K-means "
            "clustering on four indices (ROI, affordability, equity, access). "
            "They appear in the map popups:")
        for name, desc in ARCHETYPE_DESCRIPTIONS.items():
            st.markdown(f"- **{name}**: {desc}")

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

if __name__ == "__main__":
    main()
