# App Improvement Plan

Drafted April 2026 after a top-to-bottom architecture review.

---

## What's Working — Don't Touch

- **Folder-per-race with JSON + GPX** is the right data model. Human-readable, git-friendly, and the GPX files drive the best feature in the app.
- **Lazy GPX loading** (only parsed on marker click, then cached) is correct UX. Full-scan on startup would be slow as the dataset grows.
- **Pace + GAP calculation** is a genuinely useful derived metric, well-implemented in `src/pace.py`.
- **State highlight overlay + completion tracking** is a nice personal touch and works cleanly.

---

## Priority 1 — Analytics Page (new page)

**The biggest gap between what the data supports and what the app shows.**

All of this data already exists in the JSON files. The app is currently a viewer; this page makes it an analyzer.

### Charts / features to include

- **PR table by distance** — best time, date, course, and age group percentile for each canonical distance (5K, 10K, 10M, half, marathon, etc.)
- **Pace trend over time by distance bucket** — are you getting faster at trails? Road? Plot pace over time per distance type.
- **Age group percentile over time** — you have `overall_rank` and `overall_total` on every race. That normalizes across events and is a true apples-to-apples competitive metric. `1 - (rank / total)` = percentile.
- **Year-over-year volume** — races per year, total miles, total elevation gain. Bar or line chart by year.
- **Weather correlation** — temp + humidity on every race entry. Scatter plot of pace vs. temp (or humidity) to see if heat actually affects performance.
- **Elevation-adjusted performance** — GAP is already calculated but only shown in a table column. It could anchor a dedicated chart showing "effort-normalized" pace trends.

---

## Priority 2 — Richer Home Page

The current `app.py` shows 3 metrics and a last-race blurb. This should be the most compelling screen — a summary of the career arc.

### Additions

- **PR table** (pull from the analytics page logic) — best time per canonical distance
- **Year-over-year summary** — a small sparkline or bar chart showing race count and total miles by year
- **Highlight callouts** — most competitive finish (highest age group percentile), biggest race (longest distance or most elevation), newest state, current streak

---

## Priority 3 — Pydantic Validation on the Data Model

`load_race_history()` in `src/data_loader.py` currently does: file scan → JSON parse → flatten → pace calc → type coercion → fill NaN. That's a lot for one function, and there's no enforcement layer on the JSON schema.

### What to add

- Define Pydantic models for `RaceMetadata`, `Results`, `Rankings`, `Weather`, `Sources`, and a top-level `RaceEntry` model.
- Validate on ingest in `load_race_history()`. Surface validation errors clearly (bad data entry silently corrupts the app today).
- Typed access downstream instead of string-keyed dict/DataFrame lookups.

This also makes the data entry workflow safer — JSON schema violations get caught immediately when the app loads rather than causing silent NaN issues in charts.

---

## Priority 4 — Split `01_history.py`

At 300 lines, the history page is doing at least 4 distinct jobs: sidebar filtering, map rendering, race preview panel, and full GPS view. The session state logic (`_race_navigation` workaround, manual center/zoom preservation) is a direct result of this coupling.

### Approach

Extract into focused helpers or sub-modules:
- `src/history_state.py` — session state management (navigation, preview selection, map viewport)
- `src/history_map.py` — map construction (markers, clusters, GPX overlays, state highlights)
- `pages/01_history.py` — thin orchestrator that calls these and renders the layout

This doesn't change any functionality; it just makes the session state logic traceable.

---

## Priority 5 — Evaluate Map Rendering (Folium → PyDeck or Plotly)

Folium renders to static HTML, which means the map can't react to Streamlit state without a full re-render. The current center/zoom preservation workarounds exist entirely because of this constraint.

### Options

- **PyDeck** (deck.gl Python bindings) — renders natively in Streamlit's component system, so pan/zoom is just state. More complex to style; GeoJSON overlays require more work.
- **Plotly `scatter_mapbox`** — simpler API, native Streamlit integration, but less control over cluster styling and custom markers.

**Trade-off:** Both eliminate the session state hacks but would require rebuilding the custom pin/cluster CSS and the state GeoJSON overlay. Not a quick win — worth doing only after the analytics page and data model work.

---

## Potential Future Ideas (Lower Priority)

- **Scouting page improvements** — tie `02_potential.py` more tightly to history data: flag distances you haven't run, show how candidate races compare to past races at similar distances
- **In-app data entry form** — a Streamlit form to create a new race entry instead of hand-editing JSON
- **Export / share** — generate a shareable race summary card (PNG or PDF) for a given race

---

## Implementation Order Summary

| Priority | Area | Effort |
|---|---|---|
| 1 | Analytics page | Medium — data exists, need charts |
| 2 | Richer home page | Small — mostly reuses analytics logic |
| 3 | Pydantic models | Medium — schema work + refactor loader |
| 4 | Split history page | Small — refactor only, no new features |
| 5 | Map rendering swap | Large — rebuild map layer |
