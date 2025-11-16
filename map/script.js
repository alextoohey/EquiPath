// --- 1. Initialize Map ---
const map = L.map('map').setView([39.8283, -98.5795], 5);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);


// --- 2. Global Variables ---
let allData = null; // This will hold all our school data
const clusterLayer = L.markerClusterGroup(); // The cluster group
map.addLayer(clusterLayer); // Add the empty layer to the map


// --- 3. Load Data ---
fetch('schools.geojson')
    .then(response => response.json())
    .then(data => {
        allData = data; // Save the data to our global variable
        updateMap("all"); // Load all schools to start
    })
    .catch(error => console.error('Error loading GeoJSON:', error));


// --- 4. Event Listener for the Sidebar ---
document.getElementById('state-select').addEventListener('change', (event) => {
    const selectedState = event.target.value;
    updateMap(selectedState);
});


// --- 5. Update Map Function ---
function updateMap(stateAbbreviation) {
    clusterLayer.clearLayers(); // Remove all old markers

    // Filter the data
    const filteredData = (stateAbbreviation === "all")
        ? allData.features // If "all", use all features
        : allData.features.filter(feature => feature.properties.STATE === stateAbbreviation);

    // Create a new GeoJSON layer with the filtered data
    const filteredGeoJson = L.geoJSON(filteredData, {
        onEachFeature: createPopup
    });

    // Add the new layer to the cluster group
    clusterLayer.addLayer(filteredGeoJson);
}


// --- 6. Create Popup Function (No Changes) ---
function createPopup(feature, layer) {
    const props = feature.properties;
    const popupContent = `
        <h3>${props.NAME || 'Unnamed School'}</h3>
        <p>
            ${props.ADDRESS || ''}<br>
            ${props.CITY || ''}, ${props.STATE || ''} ${props.ZIP || ''}
        </p>
        <p><b>Type:</b> ${props.TYPE_DESC || 'N/A'}</p>
        ${props.WEBSITE ? `<a href="http://${props.WEBSITE}" target="_blank">Website</a>` : 'No website listed'}
    `;
    layer.bindPopup(popupContent);
}