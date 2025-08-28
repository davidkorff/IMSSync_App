-- Check ProgramID status for a specific quote
-- Run this in SQL Server Management Studio to see what's actually in the database

DECLARE @QuoteGuid UNIQUEIDENTIFIER = 'd5f59086-799d-4c23-9b6a-e73cec18b37f'; -- From your test output

-- Check all relevant tables
SELECT 
    '=== QUOTE INFO ===' AS Section,
    q.QuoteGuid,
    q.ControlNo,
    q.PolicyNumber,
    q.AccountNumber,
    q.CompanyLineGuid,
    cl.LineName,
    q.DateCreated
FROM tblQuotes q
LEFT JOIN vwCompanyLines cl ON cl.CompanyLineGuid = q.CompanyLineGuid
WHERE q.QuoteGuid = @QuoteGuid;

-- Check Triton data (see if market_segment_code is stored)
SELECT 
    '=== TRITON DATA ===' AS Section,
    tqd.QuoteGuid,
    tqd.market_segment_code,  -- This column might not exist yet
    tqd.class_of_business,
    tqd.program_name,
    tqd.transaction_type,
    tqd.opportunity_id,
    tqd.policy_number,
    tqd.created_date
FROM tblTritonQuoteData tqd
WHERE tqd.QuoteGuid = @QuoteGuid;

-- Check QuoteDetails for ProgramID
SELECT 
    '=== QUOTE DETAILS ===' AS Section,
    qd.QuoteDetailsID,
    qd.QuoteGuid,
    qd.ProgramID,
    qd.ProducerCommission,
    qd.CompanyCommission,
    qd.DateCreated
FROM tblQuoteDetails qd
WHERE qd.QuoteGuid = @QuoteGuid;

-- Check what ProgramID SHOULD be based on the rules
SELECT 
    '=== ANALYSIS ===' AS Section,
    q.QuoteGuid,
    q.CompanyLineGuid,
    tqd.market_segment_code,
    qd.ProgramID AS Current_ProgramID,
    CASE 
        WHEN tqd.market_segment_code = 'RT' AND q.CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN '11615 (RT + Primary)'
        WHEN tqd.market_segment_code = 'WL' AND q.CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN '11613 (WL + Primary)'
        WHEN tqd.market_segment_code = 'RT' AND q.CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31' THEN '11612 (RT + Excess)'
        WHEN tqd.market_segment_code = 'WL' AND q.CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31' THEN '11614 (WL + Excess)'
        ELSE 'No matching rule'
    END AS Expected_ProgramID,
    CASE 
        WHEN qd.ProgramID IS NULL THEN 'NOT SET - ProgramID is NULL'
        WHEN tqd.market_segment_code IS NULL THEN 'MISSING DATA - market_segment_code is NULL'
        WHEN q.CompanyLineGuid IS NULL THEN 'MISSING DATA - CompanyLineGuid is NULL'
        WHEN qd.ProgramID = 
            CASE 
                WHEN tqd.market_segment_code = 'RT' AND q.CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 11615
                WHEN tqd.market_segment_code = 'WL' AND q.CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 11613
                WHEN tqd.market_segment_code = 'RT' AND q.CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 11612
                WHEN tqd.market_segment_code = 'WL' AND q.CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 11614
                ELSE NULL
            END
        THEN 'CORRECT - ProgramID matches expected value'
        ELSE 'INCORRECT - ProgramID does not match expected value'
    END AS Status
FROM tblQuotes q
LEFT JOIN tblTritonQuoteData tqd ON tqd.QuoteGuid = q.QuoteGuid
LEFT JOIN tblQuoteDetails qd ON qd.QuoteGuid = q.QuoteGuid
WHERE q.QuoteGuid = @QuoteGuid;

-- Check if the columns exist in tblTritonQuoteData
SELECT 
    '=== COLUMN CHECK ===' AS Section,
    c.name AS ColumnName,
    t.name AS DataType,
    c.max_length,
    c.is_nullable,
    'Exists' AS Status
FROM sys.columns c
INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
WHERE c.object_id = OBJECT_ID('tblTritonQuoteData')
    AND c.name IN ('market_segment_code', 'opportunity_type', 'commission_percent', 'full_payload_json')
ORDER BY c.name;

-- Check the JSON payload if stored
IF EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'full_payload_json')
BEGIN
    SELECT 
        '=== JSON PAYLOAD CHECK ===' AS Section,
        JSON_VALUE(full_payload_json, '$.market_segment_code') AS market_segment_code_from_json,
        JSON_VALUE(full_payload_json, '$.transaction_type') AS transaction_type_from_json,
        JSON_VALUE(full_payload_json, '$.opportunity_id') AS opportunity_id_from_json,
        JSON_VALUE(full_payload_json, '$.class_of_business') AS class_of_business_from_json,
        JSON_VALUE(full_payload_json, '$.program_name') AS program_name_from_json
    FROM tblTritonQuoteData
    WHERE QuoteGuid = @QuoteGuid;
END

-- Show recent bind transactions to see the pattern
SELECT TOP 5
    '=== RECENT BINDS ===' AS Section,
    q.QuoteGuid,
    q.PolicyNumber,
    q.CompanyLineGuid,
    tqd.market_segment_code,
    qd.ProgramID,
    tqd.transaction_type,
    tqd.created_date
FROM tblTritonQuoteData tqd
INNER JOIN tblQuotes q ON q.QuoteGuid = tqd.QuoteGuid
LEFT JOIN tblQuoteDetails qd ON qd.QuoteGuid = q.QuoteGuid
WHERE tqd.transaction_type = 'bind'
ORDER BY tqd.created_date DESC;