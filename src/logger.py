import csv
from datetime import datetime
from pathlib import Path


RUN_SUMMARY_COLUMNS = [
    "run_timestamp",
    "file_name",
    "location",
    "rows_in_file",
    "records_created",
    "pdfs_created",
    "billing_overrides_found",
    "api_enrichment_failures",
    "pdf_generation_failures",
    "status",
]

PDF_DETAIL_COLUMNS = [
    "run_timestamp",
    "source_file",
    "location",
    "agreement_id",
    "account_number",
    "customer_name",
    "pdf_path",
    "status",
]

EXCEPTION_LOG_COLUMNS = [
    "run_timestamp",
    "source_file",
    "location",
    "stage",
    "agreement_id",
    "account_number",
    "customer_name",
    "error_message",
]


def write_run_summary(
        log_path: Path,
        file_name: str,
        location: str,
        rows_in_file: int,
        records_created: int,
        pdfs_created: int,
        billing_overrides_found: int,
        api_enrichment_failures: int,
        pdf_generation_failures: int,
        status: str,
) -> None:
    """
    Append one row to the run summary CSV log.

    If the log file does not exist yet, the header row is created first.
    """

    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = log_path.exists()

    with log_path.open(mode="a", newline="", encoding="utf-8") as log_file:
        writer = csv.DictWriter(log_file, fieldnames=RUN_SUMMARY_COLUMNS)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "run_timestamp": datetime.now().isoformat(timespec="seconds"),
            "file_name": file_name,
            "location": location,
            "rows_in_file": rows_in_file,
            "records_created": records_created,
            "pdfs_created": pdfs_created,
            "billing_overrides_found": billing_overrides_found,
            "api_enrichment_failures": api_enrichment_failures,
            "pdf_generation_failures": pdf_generation_failures,
            "status": status,
        })


def write_pdf_detail(
        log_path: Path,
        source_file: str,
        record: dict,
        pdf_path: Path,
        status: str,
) -> None:
    """
    Append one row to the PDF detail CSV log.

    This creates a record-level audit trail showing which renewal records generated which PDF files.
    """

    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = log_path.exists()

    with log_path.open(mode="a", newline="", encoding="utf-8") as log_file:
        writer = csv.DictWriter(log_file, fieldnames=PDF_DETAIL_COLUMNS)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "run_timestamp": datetime.now().isoformat(timespec="seconds"),
            "source_file": source_file,
            "location": record["location"],
            "agreement_id": record["agreement_id"],
            "account_number": record["account_number"],
            "customer_name": record["customer_name"].replace("\n", " | "),
            "pdf_path":str(pdf_path),
            "status": status,
        })


def write_exception_log(
        log_path: Path,
        source_file: str,
        location: str,
        stage: str,
        record: dict,
        error_message: str,
) -> None:
    """
    Append one row to the exception log.
    """

    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = log_path.exists()

    with log_path.open(mode="a", newline="", encoding="utf-8") as log_file:
        writer = csv.DictWriter(log_file, fieldnames=EXCEPTION_LOG_COLUMNS)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "run_timestamp": datetime.now().isoformat(timespec="seconds"),
            "source_file": source_file,
            "location": location,
            "stage": stage,
            "agreement_id": record.get("agreement_id"),
            "account_number": record.get("account_number"),
            "customer_name": record.get("customer_name"),
            "error_message": error_message,
        })