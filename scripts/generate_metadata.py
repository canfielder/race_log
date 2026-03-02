import os
import json
from pathlib import Path

def generate_clean_metadata(root_dir="data/results"):
    results_path = Path(root_dir)
    created_count = 0
    
    for year_dir in sorted(results_path.iterdir()):
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
            
        for race_dir in sorted(year_dir.iterdir()):
            if not race_dir.is_dir():
                continue
                
            metadata_file = race_dir / "metadata.json"
            if metadata_file.exists():
                continue

            parts = race_dir.name.split("__")
            race_date = f"{year_dir.name}-{parts[0].replace('_', '-')}" if len(parts) > 0 else ""
            race_name = parts[1].replace("_", " ").title() if len(parts) > 1 else "Unknown Race"
            
            location_part = parts[2] if len(parts) > 2 else ""
            state = location_part.split("_")[-1].upper() if "_" in location_part else ""
            city = location_part.rsplit("_", 1)[0].replace("_", " ").title() if "_" in location_part else location_part.title()

            skeleton = {
                "race_metadata": {
                    "name": race_name,
                    "date": race_date,
                    "distance_value": None,
                    "distance_unit": "kilometers", # Use "miles" or "kilometers"
                    "type": "Road", # Road, Trail, Relay, XC, Track, Gravel
                    "surface": "Asphalt", # See SURFACE_GUIDE.md
                    "course_style": "Loop", # Loop, Out and Back, Point to Point, Multi-loop
                    "start_city": city,
                    "start_state": state,
                    "end_state": state,
                    "personal_states_covered": [state],
                    "location_gps": [0.0, 0.0]
                },
                "results": {
                    "official_time": "00:00:00",
                    "elevation_gain": None,
                    "elevation_loss": None,
                    "elevation_unit": "feet",
                    "status": "Finished",
                    "is_official": True,
                    "is_sanctioned": True, 
                    "team_name": "", 
                    "personal_legs": [], # List of {"leg": 1, "dist": 5.0, "time": "00:40:00", "gpx": "leg_1.gpx"}
                    "notes": ""
                },
                "weather": {
                    "temp": None,
                    "feels_like": None,
                    "humidity": None,
                    "wind_speed": None,
                    "wind_direction": "",
                    "condition": "" 
                },
                "rankings": {
                    "overall_rank": None,
                    "overall_total": None,
                    "group_name": "",
                    "group_rank": None,
                    "group_total": None
                },
                "sources": {
                    "original_url": "",
                    "athlinks_id": "",
                    "local_files": [f.name for f in race_dir.iterdir() if f.is_file() and f.name != "metadata.json"]
                }
            }

            with open(metadata_file, "w") as f:
                json.dump(skeleton, f, indent=4)
                created_count += 1

    print(f"Final Architecture Deployed: {created_count} skeletons created.")

if __name__ == "__main__":
    generate_clean_metadata()
