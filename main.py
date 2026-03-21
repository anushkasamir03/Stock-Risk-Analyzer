import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import anthropic

ANTHROPIC_KEY = "your-api-key-here"  # Replace with your actual key

print("************* Smart Money Stock Analyser *************")

ticker = input("Enter stock ticker (e.g. RELIANCE.NS, TCS.NS, AAPL): ").strip().upper()

print("\n── Downloading price data...")
data = yf.download(ticker, period="5y", auto_adjust=True)

if data.empty:
    print("No data found. Check the ticker and try again.")
    exit()

close = data["Close"].squeeze()

# ── 1. RETURNS ────────────────────────────────────────────────────────────────
daily_returns = close.pct_change().dropna()
annual_return = float(daily_returns.mean() * 252)

# ── 2. RISK ───────────────────────────────────────────────────────────────────
annual_volatility = float(daily_returns.std() * np.sqrt(252))
risk_free_rate = 0.02
sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility

if annual_volatility < 0.15:
    risk_rating = "LOW"
    risk_note = "This stock is relatively stable."
elif annual_volatility < 0.30:
    risk_rating = "MEDIUM"
    risk_note = "This stock has moderate swings — manageable for most investors."
else:
    risk_rating = "HIGH"
    risk_note = "This stock swings significantly — be prepared for big moves."

# ── 3. MAX DRAWDOWN ───────────────────────────────────────────────────────────
rolling_max = close.cummax()
drawdown = (close - rolling_max) / rolling_max
max_drawdown = float(drawdown.min())
max_dd_date = drawdown.idxmin()
if hasattr(max_dd_date, '__iter__') and not isinstance(max_dd_date, str):
    max_dd_date = max_dd_date.iloc[0] if len(max_dd_date) > 0 else "N/A"

# ── 4. BENCHMARK COMPARISON ───────────────────────────────────────────────────
print("── Fetching benchmark data...")
is_indian = ticker.endswith(".NS") or ticker.endswith(".BO")
bench_ticker = "^NSEI" if is_indian else "^GSPC"
bench_label = "Nifty 50" if is_indian else "S&P 500"

benchmark = yf.download(bench_ticker, period="5y", auto_adjust=True)
bench_return = None
outperformance = None
if not benchmark.empty:
    bench_daily = benchmark["Close"].squeeze().pct_change().dropna()
    bench_return = float(bench_daily.mean() * 252)
    outperformance = annual_return - bench_return

# ── 5. OPTIONS SIGNAL ─────────────────────────────────────────────────────────
print("── Fetching options data...")
options_signal = "UNAVAILABLE"
try:
    tk = yf.Ticker(ticker)
    expirations = tk.options
    if expirations:
        chain = tk.option_chain(expirations[0])
        calls = chain.calls
        puts = chain.puts
        call_vol = calls["volume"].sum()
        put_vol = puts["volume"].sum()
        pc_ratio = put_vol / call_vol if call_vol > 0 else None
        if pc_ratio:
            if pc_ratio < 0.7:
                options_signal = f"BULLISH (Put/Call Ratio: {pc_ratio:.2f}) — More calls than puts, market is optimistic"
            elif pc_ratio > 1.3:
                options_signal = f"BEARISH (Put/Call Ratio: {pc_ratio:.2f}) — More puts than calls, market is cautious"
            else:
                options_signal = f"NEUTRAL (Put/Call Ratio: {pc_ratio:.2f}) — Balanced market sentiment"
except:
    pass

# ── 6. PRICE TARGET / ANALYST ESTIMATES ───────────────────────────────────────
price_target = None
current_price = None
upside = None
try:
    tk = yf.Ticker(ticker) if 'tk' not in dir() else tk
    info = tk.info
    current_price = info.get("currentPrice") or info.get("regularMarketPrice")
    price_target = info.get("targetMeanPrice")
    if current_price and price_target:
        upside = ((price_target - current_price) / current_price) * 100
except:
    pass

# ── 7. AI SUMMARY ─────────────────────────────────────────────────────────────
print("── Generating AI summary...")
ai_summary = "(Add your Anthropic API key above to get AI summaries)"
if ANTHROPIC_KEY and ANTHROPIC_KEY != "your-api-key-here":
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        prompt = f"""
        Analyze this stock data for {ticker} and give a short, plain English smart money summary in 4-5 sentences.
        - Annual Return: {annual_return:.2%}
        - Annual Volatility: {annual_volatility:.2%}
        - Sharpe Ratio: {sharpe_ratio:.2f}
        - Max Drawdown: {max_drawdown:.2%}
        - Risk Rating: {risk_rating}
        - Benchmark ({bench_label}) Return: {bench_return:.2%if bench_return else 'N/A'}
        - Options Signal: {options_signal}
        - Analyst Price Target: {price_target if price_target else 'N/A'}
        - Current Price: {current_price if current_price else 'N/A'}
        - Estimated Upside: {f'{upside:.1f}%' if upside else 'N/A'}
        Be direct, no fluff. Mention if it's worth considering or avoiding and why.
        """
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        ai_summary = message.content[0].text
    except Exception as e:
        ai_summary = f"AI summary failed: {e}"

# ── 8. PRINT REPORT ───────────────────────────────────────────────────────────
print("\n" + "─" * 52)
print(f"  SMART MONEY REPORT: {ticker}")
print("─" * 52)

print("\n  RETURNS")
print(f"  Annual Return      : {annual_return:+.2%}")
if bench_return:
    direction = "▲" if outperformance >= 0 else "▼"
    print(f"  {bench_label} Return  : {bench_return:+.2%}  ({direction} {abs(outperformance):.2%} {'above' if outperformance >= 0 else 'below'} benchmark)")

print("\n  RISK")
print(f"  Annual Volatility  : {annual_volatility:.2%}")
print(f"  Sharpe Ratio       : {sharpe_ratio:.2f}  ({'good' if sharpe_ratio > 1 else 'average' if sharpe_ratio > 0 else 'poor'})")
print(f"  Max Drawdown       : {max_drawdown:.2%}  (worst fall, on {max_dd_date})")
print(f"  Risk Rating        : {risk_rating}  — {risk_note}")

print("\n  ANALYST PRICE TARGET")
if current_price and price_target and upside is not None:
    direction = "📈" if upside >= 0 else "📉"
    print(f"  Current Price      : {current_price:.2f}")
    print(f"  Analyst Target     : {price_target:.2f}")
    print(f"  Estimated Upside   : {direction} {upside:+.1f}%")
else:
    print("  Price target data unavailable for this ticker.")

print("\n  SMART MONEY SIGNAL")
print(f"  Options Signal     : {options_signal}")

print("\n  AI SUMMARY")
print(f"  {ai_summary}")

print("\n" + "─" * 52)

# ── 9. CHART ──────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
fig.suptitle(f"{ticker} — Smart Money Analysis", fontsize=14, fontweight="bold")

ax1.plot(close.index, close, color="#2E86AB", linewidth=1.5, label="Price")
ax1.fill_between(close.index, close, close.cummax(), alpha=0.15, color="#D85A30", label="Drawdown zone")
ax1.set_ylabel("Price")
ax1.legend()
ax1.grid(alpha=0.3)

ax2.fill_between(drawdown.index, drawdown, 0, color="#D85A30", alpha=0.6, label="Drawdown")
ax2.set_ylabel("Drawdown")
ax2.set_xlabel("Date")
ax2.legend()
ax2.grid(alpha=0.3)

plt.tight_layout()
plt.show()