import pandas as pd


def calculate_paces(row):
    try:
        time_str = str(row['Time']).strip()
        if not time_str or time_str.lower() == 'none':
            return None, None

        # Split into Hours, Minutes, and Seconds (which may be a float)
        parts = time_str.split(':')
        if len(parts) != 3:
            return None, None
            
        h = int(parts[0])
        m = int(parts[1])
        s = float(parts[2]) # This handles '51.9' correctly
        
        total_minutes = (h * 60) + m + (s / 60)
        
        dist = float(row['Distance'])
        unit = str(row['Unit']).lower()
        
        if dist <= 0:
            return None, None

        # Standardize to Miles
        # 1 km = 0.621371 miles
        if 'km' in unit or 'kilometer' in unit:
            dist_miles = dist * 0.621371
        else:
            dist_miles = dist

        # 1. Actual Pace (min/mile)
        actual_pace_min = total_minutes / dist_miles
        
        # 2. Grade Adjusted Pace (GAP) in min/mile
        # Adjustment: ~1 mile of effort per 800ft of gain
        gain_ft = float(row['Elevation']) if row['Elevation'] else 0
        adjusted_dist_miles = dist_miles + (gain_ft / 800)
        gap_min = total_minutes / adjusted_dist_miles
        
        return actual_pace_min, gap_min
    except Exception:
        return None, None


def format_pace(minutes):
    if pd.isna(minutes):
        return "-"
    mins = int(minutes)
    secs = int((minutes - mins) * 60)
    return f"{mins}:{secs:02d}"
