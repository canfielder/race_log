# 🏃 Race Log Visualization & Analysis

An interactive Streamlit application for tracking race history and scouting future events. Visualize your lifetime running map, analyze performance with Grade Adjusted Pace (GAP), and plan your upcoming racing calendar.

---

## 📦 Project Structure

```text
├── app.py                # Main Streamlit entry point
├── pages/                # Multi-page App (History, Scouting, etc.)
├── src/                  # Core logic & data processing
│   ├── data_loader.py    # Standardized Pace & GAP calculations
│   └── paths.py          # Centralized path management
├── config/               # Configuration (regions.json, colors.json)
├── data/
│   ├── raw/              # Source spreadsheets
│   └── results/          # JSON race data & metadata
├── scripts/              # Data maintenance scripts
├── Makefile              # Developer shortcuts (launch, sync, lint)
├── pyproject.toml        # Project metadata & dependencies
└── README.md
