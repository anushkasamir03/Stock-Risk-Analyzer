import gradio as gr
import yfinance as yf
import numpy as np

def analyze_stock(ticker):
    data = yf.download(ticker, period="1y")

    if data.empty:
        return "Invalid ticker"

    close = data["Close"]

    daily_returns = close.pct_change().dropna()
    annual_return = daily_returns.mean() * 252
    volatility = daily_returns.std() * np.sqrt(252)

    return f"""
Ticker: {ticker}

Annual Return: {annual_return:.2%}
Volatility: {volatility:.2%}
"""

demo = gr.Interface(
    fn=analyze_stock,
    inputs=gr.Textbox(label="Enter Stock Ticker (e.g. AAPL, TCS.NS)"),
    outputs="text",
    title="Stock Risk Analyzer"
)

print("SCRIPT STARTED")
demo.launch()