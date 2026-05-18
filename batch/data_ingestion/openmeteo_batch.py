import requests
import pandas as pd

CITIES = [
    {
        "city": "Delhi",
        "latitude": 28.6139,
        "longitude": 77.2090
    },
    {
        "city": "Bangkok",
        "latitude": 13.7563,
        "longitude": 100.5018
    },
    {
        "city": "Jakarta",
        "latitude": -6.2088,
        "longitude": 106.8456
    },
    {
        "city": "Beijing",
        "latitude": 39.9042,
        "longitude": 116.4074
    },
    {
        "city": "Los Angeles",
        "latitude": 34.0522,
        "longitude": -118.2437
    }
]

START_DATE = "2024-09-01"
END_DATE = "2025-08-31"

all_data = []

for city in CITIES:

    print(f"Downloading data for {city['city']}...")

    url = (
        "https://air-quality-api.open-meteo.com/v1/air-quality?"
        f"latitude={city['latitude']}"
        f"&longitude={city['longitude']}"
        "&hourly=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone"
        f"&start_date={START_DATE}"
        f"&end_date={END_DATE}"
    )

    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame({
        "time": data["hourly"]["time"],
        "pm2_5": data["hourly"]["pm2_5"],
        "pm10": data["hourly"]["pm10"],
        "carbon_monoxide": data["hourly"]["carbon_monoxide"],
        "nitrogen_dioxide": data["hourly"]["nitrogen_dioxide"],
        "ozone": data["hourly"]["ozone"],
    })

    df["city"] = city["city"]
    df["latitude"] = city["latitude"]
    df["longitude"] = city["longitude"]

    all_data.append(df)

final_df = pd.concat(all_data, ignore_index=True)

final_df.to_csv(
    "data/raw/openmeteo_all_cities.csv",
    index=False
)

print("All Open-Meteo data saved successfully.")
print(final_df.head())
print(final_df.shape)