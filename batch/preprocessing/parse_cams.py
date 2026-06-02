from pathlib import Path
import xarray as xr
import pandas as pd
import logging

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename="logs/pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("CAMS parsing started")

INPUT_DIR = Path("data/external/cams")

ALLOWED_CITIES = {
    "Jakarta",
    "Surakarta",
    "Kuala Lumpur",
    "Singapore",
}

all_data = []

for file_path in INPUT_DIR.glob("*.nc"):

    try:

        message = f"Parsing {file_path.name}"
        print(message)
        logging.info(message)

        parts = file_path.stem.split("_")

        city = "_".join(parts[1:-2]).replace("_", " ").title()
        
        if city not in ALLOWED_CITIES:
            message = f"Skipping non-target city file: {file_path.name}"
            print(message)
            logging.info(message)
            continue

        ds = xr.open_dataset(file_path)

        df = ds.to_dataframe().reset_index()

        if "valid_time" in df.columns:
            df = df.rename(columns={"valid_time": "time"})

        df["city"] = city

        all_data.append(df)

        logging.info(
            f"{file_path.name} parsed successfully"
        )

    except Exception as e:

        logging.error(
            f"Failed parsing {file_path.name}"
        )

        logging.exception(e)

        continue

final_df = pd.concat(all_data, ignore_index=True)

OUTPUT_FILE = Path("data/raw/cams_all_cities.csv")
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

final_df.to_csv(
    OUTPUT_FILE,
    index=False
)

logging.info(
    f"CAMS parsing completed with shape {final_df.shape}"
)

logging.info(
    f"Saved parsed data to {OUTPUT_FILE}"
)

print("CAMS parsing completed.")
print(final_df.shape)