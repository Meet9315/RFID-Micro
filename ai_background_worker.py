import time
import requests
import google.generativeai as genai
import yfinance as yf
from config import GEMINI_API_KEY, FIREBASE_URL

def check_market_health():
    print("Fetching live market data...")
    # Fetch a few major crypto tickets
    try:
        btc_data = yf.Ticker("BTC-USD").history(period="1d", interval="1m")
        eth_data = yf.Ticker("ETH-USD").history(period="1d", interval="1m")
        
        btc_drop = (btc_data['Open'].iloc[0] - btc_data['Close'].iloc[-1]) / btc_data['Open'].iloc[0]
        eth_drop = (eth_data['Open'].iloc[0] - eth_data['Close'].iloc[-1]) / eth_data['Open'].iloc[0]
        
        # Simple heuristic to save Gemini Quota, only ask Gemini if there is a noticeable drop > 2%
        if btc_drop > 0.02 or eth_drop > 0.02:
            print("Significant drop detected. Asking Gemini to verify crash...")
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"BTC dropped {btc_drop*100:.2f}% and ETH dropped {eth_drop*100:.2f}% today. Is this considered a severe market crash? Reply ONLY with 'TRUE' or 'FALSE'."
            response = model.generate_content(prompt)
            print(f"Gemini says: {response.text}")
            
            if "TRUE" in response.text.upper():
                return True
        else:
            print("Market is relatively stable. (Skipped Gemini check to save 15 RPM quota)")
            return False
            
    except Exception as e:
        print(f"Error fetching data: {e}")
    
    return False

def push_alert_to_firebase(is_crash):
    url = f"{FIREBASE_URL}/public/market_alert.json"
    data = {"market_crash": is_crash}
    requests.put(url, json=data)
    print(f"Pushed market_crash={is_crash} to Firebase.")

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY not found in code. Make sure config.py is loaded properly.")
    else:
        print("Starting PoCS Background AI Worker (Runs every 60 seconds)...")
        # Initialize the firebase path to false so ESP32 doesn't trigger immediately
        push_alert_to_firebase(False)
        
        while True:
            is_crash = check_market_health()
            push_alert_to_firebase(is_crash)
            print("Sleeping for 60 seconds...\n")
            time.sleep(60)
