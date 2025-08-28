-- Update the ProgramID assignment section in spProcessTritonPayload_WS
-- This version adds extensive debugging to see why ProgramID isn't being set

-- Replace the section starting at line 416 (-- 5. Set ProgramID based on market_segment_code...)
-- with this improved version that has better debugging:

        -- 5. Set ProgramID based on market_segment_code and LineGuid
        -- Only apply for bind transactions
        -- Market segment codes: RT (Retail) or WL (Wholesale)
        IF @transaction_type = 'bind' AND @market_segment_code IS NOT NULL
        BEGIN
            DECLARE @CompanyLineGuid UNIQUEIDENTIFIER;
            DECLARE @NewProgramID INT = NULL;
            DECLARE @QuoteDetailsExists BIT = 0;
           
            -- Get the LineGuid from tblQuotes (CompanyLineGuid field)
            SELECT @CompanyLineGuid = CompanyLineGuid
            FROM tblQuotes
            WHERE QuoteGuid = @QuoteGuid;
            
            PRINT '===== ProgramID Assignment Debug =====';
            PRINT 'QuoteGuid: ' + CAST(@QuoteGuid AS NVARCHAR(50));
            PRINT 'Transaction Type: ' + ISNULL(@transaction_type, 'NULL');
            PRINT 'Market Segment Code: ' + ISNULL(@market_segment_code, 'NULL');
            PRINT 'CompanyLineGuid from tblQuotes: ' + ISNULL(CAST(@CompanyLineGuid AS NVARCHAR(50)), 'NULL');
           
            -- If CompanyLineGuid is null, try to get it from tblQuoteOptions
            IF @CompanyLineGuid IS NULL
            BEGIN
                SELECT TOP 1 @CompanyLineGuid = LineGuid
                FROM tblQuoteOptions
                WHERE QuoteOptionGuid = @QuoteOptionGuid;
                
                PRINT 'CompanyLineGuid was NULL in tblQuotes';
                PRINT 'Retrieved LineGuid from tblQuoteOptions: ' + CAST(ISNULL(@CompanyLineGuid, '00000000-0000-0000-0000-000000000000') AS NVARCHAR(50));
            END
            
            -- Check if tblQuoteDetails exists
            IF EXISTS (SELECT 1 FROM tblQuoteDetails WHERE QuoteGuid = @QuoteGuid)
            BEGIN
                SET @QuoteDetailsExists = 1;
                PRINT 'tblQuoteDetails record EXISTS for this quote';
                
                -- Get current ProgramID for debugging
                DECLARE @CurrentProgramID INT;
                SELECT @CurrentProgramID = ProgramID FROM tblQuoteDetails WHERE QuoteGuid = @QuoteGuid;
                PRINT 'Current ProgramID in tblQuoteDetails: ' + ISNULL(CAST(@CurrentProgramID AS NVARCHAR(10)), 'NULL');
            END
            ELSE
            BEGIN
                PRINT 'WARNING: tblQuoteDetails record DOES NOT EXIST for this quote!';
            END
            
            -- Convert GUIDs to uppercase for comparison (just in case)
            DECLARE @CompanyLineGuidUpper NVARCHAR(50) = UPPER(CAST(@CompanyLineGuid AS NVARCHAR(50)));
            PRINT 'CompanyLineGuid (uppercase): ' + ISNULL(@CompanyLineGuidUpper, 'NULL');
            
            -- Determine what ProgramID should be based on market segment and line
            -- Using explicit GUID comparison
            PRINT 'Checking ProgramID rules...';
            
            -- RT + Primary Line -> 11615
            IF @market_segment_code = 'RT' AND @CompanyLineGuid = CAST('07564291-CBFE-4BBE-88D1-0548C88ACED4' AS UNIQUEIDENTIFIER)
            BEGIN
                SET @NewProgramID = 11615;
                PRINT 'MATCHED: RT + Primary Line -> ProgramID 11615';
            END
            -- WL + Primary Line -> 11613
            ELSE IF @market_segment_code = 'WL' AND @CompanyLineGuid = CAST('07564291-CBFE-4BBE-88D1-0548C88ACED4' AS UNIQUEIDENTIFIER)
            BEGIN
                SET @NewProgramID = 11613;
                PRINT 'MATCHED: WL + Primary Line -> ProgramID 11613';
            END
            -- RT + Excess Line -> 11612
            ELSE IF @market_segment_code = 'RT' AND @CompanyLineGuid = CAST('08798559-321C-4FC0-98ED-A61B92215F31' AS UNIQUEIDENTIFIER)
            BEGIN
                SET @NewProgramID = 11612;
                PRINT 'MATCHED: RT + Excess Line -> ProgramID 11612';
            END
            -- WL + Excess Line -> 11614
            ELSE IF @market_segment_code = 'WL' AND @CompanyLineGuid = CAST('08798559-321C-4FC0-98ED-A61B92215F31' AS UNIQUEIDENTIFIER)
            BEGIN
                SET @NewProgramID = 11614;
                PRINT 'MATCHED: WL + Excess Line -> ProgramID 11614';
            END
            ELSE
            BEGIN
                PRINT 'NO MATCH FOUND!';
                PRINT '  Market Segment: ''' + ISNULL(@market_segment_code, 'NULL') + '''';
                PRINT '  CompanyLineGuid: ''' + ISNULL(CAST(@CompanyLineGuid AS NVARCHAR(50)), 'NULL') + '''';
                PRINT '  Expected GUIDs:';
                PRINT '    Primary: 07564291-CBFE-4BBE-88D1-0548C88ACED4';
                PRINT '    Excess:  08798559-321C-4FC0-98ED-A61B92215F31';
                
                -- Additional debugging - check if it's a case issue
                IF @market_segment_code = 'WL' AND UPPER(CAST(@CompanyLineGuid AS NVARCHAR(50))) = '07564291-CBFE-4BBE-88D1-0548C88ACED4'
                BEGIN
                    PRINT '  CASE SENSITIVITY ISSUE DETECTED!';
                END
            END
           
            -- Now set the ProgramID if we have one
            IF @NewProgramID IS NOT NULL AND @QuoteDetailsExists = 1
            BEGIN
                UPDATE tblQuoteDetails
                SET ProgramID = @NewProgramID
                WHERE QuoteGuid = @QuoteGuid;
                
                PRINT 'SUCCESS: Updated ProgramID to ' + CAST(@NewProgramID AS NVARCHAR(10));
                
                -- Verify it was set
                DECLARE @VerifyProgramID INT;
                SELECT @VerifyProgramID = ProgramID FROM tblQuoteDetails WHERE QuoteGuid = @QuoteGuid;
                PRINT 'Verification: ProgramID is now ' + CAST(@VerifyProgramID AS NVARCHAR(10));
            END
            ELSE IF @NewProgramID IS NOT NULL AND @QuoteDetailsExists = 0
            BEGIN
                PRINT 'ERROR: Cannot set ProgramID - tblQuoteDetails does not exist';
            END
            ELSE IF @NewProgramID IS NULL
            BEGIN
                PRINT 'ERROR: Could not determine ProgramID from rules';
            END
            
            PRINT '===== End ProgramID Assignment Debug =====';
        END
        ELSE
        BEGIN
            IF @transaction_type != 'bind'
            BEGIN
                PRINT 'Skipping ProgramID assignment - transaction_type is ' + @transaction_type + ' (not bind)';
            END
            ELSE IF @market_segment_code IS NULL
            BEGIN
                PRINT 'Skipping ProgramID assignment - market_segment_code is NULL';
            END
        END