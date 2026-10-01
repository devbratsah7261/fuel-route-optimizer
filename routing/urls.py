from django.urls import path

from .views import route_api


urlpatterns = [
    path("route/", route_api, name="route-api"),
]