import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import pytz
from datetime import datetime
import os
import time
from dotenv import load_dotenv
import streamlit.components.v1 as components

# -------------------------------
# Load environment variables
# -------------------------------
load_dotenv()
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# -------------------------------
# Streamlit Page Setup
# -------------------------------
st.set_page_config(page_title="🌍 Global Stock & Weather Dashboard", page_icon="💹", layout="wide")
st.title("🌍 Real-Time Stock, Weather, and Time Dashboard")

# -------------------------------
# Helper Functions
# -------------------------------
def fetch_weather(city):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        res = requests.get(url, timeout=5)
        data = res.json()
        if res.status_code != 200:
            return None, None, None
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"].title()
        icon = data["weather"][0]["icon"]
        return temp, desc, icon
    except Exception:
        return None, None, None


def fetch_stock_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="1m")
        if data.empty:
            return None, None, None
        latest_price = data["Close"].iloc[-1]
        open_price = data["Open"].iloc[0]
        prev_close = ticker.history(period="2d", interval="1d")["Close"].iloc[-2]
        return latest_price, open_price, prev_close
    except Exception:
        return None, None, None

# -------------------------------
# Initialize Session State
# -------------------------------
tickers = [f"{s}.NS" for s in ["RELIANCE", "TCS", "INFY"]]
cities = ["New York", "London", "New Delhi"]
timezones = {
    "New York": "America/New_York",
    "London": "Europe/London",
    "New Delhi": "Asia/Kolkata",
}

if "prices" not in st.session_state:
    st.session_state.prices = {t: [] for t in tickers}
    st.session_state.timestamps = []
if "weather" not in st.session_state:
    st.session_state.weather = {}

# -------------------------------
# CSS Styling
# -------------------------------
st.markdown("""
<style>
.delta-red { color: #ff4d4d; font-weight: 600; }
.delta-green { color: #00c853; font-weight: 600; }
.metric-compact { margin-bottom: 0.4rem; }
.clock {
    font-size: 1.4rem;
    font-weight: 600;
    color: #00FFB3;
    text-shadow: 0 0 10px #00FFB3;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Placeholders
# -------------------------------
weather_placeholder = st.empty()
stocks_placeholder = st.empty()
chart_placeholder = st.empty()

# -------------------------------
# Live Dashboard Loop
# -------------------------------
while True:
    # ========== WEATHER & TIMES ==========
    with weather_placeholder.container():
        st.subheader("🌦️ Global Weather & Times")
        wc1, wc2, wc3, wc4 = st.columns(4)
        for col, city in zip([wc1, wc2, wc3], cities):
            temp, desc, icon = fetch_weather(city)
            tz = pytz.timezone(timezones[city])
            local_time = datetime.now(tz).strftime("%I:%M:%S %p %Z")
            with col:
                if temp is not None:
                    st.markdown(f"**{city}**")
                    st.markdown(f"<p class='clock'>🕒 {local_time}</p>", unsafe_allow_html=True)
                    st.image(f"http://openweathermap.org/img/wn/{icon}@2x.png", width=60)
                    st.markdown(f"🌡️ {temp:.1f}°C — {desc}")
                else:
                    st.markdown(f"**{city}**")
                    st.markdown(f"<p class='clock'>🕒 {local_time}</p>", unsafe_allow_html=True)
                    st.markdown("❌ Weather unavailable")

        # Local clock (real-time via browser)
        with wc4:
            st.markdown("**Local Device Time**")
            components.html("""
                <div style="font-size:1.4rem; font-weight:600; color:#00FFB3; text-shadow:0 0 10px #00FFB3;">
                    🕒 <span id="local-clock"></span>
                </div>
                <script>
                function updateClock() {
                    const now = new Date();
                    const timeString = now.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit', second:'2-digit', hour12:true});
                    document.getElementById("local-clock").textContent = timeString;
                }
                setInterval(updateClock, 1000);
                updateClock();
                </script>
            """, height=50)

    # ========== STOCKS ==========
    with stocks_placeholder.container():
        st.markdown("---")
        st.subheader("💹 Live Indian Stock Prices (Yahoo Finance)")

        for t in tickers:
            current, open_price, prev_close = fetch_stock_price(t)
            if current is None:
                continue
            st.session_state.prices[t].append(current)
            st.session_state.timestamps.append(pd.Timestamp.now())

            change = current - prev_close
            pct_change = (change / prev_close) * 100 if prev_close else 0
            delta_color_class = "delta-green" if change >= 0 else "delta-red"
            arrow = "🟢⬆️" if change > 0 else "🔴⬇️" if change < 0 else "⚪"

            st.markdown(
                f"""
                <div class="metric-compact" style="margin-bottom: 25px;">
                    <b>{t}</b><br>
                    <span style="font-size:1.6rem;">₹{current:.2f}</span><br>
                    <span class="{delta_color_class}">{arrow} {change:+.2f} ({pct_change:+.2f}%)</span>
                </div>
                """,
                unsafe_allow_html=True
            )

    # ========== CHART ==========
    with chart_placeholder.container():
        if len(st.session_state.timestamps) > 1:
            min_len = min([len(st.session_state.timestamps)] + [len(st.session_state.prices[t]) for t in tickers])
            trimmed_timestamps = st.session_state.timestamps[:min_len]
            df = pd.DataFrame(index=trimmed_timestamps)
            for t in tickers:
                df[t] = st.session_state.prices[t][:min_len]
            st.line_chart(df)

    time.sleep(1)
