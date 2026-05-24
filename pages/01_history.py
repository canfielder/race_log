import os
import pathlib

import folium
import pandas as pd
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

from src.data_loader import (
    get_all_relay_legs,
    get_filtered_data,
    get_track_data,
    load_map_config,
    load_race_history,
)
from src.pace import calculate_climb_density, format_pace
from src.plotting import (
    add_relay_tracks_to_map,
    add_route_to_map,
    apply_map_styles,
    apply_state_highlights,
    get_popup,
    plot_elevation_profile,
)
from src.ui_utils import get_styles

st.set_page_config(page_title="Race History | Race Log", layout="wide")


# -------------------------------------------------------------------------------- #
# 📊 STATS COLUMN HELPERS
# Each function renders one of the three states of the right-hand stats panel.
# -------------------------------------------------------------------------------- #

def _render_full_race_view(res: pd.Series, is_relay: bool, palette: dict) -> None:
    """Render stats and external links for a fully selected race."""
    st.markdown(f"<h3 style='color:{palette['dark_teal']}'>Quick Stats</h3>", unsafe_allow_html=True)
    r_type = str(res.get("Type", "Trail")).lower()
    st.markdown(f"**{'⛰️' if 'trail' in r_type else '👟'} {res['Type']} Race**")

    dist = res["Distance"]
    unit_label = "k" if "k" in str(res["Unit"]).lower() else "miles"
    dist_label = f"{int(dist) if dist == int(dist) else dist} {unit_label}"
    st.metric("📍 Distance", dist_label)
    st.metric("⏱️ Total Time", value=res.get("Time", "--:--:--"))

    if not is_relay and res.get("Elevation", 0) > 0:
        st.metric("🔼 Vertical Gain", f"{int(res['Elevation']):,} ft")
        st.metric("📐 Avg. Climb", f"{calculate_climb_density(res['Elevation'], res['Distance'])} ft/mi")
    else:
        st.caption("🏔️ *Elevation stats not tracked for relays*")

    st.metric("⚡ Pace", f"{format_pace(res['Pace'])} min/mi")

    if "GAP" in res and pd.notna(res["GAP"]):
        st.metric("📈 GAP (Grade Adj)", f"{format_pace(res['GAP'])} /mi")

    st.markdown("---")
    st.markdown("**🔗 Race Records**")

    if res.get("athlinks_url"):
        st.link_button("🏆 Athlinks Results", res["athlinks_url"], use_container_width=True, type="primary")

    strava_data = res.get("strava_url")
    if strava_data:
        if isinstance(strava_data, list):
            for entry in strava_data:
                if isinstance(entry, dict):
                    label = entry.get("label", "Strava Activity")
                    icon = "🏃" if "Leg" in label else "🧡"
                    url = entry.get("url")
                    if url:
                        st.link_button(f"{icon} {label}", url, use_container_width=True)
                elif isinstance(entry, str):
                    st.link_button("🧡 Strava Activity", entry, use_container_width=True)
        elif isinstance(strava_data, str):
            st.link_button("🧡 Strava Activity", strava_data, use_container_width=True)

    if res.get("original_url"):
        st.link_button("🌐 Official Records", res["original_url"], use_container_width=True)


def _render_race_preview(
    preview_key: str,
    preview_row: pd.Series,
    race_display_map: dict,
    palette: dict,
) -> None:
    """Render a quick-look card when a map marker has been clicked."""
    r_type = str(preview_row.get("Type", "Trail")).lower()
    st.markdown(
        f"<h3 style='color:{palette['dark_teal']}'>{'⛰️' if 'trail' in r_type else '👟'} {preview_row['Name']}</h3>",
        unsafe_allow_html=True,
    )
    location = ", ".join(filter(None, [preview_row.get("City"), preview_row.get("State")]))
    st.caption(f"{preview_row['Date'].strftime('%B %d, %Y')} · {location}")

    if st.button("🗺️ Load GPS Track", type="primary", use_container_width=True):
        st.session_state._race_navigation = preview_key
        st.session_state.previewed_race = None
        st.rerun()
    if st.button("Clear", use_container_width=True):
        st.session_state.previewed_race = None
        st.rerun()

    st.markdown("---")
    dist = preview_row["Distance"]
    unit_label = "k" if "k" in str(preview_row["Unit"]).lower() else "miles"
    st.metric("📍 Distance", f"{int(dist) if dist == int(dist) else dist} {unit_label}")
    st.metric("⏱️ Total Time", value=preview_row.get("Time", "--:--:--"))
    if preview_row.get("Elevation", 0) > 0:
        st.metric("🔼 Vertical Gain", f"{int(preview_row['Elevation']):,} ft")
    st.metric("⚡ Pace", f"{format_pace(preview_row['Pace'])} min/mi")


def _render_overview_metrics(df_filtered: pd.DataFrame) -> None:
    """Render aggregate stats for the current filter view."""
    st.metric("🏁 Races Shown", f"{len(df_filtered):,}")
    st.metric("📍 Total Distance", f"{df_filtered['Distance'].sum():,.0f} mi")
    st.metric("⛰️ Total Gain", f"{int(df_filtered['Elevation'].sum()):,} ft")


# -------------------------------------------------------------------------------- #
# 🗃️ CONFIG & DATA
# -------------------------------------------------------------------------------- #

df = load_race_history(verbose=False)
map_cfg = load_map_config()
PALETTE = map_cfg["palette"]
tf_api_key = os.getenv("THUNDERFOREST_API_KEY", None)

st.markdown(get_styles(PALETTE), unsafe_allow_html=True)
st.title("🏃 Race History & Performance")


# -------------------------------------------------------------------------------- #
# 🧠 SESSION STATE
# -------------------------------------------------------------------------------- #

# previewed_race: race key set by a map marker click; shows the preview panel
# _race_navigation: source of truth for the selectbox; written freely unlike widget-bound keys
if "previewed_race" not in st.session_state:
    st.session_state.previewed_race = None
if "_race_navigation" not in st.session_state:
    st.session_state._race_navigation = "None"
if "map_center" not in st.session_state:
    st.session_state.map_center = None
if "map_zoom" not in st.session_state:
    st.session_state.map_zoom = None


# -------------------------------------------------------------------------------- #
# 🎚️ FILTERS
# -------------------------------------------------------------------------------- #

with st.container():
    st.markdown(f"<h3 style='color:{PALETTE['dark_teal']}; margin-bottom: 0;'>Race Timeline</h3>", unsafe_allow_html=True)
    unique_years = sorted(df["Year"].unique())
    year_range = st.select_slider("Filter by Year", options=unique_years, value=(min(unique_years), max(unique_years)))

st.sidebar.header("Filters")
state_filter = st.sidebar.multiselect("Filter by State", options=sorted(df["State"].dropna().unique()))
type_filter = st.sidebar.multiselect(
    "Race Type",
    options=sorted(df["Type"].dropna().unique()),
    default=sorted(df["Type"].dropna().unique()),
)

df_filtered = get_filtered_data(df, state_filter, type_filter, year_range)
df_map_sorted = df_filtered.sort_values(by=["Date", "Name"], ascending=False)

st.sidebar.markdown("---")
st.sidebar.header("Map Settings")
race_display_map = {f"{row['Name']} ({row['Year']})": row["folder_path"] for _, row in df_map_sorted.iterrows()}

# Compute the selectbox index from _race_navigation so the dropdown stays in sync
# with programmatic navigation (map clicks, Load GPS Track button) without using
# a widget-bound key, which Streamlit forbids writing to after render.
_race_options = ["None"] + sorted(race_display_map.keys())
_nav_target = st.session_state._race_navigation
_nav_index = _race_options.index(_nav_target) if _nav_target in _race_options else 0
selected_display = st.sidebar.selectbox("Select a race for GPS view", _race_options, index=_nav_index)
st.session_state._race_navigation = selected_display

# If the user explicitly returned to "None" via the dropdown, clear any pending preview
_prev_selected = st.session_state.get("_prev_selected_display", "None")
if selected_display == "None" and _prev_selected != "None":
    st.session_state.previewed_race = None
st.session_state._prev_selected_display = selected_display

# Clear preview if the race was filtered out of the current view
if st.session_state.previewed_race and st.session_state.previewed_race not in race_display_map:
    st.session_state.previewed_race = None

show_state_highlights = st.sidebar.checkbox("Highlight Completed States", value=(selected_display == "None"))


# -------------------------------------------------------------------------------- #
# 🗺️ INTERACTIVE MAP TAB
# -------------------------------------------------------------------------------- #

tab_map, tab_details = st.tabs(["🗺️ Interactive Map", "📊 Detailed Results"])

with tab_map:
    header_text = f"📍 {selected_display}" if selected_display != "None" else "📍 Course Explorer"
    st.markdown(f"<h2 style='color:{PALETTE['dark_teal']}; margin-bottom: 20px;'>{header_text}</h2>", unsafe_allow_html=True)

    # Resolve the selected race row and detect relays (multiple .gpx files = relay)
    res = None
    is_relay = False
    if selected_display != "None":
        target_path = race_display_map[selected_display]
        res = df_filtered[df_filtered["folder_path"] == target_path].iloc[0]
        gpx_files = list(pathlib.Path(target_path).glob("*.gpx"))
        is_relay = len(gpx_files) > 1

    col_map, col_stats = st.columns([3, 1])

    with col_map:
        tile_url = (
            f"https://tile.thunderforest.com/outdoors/{{z}}/{{x}}/{{y}}.png?apikey={tf_api_key}"
            if tf_api_key
            else "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
        )
        map_attr = "&copy; Thunderforest" if tf_api_key else "Map data: &copy; OpenStreetMap"

        m = folium.Map(
            location=map_cfg["map_defaults"]["location"],
            zoom_start=map_cfg["map_defaults"]["zoom"],
            tiles=tile_url if selected_display != "None" else "CartoDB Voyager",
            attr=map_attr,
        )

        if show_state_highlights:
            completed_states = df_filtered["State"].unique()
            apply_state_highlights(m, geo_url=map_cfg["states_geo_url"], palette=PALETTE, completed_states=completed_states)

        apply_map_styles(m, PALETTE)

        marker_cluster = MarkerCluster().add_to(m)
        for _, row in df_map_sorted.iterrows():
            if selected_display != "None" and row["folder_path"] == res["folder_path"]:
                continue

            race_key = f"{row['Name']} ({row['Year']})"
            is_previewed = race_key == st.session_state.previewed_race

            marker = folium.Marker(
                location=[row["Lat"], row["Lon"]],
                tooltip=race_key,
                popup=get_popup(row, show=is_previewed),
                icon=folium.DivIcon(html='<div class="heritage-pin"><i class="fa fa-person-running"></i></div>'),
            )
            # Previewed marker goes directly on the map so show=True works;
            # MarkerCluster intercepts popup rendering and suppresses auto-open
            marker.add_to(m if is_previewed else marker_cluster)

        track_points, elev_df, y_bounds = None, None, None
        if selected_display != "None":
            folder_path = race_display_map[selected_display]
            if is_relay:
                add_relay_tracks_to_map(m, get_all_relay_legs(folder_path), PALETTE, course_style=res.get("Course Style", "Point-to-Point"))
            else:
                track_points, elev_df, y_bounds = get_track_data(folder_path)
                if track_points:
                    add_route_to_map(m, track_points, PALETTE["red"])
                    m.fit_bounds(track_points)

        # Tooltip text matches race_display_map keys, so it directly identifies the clicked race.
        # Only restore saved viewport in overview/preview mode; in full race view
        # let fit_bounds() zoom the map to the GPS track naturally.
        _restore_viewport = selected_display == "None"
        map_output = st_folium(
            m,
            width="100%",
            height=600,
            key="history_map",
            returned_objects=["last_object_clicked_tooltip", "center", "zoom"],
            center=st.session_state.map_center if _restore_viewport else None,
            zoom=st.session_state.map_zoom if _restore_viewport else None,
        )

        clicked = map_output.get("last_object_clicked_tooltip") if map_output else None
        if clicked and clicked in race_display_map:
            raw_center = map_output.get("center")
            if raw_center:
                st.session_state.map_center = [raw_center["lat"], raw_center["lng"]]
            raw_zoom = map_output.get("zoom")
            if raw_zoom is not None:
                st.session_state.map_zoom = raw_zoom

            if selected_display == "None":
                if clicked != st.session_state.previewed_race:
                    st.session_state.previewed_race = clicked
                    st.rerun()
            else:
                if clicked != selected_display:
                    st.session_state._race_navigation = clicked
                    st.session_state.previewed_race = None
                    st.rerun()

        if not is_relay and elev_df is not None:
            st.write("#### Elevation Profile")
            plot_elevation_profile(elev_df, y_bounds, map_cfg, PALETTE)

    with col_stats:
        if selected_display != "None":
            _render_full_race_view(res, is_relay, PALETTE)
        elif st.session_state.previewed_race:
            preview_key = st.session_state.previewed_race
            preview_row = df_filtered[df_filtered["folder_path"] == race_display_map[preview_key]].iloc[0]
            _render_race_preview(preview_key, preview_row, race_display_map, PALETTE)
        else:
            _render_overview_metrics(df_filtered)


# -------------------------------------------------------------------------------- #
# 📖 DETAILED RESULTS TAB
# -------------------------------------------------------------------------------- #

with tab_details:
    st.markdown(f"<h2 style='color:{PALETTE['dark_teal']};'>📖 Historical Results Ledger</h2>", unsafe_allow_html=True)

    df_ledger = df_filtered.copy()
    if not df_ledger.empty:
        df_ledger["Pace"] = df_ledger["Pace"].apply(format_pace)
        df_ledger["GAP"] = df_ledger["GAP"].apply(format_pace)
        df_ledger["Date"] = df_ledger["Date"].dt.strftime("%Y-%m-%d")

        cols = ["Date", "Name", "State", "Distance", "Unit", "Pace", "GAP", "Elevation"]
        st.dataframe(df_ledger[cols].sort_values("Date", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("No races found for the selected filters.")
