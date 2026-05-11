import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import anthropic
from anthropic import Anthropic
import requests

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AXIOM | Smart Money",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background-color: #0a0a0a;
    color: #e8e0cc;
}
.stApp { background-color: #0a0a0a; }
section[data-testid="stSidebar"] {
    background-color: #0f0f0f;
    border-right: 1px solid #2a2520;
}
section[data-testid="stSidebar"] * { color: #e8e0cc; }
.stTextInput input, .stTextArea textarea {
    background-color: #111 !important;
    border: 1px solid #2a2520 !important;
    color: #e8e0cc !important;
    font-family: 'Space Mono', monospace !important;
    border-radius: 4px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #c9a84c !important;
    box-shadow: 0 0 0 1px #c9a84c22 !important;
}
.stButton button {
    background-color: #c9a84c !important;
    color: #0a0a0a !important;
    font-family: 'Space Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    letter-spacing: 0.1em !important;
    border: none !important;
    border-radius: 4px !important;
    padding: 10px 24px !important;
}
.stButton button:hover { background-color: #e0bc60 !important; }
[data-testid="metric-container"] {
    background-color: #111 !important;
    border: 1px solid #2a2520 !important;
    border-radius: 6px !important;
    padding: 16px !important;
}
[data-testid="metric-container"] label {
    font-family: 'Space Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 0.12em !important;
    color: #6b6050 !important;
    text-transform: uppercase !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Space Mono', monospace !important;
    font-size: 22px !important;
    color: #e8e0cc !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-family: 'Space Mono', monospace !important;
    font-size: 11px !important;
}
hr { border-color: #2a2520 !important; }
.stTabs [data-baseweb="tab-list"] {
    background-color: #0f0f0f !important;
    border-bottom: 1px solid #2a2520 !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent !important;
    color: #6b6050 !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.1em !important;
    padding: 12px 20px !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #c9a84c !important;
    border-bottom: 2px solid #c9a84c !important;
    background-color: transparent !important;
}
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0a0a0a; }
::-webkit-scrollbar-thumb { background: #2a2520; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-bottom:1px solid #2a2520;padding-bottom:20px;margin-bottom:28px;">
    <div style="display:flex;align-items:baseline;gap:14px;">
        <span style="font-family:'Space Mono',monospace;font-size:11px;color:#c9a84c;letter-spacing:0.2em;">◈ AXIOM</span>
        <span style="font-family:'Syne',sans-serif;font-size:28px;font-weight:800;color:#e8e0cc;letter-spacing:-0.02em;">Smart Money Terminal</span>
    </div>
    <p style="font-family:'Space Mono',monospace;font-size:11px;color:#4a4035;margin-top:6px;letter-spacing:0.05em;">INSTITUTIONAL-GRADE STOCK ANALYSIS · POWERED BY AI</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p style="font-family:Space Mono,monospace;font-size:10px;color:#c9a84c;letter-spacing:0.15em;margin-bottom:16px;">◈ CONFIGURATION</p>', unsafe_allow_html=True)
    api_key = st.text_input("Anthropic API Key", type="password", help="console.anthropic.com")
    st.markdown("<hr style='border-color:#2a2520;margin:20px 0;'>", unsafe_allow_html=True)
    st.markdown('<p style="font-family:Space Mono,monospace;font-size:10px;color:#c9a84c;letter-spacing:0.15em;margin-bottom:12px;">◈ MODE</p>', unsafe_allow_html=True)
    mode = st.radio(
    "Mode",
    ["Single Stock", "Peer Comparison", "Portfolio"],
    label_visibility="collapsed"
)
    st.markdown("<hr style='border-color:#2a2520;margin:20px 0;'>", unsafe_allow_html=True)
    st.markdown('<p style="font-family:Space Mono,monospace;font-size:10px;color:#4a4035;letter-spacing:0.1em;">AXIOM v2.0 · HEDGE FUND GRADE</p>', unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def analyse_ticker(ticker):
    data = yf.download(ticker, period="5y", auto_adjust=True, progress=False)
    if data.empty:
        return None
    close = data["Close"].squeeze()
    daily_returns = close.pct_change().dropna()
    annual_return = float(daily_returns.mean() * 252)
    annual_volatility = float(daily_returns.std() * np.sqrt(252))
    risk_free_rate = 0.02
    sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility
    if annual_volatility < 0.15:
        risk_rating, risk_note = "LOW", "Relatively stable."
    elif annual_volatility < 0.30:
        risk_rating, risk_note = "MEDIUM", "Moderate swings."
    else:
        risk_rating, risk_note = "HIGH", "Significant swings."
    rolling_max = close.cummax()
    drawdown = (close - rolling_max) / rolling_max
    max_drawdown = float(drawdown.min())
    max_dd_date = drawdown.idxmin()
    if hasattr(max_dd_date, '__iter__') and not isinstance(max_dd_date, str):
        max_dd_date = max_dd_date.iloc[0] if len(max_dd_date) > 0 else "N/A"
    is_indian = ticker.endswith(".NS") or ticker.endswith(".BO")
    bench_ticker = "^NSEI" if is_indian else "^GSPC"
    bench_label = "Nifty 50" if is_indian else "S&P 500"
    benchmark = yf.download(bench_ticker, period="5y", auto_adjust=True, progress=False)
    bench_return, outperformance = None, None
    if not benchmark.empty:
        bench_daily = benchmark["Close"].squeeze().pct_change().dropna()
        bench_return = float(bench_daily.mean() * 252)
        outperformance = annual_return - bench_return
    options_signal = "UNAVAILABLE"
    try:
        tk = yf.Ticker(ticker)
        expirations = tk.options
        if expirations:
            chain = tk.option_chain(expirations[0])
            call_vol = chain.calls["volume"].sum()
            put_vol = chain.puts["volume"].sum()
            pc_ratio = put_vol / call_vol if call_vol > 0 else None
            if pc_ratio:
                if pc_ratio < 0.7:
                    options_signal = "BULLISH · P/C " + str(round(pc_ratio, 2))
                elif pc_ratio > 1.3:
                    options_signal = "BEARISH · P/C " + str(round(pc_ratio, 2))
                else:
                    options_signal = "NEUTRAL · P/C " + str(round(pc_ratio, 2))
    except Exception:
        pass
    current_price, price_target, upside = None, None, None
    try:
        tk = yf.Ticker(ticker)
        info = tk.info
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        price_target = info.get("targetMeanPrice")
        if current_price and price_target:
            upside = ((price_target - current_price) / current_price) * 100
    except Exception:
        pass
    return {
        "ticker": ticker,
        "close": close,
        "drawdown": drawdown,
        "annual_return": annual_return,
        "annual_volatility": annual_volatility,
        "sharpe_ratio": sharpe_ratio,
        "risk_rating": risk_rating,
        "risk_note": risk_note,
        "max_drawdown": max_drawdown,
        "max_dd_date": max_dd_date,
        "bench_label": bench_label,
        "bench_return": bench_return,
        "outperformance": outperformance,
        "options_signal": options_signal,
        "current_price": current_price,
        "price_target": price_target,
        "upside": upside,
    }


def get_fear_greed():
    try:
        r = requests.get("https://production.dataviz.cnn.io/index/fearandgreed/graphdata", timeout=5)
        d = r.json()
        score = float(d["fear_and_greed"]["score"])
        rating = d["fear_and_greed"]["rating"]
        return score, rating
    except Exception:
        return None, None


def get_news(ticker, key):
    if not key:
        return None
    try:
        tk = yf.Ticker(ticker)
        articles = tk.news[:5]
        headlines = "\n".join([a["title"] for a in articles if "title" in a])

        client = Anthropic(api_key=key)
        msg = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": (
                    "Summarize these real news headlines for " + ticker +
                    ". Format: HEADLINE | one-line summary.\n\n" + headlines
                )
            }]
        )

        raw = msg.content[0].text.strip().split("\n")
        news = []
        for line in raw:
            if "|" in line:
                h, s = line.split("|", 1)
                news.append({"headline": h.strip(), "summary": s.strip()})
        return news[:5]
    except Exception:
        return None


def get_ai_summary(d, key):
    if not key:
        return None
    try:
        client = Anthropic(api_key=key)

        bench_ret = f'{d["bench_return"]*100:.2f}%' if d["bench_return"] is not None else "N/A"
        upside = f'{d["upside"]:.1f}%' if d["upside"] is not None else "N/A"

        content = f"""
Analyze this stock like a senior portfolio manager.

Ticker: {d['ticker']}
Annual Return: {d['annual_return']*100:.2f}%
Volatility: {d['annual_volatility']*100:.2f}%
Sharpe: {d['sharpe_ratio']:.2f}
Max Drawdown: {d['max_drawdown']*100:.2f}%
Risk: {d['risk_rating']}
Benchmark ({d['bench_label']}): {bench_ret}
Options Signal: {d['options_signal']}
Price Target: {d['price_target']}
Current Price: {d['current_price']}
Upside: {upside}

Give a 4–5 sentence institutional investment brief.
"""

        msg = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=350,
            messages=[{"role": "user", "content": content}]
        )

        return msg.content[0].text

    except Exception as e:
        return "AI summary failed: " + str(e)

def signal_color(sig):
    if "BULLISH" in sig:
        return "#4caf50"
    if "BEARISH" in sig:
        return "#c0392b"
    if "NEUTRAL" in sig:
        return "#c9a84c"
    return "#4a4035"


def make_chart(results):
    n = len(results)
    fig, axes = plt.subplots(n, 2, figsize=(14, 4 * n))
    if n == 1:
        axes = [axes]
    fig.patch.set_facecolor("#0a0a0a")
    GOLD, RED, DIM = "#c9a84c", "#c0392b", "#2a2520"
    for i, d in enumerate(results):
        ax1, ax2 = axes[i]
        for ax in (ax1, ax2):
            ax.set_facecolor("#0f0f0f")
            ax.tick_params(colors="#4a4035", labelsize=8)
            for spine in ax.spines.values():
                spine.set_color(DIM)
                spine.set_linewidth(0.5)
        ax1.plot(d["close"].index, d["close"], color=GOLD, linewidth=1.2)
        ax1.fill_between(d["close"].index, d["close"], d["close"].cummax(), alpha=0.08, color=RED)
        ax1.set_ylabel("Price", color="#4a4035", fontsize=9, fontfamily="monospace")
        ax1.set_title(d["ticker"] + " — Price", color="#6b6050", fontsize=10, fontfamily="monospace", pad=10)
        ax1.grid(alpha=0.1, color=DIM)
        ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: "{:,.0f}".format(x)))
        ax2.fill_between(d["drawdown"].index, d["drawdown"], 0, color=RED, alpha=0.5)
        ax2.axhline(0, color=DIM, linewidth=0.5)
        ax2.set_ylabel("Drawdown", color="#4a4035", fontsize=9, fontfamily="monospace")
        ax2.set_title(d["ticker"] + " — Drawdown", color="#6b6050", fontsize=10, fontfamily="monospace", pad=10)
        ax2.grid(alpha=0.1, color=DIM)
        ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: "{:.0%}".format(x)))
    plt.tight_layout(pad=2)
    return fig


def mono(text, size=13, color="#e8e0cc", bold=False):
    weight = "700" if bold else "400"
    return '<p style="font-family:Space Mono,monospace;font-size:' + str(size) + 'px;color:' + color + ';font-weight:' + weight + ';margin:0;">' + str(text) + '</p>'


def label(text):
    return '<p style="font-family:Space Mono,monospace;font-size:10px;color:#4a4035;letter-spacing:0.1em;margin:0;">' + text + '</p>'


# ══════════════════════════════════════════════════════════════════════════════
# SINGLE STOCK
# ══════════════════════════════════════════════════════════════════════════════
if mode == "Single Stock":
    col1, col2 = st.columns([4, 1])
    with col1:
        ticker = st.text_input(
    "Ticker",
    placeholder="Enter ticker — AAPL · RELIANCE.NS · TCS.NS · TSLA",
    label_visibility="collapsed"
).strip().upper()
    with col2:
        analyse = st.button("▶ ANALYSE", use_container_width=True)

    st.markdown(label("QUICK PICKS"), unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    qcols = st.columns(8)
    for i, q in enumerate(["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "RELIANCE.NS", "TCS.NS", "INFY.NS"]):
        if qcols[i].button(q, key="q_" + q):
            ticker = q
            analyse = True

    if analyse and ticker:
        with st.spinner("Analysing " + ticker + "..."):
            d = analyse_ticker(ticker)
        if d is None:
            st.error("No data found for " + ticker + ".")
            st.stop()

        tabs = st.tabs(["◈ OVERVIEW", "◈ NEWS", "◈ CHART", "◈ AI BRIEF"])

        with tabs[0]:
            fg_score, fg_rating = get_fear_greed()
            if fg_score:
                fg_color = "#c0392b" if fg_score < 30 else "#4caf50" if fg_score > 70 else "#c9a84c"
                st.markdown(
                    '<div style="background:#0f0f0f;border:1px solid #2a2520;border-radius:6px;padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;gap:20px;">'
                    '<span style="font-family:Space Mono,monospace;font-size:10px;color:#4a4035;letter-spacing:0.12em;">MARKET SENTIMENT</span>'
                    '<span style="font-family:Space Mono,monospace;font-size:22px;font-weight:700;color:' + fg_color + ';">' + str(round(fg_score)) + '</span>'
                    '<span style="font-family:Space Mono,monospace;font-size:12px;color:' + fg_color + ';letter-spacing:0.1em;">' + fg_rating.upper() + '</span>'
                    '<span style="font-family:Space Mono,monospace;font-size:10px;color:#4a4035;">CNN FEAR & GREED INDEX</span>'
                    '</div>',
                    unsafe_allow_html=True
                )

            c1, c2, c3, c4 = st.columns(4)
            bench_delta = ("vs " + d["bench_label"] + ": " + "{:+.2%}".format(d["bench_return"])) if d["bench_return"] else None
            c1.metric("Annual Return", "{:+.2%}".format(d["annual_return"]), bench_delta)
            c2.metric("Volatility", "{:.2%}".format(d["annual_volatility"]), "Risk: " + d["risk_rating"])
            sharpe_q = "good" if d["sharpe_ratio"] > 1 else "average" if d["sharpe_ratio"] > 0 else "poor"
            c3.metric("Sharpe Ratio", "{:.2f}".format(d["sharpe_ratio"]), sharpe_q)
            c4.metric("Max Drawdown", "{:.2%}".format(d["max_drawdown"]), str(d["max_dd_date"])[:10])

            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            c5, c6, c7, c8 = st.columns(4)
            c5.metric("Current Price", "{:.2f}".format(d["current_price"]) if d["current_price"] else "N/A")
            upside_delta = "{:+.1f}% upside".format(d["upside"]) if d["upside"] else None
            c6.metric("Analyst Target", "{:.2f}".format(d["price_target"]) if d["price_target"] else "N/A", upside_delta)
            out_delta = ("vs " + d["bench_label"]) if d["outperformance"] else None
            c7.metric("Outperformance", "{:+.2%}".format(d["outperformance"]) if d["outperformance"] else "N/A", out_delta)
            c8.metric("Risk Rating", d["risk_rating"], d["risk_note"])

            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            sig_col = signal_color(d["options_signal"])
            st.markdown(
                '<div style="background:#0f0f0f;border:1px solid #2a2520;border-left:3px solid ' + sig_col + ';border-radius:6px;padding:14px 20px;">'
                '<span style="font-family:Space Mono,monospace;font-size:10px;color:#4a4035;letter-spacing:0.12em;">OPTIONS SIGNAL</span><br>'
                '<span style="font-family:Space Mono,monospace;font-size:16px;font-weight:700;color:' + sig_col + ';">' + d["options_signal"] + '</span>'
                '</div>',
                unsafe_allow_html=True
            )

        with tabs[1]:
            st.markdown('<p style="font-family:Space Mono,monospace;font-size:10px;color:#c9a84c;letter-spacing:0.15em;margin-bottom:16px;">◈ LATEST INTELLIGENCE</p>', unsafe_allow_html=True)
            if not api_key:
                st.info("Add your Anthropic API key in the sidebar to load news.")
            else:
                with st.spinner("Fetching news..."):
                    news = get_news(ticker, api_key)
                if news:
                    for item in news:
                        st.markdown(
                            '<div style="background:#0f0f0f;border:1px solid #2a2520;border-radius:6px;padding:14px 18px;margin-bottom:10px;">'
                            '<p style="font-family:Syne,sans-serif;font-size:14px;font-weight:600;color:#e8e0cc;margin:0 0 6px 0;">' + item["headline"] + '</p>'
                            '<p style="font-family:Space Mono,monospace;font-size:11px;color:#6b6050;margin:0;">' + item["summary"] + '</p>'
                            '</div>',
                            unsafe_allow_html=True
                        )
                else:
                    st.warning("Could not fetch news.")

        with tabs[2]:
            fig = make_chart([d])
            st.pyplot(fig)
            plt.close(fig)

        with tabs[3]:
            st.markdown('<p style="font-family:Space Mono,monospace;font-size:10px;color:#c9a84c;letter-spacing:0.15em;margin-bottom:16px;">◈ AI PORTFOLIO MANAGER BRIEF</p>', unsafe_allow_html=True)
            if not api_key:
                st.info("Add your Anthropic API key in the sidebar to generate the AI brief.")
            else:
                with st.spinner("Generating AI brief..."):
                    summary = get_ai_summary(d, api_key)
                if summary:
                    st.markdown(
                        '<div style="background:#0f0f0f;border:1px solid #2a2520;border-left:3px solid #c9a84c;border-radius:6px;padding:20px 24px;">'
                        '<p style="font-family:Syne,sans-serif;font-size:15px;line-height:1.8;color:#e8e0cc;margin:0;">' + summary + '</p>'
                        '</div>',
                        unsafe_allow_html=True
                    )

# ══════════════════════════════════════════════════════════════════════════════
# PEER COMPARISON
# ══════════════════════════════════════════════════════════════════════════════
elif mode == "Peer Comparison":
    st.markdown('<p style="font-family:Space Mono,monospace;font-size:10px;color:#c9a84c;letter-spacing:0.15em;margin-bottom:12px;">◈ PEER COMPARISON — Enter up to 4 tickers</p>', unsafe_allow_html=True)
    cols = st.columns([2, 2, 2, 2, 1])
    tickers_input = []
    for i, placeholder in enumerate(["AAPL", "MSFT", "GOOGL", "NVDA"]):
        t = cols[i].text_input("", placeholder=placeholder, key="peer_" + str(i), label_visibility="collapsed").strip().upper()
        if t:
            tickers_input.append(t)
    run_peer = cols[4].button("▶ RUN", use_container_width=True)

    if run_peer and tickers_input:
        results = []
        for t in tickers_input:
            with st.spinner("Analysing " + t + "..."):
                d = analyse_ticker(t)
                if d:
                    results.append(d)

        if not results:
            st.error("No data found.")
            st.stop()

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown('<p style="font-family:Space Mono,monospace;font-size:10px;color:#c9a84c;letter-spacing:0.15em;">◈ COMPARISON TABLE</p>', unsafe_allow_html=True)

        header_cols = st.columns([2, 1.5, 1.5, 1.5, 1.5, 1.5, 2])
        for col, h in zip(header_cols, ["TICKER", "ANN. RETURN", "VOLATILITY", "SHARPE", "MAX DD", "UPSIDE", "SIGNAL"]):
            col.markdown(label(h), unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#2a2520;margin:8px 0;'>", unsafe_allow_html=True)

        for d in results:
            row = st.columns([2, 1.5, 1.5, 1.5, 1.5, 1.5, 2])
            ret_col = "#4caf50" if d["annual_return"] >= 0 else "#c0392b"
            up_col = "#4caf50" if (d["upside"] or 0) >= 0 else "#c0392b"
            sig_col = signal_color(d["options_signal"])
            upside_val = "{:+.1f}%".format(d["upside"]) if d["upside"] is not None else "N/A"
            row[0].markdown(mono(d["ticker"], bold=True, color="#c9a84c"), unsafe_allow_html=True)
            row[1].markdown(mono("{:+.2%}".format(d["annual_return"]), color=ret_col), unsafe_allow_html=True)
            row[2].markdown(mono("{:.2%}".format(d["annual_volatility"])), unsafe_allow_html=True)
            row[3].markdown(mono("{:.2f}".format(d["sharpe_ratio"])), unsafe_allow_html=True)
            row[4].markdown(mono("{:.2%}".format(d["max_drawdown"]), color="#c0392b"), unsafe_allow_html=True)
            row[5].markdown(mono(upside_val, color=up_col), unsafe_allow_html=True)
            row[6].markdown(mono(d["options_signal"].split("·")[0].strip(), size=11, color=sig_col), unsafe_allow_html=True)
            st.markdown("<hr style='border-color:#1a1a1a;margin:4px 0;'>", unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        fig = make_chart(results)
        st.pyplot(fig)
        plt.close(fig)

# ══════════════════════════════════════════════════════════════════════════════
# PORTFOLIO
# ══════════════════════════════════════════════════════════════════════════════
elif mode == "Portfolio":
    st.markdown('<p style="font-family:Space Mono,monospace;font-size:10px;color:#c9a84c;letter-spacing:0.15em;margin-bottom:12px;">◈ PORTFOLIO ANALYSER — One ticker + weight per line</p>', unsafe_allow_html=True)
    portfolio_input = st.text_area("", placeholder="AAPL 30\nMSFT 25\nNVDA 25\nGOOGL 20", height=160, label_visibility="collapsed")
    run_port = st.button("▶ ANALYSE PORTFOLIO")

    if run_port and portfolio_input:
        lines = [l.strip() for l in portfolio_input.strip().split("\n") if l.strip()]
        holdings = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                try:
                    holdings.append({"ticker": parts[0].upper(), "weight": float(parts[1]) / 100})
                except ValueError:
                    pass

        if not holdings:
            st.error("Could not parse input. Format: TICKER WEIGHT on each line.")
            st.stop()

        results = []
        for h in holdings:
            with st.spinner("Analysing " + h["ticker"] + "..."):
                d = analyse_ticker(h["ticker"])
                if d:
                    d["weight"] = h["weight"]
                    results.append(d)

        if not results:
            st.error("No data found.")
            st.stop()

        total_weight = sum(r["weight"] for r in results)
        port_return = sum(r["annual_return"] * r["weight"] for r in results) / total_weight
        port_vol    = sum(r["annual_volatility"] * r["weight"] for r in results) / total_weight
        port_sharpe = sum(r["sharpe_ratio"] * r["weight"] for r in results) / total_weight
        port_dd     = sum(r["max_drawdown"] * r["weight"] for r in results) / total_weight

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown('<p style="font-family:Space Mono,monospace;font-size:10px;color:#c9a84c;letter-spacing:0.15em;">◈ PORTFOLIO SUMMARY</p>', unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Portfolio Return", "{:+.2%}".format(port_return))
        c2.metric("Portfolio Volatility", "{:.2%}".format(port_vol))
        c3.metric("Weighted Sharpe", "{:.2f}".format(port_sharpe))
        c4.metric("Weighted Max DD", "{:.2%}".format(port_dd))

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown('<p style="font-family:Space Mono,monospace;font-size:10px;color:#c9a84c;letter-spacing:0.15em;">◈ HOLDINGS BREAKDOWN</p>', unsafe_allow_html=True)

        header_cols = st.columns([2, 1, 1.5, 1.5, 1.5, 1.5])
        for col, h in zip(header_cols, ["TICKER", "WEIGHT", "ANN. RETURN", "VOLATILITY", "SHARPE", "MAX DD"]):
            col.markdown(label(h), unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#2a2520;margin:8px 0;'>", unsafe_allow_html=True)

        for r in results:
            row = st.columns([2, 1, 1.5, 1.5, 1.5, 1.5])
            ret_col = "#4caf50" if r["annual_return"] >= 0 else "#c0392b"
            row[0].markdown(mono(r["ticker"], bold=True, color="#c9a84c"), unsafe_allow_html=True)
            row[1].markdown(mono("{:.0%}".format(r["weight"])), unsafe_allow_html=True)
            row[2].markdown(mono("{:+.2%}".format(r["annual_return"]), color=ret_col), unsafe_allow_html=True)
            row[3].markdown(mono("{:.2%}".format(r["annual_volatility"])), unsafe_allow_html=True)
            row[4].markdown(mono("{:.2f}".format(r["sharpe_ratio"])), unsafe_allow_html=True)
            row[5].markdown(mono("{:.2%}".format(r["max_drawdown"]), color="#c0392b"), unsafe_allow_html=True)
            st.markdown("<hr style='border-color:#1a1a1a;margin:4px 0;'>", unsafe_allow_html=True)

        if api_key:
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            with st.spinner("Generating portfolio AI brief..."):
                try:
                    client = anthropic.Anthropic(api_key=api_key)
                    holdings_str = ", ".join([r["ticker"] + " (" + "{:.0%}".format(r["weight"]) + ")" for r in results])
                    content = (
                        "Analyze this portfolio: " + holdings_str + ". "
                        "Return: " + "{:.2%}".format(port_return) + ", "
                        "volatility: " + "{:.2%}".format(port_vol) + ", "
                        "Sharpe: " + "{:.2f}".format(port_sharpe) + ", "
                        "max drawdown: " + "{:.2%}".format(port_dd) + ". "
                        "Give a 4-5 sentence institutional assessment. Is it well-diversified? Key risks? Concentration concerns? Speak like a senior portfolio manager."
                    )
                    msg = client.messages.create(
                        model="claude-opus-4-5",
                        max_tokens=350,
                        messages=[{"role": "user", "content": content}]
                    )
                    port_summary = msg.content[0].text
                    st.markdown('<p style="font-family:Space Mono,monospace;font-size:10px;color:#c9a84c;letter-spacing:0.15em;margin-bottom:12px;">◈ AI PORTFOLIO BRIEF</p>', unsafe_allow_html=True)
                    st.markdown(
                        '<div style="background:#0f0f0f;border:1px solid #2a2520;border-left:3px solid #c9a84c;border-radius:6px;padding:20px 24px;">'
                        '<p style="font-family:Syne,sans-serif;font-size:15px;line-height:1.8;color:#e8e0cc;margin:0;">' + port_summary + '</p>'
                        '</div>',
                        unsafe_allow_html=True
                    )
                except Exception as e:
                    st.warning("AI brief failed: " + str(e))