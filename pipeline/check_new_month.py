"""
Checks whether the landing files hold a month that hasn't been processed yet.

Run it after extract_clean.py and before load.py. It prints the answer and,
when running inside GitHub Actions, saves it as an output called new_month.
"""
import os
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEAN_FILE = PROJECT_ROOT / "data" / "processed" / "upi_monthly_clean.csv"
METRICS_CSV = PROJECT_ROOT / "data" / "processed" / "upi_metrics.csv"


def is_new_month():
    if not METRICS_CSV.exists():
        print("No metrics yet, so this counts as new")
        return True

    newest_in_files = pd.read_csv(CLEAN_FILE)["month"].max()
    newest_processed = pd.read_csv(METRICS_CSV)["month"].max()
    print(f"Newest month in landing files: {newest_in_files}")
    print(f"Newest month already processed: {newest_processed}")
    return newest_in_files > newest_processed


if __name__ == "__main__":
    new_month = is_new_month()
    print(f"New month: {new_month}")

    # GitHub Actions gives us a file to write step outputs into
    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"new_month={str(new_month).lower()}\n")