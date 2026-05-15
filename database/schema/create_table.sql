CREATE TABLE IF NOT EXISTS air_quality_data (
    id SERIAL PRIMARY KEY,
    time TIMESTAMP,
    pm2_5 FLOAT,
    pm10 FLOAT,
    carbon_monoxide FLOAT,
    nitrogen_dioxide FLOAT,
    ozone FLOAT,
    hour INTEGER,
    day INTEGER,
    pm2_5_rolling FLOAT
);

CREATE TABLE IF NOT EXISTS prediction_results (
    id SERIAL PRIMARY KEY,
    prediction_time TIMESTAMP,
    predicted_pm25 FLOAT
);