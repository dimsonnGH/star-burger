from .models import Location
import requests
from django.conf import settings

def fetch_coordinates(apikey, address):
    try:
        location = Location.objects.only("longitude", "latitude").get(address=address)
        return location.longitude, location.latitude
    except Location.DoesNotExist:
        pass

    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        lon = None
        lat = None
    else:
        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")

    Location.objects.create(address=address, longitude=lon, latitude=lat)
    return lon, lat


def get_address_coordinates(address, cache_of_coordinates):
    coordinates = cache_of_coordinates.get(address)
    cache_of_coordinates_modified = {**cache_of_coordinates}
    if not coordinates and address:
        coordinates = fetch_coordinates(settings.YANDEX_GEOCODER_KEY, address)
        cache_of_coordinates_modified[address] = coordinates
    return coordinates, cache_of_coordinates_modified
