import argparse
import csv
import os
from collections import defaultdict
from datetime import datetime, timezone

import config as cfg
from graph_client import (
    graph_get,
    graph_get_all,
    get_or_create_mail_folder,
    move_message
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare renewal draft and sent messages."
    )

    parser.add_argument(
        "--month",
        type=str,
        required=True,
        help="Processing month in YYMM format, for example 2608."
    )

    parser.add_argument(
        "--quarantine",
        action="store_true",
        help="Move safe cleanup candidates to a quarantine folder."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show quaratine actions without changing the mailbox"
    )

    return parser.parse_args()


def normalize_email(value: str) -> str:
    """
    Normalize an email address for comparison:
    """

    return (value or "").strip().lower()


def get_month_range(month_value: str) -> tuple[datetime, datetime]:
    """
    Convert a YYMM processing month into UTC start/end datetimes.
    """

    try:
        start = datetime.strptime(month_value, "%y%m").replace(
            tzinfo=timezone.utc
        )
    except ValueError as exc:
        raise ValueError(
            "--month must use YYMM format, for example 2608"
        ) from exc

    if start.month == 12:
        end = start.replace(
            year=start.year + 1,
            month=1,
        )
    else:
        end = start.replace(
            month=start.month + 1,
        )

    return start, end


def get_recipient(message: dict) -> str:
    """
    Return the first recipient email address from a Graph message.
    """

    recipients = message.get("toRecipients", [])

    if not recipients:
        return ""

    return normalize_email(
        recipients[0]
        .get("emailAddress", {})
        .get("address", "")
    )


def get_pdf_attachment_name(mailbox: str, message_id: str) -> str | None:
    """
    Return the single PDF attachment name for a message.

    Returns None if there is not exactly one PDF attachment.
    """

    result = graph_get(
        f"/users/{mailbox}/messages/{message_id}/attachments"
    )

    pdf_attachments = [
        attachment.get("name", "")
        for attachment in result.get("value", [])
        if attachment.get("name", "").lower().endswith(".pdf")
    ]

    if len(pdf_attachments) != 1:
        return None

    return pdf_attachments[0]


def get_reconciliation_key(
        recipient: str,
        attachment_name: str,
) -> tuple[str, str]:
    """
    Build a stable renewal-message comparison key.
    """

    return (
        normalize_email(recipient),
        attachment_name.strip().lower(),
    )


def load_folder_messages(
        mailbox: str,
        folder: str, 
        start: datetime,
        end: datetime,
        date_field: str,
) -> list[dict]:
    """
    Load recent renewal messages froma mailbox folder.
    """

    start_text = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_text = end.strftime("%Y-%m-%dT%H:%M:%SZ")

    endpoint = (
        f"/users/{mailbox}/mailFolders/{folder}/messages"
        "?$select="
        "id,subject,toRecipients,createdDateTime,"
        "sentDateTime,isDraft,hasAttachments"
        f"&$filter={date_field} ge {start_text} "
        f"and {date_field} lt {end_text}"
        "&$top=100"
    )

    messages = graph_get_all(endpoint)

    return [
        message for message in messages
        if message.get("subject") == cfg.EMAIL_SUBJECT
    ]


def build_message_records(
        mailbox: str,
        messages: list[dict],
        folder_type: str,
) -> tuple[list[dict], list[dict]]:
    """
    Convert Graph messages into reconciliation records.

    Returns usable records and ambiguous records separately.
    """

    usable_records = []
    ambiguous_records = []

    for message in messages:
        recipient = get_recipient(message)

        attachment_name = get_pdf_attachment_name(
            mailbox=mailbox,
            message_id=message["id"],
        )

        if not recipient or not attachment_name:
            ambiguous_records.append({
                "folder_type": folder_type,
                "message_id": message.get("id"),
                "recipient": recipient,
                "attachment_name": attachment_name or "",
                "reason": "Missing recipient or exactly one PDF attachment.",
            })
            continue

        usable_records.append({
            "folder_type": folder_type,
            "message_id": message.get("id"),
            "recipient": recipient,
            "attachment_name": attachment_name,
            "created_at": message.get("createdDateTime", ""),
            "sent_at": message.get("sentDateTime", ""),
            "key": get_reconciliation_key(
                recipient,
                attachment_name,
            )
        })

    return usable_records, ambiguous_records


def classify_group(
        draft_count: int,
        sent_count: int,
) -> str:
    """
    Classify one renewal-message reconciliation group.
    """

    if sent_count > 1 and draft_count > 0:
        return "DUPLICATE_SENT_WITH_DRAFT"

    if sent_count > 1:
        return "DUPLICATE_SENT"

    if sent_count == 1 and draft_count > 0:
        return "SENT_WITH_STALE_DRAFT"

    if sent_count == 1:
        return "SENT_ONLY"

    if draft_count > 1:
        return "DUPLICATE_DRAFTS"

    return "DRAFT_ONLY"


def build_reconciliation_rows(
        draft_records: list[dict],
        sent_records: list[dict],
) -> list[dict]:
    """
    Group draft and sent messages by recipient + attachment filename.
    """

    grouped = defaultdict(
        lambda: {
            "drafts": [],
            "sent": [],
        }
    )

    for record in draft_records:
        grouped[record["key"]]["drafts"].append(record)

    for record in sent_records:
        grouped[record["key"]]["sent"].append(record)

    rows = []

    for key, group in grouped.items():
        recipient, attachment_name = key

        drafts = group["drafts"]
        sent = group["sent"]

        rows.append({
            "recipient": recipient,
            "attachment_name": attachment_name,
            "draft_count": len(drafts),
            "sent_count": len(sent),
            "status": classify_group(
                draft_count=len(drafts),
                sent_count=len(sent),
            ),
            "draft_ids": ";".join(
                record["message_id"] for record in drafts
            ),
            "sent_ids": ";".join(
                record["message_id"] for record in sent
            ),
        })

    return sorted(
        rows,
        key=lambda row: (
            row["status"],
            row["recipient"],
            row["attachment_name"],
        ),
    )


def build_quarantine_plan(
        reconciliation_rows: list[dict],
        draft_records: list[dict],
) -> list[dict]:
    """
    Determine which drafts are safe quarantine candidates.

    SENT_WITH_STALE_DRAFT:
        Quarantine all matching drafts.

    DUPLICATE_DRAFTS:
        Keep the newest draftg and quarantine older copies.

    All other statuses:
        Take no action.
    """

    drafts_by_key = defaultdict(list)

    for record in draft_records:
        drafts_by_key[record["key"]].append(record)

    plan = []

    for row in reconciliation_rows:
        key = (
            row["recipient"],
            row["attachment_name"],
        )

        drafts = drafts_by_key.get(key, [])
        status = row["status"]

        if status == "SENT_WITH_STALE_DRAFT":
            for draft in drafts:
                plan.append({
                    "recipient": row["recipient"],
                    "attachment_name": row["attachment_name"],
                    "message_id": draft["message_id"],
                    "created_at": draft["created_at"],
                    "reason": "SENT_WITH_STALE_DRAFT",
                })

        elif status == "DUPLICATE_DRAFTS":
            sorted_drafts = sorted(
                drafts,
                key=lambda record: record.get("created_at", ""),
                reverse=True,
            )

            ### KEEP THE NEWEST COPY ###
            for draft in sorted_drafts[1:]:
                plan.append({
                    "recipient": row["recipient"],
                    "attachment_name": row["attachment_name"],
                    "message_id": draft["message_id"],
                    "created_at": draft["created_at"],
                    "reason": "DUPLICATE_DRAFT"
                })

    return plan


def write_reconciliation_report(
        rows: list[dict],
        output_path,
) -> None:
    """
    Write mailbox reconciliation results.
    """

    fieldnames = [
        "recipient",
        "attachment_name",
        "draft_count",
        "sent_count",
        "status",
        "draft_ids",
        "sent_ids",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        mode="w",
        newline="",
        encoding="utf-8",
    ) as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


def write_quarantine_log(
        rows: list[dict],
        output_path,
) -> None:
    """
    Write the results of a live mailbox quarantine operation.
    """

    fieldnames = [
        "recipient",
        "attachment_name",
        "message_id",
        "created_at",
        "reason",
        "result",
        "new_message_id",
        "error"
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        mode="w",
        newline="",
        encoding="utf-8",
    ) as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


def execute_quarantine_plan(
        mailbox: str,
        quarantine_plan: list[dict],
        quarantine_folder_name: str,
) -> list[dict]:
    """
    Move planned drafts into the quarantine folder.

    Each move is attempted independently so one failure does not stop the remaining quarantine operations.
    """

    folder = get_or_create_mail_folder(
        mailbox=mailbox,
        folder_name=quarantine_folder_name,
    )

    destination_folder_id = folder["id"]

    results = []

    for index, record in enumerate(quarantine_plan, start=1):
        result = {
            **record,
            "result": "",
            "new_message_id": "",
            "error": "",
        }

        try:
            moved_message = move_message(
                mailbox=mailbox,
                message_id=record["message_id"],
                destination_folder_id=destination_folder_id,
            )

            result["result"] = "MOVED"
            result["new_message_id"] = moved_message.get("id", "")

        except Exception as e:
            result["result"] = "FAILED"
            result["error"] = str(e)

        results.append(result)

        if index % 25 == 0 or index == len(quarantine_plan):
            print(
                f"Processed {index}/{len(quarantine_plan)} "
                "quarantine moves..."
            )

    return results


def main() -> None:
    args = parse_args()

    if args.dry_run and not args.quarantine:
        raise ValueError("--dry-run requires --quarantine")

    start, end = get_month_range(args.month)

    quarantine_folder_name = f"Renewal Quarantine - {args.month}"

    quarantine_log_path = (
        cfg.MAILBOX_RECONCILIATION_LOG.parent
        / f"mailbox_quarantine_{args.month}.csv"
    )

    mailbox = os.getenv("GRAPH_SHARED_MAILBOX")

    if not mailbox:
        raise ValueError("GRAPH_SHARED_MAILBOX is not configured.")

    print(f"Reviewing mailbox: {mailbox}")
    print(f"Processing month: {args.month}")
    print(f"Range: {start.isoformat()} through {end.isoformat()}")

    draft_messages = load_folder_messages(
        mailbox=mailbox,
        folder="drafts",
        start=start,
        end=end,
        date_field="createdDateTime"
    )

    sent_messages = load_folder_messages(
        mailbox=mailbox,
        folder="sentitems",
        start=start,
        end=end,
        date_field="sentDateTime",
    )

    print(f"Renewal drafts found: {len(draft_messages)}")
    print(f"Renewal sent messages found: {len(sent_messages)}")

    draft_records, ambiguous_drafts = build_message_records(
        mailbox=mailbox,
        messages=draft_messages,
        folder_type="DRAFT",
    )

    sent_records, ambiguous_sent = build_message_records(
        mailbox=mailbox,
        messages=sent_messages,
        folder_type="SENT",
    )

    reconciliation_rows = build_reconciliation_rows(
        draft_records=draft_records,
        sent_records=sent_records,
    )

    quarantine_plan = build_quarantine_plan(
        reconciliation_rows=reconciliation_rows,
        draft_records=draft_records,
    )

    write_reconciliation_report(
        rows=reconciliation_rows,
        output_path=cfg.MAILBOX_RECONCILIATION_LOG,
    )

    status_counts = defaultdict(int)

    for row in reconciliation_rows:
        status_counts[row["status"]] += 1

    print()
    print("Mailbox Reconciliation Complete")
    print("-------------------------------")

    for status in sorted(status_counts):
        print(f"{status}: {status_counts[status]}")

    ambiguous_count = (
        len(ambiguous_drafts) + len(ambiguous_sent)
    )

    print(f"AMBIGUOUS: {ambiguous_count}")
    print(f"Report: {cfg.MAILBOX_RECONCILIATION_LOG}")

    if args.quarantine:
        stale_count = sum(
            1
            for record in quarantine_plan
            if record["reason"] == "SENT_WITH_STALE_DRAFT"
        )

        duplicate_count = sum(
            1
            for record in quarantine_plan
            if record["reason"] == "DUPLICATE_DRAFT"
        )

        print()
        print("Quarantine Plan")
        print("------------------------------")
        print(f"Stale drafts to move: {stale_count}")
        print(f"Duplicate extras to move: {duplicate_count}")
        print(f"Total drafts to move: {len(quarantine_plan)}")

        if args.dry_run:
            print()
            print("DRY RUN - NO MAILBOX CHANGES MADE")
            return

        if not quarantine_plan:
            print()
            print("No quarantine candidates found.  No mailbox changes made.") 

        print()
        print(f"Quarantine folder: {quarantine_folder_name}")
        print("Moving drafts...")

        quarantine_results = execute_quarantine_plan(
            mailbox=mailbox,
            quarantine_plan=quarantine_plan,
            quarantine_folder_name=quarantine_folder_name,
        )

        write_quarantine_log(
            rows=quarantine_results,
            output_path=quarantine_log_path,
        )

        moved_count = sum(
            1
            for result in quarantine_results
            if result["result"] == "MOVED"
        )

        failed_count = sum(
            1
            for result in quarantine_results
            if result["result"] == "FAILED"
        )

        print()
        print("Quarantine Complete")
        print("-" * 30)
        print(f"Planned moves: {len(quarantine_plan)}")
        print(f"Successfully moved: {moved_count}")
        print(f"Failed moves: {failed_count}")
        print(f"Log: {quarantine_log_path}")

        if failed_count:
            print()
            print(
                "WARNING: Some drafts could not be moved."
                "Review the quarantine log before continuing."
            )


if __name__ == "__main__":
    main()