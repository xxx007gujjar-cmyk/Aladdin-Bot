import yfinance as yf
import pandas as pd
import requests
import numpy as np
from datetime import datetime
import pytz

# --- CONFIG ---
TOKEN = "8547643505:AAGvC1rstZsC477y86Y_0iP_7akA6WM9zC0"
CHAT_ID = "1304630088"

SYMBOLS = [
    "BTC-USD", "EURUSD=X", "GC=F", 
    "CL=F", "^NSEI", "^NSEBANK"
]

def send_telegram(msg):
    try:
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist).strftime('%I:%M %p')
        final_msg = f"⏰ **Scan: {now}**\n\n{msg}"
        
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.get(url, params={"chat_id": CHAT_ID, "text": final_msg, "parse_mode": "Markdown"})
    except:
        pass

def get_signal(df):
    try:
        close = df['Close']
        curr = close.iloc[-1]
        
        # Simple Logic for Test
        sma = close.rolling(20).mean().iloc[-1]
        trend = "🟢 UP" if curr > sma else "🔴 DOWN"
        
        return curr, trend
    except:
        return 0, "Error"

if __name__ == "__main__":
    report = ""
    print("Scanning...")
    
    for sym in SYMBOLS:
        try:
            # Note: Trying to fix Yahoo blocking by using 'progress=False'
            df = yf.download(sym, period="5d", interval="1h", progress=False)
            
            if not df.empty and len(df) > 5:
                price, trend = get_signal(df)
                # Har symbol ka data add karega (Filter hata diya hai)
                report += f"📊 *{sym}*\n💰 {price:.2f} | {trend}\n\n"
            else:
                report += f"⚠️ *{sym}*: No Data (Yahoo Block)\n\n"
                
        except Exception as e:
            report += f"❌ *{sym}*: Error {str(e)}\n\n"

    if report == "":
        report = "Critical Error: Script ran but generated no output."
        
    send_telegram(report)
    print("Done")
    
              
