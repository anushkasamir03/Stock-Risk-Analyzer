import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

print("\n=== Stock Risk & Return Analyzer ===\n")

ticker = input("Enter stock ticker (example: AAPL): ").upper()

print("\nDownloading data...\n")
data = yf.download(ticker, period="5y")

if data.empty:
    print("Invalid ticker or no data found.")
    exit()

data["Daily Return"] = data["Close"].pct_change()

avg_daily_return = data["Daily Return"].mean()
volatility = data["Daily Return"].std()

annual_return = avg_daily_return * 252
annual_volatility = volatility * np.sqrt(252)

risk_free_rate = 0.02
sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility

print("\n=== Analysis Report ===\n")
print(f"Ticker: {ticker}")
print(f"Annual Return: {annual_return:.2%}")
print(f"Annual Volatility: {annual_volatility:.2%}")
print(f"Sharpe Ratio: {sharpe_ratio:.2f}")

plt.figure()
plt.plot(data["Close"])
plt.title(f"{ticker} - Price Chart (5 Years)")
plt.xlabel("Date")
plt.ylabel("Price")
plt.show()