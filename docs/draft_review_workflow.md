# Draft Review Workflow

## Purpose

The draft review workflow is a temporary validation step used while email automation is being finalized.

The long-term goal is unattended renewal email processing.  During development and early production use, generatred drafts should be reviewed before manual sending.

## When to Use

Use this workflow after running batch draft generation.

## Review Steps

1. Confirm the number of drafts created matches `logs/email_draft_log.csv`
2. Confirm all 'DRAFT_CREATED` rows have a draft ID and attachment name.
3. Confirm no `PRINT_MAIL / MISSING_EMAIL` records were drafted.
4. Spot-check 5-10 drafts in the renewal shared mailbox.
5. Confirm each checked draft has:
    - correct recipient
    - correct subject
    - correct greeting
    - correct renewal details
    - correct PDF attachment
    - working company/contact links
6. Review any `DRAFT_FAILED` rows before proceeding.

## Exit Criteria

Draft generation is considered successful when:

- Draft count matches `DRAFT_CREATED` count.
- `DRAFT_FAILED` count is zero or explained.
- Spot checks shows correct recipients, content, and attachments.
- Print/mail records were not drafted.

## Future Direction

This workflow is expected to become an audit/checkpoint process as the system moves toward unattended processing and eventual automated sending.