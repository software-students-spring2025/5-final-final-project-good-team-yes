from flask import Flask, render_template, request
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import os
import requests
app = Flask(__name__)

client = MongoClient("mongodb://mongodb:27017")
db = client["deli_db"]
collection = db["deli_prices"]

if collection.count_documents({}) == 0:
    collection.insert_many([
        {
            "name": "Joe's Deli",
            "lat": 40.728,
            "lon": -73.991,
            "base_price": 3.00,
            "bagel_types": ["plain", "everything", "sesame"],
            "topping_prices": {
                "cream_cheese": 0.50,
                "onion": 0.25,
                "bacon": 1.00,
                "egg": 0.75,
                "cheese": 0.50,
                "lox_salmon": 2.00
            }
        },
        {
            "name": "East Side Bites",
            "lat": 40.732,
            "lon": -73.987,
            "base_price": 3.50,
            "bagel_types": ["plain", "wholewheat", "everything"],
            "topping_prices": {
                "cream_cheese": 0.75,
                "onion": 0.30,
                "bacon": 1.25,
                "egg": 0.75,
                "cheese": 0.65,
                "lox_salmon": 2.50
            }
        }
    ])

@app.route("/")
def home():
    """Render the homepage."""
    return render_template("home.html")

@app.route("/price-search")
def price_search():
    return render_template("price-search.html")

@app.route("/find-deli", methods=["POST"])
def find_deli():
    """Return map based on user given price"""
    target_price = float(request.form["price"])
    results = collection.find({"price": {"$lte": target_price}})

    matching_delis = [
        {"name": d["name"], "lat": d["lat"], "lon": d["lon"], "price": d["price"]}
        for d in results
    ]
    return render_template("map.html", delis=matching_delis)

@app.route("/custom-bagel")
def custom_bagel():
    return render_template("custom-bagel.html")

@app.route("/build-bagel", methods=["POST"])
def build_bagel():
    bagel_type = request.form["bagel_type"]
    toppings = request.form.getlist("toppings")

    matching_delis = []

    for deli in collection.find():
        if bagel_type not in deli.get("bagel_types", []):
            continue

        price = deli.get("base_price", deli.get("price", 0)) 
        topping_prices = deli.get("topping_prices", {})

        for topping in toppings:
            price += topping_prices.get(topping, 0)

        matching_delis.append({
            "name": deli["name"],
            "lat": deli["lat"],
            "lon": deli["lon"],
            "price": round(price, 2)
        })

    # Sort by total price
    matching_delis.sort(key=lambda d: d["price"])
    return render_template("mapbymybagel.html", delis=matching_delis, bagel=bagel_type, toppings=toppings)




if __name__ == "__main__":
    app.run(
        host="0.0.0.0", port=5003, debug=True, use_reloader=False, use_debugger=False
    )
