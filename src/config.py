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