import streamlit as st
import requests
import pandas as pd

# -------------------------------
# CONFIG
# -------------------------------
FIREBASE_URL = "https://pocs-project-68633-default-rtdb.asia-southeast1.firebasedatabase.app"
USER_ID = "UID12345"   # Change to test other users if needed

# -------------------------------
# PAGE SETUP
# -------------------------------
st.set_page_config(page_title="🔐 AES vs DES Encryption Dashboard", page_icon="🧠", layout="wide")
st.title("🔐 AES vs DES Encryption & Benchmark Dashboard")

# -------------------------------
# FETCH FIREBASE DATA
# -------------------------------
def get_firebase_data(user_id):
    """Fetch AES/DES and benchmark data from Firebase."""
    try:
        url = f"{FIREBASE_URL}/users/{user_id}.json"
        res = requests.get(url)
        if res.status_code == 200:
            return res.json()
        else:
            st.error(f"⚠️ Firebase returned status code {res.status_code}")
            return None
    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        return None


# -------------------------------
# DISPLAY DATA
# -------------------------------
data = get_firebase_data(USER_ID)

if data:
    st.success(f"✅ Data successfully fetched for user `{USER_ID}`")
    st.markdown("---")

    # ========== BASIC DISPLAY ==========
    st.subheader("🔑 Portfolio Encryption Data")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Plaintext Portfolio**")
        st.code("BTC=0.25, ETH=1.5", language="text")

    with col2:
        st.markdown("**AES Encrypted (from Firebase)**")
        st.code(data.get("portfolio_AES", "N/A"), language="text")

    with col3:
        st.markdown("**DES Encrypted (from Firebase)**")
        st.code(data.get("portfolio_DES", "N/A"), language="text")

    st.markdown("---")

    # ========== BENCHMARK RESULTS ==========
    st.subheader("⏱️ Encryption Time Benchmark (1000 cycles)")
    bench = data.get("benchmark", {})

    aes_time = bench.get("AES_ms", None)
    des_time = bench.get("DES_ms", None)

    if aes_time is not None and des_time is not None:
        c1, c2 = st.columns(2)
        with c1:
            st.metric(label="AES Time (1000 runs)", value=f"{aes_time:.2f} ms")
        with c2:
            st.metric(label="DES Time (1000 runs)", value=f"{des_time:.2f} ms")

        # Bar chart comparison
        st.markdown("### 📊 AES vs DES Performance Comparison")
        df = pd.DataFrame({
            "Algorithm": ["AES", "DES"],
            "Time (ms)": [aes_time, des_time]
        })
        st.bar_chart(df.set_index("Algorithm"))

        # Summary
        st.markdown("---")
        st.subheader("🧠 Summary & Insights")

        faster = "AES" if aes_time < des_time else "DES"
        slower = "DES" if aes_time < des_time else "AES"
        ratio = round(max(aes_time, des_time) / min(aes_time, des_time), 2)

        st.markdown(f"""
        - ✅ **{faster}** performed faster than **{slower}** by roughly **{ratio}×**.
        - AES uses **128-bit keys**, offering much stronger security.
        - DES (56-bit effective key) is **outdated** and vulnerable to brute-force attacks.
        - AES’s efficiency improves with modern CPU hardware and optimized libraries.
        """)

    else:
        st.warning("⚠️ Benchmark data not found in Firebase. Run `crypto_firebase_benchmark.py` first.")

else:
    st.error("❌ Could not load Firebase data. Check your Firebase URL or internet connection.")

# -------------------------------
# FOOTER
# -------------------------------
st.markdown("---")
st.caption("© 2025 PoCS Project | AES vs DES Encryption & Benchmark Visualization")
