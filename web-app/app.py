from flask import Flask, render_template, request, jsonify, url_for, redirect, flash
from pymongo import MongoClient
from datetime import datetime
import os
import requests
import json
import logging
import math

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, static_folder='static', static_url_path='/static',
            template_folder=os.path.join(basedir, 'templates'))
app.secret_key = 'sandwich_tracker_secret_key'  # For flash messages

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = MongoClient("mongodb://mongodb:27017")
db = client["sandwich_db"]
collection = db["sandwich_prices"]

def preload_sandwiches():
    if collection.count_documents({}) == 0:
        collection.insert_many([
            {
                "name": "Joe's Deli",
                "address": "123 Broadway, New York, NY",
                "lat": 40.728,
                "lon": -73.991,
                "price": 5.99,
                "last_updated": datetime.now()
            },
            {
                "name": "East Side Bites",
                "address": "456 Madison Ave, New York, NY",
                "lat": 40.732,
                "lon": -73.987,
                "price": 6.50,
                "last_updated": datetime.now()
            },
            {
                "name": "West Village Deli",
                "address": "789 Greenwich St, New York, NY",
                "lat": 40.735,
                "lon": -74.005,
                "price": 7.25,
                "last_updated": datetime.now()
            }
        ])

# Helper functions for getting marker color
def get_marker_color(price):
    """Get color code for price marker."""
    if price < 6.00:
        return "#4CAF50"  # green
    if price < 7.00:
        return "#2196F3"  # blue
    if price < 8.00:
        return "#FFC107"  # yellow/amber
    return "#F44336"  # red

# Geocoding providers
def geocode_with_nominatim(address):
    """Geocode an address using Nominatim API."""
    search_query = requests.utils.quote(address)
    response = requests.get(
        f"https://nominatim.openstreetmap.org/search?format=json&q={search_query}&limit=1",
        headers={'User-Agent': 'NYC Sandwich Price Tracker'}
    )
    
    if response.status_code != 200:
        logger.error(f"Nominatim API error: {response.status_code}")
        return None
    
    data = response.json()
    if not data:
        logger.info(f"No results from Nominatim for: {address}")
        return None
    
    result = data[0]
    return {
        "lat": float(result["lat"]),
        "lon": float(result["lon"]),
        "display_name": result["display_name"],
        "provider": "nominatim"
    }

def geocode_with_local_database(address):
    """Try to geocode using our existing database entries."""
    # Simplified matching - in production you'd want more sophisticated text matching
    address_lower = address.lower()
    
    # Look for partial address matches in our database
    for deli in collection.find():
        if any(term in deli["address"].lower() for term in address_lower.split()):
            logger.info(f"Found address match in database: {deli['address']}")
            return {
                "lat": deli["lat"],
                "lon": deli["lon"],
                "display_name": deli["address"],
                "provider": "local_db"
            }
    
    return None

def find_nearby_sandwiches(lat, lon, radius=1):
    """Find sandwiches near a specific location."""
    # Find nearby sandwiches
    results = list(collection.find({
        "lat": {"$gt": lat - 0.01 * radius, "$lt": lat + 0.01 * radius},
        "lon": {"$gt": lon - 0.01 * radius, "$lt": lon + 0.01 * radius}
    }, {"_id": 0}))
    
    # Calculate distances and sort
    for result in results:
        # Simplified distance calculation (not accurate but faster than haversine)
        result["distance"] = math.sqrt((result["lat"] - lat)**2 + (result["lon"] - lon)**2) * 111  # km
    
    # Sort by distance
    results.sort(key=lambda x: x["distance"])
    
    return results

@app.route("/")
def home():
    """Render the main application with all sandwich data."""
    # Get filter parameters
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    
    # Build query for filtering
    query = {}
    if min_price is not None:
        query["price"] = {"$gte": min_price}
    if max_price is not None:
        if "price" in query:
            query["price"]["$lte"] = max_price
        else:
            query["price"] = {"$lte": max_price}
    
    # Get all sandwich data with applied filters
    sandwiches = list(collection.find(query, {"_id": 0}))
    
    # Get center coordinates (default or based on data)
    if sandwiches:
        center_lat = sum(s["lat"] for s in sandwiches) / len(sandwiches)
        center_lon = sum(s["lon"] for s in sandwiches) / len(sandwiches)
    else:
        center_lat = 40.755
        center_lon = -73.978
    
    # Format sandwich data for the template
    for sandwich in sandwiches:
        sandwich["color"] = get_marker_color(sandwich["price"])
    
    return render_template(
        "index.html", 
        sandwiches=sandwiches,
        center_lat=center_lat,
        center_lon=center_lon,
        min_price=min_price,
        max_price=max_price,
        search_results=None
    )

@app.route("/search", methods=["GET", "POST"])
def search():
    """Handle address search and show results."""
    search_results = None
    nearby_sandwiches = []
    
    if request.method == "POST":
        address = request.form.get("address", "").strip()
    else:
        address = request.args.get("address", "").strip()
    
    if address:
        # If address doesn't already include New York, append it
        if "new york" not in address.lower() and "ny" not in address.lower():
            address += ", New York, NY"
        
        logger.info(f"Searching for address: {address}")
        
        # Try our database first
        result = geocode_with_local_database(address)
        
        # Fall back to Nominatim
        if not result:
            result = geocode_with_nominatim(address)
        
        if result:
            search_results = result
            nearby_sandwiches = find_nearby_sandwiches(result["lat"], result["lon"])
            
            # For logging and debugging
            logger.info(f"Found location: {result}")
            logger.info(f"Found {len(nearby_sandwiches)} nearby sandwich shops")
        
        else:
            # No results found
            flash("Address not found. Please try a more specific address.", "error")
    
    # Get all sandwich data (for map display)
    all_sandwiches = list(collection.find({}, {"_id": 0}))
    
    # Format sandwich data for the template
    for sandwich in all_sandwiches:
        sandwich["color"] = get_marker_color(sandwich["price"])
    
    # Determine map center
    if search_results:
        center_lat = search_results["lat"]
        center_lon = search_results["lon"]
        zoom_level = 16
    elif all_sandwiches:
        center_lat = sum(s["lat"] for s in all_sandwiches) / len(all_sandwiches)
        center_lon = sum(s["lon"] for s in all_sandwiches) / len(all_sandwiches)
        zoom_level = 13
    else:
        center_lat = 40.755
        center_lon = -73.978
        zoom_level = 13
    
    return render_template(
        "index.html", 
        sandwiches=all_sandwiches,
        center_lat=center_lat,
        center_lon=center_lon,
        search_query=address,
        search_results=search_results,
        nearby_sandwiches=nearby_sandwiches,
        zoom_level=zoom_level
    )

@app.route("/add", methods=["POST"])
def add_sandwich():
    """Handle adding a new sandwich price."""
    if request.method != "POST":
        return redirect(url_for("home"))
    
    try:
        # Get form data
        name = request.form.get("name", "").strip()
        address = request.form.get("address", "").strip()
        price = request.form.get("price", "")
        
        # Validate inputs
        if not name or not address or not price:
            flash("All fields are required", "error")
            return redirect(url_for("home"))
        
        try:
            price = float(price)
        except ValueError:
            flash("Price must be a valid number", "error")
            return redirect(url_for("home"))
        
        # If address doesn't already include New York, append it
        if "new york" not in address.lower() and "ny" not in address.lower():
            address += ", New York, NY"
            
        # Geocode the address
        geocode_result = geocode_with_nominatim(address)
        
        if not geocode_result:
            flash("Could not find coordinates for this address. Please try a more specific address.", "error")
            return redirect(url_for("home"))
            
        # Create new entry
        new_sandwich = {
            "name": name,
            "address": address,
            "lat": geocode_result["lat"],
            "lon": geocode_result["lon"],
            "price": price,
            "last_updated": datetime.now()
        }
        
        # Check if we already have a sandwich at this location
        existing = collection.find_one({
            "lat": {"$gt": new_sandwich["lat"] - 0.0001, "$lt": new_sandwich["lat"] + 0.0001},
            "lon": {"$gt": new_sandwich["lon"] - 0.0001, "$lt": new_sandwich["lon"] + 0.0001},
        })
        
        if existing:
            flash(f"There is already a sandwich entry for {existing['name']} at this location.", "error")
            return redirect(url_for("home"))
        
        # Insert into database
        collection.insert_one(new_sandwich)
        
        # Success message
        flash("Sandwich price added successfully!", "success")
        
        # Redirect to the new location
        return redirect(url_for("search", address=address))
        
    except Exception as e:
        logger.error(f"Error adding sandwich: {str(e)}")
        flash(f"Error: {str(e)}", "error")
    
    return redirect(url_for("home"))

@app.route("/api/geocode", methods=["GET"])
def geocode_address():
    """Server-side geocoding endpoint with multiple providers."""
    address = request.args.get('address', '')
    
    if not address:
        return jsonify({"error": "Address parameter is required"}), 400
    
    # If address doesn't already include New York, append it
    if "new york" not in address.lower() and "ny" not in address.lower():
        address += ", New York, NY"
    
    logger.info(f"Geocoding address: {address}")
    
    # Try our database first (fastest)
    try:
        result = geocode_with_local_database(address)
        if result:
            logger.info(f"Found address in local database: {result}")
            return jsonify(result)
    except Exception as e:
        logger.error(f"Error with local database geocoding: {e}")
    
    # Try Nominatim
    try:
        result = geocode_with_nominatim(address)
        if result:
            logger.info(f"Found address with Nominatim: {result}")
            return jsonify(result)
    except Exception as e:
        logger.error(f"Error with Nominatim geocoding: {e}")
    
    # If we get here, all providers failed
    return jsonify({"error": "Address not found with any provider"}), 404

@app.route("/api/sandwiches/nearby", methods=["GET"])
def get_nearby_sandwiches():
    """API endpoint to get sandwich data near a location."""
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        radius = float(request.args.get('radius', 1))  # km
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid coordinates"}), 400
    
    results = find_nearby_sandwiches(lat, lon, radius)
    return jsonify(results)

@app.route("/api/sandwiches", methods=["GET"])
def get_sandwiches():
    """API endpoint to get all sandwich data."""
    max_price = request.args.get('max_price', None)
    min_price = request.args.get('min_price', None)
    
    query = {}
    if max_price:
        query["price"] = {"$lte": float(max_price)}
    if min_price:
        if "price" in query:
            query["price"]["$gte"] = float(min_price)
        else:
            query["price"] = {"$gte": float(min_price)}
    
    results = list(collection.find(query, {"_id": 0}))
    return jsonify(results)

@app.route("/api/sandwiches", methods=["POST"])
def api_add_sandwich():
    """API endpoint to add a new sandwich location."""
    data = request.json
    
    required_fields = ["name", "address", "lat", "lon", "price"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    data["last_updated"] = datetime.now()
    
    collection.insert_one(data)
    return jsonify({"success": True}), 201

if __name__ == "__main__":
    preload_sandwiches()
    app.run(
        host="0.0.0.0", port=5003, debug=True, use_reloader=False, use_debugger=False
    )
