-- =============================================
-- PRODUCTION TABLE EXPORT SCRIPTS
-- Tables: tblTritonQuoteData, tblTritonTransactionData
-- Generated for Production Deployment
-- =============================================

-- =============================================
-- PART 1: EXPORT EXISTING TABLE STRUCTURE (if tables exist)
-- =============================================

-- Generate CREATE TABLE script for tblTritonQuoteData
SELECT 
    'CREATE TABLE [' + s.name + '].[' + t.name + '] (' + CHAR(13) +
    STUFF((
        SELECT CHAR(13) + '    [' + c.name + '] ' + 
            CASE 
                WHEN c.system_type_id IN (165, 167, 173, 175, 231, 239) 
                THEN UPPER(TYPE_NAME(c.system_type_id)) + '(' + 
                    CASE 
                        WHEN c.max_length = -1 THEN 'MAX' 
                        WHEN c.system_type_id IN (231, 239) THEN CAST(c.max_length/2 AS VARCHAR(10))
                        ELSE CAST(c.max_length AS VARCHAR(10))
                    END + ')'
                WHEN c.system_type_id IN (106, 108)
                THEN UPPER(TYPE_NAME(c.system_type_id)) + '(' + CAST(c.precision AS VARCHAR(10)) + ',' + CAST(c.scale AS VARCHAR(10)) + ')'
                ELSE UPPER(TYPE_NAME(c.system_type_id))
            END +
            CASE WHEN c.is_identity = 1 THEN ' IDENTITY(' + CAST(IDENT_SEED(t.object_id) AS VARCHAR(10)) + ',' + CAST(IDENT_INCR(t.object_id) AS VARCHAR(10)) + ')' ELSE '' END +
            CASE WHEN c.is_nullable = 0 THEN ' NOT NULL' ELSE ' NULL' END +
            CASE WHEN c.default_object_id > 0 THEN ' DEFAULT ' + OBJECT_DEFINITION(c.default_object_id) ELSE '' END + ','
        FROM sys.columns c
        WHERE c.object_id = t.object_id
        ORDER BY c.column_id
        FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 0, '') + CHAR(13) + ');' AS CreateTableScript
FROM sys.tables t
INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE t.name IN ('tblTritonQuoteData', 'tblTritonTransactionData');

-- Generate PRIMARY KEY constraints
SELECT 
    'ALTER TABLE [' + s.name + '].[' + t.name + '] ADD CONSTRAINT [' + i.name + '] PRIMARY KEY ' + 
    i.type_desc COLLATE DATABASE_DEFAULT + ' (' +
    STUFF((
        SELECT ', [' + c.name + ']' + 
            CASE WHEN ic.is_descending_key = 1 THEN ' DESC' ELSE ' ASC' END
        FROM sys.index_columns ic
        INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id
        ORDER BY ic.key_ordinal
        FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 2, '') + ');' AS PrimaryKeyScript
FROM sys.indexes i
INNER JOIN sys.tables t ON i.object_id = t.object_id
INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE i.is_primary_key = 1
    AND t.name IN ('tblTritonQuoteData', 'tblTritonTransactionData');

-- Generate UNIQUE constraints
SELECT 
    'ALTER TABLE [' + s.name + '].[' + t.name + '] ADD CONSTRAINT [' + i.name + '] UNIQUE ' + 
    i.type_desc COLLATE DATABASE_DEFAULT + ' (' +
    STUFF((
        SELECT ', [' + c.name + ']' + 
            CASE WHEN ic.is_descending_key = 1 THEN ' DESC' ELSE ' ASC' END
        FROM sys.index_columns ic
        INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id
        ORDER BY ic.key_ordinal
        FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 2, '') + ');' AS UniqueConstraintScript
FROM sys.indexes i
INNER JOIN sys.tables t ON i.object_id = t.object_id
INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE i.is_unique_constraint = 1
    AND t.name IN ('tblTritonQuoteData', 'tblTritonTransactionData');

-- Generate INDEXES
SELECT 
    'CREATE ' + 
    CASE WHEN i.is_unique = 1 THEN 'UNIQUE ' ELSE '' END +
    i.type_desc COLLATE DATABASE_DEFAULT + ' INDEX [' + i.name + '] ON [' + s.name + '].[' + t.name + '] (' +
    STUFF((
        SELECT ', [' + c.name + ']' + 
            CASE WHEN ic.is_descending_key = 1 THEN ' DESC' ELSE ' ASC' END
        FROM sys.index_columns ic
        INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.is_included_column = 0
        ORDER BY ic.key_ordinal
        FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 2, '') + ')' +
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM sys.index_columns ic2
            WHERE ic2.object_id = i.object_id AND ic2.index_id = i.index_id AND ic2.is_included_column = 1
        )
        THEN ' INCLUDE (' + 
            STUFF((
                SELECT ', [' + c.name + ']'
                FROM sys.index_columns ic
                INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
                WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.is_included_column = 1
                ORDER BY ic.index_column_id
                FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 2, '') + ')'
        ELSE ''
    END + ';' AS IndexScript
FROM sys.indexes i
INNER JOIN sys.tables t ON i.object_id = t.object_id
INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE i.is_primary_key = 0 AND i.is_unique_constraint = 0 AND i.type > 0
    AND t.name IN ('tblTritonQuoteData', 'tblTritonTransactionData');

-- Generate CHECK constraints
SELECT 
    'ALTER TABLE [' + s.name + '].[' + t.name + '] ADD CONSTRAINT [' + cc.name + '] CHECK ' + cc.definition + ';' AS CheckConstraintScript
FROM sys.check_constraints cc
INNER JOIN sys.tables t ON cc.parent_object_id = t.object_id
INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE t.name IN ('tblTritonQuoteData', 'tblTritonTransactionData');

-- Generate DEFAULT constraints
SELECT 
    'ALTER TABLE [' + s.name + '].[' + t.name + '] ADD CONSTRAINT [' + dc.name + '] DEFAULT ' + 
    dc.definition + ' FOR [' + c.name + '];' AS DefaultConstraintScript
FROM sys.default_constraints dc
INNER JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
INNER JOIN sys.tables t ON dc.parent_object_id = t.object_id
INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE t.name IN ('tblTritonQuoteData', 'tblTritonTransactionData');

-- Generate FOREIGN KEY constraints
SELECT 
    'ALTER TABLE [' + s.name + '].[' + t.name + '] ADD CONSTRAINT [' + fk.name + '] FOREIGN KEY (' +
    STUFF((
        SELECT ', [' + c.name + ']'
        FROM sys.foreign_key_columns fkc
        INNER JOIN sys.columns c ON fkc.parent_object_id = c.object_id AND fkc.parent_column_id = c.column_id
        WHERE fkc.constraint_object_id = fk.object_id
        ORDER BY fkc.constraint_column_id
        FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 2, '') + ') REFERENCES [' + 
    rs.name + '].[' + rt.name + '] (' +
    STUFF((
        SELECT ', [' + c.name + ']'
        FROM sys.foreign_key_columns fkc
        INNER JOIN sys.columns c ON fkc.referenced_object_id = c.object_id AND fkc.referenced_column_id = c.column_id
        WHERE fkc.constraint_object_id = fk.object_id
        ORDER BY fkc.constraint_column_id
        FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 2, '') + ')' +
    CASE 
        WHEN fk.delete_referential_action > 0 THEN ' ON DELETE ' + 
            CASE fk.delete_referential_action
                WHEN 1 THEN 'CASCADE'
                WHEN 2 THEN 'SET NULL'
                WHEN 3 THEN 'SET DEFAULT'
            END
        ELSE ''
    END +
    CASE 
        WHEN fk.update_referential_action > 0 THEN ' ON UPDATE ' + 
            CASE fk.update_referential_action
                WHEN 1 THEN 'CASCADE'
                WHEN 2 THEN 'SET NULL'
                WHEN 3 THEN 'SET DEFAULT'
            END
        ELSE ''
    END + ';' AS ForeignKeyScript
FROM sys.foreign_keys fk
INNER JOIN sys.tables t ON fk.parent_object_id = t.object_id
INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
INNER JOIN sys.tables rt ON fk.referenced_object_id = rt.object_id
INNER JOIN sys.schemas rs ON rt.schema_id = rs.schema_id
WHERE t.name IN ('tblTritonQuoteData', 'tblTritonTransactionData');