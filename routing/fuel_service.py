from math import radians, sin, cos, sqrt, atan2
from routing.models import FuelStation
# from routing.fuel_service import find_nearby_stations, add_destination


EARTH_RADIUS_MILES = 3958.8


def haversine_distance(
    latitude1,
    longitude1,
    latitude2,
    longitude2,
):
    """
    Calculate the distance between two coordinates in miles.
    """

    lat1 = radians(latitude1)
    lon1 = radians(longitude1)

    lat2 = radians(latitude2)
    lon2 = radians(longitude2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a),
    )

    return EARTH_RADIUS_MILES * c

from routing.models import FuelStation


def find_nearby_stations(
    route_geometry,
    max_distance_miles=5,
):
    """
    Find fuel stations within a given distance
    of the route and calculate their position
    along the route.
    """

    route_coordinates = route_geometry["coordinates"]

    nearby_stations = []

    stations = FuelStation.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
    )

    for station in stations:

        closest_index = None
        closest_distance = float("inf")

        # Find the closest point on the route
        for index, (
            route_longitude,
            route_latitude,
        ) in enumerate(route_coordinates):

            distance = haversine_distance(
                station.latitude,
                station.longitude,
                route_latitude,
                route_longitude,
            )

            if distance < closest_distance:
                closest_distance = distance
                closest_index = index

        # Ignore stations too far from the route
        if closest_distance > max_distance_miles:
            continue

        # Calculate distance from route start
        distance_along_route = 0

        for index in range(1, closest_index + 1):

            lon1, lat1 = route_coordinates[index - 1]
            lon2, lat2 = route_coordinates[index]

            distance_along_route += haversine_distance(
                lat1,
                lon1,
                lat2,
                lon2,
            )

        nearby_stations.append({
            "id": station.id,
            "name": station.truckstop_name,
            "city": station.city,
            "state": station.state,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "price": float(station.retail_price),
            "distance_from_route": round(
                closest_distance,
                2,
            ),
            "route_position_miles": round(
                distance_along_route,
                2,
            ),
        })

    # Sort stations by their position along the route
    nearby_stations.sort(
        key=lambda station: station["route_position_miles"]
    )

    return nearby_stations

def find_route_position(
    station_latitude,
    station_longitude,
    route_geometry,
):
    """
    Find the approximate position of a fuel station
    along the route, measured from the route start.
    """

    route_coordinates = route_geometry["coordinates"]

    closest_index = None
    closest_distance = float("inf")

    for index, (
        route_longitude,
        route_latitude,
    ) in enumerate(route_coordinates):

        distance = haversine_distance(
            station_latitude,
            station_longitude,
            route_latitude,
            route_longitude,
        )

        if distance < closest_distance:
            closest_distance = distance
            closest_index = index

    distance_along_route = 0

    for index in range(1, closest_index + 1):

        lon1, lat1 = route_coordinates[index - 1]
        lon2, lat2 = route_coordinates[index]

        distance_along_route += haversine_distance(
            lat1,
            lon1,
            lat2,
            lon2,
        )

    return distance_along_route


def add_destination(
    stations,
    route_distance_miles,
):
    stations = stations.copy()

    stations.append({
        "id": None,
        "name": "Destination",
        "city": None,
        "state": None,
        "latitude": None,
        "longitude": None,
        "price": None,
        "distance_from_route": 0,
        "route_position_miles": route_distance_miles,
    })

    stations.sort(
        key=lambda station: station["route_position_miles"]
    )

    return stations


def optimize_fuel_stops(
    stations,
    route_distance_miles,
    max_range_miles=500,
    mpg=10,
):
    tank_capacity = max_range_miles / mpg

    candidates = sorted(
        [
            station
            for station in stations
            if station.get("price") is not None
            and 0 < station["route_position_miles"] < route_distance_miles
        ],
        key=lambda station: station["route_position_miles"],
    )

    current_position = 0.0
    fuel_remaining = tank_capacity

    total_gallons = 0.0
    total_cost = 0.0
    fuel_stops = []

    for index, current_station in enumerate(candidates):

        # Distance from current position to this station
        distance = (
            current_station["route_position_miles"]
            - current_position
        )

        # If we cannot reach this station, route is impossible
        if distance > fuel_remaining * mpg:
            raise ValueError(
                f"No reachable fuel station from "
                f"{current_position:.2f} miles."
            )

        # Travel to current station
        fuel_remaining -= distance / mpg
        current_position = current_station["route_position_miles"]

        # Can we reach destination without buying fuel?
        distance_to_destination = (
            route_distance_miles - current_position
        )

        if distance_to_destination <= fuel_remaining * mpg:
            break

        # Look for a cheaper station ahead
        cheaper_station = None

        for next_station in candidates[index + 1:]:
            distance_to_next = (
                next_station["route_position_miles"]
                - current_position
            )

            if distance_to_next > max_range_miles:
                break

            if next_station["price"] < current_station["price"]:
                cheaper_station = next_station
                break

        # Decide target
        if cheaper_station is not None:

            target_position = cheaper_station["route_position_miles"]

            target_distance = (
                target_position - current_position
            )

            required_fuel = target_distance / mpg

            # Buy only enough to reach cheaper station
            fuel_to_buy = max(
                0,
                required_fuel - fuel_remaining
            )

        elif distance_to_destination <= max_range_miles:

            # Destination is reachable after refueling
            required_fuel = distance_to_destination / mpg

            # Buy only enough to reach destination
            fuel_to_buy = max(
                0,
                required_fuel - fuel_remaining
            )

        else:

            # No cheaper station nearby.
            # Fill the tank because current fuel is cheaper
            # than the fuel we may need later.
            fuel_to_buy = tank_capacity - fuel_remaining

        if fuel_to_buy > 0:

            fuel_to_buy = min(
                fuel_to_buy,
                tank_capacity - fuel_remaining
            )

            cost = (
                fuel_to_buy
                * float(current_station["price"])
            )

            fuel_remaining += fuel_to_buy
            total_gallons += fuel_to_buy
            total_cost += cost

            fuel_stops.append(
                {
                    "station": current_station["truckstop_name"],
                    "city": current_station["city"],
                    "state": current_station["state"],
                    "price_per_gallon": float(
                        current_station["price"]
                    ),
                    "gallons_purchased": round(
                        fuel_to_buy,
                        2
                    ),
                    "cost": round(
                        cost,
                        2
                    ),
                }
            )

    # Final destination check
    distance_to_destination = (
        route_distance_miles - current_position
    )

    if distance_to_destination > fuel_remaining * mpg:
        raise ValueError(
            "Route cannot be completed with the "
            "available fuel stations."
        )

    return {
        "total_gallons": round(total_gallons, 2),
        "total_cost": round(total_cost, 2),
        "fuel_stops": fuel_stops,
    }