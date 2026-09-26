"""
UPI Pulse DAG.

Runs the pipeline steps in order:
extract_clean -> is_new_month -> load -> transform -> notify

It runs every morning. Most days there's no new NPCI file, so
is_new_month stops the run early and nothing else happens.
You can also start it by hand from the Airflow UI.
"""
import sys
from pathlib import Path

import pendulum
from airflow.sdk import Param, dag, task

# Let Airflow find our pipeline folder, which sits next to this dags folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dag(
    dag_id="upi_pulse",
    schedule="0 9 * * *",  # every day at 9:00
    start_date=pendulum.datetime(2026, 9, 1, tz="Asia/Kolkata"),
    catchup=False,  # don't go back and run for days the laptop was off
    params={
        "force": Param(False, type="boolean",
                       description="Run every step even if there is no new month"),
    },
    tags=["upi", "npci"],
)
def upi_pulse():

    @task
    def extract_clean():
        from pipeline.extract_clean import extract_and_clean
        extract_and_clean()

    @task.short_circuit
    def is_new_month(**context):
        import pandas as pd
        from pipeline.extract_clean import OUTPUT_FILE
        from pipeline.transform import METRICS_CSV

        if context["params"]["force"]:
            print("force is on, so running every step")
            return True
        if not METRICS_CSV.exists():
            print("No metrics yet, so running every step")
            return True

        newest_in_files = pd.read_csv(OUTPUT_FILE)["month"].max()
        newest_in_metrics = pd.read_csv(METRICS_CSV)["month"].max()
        print(f"Newest month in landing files: {newest_in_files}")
        print(f"Newest month already processed: {newest_in_metrics}")
        return newest_in_files > newest_in_metrics

    @task
    def load():
        from pipeline.load import load as run_load
        run_load()

    @task
    def transform():
        from pipeline.transform import transform as run_transform
        run_transform()

    @task
    def notify():
        from pipeline.notify import send_email
        send_email()

    extract_clean() >> is_new_month() >> load() >> transform() >> notify()


upi_pulse()