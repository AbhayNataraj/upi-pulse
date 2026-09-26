"""
Pipeline step 1: extract and clean.

Reads every NPCI Excel file in data/landing, cleans it,
runs some quality checks and saves one tidy CSV in data/processed.
"""
from pathlib import Path

import pandas as pd

# Folder paths, worked out from where this file sits,
# so the script works no matter where you run it from
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LANDING = PROJECT_ROOT / "data" / "landing"
PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = PROCESSED / "upi_monthly_clean.csv"

# The columns NPCI uses, and the simpler names we give them
EXPECTED_COLUMNS = ["Month", "No. of Banks live on UPI", "Volume (In Mn.)", "Value (In Cr.)"]
NEW_NAMES = ["month", "banks_live", "volume_mn", "value_cr"]


def extract_and_clean():
    # 1. Find the files
    files = sorted(LANDING.glob("*.xlsx"))
    if not files:
        raise FileNotFoundError(f"No Excel files found in {LANDING}")
    print(f"Found {len(files)} file(s) in landing")

    # 2. Read each file, check its columns, and stack them into one table
    tables = []
    for f in files:
        df = pd.read_excel(f)
        if list(df.columns) != EXPECTED_COLUMNS:
            raise ValueError(f"{f.name} has unexpected columns: {list(df.columns)}")
        df["source_file"] = f.name
        tables.append(df)
    data = pd.concat(tables, ignore_index=True)

    # 3. Rename columns
    data.columns = NEW_NAMES + ["source_file"]

    # 4. Turn text numbers into real numbers (remove commas and hidden tabs)
    for col in ["banks_live", "volume_mn", "value_cr"]:
        data[col] = data[col].astype(str).str.replace(",", "").str.strip().astype(float)
    data["banks_live"] = data["banks_live"].astype(int)

    # 5. Turn "March-2025" into a real date (2025-03-01)
    data["month"] = pd.to_datetime(data["month"].astype(str).str.strip(), format="%B-%Y")

    # 6. Remove repeated months and sort oldest first
    data = data.drop_duplicates(subset="month", keep="last")
    data = data.sort_values("month").reset_index(drop=True)

    # 7. Quality checks: stop the pipeline if something looks wrong
    if data.isna().sum().sum() > 0:
        raise ValueError("Found empty values after cleaning")

    if (data[["banks_live", "volume_mn", "value_cr"]] <= 0).any().any():
        raise ValueError("Found zero or negative numbers")

    all_months = pd.date_range(data["month"].min(), data["month"].max(), freq="MS")
    missing = all_months.difference(data["month"])
    if len(missing) > 0:
        raise ValueError(f"Missing months: {list(missing.strftime('%b-%Y'))}")

    # 8. Save
    PROCESSED.mkdir(parents=True, exist_ok=True)
    data.to_csv(OUTPUT_FILE, index=False)
    first = data["month"].min().strftime("%b %Y")
    last = data["month"].max().strftime("%b %Y")
    print(f"Saved {len(data)} months ({first} to {last}) to {OUTPUT_FILE.name}")
    return OUTPUT_FILE


if __name__ == "__main__":
    extract_and_clean()