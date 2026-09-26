"""
UPI Pulse dashboard.

Reads the metrics CSV made by the pipeline and shows the latest numbers,
four trend charts and the full table.
Run locally with:  streamlit run dashboard/app.py
"""
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
METRICS_CSV = PROJECT_ROOT / "data" / "processed" / "upi_metrics.csv"

BLUE = "#2a78d6"
ORANGE = "#eb6834"

st.set_page_config(page_title="UPI Pulse", page_icon="📈", layout="wide")


# ---------- Load data ----------
@st.cache_data
def load_data():
    df = pd.read_csv(METRICS_CSV, parse_dates=["month"])
    # Friendlier units for charts: billions of transactions, lakh crore rupees
    df["volume_bn"] = df["volume_mn"] / 1000
    df["value_lakh_cr"] = df["value_cr"] / 100000
    return df


df = load_data()
latest = df.iloc[-1]
year_ago = df.iloc[-13]  # same month last year (the pipeline guarantees no gaps)
latest_label = latest["month"].strftime("%b %Y")
year_ago_label = year_ago["month"].strftime("%b %Y")


# ---------- Header ----------
st.title("UPI Pulse")
st.caption(
    f"Monthly Unified Payments Interface statistics from NPCI. "
    f"Latest data: {latest_label}."
)


# ---------- Headline numbers for the latest month ----------
ticket_change = (latest["avg_ticket_rs"] / year_ago["avg_ticket_rs"] - 1) * 100

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    f"Transactions in {latest_label}",
    f"{latest['volume_bn']:.2f} bn",
    f"{latest['volume_yoy_pct']:.1f}% vs {year_ago_label}",
)
col2.metric(
    f"Value in {latest_label}",
    f"₹{latest['value_lakh_cr']:.2f} lakh cr",
    f"{latest['value_yoy_pct']:.1f}% vs {year_ago_label}",
)
col3.metric(
    "Average payment",
    f"₹{latest['avg_ticket_rs']:,.0f}",
    f"{ticket_change:.1f}% vs {year_ago_label}",
    delta_color="off",  # a smaller ticket isn't good or bad, so keep it grey
)
col4.metric(
    "Banks live on UPI",
    f"{latest['banks_live']:,}",
    f"{latest['new_banks']:+.0f} this month",
)

st.divider()


# ---------- Time range filter ----------
period = st.radio(
    "Time range",
    ["Last 12 months", "Last 24 months", "All"],
    index=2,
    horizontal=True,
)
if period == "Last 12 months":
    view = df.tail(12)
elif period == "Last 24 months":
    view = df.tail(24)
else:
    view = df


# ---------- Charts ----------
left, right = st.columns(2)

with left:
    st.subheader("Monthly transactions")
    st.line_chart(view, x="month", y="volume_bn", color=BLUE,
                  x_label="", y_label="Transactions (billion)")

    st.subheader("Growth vs same month last year")
    growth = view[["month", "volume_yoy_pct", "value_yoy_pct"]].dropna()
    growth = growth.rename(columns={"volume_yoy_pct": "Transactions",
                                    "value_yoy_pct": "Value"})
    if growth.empty:
        st.info("Needs at least 13 months of data.")
    else:
        st.line_chart(growth, x="month", y=["Transactions", "Value"],
                      color=[BLUE, ORANGE], x_label="", y_label="Growth (%)")

with right:
    st.subheader("Monthly value")
    st.line_chart(view, x="month", y="value_lakh_cr", color=BLUE,
                  x_label="", y_label="Value (₹ lakh crore)")

    st.subheader("Average payment size")
    st.line_chart(view, x="month", y="avg_ticket_rs", color=BLUE,
                  x_label="", y_label="Average payment (₹)")


# ---------- Full table ----------
with st.expander("See the data"):
    table = df[["month", "fiscal_year", "banks_live", "volume_mn", "value_cr",
                "avg_ticket_rs", "volume_mom_pct", "volume_yoy_pct", "value_yoy_pct"]]
    table = table.sort_values("month", ascending=False)
    st.dataframe(table, hide_index=True, width="stretch")
    st.download_button("Download CSV", table.to_csv(index=False),
                       file_name="upi_metrics.csv", mime="text/csv")

st.caption(
    "Source: NPCI UPI Product Statistics. Volume in millions, value in ₹ crore. "
    "Built with Python, DuckDB and Streamlit."
)