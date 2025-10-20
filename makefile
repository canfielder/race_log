# Use bash for shell commands
SHELL := /bin/bash

# Default target
.DEFAULT_GOAL := launch

# Launch the Streamlit app
launch:
	@echo "🚀 Launching Streamlit app..."
	uv run streamlit run app/app.py

# Lint the code with Ruff
lint:
	@echo "🔍 Running Ruff lint..."
	uv run ruff check src

# Autoformat with Black
format:
	@echo "🎨 Formatting code with Black..."
	uv run black src

# Rebuild the environment
sync:
	@echo "🔄 Syncing dependencies..."
	uv sync --all-extras

# Clean build artifacts
clean:
	@echo "🧹 Cleaning up..."
	rm -rf dist build *.egg-info __pycache__ .pytest_cache .ruff_cache
