import yfinance as yf
import pandas as pd
import requests
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
    except Exception as e:
        print(f"Telegram Fail: {e}")

def get_signal(symbol):
    try:
        # Ticker method use kar rahe hain jo zyada stable hai
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5d", interval="1h")
        
        if df.empty:
            return 0, "⚠️ Empty Data"
            
        # Data Clean karna
        curr = df['Close'].iloc[-1]
        
        # Simple Logic
        sma = df['Close'].rolling(20).mean().iloc[-1]
        
        if pd.isna(sma): 
            return curr, "Wait (Not enough data)"
            
        trend = "🟢 UP" if curr > sma else "🔴 DOWN"
        return curr, trend
        
    except Exception as e:
        return 0, f"❌ Err: {str(e)}"

if __name__ == "__main__":
    report = ""
    print("Starting Scan...")
    
    for sym in SYMBOLS:
        price, status = get_signal(sym)
        report += f"📊 *{sym}*\n💰 {price:.2f} | {status}\n\n"
            
    if not report:
        report = "System Error: No report generated."
        
    send_telegram(report)
    print("Done")
    
