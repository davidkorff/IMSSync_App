-- Fix for ProgramID assignment - make GUID comparisons case-insensitive
-- Replace the ProgramID assignment section (around line 416-476) in spProcessTritonPayload_WS with this:

        -- 5. Set ProgramID based on market_segment_code and LineGuid
        -- Only apply for bind transactions
        -- Market segment codes: RT (Retail) or WL (Wholesale)
        IF @transaction_type = 'bind' AND @market_segment_code IS NOT NULL
        BEGIN
            DECLARE @CompanyLineGuid UNIQUEIDENTIFIER;
            DECLARE @CompanyLineGuidStr NVARCHAR(50);  -- String version for comparison
           
            -- Get the LineGuid from tblQuotes (CompanyLineGuid field)
            SELECT @CompanyLineGuid = CompanyLineGuid
            FROM tblQuotes
            WHERE QuoteGuid = @QuoteGuid;
            
            -- Convert to uppercase string for comparison
            SET @CompanyLineGuidStr = UPPER(CAST(@CompanyLineGuid AS NVARCHAR(50)));
            
            PRINT 'ProgramID Assignment:';
            PRINT '  Market Segment: ' + ISNULL(@market_segment_code, 'NULL');
            PRINT '  CompanyLineGuid: ' + ISNULL(@CompanyLineGuidStr, 'NULL');
           
            -- If CompanyLineGuid is null, try to get it from tblQuoteOptions
            IF @CompanyLineGuid IS NULL
            BEGIN
                SELECT TOP 1 @CompanyLineGuid = LineGuid
                FROM tblQuoteOptions
                WHERE QuoteOptionGuid = @QuoteOptionGuid;
                
                SET @CompanyLineGuidStr = UPPER(CAST(@CompanyLineGuid AS NVARCHAR(50)));
                PRINT '  Retrieved LineGuid from tblQuoteOptions: ' + ISNULL(@CompanyLineGuidStr, 'NULL');
            END
           
            -- Set ProgramID based on market segment and line combinations
            -- Using UPPER() for case-insensitive comparison
            IF EXISTS (SELECT 1 FROM tblQuoteDetails WHERE QuoteGuid = @QuoteGuid)
            BEGIN
                -- RT + Primary LineGuid -> ProgramID = 11615
                IF @market_segment_code = 'RT' AND @CompanyLineGuidStr = '07564291-CBFE-4BBE-88D1-0548C88ACED4'
                BEGIN
                    UPDATE tblQuoteDetails
                    SET ProgramID = 11615
                    WHERE QuoteGuid = @QuoteGuid;
                    PRINT '  Set ProgramID to 11615 (RT market, Primary Line)';
                END
                -- WL + Primary LineGuid -> ProgramID = 11613
                ELSE IF @market_segment_code = 'WL' AND @CompanyLineGuidStr = '07564291-CBFE-4BBE-88D1-0548C88ACED4'
                BEGIN
                    UPDATE tblQuoteDetails
                    SET ProgramID = 11613
                    WHERE QuoteGuid = @QuoteGuid;
                    PRINT '  Set ProgramID to 11613 (WL market, Primary Line)';
                END
                -- RT + Excess LineGuid -> ProgramID = 11612
                ELSE IF @market_segment_code = 'RT' AND @CompanyLineGuidStr = '08798559-321C-4FC0-98ED-A61B92215F31'
                BEGIN
                    UPDATE tblQuoteDetails
                    SET ProgramID = 11612
                    WHERE QuoteGuid = @QuoteGuid;
                    PRINT '  Set ProgramID to 11612 (RT market, Excess Line)';
                END
                -- WL + Excess LineGuid -> ProgramID = 11614
                ELSE IF @market_segment_code = 'WL' AND @CompanyLineGuidStr = '08798559-321C-4FC0-98ED-A61B92215F31'
                BEGIN
                    UPDATE tblQuoteDetails
                    SET ProgramID = 11614
                    WHERE QuoteGuid = @QuoteGuid;
                    PRINT '  Set ProgramID to 11614 (WL market, Excess Line)';
                END
                ELSE
                BEGIN
                    PRINT '  WARNING: No matching ProgramID rule for:';
                    PRINT '    market_segment_code: ' + ISNULL(@market_segment_code, 'NULL');
                    PRINT '    CompanyLineGuid: ' + ISNULL(@CompanyLineGuidStr, 'NULL');
                    PRINT '    Expected Primary: 07564291-CBFE-4BBE-88D1-0548C88ACED4';
                    PRINT '    Expected Excess:  08798559-321C-4FC0-98ED-A61B92215F31';
                END
            END
            ELSE
            BEGIN
                PRINT '  WARNING: tblQuoteDetails does not exist for QuoteGuid ' + CAST(@QuoteGuid AS NVARCHAR(50));
            END
        END