from dagster import asset
import subprocess


@asset
def download_cams():
    subprocess.run(
        ["python", "batch/data_ingestion/cams_batch.py"],
        check=True
    )

    return "CAMS downloaded"


@asset(deps=[download_cams])
def parse_cams():
    subprocess.run(
        ["python", "batch/preprocessing/parse_cams.py"],
        check=True
    )

    return "CAMS parsed"


@asset(deps=[parse_cams])
def clean_cams():
    subprocess.run(
        ["python", "batch/preprocessing/clean_cams.py"],
        check=True
    )

    return "CAMS cleaned"


@asset(deps=[clean_cams])
def build_cams_features():
    subprocess.run(
        ["python", "batch/feature_engineering/feature_builder.py"],
        check=True
    )

    return "CAMS features built"


@asset(deps=[build_cams_features])
def train_model():
    subprocess.run(
        ["python", "batch/training/train_model.py"],
        check=True
    )

    return "Model trained"

@asset(deps=[train_model])
def load_to_postgres():
    subprocess.run(
        ["python", "batch/main.py"],
        check=True
    )

    return "CAMS data loaded to PostgreSQL"