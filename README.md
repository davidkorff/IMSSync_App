# IMS Integration

This project provides tools to integrate bound policy data from external sources into the IMS (Insurance Management System) platform.

## Overview

The integration allows importing bound policy data from various sources (like Tritan, Xuber, CSV files, APIs, SFTP, etc.) and creating submissions and quotes in IMS through its SOAP web services.

## Architecture

The integration follows a modular architecture:

1. **Source-specific Data Gatherers**: Each source system (Tritan, Xuber, CSV, etc.) has its own data gatherer that handles the specifics of connecting to and retrieving data from that source.

2. **Common Data Model**: All data gatherers transform the source data into a common PolicyData model.

3. **IMS Integration Layer**: The core integration layer takes the common data model and interacts with IMS APIs.

## Components

- **ims_integration.py**: Main integration module that works with data from any source
- **ims_soap_client.py**: Handles SOAP XML request/response processing
- **ims_lookup_service.py**: Provides entity lookup functionality and caching
- **ims_data_model.py**: Common data model for policy data
- **data_gatherers/**: Package containing source-specific data gatherers
  - **base_gatherer.py**: Abstract base class for all data gatherers
  - **csv_gatherer.py**: Data gatherer for CSV files
  - **tritan_gatherer.py**: Data gatherer for Tritan insurance system
- **run_ims_integration.py**: Command-line interface for running the integration
- **config.py**: Configuration settings for different environments
- **OutstandingQuestions.txt**: Tracking document for open questions and issues

## Requirements

- Python 3.6+
- Required packages: requests, python-dateutil

## Usage

To run the integration with a CSV data source:

```bash
python run_ims_integration.py --env=iscmga_test --source=csv --file=BDX_Samples/Bound\ Policies\ report\ 4.25.25.csv
```

To run the integration with Tritan as a data source:

```bash
python run_ims_integration.py --env=iscmga_test --source=tritan --config=tritan_config.json
```

Command-line options:

- `--env`: Environment to use (iscmga_test, ims_one)
- `--source`: Source system to gather data from (csv, tritan, etc.)
- `--file`: Path to the CSV file (required for CSV source)
- `--config`: Path to source system configuration file (required for API sources)
- `--start-date`: Start date for policy search (YYYY-MM-DD)
- `--end-date`: End date for policy search (YYYY-MM-DD)
- `--policy-number`: Specific policy number to retrieve
- `--output`: Path to the output JSON file for results
- `--debug`: Enable debug logging
- `--limit`: Limit the number of policies to process

## Data Model

The integration uses a common data model (PolicyData) that includes:

- Policy Identification: policy number, program, line of business
- Dates: effective date, expiration date, bound date
- Insured Information: name, address, contact details
- Parties: producer, underwriter, locations
- Policy Details: limits, deductibles, commission
- Financial Information: premium
- Additional Data: source-specific information

## Adding a New Data Source

To add support for a new data source:

1. Create a new data gatherer class in the `data_gatherers` package that inherits from `BaseDataGatherer`
2. Implement the required methods: `connect()`, `disconnect()`, and `get_policies()`
3. Register the new gatherer in `data_gatherers/__init__.py`

## Development

To add support for a new data source:
1. Create a new data gatherer class that inherits from BaseDataGatherer
2. Implement the required methods to extract policy data
3. Register the gatherer in the data_gatherers/__init__.py file

## Configuration

Edit the `config.py` file to update environment settings and credentials.

```python
ENVIRONMENTS = {
    "ims_one": {
        "config_file": "IMS_ONE.config",
        "username": "your_username",
        "password": "encrypted_password"
    },
    "iscmga_test": {
        "config_file": "ISCMGA_Test.config",
        "username": "your_username",
        "password": "encrypted_password"
    }
}
```

For source-specific configuration (like Tritan), create a JSON configuration file:

```json
{
  "api_url": "https://api.tritan.example.com",
  "api_key": "your-api-key",
  "username": "your-username",
  "password": "your-password"
}
```

## Data Mapping

The integration maps the following data from source systems to IMS:

### Authentication Data
- Username
- Password (triple DES encrypted)

### Submission Data
- Insured (guid)
- ProducerContact (guid)
- Underwriter (guid)
- SubmissionDate (date)
- ProducerLocation (guid)
- TACSR (guid) - Technical Assistant/Customer Service Rep
- InHouseProducer (guid)

### Quote Data
- Submission (guid - created from submission data)
- QuotingLocation (guid)
- IssuingLocation (guid)
- CompanyLocation (guid)
- Line (guid)
- StateID (string)
- ProducerContact (guid)
- QuoteStatusID (int)
- Effective (date)
- Expiration (date)
- BillingTypeID (int)
- FinanceCompany (guid)

### Quote Detail
- CompanyCommission (decimal)
- ProducerCommission (decimal)
- TermsOfPayment (int)
- ProgramCode (string)
- CompanyContactGuid (guid)
- RaterID (int)
- FactorSetGuid (guid)
- ProgramID (int)
- LineGUID (guid)
- CompanyLocationGUID (guid)

### Risk Information
- PolicyName (string)
- CorporationName (string)
- DBA (string)
- Contact details (Name, Address, etc.)
- Tax identifiers (SSN/FEIN)
- Contact information (Phone, Fax, etc.)
- BusinessType (int)
