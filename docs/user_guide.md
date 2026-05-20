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

The tool does not yet:
- Send emails


## Planned Enhancements
Future improvements planned for the renewal notice automation system include:

### Exception Handling
- Gracefully handle malformed CSV files
- Handle missing required data fields
- Capture PDF generation failures
- Continue processing remaining records when possible

### Exception Logging
- Log record-level processing failures
- Log PDF generation errors
- Track skipped records and reasons
- Create exception reports for manual follow-up

### API Enrichment
- Retrieve additional customer/account metadata
- Support deeper account validation
- Potentially enrich agreement-level data

### Email Automation
- Generate standardized renewal email bodies
- Attach renewal PDFs automatically
- Support review/approval workflows before send
- Track send statuses and failures

### Cloud Migration
- Migrate processing workflow to AWS
- Integrate with SharePoint document storage
- Automate scheduled renewal processing


## Input Files
Monthly renewal exports should be saved as CSV files in:
- 'data/incoming'

The filename should include the location code:
- 'an' for Anderson
- 'mu' for Muncie

Example filenames:
- 'sca-renewals-an-2606.csv'
- 'sca-renewals-mu-2606.csv'


## Environment Variables
Sensitive configuration values are stored in:
- '.env'

The repository also includes:
- '.env.example'

Environment variables currently support:
- FieldPulse API base URL
- FieldPulse API keys


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


## Record Processing
After validation, each row in the CSV file is converted into a renewal record.
The total number of records created should match the number of rows in the CSV file.
This ensures all customers in the export are processed.


## Renewal Record Mapping
Each valid CSV row is converted into a clean renewal record before any PDFs are generated.

| Renewal Record Field | Source |
|---|---|
| location | Derived from filename: 'an' or 'mu' |
| run_date | Current system date |
| account_number | Customer #, with '#' removed |
| agreement_id | #ID, with '#' removed |
| customer_name | Customer Company Name, or First + Last Name |
| service_address | Location Address, City, State, ZIP Code |
| billing_address | Reserved for future API enrichment |
| agreement_type | Title |
| expiration_date | SCA End Date |
| coverage_through | SCA End Date + 1 year |
| payment_due_date | SCA End Date |
| total_price | Total Annual Fee |


## Customer Name Formatting
Customer names are formatted as follows:

- If a company name exists:
    'Company Name'
    'Attn: First Last'

- If no company name exists:
    'First Last'


## Service Address Formatting
The export's 'Location Address' field contains the full address, including city, state, and ZIP Code.
To avoid duplicate address lines, the tool extracts only the street address from 'Location Address', then uses the separate 'City', 'State', and 'ZIP Code' fields for the second line.


## Data Normalization
Certain placeholder values in the source data are treated as empty:
- '-'
- blank values
- null/NaN values

This prevents placeholder data from appearing on renewal notices.


## Structured PDF Generation
The PDF generation module now supports branded, structured renewal notice rendering.

The current layout includes:
- company logo and branding
- company contact information
- renewal notice title
- account information
- customer and service address section
- customer-facing renewal message
- agreement details
- payment details
- detachable remittance section


## PDF Naming Convention
Renewal notice PDFs use the following naming format:
    '{yymm}-renewal-{location}-{agreement_id}-{customer_name}.pdf'

Example:
    '2606-renewal-an-13661-grace-recovery-and-wellness.pdf'

Filename details:
- 'yymm' is based on the agreement expiration date
- 'agreement_id' is the renewal agreement number
- 'customer_name' is normalized into filesystem-safe text
- Special characters and spaces are converted to hyphens


## Output Directory Structure
Renewal notice PDFs are organized by renewal cycle and location.

Structure:
- 'output/{yymm}/{location}'

Examples:
- 'output/2606/an/'
- 'output/2606/mu'


## PDF Batch Generation
After validation and record creation, the application generates one PDF renewal notice for each renewal record.

The number of PDFs created should match the number of records created from the CSV file.


## Run Summary Log
Each processed CSV file is recorded in:
    'logs/run_summary.csv'

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
    'logs/pdf_detail.csv'

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


## Renewal Notice Message
Each PDF includes a short customer-facing message explaining that the customer's maintenance agreement is coming up for renewal.


## Billing Address API Enrichment
During processing, each renewal record is checked against the FieldPulse API.

If FieldPulse indicates that the customer has a different billing address, the renewal notice uses the billing address in the customer/mailing address section.

If no different billing address exists, the renewal notice uses the service address from the CSV export.

The service address is always shown separately on the renewal notice.


## Renewal Notice Layout Updates
The renewal notice PDF now includes:
- Company logo branding
- Mailing address override support from FieldPulse
- Separate mailing and service address sections
- Condensed agreement/payment summary layout
- Remittance/payment return section
- "Make checks payable to" support using company legal entity name

The PDF layout is optimized for standard tri-fold mailing and window envelopes.

## Remittance Section
The renewal notice includes a detachable remittance/payment section designed for mailed payments.

Current remittance features include:
- Account number
- Agreement number
- Customer name
- Service address
- Amount due
- Payment method selection
- Check payment information
- Driver's license verification fields
- Credit card entry fields
- Payable-to information


## Window Envelope Alignment
The renewal notice layout is adjusted for standard tri-fold mailing and window envelope visibility.

The customer/mailing address section is positioned so the mailing address appears in the envelope window when folded.


## PDF Layout Testing
'pdf_generator.py' includes a standalone testing block using a hardcoded sample record.

This allows rapid iteration of:
- PDF layout
- Window envelope alignment
- Logo sizing
- Remittance formatting
- Payment field spacing

without processing full renewal batches.


## Exception logging
Processing exceptions are recorded in:
    'logs/exception_log.csv'

The log includes:
- run timestamp
- source CSV file
- location
- processing stage
- agreement ID
- account number
- customer name
- error message

Current logged excpetion stages include:
- 'API_ENRICHMENT'
- 'PDF_GENERATION'

If API enrichment fails for a record, the system continues processing and generates the renewal notice using the CSV-derived service address.

If PDF generation fails for a record, the system logs the failure and continues processing the remaining records.