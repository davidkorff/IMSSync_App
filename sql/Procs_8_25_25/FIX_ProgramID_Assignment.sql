-- Fix for ProgramID not being set because tblQuoteDetails might not exist yet
-- This updates the logic in spProcessTritonPayload_WS to handle missing tblQuoteDetails

-- Find the section in spProcessTritonPayload_WS that sets ProgramID (around line 416-476)
-- and replace it with this improved version:

-- 5. Set ProgramID based on market_segment_code and LineGuid
-- Only apply for bind transactions
-- Market segment codes: RT (Retail) or WL (Wholesale)
IF @transaction_type = 'bind' AND @market_segment_code IS NOT NULL
BEGIN
    DECLARE @CompanyLineGuid UNIQUEIDENTIFIER;
    DECLARE @CurrentProgramID INT = NULL;
    DECLARE @NewProgramID INT = NULL;
   
    -- Get the LineGuid from tblQuotes (CompanyLineGuid field)
    SELECT @CompanyLineGuid = CompanyLineGuid
    FROM tblQuotes
    WHERE QuoteGuid = @QuoteGuid;
   
    -- If CompanyLineGuid is null, try to get it from tblQuoteOptions
    IF @CompanyLineGuid IS NULL
    BEGIN
        SELECT TOP 1 @CompanyLineGuid = LineGuid
        FROM tblQuoteOptions
        WHERE QuoteOptionGuid = @QuoteOptionGuid;
        
        PRINT 'Retrieved LineGuid from tblQuoteOptions: ' + CAST(ISNULL(@CompanyLineGuid, '00000000-0000-0000-0000-000000000000') AS NVARCHAR(50));
    END
    
    -- Determine what ProgramID should be based on market segment and line
    IF @market_segment_code = 'RT' AND @CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4'
        SET @NewProgramID = 11615;  -- RT + Primary
    ELSE IF @market_segment_code = 'WL' AND @CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4'
        SET @NewProgramID = 11613;  -- WL + Primary
    ELSE IF @market_segment_code = 'RT' AND @CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31'
        SET @NewProgramID = 11612;  -- RT + Excess
    ELSE IF @market_segment_code = 'WL' AND @CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31'
        SET @NewProgramID = 11614;  -- WL + Excess
    
    -- Log what we're about to do
    PRINT 'ProgramID Assignment:';
    PRINT '  Market Segment: ' + ISNULL(@market_segment_code, 'NULL');
    PRINT '  CompanyLineGuid: ' + ISNULL(CAST(@CompanyLineGuid AS NVARCHAR(50)), 'NULL');
    PRINT '  New ProgramID: ' + ISNULL(CAST(@NewProgramID AS NVARCHAR(10)), 'NULL');
   
    -- Now set the ProgramID
    IF @NewProgramID IS NOT NULL
    BEGIN
        -- Check if tblQuoteDetails exists
        IF EXISTS (SELECT 1 FROM tblQuoteDetails WHERE QuoteGuid = @QuoteGuid)
        BEGIN
            -- Update existing record
            UPDATE tblQuoteDetails
            SET ProgramID = @NewProgramID
            WHERE QuoteGuid = @QuoteGuid;
            
            PRINT 'Updated ProgramID to ' + CAST(@NewProgramID AS NVARCHAR(10)) + ' in existing tblQuoteDetails record';
        END
        ELSE
        BEGIN
            -- tblQuoteDetails doesn't exist yet - create it with the ProgramID
            PRINT 'WARNING: tblQuoteDetails does not exist for this quote';
            
            -- Get the QuoteID from tblQuotes (needed for insert)
            DECLARE @QuoteID INT;
            SELECT @QuoteID = QuoteID FROM tblQuotes WHERE QuoteGuid = @QuoteGuid;
            
            IF @QuoteID IS NOT NULL
            BEGIN
                -- Insert a basic tblQuoteDetails record with the ProgramID
                INSERT INTO tblQuoteDetails (
                    QuoteID,
                    QuoteGuid,
                    ProgramID,
                    ProducerCommission,
                    CompanyCommission,
                    DateCreated
                ) VALUES (
                    @QuoteID,
                    @QuoteGuid,
                    @NewProgramID,
                    ISNULL(@commission_rate / 100.0, 0),  -- Convert to decimal if needed
                    ISNULL(@commission_percent / 100.0, 0),  -- Convert to decimal if needed
                    GETDATE()
                );
                
                PRINT 'Created tblQuoteDetails record with ProgramID ' + CAST(@NewProgramID AS NVARCHAR(10));
            END
            ELSE
            BEGIN
                PRINT 'ERROR: Cannot create tblQuoteDetails - QuoteID not found';
            END
        END
    END
    ELSE
    BEGIN
        PRINT 'Warning: No matching ProgramID rule for market_segment_code ''' + ISNULL(@market_segment_code, 'NULL') + 
              ''' and LineGuid ''' + ISNULL(CAST(@CompanyLineGuid AS NVARCHAR(50)), 'NULL') + '''';
    END
END