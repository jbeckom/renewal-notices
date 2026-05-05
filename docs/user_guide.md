## Input Files

Monthly renewal exports should be saved as CSV files in:

'data/incoming'

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
- Zip Code
- SCA End Date
- Title
- Total Annual Fee

If any required column is missing, the file will be skipped and logged.


## Renewal Record Mapping

Each valid CSV row is converted into a clean renewal record before any PDFs are generated.

| Renewal Record Field | Source |
|---|---|
| location | Fieldname: 'an' or 'mu' |
| run_date | Current system date |
| account_number | Customer #, with '#' removed |
| agreement_id | #ID, with '#' removed |
| customer_name | Customer Company Name, or First + Last Name |
| service_address | Location Address, City, State, Zip Code |
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


## Data Normalization

Certain placeholder values in the source data are treated as empty:
- '-'
- blank values
- null/NaN values

This prevents placeholder data from appearing on renewal notices.