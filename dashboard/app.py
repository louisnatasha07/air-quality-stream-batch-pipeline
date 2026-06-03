import os
from pathlib import Path
from datetime import date

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Air Quality Monitoring System",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================
# STREAMLIT PLOTLY SAFE KEY PATCH
# =========================
_original_plotly_chart = st.plotly_chart
_plotly_chart_counter = 0


def safe_plotly_chart(*args, **kwargs):
    global _plotly_chart_counter

    if "key" not in kwargs:
        _plotly_chart_counter += 1
        kwargs["key"] = f"plotly_chart_{_plotly_chart_counter}"

    return _original_plotly_chart(*args, **kwargs)


st.plotly_chart = safe_plotly_chart

# ============================================================
# CONSTANTS
# ============================================================
CITY_COORDS = {
    "Jakarta": {"latitude": -6.2088, "longitude": 106.8456},
    "Surakarta": {"latitude": -7.5755, "longitude": 110.8243},
    "Kuala Lumpur": {"latitude": 3.1390, "longitude": 101.6869},
    "Singapore": {"latitude": 1.3521, "longitude": 103.8198},
}
TARGET_CITIES = list(CITY_COORDS.keys())

# ============================================================
# CUSTOM STYLE
# ============================================================
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-left: 4rem;
        padding-right: 4rem;
        padding-bottom: 3rem;
    }
    .main-header {
        font-size: 42px;
        font-weight: 800;
        letter-spacing: -1px;
        margin-bottom: 0px;
    }
    .main-subtitle {
        font-size: 16px;
        color: #8b949e;
        margin-bottom: 30px;
    }
    .section-title {
        font-size: 17px;
        letter-spacing: 4px;
        color: #7b8aa5;
        text-transform: uppercase;
        margin-top: 26px;
        margin-bottom: 14px;
        font-weight: 800;
    }
    .mini-title {
        font-size: 15px;
        color: #b8c2d6;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 10px;
        margin-bottom: 6px;
        font-weight: 700;
    }
    .insight-box {
        background-color: #161b22;
        border-left: 5px solid #4e8cff;
        padding: 16px 20px;
        border-radius: 10px;
        margin-top: 12px;
        margin-bottom: 20px;
        color: #d8dee9;
    }
    .alert-box {
        background-color: #251b1b;
        border-left: 5px solid #ff5c5c;
        padding: 16px 20px;
        border-radius: 10px;
        margin-top: 12px;
        margin-bottom: 20px;
        color: #f0d6d6;
    }
    .safe-box {
        background-color: #17251b;
        border-left: 5px solid #3ddc84;
        padding: 16px 20px;
        border-radius: 10px;
        margin-top: 12px;
        margin-bottom: 20px;
        color: #d9f7e5;
    }
    .warning-box {
        background-color: #252117;
        border-left: 5px solid #f7c948;
        padding: 16px 20px;
        border-radius: 10px;
        margin-top: 12px;
        margin-bottom: 20px;
        color: #fff0bd;
    }
    div[data-testid="metric-container"] {
        background-color: #0f172a;
        border: 1px solid #1f2a44;
        padding: 18px;
        border-radius: 14px;
        box-shadow: 0 0 0 1px rgba(255,255,255,0.02);
    }
    .footer-note {
        color: #7b8aa5;
        font-size: 13px;
        margin-top: 30px;
    }
    hr {
        border: none;
        border-top: 1px solid #202b3d;
        margin-top: 22px;
        margin-bottom: 22px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# DATABASE
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres_db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "air_quality_db")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

@st.cache_resource(show_spinner=False)
def get_engine():
    return create_engine(DATABASE_URL, pool_pre_ping=True)

engine = get_engine()

# ============================================================
# HELPERS
# ============================================================
def render_section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def render_mini_title(title):
    st.markdown(f'<div class="mini-title">{title}</div>', unsafe_allow_html=True)


def insight_box(text):
    st.markdown(f'<div class="insight-box">{text}</div>', unsafe_allow_html=True)


def alert_box(text):
    st.markdown(f'<div class="alert-box">{text}</div>', unsafe_allow_html=True)


def safe_box(text):
    st.markdown(f'<div class="safe-box">{text}</div>', unsafe_allow_html=True)


def warning_box(text):
    st.markdown(f'<div class="warning-box">{text}</div>', unsafe_allow_html=True)


def get_air_quality_status(pm25):
    if pd.isna(pm25):
        return "Unknown", "⚪"
    if pm25 <= 15:
        return "Good", "🟢"
    if pm25 <= 35:
        return "Moderate", "🟡"
    if pm25 <= 75:
        return "Unhealthy", "🟠"
    return "Hazardous", "🔴"


def calculate_aqi_category(aqi):
    if pd.isna(aqi):
        return "Unknown"
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Moderate"
    if aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    if aqi <= 200:
        return "Unhealthy"
    if aqi <= 300:
        return "Very Unhealthy"
    return "Hazardous"


def find_col(df, candidates):
    if df is None or df.empty:
        return None
    lower_map = {col.lower(): col for col in df.columns}
    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]
    return None


def safe_numeric(df, cols):
    for col in cols:
        if col and col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def safe_datetime(df, cols):
    for col in cols:
        if col and col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def normalize_bool(series):
    return series.fillna(False).astype(bool)


def add_city_coordinates(df):
    if df.empty or "city" not in df.columns:
        return df
    temp = df.copy()
    if "latitude" not in temp.columns:
        temp["latitude"] = temp["city"].map(lambda city: CITY_COORDS.get(city, {}).get("latitude"))
    if "longitude" not in temp.columns:
        temp["longitude"] = temp["city"].map(lambda city: CITY_COORDS.get(city, {}).get("longitude"))
    return temp


def latest_per_city(df, city_col="city", time_col=None):
    if df.empty or city_col not in df.columns:
        return pd.DataFrame()
    temp = df.copy()
    if time_col and time_col in temp.columns:
        temp = temp.dropna(subset=[time_col]).sort_values([city_col, time_col])
    elif "created_at" in temp.columns:
        temp = temp.sort_values([city_col, "created_at"])
    return temp.groupby(city_col, as_index=False).tail(1).reset_index(drop=True)


def filter_by_cities(df, selected_cities):
    if df.empty or "city" not in df.columns:
        return df
    if not selected_cities:
        return df
    return df[df["city"].isin(selected_cities)].copy()


def filter_by_date(df, time_col, start_date, end_date):
    if df.empty or not time_col or time_col not in df.columns:
        return df
    temp = df.copy().dropna(subset=[time_col])
    return temp[
        (temp[time_col].dt.date >= start_date)
        & (temp[time_col].dt.date <= end_date)
    ].copy()


def read_sql(query):
    try:
        return pd.read_sql(text(query), engine)
    except SQLAlchemyError as error:
        st.error(f"Database query failed: {error}")
        return pd.DataFrame()


def table_exists(table_name):
    try:
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = :table_name
            );
        """
        with engine.connect() as conn:
            return bool(conn.execute(text(query), {"table_name": table_name}).scalar())
    except SQLAlchemyError:
        return False


def get_table_columns(table_name):
    try:
        query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = :table_name
            ORDER BY ordinal_position;
        """
        with engine.connect() as conn:
            rows = conn.execute(text(query), {"table_name": table_name}).fetchall()
        return [row[0] for row in rows]
    except SQLAlchemyError:
        return []


def get_table_status():
    rows = []
    for table in ["cams_air_quality_data", "city_air_quality_summary", "air_quality_stream"]:
        exists = table_exists(table)
        count = 0
        if exists:
            try:
                with engine.connect() as conn:
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {table};")).scalar()
            except SQLAlchemyError:
                count = 0
        rows.append({"table": table, "exists": exists, "row_count": int(count or 0)})
    return pd.DataFrame(rows)


def format_date_range(df, time_col):
    if df.empty or not time_col or time_col not in df.columns:
        return "-"
    min_time = df[time_col].min()
    max_time = df[time_col].max()
    if pd.isna(min_time) or pd.isna(max_time):
        return "-"
    return f"{min_time.strftime('%Y-%m-%d %H:%M')} → {max_time.strftime('%Y-%m-%d %H:%M')}"

# ============================================================
# LOAD TABLES
# ============================================================
batch_summary = read_sql("SELECT * FROM city_air_quality_summary ORDER BY city;") if table_exists("city_air_quality_summary") else pd.DataFrame()
batch_data = read_sql("SELECT * FROM cams_air_quality_data ORDER BY city;") if table_exists("cams_air_quality_data") else pd.DataFrame()
stream_data = read_sql("SELECT * FROM air_quality_stream ORDER BY created_at DESC;") if table_exists("air_quality_stream") else pd.DataFrame()

# ============================================================
# COLUMN DETECTION + NORMALIZATION
# ============================================================
batch_time_col = find_col(batch_data, ["timestamp", "time", "datetime", "date"])
stream_time_col = find_col(stream_data, ["timestamp", "time", "datetime", "date"])
stream_created_col = find_col(stream_data, ["created_at"])

batch_pm25_col = find_col(batch_data, ["cams_pm2_5", "pm2_5", "pm25"])
batch_pm10_col = find_col(batch_data, ["cams_pm10", "pm10"])
prediction_col = find_col(batch_data, ["prediction", "predicted_pm25", "predicted_pm2_5", "avg_prediction"])
batch_anomaly_col = find_col(batch_data, ["is_anomaly", "anomaly"])

summary_avg_col = find_col(batch_summary, ["average_pm25", "average_pm2_5"])
summary_max_col = find_col(batch_summary, ["max_pm25", "maximum_pm25", "max_pm2_5"])
summary_pred_col = find_col(batch_summary, ["avg_prediction", "average_prediction", "prediction"])
summary_anomaly_col = find_col(batch_summary, ["anomaly_count", "anomalies"])

stream_pm25_col = find_col(stream_data, ["pm25", "pm2_5"])
stream_pm10_col = find_col(stream_data, ["pm10"])
stream_aqi_col = find_col(stream_data, ["aqi"])
stream_anomaly_col = find_col(stream_data, ["is_anomaly", "anomaly"])
stream_reason_col = find_col(stream_data, ["anomaly_reason", "reason"])

batch_data = safe_datetime(batch_data, [batch_time_col])
stream_data = safe_datetime(stream_data, [stream_time_col, stream_created_col])
batch_data = safe_numeric(batch_data, [batch_pm25_col, batch_pm10_col, prediction_col])
stream_data = safe_numeric(
    stream_data,
    [stream_pm25_col, stream_pm10_col, stream_aqi_col, "carbon_monoxide", "nitrogen_dioxide", "sulphur_dioxide", "ozone", "latitude", "longitude"],
)
batch_summary = safe_numeric(batch_summary, [summary_avg_col, summary_max_col, summary_pred_col, summary_anomaly_col])

if batch_anomaly_col and batch_anomaly_col in batch_data.columns:
    batch_data[batch_anomaly_col] = normalize_bool(batch_data[batch_anomaly_col])
if stream_anomaly_col and stream_anomaly_col in stream_data.columns:
    stream_data[stream_anomaly_col] = normalize_bool(stream_data[stream_anomaly_col])

batch_summary = add_city_coordinates(batch_summary)
batch_data = add_city_coordinates(batch_data)
stream_data = add_city_coordinates(stream_data)

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title("🌫️ Air Quality Dashboard")
st.sidebar.caption("Batch CAMS + Stream Open-Meteo")

table_status = get_table_status()
with st.sidebar.expander("Database Tables", expanded=True):
    st.dataframe(table_status, hide_index=True, use_container_width=True)

all_cities = sorted(
    set(batch_summary["city"].dropna().tolist() if "city" in batch_summary.columns else [])
    | set(batch_data["city"].dropna().tolist() if "city" in batch_data.columns else [])
    | set(stream_data["city"].dropna().tolist() if "city" in stream_data.columns else [])
)
if not all_cities:
    all_cities = TARGET_CITIES

selected_cities = st.sidebar.multiselect("Select Cities", all_cities, default=all_cities)

date_candidates = []
if not batch_data.empty and batch_time_col:
    date_candidates.extend(batch_data[batch_time_col].dropna().dt.date.tolist())
if not stream_data.empty and stream_time_col:
    date_candidates.extend(stream_data[stream_time_col].dropna().dt.date.tolist())

if date_candidates:
    min_date = min(date_candidates)
    max_date = max(date_candidates)
else:
    min_date = date.today()
    max_date = date.today()

date_range = st.sidebar.date_input("Global Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

if st.sidebar.button("🔄 Refresh Dashboard"):
    st.cache_data.clear()
    st.rerun()

# Apply filters
filtered_batch_summary = filter_by_cities(batch_summary, selected_cities)
filtered_batch_data = filter_by_date(filter_by_cities(batch_data, selected_cities), batch_time_col, start_date, end_date)
filtered_stream_data = filter_by_date(filter_by_cities(stream_data, selected_cities), stream_time_col, start_date, end_date)

# ============================================================
# HEADER
# ============================================================
st.markdown('<div class="main-header">Air Quality Monitoring System</div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="main-subtitle">
    Integrated dashboard for CAMS batch processing, Open-Meteo stream processing, machine learning prediction,
    anomaly detection, PostgreSQL storage, Dagster orchestration, Kafka streaming, and Telegram alerting.
    </div>
    """,
    unsafe_allow_html=True,
)

if table_status["row_count"].sum() == 0:
    st.warning("No data found in PostgreSQL tables. Run the batch and stream pipelines first.")
    st.stop()

# ============================================================
# TABS
# ============================================================
tab_overview, tab_batch, tab_stream, tab_compare, tab_anomaly, tab_data, tab_health = st.tabs(
    [
        "📌 Executive Overview",
        "🏭 Batch CAMS Analysis",
        "⚡ Realtime Stream",
        "🤖 Batch vs Stream",
        "🚨 Anomaly Center",
        "🗃️ Data Explorer",
        "🛠️ System Health",
    ]
)

# ============================================================
# TAB 1 — EXECUTIVE OVERVIEW
# ============================================================
with tab_overview:
    render_section("Executive Summary")

    latest_stream = latest_per_city(filtered_stream_data, "city", stream_time_col)
    latest_batch = latest_per_city(filtered_batch_data, "city", batch_time_col)

    total_batch_anomalies = int(filtered_batch_summary[summary_anomaly_col].sum()) if not filtered_batch_summary.empty and summary_anomaly_col else int(filtered_batch_data[batch_anomaly_col].sum()) if not filtered_batch_data.empty and batch_anomaly_col else 0
    total_stream_anomalies = int(filtered_stream_data[stream_anomaly_col].sum()) if not filtered_stream_data.empty and stream_anomaly_col else 0

    avg_batch_pm25 = filtered_batch_summary[summary_avg_col].mean() if not filtered_batch_summary.empty and summary_avg_col else np.nan
    latest_stream_avg = latest_stream[stream_pm25_col].mean() if not latest_stream.empty and stream_pm25_col else np.nan

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Cities Monitored", len(selected_cities))
    c2.metric("Batch Records", f"{len(filtered_batch_data):,}")
    c3.metric("Stream Records", f"{len(filtered_stream_data):,}")
    c4.metric("Batch Anomalies", f"{total_batch_anomalies:,}")
    c5.metric("Stream Anomalies", f"{total_stream_anomalies:,}")

    c6, c7, c8 = st.columns(3)
    c6.metric("Batch Avg PM2.5", "-" if pd.isna(avg_batch_pm25) else f"{avg_batch_pm25:.2f} µg/m³")
    c7.metric("Latest Stream Avg PM2.5", "-" if pd.isna(latest_stream_avg) else f"{latest_stream_avg:.2f} µg/m³")
    c8.metric("Latest Stream Time", "-" if latest_stream.empty or not stream_time_col else str(latest_stream[stream_time_col].max()))

    render_section("Integrated Monitoring Map")
    map_frames = []
    if not filtered_batch_summary.empty and summary_avg_col:
        batch_map = filtered_batch_summary[["city", "latitude", "longitude", summary_avg_col]].copy()
        batch_map = batch_map.rename(columns={summary_avg_col: "pm25"})
        batch_map["source"] = "Batch CAMS Average"
        batch_map["status"] = batch_map["pm25"].apply(lambda value: get_air_quality_status(value)[0])
        map_frames.append(batch_map)
    if not latest_stream.empty and stream_pm25_col:
        stream_map = latest_stream[["city", "latitude", "longitude", stream_pm25_col]].copy()
        stream_map = stream_map.rename(columns={stream_pm25_col: "pm25"})
        stream_map["source"] = "Latest Stream"
        stream_map["status"] = stream_map["pm25"].apply(lambda value: get_air_quality_status(value)[0])
        map_frames.append(stream_map)

    if map_frames:
        map_df = pd.concat(map_frames, ignore_index=True).dropna(subset=["latitude", "longitude"])
        fig_map = px.scatter_mapbox(
            map_df,
            lat="latitude",
            lon="longitude",
            color="status",
            size="pm25",
            hover_name="city",
            hover_data={"source": True, "pm25": ":.2f", "latitude": False, "longitude": False},
            zoom=2,
            height=520,
            title="Air Quality Status by City and Data Source",
        )
        fig_map.update_layout(mapbox_style="open-street-map", margin={"r": 0, "t": 45, "l": 0, "b": 0})
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("Map data is not available yet.")

    render_section("Quick Comparison")
    col_left, col_right = st.columns(2)
    with col_left:
        if not filtered_batch_summary.empty and summary_avg_col:
            temp = filtered_batch_summary.copy()
            temp["status"] = temp[summary_avg_col].apply(lambda value: get_air_quality_status(value)[0])
            fig = px.bar(
                temp.sort_values(summary_avg_col, ascending=False),
                x="city",
                y=summary_avg_col,
                color="status",
                title="Batch Average PM2.5 by City",
                labels={"city": "City", summary_avg_col: "Average PM2.5"},
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Batch summary is unavailable.")
    with col_right:
        if not latest_stream.empty and stream_pm25_col:
            temp = latest_stream.copy()
            temp["status"] = temp[stream_pm25_col].apply(lambda value: get_air_quality_status(value)[0])
            fig = px.bar(
                temp.sort_values(stream_pm25_col, ascending=False),
                x="city",
                y=stream_pm25_col,
                color="status",
                title="Latest Stream PM2.5 by City",
                labels={"city": "City", stream_pm25_col: "Latest PM2.5"},
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Latest stream data is unavailable.")

    render_section("Narrative Insights")
    if not filtered_batch_summary.empty and summary_avg_col:
        highest = filtered_batch_summary.loc[filtered_batch_summary[summary_avg_col].idxmax()]
        lowest = filtered_batch_summary.loc[filtered_batch_summary[summary_avg_col].idxmin()]
        insight_box(
            f"📌 Based on CAMS batch summary, <b>{highest['city']}</b> has the highest average PM2.5 "
            f"(<b>{highest[summary_avg_col]:.2f} µg/m³</b>), while <b>{lowest['city']}</b> has the lowest "
            f"average PM2.5 (<b>{lowest[summary_avg_col]:.2f} µg/m³</b>)."
        )
    if not latest_stream.empty and stream_pm25_col:
        worst_stream = latest_stream.loc[latest_stream[stream_pm25_col].idxmax()]
        status, icon = get_air_quality_status(worst_stream[stream_pm25_col])
        box_func = alert_box if status in ["Unhealthy", "Hazardous"] else safe_box
        box_func(
            f"{icon} Latest Open-Meteo stream data shows that <b>{worst_stream['city']}</b> currently has the highest "
            f"PM2.5 level (<b>{worst_stream[stream_pm25_col]:.2f} µg/m³</b>), categorized as <b>{status}</b>."
        )

# ============================================================
# TAB 2 — BATCH CAMS ANALYSIS
# ============================================================
with tab_batch:
    render_section("Batch CAMS Processing Output")
    if filtered_batch_summary.empty:
        st.warning("Batch summary is empty. Run the Dagster batch pipeline first.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Batch Cities", filtered_batch_summary["city"].nunique())
        c2.metric("Avg PM2.5", "-" if not summary_avg_col else f"{filtered_batch_summary[summary_avg_col].mean():.2f}")
        c3.metric("Max PM2.5", "-" if not summary_max_col else f"{filtered_batch_summary[summary_max_col].max():.2f}")
        c4.metric("Anomalies", "-" if not summary_anomaly_col else f"{int(filtered_batch_summary[summary_anomaly_col].sum()):,}")

        st.dataframe(filtered_batch_summary, use_container_width=True)

        if summary_avg_col:
            temp = filtered_batch_summary.copy()
            temp["status"] = temp[summary_avg_col].apply(lambda value: get_air_quality_status(value)[0])
            fig_rank = px.bar(
                temp.sort_values(summary_avg_col, ascending=False),
                x="city",
                y=summary_avg_col,
                color="status",
                title="Average PM2.5 Ranking from CAMS Batch Summary",
                labels={"city": "City", summary_avg_col: "Average PM2.5"},
            )
            st.plotly_chart(fig_rank, use_container_width=True)

        if summary_max_col:
            fig_max = px.bar(
                filtered_batch_summary.sort_values(summary_max_col, ascending=False),
                x="city",
                y=summary_max_col,
                title="Maximum PM2.5 by City from Batch Data",
                labels={"city": "City", summary_max_col: "Maximum PM2.5"},
            )
            st.plotly_chart(fig_max, use_container_width=True)

        if summary_anomaly_col:
            fig_anom = px.bar(
                filtered_batch_summary.sort_values(summary_anomaly_col, ascending=False),
                x="city",
                y=summary_anomaly_col,
                title="Batch Anomaly Count by City",
                labels={"city": "City", summary_anomaly_col: "Anomaly Count"},
            )
            st.plotly_chart(fig_anom, use_container_width=True)

    render_section("Batch Detail Trend")
    if filtered_batch_data.empty:
        st.warning("Batch detail data is empty.")
    else:
        selected_batch_city = st.selectbox("Select batch city", sorted(filtered_batch_data["city"].dropna().unique()), key="batch_detail_city")
        city_batch = filtered_batch_data[filtered_batch_data["city"] == selected_batch_city].copy()
        if batch_time_col:
            city_batch = city_batch.sort_values(batch_time_col)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Records", f"{len(city_batch):,}")
        c2.metric("Avg CAMS PM2.5", "-" if not batch_pm25_col else f"{city_batch[batch_pm25_col].mean():.2f}")
        c3.metric("Max CAMS PM2.5", "-" if not batch_pm25_col else f"{city_batch[batch_pm25_col].max():.2f}")
        c4.metric("Anomalies", "-" if not batch_anomaly_col else f"{int(city_batch[batch_anomaly_col].sum()):,}")

        if batch_time_col and batch_pm25_col:
            fig_batch_trend = px.line(
                city_batch,
                x=batch_time_col,
                y=batch_pm25_col,
                title=f"CAMS PM2.5 Trend in {selected_batch_city}",
                labels={batch_time_col: "Time", batch_pm25_col: "CAMS PM2.5"},
            )
            st.plotly_chart(fig_batch_trend, use_container_width=True)

        if batch_time_col and prediction_col:
            fig_pred = go.Figure()
            if batch_pm25_col:
                fig_pred.add_trace(go.Scatter(x=city_batch[batch_time_col], y=city_batch[batch_pm25_col], mode="lines", name="CAMS PM2.5"))
            fig_pred.add_trace(go.Scatter(x=city_batch[batch_time_col], y=city_batch[prediction_col], mode="lines", name="Predicted PM2.5"))
            fig_pred.update_layout(title=f"CAMS PM2.5 vs ML Prediction in {selected_batch_city}", xaxis_title="Time", yaxis_title="PM2.5", height=520)
            st.plotly_chart(fig_pred, use_container_width=True)

            if batch_pm25_col:
                temp_error = city_batch[[batch_time_col, batch_pm25_col, prediction_col]].dropna().copy()
                temp_error["prediction_error"] = (temp_error[batch_pm25_col] - temp_error[prediction_col]).abs()
                fig_error = px.histogram(
                    temp_error,
                    x="prediction_error",
                    nbins=30,
                    title=f"Batch Prediction Error Distribution in {selected_batch_city}",
                    labels={"prediction_error": "|CAMS PM2.5 - Predicted PM2.5|"},
                )
                st.plotly_chart(fig_error, use_container_width=True)

                avg_error = temp_error["prediction_error"].mean()
                if avg_error <= 10:
                    safe_box(f"✅ Model prediction is close to CAMS PM2.5 in <b>{selected_batch_city}</b>. Average error is <b>{avg_error:.2f}</b>.")
                elif avg_error <= 25:
                    insight_box(f"📌 Model prediction has moderate deviation in <b>{selected_batch_city}</b>. Average error is <b>{avg_error:.2f}</b>.")
                else:
                    alert_box(f"⚠️ Model prediction differs significantly in <b>{selected_batch_city}</b>. Average error is <b>{avg_error:.2f}</b>.")

        with st.expander("View batch detail data"):
            st.dataframe(city_batch.tail(300), use_container_width=True)

# ============================================================
# TAB 3 — REALTIME STREAM
# ============================================================
with tab_stream:
    render_section("Realtime Open-Meteo Stream Monitoring")
    if filtered_stream_data.empty:
        st.warning("Stream data is empty. Run stream producer and consumer first.")
    else:
        latest_stream = latest_per_city(filtered_stream_data, "city", stream_time_col)

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Stream Records", f"{len(filtered_stream_data):,}")
        c2.metric("Cities", filtered_stream_data["city"].nunique())
        c3.metric("Latest Avg PM2.5", "-" if latest_stream.empty or not stream_pm25_col else f"{latest_stream[stream_pm25_col].mean():.2f}")
        c4.metric("Latest Max PM2.5", "-" if latest_stream.empty or not stream_pm25_col else f"{latest_stream[stream_pm25_col].max():.2f}")
        c5.metric("Stream Anomalies", "-" if not stream_anomaly_col else f"{int(filtered_stream_data[stream_anomaly_col].sum()):,}")

        render_section("Latest Stream Data per City")
        st.dataframe(latest_stream, use_container_width=True)

        if stream_pm25_col:
            temp = latest_stream.copy()
            temp["status"] = temp[stream_pm25_col].apply(lambda value: get_air_quality_status(value)[0])
            fig_latest = px.bar(
                temp.sort_values(stream_pm25_col, ascending=False),
                x="city",
                y=stream_pm25_col,
                color="status",
                title="Latest PM2.5 from Open-Meteo Stream",
                labels={"city": "City", stream_pm25_col: "PM2.5", "status": "Status"},
            )
            st.plotly_chart(fig_latest, use_container_width=True)

        if stream_aqi_col:
            temp_aqi = latest_stream.copy()
            temp_aqi["aqi_category"] = temp_aqi[stream_aqi_col].apply(calculate_aqi_category)
            fig_aqi = px.bar(
                temp_aqi.sort_values(stream_aqi_col, ascending=False),
                x="city",
                y=stream_aqi_col,
                color="aqi_category",
                title="Latest AQI by City",
                labels={"city": "City", stream_aqi_col: "AQI"},
            )
            st.plotly_chart(fig_aqi, use_container_width=True)

        render_section("Realtime Trend by City")
        selected_stream_city = st.selectbox("Select stream city", sorted(filtered_stream_data["city"].dropna().unique()), key="stream_detail_city")
        city_stream = filtered_stream_data[filtered_stream_data["city"] == selected_stream_city].copy()
        if stream_time_col:
            city_stream = city_stream.sort_values(stream_time_col)

        pollutants = []
        for col in [stream_pm25_col, stream_pm10_col, "carbon_monoxide", "nitrogen_dioxide", "sulphur_dioxide", "ozone"]:
            if col and col in city_stream.columns and col not in pollutants:
                pollutants.append(col)

        selected_pollutants = st.multiselect(
            "Select stream metrics",
            options=pollutants,
            default=pollutants[:2] if len(pollutants) >= 2 else pollutants,
        )
        if stream_time_col and selected_pollutants:
            fig_pollutants = px.line(
                city_stream,
                x=stream_time_col,
                y=selected_pollutants,
                title=f"Realtime Pollutant Trend in {selected_stream_city}",
                labels={stream_time_col: "Time", "value": "Concentration", "variable": "Metric"},
            )
            st.plotly_chart(fig_pollutants, use_container_width=True)

        if stream_pm25_col:
            fig_dist = px.histogram(
                city_stream,
                x=stream_pm25_col,
                nbins=30,
                title=f"Stream PM2.5 Distribution in {selected_stream_city}",
                labels={stream_pm25_col: "PM2.5"},
            )
            st.plotly_chart(fig_dist, use_container_width=True)

        if stream_anomaly_col:
            anomaly_stream = filtered_stream_data[filtered_stream_data[stream_anomaly_col] == True]
            if anomaly_stream.empty:
                safe_box("✅ No realtime stream anomaly is currently detected in the selected period.")
            else:
                worst = anomaly_stream.loc[anomaly_stream[stream_pm25_col].idxmax()] if stream_pm25_col else anomaly_stream.iloc[0]
                alert_box(
                    f"⚠️ Stream anomaly detected: <b>{len(anomaly_stream)}</b> anomaly records found. "
                    f"The highest anomaly is in <b>{worst['city']}</b>."
                )

        with st.expander("View stream raw data"):
            st.dataframe(filtered_stream_data.head(500), use_container_width=True)

# ============================================================
# TAB 4 — BATCH VS STREAM
# ============================================================
with tab_compare:
    render_section("Batch Prediction vs Stream Actual PM2.5")
    if filtered_batch_data.empty or filtered_stream_data.empty:
        st.warning("Batch and stream data must both be available for comparison.")
    elif not prediction_col or not stream_pm25_col:
        st.warning("Prediction column or stream PM2.5 column is missing.")
    else:
        latest_batch = latest_per_city(filtered_batch_data, "city", batch_time_col)
        latest_stream = latest_per_city(filtered_stream_data, "city", stream_time_col)

        batch_cols = ["city", prediction_col]
        if batch_time_col:
            batch_cols.append(batch_time_col)
        if batch_pm25_col:
            batch_cols.append(batch_pm25_col)
        stream_cols = ["city", stream_pm25_col]
        if stream_time_col:
            stream_cols.append(stream_time_col)
        if stream_aqi_col:
            stream_cols.append(stream_aqi_col)

        latest_batch_compare = latest_batch[batch_cols].copy()
        latest_stream_compare = latest_stream[stream_cols].copy()

        rename_batch = {prediction_col: "predicted_pm25"}
        if batch_time_col:
            rename_batch[batch_time_col] = "batch_time"
        if batch_pm25_col:
            rename_batch[batch_pm25_col] = "batch_cams_pm25"
        rename_stream = {stream_pm25_col: "actual_pm25"}
        if stream_time_col:
            rename_stream[stream_time_col] = "stream_time"
        if stream_aqi_col:
            rename_stream[stream_aqi_col] = "stream_aqi"

        compare_df = pd.merge(
            latest_batch_compare.rename(columns=rename_batch),
            latest_stream_compare.rename(columns=rename_stream),
            on="city",
            how="inner",
        )

        if compare_df.empty:
            st.warning("No matching city found between batch and stream data.")
        else:
            compare_df["error"] = compare_df["actual_pm25"] - compare_df["predicted_pm25"]
            compare_df["absolute_error"] = compare_df["error"].abs()
            compare_df["error_percentage"] = np.where(compare_df["actual_pm25"] != 0, (compare_df["absolute_error"] / compare_df["actual_pm25"]) * 100, np.nan)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Compared Cities", compare_df["city"].nunique())
            c2.metric("Avg Absolute Error", f"{compare_df['absolute_error'].mean():.2f}")
            c3.metric("Max Absolute Error", f"{compare_df['absolute_error'].max():.2f}")
            c4.metric("Avg Error %", f"{compare_df['error_percentage'].mean():.2f}%")

            st.dataframe(compare_df, use_container_width=True)

            fig_compare = go.Figure()
            fig_compare.add_trace(go.Bar(x=compare_df["city"], y=compare_df["predicted_pm25"], name="Batch Predicted PM2.5"))
            fig_compare.add_trace(go.Bar(x=compare_df["city"], y=compare_df["actual_pm25"], name="Stream Actual PM2.5"))
            fig_compare.update_layout(
                title="Predicted PM2.5 from Batch Model vs Actual PM2.5 from Stream",
                xaxis_title="City",
                yaxis_title="PM2.5",
                barmode="group",
                height=520,
            )
            st.plotly_chart(fig_compare, use_container_width=True)

            col_a, col_b = st.columns(2)
            with col_a:
                fig_error = px.bar(
                    compare_df.sort_values("absolute_error", ascending=False),
                    x="city",
                    y="absolute_error",
                    title="Absolute Error by City",
                    labels={"city": "City", "absolute_error": "|Actual - Predicted|"},
                )
                st.plotly_chart(fig_error, use_container_width=True)
            with col_b:
                fig_scatter = px.scatter(
                    compare_df,
                    x="actual_pm25",
                    y="predicted_pm25",
                    text="city",
                    title="Actual vs Predicted PM2.5",
                    labels={"actual_pm25": "Stream Actual PM2.5", "predicted_pm25": "Batch Predicted PM2.5"},
                )
                min_axis = min(compare_df["actual_pm25"].min(), compare_df["predicted_pm25"].min())
                max_axis = max(compare_df["actual_pm25"].max(), compare_df["predicted_pm25"].max())
                fig_scatter.add_trace(go.Scatter(x=[min_axis, max_axis], y=[min_axis, max_axis], mode="lines", name="Ideal Prediction", line=dict(dash="dash")))
                st.plotly_chart(fig_scatter, use_container_width=True)

            best = compare_df.loc[compare_df["absolute_error"].idxmin()]
            worst = compare_df.loc[compare_df["absolute_error"].idxmax()]
            insight_box(
                f"📌 The closest batch prediction to stream actual PM2.5 is found in <b>{best['city']}</b> "
                f"with absolute error <b>{best['absolute_error']:.2f}</b>. The largest prediction gap occurs "
                f"in <b>{worst['city']}</b> with absolute error <b>{worst['absolute_error']:.2f}</b>."
            )
            warning_box("Interpretation note: comparison uses latest city-level records. For stricter evaluation, align timestamps by nearest hour.")

# ============================================================
# TAB 5 — ANOMALY CENTER
# ============================================================
with tab_anomaly:
    render_section("Anomaly Monitoring Center")
    col_batch, col_stream = st.columns(2)

    with col_batch:
        render_mini_title("Batch Anomaly Summary")
        if summary_anomaly_col and not filtered_batch_summary.empty:
            fig = px.bar(
                filtered_batch_summary.sort_values(summary_anomaly_col, ascending=False),
                x="city",
                y=summary_anomaly_col,
                title="Batch Anomaly Count by City",
                labels={"city": "City", summary_anomaly_col: "Anomaly Count"},
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(filtered_batch_summary[["city", summary_anomaly_col]].sort_values(summary_anomaly_col, ascending=False), use_container_width=True, hide_index=True)
        elif batch_anomaly_col and not filtered_batch_data.empty:
            batch_anomaly_summary = filtered_batch_data.groupby("city")[batch_anomaly_col].sum().reset_index(name="anomaly_count").sort_values("anomaly_count", ascending=False)
            fig = px.bar(batch_anomaly_summary, x="city", y="anomaly_count", title="Batch Anomaly Count by City")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(batch_anomaly_summary, use_container_width=True, hide_index=True)
        else:
            st.info("No batch anomaly data available.")

    with col_stream:
        render_mini_title("Stream Anomaly Summary")
        if stream_anomaly_col and not filtered_stream_data.empty:
            stream_anomaly_summary = filtered_stream_data.groupby("city")[stream_anomaly_col].sum().reset_index(name="anomaly_count").sort_values("anomaly_count", ascending=False)
            fig = px.bar(
                stream_anomaly_summary,
                x="city",
                y="anomaly_count",
                title="Stream Anomaly Count by City",
                labels={"city": "City", "anomaly_count": "Anomaly Count"},
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(stream_anomaly_summary, use_container_width=True, hide_index=True)
        else:
            st.info("No stream anomaly data available.")

    render_section("Anomaly Detail")
    anomaly_tab_batch, anomaly_tab_stream = st.tabs(["Batch Anomaly Detail", "Stream Anomaly Detail"])

    with anomaly_tab_batch:
        if batch_anomaly_col and not filtered_batch_data.empty:
            batch_anomaly_detail = filtered_batch_data[filtered_batch_data[batch_anomaly_col] == True]
            if batch_anomaly_detail.empty:
                safe_box("✅ No batch anomaly records in the selected filter.")
            else:
                st.dataframe(batch_anomaly_detail.tail(300), use_container_width=True)
                if batch_time_col and batch_pm25_col:
                    fig = px.scatter(batch_anomaly_detail, x=batch_time_col, y=batch_pm25_col, color="city", title="Batch Anomaly Events")
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Batch anomaly detail column is not available.")

    with anomaly_tab_stream:
        if stream_anomaly_col and not filtered_stream_data.empty:
            stream_anomaly_detail = filtered_stream_data[filtered_stream_data[stream_anomaly_col] == True]
            if stream_anomaly_detail.empty:
                safe_box("✅ No stream anomaly records in the selected filter.")
            else:
                display_cols = ["city"]
                if stream_time_col:
                    display_cols.append(stream_time_col)
                for col in [stream_pm25_col, stream_pm10_col, stream_aqi_col, stream_reason_col]:
                    if col and col in stream_anomaly_detail.columns:
                        display_cols.append(col)
                st.dataframe(stream_anomaly_detail[display_cols].tail(300), use_container_width=True)
                if stream_time_col and stream_pm25_col:
                    fig = px.scatter(
                        stream_anomaly_detail,
                        x=stream_time_col,
                        y=stream_pm25_col,
                        color="city",
                        hover_data=[stream_reason_col] if stream_reason_col else None,
                        title="Stream Anomaly Events",
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Stream anomaly detail column is not available.")

# ============================================================
# TAB 6 — DATA EXPLORER
# ============================================================
with tab_data:
    render_section("Data Explorer")
    selected_dataset = st.radio("Select dataset", ["Batch Summary", "Batch Detail", "Stream Detail"], horizontal=True)

    if selected_dataset == "Batch Summary":
        st.dataframe(filtered_batch_summary, use_container_width=True)
        csv = filtered_batch_summary.to_csv(index=False).encode("utf-8")
        st.download_button("Download Batch Summary CSV", csv, "batch_summary.csv", "text/csv")
    elif selected_dataset == "Batch Detail":
        st.dataframe(filtered_batch_data.tail(1000), use_container_width=True)
        csv = filtered_batch_data.to_csv(index=False).encode("utf-8")
        st.download_button("Download Batch Detail CSV", csv, "batch_detail.csv", "text/csv")
    else:
        st.dataframe(filtered_stream_data.head(1000), use_container_width=True)
        csv = filtered_stream_data.to_csv(index=False).encode("utf-8")
        st.download_button("Download Stream Detail CSV", csv, "stream_detail.csv", "text/csv")

    render_section("Column Information")
    col1, col2, col3 = st.columns(3)
    with col1:
        render_mini_title("city_air_quality_summary")
        st.write(get_table_columns("city_air_quality_summary"))
    with col2:
        render_mini_title("cams_air_quality_data")
        st.write(get_table_columns("cams_air_quality_data"))
    with col3:
        render_mini_title("air_quality_stream")
        st.write(get_table_columns("air_quality_stream"))

# ============================================================
# TAB 7 — SYSTEM HEALTH
# ============================================================
with tab_health:
    render_section("System Health and Reproducibility")
    st.markdown(
        """
        This section summarizes operational status from PostgreSQL tables. It supports demonstration of
        monitoring, reproducibility, and pipeline validation.
        """
    )
    st.dataframe(table_status, hide_index=True, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        render_mini_title("Batch Coverage")
        st.write(f"Date range: `{format_date_range(batch_data, batch_time_col)}`")
        st.write(f"Rows: `{len(batch_data):,}`")
        if "city" in batch_data.columns:
            st.write(f"Cities: `{', '.join(sorted(batch_data['city'].dropna().unique()))}`")
    with col2:
        render_mini_title("Stream Coverage")
        st.write(f"Date range: `{format_date_range(stream_data, stream_time_col)}`")
        st.write(f"Rows: `{len(stream_data):,}`")
        if "city" in stream_data.columns:
            st.write(f"Cities: `{', '.join(sorted(stream_data['city'].dropna().unique()))}`")
    with col3:
        render_mini_title("Connection")
        st.write(f"Database: `{DB_NAME}`")
        st.write(f"Host: `{DB_HOST}`")
        st.write(f"Port: `{DB_PORT}`")

    render_section("Recommended Demo Flow")
    st.markdown(
        """
        1. Open Dagster and show successful batch materialization.  
        2. Show Telegram anomaly and success alert.  
        3. Show PostgreSQL tables: `cams_air_quality_data`, `city_air_quality_summary`, and `air_quality_stream`.  
        4. Run or restart stream producer and consumer.  
        5. Refresh this dashboard and show realtime stream updates.  
        6. Present the Batch vs Stream tab to compare predicted PM2.5 with actual Open-Meteo stream data.
        """
    )
    warning_box("Security note: PostgreSQL and Kafka should remain internal. Only expose SSH, Dagster, and Streamlit dashboard ports for demo.")

# ============================================================
# FOOTER
# ============================================================
st.markdown(
    """
    <div class="footer-note">
    Dashboard sources: Copernicus CAMS batch data, Open-Meteo realtime stream data, PostgreSQL storage,
    Dagster orchestration, Kafka stream processing, and Telegram alerting.
    </div>
    """,
    unsafe_allow_html=True,
)
