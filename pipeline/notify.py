"""
Pipeline step 4: notify.

Writes a short "what changed this month" summary from upi_metrics.csv
and emails it through Gmail. If the Gmail details aren't set,
it just prints the email so you can check it without sending.
"""
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
METRICS_CSV = PROJECT_ROOT / "data" / "processed" / "upi_metrics.csv"
DASHBOARD_URL = "https://upi-pulse-abhay.streamlit.app/"

# Reads GMAIL_ADDRESS, GMAIL_APP_PASSWORD and EMAIL_TO from the .env file
load_dotenv(PROJECT_ROOT / ".env")


def build_summary():
    df = pd.read_csv(METRICS_CSV, parse_dates=["month"])
    now = df.iloc[-1]        # latest month
    prev = df.iloc[-2]       # month before
    year_ago = df.iloc[-13]  # same month last year

    now_label = now["month"].strftime("%b %Y")
    prev_label = prev["month"].strftime("%b %Y")
    year_ago_label = year_ago["month"].strftime("%b %Y")

    volume_bn = now["volume_mn"] / 1000
    value_lakh_cr = now["value_cr"] / 100000

    # A few simple rules that pick out what's worth mentioning
    highlights = []
    if now["volume_mn"] == df["volume_mn"].max():
        highlights.append("Highest monthly transaction count on record.")
    if now["avg_ticket_rs"] == df["avg_ticket_rs"].min():
        highlights.append("Smallest average payment on record.")
    if now["volume_yoy_pct"] > prev["volume_yoy_pct"]:
        highlights.append(
            f"Yearly growth sped up: {now['volume_yoy_pct']:.1f}% this month vs {prev['volume_yoy_pct']:.1f}% last month."
        )
    else:
        highlights.append(
            f"Yearly growth slowed: {now['volume_yoy_pct']:.1f}% this month vs {prev['volume_yoy_pct']:.1f}% last month."
        )
    highlights.append(f"That's about {now['avg_daily_volume_mn']:.0f} million UPI payments a day.")

    subject = f"UPI Pulse: {now_label} - {volume_bn:.2f} bn transactions ({now['volume_yoy_pct']:+.1f}% YoY)"

    lines = [
        f"UPI in {now_label}",
        "",
        f"Transactions: {volume_bn:.2f} bn ({now['volume_mom_pct']:+.1f}% vs {prev_label}, {now['volume_yoy_pct']:+.1f}% vs {year_ago_label})",
        f"Value: Rs {value_lakh_cr:.2f} lakh crore ({now['value_mom_pct']:+.1f}% vs {prev_label}, {now['value_yoy_pct']:+.1f}% vs {year_ago_label})",
        f"Average payment: Rs {now['avg_ticket_rs']:,.0f} (Rs {prev['avg_ticket_rs']:,.0f} in {prev_label})",
        f"Banks live on UPI: {now['banks_live']:,} ({now['new_banks']:+.0f} this month)",
        "",
        "What stood out:",
    ]
    lines += [f"- {h}" for h in highlights]
    lines += ["", f"Full dashboard: {DASHBOARD_URL}", "", "Source: NPCI UPI Product Statistics"]

    return subject, "\n".join(lines)


def send_email():
    subject, body = build_summary()

    sender = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")
    to = os.getenv("EMAIL_TO", sender)

    if not sender or not password:
        print("Gmail details not set, so printing the email instead of sending:\n")
        print("Subject:", subject)
        print(body)
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(msg)
    print(f"Email sent to {to}: {subject}")


if __name__ == "__main__":
    send_email()