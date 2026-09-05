import os
import schedule
import time
from finance_hub import send_telegram_alert

def send_morning_paper_trading_reminder():
    reminder_text = (
        "⏰ *PAPER TRADING REMINDER (London Session)*\n"
        "-----------------------------------------\n"
        "1. Open **MetaTrader 5 Demo Account**.\n"
        "2. Review EUR/USD and GBP/USD 4H/1H trends.\n"
        "3. Check daily Forex signals on your Streamlit Hub.\n"
        "4. Log executed paper entries in the Forex & Paper Trading tab."
    )
    send_telegram_alert(reminder_text)

def send_evening_paper_trading_check():
    reminder_text = (
        "📊 *PAPER TRADING REVIEW (New York Session)*\n"
        "-----------------------------------------\n"
        "1. Check running demo positions in MT5.\n"
        "2. Record closed trades and final PnL ($) into Streamlit.\n"
        "3. Log any daily expenses or income transactions."
    )
    send_telegram_alert(reminder_text)

# Times in UTC (e.g., 03:30 UTC = 09:00 AM IST, 12:00 UTC = 05:30 PM IST)
schedule.every().day.at("03:30").do(send_morning_paper_trading_reminder)
schedule.every().day.at("12:00").do(send_evening_paper_trading_check)

print("⏰ Cloud Background Scheduler Started...")
while True:
    schedule.run_pending()
    time.sleep(60)