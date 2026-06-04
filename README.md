# Air Quality Stream-Batch Pipeline

End-to-end hybrid Big Data pipeline for air quality monitoring using historical batch data, realtime streaming data, machine learning prediction, anomaly detection, dashboard visualization, and Telegram alerting.

This project combines:

- **Open-Meteo API** for realtime air quality stream data
- **Copernicus CAMS** for historical atmospheric batch data
- **Apache Kafka** for stream messaging
- **Dagster** for batch workflow orchestration
- **PostgreSQL** for centralized storage
- **Scikit-learn** for PM2.5 prediction
- **Streamlit** for interactive dashboard visualization
- **Telegram Bot API** for success, failure, and anomaly notifications
- **Docker Compose** for service orchestration

---

## Project Objectives

The system is designed to:

- Monitor realtime PM2.5, PM10, AQI, and pollutant conditions from Open-Meteo.
- Process historical CAMS atmospheric data through a batch pipeline.
- Train a machine learning model to predict PM2.5 concentration.
- Evaluate the model using a time-based split to avoid time-series data leakage.
- Detect air quality anomalies from both batch and stream data.
- Compare ML prediction results with realtime Open-Meteo observations.
- Visualize batch, stream, prediction, and anomaly insights through a Streamlit dashboard.
- Send Telegram notifications for batch status, stream cycle status, and detected anomalies.

---

## System Architecture

```text
                                DATA SOURCES

┌──────────────────────────────────────────────────────────────┐
│                                                              │
│ Open-Meteo API                    Copernicus CAMS            │
│ Realtime Air Quality              Historical Atmospheric     │
│ Stream Data                       Batch Data                 │
│                                                              │
└─────────────────┬───────────────────────┬────────────────────┘
                  │                       │
                  ▼                       ▼

STREAM PIPELINE                              BATCH PIPELINE

┌──────────────────────────┐          ┌──────────────────────────┐
│ Kafka Producer           │          │ Dagster Orchestration    │
│ API Retry + Timeout      │          │ CAMS Data Ingestion      │
│ Kafka Send Confirmation  │          │ NetCDF Parsing           │
└───────────┬──────────────┘          │ Data Cleaning            │
            │                         │ Feature Engineering      │
            ▼                         │ Time-Based ML Training   │
┌──────────────────────────┐          │ PM2.5 Prediction         │
│ Kafka Topic              │          │ Batch Anomaly Detection  │
└───────────┬──────────────┘          │ PostgreSQL Loading       │
            │                         │ Telegram Alerting        │
            ▼                         └───────────┬──────────────┘
┌──────────────────────────┐                      │
│ Kafka Consumer           │                      │
│ Manual Commit            │                      │
│ Auto Table Creation      │                      │
│ PostgreSQL Upsert        │                      │
│ Stream Anomaly Detection │                      │
│ Telegram Alerting        │                      │
└───────────┬──────────────┘                      │
            │                                     │
            └─────────────────┬───────────────────┘
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

## Main Workflows

### Stream Pipeline Workflow

```text
Open-Meteo API
↓
Kafka Producer
↓
Kafka Topic
↓
Kafka Consumer
↓
Realtime Processing
↓
Advanced Anomaly Detection
↓
PostgreSQL Upsert
↓
Manual Kafka Commit
↓
Telegram Notification
↓
Streamlit Dashboard
```

### Batch Pipeline Workflow

```text
Dagster Asset Materialization
↓
CAMS API Request
↓
NetCDF Download
↓
NetCDF Parsing
↓
Data Cleaning and Unit Conversion
↓
Feature Engineering with Lag and Rolling Features
↓
Time-Based ML Training
↓
PM2.5 Prediction
↓
Batch Anomaly Detection
↓
PostgreSQL Loading
↓
Telegram Notification
↓
Streamlit Dashboard
```

---

## Data Sources

### 1. Open-Meteo Realtime Stream Data

Open-Meteo is used by the stream pipeline to collect current air quality values.

Typical stream variables:

- PM2.5
- PM10
- Carbon monoxide
- Nitrogen dioxide
- Sulphur dioxide
- Ozone
- US AQI

Supported stream cities:

- Jakarta
- Surakarta
- Kuala Lumpur
- Singapore

### 2. Copernicus CAMS Historical Batch Data

Copernicus CAMS is used by the batch pipeline to collect historical atmospheric data.

Supported CAMS cities:

- Jakarta
- Surakarta
- Kuala Lumpur
- Singapore

CAMS files are downloaded in:

```text
NetCDF (.nc)
```

and stored in:

```text
data/external/cams/
```

---

## Batch Processing

The batch pipeline processes CAMS data end-to-end through Dagster orchestration.

### Batch Scripts

| Stage | Script |
|---|---|
| CAMS ingestion | `batch/data_ingestion/cams_batch.py` |
| NetCDF parsing | `batch/preprocessing/parse_cams.py` |
| Data cleaning | `batch/preprocessing/clean_cams.py` |
| Feature engineering | `batch/feature_engineering/feature_builder.py` |
| Model training | `batch/training/train_model.py` |
| Batch pipeline main runner | `batch/main.py` |
| Batch Telegram alert | `batch/utils/telegram_alert.py` |

---

### Data Ingestion

The ingestion process downloads CAMS NetCDF files for the selected cities and stores them under:

```text
data/external/cams/
```

City validation is applied so only the target cities are processed.

---

### Data Parsing

Parsing converts NetCDF files into tabular CSV format.

Output:

```text
data/raw/cams_all_cities.csv
```

---

### Data Cleaning

Cleaning is handled by:

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
- City validation
- Data preparation for feature engineering

Output:

```text
data/processed/cams_clean.csv
```

---

### Feature Engineering

Feature engineering is handled by:

```text
batch/feature_engineering/feature_builder.py
```

Generated features:

#### Temporal Features

- `hour`
- `day`
- `month`
- `day_of_week`

#### Lag Features

- `pm2_5_lag_1`
- `pm10_lag_1`

#### Rolling Features

- `pm2_5_rolling_3h`
- `pm10_rolling_3h`

Rolling features are generated using shifted values so the model does not use future information when predicting PM2.5.

Output:

```text
data/processed/cams_feature_dataset.csv
```

---

## Machine Learning

The model training process is handled by:

```text
batch/training/train_model.py
```

Model used:

```text
RandomForestRegressor
```

Prediction target:

```text
cams_pm2_5
```

Main features:

```text
cams_pm10
hour
day
month
day_of_week
pm2_5_rolling_3h
pm10_rolling_3h
pm2_5_lag_1
pm10_lag_1
```

### Time-Based Split

The model uses a **time-based split**, not a random split.

Reason:

- CAMS data is time-series data.
- Random split can cause data leakage because future patterns may leak into training data.
- Time-based split better represents real forecasting behavior.

Current strategy:

```text
80% earliest records per city  → training data
20% latest records per city    → testing data
```

For CAMS data covering approximately September 2024 to August 2025, the model is trained on the earlier period and evaluated on the later period.

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

The `model_metrics.json` file stores metrics, feature list, target column, time column, training period, testing period, and split strategy.

---

## Stream Processing

The stream pipeline handles realtime Open-Meteo data.

### Stream Scripts

| Component | Script |
|---|---|
| Stream orchestrator | `stream/stream_main.py` |
| Kafka producer | `stream/producer/producer.py` |
| Kafka consumer | `stream/consumer/consumer.py` |
| Advanced anomaly detector | `stream/anomaly_detection/anomaly_detector.py` |
| Telegram alerting | `stream/alerting/telegram_alert.py` |

---

### Kafka Producer

The producer collects realtime air quality data from Open-Meteo and sends it to Kafka.

Current reliability features:

- API request timeout
- Retry with backoff
- Response validation
- Kafka send confirmation using `.get(timeout=10)`

This ensures data is not silently dropped when API or Kafka communication fails.

---

### Kafka Consumer

The consumer reads messages from Kafka and stores them into PostgreSQL.

Current reliability features:

- `enable_auto_commit=False`
- PostgreSQL commit first
- Kafka offset commit only after successful database insert
- Rollback on database failure
- Automatic `air_quality_stream` table creation
- Unique index on `(city, timestamp)`
- Upsert handling to avoid duplicate stream records

Processing order:

```text
Read Kafka message
↓
Detect anomaly
↓
Insert/update PostgreSQL
↓
Commit PostgreSQL transaction
↓
Commit Kafka offset
↓
Send Telegram notification
```

---

### Stream Anomaly Detection

Stream anomaly detection is handled by:

```text
stream/anomaly_detection/anomaly_detector.py
```

The consumer uses a per-city detector, so each city has its own rolling statistics. This avoids mixing Jakarta, Singapore, Kuala Lumpur, and Surakarta into one global anomaly window.

An anomaly can be triggered by:

- PM2.5 threshold
- AQI threshold
- Rolling statistical deviation
- Sudden increase pattern based on recent stream values

---

### Telegram Stream Notification

Telegram stream notifications are sent from:

```text
stream/alerting/telegram_alert.py
```

Notifications include:

- Realtime PM2.5 and AQI by city
- Anomaly status
- Stream cycle number
- Batch notification summary
- Success/failure status

Time display uses **WIB / Asia Jakarta time** based on stream processing time. This prevents UTC server time from being displayed incorrectly as WIB.

---

## PostgreSQL Database

Main tables:

### `cams_air_quality_data`

Stores detailed historical CAMS batch records.

Typical columns:

- `city`
- `timestamp` or `time`
- `cams_pm2_5`
- `cams_pm10`
- temporal features
- lag features
- rolling features
- `predicted_pm2_5` or prediction column
- `is_anomaly`

### `city_air_quality_summary`

Stores city-level batch summary.

Typical columns:

- `city`
- `average_pm25`
- `max_pm25`
- `avg_prediction`
- `anomaly_count`

### `air_quality_stream`

Stores realtime Open-Meteo stream output.

Typical columns:

- `timestamp`
- `city`
- `latitude`
- `longitude`
- `pm25`
- `pm10`
- `carbon_monoxide`
- `nitrogen_dioxide`
- `sulphur_dioxide`
- `ozone`
- `aqi`
- `is_anomaly`
- `anomaly_reason`
- `created_at`

The stream table is created automatically by the consumer if it does not exist.

---

## Dashboard

The Streamlit dashboard is located at:

```text
dashboard/app.py
```

Dashboard URL:

```text
http://localhost:8501
```

or on the deployed VM:

```text
http://<vm-public-ip>:8501
```

---

### Dashboard Design Update

The dashboard no longer depends on a left sidebar for filtering. Instead, each main tab has its own filter controls.

Tabs with city and date range filters:

- Executive Overview
- Batch CAMS Analysis
- Realtime Stream
- Batch vs Stream
- Anomaly Center

Additional tabs:

- Data Explorer
- System Health

---

### Air Quality Status Categories

The dashboard uses four simplified PM2.5 quality categories:

| Status | Meaning | Dashboard Color |
|---|---|---|
| Good | Low PM2.5 | Green |
| Moderate | Medium PM2.5 | Blue |
| Unhealthy | High PM2.5 | Red |
| Hazardous | Very high PM2.5 | Pink |

---

### Executive Overview

Displays:

- Number of monitored cities
- Batch records
- Stream records
- Batch anomalies
- Stream anomalies
- Batch average PM2.5
- Latest stream average PM2.5
- Latest stream time in WIB
- Integrated monitoring map
- Batch and stream city ranking
- Narrative insight box

The latest stream time is based on stream processing time and displayed in WIB.

---

### Batch CAMS Analysis

Displays:

- CAMS batch summary table
- Average PM2.5 by city
- Maximum PM2.5 by city
- Batch anomaly count by city
- CAMS PM2.5 trend by selected city
- Batch detail data

Important note:

The Batch CAMS Analysis tab does **not** compare CAMS PM2.5 with ML prediction as the main visualization. ML prediction comparison is shown in the **Batch vs Stream** tab to compare prediction output with realtime Open-Meteo observations.

---

### Realtime Stream

Displays:

- Latest Open-Meteo stream data per city
- Latest PM2.5 ranking
- Latest AQI ranking
- Realtime pollutant trend by city
- PM2.5 distribution by selected city
- Stream anomaly summary
- Stream raw data

Notes:

- Open-Meteo current air quality values may update hourly.
- If the stream is only run for several minutes, pollutant trends and PM2.5 distribution may look flat or repeated.
- Longer stream runtime produces more visible trends and distribution variation.

---

### Batch vs Stream

Displays comparison between:

```text
Realtime Open-Meteo PM2.5
vs
ML Prediction PM2.5
```

Visualization type:

- Line chart with dots / markers
- Absolute error by city
- Actual vs predicted scatter plot
- Error metrics
- Interpretation note

Important interpretation:

Batch vs Stream compares the latest city-level ML prediction from batch output with the latest realtime Open-Meteo PM2.5 observation. Because CAMS historical batch data and Open-Meteo realtime data may come from different time periods, this comparison is used as an integration and monitoring comparison, not as the strict model evaluation method.

Strict ML evaluation is done using the time-based holdout split in `train_model.py`.

---

### Anomaly Center

The Anomaly Center is designed to support the analysis question:

> Are there anomaly conditions or patterns in air quality that may indicate increasing pollution levels?

It displays:

- Batch anomaly count by city
- Stream anomaly count by city
- Stream anomaly rate by city
- PM2.5 timeline with anomaly markers
- Normal vs anomaly PM2.5 distribution
- Anomaly heatmap by city and hour
- Anomaly detail tables
- Automatic interpretation of dominant anomaly city and anomaly time pattern

Example interpretation logic:

- A city with the highest anomaly rate may indicate recurring pollution risk.
- Anomaly clusters at specific hours may indicate temporal pollution patterns.
- A higher PM2.5 distribution during anomaly periods indicates that anomaly detection is capturing meaningful pollution increases.

---

## Telegram Alerting

Telegram alerting is used for both batch and stream pipelines.

### Batch Telegram Alerts

Batch alerts include:

- Batch success notification
- Batch failure notification
- PM2.5 anomaly summary
- Dagster success/failure notification

### Stream Telegram Alerts

Stream alerts include:

- Stream cycle notification
- Per-city PM2.5 and AQI status
- Anomaly status
- Alert delivery confirmation

Time handling:

- Telegram stream notification uses WIB / Asia Jakarta time.
- The displayed time represents pipeline processing time, not raw Open-Meteo hourly timestamp.

---

## Monitoring and Logging

Pipeline logs are stored in:

```text
logs/pipeline.log
```

Logged events include:

- CAMS ingestion status
- parsing status
- cleaning status
- feature engineering status
- model training status
- model evaluation metrics
- prediction status
- anomaly detection
- PostgreSQL loading
- stream consumer processing
- pipeline errors
- Telegram alert status

Dagster also provides:

- Run history
- Asset materialization status
- Step-level monitoring
- Failure tracking
- Asset lineage

---

## Data Governance

### Data Quality

Implemented data quality controls:

- Missing value handling
- Duplicate checking and duplicate prevention
- Timestamp validation
- City validation
- Unit conversion
- PostgreSQL table validation
- Stream upsert handling

### Metadata

Metadata outputs include:

- Source tracking from CAMS and Open-Meteo
- Processing stage information
- Model metrics in JSON format
- Training and testing periods
- Feature and target documentation
- Dagster run metadata

### Audit Trail

Audit trail sources:

- Pipeline log file
- Dagster run history
- PostgreSQL tables
- Telegram success/failure alerts
- Dashboard system health page

---

## Security

Security implementation:

- Credentials are stored in `.env`
- `.env` is excluded from GitHub using `.gitignore`
- `.env.example` is used as the public configuration reference
- PostgreSQL password fallback is not hardcoded in the consumer
- Database configuration logging avoids printing sensitive values
- PostgreSQL is intended to stay internal to Docker/server networking

Do not commit this file:

```text
.env
```

Commit this file instead:

```text
.env.example
```

---

## Environment Variables

Example `.env` for Docker execution:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=postgres_db
POSTGRES_PORT=5432
POSTGRES_DB=air_quality_db

KAFKA_BOOTSTRAP_SERVER=kafka:9092
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

CAMS_API_URL=https://ads.atmosphere.copernicus.eu/api
CAMS_API_KEY=your_cams_api_key

TELEGRAM_ENABLED=True
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

For DBeaver access from the host machine:

```text
Host: localhost
Port: 5555
Database: air_quality_db
User: postgres
Password: value from POSTGRES_PASSWORD
```

For Docker container-to-container access:

```text
Host: postgres_db
Port: 5432
Database: air_quality_db
```

---

## Technologies Used

| Component | Technology |
|---|---|
| Batch processing | Python |
| Stream processing | Apache Kafka |
| Workflow orchestration | Dagster |
| Machine learning | Scikit-learn |
| Database | PostgreSQL |
| Dashboard | Streamlit + Plotly |
| Containerization | Docker Compose |
| Realtime data source | Open-Meteo API |
| Historical data source | Copernicus CAMS |
| Alerting | Telegram Bot API |

---

## Project Structure

```text
air-quality-stream-batch-pipeline/
│
├── batch/
│   ├── data_ingestion/
│   ├── preprocessing/
│   ├── feature_engineering/
│   ├── training/
│   │   └── train_model.py
│   ├── utils/
│   └── main.py
│
├── stream/
│   ├── producer/
│   │   └── producer.py
│   ├── consumer/
│   │   └── consumer.py
│   ├── anomaly_detection/
│   │   └── anomaly_detector.py
│   ├── alerting/
│   │   └── telegram_alert.py
│   └── stream_main.py
│
├── dashboard/
│   └── app.py
│
├── database/
│   ├── db_connection.py
│   ├── schema/
│   └── queries/
│
├── orchestration/
│   └── dagster/
│
├── scripts/
│   ├── seed_demo_data.py
│   └── update_forecast_comparison.py
│
├── data/
│   ├── external/
│   ├── raw/
│   └── processed/
│
├── models/
├── logs/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

If a script is optional or not used in a specific deployment, it can be omitted without affecting the core batch-stream-dashboard workflow.

---

## Setup Instructions

### 1. Clone Repository

```bash
git clone https://github.com/your-username/air-quality-stream-batch-pipeline.git
cd air-quality-stream-batch-pipeline
```

### 2. Configure Environment Variables

Create `.env` from `.env.example`:

```bash
cp .env.example .env
nano .env
```

Fill in:

- PostgreSQL password
- CAMS API key
- Telegram bot token
- Telegram chat ID

### 3. Start Docker Services

```bash
docker compose up --build -d
```

Check service status:

```bash
docker compose ps
```

Expected important services:

```text
postgres_db          Up
zookeeper            Up
kafka                Up
stream_producer      Up
stream_consumer      Up
dagster_webserver    Up
dagster_daemon       Up
streamlit_dashboard  Up
```

### 4. Open Dagster

```text
http://localhost:3000
```

Run or materialize all batch assets.

### 5. Open Dashboard

```text
http://localhost:8501
```

Refresh the dashboard after batch and stream data have entered PostgreSQL.

---

## Useful Commands

### View service status

```bash
docker compose ps
```

### View stream consumer logs

```bash
docker compose logs -f stream_consumer --tail=100
```

### View stream producer logs

```bash
docker compose logs -f stream_producer --tail=100
```

### Stop stream only

```bash
docker compose stop stream_producer stream_consumer
```

### Restart stream only

```bash
docker compose up -d stream_producer stream_consumer
```

### Restart dashboard

```bash
docker compose up --build -d streamlit_dashboard
```

If the service name is `dashboard`, use:

```bash
docker compose up --build -d dashboard
```

### Reset database volume

Use this only if old PostgreSQL data or old password state causes conflicts:

```bash
docker compose down -v
docker compose up --build -d
```

Warning: `down -v` deletes PostgreSQL volume data.

---

## Database Validation Queries

### Check batch table rows by city

```sql
SELECT city, COUNT(*)
FROM cams_air_quality_data
GROUP BY city
ORDER BY city;
```

### Check stream latest records

```sql
SELECT city, timestamp, pm25, aqi, is_anomaly, anomaly_reason, created_at
FROM air_quality_stream
ORDER BY created_at DESC
LIMIT 10;
```

### Check city summary

```sql
SELECT *
FROM city_air_quality_summary
ORDER BY city;
```

---

## Demo Flow

Recommended demonstration order:

1. Start all services using Docker Compose.
2. Open Dagster and show successful batch asset materialization.
3. Show PostgreSQL batch tables in DBeaver or terminal.
4. Show stream producer and consumer logs.
5. Show Telegram stream alert and batch alert.
6. Open Streamlit dashboard.
7. Present Executive Overview.
8. Present Batch CAMS Analysis.
9. Present Realtime Stream.
10. Present Batch vs Stream comparison.
11. Present Anomaly Center and explain anomaly patterns.
12. Present System Health and table status.

---

## Notes on Stream Data Behavior

Open-Meteo current air quality values may not change every few seconds. In a short stream run, such as 5 to 10 minutes, PM2.5 values can look repeated because the source data may update hourly.

This can affect:

- Pollutant trend charts
- PM2.5 distribution charts
- Latest stream records

This behavior does not mean Kafka or PostgreSQL is failing. It means the source API is returning the same current value during that update window.

---

## Deployment Notes

For Azure VM or server deployment:

- Use Docker Compose for service orchestration.
- Keep `.env` private on the VM.
- Expose only required demo ports.
- Keep PostgreSQL private when possible.
- Use `postgres_db:5432` for container-to-container database access.
- Use `localhost:5555` only for local tools such as DBeaver.

Recommended public/demo ports:

```text
22    SSH
3000  Dagster UI
8501  Streamlit Dashboard
```

PostgreSQL port `5555` should only be exposed when needed for local database inspection.

---

## Future Improvements

Possible improvements:

- Add Grafana or Prometheus monitoring.
- Add log rotation and structured logging.
- Add stricter schema migration management.
- Add nearest-timestamp alignment for Batch vs Stream evaluation.
- Add model retraining schedule in Dagster.
- Add longer-running stream storage for stronger realtime trend analysis.
- Add more advanced forecasting models such as XGBoost, LSTM, or temporal models.
- Add Kubernetes deployment.
- Add role-based access and dashboard authentication for public deployment.

---

## Contributors

Batch Processing:

- Louis Natasha Voudy Nanlessy

Stream Processing:

- Muhammad Darrel Hylmi

---

## License

This project is developed for educational and academic purposes.
