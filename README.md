# Renewal Notice Automation
Automates the generation of branded renewal notice PDFs for Summers Plumbing Heating & Cooling maintenance agreements.


## Features
- Validates FieldPulse renewal export files
- Builds standardized renewal notice records
- Enriches customer records using FIeldPulse API
- Generates renewal notice PDFs
- Supports billing-address overrides
- Determines notice windows (`90_DAY`, `60_DAY`, `30_DAY`)
- Routes records by delivery action:
    - `EMAIL_ONLY`
    - `PRINT_MAIL`
    - `EMAIL_AND_PRINT`
- Generates email and print queues
- Creates Outlook draft emails via Microsoft Graph
- Logs draft creation activity
- Generates merged print batches and print manifests
- Supports draft reveiew workflow prior to sending


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

Completed:

- PDF generation
- FieldPulse API enrichment
- Billing-address override handling
- Notice-window processing
- Email queue generation
- Print queue generation
- Outlook draft creation
- HTML email templates
- Draft review workflow
- Print batch processor
- Print manifest generation
- Unknown-location guardrails

In Progress:

- Duplicate draft prevention
- Draft visibility verification
- Automated sending guardrails

Future:

- Automated email sending
- SharePoint integration
- Web UI
- Cloud hosting


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
