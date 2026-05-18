from calendar import monthrange
from pathlib import Path
import cdsapi

CITIES = [
    {"city": "Delhi", "latitude": 28.6139, "longitude": 77.2090},
    {"city": "Bangkok", "latitude": 13.7563, "longitude": 100.5018},
    {"city": "Jakarta", "latitude": -6.2088, "longitude": 106.8456},
    {"city": "Beijing", "latitude": 39.9042, "longitude": 116.4074},
    {"city": "Los Angeles", "latitude": 34.0522, "longitude": -118.2437},
]

MONTHS = [
    ("2024", "09"),
    ("2024", "10"),
    ("2024", "11"),
    ("2024", "12"),
    ("2025", "01"),
    ("2025", "02"),
    ("2025", "03"),
    ("2025", "04"),
    ("2025", "05"),
    ("2025", "06"),
    ("2025", "07"),
    ("2025", "08"),
]

OUTPUT_DIR = Path("data/external/cams")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

client = cdsapi.Client(
    url="https://ads.atmosphere.copernicus.eu/api",
    key="API_KEY_KAMU"
)

for city in CITIES:

    city_name = city["city"].lower().replace(" ", "_")

    lat = city["latitude"]
    lon = city["longitude"]

    north = lat + 0.75
    south = lat - 0.75
    west = lon - 0.75
    east = lon + 0.75

    for year, month in MONTHS:

        start_date = f"{year}-{month}-01"

        end_day = monthrange(int(year), int(month))[1]

        end_date = f"{year}-{month}-{end_day}"

        output_file = (
            OUTPUT_DIR /
            f"cams_{city_name}_{year}_{month}.nc"
        )

        if output_file.exists():
            print(f"Skipping existing file: {output_file}")
            continue

        print(
            f"Downloading CAMS for "
            f"{city['city']} "
            f"{start_date} -> {end_date}"
        )

        try:

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

            print(f"Downloaded: {output_file}")

        except Exception as e:

            print(
                f"Failed download "
                f"{city['city']} "
                f"{start_date}"
            )

            print(e)

            continue

print("All CAMS downloads completed.")
