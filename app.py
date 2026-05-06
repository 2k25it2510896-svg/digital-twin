import streamlit as st
import numpy as np
import pandas as pd
import folium
from streamlit_folium import st_folium
import datetime

# ================= CONFIG =================
st.set_page_config(layout="centered")

# ================= STYLE =================
st.markdown("""
<style>
.stButton>button {
    width: 100%;
    height: 50px;
    font-size: 16px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ================= LOGIN =================
users = {"admin": "1234", "student": "psit"}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔐 Login to Digital Twin")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in users and users[u] == p:
            st.session_state.logged_in = True
            st.success("Login Successful")
        else:
            st.error("Invalid Username or Password")

def logout():
    st.session_state.logged_in = False

# ================= AREAS =================
areas = [
    {"name": "Panki", "lat": 26.50, "lon": 80.25, "type": "industrial"},
    {"name": "Fazalganj", "lat": 26.46, "lon": 80.31, "type": "industrial"},
    {"name": "Jajmau", "lat": 26.43, "lon": 80.39, "type": "industrial"},
    {"name": "Kalyanpur", "lat": 26.51, "lon": 80.25, "type": "residential"},
    {"name": "Kakadeo", "lat": 26.48, "lon": 80.30, "type": "residential"},
    {"name": "Govind Nagar", "lat": 26.45, "lon": 80.35, "type": "mixed"},
    {"name": "Rawatpur", "lat": 26.48, "lon": 80.35, "type": "commercial"},
    {"name": "Chakeri", "lat": 26.42, "lon": 80.40, "type": "mixed"}
]

df = pd.DataFrame(areas)

# ================= INIT =================
def init_data():
    vals = []
    for _, r in df.iterrows():
        if r["type"] == "industrial":
            vals.append(np.random.uniform(60, 80))
        elif r["type"] == "commercial":
            vals.append(np.random.uniform(50, 65))
        elif r["type"] == "mixed":
            vals.append(np.random.uniform(40, 55))
        else:
            vals.append(np.random.uniform(30, 45))
    return np.array(vals)

if "pm25" not in st.session_state:
    st.session_state.pm25 = init_data()
    st.session_state.history = []
    st.session_state.before = None
    st.session_state.after = None

# ================= MAIN =================
def app():

    st.title("🌍 Digital Twin Dashboard")

    choice = st.sidebar.selectbox("📱 Menu", [
        "Home", "Map", "Trend", "Analysis", "Trees", "AI"
    ])

    st.sidebar.header("⚙ Controls")
    traffic = st.sidebar.slider("Traffic", 0.5, 2.0, 1.2)
    industry = st.sidebar.slider("Industry", 0.5, 2.5, 1.5)
    residential = st.sidebar.slider("Residential", 0.5, 2.0, 1.0)
    wind = st.sidebar.slider("Wind", 0.7, 1.3, 1.0)

    run = st.sidebar.button("▶ Run Simulation")
    trees = st.sidebar.button("🌳 Add Trees")
    reset = st.sidebar.button("🔄 Reset")
    st.sidebar.button("Logout", on_click=logout)

    # MODEL
    def update(values):
        new = []
        for i, row in df.iterrows():
            base = values[i]

            if row["type"] == "industrial":
                emission = 20 * industry
            elif row["type"] == "commercial":
                emission = 15 * traffic
            elif row["type"] == "mixed":
                emission = 10 * (traffic + industry)/2
            else:
                emission = 8 * residential

            hour = datetime.datetime.now().hour
            if 7 <= hour <= 10:
                emission *= 1.3
            elif 18 <= hour <= 22:
                emission *= 1.5

            dispersion = 0.85 if wind > 1 else 1.1

            val = (base + emission) * dispersion * 0.96
            val = max(10, min(val, 250))
            new.append(val)

        return np.array(new)

    def apply_trees(values):
        reduction = np.random.uniform(0.1, 0.25)
        return np.clip(values * (1 - reduction), 10, 250)

    # ACTIONS
    if run:
        st.session_state.pm25 = update(st.session_state.pm25)
        st.session_state.history.append(np.mean(st.session_state.pm25))

    if trees:
        st.session_state.before = st.session_state.pm25.copy()
        st.session_state.pm25 = apply_trees(st.session_state.pm25)
        st.session_state.after = st.session_state.pm25.copy()

    if reset:
        st.session_state.pm25 = init_data()
        st.session_state.history = []
        st.session_state.before = None
        st.session_state.after = None

    df["PM2.5"] = st.session_state.pm25
    df["AQI"] = (df["PM2.5"] / 250) * 500

    def color(aqi):
        if aqi < 50: return "green"
        elif aqi < 100: return "yellow"
        elif aqi < 200: return "orange"
        else: return "red"

    # ================= HOME =================
    if choice == "Home":
        st.subheader("🏠 Overview")
        st.metric("Average AQI", int(df["AQI"].mean()))
        st.metric("Worst Area", df.sort_values("AQI", ascending=False).iloc[0]["name"])

    # ================= MAP =================
    elif choice == "Map":
        st.subheader("🗺️ Pollution Map")

        m = folium.Map(location=[26.45, 80.33], zoom_start=11)

        for _, r in df.iterrows():
            folium.CircleMarker(
                location=[r["lat"], r["lon"]],
                radius=8,
                color=color(r["AQI"]),
                fill=True,
                fill_color=color(r["AQI"]),
                popup=f"{r['name']} AQI:{int(r['AQI'])}"
            ).add_to(m)

        st_folium(m, use_container_width=True)

    # ================= TREND =================
    elif choice == "Trend":
        st.subheader("📈 Trend")
        if len(st.session_state.history) > 1:
            st.line_chart(st.session_state.history)
        else:
            st.info("Run simulation")

    # ================= ANALYSIS =================
    elif choice == "Analysis":
        st.subheader("📊 Analysis")
        st.bar_chart(df.set_index("name")["AQI"])

        st.subheader("🚨 Top 3 Worst Areas")
        top3 = df.sort_values("AQI", ascending=False).head(3)
        for i, r in enumerate(top3.itertuples(), 1):
            st.error(f"{i}. {r.name} → AQI {int(r.AQI)}")

    # ================= TREES =================
    elif choice == "Trees":
        st.subheader("🌳 Tree Impact")

        if st.session_state.before is not None:
            tree_df = pd.DataFrame({
                "Before": st.session_state.before,
                "After": st.session_state.after
            })
            st.line_chart(tree_df)

            impact = ((st.session_state.before - st.session_state.after) /
                      st.session_state.before) * 100
            st.metric("Reduction %", round(np.mean(impact), 2))
        else:
            st.info("Apply trees first")

    # ================= AI =================
    elif choice == "AI":
        st.subheader("🤖 AI Suggestions")

        for _, r in df.iterrows():
            if r["AQI"] > 300:
                st.error(f"{r['name']}: Immediate industrial shutdown, vehicle ban")
            elif r["AQI"] > 200:
                st.warning(f"{r['name']}: Reduce emissions, control traffic")
            elif r["AQI"] > 100:
                st.info(f"{r['name']}: Promote public transport, greenery")
            else:
                st.success(f"{r['name']}: Air quality acceptable")

    st.markdown("---")
    st.caption("© 2026 Digital Twin Dashboard")

# ================= RUN =================
if not st.session_state.logged_in:
    login()
else:
    app()
