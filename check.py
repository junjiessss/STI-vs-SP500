# ============================================================
# Sanity check - do the stock contributions add up to the index return?
# Run this AFTER download_data.py has finished
# ============================================================

import pandas as pd   # pandas = lets us read CSV files as tables

pd.set_option("display.width", 250)   # stop the output wrapping onto new lines

# Read the two files we created
summary = pd.read_csv("stock_summary.csv")
index_prices = pd.read_csv("index_prices.csv")

# 1) How many stocks ended up in each index? (STI should be about 30, S&P about 500)
print("Stocks per index:")
print(summary.groupby("Index")["Ticker"].count())

# 2) Add up all contributions for each index (in percentage points)
summed = summary.groupby("Index")["Contribution_Pts"].sum()

# 3) Get the real index return = the last row for each index
real = index_prices.groupby("Index").tail(1).set_index("Index")["Return_Pct"]

# 4) Put them side by side and show the gap
check = pd.DataFrame({"Sum_of_contributions": summed, "Real_index_return": real})
check["Gap"] = check["Sum_of_contributions"] - check["Real_index_return"]
print("\nContribution check (all numbers are % points):")
print(check.round(2))

# 5) Which STI stocks are missing? (these would make the weights slightly off)
expected_sti = 30
found_sti = (summary["Index"] == "STI").sum()
print(f"\nSTI stocks found: {found_sti} of {expected_sti}")