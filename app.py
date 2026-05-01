import streamlit as st
import pandas as pd

st.set_page_config(page_title="Carpet Dashboard", layout="wide")

st.title("📊 Carpet Dashboard")

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

def safe_df(df):
    # LIMIT SIZE (CRITICAL)
    df = df.head(200)

    # Convert everything to string (avoid Arrow crash)
    for col in df.columns:
        df[col] = df[col].astype(str)

    return df

if orders_file and returns_file:

    st.success("Files uploaded ✅")

    try:
        orders_df = load_file(orders_file)
        returns_df = load_file(returns_file)

        st.write("Files Loaded")

        # SIMPLE MERGE (no fancy logic yet)
        orders_df = safe_df(orders_df)
        returns_df = safe_df(returns_df)

        st.write("Orders Shape:", orders_df.shape)
        st.write("Returns Shape:", returns_df.shape)

        # Show only small preview
        st.subheader("Orders Preview")
        st.dataframe(orders_df.head(50))

        st.subheader("Returns Preview")
        st.dataframe(returns_df.head(50))

        # FAKE MERGE JUST TO TEST STABILITY
        merged_df = pd.concat([returns_df, orders_df], axis=1)

        merged_df = safe_df(merged_df)

        st.subheader("Merged Preview")
        st.dataframe(merged_df.head(50))

        st.success("✅ App Stable (No Crash)")

    except Exception as e:
        st.error("🚨 Error")
        st.write(e)

else:
    st.warning("Upload both files")