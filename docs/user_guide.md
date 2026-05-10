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

The tool does not yet:
- Send emails
- Retrieve billing addresses from the API


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
- Retrieve billing address from the FieldPulse platform API
- Potentially enrich customer/account data before PDF generation

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
The PDF generation module now supports structured renewal notice rendering.

The current layout includes:
- Renewal notice header
- Account information
- Customer information
- Service address
- Agreement details
- Payment details

Branding, logos, and final styling are still in development.


## PDF Naming Convention
Renewal notice PDFs use the following naming format:
    '{yymm}-renewal-{agreement_id}-{customer_name}.pdf'

Example:
    '2606-renewal-13661-grace-recovery-and-wellness.pdf'

Filename details:
- 'yymm' is based on the agreement expiration date
- 'agreement_id' is the renewal agreement number
- 'customer_name' is normalized into filesystem-safe text
- Special characters and spaces are converted to hyphens


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
- status

This provides a basic audit trail for each processing run.


## PDF Detail Log
Each generated PDF is recorded in:
    'logs/pdf_detail.csv;

The log includes:
- run timestamp
- source CSV file
- location
- agreement ID
- account number
- customer name
- PDF path
- status

This provides a record-level audit trail for each generated renewal notice.


## Renewal Notice Message
Each PDF includes a short customer-facing message explaining that the customer's maintenance agreement is coming up for renewal.

## Remittance Section
Each renewal notice includes a detachable remittance section for customers mailing payment by check.

The remittance section includes:
- account number
- agreement number
- customer name
- payment due date
- amount due