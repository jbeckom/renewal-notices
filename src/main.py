import argparse
from logger import write_run_summary
import config as cfg
from utils import (
    detect_location,
    validate_columns,
    build_renewal_records,
)
from workflow import (
    load_csv_file,
    enrich_records,
    generate_renewal_pdfs,
    print_file_summary,
    archive_processed_file,
)


# --------------------------------------------------
# LOCAL HELPERS
# --------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate renewal notice PDFs from FieldPulse CSV exports."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and enrich records without generating PDFs or archiving files.",
    )

    return parser.parse_args()
        

# --------------------------------------------------
# MAIN PROCESS
# --------------------------------------------------

def main():
    args = parse_args()
    csv_files = list(cfg.INCOMING_DIR.glob("*.csv"))

    if not csv_files:
        print(f"No CSV files found in: {cfg.INCOMING_DIR}")
        return
    
    print(f"Found {len(csv_files)} CSV file(s).\n")

    for file_path in csv_files:
        print(f"Processing file: {file_path.name}")

        location = detect_location(file_path)
        print(f"  Detected location: {location}")

        df = load_csv_file(file_path)

        if df is None:
            continue

        is_valid = validate_columns(df, file_path.name)

        if not is_valid:
            print(f"⛔️ Skipping file due to validation failure\n")
            continue

        records = build_renewal_records(df, location)

        records, billing_override_count, api_error_count = enrich_records(
            records,
            file_path,
            location,
        )

        print(f"✅ File is ready for next processing step")

        if args.dry_run:
            pdf_count = 0
            pdf_error_count = 0
            status = "DRY_RUN"

            print_file_summary(
                file_path=file_path,
                rows_in_file=len(df),
                records_created=len(records),
                billing_override_count=billing_override_count,
                api_error_count=api_error_count,
                pdf_count=pdf_count,
                pdf_error_count=pdf_error_count,
                status=status,
            )

            write_run_summary(
                log_path=cfg.RUN_SUMMARY_LOG,
                file_name=file_path.name,
                location=location,
                rows_in_file=len(df),
                records_created=len(records),
                pdfs_created=pdf_count,
                billing_overrides_found=billing_override_count,
                api_enrichment_failures=api_error_count,
                pdf_generation_failures=pdf_error_count,
                status=status,
            )

            continue

        pdf_count, pdf_error_count = generate_renewal_pdfs(
            records,
            file_path,
            location,
        )

        status = "SUCCESS"

        if api_error_count > 0 or pdf_error_count > 0:
            status = "COMPLETED_WITH_ERRORS"

        print_file_summary(
            file_path=file_path,
            rows_in_file=len(df),
            records_created=len(records),
            billing_override_count=billing_override_count,
            api_error_count=api_error_count,
            pdf_count=pdf_count,
            pdf_error_count=pdf_error_count,
            status=status,
        )

        write_run_summary(
            log_path=cfg.RUN_SUMMARY_LOG,
            file_name=file_path.name,
            location=location,
            rows_in_file=len(df),
            records_created=len(records),
            pdfs_created=pdf_count,
            billing_overrides_found=billing_override_count,
            api_enrichment_failures=api_error_count,
            pdf_generation_failures=pdf_error_count,
            status=status,
        )

        archive_processed_file(file_path)

        print()

# --------------------------------------------------

if __name__ == "__main__":
    main()