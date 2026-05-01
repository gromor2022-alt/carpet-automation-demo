import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Carpet SaaS Dashboard", layout="wide")

# -----------------------------
# DATABASE
# -----------------------------
conn = sqlite3.connect("carpet.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS status_table (
    client TEXT,
    order_id TEXT,
    status TEXT,
    PRIMARY KEY (client, order_id)
)
""")
conn.commit()

# -----------------------------
# LOGIN SYSTEM
# -----------------------------
users = {
    "admin": {"password": "123", "role": "Admin"},
    "prod": {"password": "123", "role": "Production"},
    "ship": {"password": "123", "role": "Shipping"}
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and users[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = users[username]["role"]
            st.success("Login Successful ✅")
            st.rerun()
        else:
            st.error("Invalid Credentials ❌")

    st.stop()

# -----------------------------
# APP START
# -----------------------------
st.title("📊 Carpet Automation SaaS")

st.write(f"Logged in as: **{st.session_state.username} ({st.session_state.role})**")

# -----------------------------
# CLIENT SELECTOR
# -----------------------------
client_name = st.selectbox(
    "Select Client",
    ["Exporter A", "Exporter B", "Exporter C"]
)

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

def get_status(order_id):
    cursor.execute(
        "SELECT status FROM status_table WHERE client=? AND order_id=?",
        (client_name, order_id)
    )
    result = cursor.fetchone()
    return result[0] if result else "Pending"

def update_status(order_id, status):
    cursor.execute("""
        INSERT INTO status_table (client, order_id, status)
        VALUES (?, ?, ?)
        ON CONFLICT(client, order_id)
        DO UPDATE SET status=excluded.status
    """, (client_name, order_id, status))
    conn.commit()

def get_columns(df, keywords):
    return [
        col for col in df.columns
        if any(k in col.lower() for k in keywords)
    ]

# -----------------------------
# MAIN LOGIC
# -----------------------------
if orders_file and returns_file:

    try:
        orders_df = safe_df(load_orders(orders_file))
        returns_df = safe_df(load_returns(returns_file))

        orders_col = "order-id"
        returns_col = "Order ID (Hide)"

        merged_df = pd.merge(
            returns_df,
            orders_df,
            left_on=returns_col,
            right_on=orders_col,
            how="left"
        )

        merged_df = safe_df(merged_df)

        role = st.session_state.role

        # -----------------------------
        # ADMIN
        # -----------------------------
        if role == "Admin":

            st.subheader("👨‍💼 Admin View")

            st.write("### 🆕 Orders")
            st.dataframe(orders_df)

            st.write("### 🔁 Returns")
            st.dataframe(merged_df)

        # -----------------------------
        # PRODUCTION
        # -----------------------------
        elif role == "Production":

            st.subheader("🏭 Production View")

            keys = ["order", "product", "quantity", "ship", "date"]

            st.write("### 🆕 Orders")
            st.dataframe(orders_df[get_columns(orders_df, keys)])

            st.write("### 🔁 Returns")
            st.dataframe(merged_df[get_columns(merged_df, keys)])

        # -----------------------------
        # SHIPPING
        # -----------------------------
        elif role == "Shipping":

            st.subheader("🚚 Shipping View")

            keys = [
                "order", "product", "address", "city",
                "state", "zip", "buyer", "email",
                "phone", "ship"
            ]

            shipping_df = merged_df[get_columns(merged_df, keys)].copy()

            shipping_df["Status"] = shipping_df.apply(
                lambda x: get_status(x.get("order-id", "NA")),
                axis=1
            )

            st.dataframe(shipping_df)

            st.write("### 🔧 Update Status")

            for idx, row in shipping_df.head(20).iterrows():
                order_id = row.get("order-id", f"row-{idx}")

                c1, c2, c3, c4 = st.columns(4)

                with c1:
                    st.write(order_id)

                with c2:
                    if st.button(f"📦 Produced {idx}"):
                        update_status(order_id, "Produced")

                with c3:
                    if st.button(f"🚚 Shipped {idx}"):
                        update_status(order_id, "Shipped")

                with c4:
                    st.write(get_status(order_id))

        # -----------------------------
        # REPORT
        # -----------------------------
        st.subheader("📄 Report")

        total_orders = len(orders_df)
        total_returns = len(merged_df)

        cursor.execute("SELECT COUNT(*) FROM status_table WHERE client=? AND status='Produced'", (client_name,))
        produced = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM status_table WHERE client=? AND status='Shipped'", (client_name,))
        shipped = cursor.fetchone()[0]

        report = f"""
CARPET EXPORT REPORT

Client: {client_name}

Orders: {total_orders}
Returns: {total_returns}

Produced: {produced}
Shipped: {shipped}
Pending: {total_orders - shipped}
"""

        st.text_area("Report Preview", report)

        st.download_button(
            "⬇️ Download Report",
            report,
            file_name="report.txt"
        )

        st.success("✅ SaaS System Running")

    except Exception as e:
        st.error("🚨 Error")
        st.write(e)

else:
    st.info("Upload both files to begin")