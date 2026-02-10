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
        now = datetime.now(ist).strftime('%I:%M %p')
        final_msg = f"⏰ **Scan Time:** {now}\n{message}"
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        params = {"chat_id": CHAT_ID, "text": final_msg, "parse_mode": "Markdown"}
        requests.get(url, params=params)
    except:
        pass

# --- 🧠 TECHNICAL ENGINES ---

# 1. Volume Profile POC (Support/Resistance)
def get_poc(df):
    price = df['Close']
    vol = df['Volume']
    bins = np.linspace(price.min(), price.max(), 50)
    digitized = np.digitize(price, bins)
    vp = np.zeros(len(bins))
    for i in range(len(vol)):
        idx = digitized[i]
        if 0 <= idx < len(bins):
            vp[idx] += vol.iloc[i]
    return bins[np.argmax(vp)]

# 2. SMC FVG (Fair Value Gap) on 5 Min
def check_fvg(df):
    if len(df) < 3: return False, False
    # Bullish FVG
    c1_high = df['High'].iloc[-3]
    c3_low = df['Low'].iloc[-1]
    bull_fvg = c3_low > c1_high
    
    # Bearish FVG
    c1_low = df['Low'].iloc[-3]
    c3_high = df['High'].iloc[-1]
    bear_fvg = c3_high < c1_low
    
    return bull_fvg, bear_fvg

# 3. CRT (Liquidity Sweep) on 5 Min
def check_crt(df):
    # Check last 10 candles for a sweep
    prev_lows = df['Low'].iloc[-15:-1].min()
    prev_highs = df['High'].iloc[-15:-1].max()
    curr_low = df['Low'].iloc[-1]
    curr_high = df['High'].iloc[-1]
    curr_close = df['Close'].iloc[-1]
    
    # Bullish Sweep (Low toda par close upar)
    bull_sweep = curr_low < prev_lows and curr_close > prev_lows
    # Bearish Sweep (High toda par close neeche)
    bear_sweep = curr_high > prev_highs and curr_close < prev_highs
    
    return bull_sweep, bear_sweep

# --- 🚀 MASTER ANALYSIS ---
def analyze_fractal(symbol):
    try:
        ticker = yf.Ticker(symbol)
        
        # --- STEP 1: HTF ANALYSIS (1 Hour) ---
        # Trend aur Direction pata karne ke liye
        df_1h = ticker.history(period="5d", interval="1h")
        if df_1h.empty or len(df_1h) < 50: return None
        
        curr_price = df_1h['Close'].iloc[-1]
        poc_1h = get_poc(df_1h)
        ema_50 = df_1h['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
        
        htf_bias = "NEUTRAL"
        if curr_price > ema_50 and curr_price > poc_1h:
            htf_bias = "BULLISH 🐂"
        elif curr_price < ema_50 and curr_price < poc_1h:
            htf_bias = "BEARISH 🐻"
            
        # --- STEP 2: LTF ANALYSIS (5 Min) ---
        # Pin Point Entry (SMC + CRT)
        df_5m = ticker.history(period="1d", interval="5m")
        if df_5m.empty or len(df_5m) < 20: return None
        
        fvg_bull, fvg_bear = check_fvg(df_5m)
        crt_bull, crt_bear = check_crt(df_5m)
        
        # RSI for Momentum
        delta = df_5m['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_5m = rsi.iloc[-1]
        
        # --- STEP 3: CONFLUENCE (Matching) ---
        signal = "WAIT ✋"
        reasons = []
        
        # LOGIC FOR BUY: HTF Bullish + (LTF FVG OR LTF Sweep) + RSI Oversold
        if "BULLISH" in htf_bias:
            if (fvg_bull or crt_bull) and rsi_5m < 60:
                signal = "SNIPER BUY 🎯✅"
                if fvg_bull: reasons.append("5m FVG Created")
                if crt_bull: reasons.append("Liquidity Swept")
                if rsi_5m < 40: reasons.append("Discount Price")

        # LOGIC FOR SELL: HTF Bearish + (LTF FVG OR LTF Sweep) + RSI Overbought
        elif "BEARISH" in htf_bias:
            if (fvg_bear or crt_bear) and rsi_5m > 40:
                signal = "SNIPER SELL 🎯❌"
                if fvg_bear: reasons.append("5m FVG Created")
                if crt_bear: reasons.append("Liquidity Swept")
                if rsi_5m > 60: reasons.append("Premium Price")
        
        # Stop Loss & Target Calculation (Based on 5m ATR)
        atr_5m = (df_5m['High'] - df_5m['Low']).rolling(14).mean().iloc[-1]
        sl, tp = 0, 0
        if "BUY" in signal:
            sl = curr_price - (2 * atr_5m)
            tp = curr_price + (4 * atr_5m) # 1:2 Risk Reward
        elif "SELL" in signal:
            sl = curr_price + (2 * atr_5m)
            tp = curr_price - (4 * atr_5m)
            
        return {
            "price": curr_price, "htf": htf_bias,
            "signal": signal, "reasons": reasons,
            "sl": sl, "tp": tp, "rsi": rsi_5m
        }

    except Exception as e:
        return None

# --- MAIN LOOP ---
if __name__ == "__main__":
    report = "🦅 **FRACTAL GOD MODE** 🦅\n"
    report += "_(1H Trend + 5M SMC/CRT Entry)_\n"
    
    for name, sym in SYMBOLS.items():
        data = analyze_fractal(sym)
        
        if data:
            # Sirf Strong Signals ya clear trends dikhaye
            icon = "⏳"
            if "SNIPER" in data['signal']: icon = "🔥"
            
            report += f"\n{icon} **{name}**\n"
            report += f"🔭 1H View: {data['htf']}\n"
            report += f"🔬 5M Signal: **{data['signal']}**\n"
            
            if data['reasons']:
                report += f"✅ Conf: {', '.join(data['reasons'])}\n"
                
            if "SNIPER" in data['signal']:
                report += f"⚡ **SETUP:**\n"
                report += f"🛑 SL: `{data['sl']:.2f}`\n"
                report += f"🎯 TP: `{data['tp']:.2f}`\n"
                
            report += "➖➖➖➖"
            
    send_telegram(report)
    print("Done")
    
