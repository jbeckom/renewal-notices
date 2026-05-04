from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INCOMING_DIR = BASE_DIR / "data" / "incoming"

def detect_location(file_path: Path) -> str:
    """
    Detect location based on the CSV filename.

    Expected file names include
    - an for Anderson
    -mu for Muncie
    """

    filename = file_path.name.lower()

    if "an" in filename:
        return "AN"
    
    if "mu" in filename:
        return "MU"
    
    return "UNKNOWN"

def main():
    csv_files = list(INCOMING_DIR.glob("*.csv"))

    if not csv_files:
        print(f"No CSV files found in: {INCOMING_DIR}")
        return
    
    print (f"found {len(csv_files)} CSV file(s).\n")

    for file_path in csv_files:
        location = detect_location(file_path)

        print("File found:")
        print(f" Name: {file_path.name}")
        print(f" Location: {location}")
        print(f" Full path: {file_path}")
        print()


if __name__ == "__main__":
    main()