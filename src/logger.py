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
    "status"
]


def write_run_summary(
        log_path: Path,
        file_name: str,
        location: str,
        rows_in_file: str,
        records_created: int,
        pdfs_created: int,
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
            "status": status,
        })