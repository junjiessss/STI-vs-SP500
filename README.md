# Did STI index performed better than the S&P500 in 2026?

# STI vs S&P 500 in 2026: Who Is Carrying the Index?

Compares the year-to-date price return of the Straits Times Index (STI)
and the S&P 500 from 31 Dec 2025 to 20 Oct 2026, and shows which stocks
contributed most to each index.

## Result
- STI: +16.20% (SGD), S&P 500: +12.35% (USD), a 3.85 point lead for the STI
- DBS, OCBC and UOB account for about 90% of the STI's gain
- The S&P 500's top 5 stocks account for about 42% of its gain

## How it was built
1. `download_data.py` downloads prices from Yahoo Finance (yfinance) and the
   S&P 500 list from Wikipedia, then calculates returns and contributions.
2. The CSVs were loaded into Microsoft Fabric and the dashboard built in Power BI.

## Method and limitations
- Price return only (dividends excluded), local currency
- Weights estimated from market cap, so contributions are approximate
- Constituents are as of the download date
- Dashboard: see the screenshots and PDF in this repository
