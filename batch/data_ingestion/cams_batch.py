from calendar import monthrange
from pathlib import Path
import os
import logging

import cdsapi
from dotenv import load_dotenv

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename="logs/pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("CAMS batch ingestion started")

load_dotenv()

CITIES = [
    {
        "city": "Jakarta",
        "latitude": -6.2088,
        "longitude": 106.8456
    },
    {
        "city": "Singapore",
        "latitude": 1.3521,
        "longitude": 103.8198
    },
    {
        "city": "Kuala Lumpur",
        "latitude": 3.1390,
        "longitude": 101.6869
    },
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

CAMS_API_URL = os.getenv(
    "CAMS_API_URL",
    "https://ads.atmosphere.copernicus.eu/api"
)

CAMS_API_KEY = os.getenv("CAMS_API_KEY")

if not CAMS_API_KEY:
    logging.error("CAMS_API_KEY belum ada di .env")
    raise ValueError("CAMS_API_KEY belum ada di .env")

client = cdsapi.Client(
    url=CAMS_API_URL,
    key=CAMS_API_KEY
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

        output_file = OUTPUT_DIR / f"cams_{city_name}_{year}_{month}.nc"

        if output_file.exists():
            message = f"Skipping existing file: {output_file}"
            print(message)
            logging.info(message)
            continue

        message = f"Downloading CAMS for {city['city']} {start_date} -> {end_date}"
        print(message)
        logging.info(message)

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
                        east,
                    ],
                },
                str(output_file),
            )

            message = f"Downloaded: {output_file}"
            print(message)
            logging.info(message)

        except Exception as e:
            message = f"Failed download {city['city']} {start_date}"
            print(message)
            print(e)

            logging.error(message)
            logging.exception(e)

            continue

logging.info("All CAMS downloads completed")
print("All CAMS downloads completed.")