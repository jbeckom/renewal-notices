
import os
import csv
import argparse
import config as cfg
from pathlib import Path
from dotenv import load_dotenv
from logger import write_email_draft_log
from datetime import datetime, timedelta
from graph_client import create_shared_mailbox_draft_with_attachment

load_dotenv()

def load_email_queue(queue_path: Path) -> list[dict]:
    """
    Load email queue records from CSV.
    """

    if not queue_path.exists():
        raise FileNotFoundError(f"Email queue file not found: {queue_path}")
    
    with queue_path.open(mode="r", newline="", encoding="utf-8") as queue_file:
        reader = csv.DictReader(queue_file)
        return list(reader)
    

def get_ready_email_records(queue_records: list[dict]) -> list[dict]:
    """
    Return only records marked EMAIL / READY.
    """

    return [
        record for record in queue_records 
        if record.get("delivery_method") == "EMAIL"
        and record.get("status") == "READY"
    ]


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for email draft processing.
    """

    parser = argparse.ArgumentParser(
        description="Create Outlook drafts from the renewal email queue."
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of EMAIL / READY records to process."
    )

    return parser.parse_args()


def create_draft_from_queue_record(record: dict) -> dict:
    """
    Create one Outlook draft from one email queue record.
    """

    mailbox = os.getenv("GRAPH_SHARED_MAILBOX")

    if not mailbox:
        raise ValueError("GRAPH_SHARED_MAILBOX is not configured.")
    
    recipient = record.get("email")
    subject = record.get("subject")
    body = record.get("body")
    pdf_path = record.get("pdf_path")

    if not recipient:
        raise ValueError("Queue record is missing recipient email.")
    
    if not subject:
        raise ValueError("Queue record is missing email subject.")
    
    if not body:
        raise ValueError("Queue record is missing email body.")
    
    if not pdf_path:
        raise ValueError("Queue record is missing pdf_path.")
    
    result = create_shared_mailbox_draft_with_attachment(
        mailbox=mailbox,
        to_email=recipient,
        subject=subject,
        body=body,
        file_path=pdf_path
    )

    return {
        "status": "DRAFT_CREATED",
        "agreement_id": record.get("agreement_id"),
        "notice_window": record.get("notice_window"),
        "account_number": record.get("account_number"),
        "customer_name": record.get("customer_name"),
        "recipient": recipient,
        "draft_id": result["draft"]["id"],
        "attachment_name": result["attachment"].get("name"),
        "error": ""
    }


def process_queue_record(record: dict) -> dict:
    try:
        result = create_draft_from_queue_record(record)

    except Exception as e:
        result = {
            "status": "DRAFT_FAILED",
            "agreement_id": record.get("agreement_id"),
            "notice_window": record.get("notice_window"),
            "account_number": record.get("account_number"),
            "customer_name": record.get("customer_name"),
            "recipient": record.get("email"),
            "draft_id": "",
            "attachment_name": "",
            "error": str(e),
        }

    return result


def parse_log_timestamp(value: str) -> datetime | None:
    """
    Parse a draft log timestamp.

    Returns None when the timestamp is missing or invalid.
    """

    if not value:
        return None
    
    try:
        return datetime.fromisoformat(value.strip())
    except ValueError:
        return None


def get_draft_key(record: dict) -> tuple[str, str, str]:
    """
    Build the duplicate-prevention key for a queue or log record.
    """    

    return (
        record.get("agreement_id", "").strip(),
        record.get("notice_window", "").strip(),
        record.get("recipient", record.get("email", "")).strip().lower(),
    )


def load_successful_draft_keys(
        log_path: Path,
        lookback_days: int,
) -> set[tuple[str, str, str]]:
    """
    Load recent successful draft keys from the email draft log.
    """

    if not log_path.exists():
        return set()
    
    cutoff = datetime.now() - timedelta(days=lookback_days)
    draft_keys = set()

    with log_path.open(mode="r", newline="", encoding="utf-8") as log_file:
        reader = csv.DictReader(log_file)

        for row in reader:
            if row.get("status") != "DRAFT_CREATED":
                continue

            run_timestamp = parse_log_timestamp(row.get("run_timestamp", ""))

            if run_timestamp is None:
                continue

            if run_timestamp < cutoff:
                continue

            draft_keys.add(get_draft_key(row))

    return draft_keys


if __name__ == "__main__":
    args = parse_args()
    queue_records = load_email_queue(cfg.EMAIL_QUEUE_LOG)
    ready_records = get_ready_email_records(queue_records)

    successful_draft_keys = load_successful_draft_keys(
        log_path=cfg.EMAIL_DRAFT_LOG,
        lookback_days=cfg.DRAFT_DUPLICATE_LOOKBACK_DAYS,
    )

    draft_skipped_count = 0

    print_mail_records = [
        record for record in queue_records
        if record.get("delivery_method") == "PRINT_MAIL"
    ]

    print(f"Ready email records found: {len(ready_records)}")

    if not ready_records:
        print("No EMAIL / READY records found.")
        raise SystemExit
    
    total_ready_records = len(ready_records)

    if args.limit is not None:
        if args.limit <= 0:
            raise ValueError("--limit must be greater than zero.")
        
        ready_records = ready_records[:args.limit]

    draft_created_count = 0
    draft_failed_count = 0
    
    for record in ready_records:
        draft_key = get_draft_key(record)

        if draft_key in successful_draft_keys:
            draft_skipped_count += 1

            print(
                "Skipping duplicate draft: "
                f"{record.get('agreement_id')} | "
                f"{record.get('notice_window')} | "
                f"{record.get('email')}"
            )

            continue

        result = process_queue_record(record)

        write_email_draft_log(
            log_path=cfg.EMAIL_DRAFT_LOG,
            result=result
        )

        if result["status"] == "DRAFT_CREATED":
            draft_created_count += 1
            successful_draft_keys.add(get_draft_key(record))
        else:
            draft_failed_count += 1

        print(result)

    print()
    print("Draft Processing Complete")
    print("-------------------------")
    print(f"Queue Records Loaded: {len(queue_records)}")
    print(f"EMAIL / READY Records Found: {total_ready_records}")
    print(f"EMAIL / READY Records Processed: {len(ready_records)}")
    print(f"Drafts Created: {draft_created_count}")
    print(f"Drafts Failed: {draft_failed_count}")
    print(f"Drafts Skipped: {draft_skipped_count}")
    print(f"Print/Mail Records: {len(print_mail_records)}")

    print()
    print("Review Checklist")
    print("----------------")
    print("1. Confirm draft count mathces Drafts Created.")
    print("2. Spot-check 5-10 drafts in the renewal shared mailbox.")
    print("3. Confirm attachments open correctly.")
    print("4. Confirm no drafts were created for PRINT_MAIL records.")
    print("5. Review logs/email_draft_log.csv for failures.")

