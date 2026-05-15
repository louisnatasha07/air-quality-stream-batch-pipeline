import pandas as pd

df = pd.read_csv("data/processed/openmeteo_delhi_final.csv")

# Rolling average PM2.5
df["pm2_5_rolling"] = df["pm2_5"].rolling(window=3).mean()

# Hour feature
df["time"] = pd.to_datetime(df["time"])
df["hour"] = df["time"].dt.hour

# Day feature
df["day"] = df["time"].dt.day

# Save feature dataset
df.to_csv("data/processed/feature_dataset.csv", index=False)

print(df.head())
print("Feature engineering completed.")