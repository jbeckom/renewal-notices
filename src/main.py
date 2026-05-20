import pandas as pd
from api_client import enrich_record_with_mailing_address
from logger import write_run_summary, write_pdf_detail, write_exception_log
from config import INCOMING_DIR, CSV_HEADER_ROW, OUTPUT_DIR, COMPANY_INFO, LOGS_DIR, LOGO_PATH
from pdf_generator import (
    generate_renewal_notice_pdf,
)
from utils import (
    detect_location,
    validate_columns,
    build_renewal_records,
    build_pdf_filename,
    build_output_directory,
)


exception_log = LOGS_DIR / "exception_log.csv"

# --------------------------------------------------
# MAIN PROCESS
# --------------------------------------------------

def main():
    csv_files = list(INCOMING_DIR.glob("*.csv"))
    run_summary_log = LOGS_DIR / "run_summary.csv"
    pdf_detail_log = LOGS_DIR / "pdf_detail.csv"

    if not csv_files:
        print(f"No CSV files found in: {INCOMING_DIR}")
        return
    
    print(f"Found {len(csv_files)} CSV file(s).\n")

    for file_path in csv_files:
        print(f"Processing file: {file_path.name}")

        location = detect_location(file_path)
        print(f"  Detected location: {location}")

        # IMPORTANT: header=1 due to FieldPulse CSV output headers are on row 2
        try:
            df = pd.read_csv(file_path, header=CSV_HEADER_ROW)
        except Exception as e:
            print(f"❌ Failed to read file: {file_path.name}")
            print(f"  Error: {e}\n")
            continue

        # Validate structure
        is_valid = validate_columns(df, file_path.name)

        if not is_valid:
            print(f"⛔️ Skipping file due to validation failure\n")
            continue

        records = build_renewal_records(df, location)

        enriched_records = []

        billing_override_count = 0

        api_error_count = 0

        for record in records:
            try:
                if record['account_number'] == "14174319":
                    record['account_number'] = "99999999"

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
                    log_path=exception_log,
                    source_file=file_path.name,
                    location=location,
                    stage="API_ENRICHMENT",
                    record=record,
                    error_message=str(e),
                )

                print(
                    f"⚠️ API enrichment failed for "
                    f"Agreement {record['agreement_id']}"
                    f"Account {record['account_number']}: {e}"
                )

                # Keep processing using the original CSV-derived service address.
                record['mailing_address'] = None
                enriched_record = record

            enriched_records.append(enriched_record)
        
        record = enriched_records

        print("✔ File is ready for next processing step")
        print(f"Rows in file: {len(df)}")
        print(f"Records created: {len(records)}")
        print(f"Billing address overrides found: {billing_override_count}")
        print(f"API enrichment failures: {api_error_count}")

        pdf_count = 0

        for record in records:
            output_dir = build_output_directory(
                OUTPUT_DIR,
                record
            )

            renewal_pdf_path = (
                output_dir / 
                build_pdf_filename(record)
            )

            pdf_error_count = 0

            try:
                ### TEMP TESTING ONLY - REMOVE ###
                if record['account_number'] == "14171809":
                    from pathlib import Path
                    renewal_pdf_path = Path('/invalid-folder/test.pdf')
                ### TEMP TESTING ONLY - REMOVE ###
                

                generate_renewal_notice_pdf(
                    record,
                    renewal_pdf_path,
                    COMPANY_INFO[location],
                    LOGO_PATH
                )

                write_pdf_detail(
                    log_path=pdf_detail_log,
                    source_file=file_path.name,
                    record=record,
                    pdf_path=renewal_pdf_path,
                    status="CREATED",
                )

                pdf_error_count += 1

            except Exception as e:
                pdf_error_count += 1

                write_exception_log(
                    log_path=exception_log,
                    source_file=file_path.name,
                    location=location,
                    stage="PDF_GENERATION",
                    record=record,
                    error_message=str(e),
                )

                print (
                    f"⚠️ PDF generation failed for "
                    f"Agreement {record['agreement_id']} | "
                    f"Account {record['account_number']}: {e}"
                )

                continue
        
        print(f"Renewal PDFs created: {pdf_count}")
        print(f"PDF generation failures: {pdf_error_count}")

        write_run_summary(
            log_path=run_summary_log,
            file_name=file_path.name,
            location=location,
            rows_in_file=len(df),
            records_created=len(records),
            pdfs_created=pdf_count,
            billing_overrides_found=billing_override_count,
            api_enrichment_failures=api_error_count,
            pdf_generation_failures=pdf_error_count,
            status="SUCCESS",
        )

        print()

# --------------------------------------------------

if __name__ == "__main__":
    main()