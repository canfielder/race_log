# Use bash for shell commands
SHELL := /bin/bash

# Default target
.DEFAULT_GOAL := launch

# --- App Commands ---

# Launch the Streamlit app from the root
launch:
	@echo "🚀 Launching Race Engine..."
	uv run streamlit run app.py

# Generate metadata skeletons for any new race folders
metadata:
	@echo "📂 Generating metadata skeletons..."
	uv run python scripts/generate_metadata.py

# --- Dev Tools ---

# Lint the code with Ruff
lint:
	@echo "🔍 Running Ruff lint..."
	uv run ruff check src pages app.py

# Autoformat with Ruff (Ruff handles formatting now, replacing Black)
format:
	@echo "🎨 Formatting code..."
	uv run ruff format src pages app.py

# --- Dependency Management ---

# Sync dependencies and update lock
sync:
	@echo "🔄 Syncing dependencies..."
	uv sync --all-extras
	uv lock

lock:
	@echo "🔒 Updating lock file..."
	uv lock

# --- Cleanup ---

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf dist build *.egg-info __pycache__ .pytest_cache .ruff_cache
	find . -name "*.pyc" -delete

# --- Requirements ---
requirements:
	@echo "📦 Generating requirements.txt from pyproject.toml..."
	@uv pip compile pyproject.toml -o requirements.txt
	@echo "✅ Success! requirements.txt has been updated."

# Help menu
help:
	@echo "Available commands:"
	@echo "  make launch   - Start the Streamlit app"
	@echo "  make metadata - Generate JSON skeletons for new race folders"
	@echo "  make sync     - Update dependencies and lock file"
	@echo "  make format   - Run auto-formatter"
	@echo "  make lint     - Run linter check"
	@echo "  make clean    - Remove cache and build files"