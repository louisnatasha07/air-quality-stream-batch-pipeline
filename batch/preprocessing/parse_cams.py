from pathlib import Path
import xarray as xr
import pandas as pd

INPUT_DIR = Path("data/external/cams")

all_data = []

for file_path in INPUT_DIR.glob("*.nc"):

    print(f"Parsing {file_path.name}...")

    parts = file_path.stem.split("_")

    city = "_".join(parts[1:-2]).replace("_", " ").title()

    ds = xr.open_dataset(file_path)

    df = ds.to_dataframe().reset_index()

    if "valid_time" in df.columns:
        df = df.rename(columns={"valid_time": "time"})

    df["city"] = city

    all_data.append(df)

final_df = pd.concat(all_data, ignore_index=True)

final_df.to_csv(
    "data/raw/cams_all_cities.csv",
    index=False
)

print("CAMS parsing completed.")
print(final_df.shape)