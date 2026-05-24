import streamlit as st

from src.analytics import get_pr_table, get_volume_by_year
from src.data_loader import load_map_config, load_race_history
from src.pace import format_pace
from src.paths import validate_data_dir
from src.plotting import plot_volume_by_year

st.set_page_config(page_title="Race Records", layout="wide")
validate_data_dir()

df_history = load_race_history()
map_cfg = load_map_config()
PALETTE = map_cfg["palette"]

st.title("🏃 Personal Race Records")
st.markdown("---")

if df_history.empty:
    st.warning("No race data found in `data/results/`. Check your directory structure.")
    st.stop()


# -------------------------------------------------------------------------------- #
# 📊 LIFETIME STATS
# -------------------------------------------------------------------------------- #

df_history["_miles"] = df_history.apply(
    lambda r: r["Distance"] * 0.621371 if "km" in str(r["Unit"]).lower() else r["Distance"],
    axis=1,
)
total_miles = df_history["_miles"].sum()
total_races = len(df_history)
total_elevation = int(df_history["Elevation"].fillna(0).sum())
states_explored = df_history["State"].dropna().nunique()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Lifetime Races", total_races)
c2.metric("Total Miles", f"{total_miles:,.0f} mi")
c3.metric("States Explored", states_explored)
c4.metric("Vertical Gain", f"{total_elevation:,} ft")

st.divider()


# -------------------------------------------------------------------------------- #
# 🏁 RECENT RACE  +  🏆 PERSONAL RECORDS
# -------------------------------------------------------------------------------- #

col_recent, col_prs = st.columns([1, 2])

with col_recent:
    st.subheader("🏁 Most Recent Race")
    latest = df_history.sort_values("Date", ascending=False).iloc[0]
    st.markdown(f"### {latest['Name']}")
    location = ", ".join(filter(None, [latest.get("City"), latest.get("State")]))
    st.caption(f"{latest['Date'].strftime('%B %d, %Y')} · {location}")

    m1, m2, m3 = st.columns(3)
    dist_label = (
        f"{int(latest['Distance'])} {latest['Unit']}"
        if latest["Distance"] == int(latest["Distance"])
        else f"{latest['Distance']} {latest['Unit']}"
    )
    m1.metric("Distance", dist_label)
    m2.metric("Time", latest.get("Time") or "—")
    m3.metric("Pace", f"{format_pace(latest['Pace'])} /mi")

with col_prs:
    st.subheader("🏆 Personal Records")
    df_pr = get_pr_table(df_history)
    if not df_pr.empty:
        st.dataframe(df_pr, hide_index=True, use_container_width=True)
    else:
        st.info("No personal records computed yet.")

st.divider()


# -------------------------------------------------------------------------------- #
# 📈 YEAR-OVER-YEAR VOLUME
# -------------------------------------------------------------------------------- #

st.subheader("📈 Year-over-Year Volume")
df_vol = get_volume_by_year(df_history)
plot_volume_by_year(df_vol, PALETTE)
