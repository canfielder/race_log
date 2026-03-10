import streamlit as st
import folium
import json
import pandas as pd
from streamlit_folium import st_folium
import folium.plugins as plugins
from src.data_loader import get_raced_states, load_future_races
from src.paths import PROJECT_ROOT, RESULTS_DIR

st.set_page_config(page_title="Future Planning", layout="wide")


#### CONFIG & DATA

df = load_future_races()
raced_states = get_raced_states(RESULTS_DIR)

all_states = sorted(df["State Name"].dropna().unique())
month_order = df[['Month', 'Month, Number']].drop_duplicates().sort_values('Month, Number')
month_list = month_order['Month'].tolist()

regions_path = PROJECT_ROOT / "config" / "regions.json"
try:
    with open(regions_path, "r") as f:
        regions = json.load(f)
except FileNotFoundError:
    regions = {}
    st.error(f"Region config not found at {regions_path}")


#### SEASON FILTER

st.title("📅 Future Race Scouting")

with st.container(border=True):
    st.write("### 🗓️ Select Your Racing Season")
    start_month, end_month = st.select_slider(
        'Month Range',
        options=month_list,
        value=(month_list[0], month_list[-1]),
        label_visibility="collapsed"
    )


#### SIDEBAR

with st.sidebar:
    st.header("📍 Completed States")
    exclude_raced = st.sidebar.checkbox("Exclude states I've raced in", value=True)

    st.header("📍 Region Filters")

    if "states_filter" not in st.session_state:
        st.session_state.states_filter = all_states

    # Bulk select buttons
    q_col1, q_col2 = st.columns(2)
    if q_col1.button("Select All", use_container_width=True):
        st.session_state.states_filter = all_states
        st.rerun()
    if q_col2.button("Clear All", use_container_width=True):
        st.session_state.states_filter = []
        st.rerun()

    # Region shortcut buttons
    st.write("**Region Shortcuts:**")
    r_cols = st.columns(2)
    for i, region_name in enumerate(regions.keys()):
        if r_cols[i % 2].button(region_name, use_container_width=True):
            target_states = sorted(regions[region_name])
            st.session_state.states_filter = [s for s in target_states if s in all_states]
            st.rerun()

    new_selection = st.multiselect("Individual States:", options=all_states, key="states_filter")
    if new_selection != st.session_state.states_filter:
        st.session_state.states_filter = new_selection
        st.rerun()

    filter_list = st.session_state.states_filter

    st.divider()

    # FILTER LOGIC
    start_num = month_order[month_order['Month'] == start_month]['Month, Number'].values[0]
    end_num = month_order[month_order['Month'] == end_month]['Month, Number'].values[0]

    df_filtered = df[
        (df["State Name"].isin(filter_list)) &
        (df["Month, Number"] >= start_num) &
        (df["Month, Number"] <= end_num)
    ]
    if exclude_raced:
        df_filtered = df_filtered[~df_filtered['State'].str.upper().isin(raced_states)]

    # SCOUTING INSIGHTS
    st.header("📊 Scouting Insights")
    st.metric("Total Races Found", len(df_filtered))


#### TAB — MAP VIEW

tab_map, tab_table = st.tabs(["🗺️ Map View", "📊 Table View"])

with tab_map:
    if df_filtered.empty:
        st.warning("No races match your current filters.")
        map_center = [35.2271, -80.8431]
    else:
        map_center = [df_filtered["Latitude"].mean(), df_filtered["Longitude"].mean()]

    m = folium.Map(location=map_center, zoom_start=6)

    for _, row in df_filtered.iterrows():
        msg_tooltip = f"""
            <b>{row['Name']}</b><br>
            📅 {row['Month']}<br>
            📍 {row['Town']}, {row['State Name']}<br>
            📏 {row['Distance']}
        """
        msg_popup = msg_tooltip + f"<br>🔗 <a href='{row['Link']}' target='_blank'>Website</a>"

        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=folium.Popup(msg_popup, max_width=300),
            tooltip=msg_tooltip,
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

    plugins.Fullscreen().add_to(m)
    st_folium(m, width=1200, height=600, returned_objects=[])


#### TAB — TABLE VIEW

with tab_table:
    st.subheader("Scouting Details")
    st.dataframe(
        df_filtered.sort_values(by=["Month, Number", "State Name"]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Link": st.column_config.LinkColumn("Race Website"),
            "Month, Number": None,
            "Latitude": None,
            "Longitude": None,
            "Month": st.column_config.Column("Race Month", width="small")
        }
    )
