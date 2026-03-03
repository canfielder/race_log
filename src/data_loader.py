import json
import pandas as pd
import pathlib
import streamlit as st
import gpxpy

from src.paths import CONFIG_DIR, RAW_DIR, RESULTS_DIR
from src.pace import (
    calculate_climb_density, calculate_elevation_bounds, calculate_paces
)

@st.cache_data
def load_future_races():
    # Use the RAW_DIR imported from src.paths
    path = RAW_DIR / 'possible_races.xlsx'
    
    if not path.exists():
        st.error(f"Could not find spreadsheet at {path}")
        return pd.DataFrame()
        
    return pd.read_excel(path, sheet_name="races")


@st.cache_data
def load_race_history():
    history_data = []
    
    for json_path in RESULTS_DIR.glob("**/*.json"):
        with open(json_path, 'r') as f:
            data = json.load(f)
            
            # Extracting nested values
            meta = data.get('race_metadata', {})
            res = data.get('results', {})
            
            row = {
                "Name": meta.get('name'),
                "Date": pd.to_datetime(meta.get('date')),
                "Year": pd.to_datetime(meta.get('date')).year, # Added for map popup
                "Distance": meta.get('distance_value'),
                "Unit": meta.get('distance_unit'),
                "Type": meta.get('type'),
                "Surface": meta.get('surface'),
                "Time": res.get('official_time'),
                "Elevation": res.get('elevation_gain'),
                "State": meta.get('start_state'),
                "Lat": meta.get('location_gps')[0] if meta.get('location_gps') else None,
                "Lon": meta.get('location_gps')[1] if meta.get('location_gps') else None,
                "is_official": res.get('is_official', False),
                "folder_path": str(json_path.parent) # Crucial for finding activity.gpx
            }

            # Calculate Paces
            pace, gap = calculate_paces(row)
            row["Pace"] = pace
            row["GAP"] = gap

            history_data.append(row)

    return pd.DataFrame(history_data)


@st.cache_data
def get_track_data(folder_path):
    """
    Parses activity.gpx from the race folder.
    Returns:
        points: List of (lat, lon) tuples for folium.
        df_elev: Pandas DataFrame with Distance and Elevation.
        y_bounds: Tuple of (y_min, y_max) for chart scaling.
    """
    gpx_path = pathlib.Path(folder_path) / "activity.gpx"
    
    # Fallback to find any .gpx file in the directory
    if not gpx_path.exists():
        gpx_files = list(pathlib.Path(folder_path).glob("*.gpx"))
        if not gpx_files:
            return None, None, None
        gpx_path = gpx_files[0]

    try:
        with open(gpx_path, 'r') as f:
            gpx = gpxpy.parse(f)
        
        points = []
        elevation_data = []
        total_dist = 0.0
        prev_point = None

        for track in gpx.tracks:
            for segment in track.segments:
                # Optional: Simplify track for performance if files are massive
                # segment.simplify(5) 
                
                for point in segment.points:
                    # 1. Store coordinates for Map
                    points.append((point.latitude, point.longitude))
                    
                    # 2. Calculate Cumulative Distance (Meters to Miles)
                    if prev_point:
                        dist_delta = point.distance_2d(prev_point) * 0.000621371
                        total_dist += dist_delta
                    
                    # 3. Store Elevation (Meters to Feet)
                    elev_ft = point.elevation * 3.28084 if point.elevation else 0
                    
                    elevation_data.append({
                        "Distance (mi)": total_dist,
                        "Elevation (ft)": elev_ft
                    })
                    prev_point = point
        
        df_elev = pd.DataFrame(elevation_data)
        
        if not df_elev.empty:
            # 1. Calculate the actual physical stats
            total_gain = df_elev["Elevation (ft)"].diff().clip(lower=0).sum()
            total_dist = df_elev["Distance (mi)"].max()
            density = calculate_climb_density(total_gain, total_dist)

            # 2. Get the visually normalized bounds
            y_min, y_max = calculate_elevation_bounds(df_elev, density)
            
            return points, df_elev, (y_min, y_max)
            
        return points, None, None

    except Exception as e:
        st.error(f"Error parsing GPX: {e}")
        return None, None, None


@st.cache_data
def load_map_config():
    config_path = CONFIG_DIR / "map_style.json"
    with open(config_path, "r") as f:
        return json.load(f)
