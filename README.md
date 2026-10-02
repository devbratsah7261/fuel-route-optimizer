# Fuel Route Optimizer

A Django REST API that calculates driving routes between two locations in the USA and identifies fuel stations along the route for cost-effective fuel planning.

## Features

- Accepts start and finish locations in the USA.
- Geocodes locations using OpenStreetMap Nominatim.
- Calculates driving routes using OSRM.
- Returns route distance, duration, and GeoJSON route geometry.
- Finds fuel stations located near the calculated route.
- Uses the provided fuel-price CSV dataset.
- Optimizes fuel purchases based on fuel price and vehicle range.
- Assumes a maximum vehicle range of 500 miles.
- Assumes fuel efficiency of 10 miles per gallon (MPG).
- Calculates total fuel purchased and total fuel cost.

## Tech Stack

- Python
- Django
- Django REST Framework
- SQLite
- Requests
- OpenStreetMap Nominatim
- OSRM
- GeoJSON

## Project Structure

```text
fuel-route-optimizer/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── routing/
│   ├── management/
│   │   └── commands/
│   │       ├── import_fuel_data.py
│   │       └── geocode_fuel_stations.py
│   │
│   ├── fuel_service.py
│   ├── geocoding_service.py
│   ├── routing_service.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
│
├── data/
│   └── fuel-prices.csv
│
├── manage.py
├── requirements.txt
└── README.md