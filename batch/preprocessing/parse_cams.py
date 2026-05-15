import xarray as xr
import pandas as pd

# Load NetCDF file
ds = xr.open_dataset("data/external/cams_delhi.nc")

print(ds)

# Convert to dataframe
df = ds.to_dataframe().reset_index()

print(df.head())

# Save raw CSV
df.to_csv("data/raw/cams_delhi.csv", index=False)

print("CAMS data converted to CSV successfully.")