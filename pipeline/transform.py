"""
Pipeline step 3: transform.

Runs sql/upi_metrics.sql inside DuckDB to build the upi_metrics table,
then saves a copy as a CSV (handy for Excel, Tableau and the dashboard).
"""
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_FILE = PROJECT_ROOT / "data" / "upi.duckdb"
SQL_FILE = PROJECT_ROOT / "sql" / "upi_metrics.sql"
METRICS_CSV = PROJECT_ROOT / "data" / "processed" / "upi_metrics.csv"


def transform():
    if not DB_FILE.exists():
        raise FileNotFoundError(f"{DB_FILE.name} not found. Run load.py first.")

    sql = SQL_FILE.read_text()
    con = duckdb.connect(str(DB_FILE))
    con.execute(sql)
    metrics = con.execute("SELECT * FROM upi_metrics ORDER BY month").df()
    con.close()

    metrics.to_csv(METRICS_CSV, index=False)
    latest = metrics.iloc[-1]
    print(f"Built upi_metrics with {len(metrics)} rows, saved to {METRICS_CSV.name}")
    print(
        f"Latest month {latest['month']:%b %Y}: "
        f"{latest['volume_mn']:,.0f} mn transactions, "
        f"{latest['volume_yoy_pct']}% vs last year, "
        f"average ticket Rs {latest['avg_ticket_rs']:,.0f}"
    )


if __name__ == "__main__":
    transform()