from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .geocoding_service import geocode_location
from .routing_service import get_route
from .fuel_service import (
    find_nearby_stations,
    add_destination,
    optimize_fuel_stops,
)


@api_view(["POST"])
def route_api(request):

    start = request.data.get("start")
    finish = request.data.get("finish")

    if not start or not finish:
        return Response(
            {
                "error": "Both 'start' and 'finish' are required."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # 1. Geocode start and finish
        start_location = geocode_location(start)
        finish_location = geocode_location(finish)
        if "United States" not in start_location["display_name"]:
            return Response(
                {"error": "Start location must be in the USA."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "United States" not in finish_location["display_name"]:
            return Response(
                {"error": "Finish location must be in the USA."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Get driving route
        route = get_route(
            start_location["longitude"],
            start_location["latitude"],
            finish_location["longitude"],
            finish_location["latitude"],
        )

        # 3. Find fuel stations near the route
        stations = find_nearby_stations(
            route["geometry"],
            max_distance_miles=10,
        )

        # 4. Add destination as final route point
        stations_with_destination = add_destination(
            stations,
            route["distance_miles"],
        )

        # 5. Calculate fuel plan
        fuel_plan = optimize_fuel_stops(
            stations_with_destination,
            route["distance_miles"],
        )

        # 6. Return complete response
        return Response(
            {
                "start": start_location,
                "finish": finish_location,
                "route": route,
                "fuel_stations": stations,
                "fuel_plan": fuel_plan,
            }
        )

    except ValueError as error:
        return Response(
            {
                "error": str(error)
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as error:
        return Response(
            {
                "error": str(error)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

