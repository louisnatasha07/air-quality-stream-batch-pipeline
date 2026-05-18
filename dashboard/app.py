import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Air Quality Monitoring System",
    layout="wide",
)


# =========================
# CUSTOM STYLE
# =========================
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 3rem;
        padding-left: 5rem;
        padding-right: 5rem;
    }

    .section-title {
        font-size: 18px;
        letter-spacing: 5px;
        color: #7b8aa5;
        text-transform: uppercase;
        margin-top: 28px;
        margin-bottom: 12px;
    }

    .insight-box {
        background-color: #161b22;
        border-left: 5px solid #4e8cff;
        padding: 18px 22px;
        border-radius: 10px;
        margin-top: 12px;
        margin-bottom: 20px;
    }

    .alert-box {
        background-color: #251b1b;
        border-left: 5px solid #ff5c5c;
        padding: 18px 22px;
        border-radius: 10px;
        margin-top: 12px;
        margin-bottom: 20px;
    }

    .safe-box {
        background-color: #17251b;
        border-left: 5px solid #3ddc84;
        padding: 18px 22px;
        border-radius: 10px;
        margin-top: 12px;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# DATABASE
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
# HELPERS
# =========================
def get_air_quality_status(pm25):
    if pm25 <= 15:
        return "Good", "🟢"
    elif pm25 <= 35:
        return "Moderate", "🟡"
    elif pm25 <= 75:
        return "Unhealthy", "🟠"
    return "Hazardous", "🔴"


def insight_box(text):
    st.markdown(f'<div class="insight-box">{text}</div>', unsafe_allow_html=True)


def alert_box(text):
    st.markdown(f'<div class="alert-box">{text}</div>', unsafe_allow_html=True)


def safe_box(text):
    st.markdown(f'<div class="safe-box">{text}</div>', unsafe_allow_html=True)


def filter_by_date(dataframe, start_date, end_date):
    return dataframe[
        (dataframe["time"].dt.date >= start_date)
        & (dataframe["time"].dt.date <= end_date)
    ].copy()


def make_city_summary(dataframe):
    city_summary = (
        dataframe.groupby("city")
        .agg(
            average_pm25=("pm2_5", "mean"),
            maximum_pm25=("pm2_5", "max"),
            average_prediction=("predicted_pm2_5", "mean"),
            average_error=("prediction_error", "mean"),
            anomaly_count=("is_anomaly", "sum"),
            latitude=("latitude", "first"),
            longitude=("longitude", "first"),
            records=("city", "count"),
        )
        .reset_index()
    )

    city_summary["status"] = city_summary["average_pm25"].apply(
        lambda x: get_air_quality_status(x)[0]
    )

    return city_summary


# =========================
# LOAD DATA
# =========================
df = pd.read_sql("SELECT * FROM multi_city_air_quality_data", engine)

df["time"] = pd.to_datetime(df["time"])
df = df.sort_values(["city", "time"])
df["prediction_error"] = abs(df["pm2_5"] - df["predicted_pm2_5"])

min_date = df["time"].min().date()
max_date = df["time"].max().date()
cities = sorted(df["city"].unique())


# =========================
# HEADER
# =========================
st.title("Air Quality Monitoring System")
st.caption(
    "Prediksi kualitas udara dan deteksi anomali multi-region menggunakan "
    "Open-Meteo sebagai observed data dan Copernicus CAMS sebagai atmospheric context."
)


# =========================
# TABS
# =========================
tab_all, tab_region, tab_ml = st.tabs(
    ["📊 SUMMARY 5 REGION", "🌆 SUMMARY EACH REGION", "🤖 ML INSIGHTS"]
)


# ==========================================================
# TAB 1 — SUMMARY 5 REGION
# ==========================================================
with tab_all:
    st.markdown('<div class="section-title">Date Filter</div>', unsafe_allow_html=True)

    date_range_all = st.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="date_all",
    )

    if isinstance(date_range_all, tuple) and len(date_range_all) == 2:
        start_all, end_all = date_range_all
    else:
        start_all, end_all = min_date, max_date

    all_df = filter_by_date(df, start_all, end_all)

    if all_df.empty:
        st.warning("No data available for selected date range.")
        st.stop()

    city_summary = make_city_summary(all_df)

    st.markdown('<div class="section-title">Overview 5 Region</div>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Regions", city_summary["city"].nunique())
    c2.metric("Avg PM2.5", f"{all_df['pm2_5'].mean():.1f} µg/m³")
    c3.metric("Max PM2.5", f"{all_df['pm2_5'].max():.1f} µg/m³")
    c4.metric("Anomalies", int(all_df["is_anomaly"].sum()))
    c5.metric("Records", f"{len(all_df):,}")

    st.markdown('<div class="section-title">Air Quality Map</div>', unsafe_allow_html=True)

    fig_map = px.scatter_mapbox(
        city_summary,
        lat="latitude",
        lon="longitude",
        color="status",
        size="average_pm25",
        hover_name="city",
        hover_data={
            "average_pm25": ":.2f",
            "maximum_pm25": ":.2f",
            "average_prediction": ":.2f",
            "average_error": ":.2f",
            "anomaly_count": True,
            "latitude": False,
            "longitude": False,
        },
        zoom=1,
        height=450,
        title="Average Air Quality Status Across 5 Regions",
    )

    fig_map.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
    )

    st.plotly_chart(fig_map, width="stretch")

    highest = city_summary.loc[city_summary["average_pm25"].idxmax()]
    lowest = city_summary.loc[city_summary["average_pm25"].idxmin()]
    most_anomaly = city_summary.loc[city_summary["anomaly_count"].idxmax()]

    insight_box(
        f"📌 During the selected period, <b>{highest['city']}</b> has the highest average PM2.5 "
        f"(<b>{highest['average_pm25']:.2f} µg/m³</b>), while <b>{lowest['city']}</b> has the lowest "
        f"(<b>{lowest['average_pm25']:.2f} µg/m³</b>). The most anomaly events were detected in "
        f"<b>{most_anomaly['city']}</b> with <b>{int(most_anomaly['anomaly_count'])}</b> events."
    )

    st.markdown('<div class="section-title">Region Ranking</div>', unsafe_allow_html=True)

    fig_rank = px.bar(
        city_summary.sort_values("average_pm25", ascending=False),
        x="city",
        y="average_pm25",
        color="status",
        title="Average PM2.5 Ranking by Region",
        labels={
            "city": "Region",
            "average_pm25": "Average PM2.5",
            "status": "Status",
        },
    )

    st.plotly_chart(fig_rank, width="stretch")

    st.markdown('<div class="section-title">Prediction Error Comparison</div>', unsafe_allow_html=True)

    fig_error = px.bar(
        city_summary.sort_values("average_error"),
        x="city",
        y="average_error",
        title="Average Prediction Error Against Open-Meteo Observation",
        labels={
            "city": "Region",
            "average_error": "Avg |Observed - Predicted|",
        },
    )

    st.plotly_chart(fig_error, width="stretch")

    best_model = city_summary.loc[city_summary["average_error"].idxmin()]
    worst_model = city_summary.loc[city_summary["average_error"].idxmax()]

    insight_box(
        f"📌 Compared with Open-Meteo observed PM2.5, the prediction model is closest in "
        f"<b>{best_model['city']}</b> with average error <b>{best_model['average_error']:.2f}</b>. "
        f"The largest prediction gap occurs in <b>{worst_model['city']}</b> with average error "
        f"<b>{worst_model['average_error']:.2f}</b>."
    )

    st.markdown('<div class="section-title">Insight Per Region</div>', unsafe_allow_html=True)

    for _, row in city_summary.sort_values("average_pm25", ascending=False).iterrows():
        status, icon = get_air_quality_status(row["average_pm25"])

        text = (
            f"{icon} <b>{row['city']}</b>: average PM2.5 is "
            f"<b>{row['average_pm25']:.2f} µg/m³</b> and categorized as <b>{status}</b>. "
            f"Maximum PM2.5 reached <b>{row['maximum_pm25']:.2f} µg/m³</b>. "
            f"There are <b>{int(row['anomaly_count'])}</b> anomaly events. "
            f"Prediction error against Open-Meteo observation is <b>{row['average_error']:.2f}</b>."
        )

        if status in ["Unhealthy", "Hazardous"]:
            alert_box(text)
        else:
            safe_box(text)


# ==========================================================
# TAB 2 — SUMMARY EACH REGION
# ==========================================================
with tab_region:
    st.markdown('<div class="section-title">Region Filter</div>', unsafe_allow_html=True)

    r1, r2 = st.columns([1, 2])

    with r1:
        selected_region = st.selectbox(
            "Select Region",
            cities,
            index=cities.index("Jakarta") if "Jakarta" in cities else 0,
            key="region_city",
        )

    with r2:
        date_range_region = st.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="date_region",
        )

    if isinstance(date_range_region, tuple) and len(date_range_region) == 2:
        start_region, end_region = date_range_region
    else:
        start_region, end_region = min_date, max_date

    region_df = df[
        (df["city"] == selected_region)
        & (df["time"].dt.date >= start_region)
        & (df["time"].dt.date <= end_region)
    ].copy()

    if region_df.empty:
        st.warning("No data available for selected region and date range.")
        st.stop()

    st.markdown(
        f'<div class="section-title">{selected_region} Overview</div>',
        unsafe_allow_html=True,
    )

    avg_pm25 = region_df["pm2_5"].mean()
    max_pm25 = region_df["pm2_5"].max()
    avg_cams = region_df["cams_pm2_5"].mean()
    anomaly_count = int(region_df["is_anomaly"].sum())
    records = len(region_df)

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Avg PM2.5", f"{avg_pm25:.1f} µg/m³")
    c2.metric("Max PM2.5", f"{max_pm25:.1f} µg/m³")
    c3.metric("Avg CAMS PM2.5", f"{avg_cams:.6f}")
    c4.metric("Anomalies", anomaly_count)
    c5.metric("Records", f"{records:,}")

    status, icon = get_air_quality_status(avg_pm25)

    if status in ["Unhealthy", "Hazardous"]:
        alert_box(
            f"{icon} <b>{selected_region}</b> is categorized as <b>{status}</b> during the selected period. "
            f"Average Open-Meteo observed PM2.5 is <b>{avg_pm25:.2f} µg/m³</b>."
        )
    else:
        safe_box(
            f"{icon} <b>{selected_region}</b> is categorized as <b>{status}</b> during the selected period. "
            f"Average Open-Meteo observed PM2.5 is <b>{avg_pm25:.2f} µg/m³</b>."
        )

    st.markdown('<div class="section-title">PM2.5 Trend</div>', unsafe_allow_html=True)

    fig_trend = px.line(
        region_df,
        x="time",
        y="pm2_5",
        title=f"Open-Meteo Observed PM2.5 Trend in {selected_region}",
        labels={
            "time": "Time",
            "pm2_5": "PM2.5 Concentration",
        },
    )

    fig_trend.add_hline(
        y=75,
        line_dash="dash",
        annotation_text="Unhealthy Threshold",
        annotation_position="top right",
    )

    st.plotly_chart(fig_trend, width="stretch")

    first_avg = region_df.head(max(1, len(region_df) // 5))["pm2_5"].mean()
    last_avg = region_df.tail(max(1, len(region_df) // 5))["pm2_5"].mean()

    if last_avg > first_avg:
        insight_box(
            f"📌 PM2.5 in <b>{selected_region}</b> tends to increase toward the end of the selected period. "
            "This may indicate worsening air quality conditions."
        )
    else:
        insight_box(
            f"📌 PM2.5 in <b>{selected_region}</b> tends to decrease or remain stable toward the end of the selected period."
        )

    st.markdown('<div class="section-title">Pollution Distribution</div>', unsafe_allow_html=True)

    fig_hist = px.histogram(
        region_df,
        x="pm2_5",
        nbins=30,
        title=f"PM2.5 Distribution in {selected_region}",
        labels={"pm2_5": "PM2.5 Concentration"},
    )

    st.plotly_chart(fig_hist, width="stretch")

    high_ratio = ((region_df["pm2_5"] > 75).sum() / len(region_df)) * 100
    moderate_ratio = (
        ((region_df["pm2_5"] > 15) & (region_df["pm2_5"] <= 75)).sum()
        / len(region_df)
    ) * 100

    if high_ratio > 30:
        alert_box(
            f"⚠️ Around <b>{high_ratio:.1f}%</b> of observations in <b>{selected_region}</b> "
            "fall into unhealthy or hazardous levels."
        )
    elif high_ratio > 10:
        insight_box(
            f"📌 Around <b>{high_ratio:.1f}%</b> of observations in <b>{selected_region}</b> "
            "show unhealthy pollution levels."
        )
    else:
        safe_box(
            f"✅ Most observations in <b>{selected_region}</b> remain below severe pollution levels. "
            f"Moderate observations account for about <b>{moderate_ratio:.1f}%</b>."
        )

    st.markdown('<div class="section-title">Daily Pattern</div>', unsafe_allow_html=True)

    region_df["date"] = region_df["time"].dt.date

    daily_region = (
        region_df.groupby("date")
        .agg(
            average_pm25=("pm2_5", "mean"),
            maximum_pm25=("pm2_5", "max"),
            average_prediction=("predicted_pm2_5", "mean"),
        )
        .reset_index()
    )

    fig_daily = px.line(
        daily_region,
        x="date",
        y=["average_pm25", "maximum_pm25", "average_prediction"],
        title=f"Daily Air Quality Pattern in {selected_region}",
        labels={
            "date": "Date",
            "value": "PM2.5 Concentration",
            "variable": "Metric",
        },
    )

    st.plotly_chart(fig_daily, width="stretch")

    peak_day = daily_region.loc[daily_region["maximum_pm25"].idxmax()]
    clean_day = daily_region.loc[daily_region["average_pm25"].idxmin()]

    insight_box(
        f"📌 The highest daily PM2.5 peak in <b>{selected_region}</b> occurred on "
        f"<b>{peak_day['date']}</b> with <b>{peak_day['maximum_pm25']:.2f} µg/m³</b>. "
        f"The cleanest day on average was <b>{clean_day['date']}</b> with "
        f"<b>{clean_day['average_pm25']:.2f} µg/m³</b>."
    )


# ==========================================================
# TAB 3 — ML INSIGHTS
# ==========================================================
with tab_ml:
    st.markdown('<div class="section-title">ML Filter</div>', unsafe_allow_html=True)

    m1, m2 = st.columns([1, 2])

    with m1:
        selected_ml_region = st.selectbox(
            "Select Region",
            cities,
            index=cities.index("Jakarta") if "Jakarta" in cities else 0,
            key="ml_city",
        )

    with m2:
        date_range_ml = st.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="date_ml",
        )

    if isinstance(date_range_ml, tuple) and len(date_range_ml) == 2:
        start_ml, end_ml = date_range_ml
    else:
        start_ml, end_ml = min_date, max_date

    ml_df = df[
        (df["city"] == selected_ml_region)
        & (df["time"].dt.date >= start_ml)
        & (df["time"].dt.date <= end_ml)
    ].copy()

    if ml_df.empty:
        st.warning("No data available for selected region and date range.")
        st.stop()

    st.markdown('<div class="section-title">Prediction Overview</div>', unsafe_allow_html=True)

    latest = ml_df.iloc[-1]
    latest_status, latest_icon = get_air_quality_status(latest["predicted_pm2_5"])

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Latest Prediction", f"{latest['predicted_pm2_5']:.1f} µg/m³")
    c2.metric("Open-Meteo Observed", f"{latest['pm2_5']:.1f} µg/m³")
    c3.metric("Avg Prediction Error", f"{ml_df['prediction_error'].mean():.1f}")
    c4.metric("Prediction Status", f"{latest_icon} {latest_status}")

    st.markdown('<div class="section-title">Open-Meteo vs Prediction</div>', unsafe_allow_html=True)

    fig_pred = go.Figure()
    
    # Open-Meteo observed
    fig_pred.add_trace(
        go.Scatter(
            x=ml_df["time"],
            y=ml_df["pm2_5"],
            mode="lines",
            name="Observed PM2.5",
            line=dict(color="#7ec8ff", width=2),
        )
    )
    
    # Model prediction
    fig_pred.add_trace(
        go.Scatter(
            x=ml_df["time"],
            y=ml_df["predicted_pm2_5"],
            mode="lines",
            name="Predicted PM 2.5",
            line=dict(color="#ff4fa3", width=2),
        )
    )
    
    fig_pred.update_layout(
        title=f"Open-Meteo Observed PM2.5 vs Model Prediction in {selected_ml_region}",
        xaxis_title="Time",
        yaxis_title="PM2.5 Concentration",
        legend_title="Metric",
        height=500,
        template="plotly_dark",
    )
    
    st.plotly_chart(fig_pred, width="stretch")

    avg_error = ml_df["prediction_error"].mean()

    if avg_error <= 10:
        safe_box(
            f"✅ Model prediction is close to Open-Meteo observed PM2.5 in <b>{selected_ml_region}</b>. "
            f"Average prediction error is <b>{avg_error:.2f}</b>."
        )
    elif avg_error <= 25:
        insight_box(
            f"📌 Model prediction has moderate deviation from Open-Meteo observed PM2.5 in "
            f"<b>{selected_ml_region}</b>. Average prediction error is <b>{avg_error:.2f}</b>."
        )
    else:
        alert_box(
            f"⚠️ Model prediction differs significantly from Open-Meteo observed PM2.5 in "
            f"<b>{selected_ml_region}</b>. Average prediction error is <b>{avg_error:.2f}</b>."
        )

    st.markdown('<div class="section-title">Prediction Error Distribution</div>', unsafe_allow_html=True)

    fig_error_dist = px.histogram(
        ml_df,
        x="prediction_error",
        nbins=30,
        title=f"Prediction Error Distribution in {selected_ml_region}",
        labels={"prediction_error": "|Observed - Predicted|"},
    )

    st.plotly_chart(fig_error_dist, width="stretch")

    st.markdown('<div class="section-title">CAMS vs Open-Meteo</div>', unsafe_allow_html=True)

    fig_cams = go.Figure()
    
    # Open=Meteo observed
    fig_cams.add_trace(
        go.Scatter(
            x=ml_df["time"],
            y=ml_df["pm2_5"],
            mode="lines",
            name="Open-Meteo PM2.5",
            line=dict(color="#7ec8ff", width=2),
        )
    )
    
    # CAMS scaled biar keliatan
    fig_cams.add_trace(
        go.Scatter(
            x=ml_df["time"],
            y=ml_df["cams_pm2_5"] * 1_000_000,
            mode="lines",
            name="CAMS PM2.5 (scaled)",
            line=dict(color="#ff4fa3", width=2),
        )
    )
    
    fig_cams.update_layout(
        title=f"Open-Meteo vs Copernicus CAMS in {selected_ml_region}",
        xaxis_title="Time",
        yaxis_title="PM2.5 Concentration",
        legend_title="Source",
        height=500,
        template="plotly_dark",
    )
    
    st.plotly_chart(fig_cams, width="stretch")

    corr = ml_df["pm2_5"].corr(ml_df["cams_pm2_5"])

    if corr > 0.7:
        insight_box(
            f"📌 Strong relationship detected between Open-Meteo and CAMS in "
            f"<b>{selected_ml_region}</b> (correlation = <b>{corr:.2f}</b>). "
            "Regional atmospheric patterns align with local observations."
        )
    elif corr > 0.4:
        insight_box(
            f"📌 Moderate relationship detected between Open-Meteo and CAMS in "
            f"<b>{selected_ml_region}</b> (correlation = <b>{corr:.2f}</b>). "
            "Regional atmospheric data partially explains local pollution."
        )
    else:
        alert_box(
            f"⚠️ Weak relationship detected between Open-Meteo and CAMS in "
            f"<b>{selected_ml_region}</b> (correlation = <b>{corr:.2f}</b>). "
            "Local factors such as traffic, urban activity, or microclimate may dominate."
        )

    st.markdown('<div class="section-title">Anomaly Detection</div>', unsafe_allow_html=True)

    anomaly_df = ml_df[ml_df["is_anomaly"] == True]

    fig_anomaly = go.Figure()

    fig_anomaly.add_trace(
        go.Scatter(
            x=ml_df["time"],
            y=ml_df["pm2_5"],
            mode="lines",
            name="Open-Meteo Observed PM2.5",
        )
    )

    fig_anomaly.add_trace(
        go.Scatter(
            x=ml_df["time"],
            y=ml_df["anomaly_threshold"],
            mode="lines",
            name="Anomaly Threshold",
            line=dict(dash="dash"),
        )
    )

    fig_anomaly.add_trace(
        go.Scatter(
            x=anomaly_df["time"],
            y=anomaly_df["pm2_5"],
            mode="markers",
            name="Anomaly Event",
            marker=dict(size=8),
        )
    )

    fig_anomaly.update_layout(
        title=f"Anomaly Detection Based on Open-Meteo Observed PM2.5 in {selected_ml_region}",
        xaxis_title="Time",
        yaxis_title="PM2.5 Concentration",
    )

    st.plotly_chart(fig_anomaly, width="stretch")

    if len(anomaly_df) > 0:
        peak = anomaly_df.loc[anomaly_df["pm2_5"].idxmax()]
        alert_box(
            f"⚠️ <b>{len(anomaly_df)}</b> anomaly events detected in <b>{selected_ml_region}</b>. "
            f"The highest anomaly occurred on <b>{peak['time'].date()}</b> with Open-Meteo observed "
            f"PM2.5 = <b>{peak['pm2_5']:.2f} µg/m³</b>."
        )
    else:
        safe_box(
            f"✅ No anomaly events detected in <b>{selected_ml_region}</b> for the selected period."
        )

    with st.expander("View filtered ML dataset"):
        st.dataframe(ml_df.tail(50))