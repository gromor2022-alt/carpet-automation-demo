import streamlit as st
import pandas as pd

st.set_page_config(page_title="Carpet Dashboard", layout="wide")

st.title("📊 Carpet Automation Dashboard")

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

if orders_file and returns_file:

    st.success("Files uploaded ✅")

    try:
        # STEP 1: Load
        orders_df = load_file(orders_file)
        returns_df = load_file(returns_file)

        st.write("Step 1: Files Loaded")

        # STEP 2: Fix headers
        orders_df = fix_header(orders_df)
        returns_df = fix_header(returns_df)

        st.write("Step 2: Headers Fixed")

        # STEP 3: Clean columns
        orders_df.columns = orders_df.columns.astype(str).str.strip()
        returns_df.columns = returns_df.columns.astype(str).str.strip()

        # STEP 4: Detect order column
        orders_col = find_order_column(orders_df)
        returns_col = find_order_column(returns_df)

        st.write("Orders Order ID:", orders_col)
        st.write("Returns Order ID:", returns_col)

        if not orders_col or not returns_col:
            st.error("❌ Order ID column not found")
            st.stop()

        # STEP 5: Merge
        merged_df = pd.merge(
            returns_df,
            orders_df,
            left_on=returns_col,
            right_on=orders_col,
            how="left"
        )

        merged_df.columns = make_unique(merged_df.columns)

        st.write("Step 3: Merge Done")

        # LIMIT DATA (IMPORTANT)
        clean_df = merged_df.head(500)

        # STEP 6: Status (LIGHT VERSION)
        clean_df["Status"] = "Pending"

        st.write("Step 4: Status Added")

        # DASHBOARD
        st.subheader("📊 Summary")

        total = len(clean_df)
        transit = 0
        pending = total
        initiated = 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", total)
        c2.metric("Transit", transit)
        c3.metric("Pending", pending)
        c4.metric("Initiated", initiated)

        # REPORT
        total_cost = 0
        for col in clean_df.columns:
            if "cost" in col.lower():
                total_cost = pd.to_numeric(clean_df[col], errors="coerce").fillna(0).sum()
                break

        st.subheader("📩 Report")

        report = f"""
Total: {total}
Cost: ${total_cost:.2f}
"""

        st.text_area("Report", report)

        # TABLE
        st.subheader("📊 Data Preview (Limited)")
        st.dataframe(clean_df)

    except Exception as e:
        st.error("🚨 Error detected")
        st.write(str(e))

else:
    st.warning("👆 Upload BOTH files")