import requests


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

HEADERS = {
    "User-Agent": "FuelRouteAssessment/1.0"
}


def geocode_location(location):
    params = {
        "q": f"{location}, USA",
        "format": "jsonv2",
        "limit": 1,
    }

    response = requests.get(
        NOMINATIM_URL,
        params=params,
        headers=HEADERS,
        timeout=10,
    )

    response.raise_for_status()

    results = response.json()

    if not results:
        raise ValueError(
            f"Location could not be found: {location}"
        )

    result = results[0]

    return {
        "latitude": float(result["lat"]),
        "longitude": float(result["lon"]),
        "display_name": result["display_name"],
    }