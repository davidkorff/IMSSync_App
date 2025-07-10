# Custom IMS Web Service Stored Procedures

This folder contains custom stored procedures designed to be called through the IMS DataAccess web service. These procedures handle complex policy operations that are not directly available through the standard IMS web services.

## Prerequisites

1. These procedures must be deployed to the IMS database by MGA Systems or a database administrator
2. The procedures follow the "_WS" naming convention required for web service access
3. Appropriate permissions must be granted for the IMS web service user to execute these procedures

## Available Procedures

### 1. CancelPolicy_WS

Handles policy cancellation with full financial processing.

**Parameters:**
- `@ControlNumber` (INT) - Policy control number
- `@CancellationDate` (DATETIME) - Effective date of cancellation
- `@CancellationReasonID` (INT) - Reason code for cancellation
- `@Comments` (VARCHAR(2000)) - Optional comments
- `@UserGuid` (UNIQUEIDENTIFIER) - User performing the cancellation
- `@ReturnPremium` (BIT) - Whether to calculate return premium (default: 1)
- `@FlatCancel` (BIT) - If 1, no return premium calculated (default: 0)

**Returns:**
- QuoteID, PolicyNumber, NewStatusID, TransactionNumber, Message, Success flag

### 2. ReinstatePolicy_WS

Handles policy reinstatement after cancellation.

**Parameters:**
- `@ControlNumber` (INT) - Policy control number
- `@ReinstatementDate` (DATETIME) - Effective date of reinstatement
- `@ReinstatementReasonID` (INT) - Reason code (optional, defaults to 'REINST')
- `@Comments` (VARCHAR(2000)) - Optional comments
- `@UserGuid` (UNIQUEIDENTIFIER) - User performing the reinstatement
- `@GenerateInvoice` (BIT) - Whether to generate reinstatement invoice (default: 1)
- `@PaymentReceived` (MONEY) - Payment amount if received
- `@CheckNumber` (VARCHAR(100)) - Check number if payment received

**Returns:**
- QuoteID, PolicyNumber, NewStatusID, ReinstatementAmount, InvoiceNumber, Message, Success flag

### 3. CreateEndorsement_WS

Creates a policy endorsement as a new quote record.

**Parameters:**
- `@ControlNumber` (INT) - Policy control number
- `@EndorsementEffectiveDate` (DATETIME) - Effective date of endorsement
- `@EndorsementComment` (VARCHAR(250)) - Description of changes
- `@EndorsementReasonID` (INT) - Reason code for endorsement
- `@UserGuid` (UNIQUEIDENTIFIER) - User creating the endorsement
- `@CalculationType` (CHAR(1)) - P=Pro-rata, S=Short-rate, F=Flat (default: 'P')
- `@CopyExposures` (BIT) - Copy exposure data to endorsement (default: 1)
- `@CopyPremiums` (BIT) - Copy premium data to endorsement (default: 0)

**Returns:**
- EndorsementQuoteID, EndorsementQuoteGuid, PolicyNumber, EndorsementNumber, ProRataFactor, Message, Success flag

## Usage Examples

### Calling via DataAccess Web Service

```xml
<!-- Cancel Policy -->
<ExecuteCommand xmlns="http://tempuri.org/IMSWebServices/DataAccess">
  <procedureName>CancelPolicy_WS</procedureName>
  <parameters>
    <string>@ControlNumber</string>
    <string>12345</string>
    <string>@CancellationDate</string>
    <string>2025-02-01</string>
    <string>@CancellationReasonID</string>
    <string>1</string>
    <string>@Comments</string>
    <string>Non-payment of premium</string>
    <string>@UserGuid</string>
    <string>8a2d5f0a-c10d-4859-9ef4-a0d2e748d591</string>
  </parameters>
</ExecuteCommand>

<!-- Reinstate Policy -->
<ExecuteCommand xmlns="http://tempuri.org/IMSWebServices/DataAccess">
  <procedureName>ReinstatePolicy_WS</procedureName>
  <parameters>
    <string>@ControlNumber</string>
    <string>12345</string>
    <string>@ReinstatementDate</string>
    <string>2025-02-15</string>
    <string>@PaymentReceived</string>
    <string>500.00</string>
    <string>@CheckNumber</string>
    <string>CHK-1234</string>
    <string>@UserGuid</string>
    <string>8a2d5f0a-c10d-4859-9ef4-a0d2e748d591</string>
  </parameters>
</ExecuteCommand>

<!-- Create Endorsement -->
<ExecuteCommand xmlns="http://tempuri.org/IMSWebServices/DataAccess">
  <procedureName>CreateEndorsement_WS</procedureName>
  <parameters>
    <string>@ControlNumber</string>
    <string>12345</string>
    <string>@EndorsementEffectiveDate</string>
    <string>2025-03-01</string>
    <string>@EndorsementComment</string>
    <string>Add additional vehicle</string>
    <string>@EndorsementReasonID</string>
    <string>5</string>
    <string>@UserGuid</string>
    <string>8a2d5f0a-c10d-4859-9ef4-a0d2e748d591</string>
  </parameters>
</ExecuteCommand>
```

## Important Notes

1. **Transaction Safety**: All procedures use transactions to ensure data consistency
2. **Financial Integration**: Cancellation and reinstatement procedures integrate with the IMS financial module when enabled
3. **Document Automation**: All procedures trigger document automation events if configured
4. **Status Validation**: Procedures validate current policy status before making changes
5. **Error Handling**: Comprehensive error messages are returned for troubleshooting

## Required Database Objects

These procedures depend on the following IMS database objects:
- `tblQuotes`
- `lstQuoteStatus`
- `lstQuoteStatusReasons`
- `tblQuoteStatusLog`
- `tblFin_*` tables (for financial operations)
- Various internal stored procedures (spFin_*, spCopy*, etc.)

## Deployment Instructions

1. Have MGA Systems or your DBA review the procedures
2. Deploy to the IMS database using SQL Server Management Studio
3. Grant EXECUTE permissions to the IMS web service user
4. Test each procedure thoroughly in a test environment
5. Configure any required system settings mentioned in the procedures

## Support

For issues or modifications to these procedures, contact:
- MGA Systems Support
- Your IMS Administrator
- Database Administrator