import csv
import os
from pathlib import Path
from dotenv import load_dotenv
import config as cfg
from logger import write_email_draft_log
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
            "account_number": record.get("account_number"),
            "customer_name": record.get("customer_name"),
            "recipient": record.get("email"),
            "draft_id": "",
            "attachment_name": "",
            "error": str(e),
        }

    return result


if __name__ == "__main__":
    queue_records = load_email_queue(cfg.EMAIL_QUEUE_LOG)
    ready_records = get_ready_email_records(queue_records)

    print(f"Ready email records found: {len(ready_records)}")

    if not ready_records:
        print("No EMAIL / READY records found.")
        raise SystemExit
    
    # Safely limit for first batch test
    ready_records = ready_records[:5]

    draft_created_count = 0
    draft_failed_count = 0
    
    for record in ready_records:
        result = process_queue_record(record)

        write_email_draft_log(
            log_path=cfg.EMAIL_DRAFT_LOG,
            result=result
        )

        if result["status"] == "DRAFT_CREATED":
            draft_created_count += 1
        else:
            draft_failed_count += 1

        print(result)

    print()
    print("Draft Processing Complete")
    print("-------------------------")
    print(f"Drafts Created: {draft_created_count}")
    print(f"Drafts Failed: {draft_failed_count}")
    print(f"Total Records: {len(ready_records)}")
