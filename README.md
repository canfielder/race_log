# 🏃 Potential Races Visualization App

An interactive Streamlit app for exploring potential running races across the country by location and time of year. Visualize, filter, and plan your racing calendar with clean, interactive maps and data views.

---

## 📦 Project Structure

```
├── app/
│   └── app.py                # Main Streamlit application
├── config/
│   └── colors.json           # Color and theme configuration
├── data/
│   ├── raw/                  # Unprocessed source data (e.g., possible_races.xlsx)
│   └── processed/            # Cleaned or aggregated data
├── notebooks/                # Jupyter/analysis notebooks
├── src/
│   └── potential_races/      # Python package source
├── Makefile                  # Common developer commands
├── pyproject.toml            # Project metadata & dependencies
├── uv.lock                   # Resolved dependency versions
└── README.md
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/potential_races.git
cd potential_races
```

### 2. Create and activate the virtual environment
```bash
uv venv
source .venv/bin/activate
```

### 3. Install dependencies
Install all project and development dependencies:
```bash
uv sync --all-extras
```

---

## 🚀 Usage

### Launch the app
```bash
make launch
```
The Streamlit app will run at:
```
http://localhost:8501
```

### Lint and format code
```bash
make lint     # Run Ruff for linting
make format   # Format code using Black
```

### Sync or update dependencies
```bash
make sync
```

### Clean build artifacts
```bash
make clean
```

---

## 🧰 Developer Notes

- **Python version:** 3.11.4  
- **Package manager:** [uv](https://docs.astral.sh/uv)  
- **Linting:** [Ruff](https://docs.astral.sh/ruff)  
- **Formatting:** [Black](https://black.readthedocs.io/en/stable/)  
- **App framework:** [Streamlit](https://streamlit.io)  
- **Map visualization:** [Folium](https://python-visualization.github.io/folium/) and [streamlit-folium](https://pypi.org/project/streamlit-folium/)

---

## 🗺️ Data Overview

Raw data lives in `data/raw/`.  
Processed outputs are stored in `data/processed/`.  
Color and style mappings are configurable in `config/colors.json`.

---

## 🤝 Contributing

1. Create a new branch from `main`.  
2. Make changes and ensure linting passes:
   ```bash
   make lint && make format
   ```
3. Commit, push, and open a pull request.

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.