#!/usr/bin/env python3
"""
Check what quotes exist for an opportunity_id
"""
import sys
sys.path.append('/opt/IMSSync_App')

from app.services.ims.auth_service import get_auth_service
from app.services.ims.data_access_service import get_data_access_service

def check_opportunity_quotes(opportunity_id):
    """Check all quotes for an opportunity"""
    
    # Initialize services
    auth_service = get_auth_service()
    data_service = get_data_access_service()
    
    # Authenticate
    success, user_guid, message = auth_service.authenticate()
    if not success:
        print(f"Authentication failed: {message}")
        return
    
    print(f"Checking quotes for opportunity_id: {opportunity_id}")
    print("=" * 80)
    
    # Check tblTritonQuoteData
    query = f"""
        SELECT 
            tq.QuoteGuid,
            tq.QuoteOptionGuid,
            tq.transaction_type,
            tq.status,
            tq.policy_number,
            tq.created_date,
            tq.gross_premium,
            q.QuoteStatusID,
            q.ControlNo,
            q.PolicyNumber as QPolicyNumber,
            q.EndorsementNum,
            q.TransactionTypeID
        FROM tblTritonQuoteData tq
        LEFT JOIN tblQuotes q ON q.QuoteGUID = tq.QuoteGuid
        WHERE tq.opportunity_id = {opportunity_id}
        ORDER BY tq.created_date DESC
    """
    
    try:
        # Execute query
        success, result_xml, message = data_service.execute_dataset(
            "spExecuteSQL",
            ["SQL", query]
        )
        
        if success and result_xml:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(result_xml)
            tables = root.findall('.//Table')
            
            if tables:
                print(f"Found {len(tables)} quote(s) in tblTritonQuoteData:")
                print()
                
                for i, table in enumerate(tables, 1):
                    print(f"Quote #{i}:")
                    for child in table:
                        if child.text:
                            print(f"  {child.tag}: {child.text.strip()}")
                    print("-" * 40)
            else:
                print("No quotes found in tblTritonQuoteData")
        else:
            print(f"Query failed: {message}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Also check for the latest quote in chain
    print("\nFinding latest quote in chain...")
    success, result_xml, message = data_service.execute_dataset(
        "spGetLatestQuoteByOpportunityID",
        ["OpportunityID", str(opportunity_id)]
    )
    
    if success and result_xml:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(result_xml)
        table = root.find('.//Table')
        
        if table:
            print("Latest quote in chain:")
            for child in table:
                if child.text:
                    print(f"  {child.tag}: {child.text.strip()}")
        else:
            print("No latest quote found")
    else:
        print(f"Failed to get latest quote: {message}")

if __name__ == "__main__":
    import sys
    opportunity_id = 106208
    if len(sys.argv) > 1:
        opportunity_id = int(sys.argv[1])
    
    check_opportunity_quotes(opportunity_id)