import argparse
from logger import write_run_summary, write_exception_log
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

    parser.add_argument(
        "--file",
        type=str,
        help="Process only a specific CSV file from the incoming directory.",
    )

    parser.add_argument(
        "--location",
        choices=["an", "mu"],
        help="Process only CSV files for a specific location.",
    )

    return parser.parse_args()
        

# --------------------------------------------------
# MAIN PROCESS
# --------------------------------------------------

def main():
    # Parse command-line options such as --dry-run, --file, and --location.
    args = parse_args()

    # Prevent conflicting runtime modes.
    # A specific file and location filter should not be used together.
    if args.file and args.location:
        print("❌ Use either --file or --location, not both.")
        return
    
    # Build the list of CSV files to process.
    # If --file is provided, process only that file.
    # Otherwise, process all CSV files in the incoming directory,
    # optionally filtered by --location
    if args.file:
        target_file = cfg.INCOMING_DIR / args.file

        if not target_file.exists():
            print(f"❌ File not found: {target_file}")
            return
        
        csv_files = [target_file]

    else:
        csv_files = list(cfg.INCOMING_DIR.glob("*.csv"))

        if args.location:
            filtered_files = []

            for file_path in csv_files:
                location = detect_location(file_path)

                if location == "UNKNOWN":
                    continue

                if location.lower() == args.location:
                    filtered_files.append(file_path)

            csv_files = filtered_files

    # Stop if no matching CSV files were found.
    if not csv_files:
        print(f"No CSV files found in: {cfg.INCOMING_DIR}")
        return
    
    print(f"Found {len(csv_files)} CSV file(s).\n")

    # Process each selected CSV file independently.
    for file_path in csv_files:
        print(f"Processing file: {file_path.name}")

        # Determine Anderson/Muncie location from the file name.
        location = detect_location(file_path)
        print(f"  Detected location: {location}")

        if location == "UNKNOWN":
            write_exception_log(
                log_path=cfg.EXCEPTION_LOG,
                source_file=file_path.name,
                location=location,
                stage="LOCATION_DETECTION",
                record={},
                error_message="Unable to determine location from filename.",
            )

            print(f"⛔️ Skipping file due to unknown location: {file_path.name}\n")
            continue

        # Load the CSV into a DataFrame.
        # If the file cannot be read, skit it and continue
        df = load_csv_file(file_path)

        if df is None:
            continue

        # Confirm the CSV contains all required source columns.
        is_valid = validate_columns(df, file_path.name)

        if not is_valid:
            print(f"⛔️ Skipping file due to validation failure\n")
            continue

        # Convert CSV rows into clean internal renewal record dictionaries.
        records = build_renewal_records(df, location)

        # Enrich records using FieldPulse API billing address overrides.
        # API failures are logged per record and do not stop the batch.
        records, billing_override_count, api_error_count = enrich_records(
            records,
            file_path,
            location,
        )

        print(f"✅ File is ready for next processing step")

        # Dry run mode validates and enriches records but does not:
        # - generate PDFs
        # - archive source files
        if args.dry_run:
            pdf_count = 0
            pdf_error_count = 0
            email_ready_count = 0
            print_mail_count = 0
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
                email_ready_count=email_ready_count,
                print_mail_count=print_mail_count,
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
                email_ready_count=email_ready_count,
                print_mail_count=print_mail_count,
            )

            continue

        # Generate renewal PDFs and capture success/failure counts.
        pdf_count, pdf_error_count, email_ready_count, print_mail_count = generate_renewal_pdfs(
            records,
            file_path,
            location,
        )

        # Determine final processing status for this source file
        status = "SUCCESS"

        if api_error_count > 0 or pdf_error_count > 0:
            status = "COMPLETED_WITH_ERRORS"

        # Print a clean runtime summary to the terminal
        print_file_summary(
            file_path=file_path,
            rows_in_file=len(df),
            records_created=len(records),
            billing_override_count=billing_override_count,
            api_error_count=api_error_count,
            pdf_count=pdf_count,
            pdf_error_count=pdf_error_count,
            status=status,
            email_ready_count=email_ready_count,
            print_mail_count=print_mail_count
        )

        # Write the run-level summary log
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
            email_ready_count=email_ready_count,
            print_mail_count=print_mail_count,
        )

        # Move successfully processed source CSV out of the incoming folder
        # so it is not processed again during future runs.
        archive_processed_file(file_path)

        print()

# --------------------------------------------------

if __name__ == "__main__":
    main()