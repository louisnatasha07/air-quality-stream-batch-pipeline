import pandas as pd

df = pd.read_csv("data/raw/openmeteo_delhi.csv")

# Convert time column
df["time"] = pd.to_datetime(df["time"])

# Remove duplicates
df = df.drop_duplicates()

# Sort by time
df = df.sort_values("time")

print(df.info())
print(df.head())

# Save cleaned data
df.to_csv("data/processed/openmeteo_delhi_clean.csv", index=False)

print("Cleaned data saved.")