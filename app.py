import streamlit as st
from src.data_loader import load_race_history
from src.paths import PROJECT_ROOT

st.set_page_config(page_title="Race Engine", layout="wide")

st.title("🏃 Personal Race Engine")
st.markdown("---")

# Quick dashboard stats on the home page
df_history = load_race_history()

col1, col2, col3 = st.columns(3)
col1.metric("Lifetime Races", len(df_history))
col2.metric("Vertical Gain", f"{int(df_history['Elevation'].sum()):,} ft")
col3.metric("States Explored", df_history['State'].nunique())

st.info("Use the sidebar to navigate between your **Race History** and **Future Planning**.")