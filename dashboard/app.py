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
    initial_sidebar_state="collapsed",
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
LOCAL_TIMEZONE = "Asia/Jakarta"

QUALITY_COLOR_MAP = {
    "Good": "#2ECC71",       # hijau
    "Moderate": "#3498DB",   # biru
    "Unhealthy": "#E74C3C",  # merah
    "Hazardous": "#FF69B4",  # pink
    "Unknown": "#95A5A6",
}
QUALITY_ORDER = ["Good", "Moderate", "Unhealthy", "Hazardous", "Unknown"]

# ============================================================
# CUSTOM STYLE
# ============================================================
st.markdown(
    """
    <style>
    [data-testid="stSidebar"], [data-testid="collapsedControl"] {
        display: none;
    }
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
        return "Moderate", "🔵"
    if pm25 <= 75:
        return "Unhealthy", "🔴"
    return "Hazardous", "🩷"


def calculate_aqi_category(aqi):
    if pd.isna(aqi):
        return "Unknown"
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Moderate"
    if aqi <= 200:
        return "Unhealthy"
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
    if df.empty:
        return df
    for col in cols:
        if col and col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def safe_datetime(df, cols):
    if df.empty:
        return df
    for col in cols:
        if col and col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def to_wib_datetime(series):
    """Convert database timestamps to WIB display time.

    PostgreSQL created_at biasanya tersimpan dalam UTC di container. Karena itu stream dashboard
    memakai created_at -> WIB agar waktu dashboard sama dengan waktu proses real di Telegram/demo.
    """
    parsed = pd.to_datetime(series, errors="coerce", utc=True)
    return parsed.dt.tz_convert(LOCAL_TIMEZONE).dt.tz_localize(None)


def format_wib(value):
    if pd.isna(value):
        return "-"
    return pd.to_datetime(value).strftime("%Y-%m-%d %H:%M WIB")


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
    return temp[(temp[time_col].dt.date >= start_date) & (temp[time_col].dt.date <= end_date)].copy()


def gather_dates(df_col_pairs):
    dates = []
    for df, col in df_col_pairs:
        if df is not None and not df.empty and col and col in df.columns:
            dates.extend(df[col].dropna().dt.date.tolist())
    return dates


def render_tab_filters(key_prefix, city_source_dfs=None, date_sources=None, show_city=True):
    city_source_dfs = city_source_dfs or []
    date_sources = date_sources or []

    cities = set()
    for df in city_source_dfs:
        if df is not None and not df.empty and "city" in df.columns:
            cities.update(df["city"].dropna().tolist())
    if not cities:
        cities = set(TARGET_CITIES)
    cities = sorted(cities)

    dates = gather_dates(date_sources)
    min_date = min(dates) if dates else date.today()
    max_date = max(dates) if dates else date.today()

    render_mini_title("Filter")
    if show_city:
        col_city, col_date = st.columns([1, 2])
        with col_city:
            selected_cities = st.multiselect(
                "Cities",
                cities,
                default=cities,
                key=f"{key_prefix}_cities",
            )
        with col_date:
            selected_range = st.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key=f"{key_prefix}_date_range",
            )
    else:
        selected_cities = cities
        selected_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key=f"{key_prefix}_date_range",
        )

    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        start_date, end_date = selected_range
    else:
        start_date, end_date = min_date, max_date

    return selected_cities, start_date, end_date


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


def add_status_column(df, pm_col):
    temp = df.copy()
    if pm_col and pm_col in temp.columns:
        temp["status"] = temp[pm_col].apply(lambda value: get_air_quality_status(value)[0])
    else:
        temp["status"] = "Unknown"
    return temp


def filtered_summary_from_detail(summary_df, detail_df, selected_cities, summary_cols):
    """Prefer date-filtered detail aggregation over static summary when detail is available."""
    avg_col, max_col, pred_col, anom_col, pm_col, pred_detail_col, anom_detail_col = summary_cols
    if detail_df.empty or "city" not in detail_df.columns or not pm_col:
        return filter_by_cities(summary_df, selected_cities)

    agg = detail_df.groupby("city").agg(
        average_pm25=(pm_col, "mean"),
        max_pm25=(pm_col, "max"),
    ).reset_index()

    if pred_detail_col and pred_detail_col in detail_df.columns:
        pred_agg = detail_df.groupby("city")[pred_detail_col].mean().reset_index(name="avg_prediction")
        agg = agg.merge(pred_agg, on="city", how="left")

    if anom_detail_col and anom_detail_col in detail_df.columns:
        anom_agg = detail_df.groupby("city")[anom_detail_col].sum().reset_index(name="anomaly_count")
        agg = agg.merge(anom_agg, on="city", how="left")
    else:
        agg["anomaly_count"] = 0

    return add_city_coordinates(agg)


def anomaly_rate_summary(df, anomaly_col):
    if df.empty or not anomaly_col or anomaly_col not in df.columns or "city" not in df.columns:
        return pd.DataFrame()
    temp = df.groupby("city").agg(
        total_records=(anomaly_col, "count"),
        anomaly_count=(anomaly_col, "sum"),
    ).reset_index()
    temp["anomaly_rate_pct"] = np.where(temp["total_records"] > 0, temp["anomaly_count"] / temp["total_records"] * 100, 0)
    return temp.sort_values("anomaly_rate_pct", ascending=False)

# ============================================================
# LOAD TABLES
# ============================================================
batch_summary = read_sql("SELECT * FROM city_air_quality_summary;") if table_exists("city_air_quality_summary") else pd.DataFrame()
batch_data = read_sql("SELECT * FROM cams_air_quality_data;") if table_exists("cams_air_quality_data") else pd.DataFrame()
stream_data = read_sql("SELECT * FROM air_quality_stream;") if table_exists("air_quality_stream") else pd.DataFrame()

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

# Stream charts use insert/process time in WIB, not the API hourly timestamp.
# This fixes mismatch such as API timestamp 21:00 while the pipeline actually ran at 20:50 WIB.
STREAM_DISPLAY_TIME_COL = None
if not stream_data.empty:
    if stream_created_col and stream_created_col in stream_data.columns:
        stream_data["stream_time_wib"] = to_wib_datetime(stream_data[stream_created_col])
        STREAM_DISPLAY_TIME_COL = "stream_time_wib"
    elif stream_time_col and stream_time_col in stream_data.columns:
        stream_data["stream_time_wib"] = to_wib_datetime(stream_data[stream_time_col])
        STREAM_DISPLAY_TIME_COL = "stream_time_wib"

batch_data = safe_numeric(batch_data, [batch_pm25_col, batch_pm10_col, prediction_col])
stream_data = safe_numeric(
    stream_data,
    [
        stream_pm25_col,
        stream_pm10_col,
        stream_aqi_col,
        "carbon_monoxide",
        "nitrogen_dioxide",
        "sulphur_dioxide",
        "ozone",
        "latitude",
        "longitude",
    ],
)
batch_summary = safe_numeric(batch_summary, [summary_avg_col, summary_max_col, summary_pred_col, summary_anomaly_col])

if batch_anomaly_col and batch_anomaly_col in batch_data.columns:
    batch_data[batch_anomaly_col] = normalize_bool(batch_data[batch_anomaly_col])
if stream_anomaly_col and stream_anomaly_col in stream_data.columns:
    stream_data[stream_anomaly_col] = normalize_bool(stream_data[stream_anomaly_col])

batch_summary = add_city_coordinates(batch_summary)
batch_data = add_city_coordinates(batch_data)
stream_data = add_city_coordinates(stream_data)

if not batch_data.empty and batch_time_col:
    batch_data = batch_data.sort_values(["city", batch_time_col] if "city" in batch_data.columns else [batch_time_col])
if not stream_data.empty and STREAM_DISPLAY_TIME_COL:
    stream_data = stream_data.sort_values(["city", STREAM_DISPLAY_TIME_COL] if "city" in stream_data.columns else [STREAM_DISPLAY_TIME_COL])

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

if st.button("🔄 Refresh Dashboard"):
    st.cache_data.clear()
    st.rerun()

table_status = get_table_status()
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
    selected_cities, start_date, end_date = render_tab_filters(
        "overview",
        city_source_dfs=[batch_summary, batch_data, stream_data],
        date_sources=[(batch_data, batch_time_col), (stream_data, STREAM_DISPLAY_TIME_COL)],
    )

    filtered_batch_data = filter_by_date(filter_by_cities(batch_data, selected_cities), batch_time_col, start_date, end_date)
    filtered_stream_data = filter_by_date(filter_by_cities(stream_data, selected_cities), STREAM_DISPLAY_TIME_COL, start_date, end_date)
    filtered_batch_summary = filtered_summary_from_detail(
        batch_summary,
        filtered_batch_data,
        selected_cities,
        (summary_avg_col, summary_max_col, summary_pred_col, summary_anomaly_col, batch_pm25_col, prediction_col, batch_anomaly_col),
    )

    latest_stream = latest_per_city(filtered_stream_data, "city", STREAM_DISPLAY_TIME_COL)
    latest_batch = latest_per_city(filtered_batch_data, "city", batch_time_col)

    total_batch_anomalies = int(filtered_batch_data[batch_anomaly_col].sum()) if not filtered_batch_data.empty and batch_anomaly_col else 0
    total_stream_anomalies = int(filtered_stream_data[stream_anomaly_col].sum()) if not filtered_stream_data.empty and stream_anomaly_col else 0

    avg_batch_pm25 = filtered_batch_data[batch_pm25_col].mean() if not filtered_batch_data.empty and batch_pm25_col else np.nan
    latest_stream_avg = latest_stream[stream_pm25_col].mean() if not latest_stream.empty and stream_pm25_col else np.nan
    latest_stream_time = latest_stream[STREAM_DISPLAY_TIME_COL].max() if not latest_stream.empty and STREAM_DISPLAY_TIME_COL else np.nan

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Cities Monitored", len(selected_cities))
    c2.metric("Batch Records", f"{len(filtered_batch_data):,}")
    c3.metric("Stream Records", f"{len(filtered_stream_data):,}")
    c4.metric("Batch Anomalies", f"{total_batch_anomalies:,}")
    c5.metric("Stream Anomalies", f"{total_stream_anomalies:,}")

    c6, c7, c8 = st.columns(3)
    c6.metric("Batch Avg PM2.5", "-" if pd.isna(avg_batch_pm25) else f"{avg_batch_pm25:.2f} µg/m³")
    c7.metric("Latest Stream Avg PM2.5", "-" if pd.isna(latest_stream_avg) else f"{latest_stream_avg:.2f} µg/m³")
    c8.metric("Latest Stream Time", format_wib(latest_stream_time))

    render_section("Integrated Monitoring Map")
    map_frames = []
    if not filtered_batch_summary.empty and "average_pm25" in filtered_batch_summary.columns:
        batch_map = filtered_batch_summary[["city", "latitude", "longitude", "average_pm25"]].copy()
        batch_map = batch_map.rename(columns={"average_pm25": "pm25"})
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
            category_orders={"status": QUALITY_ORDER},
            color_discrete_map=QUALITY_COLOR_MAP,
        )
        fig_map.update_layout(mapbox_style="open-street-map", margin={"r": 0, "t": 45, "l": 0, "b": 0})
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("Map data is not available yet.")

    render_section("Quick Comparison")
    col_left, col_right = st.columns(2)
    with col_left:
        if not filtered_batch_summary.empty and "average_pm25" in filtered_batch_summary.columns:
            temp = add_status_column(filtered_batch_summary, "average_pm25")
            fig = px.bar(
                temp.sort_values("average_pm25", ascending=False),
                x="city",
                y="average_pm25",
                color="status",
                title="Batch Average PM2.5 by City",
                labels={"city": "City", "average_pm25": "Average PM2.5"},
                category_orders={"status": QUALITY_ORDER},
                color_discrete_map=QUALITY_COLOR_MAP,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Batch summary is unavailable for this date range.")
    with col_right:
        if not latest_stream.empty and stream_pm25_col:
            temp = add_status_column(latest_stream, stream_pm25_col)
            fig = px.bar(
                temp.sort_values(stream_pm25_col, ascending=False),
                x="city",
                y=stream_pm25_col,
                color="status",
                title="Latest Stream PM2.5 by City",
                labels={"city": "City", stream_pm25_col: "Latest PM2.5"},
                category_orders={"status": QUALITY_ORDER},
                color_discrete_map=QUALITY_COLOR_MAP,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Latest stream data is unavailable for this date range.")

    render_section("Narrative Insights")
    if not filtered_batch_summary.empty and "average_pm25" in filtered_batch_summary.columns:
        highest = filtered_batch_summary.loc[filtered_batch_summary["average_pm25"].idxmax()]
        lowest = filtered_batch_summary.loc[filtered_batch_summary["average_pm25"].idxmin()]
        insight_box(
            f"📌 Pada rentang tanggal terpilih, CAMS batch menunjukkan <b>{highest['city']}</b> memiliki rata-rata PM2.5 tertinggi "
            f"(<b>{highest['average_pm25']:.2f} µg/m³</b>), sedangkan <b>{lowest['city']}</b> paling rendah "
            f"(<b>{lowest['average_pm25']:.2f} µg/m³</b>)."
        )
    if not latest_stream.empty and stream_pm25_col:
        worst_stream = latest_stream.loc[latest_stream[stream_pm25_col].idxmax()]
        status, icon = get_air_quality_status(worst_stream[stream_pm25_col])
        box_func = alert_box if status in ["Unhealthy", "Hazardous"] else safe_box
        box_func(
            f"{icon} Data stream Open-Meteo terbaru berdasarkan waktu proses WIB menunjukkan <b>{worst_stream['city']}</b> "
            f"memiliki PM2.5 tertinggi (<b>{worst_stream[stream_pm25_col]:.2f} µg/m³</b>), kategori <b>{status}</b>."
        )

# ============================================================
# TAB 2 — BATCH CAMS ANALYSIS
# ============================================================
with tab_batch:
    render_section("Batch CAMS Processing Output")
    selected_cities, start_date, end_date = render_tab_filters(
        "batch",
        city_source_dfs=[batch_summary, batch_data],
        date_sources=[(batch_data, batch_time_col)],
    )
    filtered_batch_data = filter_by_date(filter_by_cities(batch_data, selected_cities), batch_time_col, start_date, end_date)
    filtered_batch_summary = filtered_summary_from_detail(
        batch_summary,
        filtered_batch_data,
        selected_cities,
        (summary_avg_col, summary_max_col, summary_pred_col, summary_anomaly_col, batch_pm25_col, prediction_col, batch_anomaly_col),
    )

    if filtered_batch_data.empty and filtered_batch_summary.empty:
        st.warning("Batch data is empty in the selected date range. Run the Dagster batch pipeline first or adjust the date range.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Batch Cities", filtered_batch_data["city"].nunique() if "city" in filtered_batch_data.columns else 0)
        c2.metric("Avg CAMS PM2.5", "-" if filtered_batch_data.empty or not batch_pm25_col else f"{filtered_batch_data[batch_pm25_col].mean():.2f}")
        c3.metric("Max CAMS PM2.5", "-" if filtered_batch_data.empty or not batch_pm25_col else f"{filtered_batch_data[batch_pm25_col].max():.2f}")
        c4.metric("Batch Anomalies", "-" if filtered_batch_data.empty or not batch_anomaly_col else f"{int(filtered_batch_data[batch_anomaly_col].sum()):,}")

        if not filtered_batch_summary.empty:
            st.dataframe(filtered_batch_summary, use_container_width=True)

        if not filtered_batch_summary.empty and "average_pm25" in filtered_batch_summary.columns:
            temp = add_status_column(filtered_batch_summary, "average_pm25")
            fig_rank = px.bar(
                temp.sort_values("average_pm25", ascending=False),
                x="city",
                y="average_pm25",
                color="status",
                title="Average PM2.5 Ranking from CAMS Batch Data",
                labels={"city": "City", "average_pm25": "Average PM2.5"},
                category_orders={"status": QUALITY_ORDER},
                color_discrete_map=QUALITY_COLOR_MAP,
            )
            st.plotly_chart(fig_rank, use_container_width=True)

        if not filtered_batch_summary.empty and "max_pm25" in filtered_batch_summary.columns:
            temp_max = add_status_column(filtered_batch_summary, "max_pm25")
            fig_max = px.bar(
                temp_max.sort_values("max_pm25", ascending=False),
                x="city",
                y="max_pm25",
                color="status",
                title="Maximum PM2.5 by City from CAMS Batch Data",
                labels={"city": "City", "max_pm25": "Maximum PM2.5"},
                category_orders={"status": QUALITY_ORDER},
                color_discrete_map=QUALITY_COLOR_MAP,
            )
            st.plotly_chart(fig_max, use_container_width=True)

        if not filtered_batch_summary.empty and "anomaly_count" in filtered_batch_summary.columns:
            fig_anom = px.bar(
                filtered_batch_summary.sort_values("anomaly_count", ascending=False),
                x="city",
                y="anomaly_count",
                title="Batch Anomaly Count by City",
                labels={"city": "City", "anomaly_count": "Anomaly Count"},
            )
            st.plotly_chart(fig_anom, use_container_width=True)

    render_section("Batch Detail Trend")
    if filtered_batch_data.empty:
        st.warning("Batch detail data is empty in the selected date range.")
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
            fig_batch_trend.update_traces(mode="lines+markers")
            st.plotly_chart(fig_batch_trend, use_container_width=True)

        if batch_time_col and batch_pm10_col:
            fig_batch_pm10 = px.line(
                city_batch,
                x=batch_time_col,
                y=batch_pm10_col,
                title=f"CAMS PM10 Trend in {selected_batch_city}",
                labels={batch_time_col: "Time", batch_pm10_col: "CAMS PM10"},
            )
            fig_batch_pm10.update_traces(mode="lines+markers")
            st.plotly_chart(fig_batch_pm10, use_container_width=True)

        insight_box(
            "📌 Tab ini hanya menampilkan analisis batch CAMS. Perbandingan ML prediction dengan data realtime Open-Meteo dipindahkan ke tab <b>Batch vs Stream</b> agar konteksnya tidak tercampur."
        )

        with st.expander("View batch detail data"):
            st.dataframe(city_batch.tail(300), use_container_width=True)

# ============================================================
# TAB 3 — REALTIME STREAM
# ============================================================
with tab_stream:
    render_section("Realtime Open-Meteo Stream Monitoring")
    selected_cities, start_date, end_date = render_tab_filters(
        "stream",
        city_source_dfs=[stream_data],
        date_sources=[(stream_data, STREAM_DISPLAY_TIME_COL)],
    )
    filtered_stream_data = filter_by_date(filter_by_cities(stream_data, selected_cities), STREAM_DISPLAY_TIME_COL, start_date, end_date)

    if filtered_stream_data.empty:
        st.warning("Stream data is empty in the selected date range. Run stream producer and consumer first or adjust the date range.")
    else:
        latest_stream = latest_per_city(filtered_stream_data, "city", STREAM_DISPLAY_TIME_COL)

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Stream Records", f"{len(filtered_stream_data):,}")
        c2.metric("Cities", filtered_stream_data["city"].nunique())
        c3.metric("Latest Avg PM2.5", "-" if latest_stream.empty or not stream_pm25_col else f"{latest_stream[stream_pm25_col].mean():.2f}")
        c4.metric("Latest Max PM2.5", "-" if latest_stream.empty or not stream_pm25_col else f"{latest_stream[stream_pm25_col].max():.2f}")
        c5.metric("Stream Anomalies", "-" if not stream_anomaly_col else f"{int(filtered_stream_data[stream_anomaly_col].sum()):,}")

        if STREAM_DISPLAY_TIME_COL:
            latest_time = latest_stream[STREAM_DISPLAY_TIME_COL].max() if not latest_stream.empty else np.nan
            insight_box(
                f"🕒 Dashboard memakai <b>stream_time_wib</b> dari waktu insert/proses data, bukan timestamp API yang biasanya dibulatkan per jam. Latest stream time: <b>{format_wib(latest_time)}</b>."
            )

        render_section("Latest Stream Data per City")
        st.dataframe(latest_stream, use_container_width=True)

        if stream_pm25_col:
            temp = add_status_column(latest_stream, stream_pm25_col)
            fig_latest = px.bar(
                temp.sort_values(stream_pm25_col, ascending=False),
                x="city",
                y=stream_pm25_col,
                color="status",
                title="Latest PM2.5 from Open-Meteo Stream",
                labels={"city": "City", stream_pm25_col: "PM2.5", "status": "Status"},
                category_orders={"status": QUALITY_ORDER},
                color_discrete_map=QUALITY_COLOR_MAP,
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
                category_orders={"aqi_category": QUALITY_ORDER},
                color_discrete_map=QUALITY_COLOR_MAP,
            )
            st.plotly_chart(fig_aqi, use_container_width=True)

        render_section("Realtime Trend by City")
        selected_stream_city = st.selectbox("Select stream city", sorted(filtered_stream_data["city"].dropna().unique()), key="stream_detail_city")
        city_stream = filtered_stream_data[filtered_stream_data["city"] == selected_stream_city].copy()
        if STREAM_DISPLAY_TIME_COL:
            city_stream = city_stream.sort_values(STREAM_DISPLAY_TIME_COL)

        pollutants = []
        for col in [stream_pm25_col, stream_pm10_col, "carbon_monoxide", "nitrogen_dioxide", "sulphur_dioxide", "ozone", stream_aqi_col]:
            if col and col in city_stream.columns and col not in pollutants:
                pollutants.append(col)

        selected_pollutants = st.multiselect(
            "Select stream metrics",
            options=pollutants,
            default=pollutants[:2] if len(pollutants) >= 2 else pollutants,
            key="stream_pollutant_multiselect",
        )

        if STREAM_DISPLAY_TIME_COL and selected_pollutants:
            fig_pollutants = go.Figure()
            for metric in selected_pollutants:
                fig_pollutants.add_trace(
                    go.Scatter(
                        x=city_stream[STREAM_DISPLAY_TIME_COL],
                        y=city_stream[metric],
                        mode="lines+markers",
                        name=metric,
                    )
                )
            fig_pollutants.update_layout(
                title=f"Realtime Pollutant Trend in {selected_stream_city}",
                xaxis_title="Processing Time (WIB)",
                yaxis_title="Concentration / AQI",
                height=520,
            )
            st.plotly_chart(fig_pollutants, use_container_width=True)

            if city_stream[STREAM_DISPLAY_TIME_COL].nunique() <= 1:
                warning_box(
                    "⚠️ Trend bisa terlihat datar/kosong kalau data realtime baru sedikit atau timestamp API masih sama. "
                    "Open-Meteo current air quality umumnya berubah per jam, sedangkan consumer bisa mengambil data setiap beberapa detik/menit. "
                    "Dashboard sekarang memakai waktu proses WIB agar titik tetap terlihat per cycle."
                )

        if stream_pm25_col:
            fig_dist = px.histogram(
                city_stream,
                x=stream_pm25_col,
                nbins=30,
                title=f"Stream PM2.5 Distribution in {selected_stream_city}",
                labels={stream_pm25_col: "PM2.5"},
            )
            st.plotly_chart(fig_dist, use_container_width=True)

            unique_pm25 = city_stream[stream_pm25_col].dropna().nunique()
            if unique_pm25 <= 2:
                warning_box(
                    f"Distribusi PM2.5 untuk <b>{selected_stream_city}</b> masih terlihat mirip/sangat sempit karena nilai uniknya baru <b>{unique_pm25}</b>. "
                    "Ini normal kalau stream hanya dijalankan beberapa menit, karena API current Open-Meteo sering masih mengembalikan nilai yang sama dalam satu jam. "
                    "Untuk distribusi yang lebih bervariasi, jalankan stream lebih lama atau ambil data lintas beberapa jam."
                )

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
            st.dataframe(filtered_stream_data.tail(500), use_container_width=True)

# ============================================================
# TAB 4 — BATCH VS STREAM
# ============================================================
with tab_compare:
    render_section("Realtime Open-Meteo vs ML Prediction")
    selected_cities, start_date, end_date = render_tab_filters(
        "compare",
        city_source_dfs=[batch_data, stream_data],
        date_sources=[(batch_data, batch_time_col), (stream_data, STREAM_DISPLAY_TIME_COL)],
    )
    filtered_batch_data = filter_by_date(filter_by_cities(batch_data, selected_cities), batch_time_col, start_date, end_date)
    filtered_stream_data = filter_by_date(filter_by_cities(stream_data, selected_cities), STREAM_DISPLAY_TIME_COL, start_date, end_date)

    if filtered_batch_data.empty or filtered_stream_data.empty:
        st.warning("Batch and stream data must both be available in the selected date range for comparison.")
    elif not prediction_col or not stream_pm25_col:
        st.warning("Prediction column or stream PM2.5 column is missing.")
    else:
        latest_batch = latest_per_city(filtered_batch_data, "city", batch_time_col)
        latest_stream = latest_per_city(filtered_stream_data, "city", STREAM_DISPLAY_TIME_COL)

        batch_cols = ["city", prediction_col]
        if batch_time_col:
            batch_cols.append(batch_time_col)
        if batch_pm25_col:
            batch_cols.append(batch_pm25_col)
        stream_cols = ["city", stream_pm25_col]
        if STREAM_DISPLAY_TIME_COL:
            stream_cols.append(STREAM_DISPLAY_TIME_COL)
        if stream_time_col:
            stream_cols.append(stream_time_col)
        if stream_aqi_col:
            stream_cols.append(stream_aqi_col)

        latest_batch_compare = latest_batch[batch_cols].copy()
        latest_stream_compare = latest_stream[stream_cols].copy()

        rename_batch = {prediction_col: "ml_predicted_pm25"}
        if batch_time_col:
            rename_batch[batch_time_col] = "batch_prediction_time"
        if batch_pm25_col:
            rename_batch[batch_pm25_col] = "batch_cams_pm25"
        rename_stream = {stream_pm25_col: "realtime_openmeteo_pm25"}
        if STREAM_DISPLAY_TIME_COL:
            rename_stream[STREAM_DISPLAY_TIME_COL] = "stream_time_wib"
        if stream_time_col:
            rename_stream[stream_time_col] = "api_timestamp"
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
            compare_df["error"] = compare_df["realtime_openmeteo_pm25"] - compare_df["ml_predicted_pm25"]
            compare_df["absolute_error"] = compare_df["error"].abs()
            compare_df["error_percentage"] = np.where(
                compare_df["realtime_openmeteo_pm25"] != 0,
                (compare_df["absolute_error"] / compare_df["realtime_openmeteo_pm25"]) * 100,
                np.nan,
            )

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Compared Cities", compare_df["city"].nunique())
            c2.metric("Avg Absolute Error", f"{compare_df['absolute_error'].mean():.2f}")
            c3.metric("Max Absolute Error", f"{compare_df['absolute_error'].max():.2f}")
            c4.metric("Avg Error %", f"{compare_df['error_percentage'].mean():.2f}%")

            st.dataframe(compare_df, use_container_width=True)

            compare_sorted = compare_df.sort_values("city")
            fig_compare = go.Figure()
            fig_compare.add_trace(
                go.Scatter(
                    x=compare_sorted["city"],
                    y=compare_sorted["realtime_openmeteo_pm25"],
                    mode="lines+markers",
                    name="Realtime Open-Meteo PM2.5",
                )
            )
            fig_compare.add_trace(
                go.Scatter(
                    x=compare_sorted["city"],
                    y=compare_sorted["ml_predicted_pm25"],
                    mode="lines+markers",
                    name="ML Predicted PM2.5",
                )
            )
            fig_compare.update_layout(
                title="Realtime Open-Meteo PM2.5 vs ML Prediction",
                xaxis_title="City",
                yaxis_title="PM2.5",
                height=520,
            )
            st.plotly_chart(fig_compare, use_container_width=True)

            col_a, col_b = st.columns(2)
            with col_a:
                fig_error = px.bar(
                    compare_df.sort_values("absolute_error", ascending=False),
                    x="city",
                    y="absolute_error",
                    title="Prediction Error by City",
                    labels={"city": "City", "absolute_error": "|Realtime - ML Prediction|"},
                )
                st.plotly_chart(fig_error, use_container_width=True)
            with col_b:
                fig_dist = px.histogram(
                    compare_df,
                    x="absolute_error",
                    nbins=20,
                    title="Prediction Error Distribution",
                    labels={"absolute_error": "Absolute Error"},
                )
                st.plotly_chart(fig_dist, use_container_width=True)

            fig_scatter = px.scatter(
                compare_df,
                x="realtime_openmeteo_pm25",
                y="ml_predicted_pm25",
                text="city",
                title="Realtime Open-Meteo Actual vs ML Predicted PM2.5",
                labels={"realtime_openmeteo_pm25": "Realtime Open-Meteo PM2.5", "ml_predicted_pm25": "ML Predicted PM2.5"},
            )
            min_axis = min(compare_df["realtime_openmeteo_pm25"].min(), compare_df["ml_predicted_pm25"].min())
            max_axis = max(compare_df["realtime_openmeteo_pm25"].max(), compare_df["ml_predicted_pm25"].max())
            fig_scatter.add_trace(go.Scatter(x=[min_axis, max_axis], y=[min_axis, max_axis], mode="lines", name="Ideal Prediction", line=dict(dash="dash")))
            st.plotly_chart(fig_scatter, use_container_width=True)

            best = compare_df.loc[compare_df["absolute_error"].idxmin()]
            worst = compare_df.loc[compare_df["absolute_error"].idxmax()]
            insight_box(
                f"📌 Perbandingan paling dekat antara realtime Open-Meteo dan ML prediction ada di <b>{best['city']}</b> "
                f"dengan absolute error <b>{best['absolute_error']:.2f}</b>. Gap terbesar ada di "
                f"<b>{worst['city']}</b> dengan absolute error <b>{worst['absolute_error']:.2f}</b>."
            )
            warning_box(
                "Catatan interpretasi: batch ML prediction berasal dari data CAMS historis, sedangkan realtime actual berasal dari Open-Meteo saat stream berjalan. "
                "Karena periode sumber data berbeda, grafik ini menunjukkan integrasi dan monitoring comparison, bukan evaluasi model time-series yang strict."
            )

# ============================================================
# TAB 5 — ANOMALY CENTER
# ============================================================
with tab_anomaly:
    render_section("Anomaly Monitoring Center")
    selected_cities, start_date, end_date = render_tab_filters(
        "anomaly",
        city_source_dfs=[batch_data, stream_data],
        date_sources=[(batch_data, batch_time_col), (stream_data, STREAM_DISPLAY_TIME_COL)],
    )
    filtered_batch_data = filter_by_date(filter_by_cities(batch_data, selected_cities), batch_time_col, start_date, end_date)
    filtered_stream_data = filter_by_date(filter_by_cities(stream_data, selected_cities), STREAM_DISPLAY_TIME_COL, start_date, end_date)

    col_batch, col_stream = st.columns(2)

    with col_batch:
        render_mini_title("Batch Anomaly Summary")
        if batch_anomaly_col and not filtered_batch_data.empty:
            batch_anomaly_summary = anomaly_rate_summary(filtered_batch_data, batch_anomaly_col)
            fig = px.bar(
                batch_anomaly_summary,
                x="city",
                y="anomaly_count",
                title="Batch Anomaly Count by City",
                labels={"city": "City", "anomaly_count": "Anomaly Count"},
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(batch_anomaly_summary, use_container_width=True, hide_index=True)
        else:
            st.info("No batch anomaly data available in the selected date range.")

    with col_stream:
        render_mini_title("Stream Anomaly Summary")
        if stream_anomaly_col and not filtered_stream_data.empty:
            stream_anomaly_summary = anomaly_rate_summary(filtered_stream_data, stream_anomaly_col)
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
            st.info("No stream anomaly data available in the selected date range.")

    render_section("Anomaly Pattern Analysis")
    st.markdown(
        """
        Bagian ini menjawab pertanyaan laporan: <b>apakah terdapat kondisi atau pola anomali pada kualitas udara
        yang dapat mengindikasikan peningkatan tingkat pencemaran?</b>
        """,
        unsafe_allow_html=True,
    )

    pattern_source = st.radio("Pattern source", ["Stream", "Batch"], horizontal=True, key="pattern_source")
    if pattern_source == "Stream":
        pattern_df = filtered_stream_data.copy()
        pattern_time_col = STREAM_DISPLAY_TIME_COL
        pattern_pm_col = stream_pm25_col
        pattern_aqi_col = stream_aqi_col
        pattern_anomaly_col = stream_anomaly_col
        source_label = "Realtime Open-Meteo stream"
        xaxis_label = "Processing Time (WIB)"
    else:
        pattern_df = filtered_batch_data.copy()
        pattern_time_col = batch_time_col
        pattern_pm_col = batch_pm25_col
        pattern_aqi_col = None
        pattern_anomaly_col = batch_anomaly_col
        source_label = "CAMS batch"
        xaxis_label = "Time"

    if pattern_df.empty or not pattern_anomaly_col or pattern_anomaly_col not in pattern_df.columns or not pattern_pm_col:
        st.info("Anomaly pattern data is not available for the selected source/date range.")
    else:
        anomaly_detail = pattern_df[pattern_df[pattern_anomaly_col] == True].copy()
        normal_detail = pattern_df[pattern_df[pattern_anomaly_col] == False].copy()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Records", f"{len(pattern_df):,}")
        c2.metric("Anomaly Records", f"{len(anomaly_detail):,}")
        c3.metric("Anomaly Rate", f"{(len(anomaly_detail) / len(pattern_df) * 100 if len(pattern_df) else 0):.2f}%")
        c4.metric("Avg PM2.5 during Anomaly", "-" if anomaly_detail.empty else f"{anomaly_detail[pattern_pm_col].mean():.2f}")

        if pattern_time_col and pattern_time_col in pattern_df.columns:
            pattern_plot_city = st.selectbox(
                "Select city for anomaly timeline",
                sorted(pattern_df["city"].dropna().unique()),
                key="anomaly_pattern_city",
            )
            city_pattern = pattern_df[pattern_df["city"] == pattern_plot_city].sort_values(pattern_time_col)
            city_anomalies = city_pattern[city_pattern[pattern_anomaly_col] == True]

            fig_pattern = go.Figure()
            fig_pattern.add_trace(
                go.Scatter(
                    x=city_pattern[pattern_time_col],
                    y=city_pattern[pattern_pm_col],
                    mode="lines+markers",
                    name="PM2.5",
                )
            )
            if not city_anomalies.empty:
                fig_pattern.add_trace(
                    go.Scatter(
                        x=city_anomalies[pattern_time_col],
                        y=city_anomalies[pattern_pm_col],
                        mode="markers",
                        marker=dict(size=13, symbol="x"),
                        name="Anomaly",
                    )
                )
            fig_pattern.update_layout(
                title=f"{source_label} PM2.5 Timeline with Anomaly Markers - {pattern_plot_city}",
                xaxis_title=xaxis_label,
                yaxis_title="PM2.5",
                height=520,
            )
            st.plotly_chart(fig_pattern, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            rate_df = anomaly_rate_summary(pattern_df, pattern_anomaly_col)
            if not rate_df.empty:
                fig_rate = px.bar(
                    rate_df,
                    x="city",
                    y="anomaly_rate_pct",
                    title="Anomaly Rate by City",
                    labels={"city": "City", "anomaly_rate_pct": "Anomaly Rate (%)"},
                )
                st.plotly_chart(fig_rate, use_container_width=True)
        with col2:
            dist_df = pattern_df[["city", pattern_pm_col, pattern_anomaly_col]].dropna().copy()
            dist_df["record_type"] = np.where(dist_df[pattern_anomaly_col], "Anomaly", "Normal")
            fig_box = px.box(
                dist_df,
                x="record_type",
                y=pattern_pm_col,
                color="record_type",
                title="PM2.5 Distribution: Normal vs Anomaly",
                labels={pattern_pm_col: "PM2.5", "record_type": "Record Type"},
            )
            st.plotly_chart(fig_box, use_container_width=True)

        if pattern_time_col and pattern_time_col in pattern_df.columns and not anomaly_detail.empty:
            anomaly_detail["hour"] = anomaly_detail[pattern_time_col].dt.hour
            heatmap_df = anomaly_detail.groupby(["city", "hour"]).size().reset_index(name="anomaly_count")
            fig_heatmap = px.density_heatmap(
                heatmap_df,
                x="hour",
                y="city",
                z="anomaly_count",
                histfunc="sum",
                title="Anomaly Pattern by City and Hour",
                labels={"hour": "Hour", "city": "City", "anomaly_count": "Anomaly Count"},
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)

        if anomaly_detail.empty:
            safe_box("✅ Tidak ada anomali pada filter terpilih. Tidak terlihat pola peningkatan pencemaran yang terdeteksi oleh rule/model anomali saat ini.")
        else:
            top_city = anomaly_detail["city"].value_counts().idxmax()
            top_city_count = anomaly_detail["city"].value_counts().max()
            avg_anom_pm = anomaly_detail[pattern_pm_col].mean()
            avg_norm_pm = normal_detail[pattern_pm_col].mean() if not normal_detail.empty else np.nan
            if pattern_time_col and pattern_time_col in anomaly_detail.columns:
                top_hour = int(anomaly_detail[pattern_time_col].dt.hour.value_counts().idxmax())
                hour_text = f" Anomali paling sering muncul sekitar jam <b>{top_hour:02d}:00</b>."
            else:
                hour_text = ""
            alert_box(
                f"⚠️ Terdapat pola anomali pada sumber <b>{source_label}</b>. Kota dengan frekuensi anomali tertinggi adalah "
                f"<b>{top_city}</b> sebanyak <b>{top_city_count}</b> record. Rata-rata PM2.5 saat anomali adalah "
                f"<b>{avg_anom_pm:.2f}</b>"
                + (f", lebih tinggi dari rata-rata kondisi normal <b>{avg_norm_pm:.2f}</b>." if not pd.isna(avg_norm_pm) else ".")
                + hour_text
                + " Pola ini dapat mengindikasikan peningkatan tingkat pencemaran, terutama jika anomali berulang pada kota/jam yang sama."
            )

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
                    fig = px.scatter(
                        batch_anomaly_detail,
                        x=batch_time_col,
                        y=batch_pm25_col,
                        color="city",
                        title="Batch Anomaly Events",
                    )
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
                for col in [STREAM_DISPLAY_TIME_COL, stream_time_col, stream_pm25_col, stream_pm10_col, stream_aqi_col, stream_reason_col]:
                    if col and col in stream_anomaly_detail.columns and col not in display_cols:
                        display_cols.append(col)
                st.dataframe(stream_anomaly_detail[display_cols].tail(300), use_container_width=True)
                if STREAM_DISPLAY_TIME_COL and stream_pm25_col:
                    fig = px.scatter(
                        stream_anomaly_detail,
                        x=STREAM_DISPLAY_TIME_COL,
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
        st.dataframe(batch_summary, use_container_width=True)
        csv = batch_summary.to_csv(index=False).encode("utf-8")
        st.download_button("Download Batch Summary CSV", csv, "batch_summary.csv", "text/csv")
    elif selected_dataset == "Batch Detail":
        st.dataframe(batch_data.tail(1000), use_container_width=True)
        csv = batch_data.to_csv(index=False).encode("utf-8")
        st.download_button("Download Batch Detail CSV", csv, "batch_detail.csv", "text/csv")
    else:
        st.dataframe(stream_data.tail(1000), use_container_width=True)
        csv = stream_data.to_csv(index=False).encode("utf-8")
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
        st.write(f"Date range WIB: `{format_date_range(stream_data, STREAM_DISPLAY_TIME_COL)}`")
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
        6. Present the Batch vs Stream tab to compare ML predicted PM2.5 with realtime Open-Meteo PM2.5.  
        7. Present the Anomaly Center tab to answer the anomaly-pattern research question.
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
