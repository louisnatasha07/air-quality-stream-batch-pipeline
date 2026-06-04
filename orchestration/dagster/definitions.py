from dagster import Definitions

from .assets import (
    download_cams,
    parse_cams,
    clean_cams,
    build_cams_features,
    train_model,
    load_to_postgres,
)

from .schedules import batch_schedule

defs = Definitions(
    assets=[
        download_cams,
        parse_cams,
        clean_cams,
        build_cams_features,
        train_model,
        load_to_postgres,
    ],
    schedules=[
        batch_schedule,
    ],
)