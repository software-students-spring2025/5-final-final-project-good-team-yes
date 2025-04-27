"""NYC Sandwich Price Tracker application.

This Flask application provides a platform for tracking sandwich prices across NYC,
allowing users to find affordable options in their area.
"""
import math
import logging
from datetime import datetime

import requests
import os
from flask import Flask, render_template, request, jsonify, url_for, redirect, flash
from pymongo import MongoClient

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = 'sandwich_tracker_secret_key'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLIENT = None
DB = None
COLLECTION = None
COLLECTION_HELPER = None  # Renamed from 'collection' to follow naming convention

# pylint: disable=too-many-return-statements
def init_db():
    """Initialize database connection and create initial data if needed.
    
    Connects to MongoDB and sets up the sandwich_db and sandwich_prices collection.
    Adds sample data if the collection is empty.
    """
    MONGO_URI = os.environ.get("MONGO_URI")
    MONGO_DB = os.environ.get("MONGO_DB")

    # Using function parameters and return values instead of globals
    client = MongoClient(MONGO_URI)
    database = client[MONGO_DB]
    collection = database["sandwich_prices"]

    # Still need to set the globals for existing code
    # pylint: disable=global-statement
    global CLIENT, DB, COLLECTION, COLLECTION_HELPER
    CLIENT = client
    DB = database
    COLLECTION = collection
    COLLECTION_HELPER = collection

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

try:
    init_db()
except ConnectionError as e:
    logger.error("Failed to connect to MongoDB: %s", str(e))
except Exception as e:  # pylint: disable=broad-except
    # Explicitly disable the warning since we want to catch any DB initialization errors
    logger.error("Database initialization error: %s", str(e))

def get_marker_color(price):
    """Get color code for price marker."""
    if price < 6.00:
        return "#4CAF50"  # green
    if price < 7.00:
        return "#2196F3"  # blue
    if price < 8.00:
        return "#FFC107"  # yellow
    return "#F44336"  # red

def geocode_address(address):
    """Simple geocoding using Nominatim API."""
    if "new york" not in address.lower() and "ny" not in address.lower():
        address += ", New York, NY"

    search_query = requests.utils.quote(address)

    url = f"https://nominatim.openstreetmap.org/search?q={search_query}&format=json"

    try:
        response = requests.get(
            url,
            headers={'User-Agent': 'NYC Sandwich Price Tracker (contact@example.com)'},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            if data:
                result = data[0]
                return {
                    "lat": float(result["lat"]),
                    "lon": float(result["lon"]),
                    "display_name": result["display_name"]
                }
    except requests.RequestException as e:
        logger.error("Geocoding error: %s", str(e))
    except (KeyError, ValueError) as e:
        logger.error("Error parsing geocoding response: %s", str(e))

    return None

def find_nearby_sandwiches(lat, lon, radius=1):
    """Find sandwiches near a specific location."""
    results = list(COLLECTION.find({
        "lat": {"$gt": lat - 0.01 * radius, "$lt": lat + 0.01 * radius},
        "lon": {"$gt": lon - 0.01 * radius, "$lt": lon + 0.01 * radius}
    }, {"_id": 0}))

    for result in results:
        distance = math.sqrt((result["lat"] - lat)**2 + (result["lon"] - lon)**2) * 111  # km
        result["distance"] = distance

    results.sort(key=lambda x: x["distance"])

    return results

def filter_sandwiches(sandwiches):
    """
    Filters sandwiches to ensure each location is only shown once, showing
    the most recently updated entry in case of conflict
    """
    unique_locations = {}
    for sandwich in sandwiches:
        key = (sandwich["lat"], sandwich["lon"])

        # Only replaces unique location if the current sandwich was more recently updated
        if (unique_locations.get(key) and 
        unique_locations[key]["last_updated"] > sandwich["last_updated"]):
            continue
        else:
            unique_locations[key] = sandwich
    
    return unique_locations.values()


@app.route("/")
def home():
    """Render the main application with all sandwich data."""
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    query = {}
    if min_price is not None:
        query["price"] = {"$gte": min_price}
    if max_price is not None:
        if "price" in query:
            query["price"]["$lte"] = max_price
        else:
            query["price"] = {"$lte": max_price}

    sandwiches = list(COLLECTION.find(query, {"_id": 0}))
    sandwiches = filter_sandwiches(sandwiches)


    if sandwiches:
        center_lat = sum(s["lat"] for s in sandwiches) / len(sandwiches)
        center_lon = sum(s["lon"] for s in sandwiches) / len(sandwiches)
    else:
        center_lat = 40.755
        center_lon = -73.978

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
    address = ""

    if request.method == "POST":
        address = request.form.get("address", "").strip()
    else:
        address = request.args.get("address", "").strip()

    if address:
        logger.info("Search request for address: '%s'", address)

        geocode_result = geocode_address(address)
        if geocode_result:
            search_results = geocode_result
            nearby_sandwiches = find_nearby_sandwiches(geocode_result["lat"], geocode_result["lon"])
            logger.info("Found %d sandwiches near location", len(nearby_sandwiches))
        else:
            flash("Could not find this address. Please try a more specific NYC address.", "error")

    all_sandwiches = list(COLLECTION.find({}, {"_id": 0}))

    all_sandwiches = filter_sandwiches(all_sandwiches)

    for sandwich in all_sandwiches:
        sandwich["color"] = get_marker_color(sandwich["price"])

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

def validate_sandwich_input(name, address, price_str):
    """Validate sandwich input and return price as float or error message."""
    if not all([name, address, price_str]):
        return None, "All fields are required"

    try:
        price = float(price_str)
        if price <= 0:
            return None, "Price must be greater than zero"
        return price, None
    except ValueError:
        return None, "Price must be a valid number"

# pylint: disable=too-many-return-statements
@app.route("/add", methods=["POST"])
def add_sandwich():
    """Handle adding a new sandwich price."""
    if request.method != "POST":
        return redirect(url_for("home"))

    try:
        name = request.form.get("name", "").strip()
        address = request.form.get("address", "").strip()
        price_str = request.form.get("price", "").strip()

        price, error = validate_sandwich_input(name, address, price_str)
        if error:
            flash(error, "error")
            return redirect(url_for("home"))

        geocode_result = geocode_address(address)
        if not geocode_result:
            msg = "Could not find this address on the map. Please try a more specific NYC address."
            flash(msg, "error")
            return redirect(url_for("home"))

        sandwich = {
            "name": name,
            "address": address,
            "lat": geocode_result["lat"],
            "lon": geocode_result["lon"],
            "price": price,
            "last_updated": datetime.now()
        }

        COLLECTION.insert_one(sandwich)

        flash(f"Added {name} with price ${price:.2f}", "success")
        logger.info("Added new sandwich shop: %s at %s", name, address)

        return redirect(url_for("home"))

    except ValueError as e:
        logger.error("Value error adding sandwich: %s", str(e))
        flash("Invalid data provided. Please check your inputs.", "error")
        return redirect(url_for("home"))
    except requests.RequestException as e:
        logger.error("Request error adding sandwich: %s", str(e))
        flash("Error contacting geocoding service. Please try again.", "error")
        return redirect(url_for("home"))
    except Exception as e:  # pylint: disable=broad-except
        # Explicitly disable warning for this catch-all exception handler
        logger.error("Error adding sandwich: %s", str(e))
        flash("An error occurred. Please try again.", "error")
        return redirect(url_for("home"))

@app.route("/api/geocode", methods=["GET"])
def api_geocode():
    """API endpoint for geocoding an address."""
    address = request.args.get("address", "")
    if not address:
        return jsonify({"error": "Address parameter is required"}), 400

    logger.info("API geocode request for: %s", address)
    result = geocode_address(address)

    if not result:
        return jsonify({"error": "Address not found"}), 404

    return jsonify(result)

@app.route("/api/sandwiches/nearby", methods=["GET"])
def get_nearby_sandwiches():
    """API endpoint to get nearby sandwich shops."""
    try:
        if "lat" not in request.args or "lon" not in request.args:
            return jsonify({"error": "Missing required parameters: lat and lon"}), 400

        lat = float(request.args.get("lat", 0))
        lon = float(request.args.get("lon", 0))
        radius = float(request.args.get("radius", 1))
    except ValueError:
        return jsonify({"error": "Invalid coordinates"}), 400

    results = find_nearby_sandwiches(lat, lon, radius)
    return jsonify(results)

def build_sandwich_query():
    """Build query for sandwich filtering from request arguments."""
    query = {}
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")

    if min_price:
        try:
            query["price"] = {"$gte": float(min_price)}
        except ValueError:
            return None, "Invalid min price"

    if max_price:
        try:
            if "price" in query:
                query["price"]["$lte"] = float(max_price)
            else:
                query["price"] = {"$lte": float(max_price)}
        except ValueError:
            return None, "Invalid max price"

    return query, None

@app.route("/api/sandwiches", methods=["GET"])
def get_sandwiches():
    """API endpoint to get all sandwich shops."""
    query, error = build_sandwich_query()
    if error:
        return jsonify({"error": error}), 400

    sandwiches = list(COLLECTION.find(query, {"_id": 0}))
    return jsonify(sandwiches)

# pylint: disable=too-many-return-statements
@app.route("/api/sandwiches", methods=["POST"])
def api_add_sandwich():
    """API endpoint to add a new sandwich shop."""
    data = request.get_json()

    # Validate input data
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required_fields = ["name", "address", "price"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    try:
        price = float(data["price"])
        if price <= 0:
            return jsonify({"error": "Price must be greater than zero"}), 400
    except ValueError:
        return jsonify({"error": "Price must be a valid number"}), 400

    # Process geocoding and database insertion
    try:
        # Get coordinates
        if "lat" in data and "lon" in data:
            lat = float(data["lat"])
            lon = float(data["lon"])
        else:
            geocode_result = geocode_address(data["address"])
            if not geocode_result:
                return jsonify({"error": "Could not geocode the address"}), 400
            lat = geocode_result["lat"]
            lon = geocode_result["lon"]

        # Create and insert sandwich record
        sandwich = {
            "name": data["name"],
            "address": data["address"],
            "lat": lat,
            "lon": lon,
            "price": price,
            "last_updated": datetime.now()
        }

        result = COLLECTION.insert_one(sandwich)

        if not result.inserted_id:
            return jsonify({"error": "Failed to add sandwich"}), 500

        logger.info("API added new sandwich shop: %s", data["name"])
        return jsonify({"success": True}), 201

    except ValueError as e:
        return jsonify({"error": f"Invalid coordinate format: {str(e)}"}), 400
    except requests.RequestException as e:
        return jsonify({"error": f"Geocoding service error: {str(e)}"}), 503

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5003)
