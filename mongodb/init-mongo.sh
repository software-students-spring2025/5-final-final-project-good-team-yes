#!/bin/bash
set -e

mongo <<EOF
use sandwich_db

db.createCollection("sandwich_prices")

db.sandwich_prices.insertMany([
  {
    "name": "Joe's Deli",
    "address": "123 Broadway, New York, NY",
    "lat": 40.728,
    "lon": -73.991,
    "price": 5.99,
    "last_updated": new Date()
  },
  {
    "name": "East Side Bites",
    "address": "456 Madison Ave, New York, NY",
    "lat": 40.732,
    "lon": -73.987,
    "price": 6.50,
    "last_updated": new Date()
  },
  {
    "name": "West Village Deli",
    "address": "789 Greenwich St, New York, NY",
    "lat": 40.735,
    "lon": -74.005,
    "price": 7.25,
    "last_updated": new Date()
  },
  {
    "name": "Midtown Sandwich Shop",
    "address": "555 5th Ave, New York, NY",
    "lat": 40.755,
    "lon": -73.978,
    "price": 8.75,
    "last_updated": new Date()
  },
  {
    "name": "Financial District Deli",
    "address": "11 Wall St, New York, NY",
    "lat": 40.707,
    "lon": -74.010,
    "price": 9.50,
    "last_updated": new Date()
  }
])

print("Database sandwich_db initialized with sample data")
EOF 