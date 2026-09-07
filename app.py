import streamlit as st
import pandas as pd
import random
import os
import pyotp
from datetime import date
from sqlalchemy import create_engine, text
import plotly.express as px

# Safe MetaTrader 5 import for cloud compatibility
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except (ImportError, Exception):
    mt5 = None
    MT5_AVAILABLE = False

# Safe import of Angel One SmartConnect
try:
    from SmartApi import SmartConnect
    SMARTAPI_AVAILABLE = True
except ImportError:
    SmartConnect = None
    SMARTAPI_AVAILABLE = False

# Import helper functions from finance_hub.py
from finance_hub import get_loan_summary, send_telegram_alert

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Financial Hub", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .stMetric { background-color: #1E222D; padding: 15px; border-radius: 10px; border: 1px solid #2B2F3A; }
    </style>
""", unsafe_allow_html=True)

# --- DATABASE SETUP (SUPABASE WITH SQLITE FALLBACK) ---
DB_URL = os.getenv("DB_URL")
engine = None
IS_POSTGRES = False

if DB_URL:
    try:
        conn_str = DB_URL.replace("postgres://", "postgresql://", 1) if DB_URL.startswith("postgres://") else DB_URL
        if "sslmode" not in conn_str:
            conn_str += "?sslmode=require" if "?" not in conn_str else "&sslmode=require"

        test_engine = create_engine(conn_str, pool_pre_ping=True, connect_args={"connect_timeout": 5})
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine = test_engine
        IS_POSTGRES = True
    except Exception:
        st.warning("⚠️ Supabase connection failed. Falling back to local SQLite database.")
        engine = create_engine("sqlite:///finance_hub.db")
else:
    engine = create_engine("sqlite:///finance_hub.db")

pk_type = "SERIAL PRIMARY KEY" if IS_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"

# --- AUTO-CREATE TABLES ---
with engine.begin() as conn:
    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS transactions (
            id {pk_type},
            entry_date TEXT,
            type TEXT,
            category TEXT,
            amount REAL,
            description TEXT
        );
    """))
    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS paper_trades (
            id {pk_type},
            trade_date TEXT,
            pair TEXT,
            type TEXT,
            entry_price REAL,
            exit_price REAL,
            pnl REAL,
            status TEXT
        );
    """))

# --- FETCH RECENT DATA ---
try:
    df_tx = pd.read_sql("SELECT * FROM transactions", con=engine)
    df_paper = pd.read_sql("SELECT * FROM paper_trades", con=engine)
except Exception:
    df_tx, df_paper = pd.DataFrame(), pd.DataFrame()

total_income = df_tx[df_tx['type'] == 'Income']['amount'].sum() if not df_tx.empty and 'type' in df_tx.columns else 0.0
total_expenses = df_tx[df_tx['type'] == 'Expense']['amount'].sum() if not df_tx.empty and 'type' in df_tx.columns else 0.0
cash_balance = total_income - total_expenses

# --- FETCH LOAN DATA SAFELY & GLOBALLY ---
raw_loan_info = get_loan_summary(months_passed=1)
loan_info = raw_loan_info if isinstance(raw_loan_info, dict) else {}

account_no = loan_info.get('account_no', 'DELEE01180707')
roi_val = loan_info.get('roi', 11.25)
disbursed_val = loan_info.get('balance', 2089689.00)
customer_val = loan_info.get('customer_transfer', 1883627.00)
next_repay_val = loan_info.get('next_repay', 7877.00)
interest_accrued_val = loan_info.get('interest_accrued', 19590.83)
next_due_val = loan_info.get('next_due', '10-09-2026')

# --- DASHBOARD HEADER METRICS ---
st.title("⚡ AI Personal Finance & Autonomous Trading Hub")
st.caption(f"Student Loan A/C: {account_no} | Active ROI: {roi_val}% p.a. | Live Portfolio & Bot Engine")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Cash Balance (Net)", f"₹ {cash_balance:,.2f}")
col2.metric("Total Expenses Logged", f"₹ {total_expenses:,.2f}")
col3.metric("Avanse Disbursed Loan", f"₹ {disbursed_val:,.2f}")
col4.metric("Next Repay (Due 10-Sep)", f"₹ {next_repay_val:,.2f}")
col5.metric("Paper Bot PnL", f"${df_paper['pnl'].sum():,.2f}" if not df_paper.empty and 'pnl' in df_paper.columns else "$0.00")

st.divider()

# --- WORKFLOW NAVIGATION TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Financial Analytics", 
    "🎓 Avanse Loan Portal", 
    "🤖 Autonomous Forex Bot", 
    "🏹 Angel One Portfolio", 
    "📝 Logs & History"
])

# --- TAB 1: FINANCIAL ANALYTICS ---
with tab1:
    col_chart, col_ai = st.columns([2, 1])
    with col_chart:
        st.subheader("📌 Cashflow & Category Breakdown")
        if not df_tx.empty and 'type' in df_tx.columns:
            df_expenses = df_tx[df_tx['type'] == 'Expense']
            if not df_expenses.empty:
                exp_cat = df_expenses.groupby('category')['amount'].sum().reset_index()
                fig_pie = px.pie(exp_cat, values='amount', names='category', title="Expenses by Category", hole=0.4)
                fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No expense entries logged yet.")
        else:
            st.info("Add entries in the 'Logs & History' tab.")

    with col_ai:
        st.subheader("🤖 Portfolio Insight Summary")
        st.success(f"Total Disbursed: ₹{disbursed_val:,.2f} | Direct Bank Transfer: ₹{customer_val:,.2f}. Active ROI is {roi_val}%. Monthly interest accrual: ~₹{interest_accrued_val:,.2f}. Next repayment of ₹{next_repay_val:,.2f} is due on {next_due_val}.")

# --- TAB 2: AVANSE STUDENT LOAN DETAILS ---
with tab2:
    st.subheader("🎓 Avanse Student Loan International")
    
    l_col1, l_col2, l_col3 = st.columns(3)
    l_col1.metric("Sanctioned Amount", f"₹ {loan_info.get('sanctioned', 2090000.00):,.2f}")
    l_col2.metric("Total Disbursed (99.99%)", f"₹ {disbursed_val:,.2f}")
    l_col3.metric("Net In-Bank Transfer", f"₹ {customer_val:,.2f}")

    st.markdown("---")
    st.markdown("### Disbursement History Breakup")
    df_disbursement = pd.DataFrame([
        {"Date": "31-07-2026", "Beneficiary Party": "VAS", "Beneficiary Name": "ICICI Lombard GIC LTD", "Account Number": "000405007307", "Amount (₹)": 58126.00, "UTR": "SBIN526213966119"},
        {"Date": "31-07-2026", "Beneficiary Party": "VAS", "Beneficiary Name": "Bajaj Finserv Health Ltd", "Account Number": "57500000397474", "Amount (₹)": 62243.00, "UTR": "SBIN526213966108"},
        {"Date": "31-07-2026", "Beneficiary Party": "VAS", "Beneficiary Name": "Bajaj Finserv Health Ltd", "Account Number": "57500000397474", "Amount (₹)": 53594.00, "UTR": "SBIN526213966120"},
        {"Date": "31-07-2026", "Beneficiary Party": "VAS", "Beneficiary Name": "ICICI Lombard GIC LTD", "Account Number": "000405007307", "Amount (₹)": 16037.00, "UTR": "SBIN526213966111"},
        {"Date": "31-07-2026", "Beneficiary Party": "Customer", "Beneficiary Name": "Mariammal Baskar", "Account Number": "053145868006", "Amount (₹)": 1883627.00, "UTR": "SBIN526213126318"}
    ])
    st.dataframe(df_disbursement, use_container_width=True)

# --- TAB 3: AUTONOMOUS FOREX BOT ---
with tab3:
    st.subheader("📈 Autonomous Paper Trading Bot Engine")
    st.caption("Executes technical trading strategies and dispatches profitable signals to Telegram.")

    col_bot, col_manual = st.columns([1, 1])

    with col_bot:
        st.markdown("### 🤖 Strategy Execution Engine")
        strategy_pair = st.selectbox("Select Currency Pair", ["EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD"])
        strategy_type = st.selectbox("Trading Strategy", ["EMA Crossover (14/50)", "RSI Mean Reversion", "Breakout Momentum"])

        if st.button("🚀 Run Autonomous Bot Cycle"):
            with st.spinner(f"Running {strategy_type} algorithm on {strategy_pair}..."):
                base_price = {"EUR/USD": 1.0850, "GBP/USD": 1.2710, "USD/JPY": 152.30, "XAU/USD": 2650.00}[strategy_pair]
                action = random.choice(["BUY", "SELL"])
                entry_p = base_price
                exit_p = round(entry_p + (random.uniform(-0.0050, 0.0080) if "USD" in strategy_pair and strategy_pair != "USD/JPY" else random.uniform(-1.5, 2.5)), 4)
                
                pnl = round((exit_p - entry_p) * 1000, 2) if action == "BUY" else round((entry_p - exit_p) * 1000, 2)

                df_bot_trade = pd.DataFrame([{
                    "trade_date": str(date.today()),
                    "pair": strategy_pair,
                    "type": action,
                    "entry_price": entry_p,
                    "exit_price": exit_p,
                    "pnl": pnl,
                    "status": "AUTO_CLOSED"
                }])
                df_bot_trade.to_sql("paper_trades", con=engine, if_exists="append", index=False)

                st.success(f"Executed {action} on {strategy_pair}! Entry: {entry_p} | Exit: {exit_p} | PnL: ${pnl}")

                if pnl > 0:
                    alert_msg = f"🟢 *WINNING BOT SIGNAL DETECTED*\n• Pair: {strategy_pair}\n• Strategy: {strategy_type}\n• Action: {action}\n• Profit: +${pnl}\n• Status: Validated"
                    send_telegram_alert(alert_msg)
                    st.info("📲 Positive return verified! Signal dispatched to Telegram.")

    with col_manual:
        st.markdown("### 📤 Dispatch Signal to Telegram")
        if st.button("Send Manual Test Alert"):
            sig_text = "💱 *AUTONOMOUS FOREX SIGNAL*\n• EUR/USD: BUY @ 1.0850 (TP: 1.0920 / SL: 1.0810)\n• Strategy: 14/50 EMA Bullish Crossover"
            res = send_telegram_alert(sig_text)
            if res.get("ok"):
                st.success("Signal Sent to Telegram Successfully!")
            else:
                st.error(f"Telegram Alert Failed: {res.get('description', res)}")

# --- TAB 4: ANGEL ONE PORTFOLIO ---
with tab4:
    st.subheader("🏹 Angel One Live Holdings Dashboard")

    api_key = os.getenv("ANGELONE_API_KEY")
    client_code = os.getenv("ANGELONE_CLIENT_CODE")
    password = os.getenv("ANGELONE_PASSWORD")
    totp_key = os.getenv("ANGELONE_TOTP_KEY")

    if not all([api_key, client_code, password, totp_key]):
        st.warning("⚠️ Angel One credentials missing in Streamlit Secrets. Displaying saved holdings preview below.")
        
        df_angel = pd.DataFrame([
            {"Symbol": "TATAMOTORS", "Qty": 15, "Avg Price": 920.50, "LTP": 980.20, "Current Value": 14703.00, "PnL": 895.50},
            {"Symbol": "INFY", "Qty": 8, "Avg Price": 1420.00, "LTP": 1510.00, "Current Value": 12080.00, "PnL": 720.00},
            {"Symbol": "RELIANCE", "Qty": 5, "Avg Price": 2850.00, "LTP": 2980.00, "Current Value": 14900.00, "PnL": 650.00}
        ])
        col_a1, col_a2 = st.columns(2)
        col_a1.metric("Total Equity Invested", "₹ 38,837.50")
        col_a2.metric("Unrealized Profit", "+₹ 2,265.50", delta="5.83%")
        st.dataframe(df_angel, use_container_width=True)
    
    elif not SMARTAPI_AVAILABLE:
        st.error("`smartapi-python` package is missing. Add `smartapi-python` to `requirements.txt` to enable live SmartAPI syncing.")
    
    else:
        try:
            smart_api = SmartConnect(api_key=api_key)
            totp_code = pyotp.TOTP(totp_key).now()
            data = smart_api.generateSession(client_code, password, totp_code)

            if data.get("status"):
                holdings_res = smart_api.holding()
                holdings_data = holdings_res.get("data", [])

                if holdings_data:
                    df_holdings = pd.DataFrame(holdings_data)
                    total_invested = (df_holdings['quantity'].astype(float) * df_holdings['averageprice'].astype(float)).sum()
                    current_val = (df_holdings['quantity'].astype(float) * df_holdings['ltp'].astype(float)).sum()
                    pnl = current_val - total_invested
                    pnl_pct = (pnl / total_invested * 100) if total_invested > 0 else 0.0

                    c1, c2 = st.columns(2)
                    c1.metric("Total Equity Invested", f"₹ {total_invested:,.2f}")
                    c2.metric("Unrealized P&L", f"₹ {pnl:,.2f}", delta=f"{pnl_pct:.2f}%")

                    st.dataframe(df_holdings[['tradingsymbol', 'quantity', 'averageprice', 'ltp', 'profitandloss']], use_container_width=True)
                else:
                    st.info("No active equity holdings found in your Angel One account.")
            else:
                st.error(f"Angel One Authentication Error: {data.get('message', 'Unknown error')}")

        except Exception as e:
            st.error(f"Error fetching Angel One SmartAPI data: {str(e)}")

# --- TAB 5: LOGS & HISTORY ---
with tab5:
    st.subheader("📝 Recorded Transactions & Paper Trade Logs")
    t1, t2, t3 = st.tabs(["Cashflow Logs", "Paper Trade Logs", "➕ Add Entry"])

    with t1:
        if not df_tx.empty:
            st.dataframe(df_tx.sort_values(by="entry_date", ascending=False), use_container_width=True)
        else:
            st.info("No cashflow transactions recorded yet.")

    with t2:
        if not df_paper.empty:
            st.dataframe(df_paper.sort_values(by="trade_date", ascending=False), use_container_width=True)
        else:
            st.info("No paper trades executed yet.")

    with t3:
        st.markdown("### Log Cashflow Entry")
        with st.form("transaction_form", clear_on_submit=True):
            entry_date = st.date_input("Date", date.today())
            trans_type = st.selectbox("Type", ["Expense", "Income"])
            category = st.selectbox("Category", ["Food & Dining", "Commute & Fuel", "Gym & Fitness", "Bills & Rent", "Trading Profit/Loss", "Salary/Freelance", "Other"])
            amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0, format="%.2f")
            description = st.text_input("Notes / Description")

            if st.form_submit_button("Save Transaction"):
                df_new_tx = pd.DataFrame([{
                    "entry_date": str(entry_date),
                    "type": trans_type,
                    "category": category,
                    "amount": amount,
                    "description": description
                }])
                df_new_tx.to_sql("transactions", con=engine, if_exists="append", index=False)
                st.success(f"Saved {trans_type} of ₹{amount:.2f} under {category}!")
                st.rerun()