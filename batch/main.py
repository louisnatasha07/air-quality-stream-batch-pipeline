import pandas as pd
from database.db_connection import engine

df = pd.read_csv("data/processed/merged_air_quality.csv")

print("Jumlah data:", len(df))

df.to_sql(
    "merged_air_quality_data",
    engine,
    if_exists="replace",
    index=False
)

print("Merged dataset inserted into PostgreSQL successfully.")