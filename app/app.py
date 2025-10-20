###############################################################################
# SETUP #

import folium
import folium.plugins as plugins
import json
import os
import pandas as pd
import pathlib as pl
import streamlit as st
import streamlit_folium as stf

# PROJECT_ROOT = find_project_root()
PROJECT_ROOT = "/Users/evancanfield/Documents/Projects/possible_races"

st.set_page_config(
    page_title = "Possible Races",
    layout = "wide"
    )

###############################################################################
# LOAD #
# Load data
@st.cache_data
def load_data():
    # Stamp ---------------------------------------------------------
    table_path = pl.Path(
        PROJECT_ROOT,
        'data',
        'raw',
        'possible_races.xlsx'
    )
    df = pd.read_excel(
        table_path, 
        sheet_name = "races" 
        )

    return df

df = load_data()

# Load config for region colors
with open(os.path.join(PROJECT_ROOT, "config", "colors.json"), "r") as f:
    colors = json.load(f)

###############################################################################
# APP #
st.markdown(
    """
    # Possible Races
    """
)

# Sidebar filters
st.sidebar.header("Filter Stamps")
states = sorted(df["State Name"].dropna().unique())

# Get unique month names sorted in calendar order
df_unique_months = df[['Month', 'Month, Number']].drop_duplicates().sort_values('Month, Number')

# Extract the ordered list of unique month names
months = df_unique_months['Month'].tolist()

states_filter = st.sidebar.multiselect("Select State", states, default=states)
month_filter = st.sidebar.multiselect("Select Month", months, default=months)

# Apply filters
df_filtered = df[
    (df["State Name"].isin(states_filter)) &
    (df["Month"].isin(month_filter))
]

# Tabs
tab1, tab2 = st.tabs(["Map View", "Table View"])

with tab1:
    st.header("Race Locations")
    
    # Create map
    if df_filtered.empty:
        location = [39.8283, -98.5795]
    else:
        location = [
            df_filtered["Latitude"].mean(), 
            df_filtered["Longitude"].mean()
        ]

    m = folium.Map(
        location = location, 
        zoom_start = 5
        )

    if not df_filtered.empty:
    
        for _, row in df_filtered.iterrows():
            # color = region_colors.get(row["region"], "blue")
            msg_tootip = f"""
                    <b>Race:</b> {row['Name']}<br>
                    <b>Location:</b> {row['Town']}, {row['State Name']}<br>
                    <b>Distance:</b> {row['Distance']}<br>
                    <b>Month:</b> {row['Month']}<br>
                """
            msg_popup = msg_tootip + f"""
                    <b>Link:</b> <a href="{row['Link']}" target="_blank">{row['Link']}</a>
                """

            folium.Marker(
                location = [row["Latitude"], row["Longitude"]],
                popup = msg_popup,
                tooltip = msg_tootip,
                icon = plugins.BeautifyIcon(
                    icon_shape = "marker", 
                )
            ).add_to(m)
    else:
        st.warning("No data available for the selected filters, displaying an empty map.")

    
    plugins.Fullscreen(position="topleft").add_to(m)
    stf.st_folium(
        m,
        height = 750,
        width = 1000,
        returned_objects = []
    )


with tab2:
    st.header("Stamp Details Table")
    # Sort Dataframe
    sorted_df = df_filtered.sort_values(by=["State Name", "Month, Number"])


    st.dataframe(sorted_df, use_container_width=True, )
    
    # Allow sorting and filtering
    # edited_df = st.data_editor(sorted_df, num_rows="dynamic")
