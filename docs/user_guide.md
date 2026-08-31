## Current Capabilities
The tool currently:
- Detects renewal CSV files in the input directory
- Validates required columns
- Normalizes and cleans source data
- Converts each row into a structured renewal record
- Generates renewal notice PDFs for each valid renewal record
- Saves PDFs using a standardized naming convention
- Organizes PDFs by renewal cycle and location
- Creates run-level and record-level log files
- Supports branded PDF generation using company logo assets
- Retrieves billing address overrides from the FieldPulse API when applicable
- Automatically archives processed CSV files
- Creates an email queue for review/future email automation
- Flags records without email addresses for print/mail handling
- Authenticates with Microsoft Graph
- Accesses the renewals shared mailbox
- Creates Outlook draft messages from email queue records
- Attaches renewal notice PDFs to draft messages
- Validates PDF attachment paths before draft creation
- Generate merged print batches
- Generate print manifests
- Supports location validation and unknown-location detection

The tool does not yet:
- Send emails


## Quick Start

Monthly processing requires:

1. Export the renewal CSV from FieldPulse.
2. Save the file to `data/incoming`
3. Run:

    `python src/main.py`

4. Review:
    - `logs/run_summary.csv`
    - `logs/exception_log.csv`

5. Generate Outlook drafts:

    `python src/email_processor.py`

6. Review draft creation results:

    - `logs/email_draft_log.csv`

7. Generate print batches:

    `python src/print_processor.py`

8. Verify outputs
    - Outlook drafts
    - `batch_print.pdf`
    - `print_manifest.csv`


## Monthly Processing Procedure

1. Export renewal file from FieldPulse.

2. Save the CSV file to: 
    
    `data/incoming`

3. Open a terminal in the project folder.

4. Run:

    `python src/main.py`

5. Review processing results:

    - `logs/run_summary.csv`
    - `logs/exception_log.csv`

6. Verify renewal PDFs were generated in:

    `output/{yymm}/{location}`

7. Generate Outlook renewal drafts:

    `python src/email_processor.py`

8. Review draft creation results:

    - `logs/email_draft_log.csv`

9. Follow the Draft Review Workflow before sending any renewal emails.

10. Generate print batches:

    `python src/print_processor.py`

11. Verify print outputs:

    - `batch_print.pdf`
    - `print_manifest.csv`

12. Print and mail all notices included in the generated print batch.

13. Archive generated output files according to company policy.


## Input Files
Monthly renewal exports should be saved as CSV files in:
- `data/incoming`

The filename should include the location code:
- "an" for Anderson
- "mu" for Muncie

Example filenames:
- `sca-renewals-an-2606.csv`
- `sca-renewals-mu-2606.csv`

### Location Detection

The system determines location from the source filename.

Supported location identifiers:

- an
- mu

If a valid location cannot be determined, the file is skipped and an exception log entry is created.

Example:

`sca-renewals-an-2607.csv` → Anderson

`sca-renewals-mu-2607.csv` → Muncie

`sca-renewals-test-2607.csv` → skipped


## File Validation
Each CSV file is automatically validated before processing.

The following columns are required:
- Customer #
- #ID
- Customer First name
- Customer Last Name
- Customer Company Name
- Location Address
- City
- State
- ZIP Code
- SCA End Date
- Title
- Total Annual Fee

If any required column is missing, the file will be skipped and logged.


## Runtime Modes
This application supports command-line runtime flags for operational control and future automation workflows.

### Dry Run Mode
Use:

`python src/main.py --dry-run`

Dry run mode:
- Loads and validates renewal CSV files
- Builds renewal records
- Performs API enrichment
- Generates runtime summaries and logs

Dry run mode does NOT:
- Generate renewal PDFs
- Archive processed CSV files

This provides a safe preflight validation mode before production processing runs.

### Single File Mode

Use:

`python src/main.py --file sca-renewals-an-2606.csv`

Single file mode processes only the specified CSV file from the incoming directory.

This is useful for:
- targeted reruns
- troubleshooting specific batches
- controlled operational processing

### Location Filter Mode

Use:

`python src/main.py --location an`

or:

`python src/main.py --location mu`

Location filter mode processes only CSV files matching the specified location code.

This is useful for:
- location-specific processing
- staged operational runs
- targeted troubleshooting

### Runtime Argument Rules

The following runtime arguments cannot be used together:
- `--file`
- `--location`

A specific file selection already determines the processing location.


## Expected Outputs

A successful processing run should produce:

- Generated renewal notice PDFs
- Run summary log entries
- PDF detail log entries
- Email queue records
- Archived source CSV files

Review the generated logs after each run to identify any exceptions or records requiring manual handling.


## Output Directory Structure
Renewal notice PDFs are organized by renewal cycle and location.

Structure:
- `output/{yymm}/{location}`

Examples:
- `output/2606/an/`
- `output/2606/mu/`


## PDF Naming Convention
Renewal notice PDFs use the following naming format:
    `{yymm}-renewal-{location}-{agreement_id}-{customer_name}.pdf`

Example:
    `2606-renewal-an-13661-grace-recovery-and-wellness.pdf`

Filename details:
- 'yymm' is based on the agreement expiration date
- 'agreement_id' is the renewal agreement number
- 'customer_name' is normalized into filesystem-safe text
- Special characters and spaces are converted to hyphens


## PDF Batch Generation
After validation and record creation, the application generates one PDF renewal notice for each renewal record.

The number of PDFs created should match the number of records created from the CSV file.


## Renewal Notice Content

Each PDF includes a short customer-facing message explaining that the customer's maintenance agreement is coming up for renewal.

### Agreement Information

Each renewal notice includes:

- Agreement number
- Agreement type
- Expiration date
- Renewal amount
- Customer account number

### Billing Address API Enrichment

During processing, each renewal record is checked against the FieldPulse API.

If FieldPulse indicates that the customer has a different billing address, the renewal notice uses the billing address in the customer/mailing address section.

If no different billing address exists, the renewal notice uses the service address from the CSV export.

The service address is always shown separately on the renewal notice.

### Renewal Notice Layout

The generated renewal notice includes:

- Company branding
- Customer mailing information
- Service address information
- Agreement details
- Renewal pricing
- Remittance/payment section

### Remittance Section
The renewal notice includes a detachable remittance/payment section designed for mailed payments.

Current remittance features include:
- Account number
- Agreement number
- Customer name
- Service address
- Amount due
- Payment method selection
- Payable-to information
- Location-specific mailing address
- Credit card entry fields

The driver's license/check verification fields were removed after operational feedback indicated they were rarely used.


## Run Summary Log
Each processed CSV file is recorded in:
    `logs/run_summary.csv`

The log includes:
- run timestamp
- source file name
- location
- rows in file
- records created
- PDFs created
- billing overrides found
- API enrichment failures
- PDF generation failures
- status

This provides a basic audit trail for each processing run.


## PDF Detail Log
Each generated PDF is recorded in:
    `logs/pdf_detail.csv`

The log includes:
- run timestamp
- source CSV file
- location
- agreement ID
- account number
- customer name
- PDF path
- status

Possible status values include:
- CREATED
- FAILED

This provides a record-level audit trail for both successful and failed PDF generation attempts.


## Exception Logging
Processing exceptions are recorded in:
    `logs/exception_log.csv`

The log includes:
- run timestamp
- source CSV file
- location
- processing stage
- agreement ID
- account number
- customer name
- error message

Current logged exception stages include:
- `LOCATION_DETECTION`
- `API_ENRICHMENT`
- `RECORD_VALIDATION`
- `PDF_GENERATION`

If API enrichment fails for a record, the system continues processing and generates the renewal notice using the CSV-derived service address.

Records missing critical required data are skipped before PDF generation and logged for manual review.

If PDF generation fails for a record, the system logs the failure and continues processing the remaining records.


## Email Queue Generation

After a renewal PDF is successfully generated, the application creates an email queue record in:

`logs/email_queue.csv`

The email queue is a staging file used by `email_processor.py`

Queue records are converted into Outlook drafts for review prior to sending.

The application does not currently send emails automatically.

The email queue includes:
- run timestamp
- source CSV file
- location
- notice window
- agreement ID
- account number
- customer name
- recipient email
- email subject
- email body
- PDF attachment path
- delivery method
- status

Notice-window values identify which renewal cycle generated the queue record:

- `90_DAY`
- `60_DAY`
- `30_DAY`

This information is retained throughout draft creation and logging.

Delivery method values include:
- `EMAIL`
- `PRINT_MAIL`

Status values include:
- `READY`
- `MISSING_EMAIL`

If a customer email address exists in the source CSV, the record is marked as `EMAIL` / `READY`.

If no customer email address exists, the record is marked as `PRINT_MAIL` / `MISSING_EMAIL` so the renewal notice can be printed and mailed.

Email bodies are generated dynamically from renewal record data.

Current personalization includes:
- First-name greeting
- Company records use the contact name from the "Attn:" line
- Greeting names are automatically converted to proper case

Examples:
- John Smith → "Hello John,"
- ACME Plumbing / Attn: Sarah Johnson → "Hello Sarah,"


## Email Automation Status

Renewal emails are generated from an HTML template stored in:

`templates/renewal_email.html`

The template supports dynamic placeholders for customer, agreement, renewal, and company information.

Generated emails are created as Outlook drafts and are not automatically sent.

### Draft Processing Limits

During testing, draft creation can be limited to a specific number of queue records.

Example:

`python src/email_processor.py --limit 5`

This processes only the first five eligible `EMAIL / READY` records.

If no limit is specified:

`python src/email_processor.py`

all eligible `EMAIL / READY` records will be processed.


## Email Draft Log

Each Outlook draft creation attempt is recorded in:

`logs/email_draft_log.csv`

The log includes:
- run timestamp
- agreement ID
- account number
- customer name
- recipient
- draft ID
- attachment name
- status
- error

Possibl status values include:
- `DRAFT_CREATED`
- `DRAFT_FAILED`


## Processed File Archiving
After a renewal CSV file is successfully processed, it is automatically moved from:

`data/incoming`

to:

`data/processed`

This prevents previously processed renewal exports from being processed again during future runs.

If a processed file with the same name already exists, a timestamp is appended to the archived filename to prevent overwriting.


## Troubleshooting

### No PDFs Generated

Check:
- CSV file exists in `data/incoming`
- Required columns are present
- Review `logs/exception_log.csv`

### Missing Billing Address Override

The system automatically checks FieldPulse for alternate billing addresses.

If the lookup fails, the service address will be used instead.

Review:
- `logs/exception_log.csv`

### Missing Email Address

Records without an email address will be marked:

- `PRINT_MAIL`
- `MISSING_EMAIL`

These customers should receive a printed renewal notice.

### API Errors

If FieldPulse API enrichment fails:

- Processing will continue.
- Renewal notices will still be staged.
- Failures will be logged in `logs/exception_log.csv`

If an issue cannot be resolved through the steps above, review:
- `logs/run_summary.csv`
- `logs/exception_log.csv`

These logs contain the most detailed processing information available.


## Planned Enhancements

Future improvements include:

- Enhanced logging and reporting
- Additional FieldPulse enrichment
- Outlook email automation
- SharePoint integration
- Cloud-based processing


## Draft Review Workflow

After a batch draft generation completes:

1. Confirm the number of drafts created matches the summary output.
2. Review `logs/email_draft_log.csv` for any failures.
3. Spot-check several drafts in the renewal shared mailbox.
4. Verify recipients, renewal details, and PDF attachments.
5. Confirm no `PRINT_MAIL` records were drafted.

The draft review process is currently used as a validation step while email automation is being finalized.


## Notice Window Processing

Renewal notices are classified based on the relationship between the current processing month and the agreement expiration month.

| Months Until Expiration | Notice Window |
|-------------------------|---------------|
| 1 Month | 30_DAY |
| 2 Months | 60_DAY |
| 3 Months | 90_DAY |

Examples:

If processed in June:

- July renewals = 30_DAY
- August renewals = 60_DAY
- September renewals = 90_DAY


## Delivery Actions

The system determines how each renewal notice should be delivered.

| Notice Window | Email Available | Delivery Action |
|---------------|-----------------|-----------------|
| 30_DAY | Yes | EMAIL_AND_PRINT |
| 30_DAY | No | PRINT_MAIL |
| 60_DAY | Yes | EMAIL_ONLY |
| 60_DAY | No | PRINT_MAIL |
| 90_DAY | Yes | EMAIL_ONLY |
| 90_DAY | No | PRINT_MAIL |


## Print Queue

Records requiring physical mailing are written to:

`logs/print_queue.csv`

This queue is used to identify renewal notices requiring printing and mailing.

A record may appear in both the email queue and print queue when the delivery action is EMAIL_AND_PRINT.


## Print Batch Processing

Print queue records can be converted into a single merged PDF for batch printing.

Run:

`python src/print_processor.py`

This creates a timestamped folder in:

`output/print_batches`

Each batch folder contains:

- `batch_print.pdf`
- `print_manifest.csv`

The `batch_print.pdf` file contains all selected renewal notices merged into one printable PDF.

The `print_manifest.csv` file provides a reconciliation list for the batch.

Optional filters:

`python src/print_processor.py --location an`

`python src/print_processor.py --notice-window 30_DAY`

`python src/print_processor.py --limit 5`

`python src/print_processor.py --dry-run`

Use `--dry-run` to preview selected records without creating batch files.


# Troubleshooting / Recovery

## Mailbox Reconciliation

`mailbox_reconciliation.py` is a recovery and troubleshooting utility used tgo company renewal drafts and sent messages for a specific processing month.

It is not part of the normal monthly renewal workflow.

### Generate a Reconciliation Report

To perform a read-only mailbox reconciliation:

```bash
python src/mailbox_reconciliation.py --month 2608
```

This generates the reconciliation report without making changes to the mailbox.

### Preview Quarantine Actions

Before moving any messages, run the quarantine process in dry-run mode:

```bash
python src/mailbox_reconciliation.py --month 2608 --quarantine --dry-run
```

Review the reconciliation report and dry-run results before performing any mailbox-changing operation.

### Quarantine Cleanup Candidates

After the dry-run has been reviewed and validated:

```bash
python src/mailbox_reconciliation.py --month 2608 --quarantine
```

Cleanup candidates are moved to a separate quarantine folder rather then deleted.

The quarantine folder should be retained until the normal renewal process for the processing month has been successfully completed and verified.