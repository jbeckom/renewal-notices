# Technical Debt

## Draft Visibility Verification

Status:
Open

Priority:
Medium

Target Milestone:
Before Automated Sending

Current Issue: 
Graph returned draft IDs and logs showed `DRAFT_CREATED`, but draft were not visible in Outlook.

Future fix:
- Add optional post-create Graph readback verification
- Confirm created draft exists in expected shared mailbox
- Log verification status


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
- Check `email_draft_log.csv` before draft creation
- Use `agreement_id` + `notice_window` + `recipient` as the duplicate key
- Support configurable lookback period
- Skip records already successfully drafted


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
- Separate draft creation from sending
- Require explicit send command/flag
- Maintain send log
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
- Optinoal processed/printed tracking


## Notice Window Processing

Status:
Closed

Priority:
High

Target Milestone:
Before July/August Renewal Run

Current Gap:
The system does not distinguish between 30-day and 60-day renewal notice processing rules.

Future Fix:
- Identify notice window
- Support EMAIL_ONLY
- Support PRINT_MAIL
- Support EMAIL_AND_PRINT
- Generate reporting by notice window