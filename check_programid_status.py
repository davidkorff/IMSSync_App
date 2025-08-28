#!/usr/bin/env python3
"""
Script to check ProgramID status after a bind transaction.
This queries the database to see what actually happened.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ims.data_access_service import get_data_access_service
from app.services.ims.auth_service import get_auth_service

def check_recent_binds():
    """Check recent bind transactions for ProgramID status."""
    print("\n" + "="*80)
    print("Checking Recent Bind Transactions for ProgramID Status")
    print("="*80)
    
    # Initialize services
    data_service = get_data_access_service()
    auth_service = get_auth_service()
    
    # Authenticate
    print("\nAuthenticating...")
    auth_success, auth_message = auth_service.login()
    if not auth_success:
        print(f"❌ Authentication failed: {auth_message}")
        return False
    print("✓ Authentication successful")
    
    # Query to check recent bind transactions
    # We'll use ExecuteDataSet to get the raw data
    query_params = [
        "query_type", "recent_binds"
    ]
    
    print("\nExecuting query to check recent bind transactions...")
    
    # Use a custom stored procedure or query
    # For now, let's check the most recent quotes
    success, result_xml, message = data_service.execute_dataset(
        "spGetRecentTritonQuotes",
        []
    )
    
    if not success:
        print(f"Note: spGetRecentTritonQuotes not found, trying alternative method")
        
        # Alternative: Check a specific quote if we know the GUID
        print("\nEnter a Quote GUID to check (or press Enter to skip): ", end="")
        quote_guid = input().strip()
        
        if quote_guid:
            check_specific_quote(data_service, quote_guid)
    else:
        print(f"Query result: {result_xml[:500] if result_xml else 'No results'}")
    
    return True

def check_specific_quote(data_service, quote_guid):
    """Check a specific quote for ProgramID details."""
    print(f"\nChecking Quote: {quote_guid}")
    print("-" * 40)
    
    # Query to check the specific quote details
    # We'll create a wrapper stored procedure for this
    params = [
        "QuoteGuid", quote_guid
    ]
    
    success, result_xml, message = data_service.execute_dataset(
        "spCheckQuoteProgramID",
        params
    )
    
    if not success:
        print(f"Note: spCheckQuoteProgramID not found")
        print("The stored procedure needs to be created to check ProgramID status")
        print("\nCreate this stored procedure in SQL Server:")
        print(get_check_procedure_sql())
    else:
        # Parse and display the results
        if result_xml:
            print(f"Results: {result_xml}")

def get_check_procedure_sql():
    """Get the SQL for the checking stored procedure."""
    return """
CREATE OR ALTER PROCEDURE [dbo].[spCheckQuoteProgramID]
    @QuoteGuid UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Check the quote details and ProgramID
    SELECT 
        -- Quote info
        q.QuoteGuid,
        q.ControlNo,
        q.PolicyNumber,
        q.AccountNumber,
        q.CompanyLineGuid,
        
        -- Triton data
        tqd.market_segment_code,
        tqd.class_of_business,
        tqd.program_name,
        tqd.transaction_type,
        tqd.opportunity_id,
        
        -- Quote details
        qd.ProgramID,
        qd.QuoteDetailsID,
        
        -- Expected ProgramID based on rules
        CASE 
            WHEN tqd.market_segment_code = 'RT' AND q.CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 11615
            WHEN tqd.market_segment_code = 'WL' AND q.CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 11613
            WHEN tqd.market_segment_code = 'RT' AND q.CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 11612
            WHEN tqd.market_segment_code = 'WL' AND q.CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 11614
            ELSE NULL
        END AS Expected_ProgramID,
        
        -- Check if it matches
        CASE 
            WHEN qd.ProgramID = 
                CASE 
                    WHEN tqd.market_segment_code = 'RT' AND q.CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 11615
                    WHEN tqd.market_segment_code = 'WL' AND q.CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 11613
                    WHEN tqd.market_segment_code = 'RT' AND q.CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 11612
                    WHEN tqd.market_segment_code = 'WL' AND q.CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 11614
                    ELSE NULL
                END
            THEN 'MATCH'
            WHEN qd.ProgramID IS NULL THEN 'NOT SET'
            ELSE 'MISMATCH'
        END AS Status,
        
        -- Dates
        tqd.created_date,
        tqd.last_updated
        
    FROM tblQuotes q
    LEFT JOIN tblTritonQuoteData tqd ON tqd.QuoteGuid = q.QuoteGuid
    LEFT JOIN tblQuoteDetails qd ON qd.QuoteGuid = q.QuoteGuid
    WHERE q.QuoteGuid = @QuoteGuid;
END
GO

GRANT EXECUTE ON spCheckQuoteProgramID TO [IMS_User];
GO

-- Also create one to check recent binds
CREATE OR ALTER PROCEDURE [dbo].[spGetRecentTritonQuotes]
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT TOP 10
        -- Quote info
        q.QuoteGuid,
        q.ControlNo,
        q.PolicyNumber,
        q.CompanyLineGuid,
        
        -- Triton data
        tqd.market_segment_code,
        tqd.transaction_type,
        tqd.opportunity_id,
        tqd.insured_name,
        
        -- Quote details
        qd.ProgramID,
        
        -- Expected ProgramID
        CASE 
            WHEN tqd.market_segment_code = 'RT' AND q.CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 11615
            WHEN tqd.market_segment_code = 'WL' AND q.CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 11613
            WHEN tqd.market_segment_code = 'RT' AND q.CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 11612
            WHEN tqd.market_segment_code = 'WL' AND q.CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 11614
            ELSE NULL
        END AS Expected_ProgramID,
        
        -- Status
        CASE 
            WHEN qd.ProgramID IS NULL THEN 'NOT SET'
            WHEN qd.ProgramID = 
                CASE 
                    WHEN tqd.market_segment_code = 'RT' AND q.CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 11615
                    WHEN tqd.market_segment_code = 'WL' AND q.CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 11613
                    WHEN tqd.market_segment_code = 'RT' AND q.CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 11612
                    WHEN tqd.market_segment_code = 'WL' AND q.CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 11614
                    ELSE NULL
                END
            THEN 'MATCH'
            ELSE 'MISMATCH'
        END AS Status,
        
        tqd.created_date
        
    FROM tblTritonQuoteData tqd
    INNER JOIN tblQuotes q ON q.QuoteGuid = tqd.QuoteGuid
    LEFT JOIN tblQuoteDetails qd ON qd.QuoteGuid = q.QuoteGuid
    WHERE tqd.transaction_type IN ('bind', 'midterm_endorsement', 'cancellation', 'reinstatement')
    ORDER BY tqd.created_date DESC;
END
GO

GRANT EXECUTE ON spGetRecentTritonQuotes TO [IMS_User];
GO
"""

def main():
    """Main function."""
    print("\nProgramID Status Checker")
    print("This script checks if ProgramID is being set correctly")
    
    # Check if a specific quote GUID was provided
    if len(sys.argv) > 1:
        quote_guid = sys.argv[1]
        print(f"\nChecking specific quote: {quote_guid}")
        
        data_service = get_data_access_service()
        auth_service = get_auth_service()
        
        auth_success, _ = auth_service.login()
        if auth_success:
            check_specific_quote(data_service, quote_guid)
    else:
        print("\nUsage: python check_programid_status.py [quote_guid]")
        print("\nFrom your test output, the Quote GUID is: d5f59086-799d-4c23-9b6a-e73cec18b37f")
        print("Run: python check_programid_status.py d5f59086-799d-4c23-9b6a-e73cec18b37f")
        
        # Also check recent binds
        check_recent_binds()
    
    return 0

if __name__ == "__main__":
    exit(main())