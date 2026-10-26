import pandas as pd

tickers = ["BDX", "BEN", "BF-A", "BIIB", "BIO",
           "BK", "BLK", "BMRA", "BMY", "BR"]

# Dictionary: key = ticker, value = cumulative return Series
print("--- CRITICAL NULL VALUE DICTIONARY CHECK ---")
for ticker in tickers:
    df_raw = pd.read_csv(f"Data/{ticker}.csv")
    
    # Check only the features required for your logic
    null_dates = df_raw["Date"].isnull().sum()
    null_adj_close = df_raw["Adjusted Close"].isnull().sum()
    
    if null_dates > 0 or null_adj_close > 0:
        print(f"⚠️ Ticker {ticker:5} has issues: Null Dates = {null_dates} | Null Adj Close = {null_adj_close}")
    else:
        print(f"✅ Ticker {ticker:5} is perfectly clean.")
print("-" * 45 + "\n")

cumulative_returns = {}

for ticker in tickers:
    df = pd.read_csv(f"Data/{ticker}.csv")
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

    # Filter 2018 to 2021
    df = df[(df["Date"].dt.year >= 2018) & (df["Date"].dt.year <= 2021)]

    # Keep only Date and Adjusted Close
    df = df[["Date", "Adjusted Close"]].set_index("Date")

    # Get the initial price (first trading day of 2018)
    initial_price = df["Adjusted Close"].iloc[0]

    # Calculate cumulative return using the formula from the question
    cum_return = (df["Adjusted Close"] - initial_price) / initial_price

    # Store in dictionary: key = stock name, value = cumulative return Series
    cumulative_returns[ticker] = cum_return

# Combine all into one DataFrame
# pd.DataFrame(dict) turns each key into a column name
# and each Series into a column, aligned by the shared Date index
combined = pd.DataFrame(cumulative_returns)

print(combined.head())
print()
print("Shape:", combined.shape)

combined.to_csv("Data/combined_cumulative_returns_2018_2021.csv", index=True, date_format="%d-%m-%Y")