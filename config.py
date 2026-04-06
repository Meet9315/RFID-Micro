"""
Centralized configuration for the PoCS Secure Dashboard project.
All shared constants, Firebase config, and environment variable loading live here.
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# -------------------
# Firebase Configuration
# -------------------
FIREBASE_URL = "https://micro-project-ee399-default-rtdb.firebaseio.com"

# -------------------
# API Keys
# -------------------
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# -------------------
# AES / DES Encryption Config
# -------------------
AES_KEY_SIZE = 16   # 128-bit AES key
DES_KEY_SIZE = 8    # 64-bit DES key
AES_BLOCK_SIZE = 16
DES_BLOCK_SIZE = 8

# -------------------
# Default Data
# -------------------
DEFAULT_USER_ID = "UID12345"    # Default RFID UID for testing

# -------------------
# Dashboard Config
# -------------------
STOCK_TICKERS = [f"{s}.NS" for s in ["RELIANCE", "TCS", "INFY"]]

CITIES = ["New York", "London", "New Delhi"]

TIMEZONES = {
    "New York": "America/New_York",
    "London": "Europe/London",
    "New Delhi": "Asia/Kolkata",
}

# -------------------
# Validation
# -------------------
def validate_config():
    """Check that required environment variables are set. Returns list of warnings."""
    warnings = []
    if not WEATHER_API_KEY:
        warnings.append("WEATHER_API_KEY is not set. Weather data will be unavailable.")
    if not GEMINI_API_KEY:
        warnings.append("GEMINI_API_KEY is not set. AI Advisory features will be unavailable.")
    return warnings
