# Quote Options Process

## Overview
The quote options service adds coverage options to an existing quote using the AutoAddQuoteOptions method.

## Service Details

### Endpoint
- **URL**: `POST http://10.64.32.234/ims_one/quotefunctions.asmx`
- **SOAPAction**: `http://tempuri.org/IMSWebServices/QuoteFunctions/AutoAddQuoteOptions`

### Request Structure
```xml
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <TokenHeader xmlns="http://tempuri.org/IMSWebServices/QuoteFunctions">
      <Token>{authentication_token}</Token>
      <Context>RSG_Integration</Context>
    </TokenHeader>
  </soap:Header>
  <soap:Body>
    <AutoAddQuoteOptions xmlns="http://tempuri.org/IMSWebServices/QuoteFunctions">
      <quoteGuid>{quote_guid}</quoteGuid>
    </AutoAddQuoteOptions>
  </soap:Body>
</soap:Envelope>
```

### Response Format
```xml
<AutoAddQuoteOptionsResponse xmlns="http://tempuri.org/IMSWebServices/QuoteFunctions">
    <AutoAddQuoteOptionsResult>
        <QuoteOption xmlns="http://ws.mgasystems.com/BusinessObjects">
            <QuoteOptionGuid>357487b6-4c81-4e00-8b6f-1b5975223a69</QuoteOptionGuid>
            <LineGuid>07564291-cbfe-4bbe-88d1-0548c88aced4</LineGuid>
            <LineName>AHC Primary</LineName>
            <CompanyLocation>Everest Indemnity Insurance Company</CompanyLocation>
        </QuoteOption>
    </AutoAddQuoteOptionsResult>
</AutoAddQuoteOptionsResponse>
```

## Extracted Data
The service extracts:
- **QuoteOptionGuid**: Unique identifier for the quote option
- **LineGuid**: GUID of the coverage line
- **LineName**: Name of the coverage line (e.g., "AHC Primary")
- **CompanyLocation**: Insurance company name

## Usage

### Import and Initialize
```python
from app.services.ims.quote_options_service import get_quote_options_service

# Get singleton instance
quote_options_service = get_quote_options_service()
```

### Add Quote Options
```python
# Add options to an existing quote
success, option_info, message = quote_options_service.auto_add_quote_options(quote_guid)

if success and option_info:
    quote_option_guid = option_info['QuoteOptionGuid']
    line_guid = option_info['LineGuid']
    line_name = option_info['LineName']
    company = option_info['CompanyLocation']
    
    print(f"Quote Option GUID: {quote_option_guid}")
    print(f"Line: {line_name} ({line_guid})")
    print(f"Company: {company}")
```

## Prerequisites
Before adding quote options, you must have:
1. Valid authentication token
2. Quote GUID from AddQuoteWithSubmission

## Workflow Integration
The quote options service is typically called after:
1. Finding/Creating Insured
2. Finding Producer
3. Finding Underwriter
4. Creating Quote
5. **Adding Quote Options** ← Current step

## Testing
Run the quote options test:
```bash
# Test complete workflow (all services)
python3 test_quote_options.py

# The test will orchestrate:
# - Authentication
# - Insured lookup/creation
# - Producer lookup
# - Underwriter lookup
# - Quote creation
# - Quote options addition
```

## Error Handling
The service handles:
- Invalid quote GUIDs
- Authentication failures
- Network errors
- XML parsing errors
- Missing quote options in response

## Next Steps
After obtaining the quote option GUID, you can:
- Add premium details
- Generate quote documents
- Proceed to binding
- Create invoices