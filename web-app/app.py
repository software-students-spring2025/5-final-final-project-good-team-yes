from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb://mongodb:27017")
db = client["sandwich_db"]
collection = db["sandwich_prices"]

# Add initial data if database is empty
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

@app.route("/")
def home():
    """Render the single-page application."""
    return render_template("index.html")

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
def add_sandwich():
    """API endpoint to add a new sandwich location."""
    data = request.json
    
    # Validate required fields
    required_fields = ["name", "address", "lat", "lon", "price"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Add timestamp
    data["last_updated"] = datetime.now()
    
    # Insert into database
    collection.insert_one(data)
    return jsonify({"success": True}), 201

if __name__ == "__main__":
    app.run(
        host="0.0.0.0", port=5003, debug=True, use_reloader=False, use_debugger=False
    )
