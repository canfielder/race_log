import json
from pathlib import Path

def validate_metadata():
    results_dir = Path("results")
    broken_files = 0
    
    print(f"🔍 Scanning for JSON errors in: {results_dir.absolute()}\n")
    
    for json_path in results_dir.glob("**/*.json"):
        try:
            with open(json_path, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            broken_files += 1
            print(f"❌ BROKEN: {json_path}")
            print(f"   Line: {e.lineno}, Column: {e.colno}")
            print(f"   Reason: {e.msg}")
            
            # Read the file to show the problematic line
            with open(json_path, 'r') as f:
                lines = f.readlines()
                if e.lineno <= len(lines):
                    print(f"   Context: {lines[e.lineno-1].strip()}")
            print("-" * 40)
            
    if broken_files == 0:
        print("✅ All JSON files are valid!")
    else:
        print(f"\nFound {broken_files} broken file(s).")

if __name__ == "__main__":
    validate_metadata()
    