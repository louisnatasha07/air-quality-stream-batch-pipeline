from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'seeker',
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='postgres_data_retention_cleaner',
    default_args=default_args,
    description='Quest harian: Membersihkan log stream yang berumur > 2 hari',
    schedule_interval='@daily', # <--- DIJADWALKAN JALAN OTOMATIS TIAP TENGAH MALAM
    start_date=datetime(2026, 5, 17),
    catchup=False,
) as dag:

    # Task untuk mengeksekusi query pembersihan di Postgres
    clean_old_data = PostgresOperator(
        task_id='purge_old_records',
        postgres_conn_id='my_postgres_conn', # Koneksi di-set via UI Airflow
        sql="""
            DELETE FROM air_quality_stream 
            WHERE timestamp < NOW() - INTERVAL '2 days';
        """
    )