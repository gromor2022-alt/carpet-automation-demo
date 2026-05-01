import streamlit as st
import pandas as pd

st.set_page_config(page_title="Carpet Automation Demo", layout="wide")

st.title("📊 Carpet Order & Return Dashboard")

# -----------------------------
# LOAD DATA (FIX HEADER ISSUE)
# -----------------------------

orders_df = pd.read_csv("Copy of Master - MASTER.csv", header=1)
returns_df = pd.read_csv("Copy of Return & Reship - MASTER.csv", header=0)

# Clean column names
orders_df.columns = orders_df.columns.astype(str).str.strip()
returns_df.columns = returns_df.columns.astype(str).str.strip()

# -----------------------------
# MERGE USING COLUMN POSITION
# -----------------------------

orders_order_col = orders_df.columns[2]   # Order ID
returns_order_col = returns_df.columns[0]  # Order ID (Hide)

merged_df = pd.merge(
    returns_df,
    orders_df,
    left_on=returns_order_col,
    right_on=orders_order_col,
    how="left"
)

# -----------------------------
# STATUS LOGIC
# -----------------------------

def get_status(row):
    if pd.notna(row.get("Return Tracking ID (Hide)", None)):
        return "In Transit"
    elif pd.notna(row.get("Return Date", None)):
        return "Return Initiated"
    else:
        return "Pending"

merged_df["Status"] = merged_df.apply(get_status, axis=1)

# -----------------------------
# CLEAN VIEW FOR CLIENT
# -----------------------------

clean_df = merged_df.rename(columns={
    "Unnamed: 0_x": "Order ID",
    "Unnamed: 1_x": "Order Date",
    "RETURN DETAILS": "Return Date",
    "Unnamed: 3_x": "RMA ID",
    "Unnamed: 4_x": "Return Cost",
    "Unnamed: 5_x": "Carrier",
    "Unnamed: 6_x": "Tracking ID",
    "Unnamed: 7_x": "Paid By"
})

# -----------------------------
# DASHBOARD METRICS
# -----------------------------

st.subheader("📊 Daily Summary")

total_returns = len(clean_df)
in_transit = len(clean_df[clean_df["Status"] == "In Transit"])
pending = len(clean_df[clean_df["Status"] == "Pending"])
initiated = len(clean_df[clean_df["Status"] == "Return Initiated"])

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Returns", total_returns)
col2.metric("In Transit", in_transit)
col3.metric("Pending", pending)
col4.metric("Initiated", initiated)

# -----------------------------
# DAILY REPORT
# -----------------------------

st.subheader("📩 Daily Report")

total_cost = pd.to_numeric(clean_df["Return Cost"], errors="coerce").fillna(0).sum()

top_carrier = (
    clean_df["Carrier"].mode()[0]
    if not clean_df["Carrier"].mode().empty
    else "N/A"
)

seller_count = len(clean_df[clean_df["Paid By"] == "Seller"])
customer_count = len(clean_df[clean_df["Paid By"] == "Customer"])

report = f"""
📊 DAILY RETURNS SUMMARY

Total Returns: {total_returns}
In Transit: {in_transit}
Pending: {pending}
Initiated: {initiated}

💰 Total Return Cost: ${total_cost:.2f}

🚚 Top Carrier Used: {top_carrier}

👤 Paid By Breakdown:
Seller: {seller_count}
Customer: {customer_count}
"""

st.text_area("Report Preview", report, height=250)

st.download_button("⬇️ Download Report", report, file_name="daily_report.txt")

# -----------------------------
# FINAL TABLE
# -----------------------------

st.subheader("📊 Clean Dashboard View")
st.dataframe(clean_df)