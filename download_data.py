# ============================================================
# STI vs S&P 500 (2026 YTD) - data download script
# Creates 3 CSV files you can load straight into Power BI
# ============================================================

import pandas as pd          # pandas = tables of data (like Excel in Python)
import yfinance as yf        # yfinance = downloads data from Yahoo Finance
import requests              # requests = lets us download a web page
from io import StringIO      # helps pandas read the web page text

# ---------- SETTINGS (change these if you need to) ----------
BASE_DATE = "2025-12-31"     # last day of 2025 = our starting point (100)
DOWNLOAD_FROM = "2025-12-20" # start a bit earlier in case 31 Dec was a holiday
OUTPUT_FOLDER = "."          # "." = save the CSVs in the same folder as this script

# ---------- STEP 1: the two index tickers ----------
INDEXES = {"STI": "^STI", "S&P 500": "^GSPC"}

# ---------- STEP 2: STI constituents (30 stocks, matches the Wikipedia list) ----------
# On Yahoo Finance, Singapore stocks end in ".SI"
sti_names = {
    "A17U.SI": "CapitaLand Ascendas REIT",
    "C38U.SI": "CapitaLand Integrated Commercial Trust",
    "9CI.SI": "CapitaLand Investment",
    "C09.SI": "City Developments",
    "D05.SI": "DBS Group",
    "D01.SI": "DFI Retail Group",
    "J69U.SI": "Frasers Centrepoint Trust",
    "BUOU.SI": "Frasers Logistics & Commercial Trust",
    "G13.SI": "Genting Singapore",
    "H78.SI": "Hongkong Land",
    "J36.SI": "Jardine Matheson",
    "BN4.SI": "Keppel Ltd",
    "AJBU.SI": "Keppel DC REIT",
    "ME8U.SI": "Mapletree Industrial Trust",
    "M44U.SI": "Mapletree Logistics Trust",
    "N2IU.SI": "Mapletree Pan Asia Commercial Trust",
    "O39.SI": "OCBC",
    "S58.SI": "SATS",
    "5E2.SI": "Seatrium",              # FIXED: was S51.SI, Yahoo uses 5E2
    "U96.SI": "Sembcorp Industries",
    "C6L.SI": "Singapore Airlines",
    "S68.SI": "Singapore Exchange",
    "S63.SI": "ST Engineering",
    "Z74.SI": "Singtel",
    "Y92.SI": "Thai Beverage",
    "U11.SI": "UOB",
    "U14.SI": "UOL Group",
    "V03.SI": "Venture Corporation",
    "F34.SI": "Wilmar International",
    "BS6.SI": "Yangzijiang Shipbuilding",
}

# ---------- STEP 3: S&P 500 constituents (from Wikipedia) ----------
print("Getting S&P 500 constituent list from Wikipedia...")
url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
# Wikipedia blocks requests with no "User-Agent", so we pretend to be a browser
page = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
page.raise_for_status()                       # stop with an error if download failed
sp_table = pd.read_html(StringIO(page.text))[0]   # first table on the page

# Yahoo uses "-" instead of "." in tickers (e.g. BRK.B becomes BRK-B)
sp_table["Symbol"] = sp_table["Symbol"].str.replace(".", "-", regex=False)
sp_names = dict(zip(sp_table["Symbol"], sp_table["Security"]))
sp_sectors = dict(zip(sp_table["Symbol"], sp_table["GICS Sector"]))

# ---------- STEP 4: combine both stock lists into one table ----------
stock_list = []
for ticker, name in sti_names.items():
    stock_list.append({"Index": "STI", "Ticker": ticker, "Name": name, "Sector": ""})
for ticker, name in sp_names.items():
    stock_list.append({"Index": "S&P 500", "Ticker": ticker, "Name": name,
                       "Sector": sp_sectors[ticker]})
stocks = pd.DataFrame(stock_list)

# ---------- STEP 5: download index prices ----------
print("Downloading index prices...")
index_frames = []   # we will collect one table per index here
for index_name, ticker in INDEXES.items():
    data = yf.download(ticker, start=DOWNLOAD_FROM, auto_adjust=False, progress=False)
    # newer yfinance versions return 2-level column names; flatten them
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data = data[["Close"]].dropna().reset_index()          # keep only Date + Close
    data["Index"] = index_name

    # find the base price = the last trading day on or before BASE_DATE
    base_price = data.loc[data["Date"] <= BASE_DATE, "Close"].iloc[-1]
    data = data[data["Date"] >= BASE_DATE]                 # keep BASE_DATE onwards
    # Rebased: starting value = 100, so both indices are comparable on one chart
    data["Rebased"] = data["Close"] / base_price * 100
    data["Return_Pct"] = (data["Close"] / base_price - 1) * 100
    index_frames.append(data)

index_prices = pd.concat(index_frames, ignore_index=True)
index_prices = index_prices[["Date", "Index", "Close", "Rebased", "Return_Pct"]]

# ---------- STEP 6: download stock prices (all tickers at once) ----------
print("Downloading stock prices (this can take a minute or two)...")
all_tickers = stocks["Ticker"].tolist()
prices = yf.download(all_tickers, start=DOWNLOAD_FROM, auto_adjust=False,
                     progress=False, group_by="column")["Close"]
prices = prices.dropna(how="all")      # drop days where nothing traded

# ---------- STEP 7: calculate each stock's return ----------
summary_rows = []
for _, row in stocks.iterrows():
    t = row["Ticker"]
    # skip tickers Yahoo had no data for
    if t not in prices.columns or prices[t].dropna().empty:
        print(f"  No price data for {t}, skipping")
        continue

    series = prices[t].dropna()
    before_base = series[series.index <= BASE_DATE]
    if before_base.empty:
        continue                              # stock didn't exist at start of year
    start_price = before_base.iloc[-1]        # price on last trading day of 2025
    latest_price = series.iloc[-1]            # most recent price

    summary_rows.append({
        "Index": row["Index"], "Ticker": t, "Name": row["Name"],
        "Sector": row["Sector"],
        "Start_Price": start_price, "Latest_Price": latest_price,
        "Return_Pct": (latest_price / start_price - 1) * 100,
    })
summary = pd.DataFrame(summary_rows)

# ---------- STEP 8: get market caps to estimate weights ----------
print("Getting market caps (slowest step, please wait)...")
caps = []
for t in summary["Ticker"]:
    try:
        caps.append(yf.Ticker(t).fast_info["market_cap"])
    except Exception:
        caps.append(None)                     # if Yahoo has no value, leave blank
summary["Market_Cap_Now"] = caps
summary = summary.dropna(subset=["Market_Cap_Now"]).copy()

# Work out what each company's market cap was at the START of the year:
# start cap = current cap / (1 + return)
summary["Market_Cap_Start"] = summary["Market_Cap_Now"] / (1 + summary["Return_Pct"] / 100)

# Weight at the start of the year = company's share of its own index's total
total_start_cap = summary.groupby("Index")["Market_Cap_Start"].transform("sum")
summary["Start_Weight_Pct"] = summary["Market_Cap_Start"] / total_start_cap * 100

# Contribution (in percentage points) = start weight x stock return
# This tells you how much of the index's gain each stock "carried"
summary["Contribution_Pts"] = summary["Start_Weight_Pct"] / 100 * summary["Return_Pct"]

# Rank inside each index: 1 = biggest positive contributor
summary["Contribution_Rank"] = (
    summary.groupby("Index")["Contribution_Pts"].rank(ascending=False, method="first")
)

# ---------- STEP 9: daily stock prices in "long" format for Power BI ----------
valid_tickers = summary["Ticker"].tolist()
daily = prices[valid_tickers].loc[prices.index >= BASE_DATE].reset_index()
daily = daily.melt(id_vars="Date", var_name="Ticker", value_name="Close").dropna()

# ---------- STEP 10: save everything as CSV ----------
index_prices.to_csv(f"{OUTPUT_FOLDER}/index_prices.csv", index=False)
summary.to_csv(f"{OUTPUT_FOLDER}/stock_summary.csv", index=False)
daily.to_csv(f"{OUTPUT_FOLDER}/stock_daily_prices.csv", index=False)

# ---------- STEP 11: quick check in the console ----------
print("\n=== Index return since", BASE_DATE, "===")
print(index_prices.groupby("Index").tail(1)[["Date", "Index", "Return_Pct"]])
for idx in ["STI", "S&P 500"]:
    print(f"\n=== Top 5 contributors: {idx} ===")
    top = summary[summary["Index"] == idx].nsmallest(5, "Contribution_Rank")
    print(top[["Ticker", "Name", "Return_Pct", "Start_Weight_Pct", "Contribution_Pts"]])
print("\nDone! 3 CSV files saved.")