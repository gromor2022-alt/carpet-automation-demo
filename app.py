import streamlit as st
import pandas as pd

st.set_page_config(page_title="Carpet Dashboard", layout="wide")

st.title("📊 Carpet Automation Dashboard")

# -----------------------------
# ROLE SELECT
# -----------------------------
role = st.selectbox("Select Role", ["Admin", "Production", "Shipping"])

# -----------------------------
# FILE UPLOAD
# -----------------------------
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

def safe_df(df):
    df = df.head(300)  # limit rows to prevent crash
    for col in df.columns:
        df[col] = df[col].astype(str)
    return df

def find_order_column(df):
    for col in df.columns:
        col_clean = str(col).lower().replace("-", "").replace("_", "")
        if "order" in col_clean and "id" in col_clean:
            return col
    return None

# -----------------------------
# MAIN
# -----------------------------
if orders_file and returns_file:

    st.success("Files uploaded ✅")

    try:
        # Load
        orders_df = load_file(orders_file)
        returns_df = load_file(returns_file)

        # Make safe
        orders_df = safe_df(orders_df)
        returns_df = safe_df(returns_df)

        # Detect columns
        orders_col = find_order_column(orders_df)
        returns_col = find_order_column(returns_df)

        st.write("Orders Order ID:", orders_col)
        st.write("Returns Order ID:", returns_col)

        if not orders_col or not returns_col:
            st.error("❌ Order ID column not found")
            st.stop()

        # -----------------------------
        # MERGE
        # -----------------------------
        merged_df = pd.merge(
            returns_df,
            orders_df,
            left_on=returns_col,
            right_on=orders_col,
            how="left"
        )

        merged_df = safe_df(merged_df)

        # -----------------------------
        # ROLE BASED VIEWS
        # -----------------------------

        # 🔒 PRODUCTION VIEW (NO CUSTOMER DATA)
        if role == "Production":

            st.subheader("🏭 Production View")

            prod_cols = []

            for col in merged_df.columns:
                col_lower = col.lower()

                if (
                    "order" in col_lower or
                    "product" in col_lower or
                    "quantity" in col_lower or
                    "ship" in col_lower or
                    "date" in col_lower
                ):
                    prod_cols.append(col)

            production_df = merged_df[prod_cols]

            st.dataframe(production_df)

        # 🚚 SHIPPING VIEW (WITH CUSTOMER DATA)
        elif role == "Shipping":

            st.subheader("🚚 Shipping View")

            ship_cols = []

            for col in merged_df.columns:
                col_lower = col.lower()

                if (
                    "order" in col_lower or
                    "product" in col_lower or
                    "address" in col_lower or
                    "city" in col_lower or
                    "state" in col_lower or
                    "zip" in col_lower or
                    "buyer" in col_lower or
                    "email" in col_lower or
                    "phone" in col_lower or
                    "ship" in col_lower
                ):
                    ship_cols.append(col)

            shipping_df = merged_df[ship_cols]

            st.dataframe(shipping_df)

        # 👨‍💼 ADMIN VIEW (FULL DATA)
        else:

            st.subheader("📊 Admin View (Full Data)")
            st.dataframe(merged_df)

        st.success("✅ App Running Stable")

    except Exception as e:
        st.error("🚨 Error occurred")
        st.write(str(e))

else:
    st.warning("👆 Upload BOTH files to continue")