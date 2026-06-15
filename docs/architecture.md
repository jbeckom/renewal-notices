# Renewal Notice Automation Architecture

## Purpose

The Renewal Notice Automation project generates branded renewal notice PDFs from FieldPulse renewal exports and prepares future email automation workflows.

The system is designed to support:
- monthly renewal CSV processing
- data validation and normalization
- FieldPulse API enrichment
- branded PDF generation
- structured logging
- email queue preparation
- future Outlook draft creation through Microsoft Graph
- future SharePoint/cloud/web app workflows

---

## Architecture Principles

The project is designed around several core principles:

### Fail One Record, Not the Entire Batch

Processing should continue whenever possible.

A single customer record failure should not prevent other renewal notices from being generated.

### Preserve Source Data Integrity

Source CSV exports are treated as read-only inputs.

All processing, enrichment, and output generation occur separately from the original source file.

### Append-Only Audit Trail

Logs are written in an append-only manner to preserve historical processing data and support troubleshooting.

### Separation of Responsibilities

Application components are organized by responsibility:

- orchestration
- workflow processing
- PDF generation
- email preparation
- logging
- external integrations

### Operator-Friendly Design

The long-term goal is for a non-technical employee to safely operate the system without modifying source code.

### Cloud Readiness

The architecture is designed to support future migration to:

- SharePoint storage
- Microsoft Graph automation
- web-based processing
- cloud-hosted execution

---

## Current Architecture Overview

The application currently runs as a local Python command-line workflow.

High-level flow:

1. Read renewal CSV files from `data/incoming`
2. Validate required source columns
3. Normalize source data into renewal records
4. Enrich records with FieldPulse billing address overrides
5. Generate branded renewal notice PDFs
6. Create email queue records
7. Write processing logs
8. Archive processed CSV files to `data/processed`

---

## Processing Flow


Location detection occurs before file processing begins

Files that do not resolve to a supported location are excluded from the workflow and logged as exceptions.

```text
FieldPulse CSV
        │
        ▼
Validation
        │
        ▼
Record Building
        │
        ▼
FieldPulse API Enrichment
        │
        ▼
PDF Generation
        │
        ▼
Delivery Routing
        │
        ├─ EMAIL_ONLY ───────► email_queue.csv
        │
        ├─ PRINT_MAIL ───────► print_queue.csv
        │
        └─ EMAIL_AND_PRINT ─► both queues
        │
        ├───────────────┐
        │               │
        ▼               ▼
email_queue.csv     print_queue.csv
        │               │
        ▼               ▼
email_processor.py  print_processor.py
        │               │
        ▼               ▼
Outlook Drafts     batch_print.pdf
        │               │
        ▼               ▼
email_draft_log    print_manifest.csv
```

---

## Application Layers

### `main.py`

Entry point for the application.

Responsibilities:
- parse runtime arguments
- select files to process
- coordinate high-level processing
- handle dry-run behavior
- write run summary logs
- call workflow helpers

Runtime flags currently include:
- `--dry-run`
- `--file`
- `--location`

### `workflow.py`

Contains operational workflow helpers.

Responsibilities:
- load CSV files
- enrich renewal records with FieldPulse API data
- generate PDFs
- create email queue records
- print runtime summaries
- archive processed files
- log processing exceptions
- determine notice window classification
- determine delivery action
- write email queue records
- wirte print queue records

#### Queue Routing

After successful PDF generation, each renewal notice is routed based on notice window and email availability.

Supported delivery actions:

- `EMAIL_ONLY`
- `PRINT_MAIL`
- `EMAIL_AND_PRINT`

Routing behavior:

- `EMAIL_ONLY` → `email_queue.csv`
- `PRINT_MAIL` → `print_queue.csv`
- `EMAIL_AND_PRINT` → `email_queue.csv` and `print_queue.csv`


### `utils.py`

Contains low-level reusable helper functions.

Responsibilities:
- detect location from filename
- validate CSV columns
- clean text and ID fields
- build customer names
- build service addresses
- build renewal records
- build PDF filenames
- build output directories
- validate renewal records

#### Notice Window Processing

The system classifies renewal notices by comparing the agreement expiration month to the processing month.

Supported notice windows:

- `30_DAY`
- `60_DAY`
- `90_DAY`

Examples:

If processed in June:

- July renewals → `30_DAY`
- August renewals → `60_DAY`
- September renewals → `90_DAY`

Notice windows are used to determine delivery actions and queue routing.


### `pdf_generator.py`

Responsible for rendering renewal notice PDFs.

Responsibilities:
- generate branded PDF renewal notices
- render company logo/contact information
- render location-specific remittance mailing section
- render mailing and service address sections
- render renewal/payment details
- render detachable remittance section
- support standalone test PDF generation

#### Development Testing
`pdf_generator.py` includes a standalone testing block using a hardcoded sample record.

This allows rapid iteration of:
- PDF layout
- Window envelope alignment
- Logo sizing
- Remittance formatting
- Payment field spacing

without processing full renewal batches.

### `email_builder.py`

Responsible for preparing email queue content.

Responsibilities:
- build email subject/body values
- generate personalized greetings
- render HTML email templates
- substitute customer, agreement, and company placeholders
- use first-name greeting logic
- use company contact first name from `Attn:` lines
- apply proper-case formatting to greeting names
- determine delivery method:
    - `EMAIL`
    - `PRINT_MAIL`

#### HTML Email Templates

Customer-facing renewal emails are generated using an external HTML template.

Template Location:

`templates/renewal_email.html`

The template is loaded at runtime and populated with customer, renewal, and company information using the email builder module.

Separating presentation from application logic allows email content updates without modifying Python source code.

### `graph_client.py`

Responsible for Microsoft Graph integration.

Current responsibilities:
- authentication with Microsoft Graph using MSAL
- cache authentication tokens locally
- call Graph API endpoints
- validate shared mailbox access
- create test draft messages in the shared mailbox

Future responsibilities:
- create renewal draft messages
- attach generated renewal PDFs
- process email queue records
- log draft creation status

### `logger.py`

Responsible for structured CSV logging.

Current logs:
- `logs/run_summary.csv`
- `logs/pdf_detail.csv`
- `logs/exception_log.csv`
- `logs/email_queue.csv`

### `config.py`

Centralized configuration/constants.

Responsibilities:
- directory paths
- company/location information
- logo paths
- log file paths
- PDF constants
- remittance text
- validation fields
- email subject
- shared runtime constants
- print batch output paths

---

## Data Flow

### Input

Renewal exports are placed in:

`data/incoming`

Expected input:
- CSV files exported from FieldPulse
- filenames include location codes:
    - `an`
    - `mu`

Example:

`sca-renewals-an-2606.csv`

### Record Building

Each CSV row is converted into a renewal record dictionary.

The renewal record becomes the common internal data object used by:
- PDF generation
- email queue generation
- logging
- API enrichment

#### Customer Name Formatting
Customer names are formatted as follows:

- If a company name exists:
    'Company Name'
    'Attn: First Last'

- If no company name exists:
    'First Last'


#### Service Address Formatting
The export's 'Location Address' field contains the full address, including city, state, and ZIP Code.
To avoid duplicate address lines, the tool extracts only the street address from 'Location Address', then uses the separate 'City', 'State', and 'ZIP Code' fields for the second line.


#### Data Normalization
Certain placeholder values in the source data are treated as empty:
- '-'
- blank values
- null/NaN values

This prevents placeholder data from appearing on renewal notices.

### API Enrichment

Each renewal record is checked against the FieldPulse API.

If the customer has `has_different_billing_address` set to true, the billing address from FieldPulse is used as the mailing address.

If API enrichment fails:
- the exception is logged
- processing continues
- the service address remains the fallback mailing address

### PDF Generation

Each valid record generates one PDF.

PDFs are saved using:

`output/{yymm}/{location}`

Example:

`output/2606/an/`

PDF filenames follow:

`{yymm}-renewal-{location}-{agreement_id}-{customer_name}.pdf`

### Email Queue Generation

After a PDF is successfully created, an email queue row is generated in:

`logs/email_queue.csv`

The queue indicates whether the record is ready for email or should be printed/mailed.

Each email queue record also retains the originating notice window (`90_DAY`, `60_DAY`, `30_DAY`).

Notice-window information is preserved throughout the email workflow to support auditability and future duplicate-draft prevention.

Delivery methods:
- `EMAIL`
- `PRINT_MAIL`

Statuses:
- `READY`
- `MISSING_EMAIL`

No emails are sent from the queue yet.

### Archiving

After a file is processed, the source CSV is moved from:

`data/incoming`

to:

`data/processed`

If a file with the same name already exists, a timestamp is appended to prevent overwriting.

---

## Runtime Execution

The application is executed through `main.py`

Runtime behavior is controlled through command-line arguments.

Supported runtime modes include:
- standard processing
- dry-run processing
- single-file processing
- location-filtered processing

Detailed usage is documented in `docs/user_guide.md`

---

## Logging Architecture

The application uses CSV-based logging for auditing, troubleshooting, and reporting.

### Run Summary Log

Provides file-level processing metrics and operational audit information.

### PDF Detail Log

Provides record-level PDF generation tracking.

### Exception Log

Provides record-level error tracking while allowing processing to continue.

### Email Queue Log

Provides staging data for future email automation workflows.

### Email Draft Log

Provides record-level tracking for Outlook draft creation attempts.

### Print Queue Log

Provides record-level tracking for renewal notices requiring physical mailing.

### Print Batch Manifest

Provides a batch-level reconciliation file for merged print batches.

---

## Microsoft Graph Architecture

The email automation feature uses Microsoft Graph and Microsoft Entra ID to support future Outlook draft creation and shared mailbox workflows.

### Current Status

Completed:

- Entra App Registration
- Delegated Graph Permissions
- Interactive Authentication
- Token Caching
- Shared Mailbox Access Validation
- Draft Creation Validation

### Shared Mailbox

Current Mailbox:

`renewals@an.summersphc.com`

### Authentication Model

Current implementation uses:

- delegated user authentication
- MSAL token caching
- user mailbox permissions

A local cache file is stored as:

`.graph_token_cache.bin`

The file is excluded from Git and should never be committed.

Token caching allows the application to reuse valid Microsoft Graph access tokens between runs, reducing repeated browser sign-ins during development.

If the token expires, is invalidated, or the cache file is deleted, the application will prompt for authentication again.

### Current Graph Capabilities

The application can currently:

- authenticate to Microsoft Graph
- reuse cached authentication tokens
- access the renewals shared mailbox
- create draft messages in the shared mailbox
- create Outlook drafts from email queue records
- attach renewal PDFs to draft messages
- log draft creation results
- process batch draft generation for all `EMAIL / READY` records
- generate HTML-formatted Outlook drafts 

### Planned Graph Capabilities

Future development will include:

- draft creation from email queue records
- PDF attachment support
- email draft logging
- optional draft review workflow
- future email sending workflow

---

## Branching Strategy

### Main Branch

`main`

Production-ready code.

Contains:
- CSV processing
- API enrichment
- PDF generation
- logging

### Email Automation Branch

`feature/email-automation`

Development branch for:

- Microsoft Graph integration
- email queue processing
- draft creation
- attachment support

The email branch is intentionally isolated until email functionality is fully validated.

---

## Release Tags

Major project milestones are captured using Git tags.

Current milestone tags:

- `pdf-production-v1`
- `email-queue-v1`
- `graph-drafts-v1`

Tags provide stable rollback points and historical reference markers.

---

## Future Architecture Roadmap

### Email Draft Automation

- process EMAIL / READY queue records
- create Outlook drafts automatically
- attach renewal PDFs
- log draft creation results

### Draft Review Workflow

- review generated Outlook drafts
- verify recipients and attachments
- validate renewal content before sending
- establish production operating procedures

### SharePoint Integration

Potential future migration:

- incoming files stored in SharePoint
- processed files archived in SharePoint
- generated PDFs stored in SharePoint
- logs stored in SharePoint

### Internal Web Application

Long-term goal:

A lightweight internal web application where a non-technical user can:

1. Upload renewal exports
2. Start processing
3. Monitor progress
4. Review logs
5. Download generated files

### Cloud-Based Processing

Potential future architecture:

- FastAPI backend
- Microsoft Graph integration
- SharePoint storage
- scheduled processing
- centralized logging
- app-only authentication