"""
Pipeline step 2: load.

Loads the clean CSV into a DuckDB database, in a table called upi_monthly.
The table is rebuilt from scratch every run, so running it twice is safe.
"""
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEAN_FILE = PROJECT_ROOT / "data" / "processed" / "upi_monthly_clean.csv"
DB_FILE = PROJECT_ROOT / "data" / "upi.duckdb"


def load():
    if not CLEAN_FILE.exists():
        raise FileNotFoundError(f"{CLEAN_FILE.name} not found. Run extract_clean.py first.")

    con = duckdb.connect(str(DB_FILE))
    con.execute(
        """
        CREATE OR REPLACE TABLE upi_monthly AS
        SELECT
            CAST(month AS DATE)         AS month,
            CAST(banks_live AS INTEGER) AS banks_live,
            CAST(volume_mn AS DOUBLE)   AS volume_mn,
            CAST(value_cr AS DOUBLE)    AS value_cr,
            source_file,
            current_timestamp           AS loaded_at
        FROM read_csv(?, header = true)
        """,
        [CLEAN_FILE.as_posix()],
    )
    rows = con.execute("SELECT COUNT(*) FROM upi_monthly").fetchone()[0]
    con.close()
    print(f"Loaded {rows} rows into table upi_monthly in {DB_FILE.name}")


if __name__ == "__main__":
    load()