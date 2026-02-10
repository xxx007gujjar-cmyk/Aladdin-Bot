import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import pytz

# --- ⚙️ USER CONFIGURATION ---
TOKEN = "8547643505:AAGvC1rstZsC477y86Y_0iP_7akA6WM9zC0"
CHAT_ID = "1304630088"

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

# --- 📡 TELEGRAM SENDER ---
def send_telegram(message):
    try:
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist).strftime('%d-%b %I:%M %p')
        final_msg = f"⏰ **Scan Time:** {now}\n{message}"
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        params = {"chat_id": CHAT_ID, "text": final_msg, "parse_mode": "Markdown"}
        requests.get(url, params=params)
    except:
        pass

# --- 🧠 STRATEGY ENGINE ---
def get_analysis(symbol):
    try:
        # ✅ FIX: Using the working method
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5d", interval="1h")
        
        if df.empty or len(df) < 20: return None
        
        price = df['Close']
        current = price.iloc[-1]
        
        # 1. Volume Profile (POC)
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
        if current > poc and "UP" in trend: signal = "BUY ✅"
        elif current < poc and "DOWN" in trend: signal = "SELL ❌"
        
        return current, poc, trend, signal
    except:
        return None

# --- 🚀 MAIN EXECUTION ---
if __name__ == "__main__":
    report = "🤖 **ALADDIN-PRO SIGNALS** 🤖\n"
    
    for name, sym in SYMBOLS.items():
        result = get_analysis(sym)
        if result:
            curr, poc, trend, sig = result
            
            # Report Formatting
            report += f"\n📊 **{name}**\n"
            report += f"💰 Price: `{curr:.2f}`\n"
            report += f"🧲 POC: `{poc:.2f}`\n"
            report += f"🚦 Trend: {trend}\n"
            report += f"📢 Signal: **{sig}**\n"
            report += "➖➖➖➖➖➖➖➖"
            
    send_telegram(report)
    print("Done")
