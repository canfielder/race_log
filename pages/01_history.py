import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import folium
import os
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

from src.data_loader import get_track_data, load_race_history, load_map_config
from src.pace import calculate_climb_density, format_pace

st.set_page_config(page_title="Race History | Race Log", layout="wide")

# 1. Load Data and config
VERBOSE = False
df = load_race_history(verbose=VERBOSE)
map_cfg = load_map_config()
PALETTE = map_cfg["palette"]

tf_api_key = os.getenv("THUNDERFOREST_API_KEY", None)

# UI Style Injection
st.markdown(f"""
    <style>
    .stApp {{ background-color: {PALETTE['vanilla']}10; }} 
    h1, h2, h3 {{ color: {PALETTE['ink_black']}; font-family: 'serif'; }}
    
    /* --- NEW: Larger Metric Headers --- */
    [data-testid="stMetricLabel"] p {{
        font-size: 1.2rem !important; /* Increased from default */
        color: {PALETTE['dark_teal']} !important;
        font-weight: 700 !important;
        font-family: 'Arial', sans-serif;
    }}
    </style>
    """, 
    unsafe_allow_html=True
)

st.title("🏃 Race History & Performance")

# --- GLOBAL YEAR FILTER (Above Tabs) ---
with st.container():
    st.markdown(f"<h3 style='color:{PALETTE['dark_teal']}; margin-bottom: 0;'>Race Timeline</h3>", unsafe_allow_html=True)
    
    # Get range from full dataframe
    unique_years = sorted(df['Year'].unique())
    min_y, max_y = int(min(unique_years)), int(max(unique_years))
    
    year_range = st.select_slider(
        "Filter all data by Year Range",
        options=unique_years,
        value=(min_y, max_y),
        key="global_year_slider"
    )

# 2. Sidebar Filters (State & Type)
st.sidebar.header("Filters")
all_states = sorted(df['State'].dropna().unique())
state_filter = st.sidebar.multiselect("Filter by State", options=all_states)

all_types = sorted(df['Type'].dropna().unique())
type_filter = st.sidebar.multiselect("Race Type", options=all_types, default=all_types)

# 3. APPLY ALL FILTERING (Combine Sidebar + Global Year Slider)
mask = pd.Series([True] * len(df))
if state_filter: 
    mask &= df['State'].isin(state_filter)
if type_filter: 
    mask &= df['Type'].isin(type_filter)

# Apply the Year Slider Mask
mask &= df['Year'].between(year_range[0], year_range[1])

# Final Filtered Dataframes
df_filtered = df[mask].copy()
df_map_sorted = df_filtered.sort_values(by=['Date', 'Name'], ascending=False)

# 4. GPX Selection (Using the already filtered data)
st.sidebar.markdown("---")
st.sidebar.header("Map Settings")

race_display_map = {
    f"{row['Name']} ({row['Year']})": row['folder_path'] 
    for _, row in df_map_sorted.iterrows()
}
display_options = ["None"] + list(race_display_map.keys())

selected_display = st.sidebar.selectbox(
    "Select a race for GPS view", 
    options=display_options
)

show_state_highlights = st.sidebar.checkbox("Highlight Completed States", value=(selected_display == "None"))

# 5. UI Tabs
tab_map, tab_details = st.tabs(["🗺️ Interactive Map", "📊 Detailed Results"])

with tab_map:
    header_text = f"📍 {selected_display}" if selected_display != "None" else "📍 Course Explorer"
    st.markdown(f"<h2 style='color:{PALETTE['dark_teal']}; margin-bottom: 20px;'>{header_text}</h2>", unsafe_allow_html=True)
    
    col_map, col_stats = st.columns([3, 1])

    with col_map:
        # Determine the tile set based on selection
        if selected_display == "None":
            map_tiles = "CartoDB Voyager"
            map_attr = None
        
        else:
            if tf_api_key:
                map_tiles = f"https://tile.thunderforest.com/outdoors/{{z}}/{{x}}/{{y}}.png?apikey={tf_api_key}"
                map_attr = '&copy; <a href="https://www.thunderforest.com/">Thunderforest</a>, &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            else:
                # Use OpenTopoMap for the detailed GPX view
                map_tiles = 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png'
                map_attr = 'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a>'
            
        # Initialize Base Map
        m = folium.Map(
            location=map_cfg["map_defaults"]["location"], 
            zoom_start=map_cfg["map_defaults"]["zoom"], 
            tiles=map_tiles,
            attr=map_attr
        )

        # --- RE-ADD STATE OVERLAY LOGIC ---
        if show_state_highlights:
            # Get unique states from your full history (not just the filtered one)
            completed_states = df_filtered['State'].dropna().unique().tolist()
            
            # Use your new palette for the fill
            state_style = {
                "fillColor": PALETTE['pearl_aqua'],
                "color": PALETTE['dark_teal'],
                "weight": 2,
                "fillOpacity": 0.3,
            }

            folium.GeoJson(
                map_cfg["states_geo_url"],
                name="Completed States",
                style_function=lambda x: state_style if x['id'] in completed_states else {
                    "fillColor": "transparent", 
                    "color": "#999", 
                    "weight": 0.5, 
                    "fillOpacity": 0
                }
            ).add_to(m)
        # --- END STATE OVERLAY ---
        # CSS #
    
        # Aggressive CSS Override for Marker Clusters
        # This targets Folium's internal classes directly using your palette
        cluster_css = f"""
        <style>
            /* Small clusters (Pearl Aqua / Dark Cyan) */
            .marker-cluster-small {{
                background-color: {PALETTE['pearl_aqua']}aa !important;
            }}
            .marker-cluster-small div {{
                background-color: {PALETTE['dark_cyan']}aa !important;
                color: {PALETTE['ink_black']} !important;
                /* Standard Sans-Serif Stack */
                font-family: 'Arial', 'Helvetica', sans-serif !important;
                font-size: 13px !important;
                font-weight: 700 !important;
                border: 1px solid {PALETTE['ink_black']}22;
            }}
            
            /* Medium clusters (Vanilla / Orange) */
            .marker-cluster-medium {{
                background-color: {PALETTE['vanilla']}aa !important;
            }}
            .marker-cluster-medium div {{
                background-color: {PALETTE['orange']}aa !important;
                color: {PALETTE['ink_black']} !important;
                font-family: 'Arial', 'Helvetica', sans-serif !important;
                font-size: 13px !important;
                font-weight: 700 !important;
                border: 1px solid {PALETTE['ink_black']}22;
            }}

            /* General Cluster Shape & Alignment */
            .marker-cluster div {{
                width: 28px !important;
                height: 28px !important;
                margin-left: 6px !important;
                margin-top: 6px !important;
                text-align: center !important;
                border-radius: 50% !important;
                line-height: 28px !important;
            }}
        </style>
        """

        m.get_root().header.add_child(folium.Element(cluster_css))

        # Custom CSS for the Heritage Marker
        # This creates a clean, circular pin using your Dark Teal
        marker_style = f"""
            <style>
                .heritage-pin {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    width: 30px;
                    height: 30px;
                    background-color: {PALETTE['dark_teal']};
                    border: 2px solid {PALETTE['ink_black']};
                    border-radius: 50% 50% 50% 0;
                    transform: rotate(-45deg);
                    margin-top: -15px;
                    margin-left: -15px;
                }}
                .heritage-pin i {{
                    transform: rotate(45deg);
                    color: white;
                    font-size: 14px;
                }}
            </style>
        """
        m.get_root().header.add_child(folium.Element(marker_style))

        # 2. Add Markers to Cluster
        marker_cluster = MarkerCluster(options={
            'maxClusterRadius': 35,
            'spiderfyOnMaxZoom': True
        }).add_to(m)

        selected_lat, selected_lon = None, None
        if selected_display != "None":
            target_path = race_display_map[selected_display]
            selected_row = df_filtered[df_filtered['folder_path'] == target_path].iloc[0]
            selected_lat = selected_row.get('Lat')
            selected_lon = selected_row.get('Lon')

        for _, row in df_map_sorted.iterrows():
            lat, lon = row.get('Lat'), row.get('Lon')
            if lat is None or lon is None: continue

            # --- THE RADIUS HIDE ---
            # If a race is selected, hide ALL markers at that specific location
            # so the GPX track is completely unobstructed.
            if selected_lat is not None and selected_lon is not None:
                if lat == selected_lat and lon == selected_lon:
                    continue

            # Create the Heritage Label: "Race Name (2026)"
            full_label = f"{row['Name']} ({row['Year']})"

            # Use DivIcon to bypass Folium's limited color set
            icon = folium.DivIcon(
                html=f'<div class="heritage-pin"><i class="fa fa-person-running"></i></div>'
            )
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(f"<b>{full_label}</b>", max_width=200),
                tooltip=full_label,
                icon=icon
            ).add_to(marker_cluster)

        # Selected Race Track Overlay
        track_points, elev_df, y_bounds = None, None, None
        if selected_display != "None":
            # Pull the folder path directly from our display map
            folder_path = race_display_map[selected_display]
            
            track_points, elev_df, y_bounds = get_track_data(folder_path)
            
            if track_points:
                folium.PolyLine(
                    track_points, 
                    color=PALETTE['red'], 
                    weight=4, 
                    opacity=0.8
                ).add_to(m)
                
                m.fit_bounds(track_points)  

        st_folium(m, width="100%", height=600, key="history_map")

        # Elevation Profile using the Earth Tones
        if elev_df is not None:
            st.write("#### Elevation Profile")

            # Convert Caramel Hex to RGB for the gradient
            c_hex = PALETTE['caramel'].lstrip('#')
            rgb = tuple(int(c_hex[i:i+2], 16) for i in (0, 2, 4))

            clean_ink = PALETTE['ink_black'][:7]

            elev_min = elev_df["Elevation (ft)"].min()
            elev_max = elev_df["Elevation (ft)"].max()

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=elev_df["Distance (mi)"], 
                y=elev_df["Elevation (ft)"],
                mode='lines',
                line=dict(
                    color=PALETTE['spice'],
                    width=3,
                    # shape="spline"
                    ),
                fill="tozeroy",
                fillgradient=dict(
                    type="vertical",
                    start=elev_min,
                    stop=elev_max,
                    colorscale=[
                        [0.0, f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.0)"], # Bottom: fully transparent
                        [1.0, f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.4)"]  # Top: 40% opaque Caramel
                    ]
                ),
                hovertemplate='%{y:,.0f} ft<extra></extra>'
            ))

            fig.update_layout(
                height=map_cfg["chart_style"]["height"], 
                margin=dict(l=0, r=0, t=20, b=0),
                xaxis=dict(
                    showgrid=False,
                    showspikes=True,
                    spikemode='across',
                    spikedash='dot',
                    spikecolor=clean_ink
                    ),
                yaxis=dict(
                    range=[
                        y_bounds[0],
                        y_bounds[1]
                        ] if y_bounds else None, 
                        showgrid=True, 
                        gridcolor='rgba(0, 18, 25, 0.1)',
                        zeroline=False
                        ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                hovermode='x',
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col_stats:
        st.markdown(
            f"<h3 style='color:{PALETTE['dark_teal']}'>Quick Stats</h3>",
            unsafe_allow_html=True
            )
        if selected_display != "None":
            # 1. Get the folder path from our map
            target_path = race_display_map[selected_display]
            
            # 2. Find the exact record using the path instead of the Name
            res = df_filtered[df_filtered['folder_path'] == target_path].iloc[0]

            # 3. Race Type Icon Logic
            # Minimalist icons: Mountain for Trail, Road for Road
            r_type = str(res.get('Type', 'Trail')).lower()
            type_icon = "⛰️" if "trail" in r_type else "👟"
            
            # Distance logic
            dist_val = res['Distance']
            clean_num = int(dist_val) if dist_val == int(dist_val) else dist_val
            u = str(res.get('Unit', 'miles')).lower()
            display_dist = f"{clean_num}k" if 'k' in u else f"{clean_num} miles"

            # Pull elapsed time
            total_time = res.get('Time', '--:--:--')
            
            # 4. Styled Metrics
            st.markdown(f"**{type_icon} {res['Type']} Race**")

            st.metric("📍 Distance", display_dist)
            st.metric("⏱️ Total Time", value=total_time)
            st.metric("🔼 Vertical Gain", f"{int(res['Elevation'] or 0):,} ft")
            st.metric("⚡ Pace", f"{format_pace(res['Pace'])} min/mi")

            if 'GAP' in res and pd.notna(res['GAP']):
                st.metric("📈 GAP (Grade Adj)", f"{format_pace(res['GAP'])} /mi")

            st.metric("📐 Avg. Climb", f"{calculate_climb_density(res['Elevation'], res['Distance'])} ft/mi")

            # 5. External Sources Section
            st.markdown("---")
            st.markdown("**🔗 Race Records**")

            # 1. Official Results (Athlinks)
            if res.get('athlinks_url'):
                st.link_button("🏆 Athlinks Results", res['athlinks_url'], use_container_width=True, type="primary")

            # 2. Social/Activity (Strava)
            if res.get('strava_url'):
                st.link_button("🧡 Strava Activity", res['strava_url'], use_container_width=True)

            # 3. Original Source (Race Website/Backup)
            if res.get('original_url'):
                st.link_button("🌐 Official Records", res['original_url'], use_container_width=True)

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