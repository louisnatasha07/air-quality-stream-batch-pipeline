# Air Quality Stream-Batch Pipeline

Hybrid Big Data Pipeline for real-time air quality monitoring, anomaly detection, and predictive analytics using Open-Meteo and Copernicus CAMS.

---

## Project Overview

This project implements an end-to-end hybrid data pipeline that combines:

- **Stream Processing** for real-time environmental monitoring
- **Batch Processing** for historical analytics and machine learning
- **Anomaly Detection** for identifying unusual air quality conditions
- **Predictive Analytics** for air quality forecasting

The system integrates realtime environmental data from **Open-Meteo API** and historical atmospheric datasets from **Copernicus CAMS**.

---

## Architecture

```text
                ┌─────────────────────────┐
                │      DATA SOURCES       │
                ├─────────────────────────┤
                │ Open-Meteo API          │
                │ Copernicus CAMS         │
                └──────────┬──────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
        ▼                                     ▼

┌──────────────────────┐           ┌──────────────────────┐
│ Stream Processing    │           │ Batch Processing     │
├──────────────────────┤           ├──────────────────────┤
│ Kafka Producer       │           │ ETL Pipeline         │
│ Kafka Consumer       │           │ Data Cleaning        │
│ Realtime Analytics   │           │ Feature Engineering  │
│ Anomaly Detection    │           │ ML Training          │
│ Alerting             │           │ Aggregation          │
└──────────┬───────────┘           └──────────┬───────────┘
           │                                 │
           └──────────────┬──────────────────┘
                          ▼
                  ┌───────────────┐
                  │ PostgreSQL DB │
                  └───────┬───────┘
                          ▼
                   ┌────────────┐
                   │ Dashboard  │
                   │ Streamlit  │
                   └────────────┘
```

---

## Features

### Batch Processing
- Historical air quality data ingestion
- Data cleaning and transformation
- Feature engineering
- Air quality prediction model training
- Daily and hourly aggregation

### Stream Processing
- Real-time API ingestion
- Kafka-based streaming pipeline
- Realtime anomaly detection
- Realtime prediction
- Alerting system

### Dashboard
- Realtime PM2.5 visualization
- Historical trend analysis
- Air quality prediction
- Anomaly monitoring
- Interactive charts and maps

---

## Technologies Used

| Component | Technology |
|---|---|
| Stream Processing | Apache Kafka |
| Batch Processing | Python |
| Machine Learning | Scikit-learn |
| Database | PostgreSQL |
| Dashboard | Streamlit |
| Containerization | Docker |
| Realtime Data | Open-Meteo API |
| Historical Data | Copernicus CAMS |

---

## Project Structure

```text
air-quality-stream-batch-pipeline/
│
├── batch/
│   ├── etl/
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
│   ├── schema/
│   └── queries/
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

## Data Sources

### Open-Meteo API
Used for:
- Realtime air quality monitoring
- Weather features
- Streaming data ingestion

### Copernicus CAMS
Used for:
- Historical atmospheric data
- Batch analytics
- Machine learning training

---

## Machine Learning

### Prediction Model
The project uses machine learning models to predict:
- PM2.5 concentration
- Air Quality Index (AQI)

Possible models:
- Random Forest Regressor
- XGBoost

### Anomaly Detection
Used to detect unusual environmental conditions using:
- Isolation Forest
- Statistical thresholding
- Rolling Z-score

---

## Setup Instructions

### Clone Repository

```bash
git clone https://github.com/your-username/air-quality-stream-batch-pipeline.git
cd air-quality-stream-batch-pipeline
```

---

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Run PostgreSQL and Kafka

```bash
docker-compose up -d
```

---

### Run Batch Pipeline

```bash
python batch/main.py
```

---

### Run Stream Producer

```bash
python stream/producer/producer.py
```

---

### Run Stream Consumer

```bash
python stream/consumer/consumer.py
```

---

### Run Dashboard

```bash
streamlit run dashboard/app.py
```

---

## Future Improvements

- Spark Streaming integration
- Advanced forecasting models (LSTM)
- Kubernetes deployment
- Grafana monitoring
- Multi-city realtime analysis

---

## Contributors

- Batch Processing Team
- Stream Processing Team

---

## License

This project is developed for academic and educational purposes.
