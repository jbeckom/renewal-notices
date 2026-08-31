# Technical Debt

## Draft Visibility Verification

Status:
Closed

Priority:
Resolved

Resolution:
Drafts were successfully created through Microsoft Graph and written to the correct shared mailbox.

The observed issue was determined to be an Outlook client synchronization problem rather than an application defect.


## Duplicate Draft Prevention

Status:
Open

Priority:
High

Target Milestone:
Before Production Pilot

Current risk:
- Running `email_processor.py` multiple times against the same queue can create duplicate drafts

Future fix:
- Load recent `DRAFT_CREATED` rows from `email_draft_log.csv`
- Use `agreement_id` + `notice_window` + `recipient` as the duplicate key
- Limit duplicate scan to a configuratble lookback window
- Skip records already successfully drafted within the lookback period
- Report skipped duplicate count in the terminal summary


## Batch Send Guardrails

Status:
Open

Priority:
Medium

Target Milestone:
Before Automated Sending

Current Gap:
The system currently creates drafts only and does not contain safeguards for automated sending.

Completed Safeguards:
- Draft generation requires explicit execution of `email_processor.py`
- Optional processing limits are available using `--limit`

Future Fix:
- Keep draft creation and sending as separate commands
- Require an explicit send command or flag
- Require pre-send validation before any message is sent
- Require duplicate prevention before sending
- Require draft visibility/readback verification before sending
- Maintain a dedicated send log
- Log message ID, recipient, agreement ID, notice window, status, and error
- Block accidental sends from normal processing


## Print Queue / Print Manifest

Status:
Closed

Priority:
High

Target Milestone:
Before July/August Renewal Run

Resolved:
- `PRINT_MAIL` and `EMAIL_AND_PRINT` records are routed to `print_queue.csv`
- Print processor creates a merged `batch_print.pdf`
- Print processor creates `print_manifest.csv`
- Supports filtering by location
- Supports filtering by notice window
- Supports dry-run validation
- Supports limited test batches

Future Considerations:
- Optional per-notice-window batch files
- Optional print batch log
- Optional processed/printed tracking


## Notice Window Processing

Status:
Closed

Priority:
High

Target Milestone:
Before July/August Renewal Run

Resolved:
- Identify notice window
- Support EMAIL_ONLY
- Support PRINT_MAIL
- Support EMAIL_AND_PRINT
- Generate reporting by notice window


## Mailbox Draft Reconciliation / Recovery

**Status:** CLOSED

A temporary mailbox reconciliation utility was created to recover from duplicate Outlook draft creation during development of the renewal email workflow.

`mailbox_reconciliation.py` compares renewal messages in the shared mailbox for a specified processing month using:

- normalized recipient email address
- renewal PDF attachment filename

Messages are classified as:

- `DRAFT_ONLY`
- `DUPLICATE_DRAFTS`
- `SENT_ONLY`
- `SEND_WITH_STALE_DRAFT`
- `AMBIGUOUS`

The utility supports a quarantine workflow for safely isolating duplicate or stale drafts without immediately deleting them.

Example:

```bash
python src/mailbox_reconciliation.py --month 2608 --quarantine --dry-run
```

The dry-run should always be reviewed before performing mailbox changes.

Cleanup candidates are moved to a separate mailbox folder rather than deleted, allowing them to be retained until the normal process has been successfully completed and verified.

This utility is intended primarily as a recovery/troubleshooting tool and is not part of the normal monthly renewal workflow.