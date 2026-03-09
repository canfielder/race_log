import os
import json
import pandas as pd
import pathlib
import streamlit as st
import gpxpy
from dotenv import load_dotenv

from src.paths import CONFIG_DIR, RAW_DIR, RESULTS_DIR
from src.pace import (
    calculate_climb_density, calculate_elevation_bounds, calculate_paces
)

# Load the .env file
load_dotenv()

# Access the key
TF_API_KEY = os.getenv("THUNDERFOREST_API_KEY")

@st.cache_data
def load_future_races():
    # Use the RAW_DIR imported from src.paths
    path = RAW_DIR / 'possible_races.csv'
    
    if not path.exists():
        st.error(f"Could not find spreadsheet at {path}")
        return pd.DataFrame()
        
    return pd.read_csv(path)


@st.cache_data
def load_race_history(verbose=False):
    history_data = []
    
    for json_path in RESULTS_DIR.glob("**/*.json"):
        if json_path.name.startswith("._"):
            if verbose:
                print(f"File Detected With Leading Underscore: {json_path}")
            continue

        if verbose:
            print(f"📂 Processing: {json_path}")

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
                # Extracting nested values
                meta = data.get('race_metadata', {})
                res = data.get('results', {})
                src = data.get('sources', {}) # New source extraction
                
                row = {
                    "Name": meta.get('name'),
                    "Date": pd.to_datetime(meta.get('date')),
                    "Year": pd.to_datetime(meta.get('date')).year,
                    "Distance": meta.get('distance_value'),
                    "Unit": meta.get('distance_unit'),
                    "Type": meta.get('type'),
                    "Course Style": meta.get('course_style', "Point-to-Point"),
                    "Surface": meta.get('surface'),
                    "Time": res.get('official_time'),
                    "Elevation": res.get('elevation_gain'),
                    "State": meta.get('start_state'),
                    "Lat": meta.get('location_gps')[0] if meta.get('location_gps') else None,
                    "Lon": meta.get('location_gps')[1] if meta.get('location_gps') else None,
                    "is_official": res.get('is_official', False),
                    "folder_path": str(json_path.parent),

                    
                    # New URL fields
                    "athlinks_url": src.get('athlinks_url', None),
                    "original_url": src.get('original_url', None),
                    "strava_url": src.get('strava_url', None)
                }

                # Calculate Paces
                pace, gap = calculate_paces(row)
                row["Pace"] = pace
                row["GAP"] = gap

                history_data.append(row)

        except json.JSONDecodeError as e:
            # We always print errors, regardless of verbose level
            print(f"\n❌ JSON ERROR in: {json_path}")
            print(f"   Line {e.lineno}, Col {e.colno}: {e.msg}")
            continue

    df = pd.DataFrame(history_data)

    if not df.empty:
            # --- THE NULL FIX ---
            # Force numeric conversion and fill NaNs with 0 for metrics
            cols_to_fix = ["Distance", "Elevation", "Lat", "Lon"]
            for col in cols_to_fix:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df


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


@st.cache_data
def get_all_relay_legs(folder_path):
    """
    Parses all .gpx files in the folder and returns a list of 
    (points_list, label_string) tuples.
    """
    relay_data = []
    
    # Get all .gpx files and sort them to ensure consistent ordering
    files = sorted([f for f in os.listdir(folder_path) if f.endswith('.gpx')])
    
    for file in files:
        file_path = os.path.join(folder_path, file)
        
        # Parse GPX
        with open(file_path, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
            points = []
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        points.append((point.latitude, point.longitude))
        
        # Create a clean label from the filename (e.g., 'leg_01.gpx' -> 'Leg 01')
        label = file.replace('.gpx', '').replace('_', ' ').title()
        
        relay_data.append((points, label))
        
    return relay_data


def get_filtered_data(df, state_filter, type_filter, year_range):
    mask = df['Year'].between(year_range[0], year_range[1])
    if state_filter: mask &= df['State'].isin(state_filter)
    if type_filter: mask &= df['Type'].isin(type_filter)
    return df[mask].sort_values(by=['Date', 'Name'], ascending=False)


def get_raced_states(results_dir):
    """Scans all past race metadata to return a unique set of states."""
    raced_states = set()
    for meta_file in results_dir.rglob("metadata.json"):
        try:
            with open(meta_file, 'r') as f:
                data = json.load(f)
                # Navigate into the nested 'race_metadata' dictionary
                meta = data.get('race_metadata', {})
                state = meta.get('start_state', '').strip().upper()
                if state:
                    raced_states.add(state)
        except (json.JSONDecodeError, AttributeError):
            continue
    return raced_states
