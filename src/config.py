from pathlib import Path

# --------------------------------------------------
# PATH SETUP
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

INCOMING_DIR = BASE_DIR / "data" / "incoming"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
TEMPLATES_DIR = BASE_DIR / "templates"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
LOGO_PATH = TEMPLATES_DIR / "SPHC-Logo-BlkText.jpg"


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
        "website": "www.summersphc.com",
        "location_url": "anderson"
    },
    "MU": {
        "name": "Summers Plumbing Heating & Cooling",
        "address": "3700 S Hoyt Ave, Muncie, IN 47302",
        "phone": "765.399.4328",
        "website": "www.summersphc.com",
        "location_url": "muncie"
    }
}


# --------------------------------------------------
# COMPANY / PAYMENT CONFIG
# --------------------------------------------------

PAYABLE_TO = "Summers of Anderson, Inc."

REMITTANCE_SEPARATOR_TEXT = (
    "Please detach and return this section with your payment."
)


# --------------------------------------------------
# LOG FILES
# --------------------------------------------------

RUN_SUMMARY_LOG = LOGS_DIR / "run_summary.csv"
PDF_DETAIL_LOG = LOGS_DIR / "pdf_detail.csv"
EXCEPTION_LOG = LOGS_DIR / "exception_log.csv"
EMAIL_QUEUE_LOG = LOGS_DIR / "email_queue.csv"
PRINT_QUEUE_LOG = LOGS_DIR / "print_queue.csv"


# --------------------------------------------------
# PDF SETTINGS
# --------------------------------------------------

PDF_FONT = "Helvetica"
PDF_FONT_BOLD = "Helvetica-Bold"
PDF_FONT_ITALIC = "Helvetica-Oblique"


# --------------------------------------------------
# RECORD VALIDATION
# --------------------------------------------------

REQUIRED_RECORD_FIELDS = [
    "agreement_id",
    "account_number",
    "customer_name",
    "service_address",
    "payment_due_date",
    "total_price",
]


# --------------------------------------------------
# EMAIL CONFIGS
# --------------------------------------------------

EMAIL_SUBJECT = (
    "Action Required: Your Safety & Comfort Membership Renewal is enclosed"
)

EMAIL_DRAFT_LOG = LOGS_DIR / "email_draft_log.csv"
RENEWAL_EMAIL_TEMPLATE = TEMPLATES_DIR / "renewal_email.html"