import folium
import plotly.graph_objects as go
import streamlit as st

from src.ui_utils import (
    get_cluster_css,
    get_marker_css
)

def plot_elevation_profile(elev_df, y_bounds, map_cfg, PALETTE):
    """Handles the rendering of the elevation Plotly chart."""
    c_hex = PALETTE['caramel'].lstrip('#')
    rgb = tuple(int(c_hex[i:i+2], 16) for i in (0, 2, 4))
    clean_ink = PALETTE['ink_black'][:7]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=elev_df["Distance (mi)"], 
        y=elev_df["Elevation (ft)"],
        mode='lines',
        line=dict(color=PALETTE['spice'], width=3),
        fill="tozeroy",
        fillgradient=dict(
            type="vertical",
            colorscale=[[0.0, f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.0)"], 
                        [1.0, f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.4)"]]
        ),
        hovertemplate='%{y:,.0f} ft<extra></extra>'
    ))

    fig.update_layout(
        height=map_cfg["chart_style"]["height"], 
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis=dict(showgrid=False, showspikes=True, spikemode='across', spikedash='dot', spikecolor=clean_ink),
        yaxis=dict(range=[y_bounds[0], y_bounds[1]] if y_bounds else None, showgrid=True, gridcolor='rgba(0, 18, 25, 0.1)', zeroline=False),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', hovermode='x'
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def add_relay_tracks_to_map(m, relay_data_list, palette, course_style):
    colors = [palette['red'], palette['dark_teal'], palette['orange'], palette['spice'], '#8E44AD', '#27AE60', '#F39C12']
    
    # Circuit relays need more transparency to prevent 'pooling' at the hub
    if course_style.lower() == "circuit":
        weight = 4
        opacity = 0.5
    else:
        weight = 5
        opacity = 0.75
        
    for i, (points, label) in enumerate(relay_data_list):
        color = colors[i % len(colors)]
        folium.PolyLine(
            points, 
            color=color, 
            weight=weight, 
            opacity=opacity,
            tooltip=label
        ).add_to(m)

     # Fit map to the whole route
    if relay_data_list:
        all_points = [p for leg, _ in relay_data_list for p in leg]
        
        # Calculate bounds manually
        min_lat = min(p[0] for p in all_points)
        min_lon = min(p[1] for p in all_points)
        max_lat = max(p[0] for p in all_points)
        max_lon = max(p[1] for p in all_points)
        
        # Folium's fit_bounds accepts a list of two points: [[sw_lat, sw_lon], [ne_lat, ne_lon]]
        m.fit_bounds(
            [[min_lat, min_lon], [max_lat, max_lon]],
            padding=(50, 50)
            )
    
    return m


def add_route_to_map(m, track_points, color, weight=4, opacity=0.8):
    """
    Renders a single GPX track onto the Folium map.
    """
    folium.PolyLine(
        track_points,
        color=color,
        weight=weight,
        opacity=opacity
    ).add_to(m)


def apply_state_highlights(m, geo_url, palette, completed_states):
    # styles
    highlight_style = {
        "fillColor": palette['pearl_aqua'],
        "color": palette['dark_teal'],
        "weight": 2,
        "fillOpacity": 0.3
        }

    non_highlight_style = {
        "fillColor": "transparent",
        "color": "#999",
        "weight": 0.5,
        "fillOpacity": 0
    }

    folium.GeoJson(
        geo_url,
        style_function=lambda x:  highlight_style if x['id'] in completed_states else non_highlight_style
        ).add_to(m)


def get_popup(row, show=False):
    unit_map = {"miles": "mi", "mile": "mi", "kilometers": "km", "kilometer": "km"}
    unit = unit_map.get(str(row.get('Unit', '')).lower(), row.get('Unit', ''))

    raw_dist = row.get('Distance', '')
    dist = int(raw_dist) if isinstance(raw_dist, float) and raw_dist % 1 == 0 else raw_dist

    location_str = ', '.join(filter(None, [row.get('City'), row.get('State')]))

    html = f"""
        <div style="font-family: sans-serif; min-width: 140px;">
            <b>{row.get('Name')}</b><br>
            📅 {row['Date'].strftime('%B %d, %Y')}<br>
            📍 {location_str}<br>
            📏 {dist} {unit}
        </div>
    """
    return folium.Popup(html, max_width=200, show=show)


def apply_map_styles(m, palette):
    cluster_css = get_cluster_css(palette)
    marker_style = get_marker_css(palette)
    m.get_root().header.add_child(folium.Element(cluster_css))
    m.get_root().header.add_child(folium.Element(marker_style))