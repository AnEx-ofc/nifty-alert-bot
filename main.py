# main.py
import yfinance as yf
import requests
import os
import pytz
from datetime import datetime

# --- CONFIGURATION ---
# 1. Enter your Topic Name below OR use GitHub Secrets (Recommended)
TOPIC_NAME = os.environ.get("TOPIC_NAME", "nifty_alert_test_07121996") 
TEST_MODE = os.environ.get("TEST_MODE", "false").lower() == "true" or "--test" in os.sys.argv
# ---------------------

def send_notification(title, message, priority="default"):
    try:
        print(f"""\
              \r==================================Sending notification=====================================
              \r{title}
              \r-------------------------------------------------------------------------------------------
              \r{message}
            """)
        
        requests.post(
            f"https://ntfy.sh/{TOPIC_NAME}",
            data=message.encode(encoding='utf-8'),
            headers={
                "Title": title.encode('utf-8'), # Ensure title is also encoded to avoid encoding errors with emojis
                "Priority": priority,
                "Tags": "chart_with_downwards_trend,warning"
            }
        )
        print("✅ Notification sent!")
    except Exception as e:
        print(f"❌ Error sending notification: {e}")

def check_market():
    ticker = "^NSEI" # Nifty 50 Symbol
    
    print("Fetching market data...")
    # 1. Get 1 Year History to find the True All-Time High (ATH)
    history = yf.download(ticker, period="3y", interval="1wk", progress=False)
    
    if history.empty:
        print("Error: No data fetched.")
        return

    # Find the ATH from the last 365 days
    ath_price = float(history['High'].max().iloc[0] if not history.empty else 0.0)
    
    # 2. Get Live Price (Latest minute data)
    live_data = yf.download(ticker, period="1d", interval="1m", progress=False)
    
    # Fallback if live data is empty (e.g., pre-market)
    current_price = float((live_data['Close'].iloc[-1] if not live_data.empty else history['Close'].iloc[-1]).iloc[0])
    
    # 3. Calculate Drawdown Percentage
    drop_pct = ((current_price - ath_price) / ath_price) * 100.0
    
    # Time for log
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist).strftime('%H:%M')
    
    
    # print(f"ATH: {ath_price} | Current: {current_price} | Drop: {drop_pct}%")
    print(f"ATH: {ath_price:.2f} | Current: {current_price:.2f} | Drop: {drop_pct:.2f}%")

    # --- ALERT LOGIC ---
    # Change -5.0 to -0.01 if you want to test it TODAY
    
    if TEST_MODE:
        title = f"🚨 TEST ALERT: {drop_pct:.2f}%"
        msg = f"Current: {current_price:.0f}\nATH: {ath_price:.0f}\nTime: {now_ist}"
        send_notification(title, msg, priority="high")
    
    elif drop_pct <= -5.0:
        title = f"🚨 Nifty Crash Alert: {drop_pct:.2f}%"
        msg = f"Current: {current_price:.0f}\nATH: {ath_price:.0f}\nTime: {now_ist}"
        send_notification(title, msg, priority="high")
        
    elif drop_pct <= -10.0:
        title = f"💣 MARKET CRASH: {drop_pct:.2f}%"
        msg = f"Current: {current_price:.0f}\nDEPLOY CAPITAL NOW!"
        send_notification(title, msg, priority="urgent")
        
    elif drop_pct <= -15.0:
        title = f"🔥 MARKET MELTDOWN: {drop_pct:.2f}%"
        msg = f"Current: {current_price:.0f}\nALL HANDS ON DECK!"
        send_notification(title, msg, priority="emergency")     
    
    elif drop_pct <= -20.0:
        title = f"💥 MARKET APOCALYPSE: {drop_pct:.2f}%"
        msg = f"Current: {current_price:.0f}\nSELL EVERYTHING!"
        send_notification(title, msg, priority="critical")
        
    else:
        print(f"Market is safe (Down {drop_pct:.2f}%). No alert sent.")

if __name__ == "__main__":
    check_market()