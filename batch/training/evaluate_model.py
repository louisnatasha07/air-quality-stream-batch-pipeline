import pandas as pd
import joblib

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from batch.training.model_config import DATASET_FILE, MODEL_FILE, FEATURES, TARGET, TIME_COL

df = pd.read_csv(DATASET_FILE)
df = df.dropna()
df[TIME_COL] = pd.to_datetime(df[TIME_COL])
df = df.sort_values(["city", TIME_COL])

df["row_number"] = df.groupby("city").cumcount()
df["total_rows"] = df.groupby("city")["row_number"].transform("max") + 1

test_df = df[df["row_number"] >= df["total_rows"] * 0.8]

X_test = test_df[FEATURES]
y_test = test_df[TARGET]

model = joblib.load(MODEL_FILE)

predictions = model.predict(X_test)

mae = mean_absolute_error(y_test, predictions)
mse = mean_squared_error(y_test, predictions)
rmse = mse ** 0.5
r2 = r2_score(y_test, predictions)

print("Model Evaluation on Time-Based Holdout")
print("Test rows:", len(test_df))
print("MAE:", mae)
print("MSE:", mse)
print("RMSE:", rmse)
print("R2 Score:", r2)