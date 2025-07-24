# IMS Stored Procedures for RSG Integration

This directory contains SQL scripts for stored procedures needed by the RSG Integration service.

## Required Stored Procedures

### 1. spGetQuoteOptionID_WS
**File:** `create_spGetQuoteOptionID_WS.sql`

**Purpose:** Returns the integer QuoteOptionID for a given QuoteGuid. This is needed because:
- The AddQuoteOption API returns a GUID
- The Bind and BindWithInstallment methods need an integer ID
- The standard DataAccess methods have parameter format issues

**Usage:**
```sql
EXEC spGetQuoteOptionID_WS @QuoteGuid = 'your-quote-guid-here'
```

**Returns:**
- QuoteOptionID (int) - The integer ID needed for bind operations
- QuoteOptionGuid (uniqueidentifier) - The GUID returned by AddQuoteOption
- QuoteGuid (uniqueidentifier) - The quote this option belongs to

## Installation Instructions

1. Connect to the IMS database with appropriate permissions
2. Run each SQL script in SQL Server Management Studio
3. Verify the stored procedures were created:
   ```sql
   SELECT * FROM sys.procedures WHERE name LIKE '%_WS'
   ```

## Notes

- All IMS web service stored procedures must end with '_WS' suffix
- The DataAccess service automatically appends '_WS' to procedure names
- Grant appropriate execute permissions to the IMS web service user

## Troubleshooting

If bind operations are still failing after creating these procedures:
1. Check that the stored procedure exists and has correct permissions
2. Verify that quote options are being created correctly
3. Check IMS logs for detailed error messages
4. Consider enabling installment billing configuration in IMS