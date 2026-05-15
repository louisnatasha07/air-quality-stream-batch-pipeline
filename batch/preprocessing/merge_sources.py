import pandas as pd

# Load Open-Meteo dataset
openmeteo_df = pd.read_csv(
    "data/processed/feature_dataset.csv"
)

# Load CAMS dataset
cams_df = pd.read_csv(
    "data/processed/cams_delhi_clean.csv"
)

# Convert datetime
openmeteo_df["time"] = pd.to_datetime(openmeteo_df["time"])
cams_df["time"] = pd.to_datetime(cams_df["time"])

print("Open-Meteo shape:", openmeteo_df.shape)
print("CAMS shape:", cams_df.shape)

# Merge by time
merged_df = pd.merge(
    openmeteo_df,
    cams_df,
    on="time",
    how="inner"
)

print("Merged shape:", merged_df.shape)
print(merged_df.head())

# Save merged dataset
merged_df.to_csv(
    "data/processed/merged_air_quality.csv",
    index=False
)

print("Merged dataset saved successfully.")