# Race Log

Personal race records tracker and visualization app built with Streamlit.

## Stack

- **Python 3.11** with `uv` for package management
- **Streamlit** multi-page app
- **Plotly** and **Folium** for charts and maps
- **gpxpy** for GPX file parsing
- **Ruff** for linting and formatting

## Common Commands

```bash
make launch     # Run the Streamlit app (uv run streamlit run app.py)
make lint       # Ruff lint check
make format     # Ruff auto-format
make sync       # Sync dependencies and update lock file
make metadata   # Generate JSON skeletons for new race folders
make clean      # Remove build artifacts and caches
```

## Project Structure

```
app.py              # Home page entry point
pages/              # Streamlit multi-page app pages
  01_history.py     # Race history view
  02_potential.py   # Future race planning
src/
  data_loader.py    # Data loading with @st.cache_data
  plotting.py       # Plotly chart builders
  mapping.py        # Folium map builders
  pace.py           # Pace/elevation calculations
  ui_utils.py       # Shared UI helpers
  paths.py          # Path constants (PROJECT_ROOT, DATA_DIR, etc.)
data/
  results/          # Race result JSON files (one per race)
  raw/              # Raw inputs (possible_races.csv, etc.)
  processed/        # Processed data outputs
config/             # App config (map_style.json, regions.json)
scripts/            # Utility scripts (generate_metadata.py)
```

## Data Format

Race results live under `data/results/YYYY/` in per-race folders named:

```
MM_DD__race_name_in_snake_case__city_state
```

Each folder contains `metadata.json` plus supporting files. `activity.gpx` is always included (drives map visualization). For results, prefer whatever native format the race director provides (CSV, TXT, PDF). Fall back to saving the results page as HTML or a screenshot only when no structured file is available.

The `metadata.json` schema has five top-level keys:

```
race_metadata   name, date, distance, type, surface, course_style, city/state, GPS coords
results         official_time, elevation_gain/loss, status, is_official, is_sanctioned, notes
weather         temp, feels_like, humidity, wind_speed, wind_direction, condition
rankings        overall_rank, overall_total, group_name, group_rank, group_total
sources         original_url, athlinks_url, strava_url (string or array), local_files
```

- Future/possible races are in `data/raw/possible_races.csv`
- Environment variable `THUNDERFOREST_API_KEY` is required for map tiles (stored in `.env`)

## Development Notes

- Always use `uv run` to execute Python scripts and tools
- Line length is 88 characters (Ruff + Black compatible)
- Streamlit caching (`@st.cache_data`) is used on all data-loading functions
