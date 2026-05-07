import pandas as pd
from config import INCOMING_DIR, CSV_HEADER_ROW
from utils import (
    detect_location,
    validate_columns,
    build_renewal_records,
)

# --------------------------------------------------
# MAIN PROCESS
# --------------------------------------------------

def main():
    csv_files = list(INCOMING_DIR.glob("*.csv"))

    if not csv_files:
        print(f"No CSV files found in: {INCOMING_DIR}")
        return
    
    print(f"Found {len(csv_files)} CSV file(s).\n")

    for file_path in csv_files:
        print(f"Processing file: {file_path.name}")

        location = detect_location(file_path)
        print(f"  Detected location: {location}")

        # IMPORTANT: header=1 due to FieldPulse CSV output headers are on row 2
        try:
            df = pd.read_csv(file_path, header=CSV_HEADER_ROW)
        except Exception as e:
            print(f"❌ Failed to read file: {file_path.name}")
            print(f"  Error: {e}\n")
            continue

        # Validate structure
        is_valid = validate_columns(df, file_path.name)

        if not is_valid:
            print(f"⛔️ Skipping file due to validation failure\n")
            continue

        records = build_renewal_records(df, location)

        print("✔ File is ready for next processing step")
        print(f"Rows in file: {len(df)}")
        print(f"Records created: {len(records)}")

        print("\nFirst sample record:")
        for key, value in records[0].items():
            print(f"  {key}: {value}")

        print("\nLast sample record:")
        for key, value in records[-1].items():
            print(f"  {key}: {value}")

        print()

# --------------------------------------------------

if __name__ == "__main__":
    main()