## Current Capabilities
The tool currently:
- Detects renewal CSV files in the input directory
- Validates required columns
- Normalizes and cleans source data
- Converts each row into a structured renewal record

The tool does not yet:
- Generate PDF notices
- Send emails
- Retrieve billing addresses from the API


## Planned Enhancements

- PDF Generation using company letterhead
- Email delivery of renewal notices
- API integration to retireve billing addresses
- Logging and exception reporting


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


