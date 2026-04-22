"""
fetch_data.py
Fetches daily S&P 500 OHLC data from Yahoo Finance and EUR/USD reference
rates from the European Central Bank, converts the index values to EUR,
and writes an HTML table that Portfolio Performance can scrape.
"""
 
import yfinance as yf
import requests
import pandas as pd
from io import StringIO
from datetime import date
import sys
 
START_DATE = "2021-01-01"
OUTPUT_FILE = "index.html"
 
 
def fetch_sp500():
    """Download S&P 500 daily OHLC from Yahoo Finance via yfinance."""
    print("Fetching S&P 500 data from Yahoo Finance...")
    ticker = yf.Ticker("^GSPC")
    df = ticker.history(start=START_DATE, auto_adjust=False)
    df = df[["Open", "High", "Low", "Close"]].copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = "Date"
    df = df[df.index >= START_DATE]
    print(f"  Got {len(df)} trading days.")
    return df
 
 
def fetch_ecb_rates():
    """Download daily EUR/USD reference rates from the ECB (USD per 1 EUR)."""
    print("Fetching EUR/USD rates from the European Central Bank...")
    url = (
        "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A"
        f"?format=csvdata&startPeriod={START_DATE}"
    )
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
 
    # ECB CSV has a multi-line header; find the row containing TIME_PERIOD
    lines = resp.text.strip().split("\n")
    header_idx = next(
        i for i, line in enumerate(lines) if "TIME_PERIOD" in line
    )
    csv_text = "\n".join(lines[header_idx:])
    df = pd.read_csv(StringIO(csv_text))
    df = df[["TIME_PERIOD", "OBS_VALUE"]].copy()
    df.columns = ["Date", "EURUSD"]
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date")
    df["EURUSD"] = pd.to_numeric(df["EURUSD"], errors="coerce")
    print(f"  Got {len(df)} ECB rate days.")
    return df
 
 
def main():
    sp500 = fetch_sp500()
    ecb   = fetch_ecb_rates()
 
    # Merge on date; S&P 500 is the left frame (trading days only)
    merged = sp500.join(ecb, how="left")
 
    # ECB doesn't publish on weekends/holidays — forward-fill the last known rate
    merged["EURUSD"] = merged["EURUSD"].ffill()
 
    missing = merged["EURUSD"].isna().sum()
    if missing > 0:
        print(f"  Warning: {missing} rows still missing FX rate after ffill. Dropping them.")
        merged = merged.dropna(subset=["EURUSD"])
 
    # Convert USD → EUR  (divide by USD-per-EUR rate)
    for col in ["Open", "High", "Low", "Close"]:
        merged[col] = (merged[col] / merged["EURUSD"]).round(2)
 
    merged = merged.drop(columns=["EURUSD"])
    merged = merged.sort_index(ascending=False)   # newest first
 
    # Build HTML rows
    rows = []
    for dt, row in merged.iterrows():
        rows.append(
            f"    <tr>"
            f"<td>{dt.strftime('%Y-%m-%d')}</td>"
            f"<td>{row['Open']:.2f}</td>"
            f"<td>{row['High']:.2f}</td>"
            f"<td>{row['Low']:.2f}</td>"
            f"<td>{row['Close']:.2f}</td>"
            f"</tr>"
        )
 
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>S&amp;P 500 in EUR</title>
</head>
<body>
  <h1>S&amp;P 500 — daily OHLC converted to EUR</h1>
  <p>
    Source: Yahoo Finance (^GSPC) × ECB daily EUR/USD reference rate.<br>
    Last updated: {date.today().isoformat()}
  </p>
  <table>
    <thead>
      <tr>
        <th>Date</th>
        <th>Open</th>
        <th>High</th>
        <th>Low</th>
        <th>Close</th>
      </tr>
    </thead>
    <tbody>
{chr(10).join(rows)}
    </tbody>
  </table>
</body>
</html>
"""
 
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
 
    print(f"Done. Wrote {len(merged)} rows to {OUTPUT_FILE}.")
 
 
if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
 
