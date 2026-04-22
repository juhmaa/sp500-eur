S&P 500 in EUR --- Portfolio Performance feed
===========================================

This repository automatically generates a daily-updated HTML table of the S&P 500 index (^GSPC) with OHLC values converted from USD to EUR using the European Central Bank's official daily reference rates.

It is designed to be used as a custom benchmark index in [Portfolio Performance](https://www.portfolio-performance.info/) via the **"Table on Website"** quote feed.

How it works
------------

1.  A GitHub Actions workflow runs every weekday at 22:30 UTC.
2.  `fetch_data.py` pulls S&P 500 OHLC from Yahoo Finance and EUR/USD rates from the ECB, converts the values, and writes `index.html`.
3.  GitHub Pages serves `index.html` at your public URL.
4.  Portfolio Performance fetches that URL and appends any new prices.

Data sources
------------

| Data | Source |
| --- | --- |
| S&P 500 OHLC | Yahoo Finance (`^GSPC`) |
| EUR/USD rate | ECB daily reference rates |

Portfolio Performance configuration
-----------------------------------

-   Security currency: **EUR**
-   Quote feed: **Table on Website**
-   Feed URL: `https://<your-username>.github.io/<repo-name>/`
-   Column mapping: Date - Open - High - Low - Close
