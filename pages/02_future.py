import streamlit as st
import folium
import json
import pandas as pd
from streamlit_folium import st_folium
import folium.plugins as plugins
from src.data_loader import load_future_races
from src.paths import PROJECT_ROOT

st.set_page_config(page_title="Future Planning", layout="wide")

# --- DATA LOADING ---
df = load_future_races()

# --- PREPARE FILTER DATA ---
all_states = sorted(df["State Name"].dropna().unique())
month_order = df[['Month', 'Month, Number']].drop_duplicates().sort_values('Month, Number')
month_list = month_order['Month'].tolist()

# Load regions from config
regions_path = PROJECT_ROOT / "config" / "regions.json"
try:
    with open(regions_path, "r") as f:
        regions = json.load(f)
except FileNotFoundError:
    regions = {}
    st.error(f"Region config not found at {regions_path}")

# --- TOP FILTER SECTION ---
st.title("📅 Future Race Scouting")

# Season Slider above the tabs
with st.container(border=True):
    st.write("### 🗓️ Select Your Racing Season")
    start_month, end_month = st.select_slider(
        'Month Range',
        options=month_list,
        value=(month_list[0], month_list[-1]),
        label_visibility="collapsed"
    )

# --- SIDEBAR: REGIONS & INSIGHTS ---
with st.sidebar:
    st.header("📍 Region Filters")

    # Initialize session state for states if not present
    if "states_filter" not in st.session_state:
        st.session_state.states_filter = all_states

    # Bulk Select Buttons
    q_col1, q_col2 = st.columns(2)
    if q_col1.button("Select All", use_container_width=True):
        st.session_state.states_filter = all_states
    if q_col2.button("Clear All", use_container_width=True):
        st.session_state.states_filter = []

    # Region Grid
    st.write("**Region Shortcuts:**")
    r_cols = st.columns(2)
    for i, region_name in enumerate(regions.keys()):
        if r_cols[i % 2].button(region_name, use_container_width=True):
            target_states = regions[region_name]
            # Update filter to only states in that region that exist in the data
            st.session_state.states_filter = [s for s in target_states if s in all_states]

    # Individual State Selection (synced via key)
    states_filter = st.multiselect(
        "Individual States:", 
        options=all_states, 
        key="states_filter"
    )
    
    st.divider()

    # --- FILTER LOGIC ---
    start_num = month_order[month_order['Month'] == start_month]['Month, Number'].values[0]
    end_num = month_order[month_order['Month'] == end_month]['Month, Number'].values[0]

    df_filtered = df[
        (df["State Name"].isin(states_filter)) &
        (df["Month, Number"] >= start_num) &
        (df["Month, Number"] <= end_num)
    ]

    # DYNAMIC METRICS
    st.header("📊 Scouting Insights")
    st.metric("Total Races Found", len(df_filtered))
    
    if not df_filtered.empty:
        st.write("**Distance Mix:**")
        dist_counts = df_filtered['Distance'].value_counts()
        for dist, count in dist_counts.items():
            st.progress(count / len(df_filtered), text=f"{dist}: {count}")

# --- MAIN TABS ---
tab_map, tab_table = st.tabs(["🗺️ Map View", "📊 Table View"])

with tab_map:
    if df_filtered.empty:
        st.warning("No races match your current filters.")
        map_center = [35.2271, -80.8431] # Default to Charlotte
    else:
        map_center = [df_filtered["Latitude"].mean(), df_filtered["Longitude"].mean()]

    m = folium.Map(location=map_center, zoom_start=6)

    for _, row in df_filtered.iterrows():
        # Clean tooltip with Name, Month, and Location
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
    