# main.py
import yfinance as yf
import requests
import os
import pytz
from datetime import datetime

PERIOD = "3y" # Lookback period for ATH calculation (e.g., "1y", "3y", "5y")

# --- CONFIGURATION ---
# 1. Enter your Topic Name below OR use GitHub Secrets (Recommended)
TOPIC_NAME = os.environ.get("TOPIC_NAME", "nifty_alert_test_07121996") 
TEST_MODE = os.environ.get("TEST_MODE", "false").lower() == "true" or "--test" in os.sys.argv
NO_NOTIFY = os.environ.get("NO_NOTIFY", "false").lower() == "true" or "--no-notify" in os.sys.argv
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
    history = yf.download(ticker, period=PERIOD, interval="1wk", progress=False)
    
    if history.empty:
        print("Error: No data fetched.")
        return

    # Find the ATH from the last 365 days
    ath_price = float(history['High'].max().iloc[0] if not history.empty else 0.0)
    
    # 2. Get Live Price (Latest minute data)
    live_data = yf.download(ticker, period="1d", interval="1m", progress=False)
    if live_data.empty:
        print("Error: No live data fetched.")
        return
    
    # Fallback if live data is empty (e.g., pre-market)
    current_price = float((live_data['Close'].iloc[-1]).iloc[0])
    todays_low = float(live_data['Low'].min().iloc[0])
    
    # 3. Calculate Drawdown Percentage
    drop_pct = ((current_price - ath_price) / ath_price) * 100.0
    lowest_drop_pct = ((todays_low - ath_price) / ath_price) * 100.0
    
    # Time for log
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist).strftime('%H:%M')
    
    
    # print(f"ATH: {ath_price} | Current: {current_price} | Drop: {drop_pct}%")
    print(f"ATH: {ath_price:.2f} | Current: {current_price:.2f} | Drop: {drop_pct:.2f}%")

    # --- ALERT LOGIC ---
    # Change -5.0 to -0.01 if you want to test it TODAY
    
    msg_base = f"Time: {now_ist}\nCurrent: {current_price:.0f}\nToday's Low: {todays_low:.0f}\n{PERIOD}'s ATH: {ath_price:.0f}\nDrop: {drop_pct:.2f}%\nLowest Drop: {lowest_drop_pct:.2f}%"
    
    if TEST_MODE:
        title = f"🚨 TEST ALERT: {lowest_drop_pct:.2f}%"
        msg = f"{msg_base}\nThis is a test notification."
        send_notification(title, msg, priority="high")
        
    if NO_NOTIFY:
        print("🚫 NO_NOTIFY is set to true. Skipping notification.")
        return
    
    if lowest_drop_pct <= -5.0:
        title = f"🚨 Nifty Crash Alert: {lowest_drop_pct:.2f}%"
        msg = f"{msg_base}\nMarket is dropping! Look for opportunities."
        send_notification(title, msg, priority="high")
        
    elif lowest_drop_pct <= -10.0:
        title = f"💣 MARKET CRASH: {lowest_drop_pct:.2f}%"
        msg = f"{msg_base}\nMarket is crashing! Consider buying the dip."
        send_notification(title, msg, priority="urgent")
        
    elif lowest_drop_pct <= -15.0:
        title = f"🔥 MARKET MELTDOWN: {lowest_drop_pct:.2f}%"
        msg = f"{msg_base}\n Market is melting down! Consider buying the dip."
        send_notification(title, msg, priority="emergency")     
    
    elif lowest_drop_pct <= -20.0:
        title = f"💥 MARKET APOCALYPSE: {lowest_drop_pct:.2f}%"
        msg = f"{msg_base}\nMarket is in freefall! Consider buying the dip."
        send_notification(title, msg, priority="critical")
        
    else:
        print(f"Market is safe (Down {lowest_drop_pct:.2f}%). No alert sent.")

if __name__ == "__main__":
    check_market()