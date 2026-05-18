import pandas as pd

df = pd.read_csv("data/raw/cams_all_cities.csv")

if "valid_time" in df.columns:
    df = df.rename(columns={"valid_time": "time"})

df["time"] = pd.to_datetime(df["time"])

numeric_cols = df.select_dtypes(include="number").columns.tolist()

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

cams_clean.to_csv(
    "data/processed/cams_clean.csv",
    index=False
)

print("CAMS cleaning completed.")
print(cams_clean.shape)