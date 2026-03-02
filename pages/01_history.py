import streamlit as st
import folium
from streamlit_folium import st_folium
import folium.plugins as plugins
from src.data_loader import load_race_history
from src.pace import format_pace

st.set_page_config(page_title="Race History", layout="wide")

# --- DATA LOADING ---
df = load_race_history() 
df['Year'] = df['Date'].dt.year

st.title("🏃 Race History")

# --- TOP FILTER SECTION ---
with st.container(border=True):
    st.write("### 📅 Select Year Range")
    min_year, max_year = int(df['Year'].min()), int(df['Year'].max())
    year_range = st.slider("Year Range", min_year, max_year, (min_year, max_year), label_visibility="collapsed")

# Filter dataframe
df_filtered = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]

# --- SIDEBAR: DETAILED METRICS ---
with st.sidebar:
    st.header("📊 History Insights")
    
    st.metric("Total Events", len(df_filtered))
    
    col1, col2 = st.columns(2)
    with col1:
        # Summing the boolean is_official column
        official_count = df_filtered['is_official'].sum()
        st.metric("Official", int(official_count))
    with col2:
        personal_count = len(df_filtered) - official_count
        st.metric("Personal", int(personal_count))
    
    st.divider()
    st.metric("Unique States", df_filtered['State'].nunique())
    
    st.divider()
    st.subheader("Races by State")
    st.write(df_filtered['State'].value_counts())

# --- MAIN CONTENT ---
tab_map, tab_table = st.tabs(["🗺️ Lifetime Map", "📄 Raw Data"])

with tab_map:
    if not df_filtered.empty:
        df_map = df_filtered.dropna(subset=['Lat', 'Lon'])
        map_center = [df_map["Lat"].mean(), df_map["Lon"].mean()]
        
        # Clean, modern map tiles
        m = folium.Map(location=map_center, zoom_start=6, tiles="CartoDB positron")

        for _, row in df_map.iterrows():
            # Color logic: Blue for official, Orange for personal
            # Both use the 'person-running' icon
            icon_color = 'cadetblue' if row['is_official'] else 'orange'
            
            tooltip = f"<b>{row['Name']}</b><br>{row['Date'].strftime('%Y-%m-%d')}<br>{row['Distance']} {row['Unit']}"
            
            folium.Marker(
                location=[row["Lat"], row["Lon"]],
                tooltip=tooltip,
                popup=tooltip,
                icon=folium.Icon(color=icon_color, icon='person-running', prefix='fa')
            ).add_to(m)

        plugins.Fullscreen().add_to(m)
        st_folium(m, width=1200, height=600, returned_objects=[])
    else:
        st.info("No races found for this year range.")

with tab_table:
    # Prepare formatted columns for display
    df_display = df_filtered.copy()
    df_display['Pace'] = df_display['Pace'].apply(format_pace)
    df_display['GAP'] = df_display['GAP'].apply(format_pace)

    st.dataframe(
            df_display.sort_values("Date", ascending=False), 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "is_official": st.column_config.CheckboxColumn("Official?"),
                "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "Time": st.column_config.TextColumn("Total Time"), # Explicitly shown
                "Pace": st.column_config.TextColumn("Pace (min/mi)"),
                "GAP": st.column_config.TextColumn("GAP (Adj)"),
                "Elevation": st.column_config.NumberColumn("Gain (ft)", format="%d"),
                "Distance": st.column_config.NumberColumn("Dist", format="%.1f"),
                "Lat": None, "Lon": None, "Year": None # Hidden columns
            }
        )