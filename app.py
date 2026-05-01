import streamlit as st
import pandas as pd

st.set_page_config(page_title="Carpet Dashboard", layout="wide")

st.title("📊 Carpet Automation Dashboard")

# -----------------------------
# ROLE
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
def load_orders(file):
    return pd.read_csv(file)

def load_returns(file):
    # Fix header issue
    return pd.read_csv(file, header=1)

def safe_df(df):
    df = df.head(300)
    for col in df.columns:
        df[col] = df[col].astype(str)
    return df

# -----------------------------
# MAIN
# -----------------------------
if orders_file and returns_file:

    st.success("Files uploaded ✅")

    try:
        # Load data
        orders_df = load_orders(orders_file)
        returns_df = load_returns(returns_file)

        orders_df = safe_df(orders_df)
        returns_df = safe_df(returns_df)

        # Fixed columns (based on your file)
        orders_col = "order-id"
        returns_col = "Order ID (Hide)"

        # Merge
        merged_df = pd.merge(
            returns_df,
            orders_df,
            left_on=returns_col,
            right_on=orders_col,
            how="left"
        )

        merged_df = safe_df(merged_df)

        # -----------------------------
        # PRODUCTION VIEW
        # -----------------------------
        if role == "Production":

            st.subheader("🏭 Production View")

            # NEW ORDERS
            st.write("### 🆕 New Orders")

            orders_cols = [
                col for col in orders_df.columns
                if any(x in col.lower() for x in ["order", "product", "quantity", "ship", "date"])
            ]

            st.dataframe(orders_df[orders_cols])

            # RETURNS
            st.write("### 🔁 Returned Orders")

            returns_cols = [
                col for col in merged_df.columns
                if any(x in col.lower() for x in ["order", "product", "quantity", "ship", "date"])
            ]

            st.dataframe(merged_df[returns_cols])

        # -----------------------------
        # SHIPPING VIEW
        # -----------------------------
        elif role == "Shipping":

            st.subheader("🚚 Shipping View")

            ship_cols = [
                col for col in merged_df.columns
                if any(x in col.lower() for x in [
                    "order", "product", "address", "city", "state",
                    "zip", "buyer", "email", "phone", "ship"
                ])
            ]

            st.dataframe(merged_df[ship_cols])

        # -----------------------------
        # ADMIN VIEW
        # -----------------------------
        else:

            st.subheader("📊 Admin View")
            st.dataframe(merged_df)

        st.success("✅ System Running Perfectly")

    except Exception as e:
        st.error("🚨 Error occurred")
        st.write(e)

else:
    st.warning("👆 Upload both files to continue")