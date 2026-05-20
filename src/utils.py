import re
import pandas as pd
from pathlib import Path
from datetime import date 
from dateutil.relativedelta import relativedelta
from config import REQUIRED_RECORD_FIELDS

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
    Determine which location the file belongs to based on file name.

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

    if company:
        if full_name:
            return f"{company}\nAttn: {full_name}"
        return company
    
    return full_name

def build_service_address(row: pd.Series) -> str:
    """
    Build a multi-line service address.

    The Location Address field from export includes the full address:
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
        "location": location,
        "run_date": date.today().strftime("%-m/%-d/%Y"),
        "account_number": clean_id(row["Customer #"]),
        "agreement_id": clean_id(row["#ID"]),
        "customer_name": build_customer_name(row),
        "service_address": build_service_address(row),
        "billing_address": None,
        "agreement_type": clean_text(row["Title"]),
        "expiration_date": format_date(row["SCA End Date"]),
        "coverage_through": coverage_through.strftime("%-m/%-d/%Y"),
        "payment_due_date": expiration_date.strftime("%-m/%-d/%Y"),
        "total_price": format_currency(row["Total Annual Fee"]),
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

def build_pdf_filename(record: dict) -> str:
    """
    Build a standardized PDF filename.

    Format:
        {yymm}-renewal-{agreement_id}-{customer_name}.pdf
    """

    exp_date = record['expiration_date']
    agreement_id = record['agreement_id']
    location = record['location'].lower()
    
    #  Use only the first line fo customer_name
    customer_name = record['customer_name'].split("\n")[0].lower()

    # Replace non-alphanumeric characters with hyphens
    customer_slug = re.sub(r"[^a-z0-9]+", "-", customer_name)

    # Remove leading/trailing hyphens
    customer_slug = customer_slug.strip("-")

    yymm = pd.to_datetime(exp_date).strftime("%y%m")

    return (
        f"{yymm}-renewal-"
        f"{location}-"
        f"{agreement_id}-"
        f"{customer_slug}.pdf"
    )

def build_output_directory(base_output_dir: Path, record: dict) -> Path:
    """
    Build the output directory structure for renewal PDFs.

    Structure:
        output/{yymm}/{location}
    """

    expiration_date = pd.to_datetime(record['expiration_date'])
    yymm = expiration_date.strftime("%y%m")

    location = record['location'].lower()

    output_dir = (
        base_output_dir /
        yymm / 
        location
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    return output_dir


def validate_record(record: dict) -> list[str]:
    """
    Validate one renewal record before PDF generation.

    Returns a list of validation error messages.
    Empty list means the record is valid.
    """

    errors = []

    for field in REQUIRED_RECORD_FIELDS:
        if not record.get(field):
            errors.append(f"Missing required field: {field}")

    return errors