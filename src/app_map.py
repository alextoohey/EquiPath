"""
Streamlit app for interactive U.S. Schools Map.
Displays postsecondary schools on a Leaflet map with clustering and filtering by state.
"""

import streamlit as st
import streamlit.components.v1 as components
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
    - **Filter by state** using the dropdown on the map
    - **Click on clusters** to zoom in and see individual schools
    - **Click on markers** to view detailed information about each school
    """)

    st.divider()

    # Read the necessary files
    map_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "map")

    # Read the HTML, CSS, and JS files
    with open(os.path.join(map_dir, "index.html"), "r") as f:
        html_content = f.read()

    with open(os.path.join(map_dir, "style.css"), "r") as f:
        css_content = f.read()

    with open(os.path.join(map_dir, "script.js"), "r") as f:
        js_content = f.read()

    # Read GeoJSON data
    geojson_path = os.path.join(map_dir, "schools.geojson")
    with open(geojson_path, "r") as f:
        geojson_data = f.read()

    # Create an embedded HTML component
    # We need to inline everything since Streamlit components don't have direct file access
    embedded_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>U.S. Schools Map</title>

        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />

        <style>
            {css_content}
        </style>
    </head>
    <body>
        <div id="sidebar">
            <h2>Filter by State</h2>
            <select id="state-select">
                <option value="all">All States</option>
                <option value="AL">Alabama</option>
                <option value="AK">Alaska</option>
                <option value="AZ">Arizona</option>
                <option value="AR">Arkansas</option>
                <option value="CA">California</option>
                <option value="CO">Colorado</option>
                <option value="CT">Connecticut</option>
                <option value="DE">Delaware</option>
                <option value="DC">District of Columbia</option>
                <option value="FL">Florida</option>
                <option value="GA">Georgia</option>
                <option value="HI">Hawaii</option>
                <option value="ID">Idaho</option>
                <option value="IL">Illinois</option>
                <option value="IN">Indiana</option>
                <option value="IA">Iowa</option>
                <option value="KS">Kansas</option>
                <option value="KY">Kentucky</option>
                <option value="LA">Louisiana</option>
                <option value="ME">Maine</option>
                <option value="MD">Maryland</option>
                <option value="MA">Massachusetts</option>
                <option value="MI">Michigan</option>
                <option value="MN">Minnesota</option>
                <option value="MS">Mississippi</option>
                <option value="MO">Missouri</option>
                <option value="MT">Montana</option>
                <option value="NE">Nebraska</option>
                <option value="NV">Nevada</option>
                <option value="NH">New Hampshire</option>
                <option value="NJ">New Jersey</option>
                <option value="NM">New Mexico</option>
                <option value="NY">New York</option>
                <option value="NC">North Carolina</option>
                <option value="ND">North Dakota</option>
                <option value="OH">Ohio</option>
                <option value="OK">Oklahoma</option>
                <option value="OR">Oregon</option>
                <option value="PA">Pennsylvania</option>
                <option value="RI">Rhode Island</option>
                <option value="SC">South Carolina</option>
                <option value="SD">South Dakota</option>
                <option value="TN">Tennessee</option>
                <option value="TX">Texas</option>
                <option value="UT">Utah</option>
                <option value="VT">Vermont</option>
                <option value="VA">Virginia</option>
                <option value="WA">Washington</option>
                <option value="WV">West Virginia</option>
                <option value="WI">Wisconsin</option>
                <option value="WY">Wyoming</option>
            </select>
        </div>
        <div id="map"></div>

        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>

        <script>
            // Embed GeoJSON data directly
            const geojsonData = {geojson_data};

            // Modified script to use embedded data
            const map = L.map('map').setView([39.8283, -98.5795], 5);

            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }}).addTo(map);

            let allData = geojsonData;
            const clusterLayer = L.markerClusterGroup();
            map.addLayer(clusterLayer);

            // Load all schools to start
            updateMap("all");

            document.getElementById('state-select').addEventListener('change', (event) => {{
                const selectedState = event.target.value;
                updateMap(selectedState);
            }});

            function updateMap(stateAbbreviation) {{
                clusterLayer.clearLayers();

                const filteredData = (stateAbbreviation === "all")
                    ? allData.features
                    : allData.features.filter(feature => feature.properties.STATE === stateAbbreviation);

                const filteredGeoJson = L.geoJSON(filteredData, {{
                    onEachFeature: createPopup
                }});

                clusterLayer.addLayer(filteredGeoJson);
            }}

            function createPopup(feature, layer) {{
                const props = feature.properties;
                const popupContent = `
                    <h3>${{props.NAME || 'Unnamed School'}}</h3>
                    <p>
                        ${{props.ADDRESS || ''}}<br>
                        ${{props.CITY || ''}}, ${{props.STATE || ''}} ${{props.ZIP || ''}}
                    </p>
                    <p><b>Type:</b> ${{props.TYPE_DESC || 'N/A'}}</p>
                    ${{props.WEBSITE ? \`<a href="http://${{props.WEBSITE}}" target="_blank">Website</a>\` : 'No website listed'}}
                `;
                layer.bindPopup(popupContent);
            }}
        </script>
    </body>
    </html>
    """

    # Display the map using Streamlit's HTML component
    # Set a reasonable height for the map
    components.html(embedded_html, height=800, scrolling=False)

    # Add some statistics below the map
    st.divider()

    # Load GeoJSON to get statistics
    geojson_obj = json.loads(geojson_data)
    total_schools = len(geojson_obj.get('features', []))

    # Count schools by state
    state_counts = {}
    for feature in geojson_obj.get('features', []):
        state = feature.get('properties', {}).get('STATE', 'Unknown')
        state_counts[state] = state_counts.get(state, 0) + 1

    # Display statistics
    st.subheader("📊 Dataset Statistics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Schools", f"{total_schools:,}")

    with col2:
        st.metric("States Represented", len(state_counts))

    with col3:
        if state_counts:
            top_state = max(state_counts.items(), key=lambda x: x[1])
            st.metric("Most Schools", f"{top_state[0]} ({top_state[1]:,})")

    # Optional: Show state breakdown
    with st.expander("📍 Schools by State"):
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
