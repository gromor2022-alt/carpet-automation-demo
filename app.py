import streamlit as st
import pandas as pd

st.set_page_config(page_title="Carpet Automation Dashboard", layout="wide")

st.title("📊 Carpet Order & Return Dashboard")

# Upload
orders_file = st.file_uploader("Upload Orders File", type=["csv"])
returns_file = st.file_uploader("Upload Returns File", type=["csv"])

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

def fix_header(df):
    for i in range(min(5, len(df))):
        row = df.iloc[i].astype(str).str.lower()
        if row.str.contains("order").any():
            df.columns = df.iloc[i]
            df = df[i+1:]
            break
    return df.reset_index(drop=True)

def find_order_column(df):
    for col in df.columns:
        col_clean = str(col).lower().replace("-", "").replace("_", "")
        if "order" in col_clean and "id" in col_clean:
            return col
    return None

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

# MAIN LOGIC
if orders_file and returns_file:

    orders_df = load_file(orders_file)
    returns_df = load_file(returns_file)

    orders_df = fix_header(orders_df)
    returns_df = fix_header(returns_df)

    orders_df.columns = orders_df.columns.astype(str).str.strip()
    returns_df.columns = returns_df.columns.astype(str).str.strip()

    orders_col = find_order_column(orders_df)
    returns_col = find_order_column(returns_df)

    st.write("Orders Order ID:", orders_col)
    st.write("Returns Order ID:", returns_col)

    if not orders_col or not returns_col:
        st.error("❌ Order ID column not found")
        st.stop()

    merged_df = pd.merge(
        returns_df,
        orders_df,
        left_on=returns_col,
        right_on=orders_col,
        how="left"
    )

    # Fix duplicate columns
    merged_df.columns = make_unique(merged_df.columns)

    clean_df = merged_df.copy()

    # STATUS
    def get_status(row):
        text = str(row).lower()
        if "tracking" in text:
            return "In Transit"
        elif "return" in text:
            return "Return Initiated"
        else:
            return "Pending"

    clean_df["Status"] = clean_df.apply(get_status, axis=1)

    # DASHBOARD
    st.subheader("📊 Daily Summary")

    total = len(clean_df)
    transit = len(clean_df[clean_df["Status"] == "In Transit"])
    pending = len(clean_df[clean_df["Status"] == "Pending"])
    initiated = len(clean_df[clean_df["Status"] == "Return Initiated"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", total)
    c2.metric("Transit", transit)
    c3.metric("Pending", pending)
    c4.metric("Initiated", initiated)

    # REPORT
    st.subheader("📩 Report")

    total_cost = 0
    for col in clean_df.columns:
        if "cost" in col.lower():
            total_cost = pd.to_numeric(clean_df[col], errors="coerce").fillna(0).sum()
            break

    report = f"""
Total: {total}
Transit: {transit}
Pending: {pending}
Initiated: {initiated}
Cost: ${total_cost:.2f}
"""

    st.text_area("Report", report)
    st.download_button("Download Report", report)

    # TABLE
    st.subheader("📊 Data")
    st.dataframe(clean_df)

else:
    st.info("Upload both files to continue")