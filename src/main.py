from pathlib import Path
from datetime import date 
import pandas as pd
from dateutil.relativedelta import relativedelta

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

def clean_id(value) -> str:
    """
    Remove the leading # symbol from ID fields and return clean text.
    """

    return str(value).replace("#","").strip()

def format_currency(value) -> str:
    """
    Convert a raw currency value into a standard dollar format.
    """

    try:
        cleaned = str(value).replace("$","").replace(",","").strip()
        return f"${float(cleaned):,.2f}"
    except Exception:
        return "$0.00"
    
def format_date(value) -> str:
    """
    Convert a raw date value into M/D/YYYY format.
    """

    parsed_date = pd.to_datetime(value).date()
    return parsed_date.strftime("%-m/%-d/%Y")

def build_customer_name(row: pd.Series) -> str:
    """
    Build the display name for the customer.

    Rule:
    - If a company name exists:
        Company Name
        Attn: First Last
    - Otherwise:
        First Last
    """

    company = clean_text(row.get("Customer Company Name", ""))
    first = clean_text(row.get("Customer First name", ""))
    last = clean_text(row.get("Customer Last Name", "")).strip()

    full_name = f"{first} {last}".strip()

    # Handle NaN values (pands can treat empty cells as 'nan')
    if company and company.lower() != "nan":
        if full_name:
            return f"{company}\nAttn: {full_name}"
        return company
    
    return full_name

def build_service_address(row: pd.Series) -> str:
    """
    Build a multi-line service address.

    The Location Address field from export inclues the full address:
        Street, City, State ZIP

    Since City, State, and Zip Code are also provided as separate fields, 
    we use those separate fields as the source of truth and only extract 
    the street address from Location Address.
    """

    full_location_address = clean_text(row.get("Location Address"))
    city = clean_text(row.get("City"))
    state = clean_text(row.get("State"))
    zip_code = clean_text(row.get("Zip Code"))

    # Location Address appears to be comma-separated:
    # "3301 West University Avenue, Muncie, Indiana 47304"
    # The first segment is the street address.
    street_address = full_location_address.split(",")[0].strip()

    return f"{street_address}\n{city}, {state} {zip_code}"

def build_renewal_record(row: pd.Series, location: str) -> dict:
    """
    Convert one CSV row into one clean renewal notice record.

    This clean record is what future steps will use for:
    - PDF generation
    - email generation
    - logging
    - API enrichment
    """

    expiration_date = pd.to_datetime(row["SCA End Date"]).date()
    coverage_through = expiration_date + relativedelta(years=1)

    return {
        "location":location,
        "run_date":date.today().strftime("%-m/%-d/%Y"),
        "account_number":clean_id(row["Customer #"]),
        "agreement_id":clean_id(row["#ID"]),
        "customer_name":build_customer_name(row),
        "service_address":build_service_address(row),
        "billing_address":None,
        "agreement_type":str(row["Title"]).strip(),
        "expiration_date":expiration_date.strftime("%-m/%-d/%Y"),
        "coverage_through":coverage_through.strftime("%-m/%-d/%Y"),
        "payment_due_date":expiration_date.strftime("%-m/%-d/%Y"),
        "total_price":format_currency(row["Total Annual Fee"]),
    }

def build_renewal_records(df: pd.DataFrame, location: str) -> list[dict]:
    """
    Convert all rows in a validated CSV into clean renewal records.

    Args:
        df: Validated renewal export DataFrame
        location: Location code detected from file name

    Returns:
        A list of clean renewal record dictionaries
    """

    records = []

    for _, row in df.iterrows():
        record = build_renewal_record(row, location)
        records.append(record)

    return records

def clean_text(value) -> str:
    """
    Normalize text fields by removing placeholder values.

    Treats the following as empty:
    - None
    - NaN
    - "-"
    - empty strings
    """

    text = str(value).strip()

    if text.lower() in ("nan","","-"):
        return ""
    
    return text

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