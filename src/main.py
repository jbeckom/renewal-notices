from pathlib import Path
import pandas as pd

# --------------------------------------------------
# PATH SETUP
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
INCOMING_DIR = BASE_DIR / "data" / "incoming"

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

REQUIRED_COLUMNS = [
    "Customer #",
    "#ID",
    "Customer First name",
    "Customer Last Name",
    "Customer Company Name",
    "Location Address",
    "City",
    "State",
    "Zip Code",
    "SCA End Date",
    "Title",
    "Total Annual Fee",
]

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def detect_location(file_path: Path) -> str:
    """
    Determine which location the file belongs to base on file name.

    Returns:
        "AN", "MU", or "UNKNOWN"
    """

    filename = file_path.name.lower()

    if "an" in filename:
        return "AN"
    
    if "mu" in filename:
        return "MU"
    
    return "UNKNOWN"

def validate_columns(df: pd.DataFrame, file_name: str) -> bool:
    """
    Check that all required columns exist in the DataFrame.

    Args:
        df: Loaded pandas DataFrame
        file_name: Name of the file (for logging)

    Returns:
        True if valid, False if missing columns
    """

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    
    if missing:
        print(f"❌ Column validation FAILED for: {file_name}")
        print("    Missing columns:")
        for col in missing:
            print(f"    - {col}")
        print()
        return False
    
    print(f"✅ Column validation PASSED for: {file_name}\n")
    return True

# --------------------------------------------------
# MAIN PROCESS
# --------------------------------------------------

def main():
    csv_files = list(INCOMING_DIR.glob("*.csv"))

    if not csv_files:
        print(f"No CSV files found in: {INCOMING_DIR}")
        return
    
    print (f"found {len(csv_files)} CSV file(s).\n")

    for file_path in csv_files:
        print(f"Processing file: {file_path.name}")

        location = detect_location(file_path)
        print(f"  Detected location: {location}")

        # IMPORTANT: header=1 due to FieldPulse CSV output headers are on row 2
        try:
            df = pd.read_csv(file_path, header=1)
        except Exception as e:
            print(f"❌ Failed to read file: {file_path.name}")
            print(f"  Error: {e}\n")
            continue

        # Validate structure
        is_valid = validate_columns(df, file_path.name)

        if not is_valid:
            print(f"⛔️ Skipping file due to validation failure\n")
            continue

        print(f"✅ File is ready for next processing step\n")

# --------------------------------------------------

if __name__ == "__main__":
    main()