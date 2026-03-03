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


def calculate_climb_density(elevation_ft, distance_miles):
    """Returns average feet of gain per mile."""
    if not distance_miles or distance_miles == 0:
        return 0
    return round(float(elevation_ft / distance_miles), 1)
 

def calculate_elevation_bounds(df_elev, climb_density):
    """
    Calculates dynamic y-min and y-max with an inverse buffer.
    Flatter races get larger buffers to prevent 'mountainous' visual distortion.
    """
    elev_min = df_elev["Elevation (ft)"].min()
    elev_max = df_elev["Elevation (ft)"].max()
    elev_range = elev_max - elev_min

    # DYNAMIC BUFFER LOGIC:
    # If density is 300+ ft/mi, buffer is 10% (0.1)
    # If density is 10 ft/mi, buffer scales up significantly
    # Formula: We want buffer to be large when density is low.
    if climb_density < 50:
        buffer_factor = 2.0  # 200% buffer for very flat races
    elif climb_density < 150:
        buffer_factor = 0.5  # 50% buffer for rolling hills
    else:
        buffer_factor = 0.1  # 10% buffer for technical/mountain races

    padding = max(elev_range * buffer_factor, 100) # Minimum 100ft window
    
    # CLAMP: Ensure y_min is at least 0
    y_min = max(0, elev_min - padding)
    y_max = elev_max + padding
    
    return y_min, y_max