import streamlit as st
import pandas as pd

st.set_page_config(page_title="Carpet Automation Dashboard", layout="wide")

st.title("📊 Carpet Order & Return Dashboard")

# -----------------------------
# FILE UPLOAD
# -----------------------------

st.subheader("📤 Upload Your Reports")

orders_file = st.file_uploader("Upload Orders File (Amazon/Shopify)", type=["csv"])
returns_file = st.file_uploader("Upload Returns File", type=["csv"])

if orders_file and returns_file:

    # -----------------------------
    # LOAD ORDERS FILE (AUTO DETECT FORMAT)
    # -----------------------------
    try:
        # Try Amazon format (tab-separated)
        orders_df = pd.read_csv(orders_file, sep="\t")
        if len(orders_df.columns) == 1:
            raise Exception("Wrong format")
    except:
        orders_file.seek(0)
        orders_df = pd.read_csv(orders_file)

    # -----------------------------
    # LOAD RETURNS FILE
    # -----------------------------
    try:
        returns_df = pd.read_csv(returns_file)
    except:
        st.error("❌ Error reading returns file")
        st.stop()

    # -----------------------------
    # CLEAN COLUMN NAMES
    # -----------------------------
    orders_df.columns = orders_df.columns.astype(str).str.strip()
    returns_df.columns = returns_df.columns.astype(str).str.strip()

    # -----------------------------
    # FIND ORDER ID COLUMNS (ROBUST)
    # -----------------------------
    def find_order_column(df):
        for col in df.columns:
            col_clean = col.lower().replace("-", "").replace("_", "")
            if "order" in col_clean and "id" in col_clean:
                return col
        return None

    orders_order_col = find_order_column(orders_df)
    returns_order_col = find_order_column(returns_df)

    st.write("📌 Orders Order ID Column:", orders_order_col)
    st.write("📌 Returns Order ID Column:", returns_order_col)

    if not orders_order_col or not returns_order_col:
        st.error("❌ Could not detect Order ID columns. Please check file format.")
        st.stop()

    # -----------------------------
    # MERGE DATA
    # -----------------------------
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
        if "tracking" in str(row).lower():
            return "In Transit"
        elif "return" in str(row).lower():
            return "Return Initiated"
        else:
            return "Pending"

    merged_df["Status"] = merged_df.apply(get_status, axis=1)

    clean_df = merged_df.copy()

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

    # Safe cost calculation
    total_cost = 0
    if "return cost" in [c.lower() for c in clean_df.columns]:
        col = [c for c in clean_df.columns if "return cost" in c.lower()][0]
        total_cost = pd.to_numeric(clean_df[col], errors="coerce").fillna(0).sum()

    # Safe carrier
    carrier_col = None
    for col in clean_df.columns:
        if "carrier" in col.lower():
            carrier_col = col
            break

    if carrier_col and not clean_df[carrier_col].mode().empty:
        top_carrier = clean_df[carrier_col].mode()[0]
    else:
        top_carrier = "N/A"

    # Paid by counts
    seller_count = 0
    customer_count = 0

    for col in clean_df.columns:
        if "paid" in col.lower():
            seller_count = len(clean_df[clean_df[col] == "Seller"])
            customer_count = len(clean_df[clean_df[col] == "Customer"])
            break

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

else:
    st.info("👆 Please upload both Orders and Returns files to proceed.")