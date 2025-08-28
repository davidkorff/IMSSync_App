-- =============================================
-- TABLE VERIFICATION SCRIPT
-- Run this after creating tables to verify everything is correct
-- =============================================

USE [YourDatabaseName]; -- CHANGE THIS TO YOUR DATABASE NAME
GO

PRINT '=========================================='
PRINT 'TABLE VERIFICATION REPORT'
PRINT '=========================================='
PRINT ''

-- Check if tables exist
PRINT 'CHECKING TABLE EXISTENCE:'
PRINT '--------------------------'

IF EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonQuoteData')
    PRINT '✓ tblTritonQuoteData EXISTS'
ELSE
    PRINT '✗ tblTritonQuoteData MISSING!'

IF EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonTransactionData')
    PRINT '✓ tblTritonTransactionData EXISTS'
ELSE
    PRINT '✗ tblTritonTransactionData MISSING!'

PRINT ''
PRINT 'TABLE DETAILS:'
PRINT '--------------------------'

-- Show table details
SELECT 
    'Table Info' AS QueryType,
    t.name AS TableName,
    p.rows AS RowCount,
    SUM(a.total_pages) * 8 AS TotalSpaceKB,
    SUM(a.used_pages) * 8 AS UsedSpaceKB,
    (SUM(a.total_pages) - SUM(a.used_pages)) * 8 AS UnusedSpaceKB
FROM sys.tables t
INNER JOIN sys.indexes i ON t.object_id = i.object_id
INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
WHERE t.name IN ('tblTritonQuoteData', 'tblTritonTransactionData')
    AND i.object_id > 255
GROUP BY t.name, p.rows
ORDER BY t.name;

PRINT ''
PRINT 'CONSTRAINT VERIFICATION:'
PRINT '--------------------------'

-- Check Primary Keys
SELECT 
    'Primary Keys' AS ConstraintType,
    t.name AS TableName,
    i.name AS ConstraintName,
    STRING_AGG(c.name, ', ') AS Columns
FROM sys.indexes i
JOIN sys.tables t ON i.object_id = t.object_id
JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE i.is_primary_key = 1
    AND t.name IN ('tblTritonQuoteData', 'tblTritonTransactionData')
GROUP BY t.name, i.name
ORDER BY t.name;

-- Check Unique Constraints
SELECT 
    'Unique Constraints' AS ConstraintType,
    t.name AS TableName,
    i.name AS ConstraintName,
    STRING_AGG(c.name, ', ') AS Columns
FROM sys.indexes i
JOIN sys.tables t ON i.object_id = t.object_id
JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE i.is_unique_constraint = 1
    AND t.name IN ('tblTritonQuoteData', 'tblTritonTransactionData')
GROUP BY t.name, i.name
ORDER BY t.name;

PRINT ''
PRINT 'INDEX VERIFICATION:'
PRINT '--------------------------'

-- List all indexes
SELECT 
    'Indexes' AS ObjectType,
    t.name AS TableName,
    i.name AS IndexName,
    i.type_desc AS IndexType,
    STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) AS IndexColumns
FROM sys.indexes i
JOIN sys.tables t ON i.object_id = t.object_id
JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE t.name IN ('tblTritonQuoteData', 'tblTritonTransactionData')
    AND i.is_primary_key = 0 
    AND i.is_unique_constraint = 0
    AND ic.is_included_column = 0
GROUP BY t.name, i.name, i.type_desc
ORDER BY t.name, i.name;

PRINT ''
PRINT 'CRITICAL COLUMNS CHECK:'
PRINT '--------------------------'

-- Verify critical columns exist
WITH CriticalColumns AS (
    SELECT 'tblTritonQuoteData' AS TableName, 'QuoteGuid' AS ColumnName, 'UNIQUEIDENTIFIER' AS ExpectedType
    UNION ALL SELECT 'tblTritonQuoteData', 'QuoteOptionGuid', 'UNIQUEIDENTIFIER'
    UNION ALL SELECT 'tblTritonQuoteData', 'opportunity_id', 'INT'
    UNION ALL SELECT 'tblTritonQuoteData', 'policy_number', 'NVARCHAR'
    UNION ALL SELECT 'tblTritonQuoteData', 'full_payload_json', 'NVARCHAR'
    UNION ALL SELECT 'tblTritonTransactionData', 'transaction_id', 'NVARCHAR'
    UNION ALL SELECT 'tblTritonTransactionData', 'QuoteGuid', 'UNIQUEIDENTIFIER'
    UNION ALL SELECT 'tblTritonTransactionData', 'QuoteOptionGuid', 'UNIQUEIDENTIFIER'
    UNION ALL SELECT 'tblTritonTransactionData', 'full_payload_json', 'NVARCHAR'
    UNION ALL SELECT 'tblTritonTransactionData', 'opportunity_id', 'INT'
)
SELECT 
    cc.TableName,
    cc.ColumnName,
    CASE 
        WHEN c.name IS NULL THEN '✗ MISSING'
        WHEN TYPE_NAME(c.system_type_id) LIKE cc.ExpectedType + '%' THEN '✓ OK'
        ELSE '⚠ TYPE MISMATCH: ' + TYPE_NAME(c.system_type_id)
    END AS Status
FROM CriticalColumns cc
LEFT JOIN sys.tables t ON t.name = cc.TableName
LEFT JOIN sys.columns c ON c.object_id = t.object_id AND c.name = cc.ColumnName
ORDER BY cc.TableName, cc.ColumnName;

PRINT ''
PRINT 'DEFAULT CONSTRAINTS:'
PRINT '--------------------------'

-- Check default constraints
SELECT 
    'Default Constraints' AS ConstraintType,
    t.name AS TableName,
    c.name AS ColumnName,
    dc.name AS ConstraintName,
    dc.definition AS DefaultValue
FROM sys.default_constraints dc
JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
JOIN sys.tables t ON dc.parent_object_id = t.object_id
WHERE t.name IN ('tblTritonQuoteData', 'tblTritonTransactionData')
ORDER BY t.name, c.name;

PRINT ''
PRINT '=========================================='
PRINT 'VERIFICATION COMPLETE'
PRINT '=========================================='