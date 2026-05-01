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
        # STATUS COLUMN (SESSION BASED)
        # -----------------------------
        if "status_dict" not in st.session_state:
            st.session_state.status_dict = {}

        def get_status(order_id):
            return st.session_state.status_dict.get(order_id, "Pending")

        def update_status(order_id, new_status):
            st.session_state.status_dict[order_id] = new_status

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

            shipping_df = merged_df[get_columns(merged_df, ship_keys)].copy()

            # Add Status Column
            shipping_df["Status"] = shipping_df.apply(
                lambda x: get_status(x.get("order-id", "NA")), axis=1
            )

            st.dataframe(shipping_df)

            st.write("### 🔧 Update Status")

            for idx, row in shipping_df.head(20).iterrows():
                order_id = row.get("order-id", f"row-{idx}")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.write(order_id)

                with col2:
                    if st.button(f"📦 Produced {idx}"):
                        update_status(order_id, "Produced")

                with col3:
                    if st.button(f"🚚 Shipped {idx}"):
                        update_status(order_id, "Shipped")

                with col4:
                    st.write(get_status(order_id))

            # -----------------------------
            # COURIER COMPARISON
            # -----------------------------
            st.subheader("🚛 Courier Comparison")

            base_cost = 100  # dummy base

            shipping_df["FedEx Cost"] = base_cost * 1.1
            shipping_df["DHL Cost"] = base_cost * 1.2

            shipping_df["Best Option"] = shipping_df.apply(
                lambda x: "FedEx" if x["FedEx Cost"] < x["DHL Cost"] else "DHL",
                axis=1
            )

            st.dataframe(shipping_df[["FedEx Cost", "DHL Cost", "Best Option"]])

        # -----------------------------
        # REPORT
        # -----------------------------
        st.subheader("📄 Generate Report")

        total_orders = len(orders_df)
        total_returns = len(merged_df)

        produced = list(st.session_state.status_dict.values()).count("Produced")
        shipped = list(st.session_state.status_dict.values()).count("Shipped")

        report = f"""
CARPET EXPORT DASHBOARD REPORT

Total Orders: {total_orders}
Total Returns: {total_returns}

Produced: {produced}
Shipped: {shipped}
Pending: {total_orders - shipped}

System Generated Report
"""

        st.text_area("Report Preview", report, height=200)

        st.download_button(
            label="⬇️ Download Report",
            data=report,
            file_name="carpet_report.txt"
        )

        st.success("✅ Full System Running")

    except Exception as e:
        st.error("🚨 Error occurred")
        st.write(e)

else:
    st.warning("👆 Upload both files to continue")