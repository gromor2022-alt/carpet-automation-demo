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

# -----------------------------
# LOAD FILE (AUTO DETECT FORMAT)
# -----------------------------
def load_file(file):
    for sep in ["\t", ","]:
        try:
            file.seek(0)
            df = pd.read_csv(file, sep=sep)
            if len(df.columns) > 1:
                return df
        except:
            continue
    file.seek(0)
    return pd.read_csv(file)

# -----------------------------
# FIX HEADER (AUTO DETECT)
# -----------------------------
def fix_header(df):
    for i in range(min(5, len(df))):
        row = df.iloc[i].astype(str).str.lower()
        if row.str.contains("order").any():
            df.columns = df.iloc[i]
            df = df[i+1:]
            break
    return df.reset_index(drop=True)

# -----------------------------
# FIND ORDER COLUMN
# -----------------------------
def find_order_column(df):
    for col in df.columns:
        col_clean = str(col).lower().replace("-", "").replace("_", "")
        if "order" in col_clean and "id" in col_clean:
            return col
    return None

if orders_file and returns_file:

    # Load files
    orders_df = load_file(orders_file)
    returns_df = load_file(returns_file)

    # Fix headers
    orders_df = fix_header(orders_df)
    returns_df = fix_header(returns_df)

    # Clean column names
    orders_df.columns = orders_df.columns.astype(str).str.strip()
    returns_df.columns = returns_df.columns.astype(str).str.strip()

    # Detect order columns
    orders_order_col = find_order_column(orders_df)
    returns_order_col = find_order_column(returns_df)

    st.write("📌 Orders Order ID Column:", orders_order_col)
    st.write("📌 Returns Order ID Column:", returns_order_col)

    if not orders_order_col or not returns_order_col:
        st.error("❌ Could not detect Order ID columns. Please check file format.")
        st.stop()

    # -----------------------------
    # MERGE
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
        row_str = str(row).lower()
        if "tracking" in row_str:
            return "In Transit"
        elif "return" in row_str:
            return "Return Initiated"
        else:
            return "Pending"

    merged_df["Status"] = merged_df.apply(get_status, axis=1)

    clean_df = merged_df.copy()

# Safe duplicate column fix
def make_unique(cols):
    seen = {}
    new_cols = []
    for col in cols:
        if col in seen:
            seen[col] += 1
            new_cols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_cols.append(col)
    return new_cols

clean_df.columns = make_unique(clean_df.columns)

    # -----------------------------
    # DASHBOARD
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
    # REPORT
    # -----------------------------
    st.subheader("📩 Daily Report")

    total_cost = 0
    for col in clean_df.columns:
        if "cost" in col.lower():
            total_cost = pd.to_numeric(clean_df[col], errors="coerce").fillna(0).sum()
            break

    top_carrier = "N/A"
    for col in clean_df.columns:
        if "carrier" in col.lower():
            if not clean_df[col].mode().empty:
                top_carrier = clean_df[col].mode()[0]
            break

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
    # TABLE
    # -----------------------------
    st.subheader("📊 Data View")
    st.dataframe(clean_df)

else:
    st.info("👆 Please upload both Orders and Returns files to proceed.")