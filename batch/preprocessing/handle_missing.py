import pandas as pd

df = pd.read_csv("data/processed/openmeteo_delhi_clean.csv")

# Check missing values
print(df.isnull().sum())

# Fill missing values
df = df.interpolate()

# Save processed data
df.to_csv("data/processed/openmeteo_delhi_final.csv", index=False)

print("Missing values handled.")