import pandas as pd
from api_client import enrich_record_with_mailing_address
from logger import write_run_summary, write_pdf_detail, write_exception_log
import config as cfg
from pdf_generator import (
    generate_renewal_notice_pdf,
)
from utils import (
    detect_location,
    validate_columns,
    build_renewal_records,
    build_pdf_filename,
    build_output_directory,
    validate_record,
)


# --------------------------------------------------
# LOCAL HELPERS
# --------------------------------------------------

def load_csv_file(file_path):
    """
    Load a FieldPulse renewal CSV file.
    Returns the DataFrame if successful, otherwise None.
    """

    try:
        # IMPORTANT: header=1 due to FieldPulse CSV output headers are on row 2
        return pd.read_csv(file_path, header=cfg.CSV_HEADER_ROW)
    
    except Exception as e:
        print(f"❌ Failed to read file: {file_path.name}")
        print(f"  Error: {e}\n")
        return None
    

def enrich_records(records, file_path, location):
    """
    Enrich renewal records with FieldPulse mailing address overrides.
    Returns enriched records, billing override count, and API error count.
    """

    enriched_records = []
    billing_override_count = 0
    api_error_count = 0

    for record in records:
        try:
            enriched_record = enrich_record_with_mailing_address(record)

            if enriched_record['mailing_address']:
                billing_override_count += 1

                print(
                    f"Billing override applied: "
                    f"{record['agreement_id']} | "
                    f"{record['customer_name']}"
                )

        except Exception as e:
            api_error_count += 1

            write_exception_log(
                log_path=cfg.EXCEPTION_LOG,
                source_file=file_path.name,
                location=location,
                stage="API_ENRICHMENT",
                record=record,
                error_message=str(e)
            )

            print(
                f"⚠️ API enrichment failed for "
                f"Agreement {record['agreement_id']} | "
                f"Account {record['account_number']}: {e}"
            )

            record['mailing_address'] = None
            enriched_record = record

        enriched_records.append(enriched_record)

    return enriched_records, billing_override_count, api_error_count


def generate_renewal_pdfs(records, file_path, location):
    """
    Generate renewal notice PDFs for validated records.
    Returns PDF success count and PDF error count.
    """

    pdf_count = 0
    pdf_error_count = 0

    for record in records:
        output_dir = build_output_directory(
            cfg.OUTPUT_DIR,
            record
        )

        renewal_pdf_path = (
            output_dir / 
            build_pdf_filename(record)
        )

        record_errors = validate_record(record)

        if record_errors:
            pdf_error_count += 1

            write_exception_log(
                log_path=cfg.EXCEPTION_LOG,
                source_file=file_path.name,
                location=location,
                stage="RECORD_VALIDATION",
                record=record,
                error_message="; ".join(record_errors),
            )

            write_pdf_detail(
                log_path=cfg.PDF_DETAIL_LOG,
                source_file=file_path.name,
                record=record,
                pdf_path=renewal_pdf_path,
                status="FAILED",
            )

            print(
                f"⚠️ Record validation failed for: "
                f"Agreement {record['agreement_id']} | "
                f"Account {record['account_number']}: "
                f"{'; '.join(record_errors)}",
            )

            continue

        try:
            generate_renewal_notice_pdf(
                record,
                renewal_pdf_path,
                cfg.COMPANY_INFO[location],
                cfg.LOGO_PATH,
            )

            write_pdf_detail(
                log_path=cfg.PDF_DETAIL_LOG,
                source_file=file_path.name,
                record=record,
                pdf_path=renewal_pdf_path,
                status="CREATED",
            )

            pdf_count += 1 

        except Exception as e:
            pdf_error_count += 1

            write_exception_log(
                log_path=cfg.EXCEPTION_LOG,
                source_file=file_path.name,
                location=location,
                stage="PDF_GENERATION",
                record=record,
                error_message=str(e),
            )

            write_pdf_detail(
                log_path=cfg.PDF_DETAIL_LOG,
                source_file=file_path.name,
                record=record,
                pdf_path=renewal_pdf_path,
                status="FAILED",
            )

            print(
                f"⚠️ PDF generation failed for "
                f"Agreement {record['agreement_id']} | "
                f"Account {record['account_number']}: {e}"
            )

    return pdf_count, pdf_error_count


def print_file_summary(
        file_path,
        rows_in_file,
        records_created,
        billing_override_count,
        api_error_count,
        pdf_count,
        pdf_error_count,
        status,
):
    """
    Print a clean runtime summary for one processed file.
    """
 
    print()
    print("-" * 50)
    print(f"File complete: {file_path.name}")
    print(f"Rows in file: {rows_in_file}")
    print(f"Records created: {records_created}")
    print(f"Billing overrides found: {billing_override_count}")
    print(f"API enrichment failures: {api_error_count}")
    print(f"Renewal PDFs created: {pdf_count}")
    print(f"PDF generation failures: {pdf_error_count}")
    print(f"Status: {status}")
    print("-" * 50)


def archive_processed_file(file_path):
    """
    Move a processed CSV file out of the incoming folder.

    This prevents the same source file from being processed again
    on the next run.
    """

    cfg.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    destination = cfg.PROCESSED_DIR / file_path.name

    if destination.exists():
        timestamp = pd.Timestamp.now().strftime("%Y%m%d-%H%M%S")
        destination = cfg.PROCESSED_DIR / f"{file_path.stem}-{timestamp}{file_path.suffix}"

    file_path.rename(destination)

    print(f"Archived source file: {destination}")
        


# --------------------------------------------------
# MAIN PROCESS
# --------------------------------------------------

def main():
    csv_files = list(cfg.INCOMING_DIR.glob("*.csv"))
    run_summary_log = cfg.RUN_SUMMARY_LOG
    pdf_detail_log = cfg.PDF_DETAIL_LOG

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

        print(f"✔️ File is ready for next processing step")

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