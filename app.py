import streamlit as st
from src.data_loader import load_race_history
from src.paths import validate_data_dir

st.set_page_config(page_title="Race Records", layout="wide")
validate_data_dir()

df_history = load_race_history()

st.title("🏃 Personal Race Records")
st.markdown("---")

if not df_history.empty:
    total_races = len(df_history)
    total_elevation = int(df_history['Elevation'].fillna(0).sum())
    states_explored = df_history['State'].dropna().nunique()

    col1, col2, col3 = st.columns(3)
    col1.metric("Lifetime Races", total_races)
    col2.metric("Vertical Gain", f"{total_elevation:,} ft")
    col3.metric("States Explored", states_explored)
else:
    st.warning("No race data found in `data/results/`. Check your directory structure.")

st.info("Use the sidebar to navigate between your **Race History** and **Future Planning**.")

if not df_history.empty:
    latest = df_history.sort_values('Date', ascending=False).iloc[0]
    st.write(f"**Last Race:** {latest['Name']} in {latest['State']} ({latest['Date'].date()})")
