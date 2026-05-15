import pandas as pd

df = pd.read_csv("data/raw/cams_delhi.csv")

print("Kolom awal:")
print(df.columns.tolist())
print(df.head())

# Rename valid_time -> time
df = df.rename(columns={"valid_time": "time"})

# Convert time
df["time"] = pd.to_datetime(df["time"])

# Ambil numeric columns
numeric_cols = df.select_dtypes(include="number").columns.tolist()

# Remove coordinate columns
for col in ["latitude", "longitude"]:
    if col in numeric_cols:
        numeric_cols.remove(col)

# Group by time
cams_clean = df.groupby("time")[numeric_cols].mean().reset_index()

# Rename columns
rename_map = {
    "pm2p5": "cams_pm2_5",
    "pm10": "cams_pm10",
}

cams_clean = cams_clean.rename(columns=rename_map)

print("Kolom setelah cleaning:")
print(cams_clean.columns.tolist())
print(cams_clean.head())

# Save clean dataset
cams_clean.to_csv("data/processed/cams_delhi_clean.csv", index=False)

print("CAMS cleaned data saved successfully.")