import time
import requests
import google.generativeai as genai
import yfinance as yf
from config import GEMINI_API_KEY, FIREBASE_URL, WEATHER_API_KEY

def check_market_and_weather():
    print("Fetching live market and weather data...")
    btc_price = 0
    weather_desc = "Unknown"
    is_crash = False
    
    # 1. Fetch Weather
    try:
        if WEATHER_API_KEY:
            clean_key = WEATHER_API_KEY.strip()
            city = "New York" # Default city for idle feed
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={clean_key}&units=metric"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                temp = data["main"]["temp"]
                desc = data["weather"][0]["description"]
                weather_desc = f"{temp:.1f}C {desc.title()}"
    except Exception as e:
        print(f"Weather error: {e}")

    # 2. Fetch Market
    try:
        btc_data = yf.Ticker("BTC-USD").history(period="1d", interval="1m")
        eth_data = yf.Ticker("ETH-USD").history(period="1d", interval="1m")
        
        btc_price = btc_data['Close'].iloc[-1]
        
        btc_drop = (btc_data['Open'].iloc[0] - btc_data['Close'].iloc[-1]) / btc_data['Open'].iloc[0]
        eth_drop = (eth_data['Open'].iloc[0] - eth_data['Close'].iloc[-1]) / eth_data['Open'].iloc[0]
        
        if btc_drop > 0.02 or eth_drop > 0.02:
            print("Significant drop detected. Asking Gemini to verify crash...")
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"BTC dropped {btc_drop*100:.2f}% and ETH dropped {eth_drop*100:.2f}% today. Is this considered a severe market crash? Reply ONLY with 'TRUE' or 'FALSE'."
            response = model.generate_content(prompt)
            print(f"Gemini says: {response.text}")
            if "TRUE" in response.text.upper():
                is_crash = True
        else:
            print("Market is relatively stable. (Skipped Gemini check)")
            is_crash = False
    except Exception as e:
        print(f"Market error: {e}")
    
    return is_crash, weather_desc, btc_price

def push_alert_to_firebase(is_crash):
    url = f"{FIREBASE_URL}/public/market_alert.json"
    data = {"market_crash": is_crash}
    requests.put(url, json=data)

def push_feed_to_firebase(weather, btc_price):
    url = f"{FIREBASE_URL}/public/idle_feed.json"
    feed_msg = f"NY:{weather} | BTC:${btc_price:.0f}"
    data = {"feed": feed_msg[:32]} # Cap string length to 32 max for ESP32 LCD logic
    requests.put(url, json=data)
    print(f"Pushed to idle_feed: {data['feed']}")

if __name__ == "__main__":
    print("Starting PoCS Background AI + Feed Worker (Runs every 60 seconds)...")
    push_alert_to_firebase(False)
    
    while True:
        is_crash, weather, btc = check_market_and_weather()
        push_alert_to_firebase(is_crash)
        if btc > 0:
            push_feed_to_firebase(weather, btc)
        print("Sleeping for 60 seconds...\n")
        time.sleep(60)

