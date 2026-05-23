import pandas as pd
import logging
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename="logs/pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("CAMS cleaning started")

try:

    INPUT_FILE = "data/raw/cams_all_cities.csv"

    logging.info(
        f"Loading raw CAMS data from {INPUT_FILE}"
    )

    df = pd.read_csv(INPUT_FILE)

    if "valid_time" in df.columns:
        df = df.rename(columns={"valid_time": "time"})

    df["time"] = pd.to_datetime(df["time"])

    numeric_cols = (
        df.select_dtypes(include="number")
        .columns
        .tolist()
    )

    for col in ["latitude", "longitude"]:
        if col in numeric_cols:
            numeric_cols.remove(col)

    cams_clean = (
        df.groupby(["city", "time"])[numeric_cols]
        .mean()
        .reset_index()
    )

    cams_clean = cams_clean.rename(columns={
        "pm2p5": "cams_pm2_5",
        "pm10": "cams_pm10",
    })

    OUTPUT_FILE = "data/processed/cams_clean.csv"

    cams_clean.to_csv(
        OUTPUT_FILE,
        index=False
    )

    logging.info(
        f"CAMS cleaning completed with shape {cams_clean.shape}"
    )

    logging.info(
        f"Cleaned data saved to {OUTPUT_FILE}"
    )

    print("CAMS cleaning completed.")
    print(cams_clean.shape)

except Exception as e:

    logging.error("CAMS cleaning failed")

    logging.exception(e)

    raise