# Air Quality Stream-Batch Pipeline

End-to-end hybrid Big Data pipeline for environmental monitoring using realtime streaming data and historical atmospheric datasets.

This project combines:

- Open-Meteo API → realtime streaming data
- Copernicus CAMS → historical batch data
- Machine Learning → PM2.5 forecasting
- Dagster → workflow orchestration and automation
- PostgreSQL → centralized storage
- Streamlit → interactive dashboard

---

# Project Objectives

The system is designed to:

- Monitor realtime air quality conditions
- Process historical atmospheric datasets
- Detect anomalies in environmental data
- Forecast PM2.5 concentrations
- Compare predicted values with realtime observations
- Visualize environmental insights through dashboards

---

# System Architecture

```text
                                DATA SOURCES

┌──────────────────────────────────────────────────────────────┐
│                                                              │
│ Open-Meteo API                    Copernicus CAMS           │
│ (Realtime Data)                   (Historical Data)         │
│                                                              │
└─────────────────┬───────────────────────┬────────────────────┘
                  │                       │
                  ▼                       ▼


STREAM PIPELINE                              BATCH PIPELINE

┌─────────────────────┐              ┌──────────────────────────┐
│ Kafka Producer      │              │ Dagster Scheduler        │
│ Kafka Consumer      │              │ Data Ingestion           │
│ Realtime Analytics  │              │ NetCDF Parsing           │
│ Anomaly Detection   │              │ Data Cleaning            │
│ Alerting System     │              │ Feature Engineering      │
└─────────┬───────────┘              │ Machine Learning         │
          │                          │ Aggregation              │
          │                          └───────────┬──────────────┘
          │                                      │
          └─────────────────┬────────────────────┘
                            ▼

                    ┌─────────────────┐
                    │ PostgreSQL DB   │
                    │ Central Storage │
                    └────────┬────────┘
                             ▼

                    ┌──────────────────┐
                    │ Streamlit        │
                    │ Dashboard        │
                    └──────────────────┘
```

---

# Project Workflow

## Stream Pipeline Workflow

```text
Open-Meteo API
↓
Kafka Producer
↓
Kafka Consumer
↓
Realtime Processing
↓
Anomaly Detection
↓
Alerting
↓
PostgreSQL
↓
Dashboard
```

---

## Batch Pipeline Workflow

```text
Dagster Automation
↓
CAMS API
↓
NetCDF Download
↓
Data Parsing
↓
Data Cleaning
↓
Feature Engineering
↓
Machine Learning Training
↓
Forecast Generation
↓
PostgreSQL
↓
Dashboard
```

---

# Batch Processing

The batch pipeline handles historical environmental data processing and predictive analytics.

---

## Data Ingestion

Historical data is collected from:

- Copernicus CAMS API

Supported cities:

- Jakarta
- Singapore
- Kuala Lumpur

Downloaded data format:

```text
NetCDF (.nc)
```

---

## Data Preprocessing

Preprocessing tasks:

- Missing value handling
- Duplicate removal
- Timestamp formatting
- Column normalization
- Data transformation

---

## Feature Engineering

Generated features:

### Temporal Features

- hour
- day
- month
- day_of_week

### Rolling Features

- pm2_5_rolling_3h
- pm10_rolling_3h

### Lag Features

- pm2_5_lag_1
- pm10_lag_1

---

## Machine Learning

Prediction target:

```text
PM2.5 concentration
```

Model used:

```text
RandomForestRegressor
```

Evaluation metrics:

- MAE
- MSE
- RMSE
- R² score

Output:

```text
models/trained_model.pkl
models/model_metrics.json
```

---

## Forecasting Process

Forecast results are generated using historical CAMS data and later compared with realtime Open-Meteo observations.

Comparison:

```text
Predicted PM2.5 (CAMS historical model)

vs

Actual PM2.5 (Open-Meteo realtime)
```

---

# Stream Processing

The stream pipeline handles realtime environmental monitoring.

Features:

- Realtime ingestion
- Kafka streaming
- Realtime anomaly detection
- Alert generation
- Live prediction

---

# Workflow Orchestration

Batch processing uses Dagster.

Dagster responsibilities:

- Scheduling batch execution
- Automation
- Run monitoring
- Pipeline tracking
- Asset lineage

Current automation schedule:

```text
Runs at 12:00 AM UTC on day 1 of every month
```

Dagster UI:

```text
http://localhost:3000
```

---

# Database Schema

Main tables:

## cams_air_quality_data

Stores processed historical data.

Columns:

- city
- timestamp
- pm2_5
- pm10
- no2
- o3

---

## city_air_quality_summary

Stores aggregated city statistics.

---

## forecast_results

Stores machine learning prediction results.

Columns:

- city
- timestamp
- predicted_pm25
- actual_pm25
- anomaly_status

---

# Dashboard Features

The dashboard provides:

## Realtime Monitoring

Displays:

- current PM2.5
- AQI status
- realtime charts

---

## Historical Analysis

Displays:

- historical trends
- daily statistics
- city comparison

---

## Forecast Comparison

Displays:

```text
Predicted PM2.5 (CAMS)

vs

Actual PM2.5 (Open-Meteo)
```

Purpose:

- evaluate model performance
- compare prediction accuracy

---

## Anomaly Monitoring

Displays:

- anomaly count
- anomaly location
- anomaly alerts

---

# Monitoring and Logging

Pipeline activity logs are stored in:

```text
logs/pipeline.log
```

Logged events:

- ingestion status
- preprocessing status
- model training status
- anomaly detection
- pipeline errors

---

# Data Governance

Data governance implementation:

## Data Quality

- Missing value handling
- Duplicate removal
- Timestamp validation

## Metadata

- Source tracking
- Processing information

## Audit Trail

- Pipeline logs
- Dagster run history

---

# Security

Security implementation:

- Environment variables for credentials
- API keys stored in .env
- Sensitive credentials excluded from repository
- .env ignored using .gitignore

Example:

```env
CAMS_API_KEY=your_api_key
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=password
```

---

# Technologies Used

| Component | Technology |
|---|---|
| Workflow Orchestration | Dagster |
| Stream Processing | Apache Kafka |
| Batch Processing | Python |
| Machine Learning | Scikit-learn |
| Database | PostgreSQL |
| Dashboard | Streamlit |
| Containerization | Docker |
| Realtime Data | Open-Meteo API |
| Historical Data | Copernicus CAMS |

---

# Project Structure

```text
air-quality-stream-batch-pipeline/
│
├── batch/
│   ├── data_ingestion/
│   ├── preprocessing/
│   ├── feature_engineering/
│   ├── training/
│   └── aggregation/
│
├── stream/
│   ├── producer/
│   ├── consumer/
│   ├── anomaly_detection/
│   └── alerting/
│
├── dashboard/
│
├── database/
│
├── orchestration/
│   └── dagster/
│
├── models/
│
├── logs/
│
├── docker/
│
├── requirements.txt
├── docker-compose.yml
└── README.md
```

---

# Setup Instructions

## Clone Repository

```bash
git clone https://github.com/your-username/air-quality-stream-batch-pipeline.git

cd air-quality-stream-batch-pipeline
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment Variables

Create:

```bash
.env
```

Example:

```env
CAMS_API_KEY=your_api_key
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=password
```

---

## Run Services

```bash
docker-compose up -d
```

---

## Run Dagster

```bash
dagster dev -f orchestration/dagster/definitions.py
```

Open:

```text
http://localhost:3000
```

---

## Run Batch Pipeline

```bash
python batch/main.py
```

---

## Train Machine Learning Model

```bash
python batch/training/train_model.py
```

---

## Run Stream Pipeline

Producer:

```bash
python stream/producer/producer.py
```

Consumer:

```bash
python stream/consumer/consumer.py
```

---

## Run Dashboard

```bash
streamlit run dashboard/app.py
```

---

# Future Improvements

- Spark Streaming integration
- LSTM forecasting
- Grafana monitoring
- Kubernetes deployment
- Multi-city deployment
- Advanced anomaly detection

---

# Contributors

Batch Processing:
- Louis Natasha Voudy Nanlessy

Stream Processing:
- Muhammad Darrel Hylmi

---

# License

This project is developed for educational and academic purposes.
