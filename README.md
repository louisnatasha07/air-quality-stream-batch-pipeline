# Air Quality Stream-Batch Pipeline

End-to-end hybrid Big Data pipeline for environmental monitoring using realtime streaming data and historical atmospheric datasets.

This project combines:

- Open-Meteo API → realtime streaming data
- Copernicus CAMS → historical batch data
- Machine Learning → PM2.5 forecasting and anomaly support
- Dagster → workflow orchestration and automation
- PostgreSQL → centralized storage
- Streamlit → interactive dashboard
- Telegram Bot API → pipeline success, failure, and anomaly alerting

---

# Project Objectives

The system is designed to:

- Monitor realtime air quality conditions
- Process historical atmospheric datasets
- Detect anomalies in environmental data
- Forecast PM2.5 concentrations
- Compare predicted values with realtime observations
- Visualize environmental insights through dashboards
- Provide automated alerting when anomalies or pipeline failures occur

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
│ Kafka Producer      │              │ Dagster Orchestration    │
│ Kafka Consumer      │              │ CAMS Data Ingestion      │
│ Realtime Analytics  │              │ NetCDF Parsing           │
│ Anomaly Detection   │              │ Data Cleaning            │
│ Alerting System     │              │ Feature Engineering      │
└─────────┬───────────┘              │ ML Training & Prediction │
          │                          │ Anomaly Detection        │
          │                          │ Telegram Alerting        │
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
Data Cleaning and Unit Conversion
↓
Feature Engineering with Lag and Rolling Features
↓
Machine Learning Training
↓
PM2.5 Prediction
↓
Anomaly Detection
↓
PostgreSQL
↓
Telegram Alert
↓
Dashboard-ready Tables
```

---

# Batch Processing

The batch pipeline handles historical air quality data processing using Copernicus CAMS data. The current batch implementation has been completed end-to-end through Dagster orchestration, PostgreSQL loading, model prediction, anomaly detection, and Telegram alerting.

---

## Data Ingestion

Historical data is collected from:

- Copernicus CAMS API

Supported cities:

- Jakarta
- Surakarta
- Kuala Lumpur
- Singapore

Downloaded data format:

```text
NetCDF (.nc)
```

The ingestion process is handled by:

```text
batch/data_ingestion/cams_batch.py
```

The downloaded NetCDF files are stored in:

```text
data/external/cams/
```

---

## Data Parsing

The parsing process converts NetCDF files into tabular CSV format.

Main script:

```text
batch/preprocessing/parse_cams.py
```

Output:

```text
data/raw/cams_all_cities.csv
```

A city validation step is applied so that only the target cities are processed:

```text
Jakarta
Surakarta
Kuala Lumpur
Singapore
```

This validation prevents old or non-target city files from being included in the active batch dataset.

---

## Data Cleaning

The cleaning process is handled by:

```text
batch/preprocessing/clean_cams.py
```

Preprocessing tasks include:

- Column selection
- Column normalization
- Timestamp formatting
- Missing value handling
- Duplicate checking
- PM2.5 and PM10 unit conversion
- Data preparation for feature engineering

Output:

```text
data/processed/cams_clean.csv
```

PM2.5 and PM10 values are converted into readable concentration values so the output can be interpreted more clearly in PostgreSQL and dashboard visualizations.

---

## Feature Engineering

Feature engineering is handled by:

```text
batch/feature_engineering/feature_builder.py
```

Generated features include:

### Temporal Features

- hour
- day
- month
- day_of_week

### Lag Features

- pm2_5_lag_1
- pm10_lag_1

### Rolling Features

- pm2_5_rolling_3h
- pm10_rolling_3h

The rolling features are generated using `shift(1)` before applying rolling calculation. This is done to avoid data leakage, because the model should only use previous air quality values when predicting PM2.5.

Output:

```text
data/processed/cams_feature_dataset.csv
```

---

## Machine Learning

The machine learning process is handled by:

```text
batch/training/train_model.py
```

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

Model outputs:

```text
models/trained_model.pkl
models/model_metrics.json
```

The trained model is later loaded by the batch pipeline to generate PM2.5 predictions and support anomaly detection before the final data is inserted into PostgreSQL.

---

## Anomaly Detection

Anomaly detection is applied after PM2.5 prediction is generated. The batch pipeline identifies PM2.5 anomaly records and summarizes anomaly counts by city.

Example alert output from the latest successful batch run:

```text
BATCH ALERT: PM2.5 anomalies detected
Total anomalies: 206
- Jakarta: 52 anomalies
- Kuala Lumpur: 47 anomalies
- Singapore: 51 anomalies
- Surakarta: 56 anomalies
```

---

## Load to PostgreSQL

The final batch loading process is handled by:

```text
batch/main.py
```

The batch pipeline loads processed and prediction-ready data into PostgreSQL.

Main output tables:

```text
cams_air_quality_data
city_air_quality_summary
```

### cams_air_quality_data

Stores detailed batch data, including city, timestamp, CAMS air quality variables, prediction results, and anomaly status.

### city_air_quality_summary

Stores city-level summary statistics, including average PM2.5, maximum PM2.5, average prediction, and anomaly count.

Validation query:

```sql
SELECT city, COUNT(*)
FROM cams_air_quality_data
GROUP BY city
ORDER BY city;
```

Expected cities:

```text
Jakarta
Kuala Lumpur
Singapore
Surakarta
```

---

## Telegram Alerting

The batch pipeline is integrated with Telegram alerting.

Main script:

```text
batch/utils/telegram_alert.py
```

Telegram notifications are sent for:

- PM2.5 anomaly detection
- Successful batch execution
- Dagster batch failure
- Successful Dagster batch execution

Example success notification:

```text
BATCH SUCCESS: CAMS batch pipeline completed
Rows inserted: 5836
Cities: Jakarta, Kuala Lumpur, Singapore, Surakarta
Anomalies detected: 206

DAGSTER BATCH SUCCESS
All batch assets completed successfully.
```

---

## Current Batch Status

The latest batch processing run has been successfully executed through Dagster.

Latest verified output:

```text
Rows inserted: 5836
Cities: Jakarta, Kuala Lumpur, Singapore, Surakarta
Anomalies detected: 206
Dagster status: Success
Telegram alert: Success
PostgreSQL load: Success
```

The batch output has also been validated in DBeaver through the `city_air_quality_summary` table.

---

# Stream Processing

The stream pipeline handles realtime environmental monitoring.

Features:

- Realtime ingestion
- Kafka streaming
- Realtime anomaly detection
- Alert generation
- Live prediction

Current stream processing development is handled separately and will be integrated with the batch output through PostgreSQL and the dashboard.

---

# Workflow Orchestration

Batch processing uses Dagster.

Dagster responsibilities:

- Scheduling batch execution
- Automation
- Run monitoring
- Pipeline tracking
- Asset lineage
- Failure visibility

Current batch assets:

```text
download_cams
parse_cams
clean_cams
build_cams_features
train_model
load_to_postgres
```

Dagster UI:

```text
http://localhost:3000
```

---

# Database Schema

Main tables:

## cams_air_quality_data

Stores processed historical CAMS batch data.

Typical columns include:

- city
- timestamp
- cams_pm2_5
- cams_pm10
- prediction
- is_anomaly

---

## city_air_quality_summary

Stores aggregated city statistics.

Typical columns include:

- city
- average_pm25
- max_pm25
- avg_prediction
- anomaly_count

---

## forecast_results

Planned table for stream-batch forecast comparison.

Columns may include:

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
- city comparison
- summary statistics from CAMS batch data

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
- compare batch prediction with stream observation

---

## Anomaly Monitoring

Displays:

- anomaly count
- anomaly location
- anomaly alerts

Recommended dashboard tables:

```text
cams_air_quality_data
city_air_quality_summary
```

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
- prediction status
- anomaly detection
- PostgreSQL loading
- pipeline errors
- Telegram alert status

Dagster UI also provides run history, step status, and failure tracking.

---

# Data Governance

Data governance implementation:

## Data Quality

- Missing value handling
- Duplicate removal
- Timestamp validation
- City validation for target cities
- Unit conversion for PM2.5 and PM10
- Unexpected city prevention before database loading

## Metadata

- Source tracking from CAMS
- Processing stage information
- Model metrics output
- Dagster run metadata

## Audit Trail

- Pipeline logs
- Dagster run history
- Telegram success and failure alerts
- PostgreSQL output validation

---

# Security

Security implementation:

- Environment variables for credentials
- API keys stored in `.env`
- Telegram token stored in `.env`
- Sensitive credentials excluded from repository
- `.env` ignored using `.gitignore`
- `.env.example` used as configuration reference

Example for Docker-based execution:

```env
POSTGRES_HOST=postgres_db
POSTGRES_PORT=5432
POSTGRES_DB=air_quality_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

For DBeaver access from local machine:

```text
Host: localhost
Port: 5555
Database: air_quality_db
```

For Docker container-to-container access:

```text
Host: postgres_db
Port: 5432
Database: air_quality_db
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
| Alerting | Telegram Bot API |

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
│   ├── utils/
│   └── main.py
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
├── data/
│   ├── external/
│   ├── raw/
│   └── processed/
│
├── models/
│
├── logs/
│
├── docker/
│
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
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

## Configure Environment Variables

Create:

```bash
.env
```

Example:

```env
POSTGRES_HOST=postgres_db
POSTGRES_PORT=5432
POSTGRES_DB=air_quality_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

---

## Run Services

```bash
docker compose up -d --build
```

---

## Open Dagster

```text
http://localhost:3000
```

Run all batch assets from Dagster UI.

---

## Run Batch Pipeline Manually

```bash
python batch/main.py
```

For manual local execution, database host and port may need to be adjusted:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5555
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

# Deployment Notes

For Azure VM or other server deployment:

- Use Docker Compose for service orchestration
- Keep `.env` private on the VM
- Expose only required ports
- Keep PostgreSQL private and avoid exposing it directly to the public internet
- Use `postgres_db:5432` for container-to-container database access
- Use `localhost:5555` only for local tools such as DBeaver

Recommended public ports for demo:

```text
22    SSH
3000  Dagster UI
8501  Streamlit Dashboard
```

---

# Future Improvements

- Complete stream processing integration
- Finalize stream-batch dashboard comparison
- Add Grafana monitoring
- Add Spark Streaming integration
- Add LSTM forecasting
- Add Kubernetes deployment
- Add advanced anomaly detection
- Add automated dashboard deployment on Azure VM

---

# Contributors

Batch Processing:
- Louis Natasha Voudy Nanlessy

Stream Processing:
- Muhammad Darrel Hylmi

---

# License

This project is developed for educational and academic purposes.
