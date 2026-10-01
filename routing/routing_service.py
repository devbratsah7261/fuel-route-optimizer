import requests


OSRM_URL = "https://router.project-osrm.org"


def get_route(start_lon, start_lat, finish_lon, finish_lat):
    url = (
        f"{OSRM_URL}/route/v1/driving/"
        f"{start_lon},{start_lat};{finish_lon},{finish_lat}"
    )

    params = {
        "overview": "full",
        "geometries": "geojson",
    }

    response = requests.get(
        url,
        params=params,
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()

    if data["code"] != "Ok":
        raise ValueError("Route could not be found.")

    route = data["routes"][0]

    return {
        "distance_miles": route["distance"] / 1609.344,
        "duration_minutes": route["duration"] / 60,
        "geometry": route["geometry"],
    }