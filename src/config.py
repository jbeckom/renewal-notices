from pathlib import Path

# --------------------------------------------------
# PATH SETUP
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

INCOMING_DIR = BASE_DIR / "data" / "incoming"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
TEMPLATES_DIR = BASE_DIR / "templates"

CSV_HEADER_ROW = 1

LOCATION_NAMES = {
    "AN": "Anderson",
    "MU": "Muncie",
}

COMPANY_INFO = {
    "AN": {
        "name": "Summers Plumbing Heating & Cooling",
        "address": "3423 Columbus Ave, Anderson, IN 46013",
        "phone": "765.644.4328",
        "website": "www.summersphc.com"
    },
    "MU": {
        "name": "Summers Plumbing Heating & Cooling",
        "address": "3700 S Hoyt Ave, Muncie, IN 47302",
        "phone": "765.399.4328",
        "website": "www.summersphc.com"
    }
}