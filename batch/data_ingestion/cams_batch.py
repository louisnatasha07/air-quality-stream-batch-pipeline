from calendar import monthrange
from pathlib import Path
import cdsapi

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

OUTPUT_DIR = Path("data/external/cams")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

client = cdsapi.Client(
    url="https://ads.atmosphere.copernicus.eu/api",
    key="648f0c61-e942-43d7-8386-b9834660a9e4"
)

YEAR = 2025

for city in CITIES:

    city_name = city["city"].lower().replace(" ", "_")

    lat = city["latitude"]
    lon = city["longitude"]

    north = lat + 1
    south = lat - 1
    west = lon - 1
    east = lon + 1

    for month in range(1, 13):

        start_date = f"{YEAR}-{month:02d}-01"

        end_day = monthrange(YEAR, month)[1]
        end_date = f"{YEAR}-{month:02d}-{end_day}"

        output_file = (
            OUTPUT_DIR /
            f"cams_{city_name}_{YEAR}_{month:02d}.nc"
        )

        if output_file.exists():
            print(f"Skipping existing file: {output_file}")
            continue

        print(
            f"Downloading CAMS for "
            f"{city['city']} "
            f"{start_date} -> {end_date}"
        )

        client.retrieve(
            "cams-global-reanalysis-eac4",
            {
                "variable": [
                    "particulate_matter_2.5um",
                    "particulate_matter_10um",
                ],

                "date": f"{start_date}/{end_date}",

                "time": [
                    "00:00",
                    "06:00",
                    "12:00",
                    "18:00",
                ],

                "data_format": "netcdf",

                "area": [
                    north,
                    west,
                    south,
                    east
                ],
            },

            str(output_file)
        )

print("All CAMS downloads completed.")