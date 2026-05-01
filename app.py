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
    return pd.read_csv(file, header=1)

def safe_df(df):
    df = df.head(300)
    for col in df.columns:
        df[col] = df[col].astype(str)
    return df

def get_columns(df, keywords):
    return [
        col for col in df.columns
        if any(k in col.lower() for k in keywords)
    ]

# -----------------------------
# MAIN
# -----------------------------
if orders_file and returns_file:

    st.success("Files uploaded ✅")

    try:
        # Load
        orders_df = safe_df(load_orders(orders_file))
        returns_df = safe_df(load_returns(returns_file))

        # Fixed columns
        orders_col = "order-id"
        returns_col = "Order ID (Hide)"

        # Merge returns with orders
        merged_df = pd.merge(
            returns_df,
            orders_df,
            left_on=returns_col,
            right_on=orders_col,
            how="left"
        )

        merged_df = safe_df(merged_df)

        # -----------------------------
        # ADMIN VIEW
        # -----------------------------
        if role == "Admin":

            st.subheader("👨‍💼 Admin View")

            st.write("### 🆕 New Orders")
            st.dataframe(orders_df)

            st.write("### 🔁 Returned Orders")
            st.dataframe(merged_df)

        # -----------------------------
        # PRODUCTION VIEW
        # -----------------------------
        elif role == "Production":

            st.subheader("🏭 Production View")

            prod_keys = ["order", "product", "quantity", "ship", "date"]

            st.write("### 🆕 New Orders")
            st.dataframe(orders_df[get_columns(orders_df, prod_keys)])

            st.write("### 🔁 Returned Orders")
            st.dataframe(merged_df[get_columns(merged_df, prod_keys)])

        # -----------------------------
        # SHIPPING VIEW
        # -----------------------------
        elif role == "Shipping":

            st.subheader("🚚 Shipping View")

            ship_keys = [
                "order", "product", "address", "city",
                "state", "zip", "buyer", "email",
                "phone", "ship"
            ]

            st.write("### 🆕 New Orders")
            st.dataframe(orders_df[get_columns(orders_df, ship_keys)])

            st.write("### 🔁 Returned Orders")
            st.dataframe(merged_df[get_columns(merged_df, ship_keys)])

        # -----------------------------
        # REPORT GENERATION
        # -----------------------------
        st.subheader("📄 Generate Report")

        total_orders = len(orders_df)
        total_returns = len(merged_df)

        report = f"""
CARPET EXPORT DASHBOARD REPORT

Total New Orders: {total_orders}
Total Returns: {total_returns}

Generated from system.
"""

        st.text_area("Report Preview", report, height=200)

        st.download_button(
            label="⬇️ Download Report",
            data=report,
            file_name="carpet_report.txt"
        )

        st.success("✅ System Running Perfectly")

    except Exception as e:
        st.error("🚨 Error occurred")
        st.write(e)

else:
    st.warning("👆 Upload both files to continue")