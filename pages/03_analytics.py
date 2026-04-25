import streamlit as st

from src.analytics import get_pr_table, get_volume_by_year
from src.data_loader import load_map_config, load_race_history
from src.plotting import plot_pace_over_time, plot_volume_by_year
from src.ui_utils import get_styles

st.set_page_config(page_title="Performance | Race Log", layout="wide")

df = load_race_history()
map_cfg = load_map_config()
PALETTE = map_cfg["palette"]

st.markdown(get_styles(PALETTE), unsafe_allow_html=True)
st.title("📈 Performance Analytics")


# -------------------------------------------------------------------------------- #
# 🎚️ FILTERS
# -------------------------------------------------------------------------------- #

st.sidebar.header("Filters")

unique_years = sorted(df["Year"].unique())
year_range = st.sidebar.select_slider(
    "Year Range",
    options=unique_years,
    value=(min(unique_years), max(unique_years)),
)

type_options = sorted(df["Type"].dropna().unique())
type_filter = st.sidebar.multiselect(
    "Race Type",
    options=type_options,
    default=type_options,
)

mask = df["Year"].between(year_range[0], year_range[1])
if type_filter:
    mask &= df["Type"].isin(type_filter)
df_filtered = df[mask].copy()


# -------------------------------------------------------------------------------- #
# 🏆 PERSONAL RECORDS
# -------------------------------------------------------------------------------- #

st.markdown(
    f"<h2 style='color:{PALETTE['dark_teal']}'>🏆 Personal Records</h2>",
    unsafe_allow_html=True,
)
st.caption(
    "Best time per standard distance, ranked by min/mile pace. "
    "Applies the year range and type filters above."
)

df_pr = get_pr_table(df_filtered)
if df_pr.empty:
    st.info("No races match the selected filters for any standard distance.")
else:
    st.dataframe(df_pr, use_container_width=True, hide_index=True)

st.markdown("---")


# -------------------------------------------------------------------------------- #
# ⚡ PACE OVER TIME
# -------------------------------------------------------------------------------- #

st.markdown(
    f"<h2 style='color:{PALETTE['dark_teal']}'>⚡ Pace Over Time</h2>",
    unsafe_allow_html=True,
)
st.caption("One dot per race. Y-axis inverted — higher = faster.")

pace_metric = st.radio(
    "Metric",
    options=["Pace", "GAP (Grade Adjusted)"],
    horizontal=True,
    label_visibility="collapsed",
)
show_gap = pace_metric == "GAP (Grade Adjusted)"

if df_filtered.empty:
    st.info("No races match the selected filters.")
else:
    plot_pace_over_time(df_filtered, PALETTE, show_gap=show_gap)

st.markdown("---")


# -------------------------------------------------------------------------------- #
# 📅 YEAR OVER YEAR
# -------------------------------------------------------------------------------- #

st.markdown(
    f"<h2 style='color:{PALETTE['dark_teal']}'>📅 Year Over Year</h2>",
    unsafe_allow_html=True,
)
st.caption("Total miles (bars) and race count (line) by year.")

df_volume = get_volume_by_year(df_filtered)
if df_volume.empty:
    st.info("No races match the selected filters.")
else:
    plot_volume_by_year(df_volume, PALETTE)
