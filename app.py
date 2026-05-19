import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px
from reportlab.pdfgen import canvas
import tempfile
import base64

# ---------------------------------
# PAGE CONFIG
# ---------------------------------
st.set_page_config(page_title="Exporter Operations SaaS", layout="wide")

# ---------------------------------
# DATABASE
# ---------------------------------
conn = sqlite3.connect("carpet.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders_status (
    client TEXT,
    order_id TEXT,
    status TEXT,
    delay_reason TEXT,
    updated_at TEXT,
    PRIMARY KEY (client, order_id)
)
""")

conn.commit()

# ---------------------------------
# LOGIN USERS
# ---------------------------------
users = {
    "admin": {"password": "123", "role": "Admin"},
    "prod": {"password": "123", "role": "Production"},
    "ship": {"password": "123", "role": "Shipping"}
}

# ---------------------------------
# SESSION
# ---------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ---------------------------------
# LOGIN PAGE
# ---------------------------------
if not st.session_state.logged_in:

    st.title("🔐 Export Operations Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if username in users and users[username]["password"] == password:

            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = users[username]["role"]

            st.success("Login Successful")
            st.rerun()

        else:
            st.error("Invalid Credentials")

    st.stop()

# ---------------------------------
# MAIN APP
# ---------------------------------
st.title("📊 Export Operations SaaS")

st.write(
    f"Logged in as: "
    f"**{st.session_state.username} "
    f"({st.session_state.role})**"
)

# ---------------------------------
# CLIENT SELECTOR
# ---------------------------------
client_name = st.selectbox(
    "Select Client",
    ["Exporter A", "Exporter B", "Exporter C"]
)

# ---------------------------------
# FILE UPLOAD
# ---------------------------------
orders_file = st.file_uploader(
    "Upload Orders File",
    type=["csv"]
)

returns_file = st.file_uploader(
    "Upload Returns File",
    type=["csv"]
)

# ---------------------------------
# HELPERS
# ---------------------------------
def clean_df(df):

    df.columns = [str(col).strip() for col in df.columns]

    for col in df.columns:
        df[col] = df[col].astype(str)

    return df


def get_status(order_id):

    cursor.execute(
        """
        SELECT status
        FROM orders_status
        WHERE client=? AND order_id=?
        """,
        (client_name, order_id)
    )

    result = cursor.fetchone()

    return result[0] if result else "Order Received"


def update_status(order_id, status, reason=""):

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO orders_status
        (
            client,
            order_id,
            status,
            delay_reason,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?)

        ON CONFLICT(client, order_id)

        DO UPDATE SET
            status=excluded.status,
            delay_reason=excluded.delay_reason,
            updated_at=excluded.updated_at
    """, (
        client_name,
        order_id,
        status,
        reason,
        now
    ))

    conn.commit()


def count_status(status):

    cursor.execute("""
        SELECT COUNT(*)
        FROM orders_status
        WHERE client=? AND status=?
    """, (client_name, status))

    return cursor.fetchone()[0]


def generate_pdf(report_text):

    temp_pdf = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    )

    c = canvas.Canvas(temp_pdf.name)

    lines = report_text.split("\n")

    y = 800

    for line in lines:
        c.drawString(50, y, line)
        y -= 20

    c.save()

    return temp_pdf.name


# ---------------------------------
# MAIN LOGIC
# ---------------------------------
if orders_file and returns_file:

    try:

        orders_df = pd.read_csv(orders_file)
        returns_df = pd.read_csv(returns_file, header=1)

        orders_df = clean_df(orders_df)
        returns_df = clean_df(returns_df)

        orders_col = "order-id"
        returns_col = "Order ID (Hide)"

        merged_df = pd.merge(
            returns_df,
            orders_df,
            left_on=returns_col,
            right_on=orders_col,
            how="left"
        )

        merged_df = clean_df(merged_df)

        role = st.session_state.role

        # =================================
        # ADMIN DASHBOARD
        # =================================
        if role == "Admin":

            st.subheader("👨‍💼 Admin Dashboard")

            total_orders = len(orders_df)

            in_production = count_status("In Production")

            delayed = count_status("Delayed")

            ready_shipping = count_status("Ready for Shipping")

            shipped = count_status("Shipped")

            returned = (
                count_status("Returned") +
                count_status("Cancelled")
            )

            c1, c2, c3, c4, c5, c6 = st.columns(6)

            c1.metric("Orders", total_orders)
            c2.metric("In Production", in_production)
            c3.metric("Delayed", delayed)
            c4.metric("Ready Shipping", ready_shipping)
            c5.metric("Shipped", shipped)
            c6.metric("Returned", returned)

            # -----------------------------
            # MONTHLY ANALYTICS
            # -----------------------------
            cursor.execute("""
                SELECT updated_at, status
                FROM orders_status
                WHERE client=?
            """, (client_name,))

            rows = cursor.fetchall()

            if rows:

                analytics_df = pd.DataFrame(
                    rows,
                    columns=["updated_at", "status"]
                )

                analytics_df["updated_at"] = pd.to_datetime(
                    analytics_df["updated_at"]
                )

                analytics_df["month"] = (
                    analytics_df["updated_at"]
                    .dt.strftime("%Y-%m")
                )

                chart_df = (
                    analytics_df
                    .groupby(["month", "status"])
                    .size()
                    .reset_index(name="count")
                )

                fig = px.bar(
                    chart_df,
                    x="month",
                    y="count",
                    color="status",
                    title="Monthly Operations Analytics"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            # -----------------------------
            # PDF REPORT
            # -----------------------------
            st.subheader("📄 Generate PDF Report")

            report = f"""
EXPORT OPERATIONS REPORT

Client: {client_name}

Total Orders: {total_orders}
In Production: {in_production}
Delayed: {delayed}
Ready for Shipping: {ready_shipping}
Shipped: {shipped}
Returned/Cancelled: {returned}

Generated At:
{datetime.now()}
"""

            pdf_path = generate_pdf(report)

            with open(pdf_path, "rb") as f:

                st.download_button(
                    "⬇️ Download PDF Report",
                    f,
                    file_name="operations_report.pdf"
                )

        # =================================
        # PRODUCTION LOGIN
        # =================================
        elif role == "Production":

            st.subheader("🏭 Production Dashboard")

            prod_df = orders_df.copy()

            st.dataframe(prod_df)

            st.subheader("🔧 Update Production Status")

            for idx, row in prod_df.head(20).iterrows():

                order_id = row.get("order-id", f"row-{idx}")

                current_status = get_status(order_id)

                st.markdown("---")

                st.write(f"### Order: {order_id}")

                st.write(f"Current Status: {current_status}")

                status = st.selectbox(
                    f"Select Status {idx}",
                    [
                        "Order Received",
                        "In Production",
                        "Delayed",
                        "Ready for Shipping"
                    ],
                    key=f"status_{idx}"
                )

                reason = ""

                if status == "Delayed":

                    reason = st.text_input(
                        "Enter Delay Reason",
                        key=f"reason_{idx}"
                    )

                if st.button(f"Update {idx}"):

                    update_status(
                        order_id,
                        status,
                        reason
                    )

                    st.success("Status Updated")

                # -------------------------
                # WHATSAPP BUTTON
                # -------------------------
                whatsapp_number = "919999999999"

                message = (
                    f"Order {order_id} "
                    f"status updated to {status}"
                )

                whatsapp_link = (
                    f"https://wa.me/"
                    f"{whatsapp_number}"
                    f"?text={message}"
                )

                st.markdown(
                    f"[📲 Forward on WhatsApp]({whatsapp_link})"
                )

                # -------------------------
                # EMAIL BUTTON
                # -------------------------
                email_link = (
                    f"mailto:operations@company.com"
                    f"?subject=Order Update"
                    f"&body={message}"
                )

                st.markdown(
                    f"[📧 Forward on Email]({email_link})"
                )

        # =================================
        # SHIPPING LOGIN
        # =================================
        elif role == "Shipping":

            st.subheader("🚚 Shipping Dashboard")

            shipping_df = merged_df.copy()

            st.dataframe(shipping_df)

            st.subheader("📦 Shipping Updates")

            for idx, row in shipping_df.head(20).iterrows():

                order_id = row.get("order-id", f"row-{idx}")

                current_status = get_status(order_id)

                st.markdown("---")

                st.write(f"### Order: {order_id}")

                st.write(f"Current Status: {current_status}")

                ship_status = st.selectbox(
                    f"Shipping Status {idx}",
                    [
                        "Shipped",
                        "Returned",
                        "Cancelled"
                    ],
                    key=f"ship_{idx}"
                )

                if st.button(f"Update Shipping {idx}"):

                    update_status(
                        order_id,
                        ship_status
                    )

                    st.success("Shipping Updated")

                # -------------------------
                # WHATSAPP BUTTON
                # -------------------------
                whatsapp_number = "919999999999"

                message = (
                    f"Order {order_id} "
                    f"updated to {ship_status}"
                )

                whatsapp_link = (
                    f"https://wa.me/"
                    f"{whatsapp_number}"
                    f"?text={message}"
                )

                st.markdown(
                    f"[📲 Notify via WhatsApp]({whatsapp_link})"
                )

        st.success("✅ Export Operations SaaS Running")

    except Exception as e:

        st.error("🚨 Error")
        st.write(e)

else:

    st.info("Upload both files to begin")