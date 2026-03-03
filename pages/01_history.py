import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from src.data_loader import get_track_data, load_race_history, load_map_config
from src.pace import calculate_climb_density, format_pace

st.set_page_config(page_title="Race History | Race Log", layout="wide")

st.title("🏃 Race History & Performance")

# 1. Load Data and Config
df = load_race_history()
map_cfg = load_map_config()

# 2. Sidebar Filters
st.sidebar.header("Filters")
all_states = sorted(df['State'].dropna().unique())
state_filter = st.sidebar.multiselect("Filter by State", options=all_states)

all_types = sorted(df['Type'].dropna().unique())
type_filter = st.sidebar.multiselect("Race Type", options=all_types, default=[t for t in all_types if t == "Trail"])

# 3. Apply Pandas Filtering
mask = pd.Series([True] * len(df))
if state_filter: mask &= df['State'].isin(state_filter)
if type_filter: mask &= df['Type'].isin(type_filter)
df_filtered = df[mask].copy()

# 4. GPX Selection & Auto-Toggle Logic
st.sidebar.markdown("---")
st.sidebar.header("Map Settings")

race_options = ["None"] + sorted(df_filtered['Name'].tolist())
selected_race_name = st.sidebar.selectbox("Select a race for GPS view", options=race_options)

# LOGIC: Auto-off highlight if a race is selected, but allow manual override
default_highlight = True if selected_race_name == "None" else False
show_state_highlights = st.sidebar.checkbox("Highlight Completed States", value=default_highlight)

# 5. UI Tabs
tab_map, tab_details = st.tabs(["🗺️ Interactive Map", "📊 Detailed Results"])

with tab_map:
    # Title logic: Show race name if selected, otherwise a generic header
    if selected_race_name != "None":
        st.subheader(f"📍 {selected_race_name}")
    else:
        st.subheader("📍 Course Explorer")
    
    col_map, col_stats = st.columns([3, 1])

    with col_map:
        # Initialize Map from Config
        m = folium.Map(
            location=map_cfg["map_defaults"]["location"], 
            zoom_start=map_cfg["map_defaults"]["zoom"], 
            tiles="CartoDB Voyager"
        )

        # A. State Highlights (JSON Driven)
        if show_state_highlights:
            completed_states = df_filtered['State'].unique().tolist()
            style = map_cfg["highlight_style"]
            
            folium.GeoJson(
                map_cfg["states_geo_url"],
                style_function=lambda feature: {
                    'fillColor': style["fill_color"] if feature['id'] in completed_states else 'transparent',
                    'color': style["border_color"],
                    'weight': style["weight"],
                    'fillOpacity': style["fill_opacity"] if feature['id'] in completed_states else 0,
                },
                tooltip=folium.GeoJsonTooltip(fields=['name'], aliases=['State: '])
            ).add_to(m)

        # B. Markers & GPX Overlay
        track_points, elev_df = None, None
        for _, row in df_filtered.iterrows():
            if row['Lat'] and row['Lon']:
                color = "cadetblue" if row['is_official'] else "orange"
                folium.Marker(
                    location=[row['Lat'], row['Lon']],
                    popup=f"{row['Name']} ({row['Year']})",
                    icon=folium.Icon(color=color, icon="person-running", prefix="fa")
                ).add_to(m)

        if selected_race_name != "None":
            race_info = df_filtered[df_filtered['Name'] == selected_race_name].iloc[0]
            track_points, elev_df, y_bounds = get_track_data(race_info['folder_path'])
            y_min, y_max = y_bounds
            if track_points:
                folium.PolyLine(track_points, color="#E91E63", weight=4, opacity=0.8).add_to(m)
                m.fit_bounds(track_points)

        st_folium(m, width="100%", height=600)

        # C. Elevation Profile
        if elev_df is not None:
            st.write(f"#### Elevation Profile")

            c_style = map_cfg["chart_style"]

            # Build the Plotly Figure
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=elev_df["Distance (mi)"],
                y=elev_df["Elevation (ft)"],
                mode='lines',
                line=dict(color=c_style["primary_color"], width=2),
                fill='tozeroy',
                fillcolor=c_style["fill_color"],
                hovertemplate='<b>Distance:</b> %{x:.2f} mi<br><b>Elevation:</b> %{y:,.0f} ft<extra></extra>'
            ))

            fig.update_layout(
                height=c_style["height"],
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(
                            title="Distance (miles)", 
                            showgrid=False,
                            # This brings back the vertical bar
                            showspikes=True,
                            spikemode='across',
                            spikethickness=1,
                            spikedash='dash',
                            spikecolor='#999999',
                            # This is the secret: it prevents the axis from showing a value on hover
                            showticklabels=True
                        ),
                yaxis=dict(
                    title="Elevation (ft)", 
                    range=[y_min, y_max], # Respects your config buffer
                    showgrid=True,
                    gridcolor='rgba(200, 200, 200, 0.2)'
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                hovermode='x',
            )

            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col_stats:
        st.write("### Quick Stats")
        if selected_race_name != "None":
            res = df_filtered[df_filtered['Name'] == selected_race_name].iloc[0]
            
            # 1. Format the number (strip .0 if it's an integer)
            dist_val = res['Distance']
            clean_num = int(dist_val) if dist_val == int(dist_val) else dist_val
            
            # 2. Handle unit suffix and spacing
            unit_raw = str(res['Unit']).lower()
            
            if 'k' in unit_raw or 'kilometer' in unit_raw:
                # No space for kilometers (e.g., 15k)
                display_text = f"{clean_num}k"
            elif 'mile' in unit_raw:
                # Space for miles (e.g., 10 miles)
                display_text = f"{clean_num} miles"
            else:
                # Generic fallback
                display_text = f"{clean_num} {res['Unit']}"
            
            st.metric("Distance", display_text)

            # Pace metrics
            st.metric("Pace", f"{format_pace(res['Pace'])} min/mi")
            st.metric("GAP", f"{format_pace(res['GAP'])} min/mi")

            # Climb Density Metric
            gain_per_mile = calculate_climb_density(res['Elevation'], res['Distance'])
            st.metric("Avg. Climb", f"{gain_per_mile} ft/mi")

            st.metric("Elevation", f"{int(res['Elevation'] or 0):,} ft")
        else:
            st.metric("Races Shown", len(df_filtered))
            st.metric("Total Gain", f"{int(df_filtered['Elevation'].sum()):,} ft")

with tab_details:
    st.subheader("Historical Results Ledger")
    df_display = df_filtered.copy()
    df_display['Pace'] = df_display['Pace'].apply(format_pace)
    df_display['GAP'] = df_display['GAP'].apply(format_pace)
    df_display['Date'] = df_display['Date'].dt.strftime('%Y-%m-%d')
    
    cols = ['Date', 'Name', 'State', 'Distance', 'Unit', 'Pace', 'GAP', 'Elevation']
    st.dataframe(df_display[cols].sort_values('Date', ascending=False), use_container_width=True, hide_index=True)
