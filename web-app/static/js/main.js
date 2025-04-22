// Mobile sidebar toggle
document.getElementById('toggleSidebar').addEventListener('click', function() {
    document.querySelector('.sidebar').classList.toggle('active');
    
    const icon = this.querySelector('i');
    if (icon.classList.contains('fa-bars')) {
        icon.classList.remove('fa-bars');
        icon.classList.add('fa-times');
    } else {
        icon.classList.remove('fa-times');
        icon.classList.add('fa-bars');
    }
});

// Collapse sections
document.querySelectorAll('.sidebar-collapse').forEach(button => {
    button.addEventListener('click', function() {
        const targetId = this.getAttribute('data-target');
        const content = document.getElementById(targetId);
        const icon = this.querySelector('i');
        
        if (content.style.maxHeight === '0px') {
            content.style.maxHeight = '500px';
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-up');
        } else {
            content.style.maxHeight = '0px';
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
        }
    });
});

// Initialize map
const map = L.map('map').setView([40.755, -73.978], 13);

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Add legend to map
const legend = L.control({position: 'bottomleft'});
legend.onAdd = function() {
    const div = L.DomUtil.create('div', 'legend');
    div.innerHTML = `
        <div><b>Price Ranges</b></div>
        <div class="legend-item">
            <span class="legend-color" style="background: #4CAF50"></span> Under $6.00
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #2196F3"></span> $6.00 - $6.99
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #FFC107"></span> $7.00 - $7.99
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #F44336"></span> $8.00+
        </div>
    `;
    return div;
};
legend.addTo(map);

// Function to get marker color based on price
function getMarkerColor(price) {
    if (price < 6.00) return "#4CAF50"; // green
    if (price < 7.00) return "#2196F3"; // blue
    if (price < 8.00) return "#FFC107"; // yellow/amber
    return "#F44336"; // red
}

// DOM Elements
const addressInput = document.getElementById('address');
const searchButton = document.getElementById('searchAddress');
const submitButton = document.getElementById('submitBtn');
const latInput = document.getElementById('lat');
const lonInput = document.getElementById('lon');
const locationPreview = document.getElementById('locationPreview');
const foundAddress = document.getElementById('foundAddress');
const errorMessage = document.getElementById('errorMessage');
const successMessage = document.getElementById('successMessage');
const resetForm = document.getElementById('resetForm');
const addForm = document.getElementById('addForm');
const minPriceInput = document.getElementById('minPrice');
const maxPriceInput = document.getElementById('maxPrice');
const applyFilterButton = document.getElementById('applyFilter');
const resetFilterButton = document.getElementById('resetFilter');

// Initialize markers array
let markers = [];

// Load sandwich data on page load
loadSandwiches();

// Function to load sandwich data from API
function loadSandwiches(minPrice = null, maxPrice = null) {
    // Clear existing markers
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
    
    // Build query parameters
    let url = '/api/sandwiches';
    let params = [];
    if (minPrice !== null) params.push(`min_price=${minPrice}`);
    if (maxPrice !== null) params.push(`max_price=${maxPrice}`);
    if (params.length > 0) url += '?' + params.join('&');
    
    // Fetch data
    fetch(url)
        .then(response => response.json())
        .then(data => {
            data.forEach(deli => {
                const marker = L.circleMarker([deli.lat, deli.lon], {
                    radius: 12,
                    fillColor: getMarkerColor(deli.price),
                    color: "#000",
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                }).addTo(map);
                
                marker.bindPopup(`
                    <strong>${deli.name}</strong><br>
                    ${deli.address}<br>
                    <b>Price: $${deli.price.toFixed(2)}</b>
                `);
                
                markers.push(marker);
            });
            
            // If no results, show message
            if (data.length === 0) {
                alert('No sandwiches found with the selected price range.');
            }
        })
        .catch(error => {
            console.error('Error loading sandwich data:', error);
        });
}

// Search address functionality
let tempMarker;

searchButton.addEventListener('click', function() {
    const address = addressInput.value.trim();
    if (!address) return;
    
    // Update UI
    searchButton.disabled = true;
    errorMessage.style.display = 'none';
    
    // Use Nominatim for geocoding
    const searchQuery = encodeURIComponent(address);
    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${searchQuery}&limit=1`)
        .then(response => response.json())
        .then(data => {
            searchButton.disabled = false;
            
            if (data.length === 0) {
                // No results found
                errorMessage.style.display = 'block';
                submitButton.disabled = true;
                return;
            }
            
            const result = data[0];
            const lat = parseFloat(result.lat);
            const lon = parseFloat(result.lon);
            
            // Update hidden inputs
            latInput.value = lat;
            lonInput.value = lon;
            
            // Update the map
            if (tempMarker) {
                map.removeLayer(tempMarker);
            }
            
            tempMarker = L.marker([lat, lon]).addTo(map);
            map.setView([lat, lon], 16);
            
            // Show confirmation
            locationPreview.style.display = 'block';
            foundAddress.textContent = result.display_name;
            
            // Enable submit button
            submitButton.disabled = false;
        })
        .catch(error => {
            console.error('Error geocoding address:', error);
            searchButton.disabled = false;
            errorMessage.style.display = 'block';
            submitButton.disabled = true;
        });
});

// Submit form
addForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    if (!latInput.value || !lonInput.value) {
        alert('Please search for a valid address first');
        return;
    }
    
    const formData = {
        name: document.getElementById('name').value,
        address: foundAddress.textContent,
        price: parseFloat(document.getElementById('price').value),
        lat: parseFloat(latInput.value),
        lon: parseFloat(lonInput.value)
    };
    
    // Disable submit button
    submitButton.disabled = true;
    
    // Submit data to API
    fetch('/api/sandwiches', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            successMessage.style.display = 'block';
            errorMessage.style.display = 'none';
            
            // Reset form
            addForm.reset();
            
            // Reset UI elements
            if (tempMarker) {
                map.removeLayer(tempMarker);
            }
            locationPreview.style.display = 'none';
            
            // Reload sandwiches
            loadSandwiches();
            
            // Hide success message after 3 seconds
            setTimeout(() => {
                successMessage.style.display = 'none';
            }, 3000);
        } else {
            alert('Error: ' + (data.error || 'Failed to add sandwich price'));
            submitButton.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error submitting data. Please try again.');
        submitButton.disabled = false;
    });
});

// Reset form button
resetForm.addEventListener('click', function() {
    errorMessage.style.display = 'none';
    successMessage.style.display = 'none';
    locationPreview.style.display = 'none';
    
    if (tempMarker) {
        map.removeLayer(tempMarker);
    }
    
    map.setView([40.755, -73.978], 13);
    submitButton.disabled = true;
});

// Filter functionality
applyFilterButton.addEventListener('click', function() {
    const minPrice = minPriceInput.value ? parseFloat(minPriceInput.value) : null;
    const maxPrice = maxPriceInput.value ? parseFloat(maxPriceInput.value) : null;
    
    loadSandwiches(minPrice, maxPrice);
});

// Reset filter
resetFilterButton.addEventListener('click', function() {
    minPriceInput.value = '';
    maxPriceInput.value = '';
    loadSandwiches();
});

// Enter key in address field
addressInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        searchButton.click();
    }
}); 