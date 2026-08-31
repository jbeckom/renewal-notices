import argparse
import csv
import config as cfg
from datetime import datetime
from pathlib import Path
from pypdf import PdfWriter


VALID_NOTICE_WINDOWS = {"30_DAY", "60_DAY", "90_DAY"}


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for print batch processing.
    """

    parser = argparse.ArgumentParser(
        description="Create print batches from the renewal print queue."
    )

    parser.add_argument(
        "--location",
        choices=["an", "mu"],
        help="Only process print queue records for the specified location.",
    )

    parser.add_argument(
        "--notice-window",
        choices=sorted(VALID_NOTICE_WINDOWS),
        help="Only process records for the specified notice window.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of print queue records to process.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview print batch records without creating output files.",
    )

    return parser.parse_args()


def load_print_queue(queue_path: Path) -> list[dict]:
    """
    Load print queue records from CSV.
    """

    if not queue_path.exists():
        raise FileNotFoundError(f"Print queue not found: {queue_path}")
    
    with queue_path.open(mode="r", newline="", encoding="utf-8") as queue_file:
        return list(csv.DictReader(queue_file))
    

def filter_print_records(
        records: list[dict],
        location: str | None = None,
        notice_window: str | None = None,
) -> list[dict]:
    """
    Filter print queue records by optional location and notice window.
    """

    filtered_records = []

    for record in records:
        if location and record.get("location") != location:
            continue

        if notice_window and record.get("notice_window") != notice_window:
            continue

        filtered_records.append(record)

    return filtered_records


def validate_pdf_paths(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Split records into valid and invalid groups based on PDF path existence.
    """

    valid_records = []
    invalid_records = []

    for record in records:
        pdf_path = Path(record.get("pdf_path", ""))

        if pdf_path.exists() and pdf_path.is_file():
            valid_records.append(record)
        else:
            record["validation_error"] = f"PDF not found: {pdf_path}"
            invalid_records.append(record)

    return valid_records, invalid_records


def create_batch_directory() -> Path:
    """
    Create timestamped print batch output directory.
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_dir = cfg.PRINT_BATCHES_DIR / timestamp
    batch_dir.mkdir(parents=True, exist_ok=False)

    return batch_dir


def merge_pdfs(records: list[dict], output_path: Path) -> None:
    """
    Merge individual renewal PDFs into a single batch print PDF.
    """

    writer = PdfWriter()

    for record in records:
        writer.append(record["pdf_path"])

    with output_path.open(mode="wb") as output_file:
        writer.write(output_file)

    
def write_manifest(records: list[dict], manifest_path: Path) -> None:
    """
    Write print batch manifest CSV.
    """

    fieldnames = [
        "location",
        "notice_window",
        "delivery_action",
        "agreement_id",
        "account_number",
        "customer_name",
        "email",
        "original_pdf_path",
    ]

    with manifest_path.open(mode="w", newline="", encoding="utf-8") as manifest_file:
        writer = csv.DictWriter(manifest_file, fieldnames=fieldnames)
        writer.writeheader()

        for record in records:
            writer.writerow({
                "location": record.get("location"),
                "notice_window": record.get("notice_window"),
                "delivery_action": record.get("delivery_action"),
                "agreement_id": record.get("agreement_id"),
                "account_number": record.get("account_number"),
                "customer_name": record.get("customer_name"),
                "email": record.get("email"),
                "original_pdf_path": record.get("pdf_path"),
            })


def print_summary(
        total_records: int, 
        filtered_records: int, 
        valid_records: int, 
        invalid_records: int, 
        dry_run: bool, 
        batch_pdf_path: Path | None = None,
        manifest_path: Path | None = None,
) -> None:
    """
    Print processing summary.
    """

    print("\nPrint Batch Summary")
    print("---------------------")
    print(f"Print Queue Records Found: {total_records}")
    print(f"Records Selected: {filtered_records}")
    print(f"Valid PDFs: {valid_records}")
    print(f"Missing PDFs: {invalid_records}")

    if dry_run:
        print("Dry Run: No files created")
        return
    
    print(f"Batch PDF: {batch_pdf_path}")
    print(f"Manifest: {manifest_path}")


def main() -> None:
    """
    Process print queue records into a merged print batch.
    """

    args = parse_args()

    if args.limit is not None and args.limit <= 0:
        raise ValueError("--limit must be greater than zero.")
    
    records = load_print_queue(cfg.PRINT_QUEUE_LOG)

    filtered_records = filter_print_records(
        records=records,
        location=args.location,
        notice_window=args.notice_window
    )

    if args.limit is not None:
        filtered_records = filtered_records[:args.limit]

    valid_records, invalid_records = validate_pdf_paths(filtered_records)

    if args.dry_run:
        print_summary(
            total_records=len(records),
            filtered_records=len(filtered_records),
            valid_records=len(valid_records),
            invalid_records=len(invalid_records),
            dry_run=True
        )
        return
    
    if not valid_records:
        raise RuntimeError("No valid PDF records found for print batch.")
    
    batch_dir = create_batch_directory()

    batch_pdf_path = batch_dir / "batch_print.pdf"
    manifest_path = batch_dir / "print_manifest.csv"

    merge_pdfs(valid_records, batch_pdf_path)
    write_manifest(valid_records, manifest_path)

    print_summary(
        total_records=len(records),
        filtered_records=len(filtered_records),
        valid_records=len(valid_records),
        invalid_records=len(invalid_records),
        dry_run=False, 
        batch_pdf_path=batch_pdf_path,
        manifest_path=manifest_path
    )


if __name__ == "__main__":
    main()