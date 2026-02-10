import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import pytz

# --- ⚙️ CONFIGURATION ---
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

# --- 🧠 ADVANCED STRATEGY ENGINES ---

# 1. Fibonacci Golden Zone (0.5 - 0.618)
def get_fibonacci(df):
    recent_high = df['High'][-50:].max()
    recent_low = df['Low'][-50:].min()
    curr = df['Close'].iloc[-1]
    
    fib_50 = recent_low + 0.5 * (recent_high - recent_low)
    fib_618 = recent_low + 0.618 * (recent_high - recent_low)
    
    # Check if price is in Golden Pocket
    if fib_618 <= curr <= fib_50: # Downtrend Retracement
        return "GOLDEN ZONE (Bearish) 🐻", fib_618
    elif fib_50 <= curr <= fib_618: # Uptrend Retracement (Logic varies by trend)
        return "GOLDEN ZONE (Bullish) 🐂", fib_618
    else:
        return "No Fib Level", 0

# 2. SMC: Fair Value Gap (FVG)
def check_fvg(df):
    if len(df) < 3: return False
    # Bullish FVG: Candle 1 High < Candle 3 Low
    c1_high = df['High'].iloc[-3]
    c3_low = df['Low'].iloc[-1]
    if c3_low > c1_high: return "Bullish FVG 🟢"
    
    # Bearish FVG: Candle 1 Low > Candle 3 High
    c1_low = df['Low'].iloc[-3]
    c3_high = df['High'].iloc[-1]
    if c3_high < c1_low: return "Bearish FVG 🔴"
    
    return "None"

# 3. CRT: Liquidity Sweep (Turtle Soup)
def check_crt(df):
    # Pichle 10 candles ka low/high dekhein
    prev_lows = df['Low'].iloc[-10:-1].min()
    prev_highs = df['High'].iloc[-10:-1].max()
    
    curr_low = df['Low'].iloc[-1]
    curr_high = df['High'].iloc[-1]
    curr_close = df['Close'].iloc[-1]
    
    # Bullish Sweep: Low toda par wapas upar close hua
    if curr_low < prev_lows and curr_close > prev_lows:
        return "LIQUIDITY GRAB (Buy) 💎"
        
    # Bearish Sweep: High toda par wapas neeche close hua
    if curr_high > prev_highs and curr_close < prev_highs:
        return "LIQUIDITY GRAB (Sell) 🩸"
        
    return "None"

# 4. Volume Profile (POC) & 18-YCT Trend
def get_main_logic(df):
    price = df['Close']
    curr = price.iloc[-1]
    
    # Volume Profile POC
    vol = df['Volume']
    bins = np.linspace(price.min(), price.max(), 50)
    digitized = np.digitize(price, bins)
    vp = np.zeros(len(bins))
    for i in range(len(vol)):
        idx = digitized[i]
        if 0 <= idx < len(bins):
            vp[idx] += vol.iloc[i]
    poc = bins[np.argmax(vp)]
    
    # 18-YCT (EMA Trend)
    ema_18 = price.ewm(span=18, adjust=False).mean().iloc[-1]
    trend = "UP 🔥" if curr > ema_18 else "DOWN ❄️"
    
    return curr, poc, trend, ema_18

# --- 🚀 MASTER ANALYSIS ---
def analyze_market(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="10d", interval="1h")
        if df.empty or len(df) < 50: return None
        
        curr, poc, trend, ema_18 = get_main_logic(df)
        fvg = check_fvg(df)
        crt = check_crt(df)
        fib_status, fib_level = get_fibonacci(df)
        
        # --- SCORING SYSTEM (Out of 5) ---
        score = 0
        signal = "WAIT ✋"
        
        # BUY SCORING
        if "UP" in trend: score += 1
        if curr > poc: score += 1
        if "Bullish" in fvg: score += 1
        if "Bullish" in fib_status: score += 1
        if "Buy" in crt: score += 2 # CRT is powerful
        
        # SELL SCORING
        if "DOWN" in trend: score -= 1
        if curr < poc: score -= 1
        if "Bearish" in fvg: score -= 1
        if "Bearish" in fib_status: score -= 1
        if "Sell" in crt: score -= 2
        
        # --- DECISION ---
        atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
        
        if score >= 3: # Strong Buy
            signal = "SNIPER BUY 🎯✅"
            sl = curr - (2 * atr)
            tp = curr + (3 * atr)
        elif score <= -3: # Strong Sell
            signal = "SNIPER SELL 🎯❌"
            sl = curr + (2 * atr)
            tp = curr - (3 * atr)
        else:
            sl, tp = 0, 0
            
        return {
            "price": curr, "poc": poc, "trend": trend,
            "fvg": fvg, "crt": crt, "signal": signal,
            "sl": sl, "tp": tp, "score": score
        }
    except:
        return None

# --- MAIN LOOP ---
if __name__ == "__main__":
    report = "🏛️ **ALADDIN-PRO: GOD MODE** 🏛️\n"
    report += "_SMC + ICT + Fib + CRT + Vol_\n"
    
    for name, sym in SYMBOLS.items():
        data = analyze_market(sym)
        if data:
            # Sirf Strong Signals bhejein (Wait wala bheed na kare)
            if "WAIT" not in data['signal']:
                report += f"\n📊 **{name}**\n"
                report += f"💰 Price: `{data['price']:.2f}`\n"
                report += f"🚦 Trend (18YCT): {data['trend']}\n"
                report += f"🧱 Structure: {data['fvg']} | {data['crt']}\n"
                report += f"📢 Signal: **{data['signal']}** (Score: {abs(data['score'])}/5)\n"
                
                # Trade Setup
                report += f"⚡ **ENTRY SETUP:**\n"
                report += f"🛑 SL: `{data['sl']:.2f}`\n"
                report += f"🎯 TP: `{data['tp']:.2f}`\n"
                report += "➖➖➖➖➖➖➖➖"
    
    if "Price" in report: # Agar koi signal mila
        send_telegram(report)
    else:
        # Agar market boring hai
        print("No High Probability Setup Found")
        
