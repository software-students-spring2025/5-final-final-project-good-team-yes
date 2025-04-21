from flask import Flask, render_template, request
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import os
import requests
app = Flask(__name__)

# Mock deli dataset before setting up MongoDB
mock_deli_data = [
    {"name": "Joe's Deli", "lat": 40.728, "lon": -73.991, "price": 4.25},
    {"name": "East Side Bites", "lat": 40.732, "lon": -73.987, "price": 5.00},
    {"name": "Bagel Bros", "lat": 40.730, "lon": -73.995, "price": 3.75},
    {"name": "Westside Deli", "lat": 40.735, "lon": -73.982, "price": 4.75},
]

@app.route("/")
def home():
    """Render the homepage."""
    return render_template("home.html")

@app.route("/find-deli", methods=["POST"])
def find_deli():
    target_price = float(request.form["price"])
    matching_delis = [d for d in mock_deli_data if d["price"] <= target_price]
    if not matching_delis:
        matching_delis = [{"name": "No results found", "lat": 40.73, "lon": -73.99, "price": 0}]
    return render_template("map.html", delis=matching_delis)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0", port=5003, debug=True, use_reloader=False, use_debugger=False
    )
