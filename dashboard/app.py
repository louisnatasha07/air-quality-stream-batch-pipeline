import streamlit as st
import pandas as pd
import plotly.express as px
import joblib
import os

from sqlalchemy import create_engine
from dotenv import load_dotenv
from pathlib import Path

# =========================
# Load Environment Variables
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")

DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)

# =========================
# Page Config
# =========================
st.set_page_config(
    page_title="Air Quality Monitoring System",
    layout="wide"
)

# =========================
# Helper Functions
# =========================
def get_air_quality_status(pm25):
    if pm25 <= 15:
        return "Good", "🟢", "Air quality is safe for outdoor activities."
    elif pm25 <= 35:
        return "Moderate", "🟡", "Air quality is acceptable, but sensitive groups should be cautious."
    elif pm25 <= 75:
        return "Unhealthy", "🟠", "Air quality may affect sensitive groups and outdoor activity should be limited."
    else:
        return "Hazardous", "🔴", "High pollution level detected. Outdoor activity is not recommended."


def detect_anomaly(value, mean, std):
    threshold = mean + (2 * std)
    return value > threshold, threshold


def show_prediction_insight(latest_prediction, avg_prediction):
    if latest_prediction > avg_prediction:
        st.warning(
            "⚠️ Predicted PM2.5 is currently above the historical prediction average. "
            "This suggests a potential increase in pollution concentration compared with the normal pattern."
        )
    else:
        st.success(
            "✅ Predicted PM2.5 remains within or below the historical prediction average. "
            "This suggests relatively stable air quality conditions."
        )


def show_correlation_insight(correlation):
    if correlation > 0.7:
        st.info(
            f"📌 Strong relationship detected between Open-Meteo observations and Copernicus CAMS data "
            f"(correlation = {correlation:.2f}). "
            "This means local pollution observations are closely aligned with regional atmospheric patterns."
        )
    elif correlation > 0.4:
        st.info(
            f"📌 Moderate relationship detected between Open-Meteo observations and Copernicus CAMS data "
            f"(correlation = {correlation:.2f}). "
            "This suggests regional atmospheric conditions may partially influence local pollution levels."
        )
    else:
        st.warning(
            f"⚠️ Weak relationship detected between Open-Meteo observations and Copernicus CAMS data "
            f"(correlation = {correlation:.2f}). "
            "This suggests local pollution may be influenced more by local activities such as traffic or emissions."
        )


def show_distribution_insight(df):
    high_pollution_ratio = ((df["pm2_5"] > 75).sum() / len(df)) * 100
    moderate_ratio = (((df["pm2_5"] > 15) & (df["pm2_5"] <= 75)).sum() / len(df)) * 100

    if high_pollution_ratio > 30:
        st.error(
            f"⚠️ Around {high_pollution_ratio:.1f}% of observations fall into unhealthy or hazardous levels. "
            "This indicates persistent air quality risk in the observed period."
        )
    elif high_pollution_ratio > 10:
        st.warning(
            f"⚠️ Around {high_pollution_ratio:.1f}% of observations show unhealthy pollution levels. "
            "Air quality risk appears occasionally and should be monitored."
        )
    else:
        st.success(
            f"✅ Most observations remain below severe pollution levels. "
            f"Moderate observations account for about {moderate_ratio:.1f}% of the data."
        )


def show_daily_summary_insight(daily_summary):
    peak_day = daily_summary.loc[daily_summary["maximum_pm25"].idxmax()]
    cleanest_day = daily_summary.loc[daily_summary["average_pm25"].idxmin()]

    st.info(
        f"📌 The highest daily PM2.5 peak occurred on {peak_day['date']} "
        f"with {peak_day['maximum_pm25']:.2f} µg/m³. "
        f"The cleanest day on average was {cleanest_day['date']} "
        f"with {cleanest_day['average_pm25']:.2f} µg/m³."
    )


# =========================
# Load Data
# =========================
df = pd.read_sql("SELECT * FROM merged_air_quality_data", engine)
df["time"] = pd.to_datetime(df["time"])
df = df.sort_values("time")

# =========================
# Load ML Model & Prediction
# =========================
model = joblib.load("models/trained_model.pkl")

features = [
    "pm10",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "ozone",
    "hour",
    "day",
    "cams_pm2_5",
    "cams_pm10"
]

df = df.dropna(subset=features + ["pm2_5"])
df["predicted_pm2_5"] = model.predict(df[features])

latest = df.iloc[-1]
latest_pm25 = latest["pm2_5"]
latest_prediction = latest["predicted_pm2_5"]

status, icon, message = get_air_quality_status(latest_prediction)

pm25_mean = df["pm2_5"].mean()
pm25_std = df["pm2_5"].std()
is_anomaly, anomaly_threshold = detect_anomaly(latest_pm25, pm25_mean, pm25_std)

# =========================
# Header
# =========================
st.title("🌍 Air Quality Monitoring System")

st.caption(
    "Prediksi kualitas udara dan deteksi anomali menggunakan Big Data Pipeline "
    "berbasis data lingkungan dari Open-Meteo dan Copernicus CAMS."
)

# =========================
# Main Status
# =========================
st.subheader("Current Environmental Condition")

col1, col2, col3 = st.columns([1.3, 1, 1])

with col1:
    st.markdown(f"## {icon} {status}")
    st.write(message)

with col2:
    st.metric(
        "Predicted PM2.5",
        f"{latest_prediction:.2f} µg/m³"
    )

with col3:
    st.metric(
        "Observed PM2.5",
        f"{latest_pm25:.2f} µg/m³"
    )

# =========================
# Anomaly Detection
# =========================
st.subheader("Anomaly Detection")

if is_anomaly:
    st.error(
        f"⚠️ Environmental anomaly detected. "
        f"Observed PM2.5 reached {latest_pm25:.2f} µg/m³, "
        f"above the anomaly threshold of {anomaly_threshold:.2f} µg/m³. "
        "This may indicate unusual pollution activity."
    )
else:
    st.success(
        "✅ No significant anomaly detected in the latest observation. "
        "Pollution level is still within the expected historical pattern."
    )

# =========================
# Summary Cards
# =========================
st.subheader("Air Quality Summary")

avg_pm25 = df["pm2_5"].mean()
max_pm25 = df["pm2_5"].max()
avg_pred = df["predicted_pm2_5"].mean()
total_records = len(df)

c1, c2, c3, c4 = st.columns(4)

c1.metric("Average PM2.5", f"{avg_pm25:.2f}")
c2.metric("Highest PM2.5", f"{max_pm25:.2f}")
c3.metric("Average Prediction", f"{avg_pred:.2f}")
c4.metric("Historical Records", total_records)

# =========================
# Main Insight
# =========================
st.subheader("Brief Environmental Insight")

if latest_prediction > avg_pred:
    st.warning(
        "📌 The latest predicted PM2.5 level is higher than the average prediction. "
        "This indicates a possible increase in pollution concentration compared with historical conditions."
    )
else:
    st.info(
        "📌 The latest predicted PM2.5 level is lower than the average prediction. "
        "This indicates relatively stable or improving air quality conditions."
    )

# =========================
# Predicted Trend
# =========================
st.subheader("Predicted Pollution Trend")

fig_pred = px.line(
    df,
    x="time",
    y=["pm2_5", "predicted_pm2_5"],
    title="Observed vs Predicted PM2.5"
)

fig_pred.update_layout(
    xaxis_title="Time",
    yaxis_title="PM2.5 Concentration",
    legend_title="Data Source"
)

st.plotly_chart(fig_pred, width="stretch")

show_prediction_insight(latest_prediction, avg_pred)

# =========================
# CAMS vs Open-Meteo
# =========================
st.subheader("Regional Atmospheric Pattern Comparison")

st.write(
    "This section compares local air quality observations from Open-Meteo "
    "with regional atmospheric reanalysis data from Copernicus CAMS."
)

fig_compare = px.line(
    df,
    x="time",
    y=["pm2_5", "cams_pm2_5"],
    title="Open-Meteo PM2.5 vs Copernicus CAMS PM2.5"
)

fig_compare.update_layout(
    xaxis_title="Time",
    yaxis_title="PM2.5 Concentration",
    legend_title="Source"
)

st.plotly_chart(fig_compare, width="stretch")

cams_corr = df["pm2_5"].corr(df["cams_pm2_5"])
show_correlation_insight(cams_corr)

# =========================
# Pollution Distribution
# =========================
st.subheader("Pollution Level Distribution")

fig_hist = px.histogram(
    df,
    x="pm2_5",
    nbins=30,
    title="Distribution of PM2.5 Concentration"
)

fig_hist.update_layout(
    xaxis_title="PM2.5 Concentration",
    yaxis_title="Frequency"
)

st.plotly_chart(fig_hist, width="stretch")

show_distribution_insight(df)

# =========================
# Daily Summary
# =========================
st.subheader("Daily Air Quality Summary")

df["date"] = df["time"].dt.date

daily_summary = df.groupby("date").agg(
    average_pm25=("pm2_5", "mean"),
    maximum_pm25=("pm2_5", "max"),
    average_prediction=("predicted_pm2_5", "mean")
).reset_index()

fig_daily = px.line(
    daily_summary,
    x="date",
    y=["average_pm25", "maximum_pm25", "average_prediction"],
    title="Daily Air Quality Pattern"
)

fig_daily.update_layout(
    xaxis_title="Date",
    yaxis_title="PM2.5 Concentration",
    legend_title="Metric"
)

st.plotly_chart(fig_daily, width="stretch")

show_daily_summary_insight(daily_summary)

# =========================
# How It Works
# =========================
st.subheader("How This System Works")

st.markdown(
    """
    This dashboard is generated from a batch data pipeline that supports air quality prediction
    and anomaly detection.

    **Data Sources**
    - **Open-Meteo:** local air quality and meteorological data.
    - **Copernicus CAMS:** regional atmospheric reanalysis data.

    **Pipeline Process**
    1. Historical environmental data is collected from Open-Meteo and CAMS.
    2. Raw data is cleaned and converted into structured tabular format.
    3. Both data sources are merged based on timestamp.
    4. Machine learning is used to predict PM2.5 concentration.
    5. Anomaly detection identifies unusual pollution spikes.
    6. The processed results are stored in PostgreSQL and displayed in this dashboard.
    """
)

# =========================
# Dataset Preview
# =========================
with st.expander("View Processed Dataset"):
    st.dataframe(df.tail(30))