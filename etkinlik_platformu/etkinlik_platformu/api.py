import requests
from config import MAPBOX_ACCESS_TOKEN

def get_coordinates(address):
    """Adresin enlem ve boylam bilgilerini almak için Mapbox Geocoding API kullanılır."""
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json"
    params = {
        "access_token": MAPBOX_ACCESS_TOKEN,
        "limit": 1
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["features"]:
            coordinates = data["features"][0]["geometry"]["coordinates"]
            return coordinates[1], coordinates[0]  # Enlem, Boylam olarak döner
    return None

def get_route(start, end, travel_mode):
    """Mapbox Directions API ile rota almak için fonksiyon."""
    url = f"https://api.mapbox.com/directions/v5/mapbox/{travel_mode}/{start[1]},{start[0]};{end[1]},{end[0]}"
    
    params = {
        "access_token": MAPBOX_ACCESS_TOKEN,
        "geometries": "geojson"
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        route_data = response.json()
        print(f"Route data for {travel_mode}:", route_data)  # Debug: API yanıtını logla
        return route_data  # API yanıtını döndür
    else:
        print(f"Error fetching route for {travel_mode}: {response.status_code}")
        return None  # Hata durumunda None döndür

