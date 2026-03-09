import streamlit as st
import pandas as pd
import folium
import os
import pathlib
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

from src.data_loader import (
    get_all_relay_legs,
    get_track_data,
    load_race_history,
    load_map_config,
    get_filtered_data
)
from src.pace import calculate_climb_density, format_pace
from src.plotting import (
    add_relay_tracks_to_map,
    add_route_to_map,
    apply_map_styles,
    apply_state_highlights,
    plot_elevation_profile
)
from src.ui_utils import get_styles

st.set_page_config(page_title="Race History | Race Log", layout="wide")

# Load configuration and data
df = load_race_history(verbose=False)
map_cfg = load_map_config()
PALETTE = map_cfg["palette"]
tf_api_key = os.getenv("THUNDERFOREST_API_KEY", None)

# Apply global styles
st.markdown(get_styles(PALETTE), unsafe_allow_html=True)
st.title("🏃 Race History & Performance")

# Handle global filters
with st.container():
    st.markdown(f"<h3 style='color:{PALETTE['dark_teal']}; margin-bottom: 0;'>Race Timeline</h3>", unsafe_allow_html=True)
    unique_years = sorted(df['Year'].unique())
    year_range = st.select_slider("Filter by Year", options=unique_years, value=(min(unique_years), max(unique_years)))

# Sidebar filtering logic
st.sidebar.header("Filters")
state_filter = st.sidebar.multiselect("Filter by State", options=sorted(df['State'].dropna().unique()))
type_filter = st.sidebar.multiselect("Race Type", options=sorted(df['Type'].dropna().unique()), default=sorted(df['Type'].dropna().unique()))

# Apply filters via modular helper
df_filtered = get_filtered_data(df, state_filter, type_filter, year_range)
df_map_sorted = df_filtered.sort_values(by=['Date', 'Name'], ascending=False)

# Map selection settings
st.sidebar.markdown("---")
st.sidebar.header("Map Settings")
race_display_map = {f"{row['Name']} ({row['Year']})": row['folder_path'] for _, row in df_map_sorted.iterrows()}
selected_display = st.sidebar.selectbox("Select a race for GPS view", ["None"] + sorted(race_display_map.keys()))
show_state_highlights = st.sidebar.checkbox("Highlight Completed States", value=(selected_display == "None"))

tab_map, tab_details = st.tabs(["🗺️ Interactive Map", "📊 Detailed Results"])

with tab_map:
    header_text = f"📍 {selected_display}" if selected_display != "None" else "📍 Course Explorer"
    st.markdown(f"<h2 style='color:{PALETTE['dark_teal']}; margin-bottom: 20px;'>{header_text}</h2>", unsafe_allow_html=True)

    res = None
    is_relay = False
    if selected_display != "None":
        target_path = race_display_map[selected_display]
        res = df_filtered[df_filtered['folder_path'] == target_path].iloc[0]

        # DYNAMIC RELAY DETECTION:
        # Check if there is more than one .gpx file in the race folder
        gpx_files = list(pathlib.Path(target_path).glob("*.gpx"))
        is_relay = len(gpx_files) > 1

    col_map, col_stats = st.columns([3, 1])

    with col_map:
        # Determine map tiles based on API key availability
        tile_url = f"https://tile.thunderforest.com/outdoors/{{z}}/{{x}}/{{y}}.png?apikey={tf_api_key}" if tf_api_key else 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png'
        map_attr = '&copy; Thunderforest' if tf_api_key else 'Map data: &copy; OpenStreetMap'
        
        # Initialize map
        m = folium.Map(
            location=map_cfg["map_defaults"]["location"],
            zoom_start=map_cfg["map_defaults"]["zoom"],
            tiles=tile_url if selected_display != "None" else "CartoDB Voyager",
            attr=map_attr
            )

        # Draw state overlays if no specific race is selected
        if show_state_highlights:
            completed_states = df_filtered['State'].unique()
            apply_state_highlights(
                m,
                geo_url=map_cfg["states_geo_url"],
                palette=PALETTE,
                completed_states=completed_states
            )

        # Apply custom pin and cluster styles
        apply_map_styles(m, PALETTE)

        # Add race markers to a cluster
        marker_cluster = MarkerCluster().add_to(m)
        for _, row in df_map_sorted.iterrows():
            if selected_display != "None" and row['folder_path'] == res['folder_path']: continue
            folium.Marker(location=[row['Lat'], row['Lon']], tooltip=f"{row['Name']} ({row['Year']})", icon=folium.DivIcon(html=f'<div class="heritage-pin"><i class="fa fa-person-running"></i></div>')).add_to(marker_cluster)

        track_points, elev_df, y_bounds = None, None, None

        # Draw selected race tracks
        if selected_display != "None":
            folder_path = race_display_map[selected_display]
            if is_relay:
                add_relay_tracks_to_map(
                    m,
                    get_all_relay_legs(folder_path),
                    PALETTE,
                    course_style=res.get('Course Style', 'Point-to-Point')
                    )
            else:
                track_points, elev_df, y_bounds = get_track_data(folder_path)
                if track_points:
                    add_route_to_map(
                        m,
                        track_points,
                        PALETTE['red']
                        )
                    m.fit_bounds(track_points)
            
        st_folium(m, width="100%", height=600, key="history_map")

        # Elevation rendering: only if it's NOT a relay and data exists
        if not is_relay and elev_df is not None:
            st.write("#### Elevation Profile")
            plot_elevation_profile(elev_df, y_bounds, map_cfg, PALETTE)

    with col_stats:
        # Quick Stats section for the selected race
        if selected_display != "None":
            st.markdown(f"<h3 style='color:{PALETTE['dark_teal']}'>Quick Stats</h3>", unsafe_allow_html=True)
            r_type = str(res.get('Type', 'Trail')).lower()
            st.markdown(f"**{'⛰️' if 'trail' in r_type else '👟'} {res['Type']} Race**")
            st.metric("📍 Distance", f"{int(res['Distance']) if res['Distance'] == int(res['Distance']) else res['Distance']} {'k' if 'k' in str(res['Unit']).lower() else 'miles'}")
            st.metric("⏱️ Total Time", value=res.get('Time', '--:--:--'))
            
            if not is_relay and res.get('Elevation', 0) > 0:
                st.metric("🔼 Vertical Gain", f"{int(res['Elevation']):,} ft")
                st.metric("📐 Avg. Climb", f"{calculate_climb_density(res['Elevation'], res['Distance'])} ft/mi")
            else:
                st.caption("🏔️ *Elevation stats not tracked for relays*")
                
            st.metric("⚡ Pace", f"{format_pace(res['Pace'])} min/mi")

            if 'GAP' in res and pd.notna(res['GAP']):
                st.metric("📈 GAP (Grade Adj)", f"{format_pace(res['GAP'])} /mi")
            
            # External Links rendering
            st.markdown("---")
            st.markdown("**🔗 Race Records**")
            if res.get('athlinks_url'): 
                st.link_button("🏆 Athlinks Results", res['athlinks_url'], use_container_width=True, type="primary")
           
           # Social/Activity (Strava)
            strava_data = res.get('strava_url')

            if strava_data:
                # Case 1: New Relay Schema (List of dicts)
                if isinstance(strava_data, list):
                    for entry in strava_data:
                        # Ensure it's a dict before accessing keys
                        if isinstance(entry, dict):
                            label = entry.get('label', 'Strava Activity')
                            icon = "🏃" if "Leg" in label else "🧡"
                            url = entry.get('url')
                            if url:
                                st.link_button(f"{icon} {label}", url, use_container_width=True)

                        # Fallback if it's just a list of strings
                        elif isinstance(entry, str):
                            st.link_button("🧡 Strava Activity", entry, use_container_width=True)
                            
                # Case 2: Legacy Schema (Single string)
                elif isinstance(strava_data, str):
                    st.link_button("🧡 Strava Activity", strava_data, use_container_width=True)

            # 3. Original Source (Race Website/Backup)
            if res.get('original_url'):
                st.link_button("🌐 Official Records", res['original_url'], use_container_width=True)

        # Race has not been selected. Aggregate Metrics
        else:
            st.metric("🏁 Races Shown", f"{len(df_filtered):,}")
            st.metric("📍 Total Distance", f"{df_filtered['Distance'].sum():,.0f} mi")
            st.metric("⛰️ Total Gain", f"{int(df_filtered['Elevation'].sum()):,} ft")

with tab_details:
    st.markdown(f"<h2 style='color:{PALETTE['dark_teal']};'>📖 Historical Results Ledger</h2>", unsafe_allow_html=True)
    
    df_ledger = df_filtered.copy()
    if not df_ledger.empty:
        df_ledger['Pace'] = df_ledger['Pace'].apply(format_pace)
        df_ledger['GAP'] = df_ledger['GAP'].apply(format_pace)
        df_ledger['Date'] = df_ledger['Date'].dt.strftime('%Y-%m-%d')
        
        cols = ['Date', 'Name', 'State', 'Distance', 'Unit', 'Pace', 'GAP', 'Elevation']
        st.dataframe(df_ledger[cols].sort_values('Date', ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("No races found for the selected filters.")