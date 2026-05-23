from dagster import ScheduleDefinition

monthly_cams_schedule = ScheduleDefinition(
    job_name="__ASSET_JOB",
    cron_schedule="0 0 1 * *"
)