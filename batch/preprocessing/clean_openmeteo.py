import pandas as pd

df = pd.read_csv("data/raw/openmeteo_all_cities.csv")

df["time"] = pd.to_datetime(df["time"])

df = df.drop_duplicates()

pollutant_cols = [
    "pm2_5",
    "pm10",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "ozone",
]

df[pollutant_cols] = (
    df.groupby("city")[pollutant_cols]
    .transform(lambda x: x.interpolate())
)

df["hour"] = df["time"].dt.hour
df["day"] = df["time"].dt.day
df["month"] = df["time"].dt.month
df["day_of_week"] = df["time"].dt.dayofweek

df["pm2_5_rolling_3h"] = (
    df.groupby("city")["pm2_5"]
    .transform(
        lambda x: x.rolling(3, min_periods=1).mean()
    )
)

df.to_csv(
    "data/processed/openmeteo_clean.csv",
    index=False
)

print("Open-Meteo cleaning completed.")
print(df.shape)