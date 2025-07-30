#!/usr/bin/env python3
"""
Standalone test script for bind transaction - no external dependencies
"""
import os
import sys
import json
from datetime import datetime
from uuid import UUID
import logging
from zeep import Client, Settings
from zeep.transports import Transport

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Configuration
IMS_CONFIG = {
    "endpoints": {
        "base_url": "http://10.64.32.234/ims_one",
        "services": {
            "logon": "/logon.asmx?WSDL",
            "insured_functions": "/insuredfunctions.asmx?WSDL",
            "quote_functions": "/quotefunctions.asmx?WSDL"
        }
    },
    "credentials": {
        "username": os.getenv("IMS_ONE_USERNAME"),
        "password": os.getenv("IMS_ONE_PASSWORD"),
    }
}

# Default GUIDs
DEFAULT_GUIDS = {
    "producer": "895E9291-CFB6-4299-8799-9AF77DF937D6",
    "underwriter": "E4391D2A-58FB-4E2D-8B7D-3447D9E18C88",
    "company_location": "DF35D4C7-C663-4974-A886-A1E18D3C9618",
    "line": "07564291-CBFE-4BBE-88D1-0548C88ACED4"
}

def authenticate():
    """Authenticate with IMS"""
    url = IMS_CONFIG["endpoints"]["base_url"] + IMS_CONFIG["endpoints"]["services"]["logon"]
    client = Client(url, settings=Settings(strict=False, xml_huge_tree=True))
    
    response = client.service.LoginIMSUser(
        username=IMS_CONFIG["credentials"]["username"],
        password=IMS_CONFIG["credentials"]["password"]
    )
    
    # Extract token
    token = str(response.Token) if hasattr(response, 'Token') else str(response)
    print(f"Authentication successful. Token: {token}")
    return token

def create_insured(token, data):
    """Create insured with location"""
    url = IMS_CONFIG["endpoints"]["base_url"] + IMS_CONFIG["endpoints"]["services"]["insured_functions"]
    client = Client(url, settings=Settings(strict=False, xml_huge_tree=True))
    
    insured = {
        'BusinessTypeID': 9,  # LLC - Partnership
        'CorporationName': data["insured_name"],
        'Salutation': '',
        'FirstName': '',
        'MiddleName': '',
        'LastName': '',
        'NameOnPolicy': data["insured_name"],
        'DBA': '',
        'FEIN': '',
        'SSN': '',
        'DateOfBirth': None,
        'RiskId': '',
        'Office': "00000000-0000-0000-0000-000000000000"
    }
    
    location = {
        'InsuredGuid': "00000000-0000-0000-0000-000000000000",
        'LocationName': 'Primary',
        'Address1': data["address_1"],
        'Address2': data.get("address_2", ""),
        'City': data["city"],
        'County': '',
        'State': data["state"],
        'Zip': data["zip"],
        'ZipPlus': '',
        'ISOCountryCode': 'US',
        'Region': '',
        'Phone': '',
        'Fax': '',
        'Email': '',
        'Website': '',
        'DeliveryMethodID': 1,
        'LocationTypeID': 1,
        'MobileNumber': '',
        'OptOut': False
    }
    
    header = {'TokenHeader': {'Token': token, 'Context': ''}}
    response = client.service.AddInsuredWithLocation(
        insured=insured,
        location=location,
        _soapheaders=header
    )
    
    insured_guid = UUID(str(response))
    print(f"Created insured: {insured_guid}")
    return insured_guid

def create_quote(token, insured_guid, data):
    """Create submission and quote"""
    url = IMS_CONFIG["endpoints"]["base_url"] + IMS_CONFIG["endpoints"]["services"]["quote_functions"]
    client = Client(url, settings=Settings(strict=False, xml_huge_tree=True))
    
    # Convert dates
    effective_date = datetime.strptime(data["effective_date"], "%m/%d/%Y").strftime("%Y-%m-%d")
    expiration_date = datetime.strptime(data["expiration_date"], "%m/%d/%Y").strftime("%Y-%m-%d")
    
    submission = {
        'Insured': str(insured_guid),
        'ProducerContact': DEFAULT_GUIDS["producer"],
        'Underwriter': DEFAULT_GUIDS["underwriter"],
        'SubmissionDate': datetime.now().strftime("%Y-%m-%d"),
        'ProducerLocation': DEFAULT_GUIDS["producer"],
        'TACSR': "00000000-0000-0000-0000-000000000000",
        'InHouseProducer': "00000000-0000-0000-0000-000000000000"
    }
    
    quote = {
        'Submission': "00000000-0000-0000-0000-000000000000",
        'QuotingLocation': DEFAULT_GUIDS["company_location"],
        'IssuingLocation': DEFAULT_GUIDS["company_location"],
        'CompanyLocation': DEFAULT_GUIDS["company_location"],
        'Line': DEFAULT_GUIDS["line"],
        'StateID': data["state"],
        'ProducerContact': DEFAULT_GUIDS["producer"],
        'QuoteStatusID': 1,
        'Effective': effective_date,
        'Expiration': expiration_date,
        'BillingTypeID': 1,
        'FinanceCompany': "00000000-0000-0000-0000-000000000000",
        'NetRateQuoteID': 0,
        'QuoteDetail': {
            'CompanyCommission': data.get("commission_rate", 17.5) / 100,
            'ProducerCommission': data.get("commission_rate", 17.5) / 100,
            'TermsOfPayment': 1,
            'ProgramCode': '',
            'CompanyContactGuid': "00000000-0000-0000-0000-000000000000",
            'RaterID': 0,
            'FactorSetGuid': "00000000-0000-0000-0000-000000000000",
            'ProgramID': 0,
            'LineGUID': DEFAULT_GUIDS["line"],
            'CompanyLocationGUID': DEFAULT_GUIDS["company_location"]
        },
        'ExpiringQuoteGuid': "00000000-0000-0000-0000-000000000000",
        'Underwriter': DEFAULT_GUIDS["underwriter"],
        'ExpiringPolicyNumber': "",
        'ExpiringCompanyLocationGuid': "00000000-0000-0000-0000-000000000000",
        'PolicyTypeID': 1,
        'RenewalOfQuoteGuid': "00000000-0000-0000-0000-000000000000",
        'InsuredBusinessTypeID': 9,
        'AccountNumber': "",
        'AdditionalInformation': [],
        'OnlineRaterID': 0,
        'CostCenterID': 0,
        'ProgramCode': '',
        'RiskInformation': {
            'PolicyName': data["insured_name"],
            'CorporationName': data["insured_name"],
            'DBA': None,
            'Salutation': None,
            'FirstName': None,
            'MiddleName': None,
            'LastName': None,
            'SSN': None,
            'FEIN': None,
            'Address1': data["address_1"],
            'Address2': data.get("address_2", None),
            'City': data["city"],
            'State': data["state"],
            'ISOCountryCode': "US",
            'Region': None,
            'ZipCode': data["zip"],
            'ZipPlus': None,
            'Phone': None,
            'Fax': None,
            'Mobile': None,
            'BusinessType': 9
        },
        'ProgramID': 0
    }
    
    header = {'TokenHeader': {'Token': token, 'Context': ''}}
    response = client.service.AddQuote(
        submission=submission,
        quote=quote,
        _soapheaders=header
    )
    
    quote_guid = UUID(str(response))
    print(f"Created quote: {quote_guid}")
    return quote_guid

def bind_quote(token, quote_guid):
    """Bind a quote"""
    url = IMS_CONFIG["endpoints"]["base_url"] + IMS_CONFIG["endpoints"]["services"]["quote_functions"]
    client = Client(url, settings=Settings(strict=False, xml_huge_tree=True))
    
    header = {'TokenHeader': {'Token': token, 'Context': ''}}
    
    # Fixed: BindQuote only accepts quoteGuid parameter
    response = client.service.BindQuote(
        quoteGuid=str(quote_guid),
        _soapheaders=header
    )
    
    print(f"Bind response: {response}")
    return response

def main():
    """Main test function"""
    # Load test data
    with open("TEST.json", "r") as f:
        test_data = json.load(f)
    
    try:
        # Step 1: Authenticate
        print("\n=== Step 1: Authenticating ===")
        token = authenticate()
        
        # Step 2: Create insured
        print("\n=== Step 2: Creating Insured ===")
        insured_guid = create_insured(token, test_data)
        
        # Step 3: Create quote
        print("\n=== Step 3: Creating Quote ===")
        quote_guid = create_quote(token, insured_guid, test_data)
        
        # Step 4: Bind quote
        print("\n=== Step 4: Binding Quote ===")
        bind_result = bind_quote(token, quote_guid)
        
        print("\n=== SUCCESS! ===")
        print(f"Policy bound successfully!")
        print(f"Policy GUID: {bind_result}")
        
    except Exception as e:
        print(f"\n=== ERROR ===")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()