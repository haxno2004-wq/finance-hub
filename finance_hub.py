import os
import requests

def get_loan_summary(months_passed=1):
    account_no = "DELEE01180707"
    sanctioned_amount = 2090000.00
    disbursed_amount = 2089689.00     # Exact total disbursed value (99.99%)
    customer_transfer = 1883627.00    # Direct bank transfer portion
    annual_roi = 11.25
    monthly_repay = 7877.00
    next_due_date = "10-09-2026"
    
    monthly_rate = (annual_roi / 100) / 12
    interest_accrued = disbursed_amount * monthly_rate * months_passed
    
    return {
        "account_no": account_no,
        "sanctioned": sanctioned_amount,
        "balance": disbursed_amount,
        "customer_transfer": customer_transfer,
        "next_repay": monthly_repay,
        "next_due": next_due_date,
        "roi": annual_roi,
        "interest_accrued": round(interest_accrued, 2)
    }

def send_telegram_alert(message):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    if not token or not chat_id:
        return {"ok": False, "description": "Telegram credentials missing"}
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.json()
    except Exception as e:
        return {"ok": False, "description": str(e)}