-- Check the most recent endorsement and its status
-- This query helps diagnose why premiums aren't being applied

-- Get the most recent endorsement quote
WITH RecentEndorsement AS (
    SELECT TOP 1 
        q.QuoteGUID,
        q.QuoteID,
        q.PolicyNumber,
        q.TransactionTypeID,
        q.EndorsementNum,
        q.Bound,
        q.DateBound,
        q.QuoteStatusID,
        q.EffectiveDate,
        q.EndorsementEffective,
        tq.opportunity_id,
        tq.gross_premium,
        tq.transaction_type,
        tq.status as triton_status,
        tq.created_date
    FROM tblQuotes q
    LEFT JOIN tblTritonQuoteData tq ON tq.QuoteGuid = q.QuoteGUID
    WHERE q.TransactionTypeID = 'E'
    ORDER BY q.QuoteID DESC
)
SELECT 
    'Quote Info' as Section,
    RE.*
FROM RecentEndorsement RE

UNION ALL

-- Check quote option status
SELECT 
    'Quote Option' as Section,
    NULL, NULL, NULL, NULL, NULL,
    qo.Bound,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
FROM RecentEndorsement RE
INNER JOIN tblQuoteOptions qo ON qo.QuoteGUID = RE.QuoteGUID

UNION ALL

-- Check if any premiums exist
SELECT 
    'Premium Count' as Section,
    NULL, NULL, NULL, NULL, NULL,
    COUNT(*) as PremiumCount,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
FROM RecentEndorsement RE
LEFT JOIN tblQuoteOptionPremiums qop ON qop.QuoteOptionGUID = (
    SELECT QuoteOptionGUID FROM tblQuoteOptions WHERE QuoteGUID = RE.QuoteGUID
)

-- Show the actual premiums if any
SELECT 
    'Premiums' as Section,
    qop.ChargeCode,
    qop.ChargeName,
    qop.Premium,
    qop.CreatedDate
FROM RecentEndorsement RE
INNER JOIN tblQuoteOptions qo ON qo.QuoteGUID = RE.QuoteGUID
LEFT JOIN tblQuoteOptionPremiums qop ON qop.QuoteOptionGUID = qo.QuoteOptionGUID

-- Check trigger status
SELECT 
    name as TriggerName,
    is_disabled,
    CASE 
        WHEN is_disabled = 0 THEN 'ACTIVE - Will block premium updates on bound quotes'
        ELSE 'DISABLED - Premium updates allowed'
    END as Status
FROM sys.triggers 
WHERE name = 'CantModifyPremiumOnBoundPolicy'