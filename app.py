import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
import os
from datetime import date

# --- SAFE METATRADER 5 IMPORT FOR CLOUD COMPATIBILITY ---
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except (ImportError, Exception):
    mt5 = None
    MT5_AVAILABLE = False

# Import helpers from finance_hub.py
from finance_hub import get_loan_summary, send_telegram_alert

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Financial Hub", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .stMetric { background-color: #1E222D; padding: 15px; border-radius: 10px; border: 1px solid #2B2F3A; }
    </style>
""", unsafe_allow_html=True)

# --- DATABASE SETUP ---
conn = sqlite3.connect("finance_hub.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_date TEXT,
        type TEXT,
        category TEXT,
        amount REAL,
        description TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS paper_trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_date TEXT,
        pair TEXT,
        type TEXT,
        entry_price REAL,
        exit_price REAL,
        pnl REAL,
        status TEXT
    )
""")
conn.commit()

# --- AI SETUP ---
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

if NVIDIA_API_KEY:
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=NVIDIA_API_KEY)
else:
    client = None

# --- REAL-TIME TRADING PnL FETCHERS ---
def get_forex_pnl():
    if not MT5_AVAILABLE:
        return 0.0
    try:
        if not mt5.initialize():
            return 0.0
        positions = mt5.positions_get()
        mt5.shutdown()
        return sum(pos.profit for pos in positions) if positions else 0.0
    except Exception:
        return 0.0

# Fetch local DB cash balances & live PnL
df_tx = pd.read_sql_query("SELECT * FROM transactions", conn)
df_paper = pd.read_sql_query("SELECT * FROM paper_trades", conn)

total_income = df_tx[df_tx['type'] == 'Income']['amount'].sum() if not df_tx.empty else 0.0
total_expenses = df_tx[df_tx['type'] == 'Expense']['amount'].sum() if not df_tx.empty else 0.0
cash_balance = total_income - total_expenses

forex_pnl_usd = get_forex_pnl()
loan_info = get_loan_summary(months_passed=1)

# --- DASHBOARD HEADER ---
st.title("⚡ AI Personal Finance & Forex Hub")
st.caption("Enterprise Portfolio Dashboard & Personal Wealth Tracker")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Cash Balance (Net)", f"₹ {cash_balance:,.2f}")
col2.metric("Total Expenses Logged", f"₹ {total_expenses:,.2f}")
col3.metric("Live MT5 PnL", f"${forex_pnl_usd:,.2f}")
col4.metric("Paper PnL (3-Wk)", f"${df_paper['pnl'].sum():,.2f}" if not df_paper.empty else "$0.00")
col5.metric("Avanse Loan Balance", f"₹ {loan_info['balance']:,.2f}")

if not MT5_AVAILABLE:
    st.info("ℹ️ Note: Live MT5 integration is disabled in cloud hosting (requires local Windows execution environment).")

st.divider()

# --- TABS FOR WORKFLOW ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Financial Analytics", 
    "💱 Forex & Paper Trading", 
    "➕ Add Entry", 
    "📝 History & Logs"
])

# --- TAB 1: FINANCIAL ANALYTICS & AI ADVISOR ---
with tab1:
    col_chart, col_ai = st.columns([2, 1])

    with col_chart:
        st.subheader("📌 Monthly Expense & Income Breakdown")
        if not df_tx.empty:
            df_expenses = df_tx[df_tx['type'] == 'Expense']
            if not df_expenses.empty:
                exp_cat = df_expenses.groupby('category')['amount'].sum().reset_index()
                fig_pie = px.pie(exp_cat, values='amount', names='category', title="Expenses by Category", hole=0.4)
                fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No expense entries logged yet.")
        else:
            st.info("Add transactions in the 'Add Entry' tab to render monthly charts.")

    with col_ai:
        st.subheader("🤖 Dynamic AI Advisor")
        if st.button("Generate Portfolio Insights"):
            if not client:
                st.error("NVIDIA_API_KEY is not configured in Streamlit Secrets.")
            else:
                with st.spinner("Analyzing financial logs..."):
                    try:
                        summary_prompt = f"Net Cash Balance: INR {cash_balance}, Total Expenses: INR {total_expenses}, Active MT5 PnL: ${forex_pnl_usd}. Loan Balance: INR {loan_info['balance']}."
                        response = client.chat.completions.create(
                            model="nvidia/llama-3.3-nemotron-super-49b-v1",
                            messages=[
                                {"role": "system", "content": "You are a corporate financial advisor. Give brief budget insights."},
                                {"role": "user", "content": summary_prompt}
                            ],
                            temperature=0.3
                        )
                        st.success("Advisor Response:")
                        st.write(response.choices[0].message.content)
                    except Exception as e:
                        st.error(f"NVIDIA API Error: {e}")

# --- TAB 2: FOREX & PAPER TRADING ---
with tab2:
    st.subheader("📈 3-Week Paper Trading Engine & Daily Signals")
    
    col_sig, col_log = st.columns([1, 1])
    
    with col_sig:
        st.markdown("### Daily Forex Signals")
        st.info("🎯 **EUR/USD Buy Signal** | Entry: 1.0850 | TP: 1.0920 | SL: 1.0810")
        st.info("🎯 **GBP/USD Sell Signal** | Entry: 1.2710 | TP: 1.2640 | SL: 1.2750")
        
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col1:
            if st.button("📤 Send Signals to Telegram"):
                sig_text = "💱 *FOREX SIGNALS*\n• EUR/USD: BUY @ 1.0850 (TP: 1.0920 / SL: 1.0810)\n• GBP/USD: SELL @ 1.2710 (TP: 1.2640 / SL: 1.2750)"
                res = send_telegram_alert(sig_text)
                if res.get("ok"):
                    st.success("Sent!")
                else:
                    st.error(f"Telegram Error: {res.get('description', res)}")
                
        with btn_col2:
            if st.button("⏰ Send Trading Reminder"):
                rem_text = (
                    "🔔 *INSTANT PAPER TRADING REMINDER*\n"
                    "• Open MT5 Demo Account\n"
                    "• Place paper orders for EUR/USD & GBP/USD\n"
                    "• Record results in Streamlit"
                )
                res = send_telegram_alert(rem_text)
                if res.get("ok"):
                    st.success("Reminder Sent!")
                else:
                    st.error(f"Telegram Error: {res.get('description', res)}")

    with col_log:
        st.markdown("### Log Paper Trade")
        with st.form("paper_trade_form", clear_on_submit=True):
            p_date = st.date_input("Trade Date", date.today())
            p_pair = st.selectbox("Pair", ["EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD"])
            p_type = st.selectbox("Type", ["BUY", "SELL"])
            p_entry = st.number_input("Entry Price", format="%.4f")
            p_exit = st.number_input("Exit Price", format="%.4f")
            p_pnl = st.number_input("PnL ($ USD)", format="%.2f")
            
            if st.form_submit_button("Record Paper Trade"):
                cursor.execute(
                    "INSERT INTO paper_trades (trade_date, pair, type, entry_price, exit_price, pnl, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (str(p_date), p_pair, p_type, p_entry, p_exit, p_pnl, "CLOSED")
                )
                conn.commit()
                st.success("Paper Trade Logged!")
                st.rerun()

# --- TAB 3: ADD TRANSACTIONS ---
with tab3:
    st.subheader("➕ Log Cashflow Entry")
    with st.form("transaction_form", clear_on_submit=True):
        entry_date = st.date_input("Date", date.today())
        trans_type = st.selectbox("Type", ["Expense", "Income"])
        category = st.selectbox("Category", ["Food & Dining", "Commute & Fuel", "Gym & Fitness", "Bills & Rent", "Trading Profit/Loss", "Salary/Freelance", "Other"])
        amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0, format="%.2f")
        description = st.text_input("Notes / Description")
        
        submitted = st.form_submit_button("Save Transaction")
        if submitted:
            cursor.execute(
                "INSERT INTO transactions (entry_date, type, category, amount, description) VALUES (?, ?, ?, ?, ?)",
                (str(entry_date), trans_type, category, amount, description)
            )
            conn.commit()
            st.success(f"Saved {trans_type} of ₹{amount:.2f} under {category}!")
            st.rerun()

# --- TAB 4: HISTORY & LOGS ---
with tab4:
    st.subheader("📝 Recorded Transactions & Paper Trade Logs")
    t1, t2 = st.tabs(["Cashflow Logs", "Paper Trade Logs"])
    with t1:
        st.dataframe(df_tx.sort_values(by="entry_date", ascending=False), use_container_width=True) if not df_tx.empty else st.write("No transactions recorded yet.")
    with t2:
        st.dataframe(df_paper.sort_values(by="trade_date", ascending=False), use_container_width=True) if not df_paper.empty else st.write("No paper trades recorded yet.")