import os
import requests

# Fetch tokens securely from Environment Variables, with fallback values for local testing
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8376270764:AAEvoY1EUsJbkZtnbrRvpjVR4UzNx4XX8ps")
CHAT_ID = os.getenv("CHAT_ID", "2051953950")  

def send_telegram_alert(message, months_passed=1):
    """
    Sends a formatted Markdown alert message to your configured Telegram Chat.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

def get_loan_summary(months_passed=1):
    """
    Calculates remaining loan details accounting for the 38-month moratorium period.
    """
    sanctioned_amount = 2000000.00   # ₹20 Lakhs
    disbursed_principal = 1880000.00 # Net disbursed principal after fees
    
    moratorium_months = 38
    moratorium_monthly_payment = 2000.00  # Partial simple interest during moratorium
    post_moratorium_emi = 36007.00        # Full EMI after moratorium
    
    if months_passed <= moratorium_months:
        # During moratorium: Principal balance remains untouched as you pay simple interest
        current_balance = disbursed_principal
        active_monthly_payment = moratorium_monthly_payment
        status = "Moratorium Period (Simple Interest)"
    else:
        # Post-moratorium: Full EMI payments start reducing the principal balance
        post_months = months_passed - moratorium_months
        current_balance = max(0.0, disbursed_principal - (post_moratorium_emi * post_months))
        active_monthly_payment = post_moratorium_emi
        status = "Full Repayment Phase"
    
    return {
        "sanctioned_amount": sanctioned_amount,
        "principal": disbursed_principal,
        "balance": current_balance,
        "emi": active_monthly_payment,
        "status": status
    }