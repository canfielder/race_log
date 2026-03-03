import streamlit as st
from src.data_loader import load_race_history
from src.paths import PROJECT_ROOT

st.set_page_config(page_title="Race Engine", layout="wide")

st.title("🏃 Personal Race Engine")
st.markdown("---")

# Load history with a safety check
df_history = load_race_history()

if not df_history.empty:
    # 1. Total Count
    total_races = len(df_history)
    
    # 2. Total Elevation (Handling None/NaN values)
    # Using .get() or fillna(0) to ensure the sum doesn't fail
    total_elevation = int(df_history['Elevation'].fillna(0).sum())
    
    # 3. Unique States (Dropping None)
    states_explored = df_history['State'].dropna().nunique()

    # Layout Dashboard
    col1, col2, col3 = st.columns(3)
    col1.metric("Lifetime Races", total_races)
    col2.metric("Vertical Gain", f"{total_elevation:,} ft")
    col3.metric("States Explored", states_explored)
else:
    st.warning("No race data found in `data/results/`. Check your directory structure.")

st.info("Use the sidebar to navigate between your **Race History** and **Future Planning**.")

# Optional: Show a quick glimpse of the most recent race
if not df_history.empty:
    latest = df_history.sort_values('Date', ascending=False).iloc[0]
    st.write(f"**Last Race:** {latest['Name']} in {latest['State']} ({latest['Date'].date()})")