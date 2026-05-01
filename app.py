import streamlit as st
import pandas as pd

st.set_page_config(page_title="Carpet Dashboard", layout="wide")

st.title("📊 Carpet Automation Dashboard")

# Upload
orders_file = st.file_uploader("Upload Orders File", type=["csv"])
returns_file = st.file_uploader("Upload Returns File", type=["csv"])

# -----------------------------
# HELPERS
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

def find_order_column(df):
    for col in df.columns:
        col_clean = str(col).lower().replace("-", "").replace("_", "")
        if "order" in col_clean and "id" in col_clean:
            return col
    return None

def safe_df(df):
    df = df.head(200)
    for col in df.columns:
        df[col] = df[col].astype(str)
    return df

# -----------------------------
# MAIN
# -----------------------------
if orders_file and returns_file:

    st.success("Files uploaded ✅")

    try:
        orders_df = load_file(orders_file)
        returns_df = load_file(returns_file)

        orders_df = safe_df(orders_df)
        returns_df = safe_df(returns_df)

        st.write("Orders Columns:", list(orders_df.columns))
        st.write("Returns Columns:", list(returns_df.columns))

        # Detect automatically
        orders_col = find_order_column(orders_df)
        returns_col = find_order_column(returns_df)

        # If not found → user selects
        if not returns_col:
            st.warning("⚠️ Could not auto-detect Order ID in Returns file")
            returns_col = st.selectbox("Select Order ID column (Returns)", returns_df.columns)

        if not orders_col:
            st.warning("⚠️ Could not auto-detect Order ID in Orders file")
            orders_col = st.selectbox("Select Order ID column (Orders)", orders_df.columns)

        st.write("Using Orders Column:", orders_col)
        st.write("Using Returns Column:", returns_col)

        # Merge
        merged_df = pd.merge(
            returns_df,
            orders_df,
            left_on=returns_col,
            right_on=orders_col,
            how="left"
        )

        merged_df = safe_df(merged_df)

        st.subheader("📊 Merged Preview")
        st.dataframe(merged_df.head(50))

        st.success("✅ Merge Working")

    except Exception as e:
        st.error("🚨 Error occurred")
        st.write(str(e))

else:
    st.warning("👆 Upload BOTH files to continue")