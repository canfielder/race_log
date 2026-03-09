import pathlib

def find_project_root(sentinel_files=None):
    """
    Search upwards from the current file to find the project root.
    Looks for sentinel files like pyproject.toml or .git.
    """
    if sentinel_files is None:
        sentinel_files = ["pyproject.toml", ".git", "app.py"]
    
    current_path = pathlib.Path(__file__).resolve()
    
    # Iterate through parents until we find a sentinel
    for parent in [current_path] + list(current_path.parents):
        if any((parent / sentinel).exists() for sentinel in sentinel_files):
            return parent
            
    # Fallback to current file's parent's parent (assuming it's in src/)
    return current_path.parent.parent

# Define global constants
# PROJECT_ROOT = find_project_root()
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent

CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
RAW_DIR = DATA_DIR / "raw"


def validate_data_dir():
    """Checks if the expected data subdirectories exist."""
    required_dirs = [DATA_DIR, RESULTS_DIR, RAW_DIR]
    for d in required_dirs:
        if not d.exists():
            raise FileNotFoundError(f"Missing required directory: {d}")
