# Race Surface Reference Guide

Use this guide to ensure consistency in the `race_metadata.surface` field. Consistency allows the Streamlit app to accurately compare your "Road PR" vs. "Trail PR."

## 1. Hard Surfaces (Fastest)
* **Asphalt**: Standard road races, highways, and paved city streets.
* **Concrete**: Sidewalks or urban greenways. (Harder impact than asphalt).
* **Synthetic**: All-weather running tracks (Tartan/Polyurethane).

## 2. Packed & Groomed (Intermediate)
* **Gravel (Packed)**: Fine-crush stone, rail-trails, or well-maintained park paths (e.g., C&O Canal style).
* **Trail (Groomed)**: Wide, flat dirt paths or fire roads. No significant roots/rocks.
* **Grass**: Traditional Cross Country (XC) courses.

## 3. Technical & Natural (Slowest)
* **Trail (Technical)**: Single-track with roots, rocks, and "rolling" elevation. Requires focus on foot placement (e.g., Fort Clinch, USNWC trails).
* **Sand**: Beach races or deep sugar-sand sections.
* **Mud**: For "Obstacle" races or trail races that were exceptionally washed out.

---

## Decision Logic for Mixed Surfaces
If a race covers multiple surfaces, follow the **"70/30 Rule"**:

1.  **Dominant Surface**: If >70% of the race is on one surface, use that.
    * *Example (Fort Clinch)*: 6 miles of rooty trails + 0.2 miles of sand = **Trail (Technical)**.
2.  **The "Effort" Modifier**: If a surface is so difficult that it defines the race (even if it's less than 70%), use the more difficult surface.
    * *Example*: 3 miles of road + 2 miles of deep beach sand = **Sand**.
3.  **Notes**: Always use the `notes` field to document the mix (e.g., *"Rolling technical trail; brutal 0.5mi sand finish."*)