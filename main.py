import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime
import pytz # Indian Timezone ke liye

# --- ⚙️ USER CONFIGURATION (Aapki Details Fixed Hain) ---
TOKEN = "8547643505:AAGvC1rstZsC477y86Y_0iP_7akA6WM9zC0"
CHAT_ID = "1304630088"

# --- 🌍 GLOBAL MARKET WATCHLIST ---
SYMBOLS = {
    # 🇮🇳 India
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "RELIANCE": "RELIANCE.NS",
    
    # 🛢️ Commodities
    "GOLD": "GC=F",
    "CRUDE OIL": "CL=F",
    "NATURAL GAS": "NG=F",
    
    # ₿ Crypto & Forex
    "BITCOIN": "BTC-USD",
    "EUR/USD": "EURUSD=X"
}

# --- 📡 TELEGRAM SENDER (With Indian Time) ---
def send_telegram(message):
    try:
        # Indian Time set karna
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist).strftime('%d-%b %I:%M %p')
        
        # Message me Time jodna
        final_msg = f"⏰ **Scan Time:** {now}\n{message}"
        
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        params = {"chat_id": CHAT_ID, "text": final_msg, "parse_mode": "Markdown"}
        requests.get(url, params=params)
        print("✅ Message Sent to Telegram")
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

# --- 🧠 STRATEGY ENGINE ---
def get_analysis(df):
    price = df['Close']
    current = price.iloc[-1]
    
    # 1. Volume Profile (POC) Logic
    vol = df['Volume']
    bins = np.linspace(price.min(), price.max(), 50)
    digitized = np.digitize(price, bins)
    vp = np.zeros(len(bins))
    for i in range(len(vol)):
        idx = digitized[i]
        if 0 <= idx < len(bins):
            vp[idx] += vol.iloc[i]
    poc = bins[np.argmax(vp)]
    
    # 2. Trend Logic (20 SMA)
    sma = price.rolling(20).mean().iloc[-1]
    trend = "UP 🟢" if current > sma else "DOWN 🔴"
    
    # 3. Signal Generation
    signal = "WAIT ✋"
    
    # Buy Condition: Price POC ke upar aur Trend Up
    if current > poc and "UP" in trend:
        signal = "BUY ✅"
        
    # Sell Condition: Price POC ke niche aur Trend Down
    elif current < poc and "DOWN" in trend:
        signal = "SELL ❌"
    
    return current, poc, trend, signal

# --- 🚀 MAIN EXECUTION ---
if __name__ == "__main__":
    print("🔍 Starting Scan...")
    
    # Report shuru karein
    report = "🤖 **ALADDIN-PRO MARKET SCAN** 🤖\n"
    signal_found = False
    
    for name, sym in SYMBOLS.items():
        try:
            # Data download (5 din ka data, 1 ghante ka candle)
            df = yf.download(sym, period="5d", interval="1h", progress=False)
            
            if len(df) > 20:
                curr, poc, trend, sig = get_analysis(df)
                
                # Report me add karein
                report += f"\n➖➖➖➖➖➖➖➖\n"
                report += f"📊 **{name}**\n"
                report += f"💰 Price: `{curr:.2f}`\n"
                report += f"🧲 POC: `{poc:.2f}`\n"
                report += f"🚦 Trend: {trend}\n"
                report += f"📢 Signal: **{sig}**\n"
                
                # Agar WAIT nahi hai, matlab Buy/Sell hai
                if "WAIT" not in sig:
                    signal_found = True
                    
        except Exception as e:
            print(f"Skipping {name}: {e}")
            
    # Agar koi strong signal mila ya report ban gayi to bheje
    # (Abhi testing ke liye hum hamesha bhejenge)
    send_telegram(report + "\n🚀 **Market Update Complete!**")
              
