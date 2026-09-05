import requests

TELEGRAM_TOKEN = "8376270764:AAEvoY1EUsJbkZtnbrRvpjVR4UzNx4XX8ps"
CHAT_ID = "2051953950"

def send_telegram_alert(trade_signal_text: str, loan_data: dict):
    message = (
        "🤖 *AI TRADE BOT & DASHBOARD UPDATE*\n"
        "------------------------------------\n"
        f"{trade_signal_text}\n\n"
        "💳 *Avanse Loan Status*\n"
        f"• Outstanding Balance: ₹{loan_data['balance']:,.2f}\n"
        f"• Phase: {loan_data['phase']}\n"
        f"• Upcoming Due: ₹{loan_data['due']:,.2f} (Due on 10th)\n"
    )
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    
    res = requests.post(url, json=payload)
    return res.json()