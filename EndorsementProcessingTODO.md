# Endorsement Processing Refactor TODO

## Overview
Refactor the midterm_endorsement transaction_type routing to properly handle endorsements by:
1. Finding the latest quote in the chain using opportunity_id
2. Calculating total existing premium from invoices
3. Using ProcessFlatEndorsement stored procedure to create unbound endorsement
4. Applying fees and binding the endorsement

## Key Issues with Current Implementation
- Current flow doesn't properly find the latest quote in the chain
- Doesn't calculate total existing premium from all invoices
- Uses Triton_EndorsePolicy_WS instead of ProcessFlatEndorsement
- Doesn't properly handle the quote chain (QuoteGuid -> OriginalQuoteGuid relationships)

## Required SQL Components

### 1. Create spGetLatestQuoteByOpportunityID_WS
**Purpose**: Find the latest quote in a chain by opportunity_id
```sql
CREATE OR ALTER PROCEDURE [dbo].[spGetLatestQuoteByOpportunityID_WS]
    @OpportunityID INT
AS
BEGIN
    -- Get the most recent quote from tblTritonQuoteData for this opportunity
    DECLARE @InitialQuoteGuid UNIQUEIDENTIFIER;
    
    SELECT TOP 1 @InitialQuoteGuid = QuoteGuid
    FROM tblTritonQuoteData
    WHERE OpportunityID = @OpportunityID
    ORDER BY CreatedDate DESC;
    
    -- Now find the latest quote in the chain
    WITH QuoteChain AS (
        SELECT 
            QuoteGuid,
            OriginalQuoteGuid,
            ControlNo,
            PolicyNumber,
            QuoteStatusID,
            0 as Level
        FROM tblQuotes
        WHERE QuoteGuid = @InitialQuoteGuid
        
        UNION ALL
        
        SELECT 
            q.QuoteGuid,
            q.OriginalQuoteGuid,
            q.ControlNo,
            q.PolicyNumber,
            q.QuoteStatusID,
            qc.Level + 1
        FROM tblQuotes q
        INNER JOIN QuoteChain qc ON q.OriginalQuoteGuid = qc.QuoteGuid
    )
    SELECT TOP 1
        QuoteGuid,
        ControlNo,
        PolicyNumber,
        QuoteStatusID
    FROM QuoteChain
    ORDER BY Level DESC;
END
```

### 2. Create spGetPolicyPremiumTotal_WS
**Purpose**: Calculate total premium from all invoices for a policy
```sql
CREATE OR ALTER PROCEDURE [dbo].[spGetPolicyPremiumTotal_WS]
    @ControlNo INT
AS
BEGIN
    SELECT 
        ISNULL(SUM(AnnualPremium), 0) as TotalPremium,
        COUNT(*) as InvoiceCount
    FROM tblFin_Invoices
    WHERE QuoteControlNum = @ControlNo;
END
```

### 3. ProcessFlatEndorsement Already Exists
- Located at: `/sql/needforproduction/Prod migration/ProcessFlatEndorsement.sql`
- Returns NewQuoteGuid as OUTPUT parameter
- Creates endorsement in Status 9 (Unbound)
- Properly handles quote chain and endorsement numbers

## Python Code Changes Required

### 1. Add New Methods to data_access_service.py

```python
def get_latest_quote_by_opportunity_id(self, opportunity_id: int) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Get the latest quote in a chain by opportunity_id.
    First finds the most recent entry in tblTritonQuoteData,
    then follows the quote chain to find the latest.
    """
    
def get_policy_premium_total(self, control_no: int) -> Tuple[bool, float, str]:
    """
    Get the total premium from all invoices for a policy.
    """
```

### 2. Create New Endorsement Service Method

```python
def create_flat_endorsement(
    self,
    original_quote_guid: str,
    total_premium: float,
    effective_date: str,
    comment: str = "Midterm Endorsement"
) -> Tuple[bool, Dict[str, Any], str]:
    """
    Create a flat endorsement using ProcessFlatEndorsement stored procedure.
    Returns the new quote guid and other details.
    """
```

### 3. Refactor transaction_handler.py midterm_endorsement Route

The new flow should be:

1. **Find Latest Quote**
   - Call `get_latest_quote_by_opportunity_id(opportunity_id)`
   - This gets the latest quote in the chain

2. **Calculate Total Premium**
   - Get control_no from the latest quote
   - Call `get_policy_premium_total(control_no)` to get existing premium
   - Add payload's `midterm_endt_premium` to this total

3. **Create Flat Endorsement**
   - Extract `midterm_endt_effective_from` from payload
   - Call ProcessFlatEndorsement with:
     - @OriginalQuoteGuid = latest_quote_guid
     - @NewPremium = total_premium (existing + new)
     - @EndorsementEffectiveDate = midterm_endt_effective_from
   - This returns NewQuoteGuid

4. **Apply Fees (if needed)**
   - Check fee criteria and apply auto fees if necessary
   - Use existing fee application logic

5. **Process Payload**
   - Call `process_payload` with the new endorsement quote_guid
   - This registers the premium in the system

6. **Bind Endorsement**
   - Call `bind_quote` with the new endorsement quote_guid
   - This completes the endorsement

## Implementation Steps

1. **SQL Stored Procedures** (Priority: HIGH)
   - [ ] Create spGetLatestQuoteByOpportunityID_WS
   - [ ] Create spGetPolicyPremiumTotal_WS
   - [ ] Verify ProcessFlatEndorsement is deployed

2. **Python Service Layer** (Priority: HIGH)
   - [ ] Add get_latest_quote_by_opportunity_id to data_access_service.py
   - [ ] Add get_policy_premium_total to data_access_service.py
   - [ ] Add create_flat_endorsement to endorsement_service.py

3. **Transaction Handler Refactor** (Priority: HIGH)
   - [ ] Replace current midterm_endorsement logic (lines 196-308)
   - [ ] Implement new flow as described above
   - [ ] Ensure proper error handling at each step
   - [ ] Maintain backward compatibility for logs/results

4. **Testing** (Priority: HIGH)
   - [ ] Test with single endorsement
   - [ ] Test with multiple endorsements (chain)
   - [ ] Test premium calculations
   - [ ] Test fee applications
   - [ ] Test binding process

## Key Considerations

1. **Quote Chain Management**
   - The system maintains a chain: QuoteGuid -> OriginalQuoteGuid
   - Each endorsement creates a new quote pointing to the previous
   - We must find the LATEST in the chain to endorse

2. **Premium Calculation**
   - Must sum ALL invoices for the policy (tblFin_Invoices.AnnualPremium)
   - Add the new endorsement premium to this total
   - ProcessFlatEndorsement calculates the difference internally

3. **Status Management**
   - ProcessFlatEndorsement creates quote in Status 9 (Unbound)
   - Must bind after processing to complete the endorsement
   - Binding changes status and generates invoice

4. **Fee Application**
   - Check existing fee application criteria
   - Apply fees after endorsement creation but before binding
   - Use existing autoapply fee logic

## Files to Modify

1. `/sql/needforproduction/actaullyneed/spGetLatestQuoteByOpportunityID_WS.sql` (NEW)
2. `/sql/needforproduction/actaullyneed/spGetPolicyPremiumTotal_WS.sql` (NEW)
3. `/app/services/ims/data_access_service.py`
4. `/app/services/ims/endorsement_service.py`
5. `/app/services/transaction_handler.py`

## Success Criteria

- Endorsements properly find the latest quote in a chain
- Premium calculations include all existing invoices
- ProcessFlatEndorsement creates unbound endorsements
- Fees are properly applied based on criteria
- Endorsements are successfully bound
- Invoice data is generated and returned