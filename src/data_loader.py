import json
import pandas as pd
import pathlib as pl
import streamlit as st

from src.paths import RAW_DIR, RESULTS_DIR
from src.pace import calculate_paces


@st.cache_data
def load_future_races(root_path):
    path = pl.Path(root_path, 'data', 'raw', 'possible_races.xlsx')
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
                "Distance": meta.get('distance_value'),
                "Unit": meta.get('distance_unit'),
                "Type": meta.get('type'),
                "Surface": meta.get('surface'),
                "Time": res.get('official_time'),
                "Elevation": res.get('elevation_gain'),
                "State": meta.get('start_state'),
                "Lat": meta.get('location_gps')[0] if meta.get('location_gps') else None,
                "Lon": meta.get('location_gps')[1] if meta.get('location_gps') else None,
                "is_official": res.get('is_official', False) # New field
            }

            # Calculate Paces
            pace, gap = calculate_paces(row)
            row["Pace"] = pace
            row["GAP"] = gap

            history_data.append(row)

    return pd.DataFrame(history_data)


@st.cache_data
def load_future_races():
    """Loads the spreadsheet of races being considered."""
    table_path = RAW_DIR / 'possible_races.xlsx'
    
    # Load and do some light cleaning
    df = pd.read_excel(table_path, sheet_name="races")
    
    # Ensure month numbers exist for proper sorting
    if 'Month, Number' in df.columns:
        df = df.sort_values('Month, Number')
        
    return df