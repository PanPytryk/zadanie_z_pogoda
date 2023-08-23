import json

from typing import Any
import requests
from requests import Response
from geopy.geocoders import Nominatim
from geopy.location import Location

from datetime import datetime, timedelta


API_URL = "https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}" \
          "&hourly=rain&daily=rain_sum&timezone=Europe%2FLondon&start_date={searched_date}&end_date={searched_date}"



def retrieve_data_from_api(searched_date: str, latitude: float, longitude: float):
    return requests.get(
        API_URL.format(
            latitude=latitude,
            longitude=longitude,
            searched_date=searched_date
        )
    )


def get_error_reason(response_text: str) -> str:        
    reason = json.loads(response_text)
    return reason['reason']



def response_status_code_handler(resposne: Response) -> bool:
    status_code = resposne.status_code
    if status_code == 200:
        return True
    else:
        print("status code: ", resposne.status_code)
        print("reason: ", get_error_reason(resposne.text))
        return False


def find_coordinates_for_city(city: str) -> tuple[float, float]:
    geolocator = Nominatim(user_agent="MyApp")
    location: Location = geolocator.geocode(city)
    return location.latitude, location.longitude


def date_parser() -> str | None:
    date: str = input("date 'YYYY-mm-dd': ")
    if not date:
        new_date: datetime = datetime.today() + timedelta(days=1)
        return new_date.strftime("%Y-%m-%d")
    elif len(date) == 10:
        try:
            new_date = datetime.strptime(date, "%Y-%m-%d")
            return new_date.strftime("%Y-%m-%d")

        except Exception as e:
            print("Błędny format daty: ", e)
            date_parser()
    else:
        print("Błędny format daty: Nie poprawna długość")
        date_parser()
    

def check_raining_sum(raining_sum: float) -> str:
    if raining_sum > 0.0:
        return "Bedzie padać"
    elif raining_sum == 0.0:
        return "Nie bedzie padać"
    else:
        return "Nie wiem"


def connect_with_api() -> Response:
    resposne: Response = retrieve_data_from_api(date, *coordinates)
    resposne_status_proces = True
    attempt = 0
    while resposne_status_proces:
        attempt += 1

        resposne = retrieve_data_from_api(date, *coordinates)
        if response_status_code_handler(resposne):
            resposne_status_proces = False

        if attempt == 5:
            resposne_status_proces = False
            print("Nie udało się połączyć z API")

    return resposne

def get_json_file_data() -> dict[str, Any]:
    with open(f"opady.json", mode="r") as f:
        data = f.read()
    return json.loads(data) if data else {}

def save_data_in_json_file(data: dict[str, Any]):
    with open(f"opady.json", "w+",  encoding="utf8") as f:
        json.dump(data, f, indent=4)


def extract_raining_sum(api_wetaher_data: dict[str, Any]) -> float:
    daily_location_weather_data: dict[str, Any] | None = api_wetaher_data.get("daily")
    if daily_location_weather_data is None:
        return -1.0
    else:
        raining_sum: list[float] | None = daily_location_weather_data.get("rain_sum")
        if raining_sum is None:
            return -1.0 
        elif len(raining_sum):
            return raining_sum[0]
        else:
            return -1.0


if __name__ == "__main__":
    open(f"opady.json", mode="a+")

    location_name: str = input("location name: ")

    coordinates = find_coordinates_for_city(location_name)
    date: str = date_parser()

    rainfall_data: dict[str, dict[str, float]] = get_json_file_data()

    location_rainfall_data: dict[str, float] = rainfall_data.setdefault(location_name, {})
    print()

    if location_rainfall_data.get(date) is None:
        resposne: Response = connect_with_api()

        api_wetaher_data = json.loads(resposne.text)
        raining_sum = extract_raining_sum(json.loads(resposne.text))

        print("Pobrano dane z api")
        location_rainfall_data[date] = raining_sum
        save_data_in_json_file(rainfall_data)

    else:
        raining_sum = location_rainfall_data.get(date)
        print("Pobrano dane z pliku")
    print(f"{location_name}, {date}, {check_raining_sum(raining_sum)}")

