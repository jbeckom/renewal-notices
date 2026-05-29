import pandas as pd
import config as cfg
from api_client import enrich_record_with_mailing_address
from logger import write_pdf_detail, write_exception_log, write_email_queue
from pdf_generator import generate_renewal_notice_pdf
from email_builder import build_email_queue_values
from utils import (
    build_pdf_filename,
    build_output_directory,
    validate_record,
)


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
    email_ready_count = 0
    print_mail_count = 0

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

            email_values = build_email_queue_values(
                record,
                renewal_pdf_path,
                cfg.COMPANY_INFO[location]
            )

            if email_values["delivery_method"] == "EMAIL":
                email_ready_count += 1

            if email_values["delivery_method"] == "PRINT_MAIL":
                print_mail_count += 1

            write_email_queue(
                log_path=cfg.EMAIL_QUEUE_LOG,
                source_file=file_path.name,
                record=record,
                pdf_path=renewal_pdf_path,
                subject=email_values["subject"],
                body=email_values["body"],
                delivery_method=email_values["delivery_method"],
                status=email_values["status"]
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

    return pdf_count, pdf_error_count, email_ready_count, print_mail_count


def print_file_summary(
        file_path,
        rows_in_file,
        records_created,
        billing_override_count,
        api_error_count,
        pdf_count,
        pdf_error_count,
        status,
        email_ready_count,
        print_mail_count,
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
    print(f"Email ready: {email_ready_count}")
    print(f"Print/mail needed: {print_mail_count}")
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