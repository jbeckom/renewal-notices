# Renewal Notice Automation
Automates the generation of branded renewal notice PDFs for Summers Plumbing Heating & Cooling maintenance agreements.


## Features
- CSV import and validation
- Renewal record normalization
- Branded PDF generation
- FieldPulse API enrichment
- Billing Address overrides
- Structured CSV logging
- Organized output directories
- Automatic source file archiving
- Email queue generation
- Microsoft Graph authentication
- Shared mailbox integration
- Batch Outlook draft generation
- PDF attachment support for draft messages
- Email draft logging
- HTML email template support
- Outlook draft generation via Microsoft Graph
- PDF attachment support
- Batch draft creation
- Email draft logging
- HTML email template rendering
- Batch Outlook draft generation
- Email draft logging
- Draft processing summaries
- Draft review workflow
- Notice window processing (30/60/90 day renewals)
- Print queue generation
- Support for email-only, print-only, and email-and-print delivery workflows


## Requirements
- Python 3.14+
- FieldPulse API access


## Setup
1. Clone repository
2. Create virtual environment
3. Install requirements
4. Configure `.env`
5. Place renewal CSV files in `data/incoming`
6. Run `python src/main.py`


## Documentation

Project documentation:

- `docs/user_guide.md`
- `docs/architecture.md`

Purpose:

- user_guide.md → operational usage
- architecture.md → system design and implementation


## Current Status

Current production capabilities:

- CSV processing
- FieldPulse API enrichment
- PDF generation
- Logging
- Email queue generation

Current development capabilities:

- Microsoft Graph authentication
- Shared mailbox access
- Outlook draft creation
- PDF attachment support
- Batch draft generation from email queue records
- Email draft logging

Email delivery automation is currently under development.

## Environment Variables
Sensitive configuration values are stored in:
- `.env`

The repository also includes:
- `.env.example`

Environment variables currently support:

FieldPulse:
- FieldPulse API base URL
- FieldPulse API keys

Microsoft Graph:
- Tenant ID
- Client ID
- Shared mailbox address


## Quick Start

```bash
python src/main.py
```

The application will:

1. Process renewal CSV files in `data/incoming`
2. Generate renewal notice PDFs
3. Create processing logs
4. Create email queue records
5. Archive processed source files
```