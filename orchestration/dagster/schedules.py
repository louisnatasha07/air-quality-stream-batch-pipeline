from dagster import ScheduleDefinition

batch_schedule = ScheduleDefinition(
    job_name="__ASSET_JOB",
    cron_schedule="0 1 * * *",
    execution_timezone="Asia/Jakarta",
)