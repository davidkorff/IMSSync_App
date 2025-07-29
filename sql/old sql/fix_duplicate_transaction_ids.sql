-- Script to investigate and fix duplicate transaction_ids in tblTritonQuoteData

-- 1. First, let's see all the quotes with duplicate transaction_ids
PRINT 'Investigating duplicate transaction_ids in tblTritonQuoteData';
PRINT '=========================================================';

-- Show all rows with the duplicate transaction_id
SELECT 
    TritonQuoteDataID,
    QuoteGuid,
    transaction_id,
    policy_number,
    insured_name,
    created_date,
    last_updated
FROM tblTritonQuoteData
WHERE transaction_id IN (
    SELECT transaction_id 
    FROM tblTritonQuoteData 
    WHERE transaction_id IS NOT NULL
    GROUP BY transaction_id 
    HAVING COUNT(*) > 1
)
ORDER BY transaction_id, created_date;

-- 2. Count how many unique QuoteGuids have duplicate transaction_ids
PRINT '';
PRINT 'Summary of duplicates:';
SELECT 
    transaction_id,
    COUNT(*) as duplicate_count,
    COUNT(DISTINCT QuoteGuid) as unique_quotes,
    MIN(created_date) as first_created,
    MAX(created_date) as last_created
FROM tblTritonQuoteData
WHERE transaction_id IS NOT NULL
GROUP BY transaction_id
HAVING COUNT(*) > 1;

-- 3. Options to fix the duplicates:

PRINT '';
PRINT 'FIX OPTIONS:';
PRINT '============';
PRINT '1. Keep only the most recent record per QuoteGuid (recommended for quote data)';
PRINT '2. Update transaction_ids to make them unique by appending a sequence number';
PRINT '3. Clear transaction_id from older records';
PRINT '';
PRINT 'Run one of the following fixes:';

-- Option 1: Delete older duplicates, keeping the most recent per QuoteGuid
PRINT '';
PRINT '-- OPTION 1: Delete older duplicate records (keeping most recent per QuoteGuid)';
PRINT '-- Uncomment and run if you want to use this option:';
PRINT '/*';
PRINT 'DELETE t1';
PRINT 'FROM tblTritonQuoteData t1';
PRINT 'INNER JOIN (';
PRINT '    SELECT QuoteGuid, MAX(created_date) as max_date';
PRINT '    FROM tblTritonQuoteData';
PRINT '    GROUP BY QuoteGuid';
PRINT '    HAVING COUNT(*) > 1';
PRINT ') t2 ON t1.QuoteGuid = t2.QuoteGuid';
PRINT 'WHERE t1.created_date < t2.max_date;';
PRINT '*/';

-- Option 2: Make transaction_ids unique by appending sequence
PRINT '';
PRINT '-- OPTION 2: Make transaction_ids unique by appending sequence number';
PRINT '-- Uncomment and run if you want to use this option:';
PRINT '/*';
PRINT 'WITH DuplicateRows AS (';
PRINT '    SELECT ';
PRINT '        TritonQuoteDataID,';
PRINT '        transaction_id,';
PRINT '        ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY created_date) as rn';
PRINT '    FROM tblTritonQuoteData';
PRINT '    WHERE transaction_id IS NOT NULL';
PRINT ')';
PRINT 'UPDATE t';
PRINT 'SET t.transaction_id = t.transaction_id + ''-'' + CAST(d.rn AS VARCHAR(10))';
PRINT 'FROM tblTritonQuoteData t';
PRINT 'INNER JOIN DuplicateRows d ON t.TritonQuoteDataID = d.TritonQuoteDataID';
PRINT 'WHERE d.rn > 1;';
PRINT '*/';

-- Option 3: Clear transaction_id from older records
PRINT '';
PRINT '-- OPTION 3: Clear transaction_id from all but the most recent record';
PRINT '-- Uncomment and run if you want to use this option:';
PRINT '/*';
PRINT 'WITH RankedData AS (';
PRINT '    SELECT ';
PRINT '        TritonQuoteDataID,';
PRINT '        ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY created_date DESC) as rn';
PRINT '    FROM tblTritonQuoteData';
PRINT '    WHERE transaction_id IS NOT NULL';
PRINT ')';
PRINT 'UPDATE t';
PRINT 'SET t.transaction_id = NULL';
PRINT 'FROM tblTritonQuoteData t';
PRINT 'INNER JOIN RankedData r ON t.TritonQuoteDataID = r.TritonQuoteDataID';
PRINT 'WHERE r.rn > 1;';
PRINT '*/';

-- Since this is quote data and QuoteGuid should be unique, let's also check that
PRINT '';
PRINT 'Checking QuoteGuid uniqueness:';
SELECT 
    QuoteGuid,
    COUNT(*) as duplicate_count
FROM tblTritonQuoteData
GROUP BY QuoteGuid
HAVING COUNT(*) > 1;

-- If no QuoteGuid duplicates, we can safely use Option 2
PRINT '';
PRINT 'RECOMMENDED FIX for your situation:';
PRINT '===================================';
PRINT 'Since QuoteGuid is already unique, use Option 2 to make transaction_ids unique:';
PRINT '';

-- Here's the actual fix command (commented out for safety)
PRINT '-- Run this to fix the duplicate transaction_ids:';
PRINT '/*';
PRINT 'WITH DuplicateRows AS (';
PRINT '    SELECT ';
PRINT '        TritonQuoteDataID,';
PRINT '        transaction_id,';
PRINT '        ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY created_date) as rn';
PRINT '    FROM tblTritonQuoteData';
PRINT '    WHERE transaction_id IS NOT NULL';
PRINT ')';
PRINT 'UPDATE t';
PRINT 'SET t.transaction_id = t.transaction_id + ''-'' + CAST(d.rn AS VARCHAR(10))';
PRINT 'FROM tblTritonQuoteData t';
PRINT 'INNER JOIN DuplicateRows d ON t.TritonQuoteDataID = d.TritonQuoteDataID';
PRINT 'WHERE d.rn > 1;';
PRINT '';
PRINT '-- Then add the unique constraint:';
PRINT 'ALTER TABLE tblTritonQuoteData ';
PRINT 'ADD CONSTRAINT UQ_tblTritonQuoteData_transaction_id UNIQUE (transaction_id);';
PRINT '*/';

GO