from dagster import asset
import subprocess

from batch.utils.telegram_alert import send_telegram_message


def run_batch_step(command, step_name):
    try:
        subprocess.run(command, check=True)
        return f"{step_name} completed"

    except subprocess.CalledProcessError as e:
        send_telegram_message(
            f"DAGSTER BATCH FAILED\n"
            f"Step: {step_name}\n"
            f"Command: {' '.join(command)}\n"
            f"Error: {str(e)}"
        )
        raise


@asset
def download_cams():
    return run_batch_step(
        ["python", "batch/data_ingestion/cams_batch.py"],
        "Download CAMS"
    )


@asset(deps=[download_cams])
def parse_cams():
    return run_batch_step(
        ["python", "batch/preprocessing/parse_cams.py"],
        "Parse CAMS"
    )


@asset(deps=[parse_cams])
def clean_cams():
    return run_batch_step(
        ["python", "batch/preprocessing/clean_cams.py"],
        "Clean CAMS"
    )


@asset(deps=[clean_cams])
def build_cams_features():
    return run_batch_step(
        ["python", "batch/feature_engineering/feature_builder.py"],
        "Build CAMS Features"
    )


@asset(deps=[build_cams_features])
def train_model():
    return run_batch_step(
        ["python", "batch/training/train_model.py"],
        "Train Model"
    )


@asset(deps=[train_model])
def load_to_postgres():
    result = run_batch_step(
        ["python", "batch/main.py"],
        "Load to PostgreSQL"
    )

    send_telegram_message(
        "DAGSTER BATCH SUCCESS\n"
        "All batch assets completed successfully."
    )

    return result