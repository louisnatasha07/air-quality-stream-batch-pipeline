import pandas as pd

openmeteo_df = pd.read_csv(
    "data/processed/openmeteo_clean.csv"
)

cams_df = pd.read_csv(
    "data/processed/cams_clean.csv"
)

openmeteo_df["time"] = pd.to_datetime(openmeteo_df["time"])
cams_df["time"] = pd.to_datetime(cams_df["time"])

openmeteo_df["time_6h"] = (
    openmeteo_df["time"].dt.floor("6h")
)

cams_df["time_6h"] = cams_df["time"]

merged_df = pd.merge(
    openmeteo_df,
    cams_df.drop(columns=["time"]),
    on=["city", "time_6h"],
    how="inner"
)

merged_df = merged_df.drop(columns=["time_6h"])

merged_df.to_csv(
    "data/processed/final_multi_city_air_quality.csv",
    index=False
)

print("Multi-city merge completed.")
print(merged_df.shape)