-- =============================================
-- Flat Reinstatement Procedure
-- Reinstates a cancelled policy
-- =============================================

CREATE OR ALTER PROCEDURE [dbo].[ProcessFlatReinstatement]
    @OpportunityID INT = NULL,
    @CancelledQuoteGuid UNIQUEIDENTIFIER = NULL,
    @ReinstatementPremium MONEY,
    @ReinstatementEffectiveDate DATETIME,
    @ReinstatementComment VARCHAR(500) = 'Policy Reinstatement',
    @UserGuid UNIQUEIDENTIFIER = NULL,
    @NewQuoteGuid UNIQUEIDENTIFIER = NULL OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- =============================================
        -- VALIDATION SECTION
        -- =============================================
        
        -- Variables to store quote information
        DECLARE @OriginalQuoteGuid UNIQUEIDENTIFIER;
        DECLARE @ControlNo INT;
        DECLARE @ControlGuid UNIQUEIDENTIFIER;
        DECLARE @PolicyNumber VARCHAR(50);
        DECLARE @CompanyLocationGuid UNIQUEIDENTIFIER;
        DECLARE @LineGuid UNIQUEIDENTIFIER;
        DECLARE @StateID CHAR(2);
        DECLARE @ProducerContactGuid UNIQUEIDENTIFIER;
        DECLARE @ProducerLocationID INT;
        DECLARE @EffectiveDate DATETIME;
        DECLARE @ExpirationDate DATETIME;
        DECLARE @CurrentQuoteStatusID INT;
        DECLARE @PolicyTypeID TINYINT;
        DECLARE @QuotingLocationGuid UNIQUEIDENTIFIER;
        DECLARE @IssuingLocationGuid UNIQUEIDENTIFIER;
        DECLARE @SubmissionGroupGuid UNIQUEIDENTIFIER;
        DECLARE @UnderwriterUserGuid UNIQUEIDENTIFIER;
        DECLARE @RetailerGuid UNIQUEIDENTIFIER;
        DECLARE @TACSRUserGuid UNIQUEIDENTIFIER;
        DECLARE @BillingTypeID INT;
        DECLARE @MinimumEarnedPercentage DECIMAL(5,2);
        DECLARE @CompanyLineGuid UNIQUEIDENTIFIER;
        DECLARE @OfficeID INT;
        DECLARE @CostCenterID INT;
        DECLARE @CompanyInstallmentID INT;
        DECLARE @QuoteID INT;
        DECLARE @CancellationQuoteGuid UNIQUEIDENTIFIER;
        
        -- Insured information
        DECLARE @SIC_Code VARCHAR(10);
        DECLARE @InsuredDBA VARCHAR(255);
        DECLARE @InsuredFEIN VARCHAR(20);
        DECLARE @InsuredSSN VARCHAR(20);
        DECLARE @InsuredBusinessTypeID INT;
        DECLARE @InsuredPolicyName VARCHAR(255);
        DECLARE @InsuredCorporationName VARCHAR(255);
        DECLARE @InsuredSalutation VARCHAR(50);
        DECLARE @InsuredFirstName VARCHAR(50);
        DECLARE @InsuredMiddleName VARCHAR(50);
        DECLARE @InsuredLastName VARCHAR(50);
        DECLARE @InsuredAddress1 VARCHAR(255);
        DECLARE @InsuredAddress2 VARCHAR(255);
        DECLARE @InsuredCity VARCHAR(100);
        DECLARE @InsuredCounty VARCHAR(100);
        DECLARE @InsuredState CHAR(2);
        DECLARE @InsuredISOCountryCode CHAR(3);
        DECLARE @InsuredRegion VARCHAR(100);
        DECLARE @InsuredZipCode VARCHAR(10);
        DECLARE @InsuredZipPlus VARCHAR(10);
        DECLARE @InsuredPhone VARCHAR(20);
        DECLARE @InsuredFax VARCHAR(20);
        
        -- Find the cancelled quote
        IF @OpportunityID IS NOT NULL
        BEGIN
            -- Find by opportunity_id - get the most recent cancelled quote
            SELECT TOP 1 
                @CancellationQuoteGuid = q.QuoteGuid,
                @ControlNo = q.ControlNo,
                @PolicyNumber = q.PolicyNumber,
                @OriginalQuoteGuid = q.OriginalQuoteGuid
            FROM tblTritonQuoteData tq
            INNER JOIN tblQuotes q ON q.QuoteGUID = tq.QuoteGuid
            WHERE tq.opportunity_id = @OpportunityID
            AND q.QuoteStatusID = 7  -- Cancelled status
            AND q.TransactionTypeID = 'C'  -- Cancellation transaction
            ORDER BY q.QuoteID DESC
        END
        ELSE IF @CancelledQuoteGuid IS NOT NULL
        BEGIN
            -- Find by QuoteGuid
            SELECT 
                @CancellationQuoteGuid = QuoteGuid,
                @ControlNo = ControlNo,
                @PolicyNumber = PolicyNumber,
                @OriginalQuoteGuid = OriginalQuoteGuid
            FROM tblQuotes
            WHERE QuoteGuid = @CancelledQuoteGuid
            AND QuoteStatusID = 7  -- Cancelled status
        END
        
        IF @CancellationQuoteGuid IS NULL
        BEGIN
            RAISERROR('No cancelled policy found for reinstatement', 16, 1);
            RETURN;
        END
        
        -- Get details from the original (pre-cancellation) quote
        IF @OriginalQuoteGuid IS NULL
        BEGIN
            -- If no OriginalQuoteGuid in cancellation, find the last bound quote before cancellation
            SELECT TOP 1 @OriginalQuoteGuid = QuoteGuid
            FROM tblQuotes
            WHERE ControlNo = @ControlNo
            AND QuoteStatusID IN (3, 4)  -- Bound or Issued
            AND TransactionTypeID IN ('N', 'R', 'E')  -- New, Renewal, or Endorsement
            ORDER BY QuoteID DESC
        END
        
        -- Get all details from the original quote
        SELECT 
            @ControlGuid = ControlGuid,
            @CompanyLocationGuid = CompanyLocationGuid,
            @LineGuid = LineGuid,
            @CompanyLineGuid = CompanyLineGuid,
            @StateID = StateID,
            @ProducerContactGuid = ProducerContactGuid,
            @ProducerLocationID = ProducerLocationID,
            @EffectiveDate = EffectiveDate,
            @ExpirationDate = ExpirationDate,
            @PolicyTypeID = PolicyTypeID,
            @QuotingLocationGuid = QuotingLocationGuid,
            @IssuingLocationGuid = IssuingLocationGuid,
            @SubmissionGroupGuid = SubmissionGroupGuid,
            @UnderwriterUserGuid = UnderwriterUserGuid,
            @RetailerGuid = RetailerGuid,
            @TACSRUserGuid = TACSRUserGuid,
            @BillingTypeID = BillingTypeID,
            @MinimumEarnedPercentage = MinimumEarnedPercentage,
            @CostCenterID = CostCenterID,
            @QuoteID = QuoteID,
            @SIC_Code = SIC_Code,
            @InsuredDBA = InsuredDBA,
            @InsuredFEIN = InsuredFEIN,
            @InsuredSSN = InsuredSSN,
            @InsuredBusinessTypeID = InsuredBusinessTypeID,
            @InsuredPolicyName = InsuredPolicyName,
            @InsuredCorporationName = InsuredCorporationName,
            @InsuredSalutation = InsuredSalutation,
            @InsuredFirstName = InsuredFirstName,
            @InsuredMiddleName = InsuredMiddleName,
            @InsuredLastName = InsuredLastName,
            @InsuredAddress1 = InsuredAddress1,
            @InsuredAddress2 = InsuredAddress2,
            @InsuredCity = InsuredCity,
            @InsuredCounty = InsuredCounty,
            @InsuredState = InsuredState,
            @InsuredISOCountryCode = InsuredISOCountryCode,
            @InsuredRegion = InsuredRegion,
            @InsuredZipCode = InsuredZipCode,
            @InsuredZipPlus = InsuredZipPlus,
            @InsuredPhone = InsuredPhone,
            @InsuredFax = InsuredFax
        FROM tblQuotes
        WHERE QuoteGuid = @OriginalQuoteGuid;
        
        IF @ControlNo IS NULL
        BEGIN
            RAISERROR('Original quote details not found', 16, 1);
            RETURN;
        END
        
        -- Get Office ID for premium records
        SELECT @OfficeID = OfficeID 
        FROM tblClientOffices 
        WHERE OfficeGuid = @QuotingLocationGuid;
        
        -- Default Office ID if not found
        IF @OfficeID IS NULL
            SET @OfficeID = 1;
        
        -- Get CompanyInstallmentID from original quote option
        SELECT TOP 1 @CompanyInstallmentID = CompanyInstallmentID
        FROM tblQuoteOptions
        WHERE QuoteGuid = @OriginalQuoteGuid
            AND Bound = 1;
        
        -- Validate reinstatement date
        IF @ReinstatementEffectiveDate < @EffectiveDate OR @ReinstatementEffectiveDate > @ExpirationDate
        BEGIN
            RAISERROR('Reinstatement date must be within policy period', 16, 1);
            RETURN;
        END
        
        -- =============================================
        -- CALCULATE REINSTATEMENT NUMBER
        -- =============================================
        
        DECLARE @NextReinstatementNum INT;
        SELECT @NextReinstatementNum = ISNULL(MAX(EndorsementNum), 0) + 1
        FROM tblQuotes
        WHERE ControlNo = @ControlNo;
        
        -- =============================================
        -- CREATE NEW QUOTE FOR REINSTATEMENT (AS UNBOUND!)
        -- =============================================
        
        IF @NewQuoteGuid IS NULL
            SET @NewQuoteGuid = NEWID();
        
        -- Get UserID from UserGuid if provided
        DECLARE @UserID INT = NULL;
        IF @UserGuid IS NOT NULL
            SELECT @UserID = UserID FROM tblUsers WHERE UserGuid = @UserGuid;
        
        -- Insert the reinstatement quote as UNBOUND (Status 8 = Pending Reinstatement)
        INSERT INTO tblQuotes (
            QuoteGuid,
            ControlNo,
            ControlGuid,
            OriginalQuoteGuid,
            EndorsementNum,
            TransactionTypeID,
            SubmissionGroupGuid,
            CompanyLocationGuid,
            CompanyLineGuid,
            LineGuid,
            StateID,
            ProducerContactGuid,
            ProducerLocationID,
            UnderwriterUserGuid,
            RetailerGuid,
            QuoteStatusID,
            QuoteStatusReasonID,
            EffectiveDate,
            ExpirationDate,
            PolicyTypeID,
            PolicyNumber,
            QuotingLocationGuid,
            IssuingLocationGuid,
            EndorsementEffective,
            EndorsementCalculationType,
            EndorsementComment,
            DateCreated,
            TACSRUserGuid,
            BillingTypeID,
            MinimumEarnedPercentage,
            CostCenterID,
            SIC_Code,
            InsuredDBA,
            InsuredFEIN,
            InsuredSSN,
            InsuredBusinessTypeID,
            InsuredPolicyName,
            InsuredCorporationName,
            InsuredSalutation,
            InsuredFirstName,
            InsuredMiddleName,
            InsuredLastName,
            InsuredAddress1,
            InsuredAddress2,
            InsuredCity,
            InsuredCounty,
            InsuredState,
            InsuredISOCountryCode,
            InsuredRegion,
            InsuredZipCode,
            InsuredZipPlus,
            InsuredPhone,
            InsuredFax
        )
        VALUES (
            @NewQuoteGuid,
            @ControlNo,
            @ControlGuid,
            @OriginalQuoteGuid,
            @NextReinstatementNum,
            'W',                         -- W = Reinstatement
            @SubmissionGroupGuid,
            @CompanyLocationGuid,
            @CompanyLineGuid,
            @LineGuid,
            @StateID,
            @ProducerContactGuid,
            @ProducerLocationID,
            @UnderwriterUserGuid,
            @RetailerGuid,
            8,                           -- STATUS 8 = PENDING REINSTATEMENT
            NULL,
            @EffectiveDate,
            @ExpirationDate,
            @PolicyTypeID,
            @PolicyNumber,
            @QuotingLocationGuid,
            @IssuingLocationGuid,
            @ReinstatementEffectiveDate,
            'F',                         -- Flat calculation
            @ReinstatementComment,
            GETDATE(),
            @TACSRUserGuid,
            @BillingTypeID,
            @MinimumEarnedPercentage,
            @CostCenterID,
            @SIC_Code,
            @InsuredDBA,
            @InsuredFEIN,
            @InsuredSSN,
            @InsuredBusinessTypeID,
            @InsuredPolicyName,
            @InsuredCorporationName,
            @InsuredSalutation,
            @InsuredFirstName,
            @InsuredMiddleName,
            @InsuredLastName,
            @InsuredAddress1,
            @InsuredAddress2,
            @InsuredCity,
            @InsuredCounty,
            @InsuredState,
            @InsuredISOCountryCode,
            @InsuredRegion,
            @InsuredZipCode,
            @InsuredZipPlus,
            @InsuredPhone,
            @InsuredFax
        );
        
        -- Get the new QuoteID
        DECLARE @NewQuoteID INT;
        SELECT @NewQuoteID = QuoteID FROM tblQuotes WHERE QuoteGuid = @NewQuoteGuid;
        
        -- =============================================
        -- CREATE QUOTE OPTION WITH INSTALLMENT INFO
        -- =============================================
        
        DECLARE @NewQuoteOptionGuid UNIQUEIDENTIFIER = NEWID();
        
        -- Get Line details for quote option
        DECLARE @LineName VARCHAR(100);
        DECLARE @LineID INT;
        SELECT @LineName = LineName, @LineID = LineID 
        FROM lstLines 
        WHERE LineGuid = @LineGuid;
        
        INSERT INTO tblQuoteOptions (
            QuoteOptionGuid,
            QuoteGuid,
            LineGuid,
            LineName,
            CompanyLocationGuid,
            PolicyNumber,
            Premium,
            Taxes,
            Fees,
            OtherCharges,
            CompanyInstallmentID,
            DateCreated,
            Bound,
            FullyEarned
        )
        VALUES (
            @NewQuoteOptionGuid,
            @NewQuoteGuid,
            @LineGuid,
            @LineName,
            @CompanyLocationGuid,
            @PolicyNumber,
            @ReinstatementPremium,       -- Use the reinstatement premium
            0,                           -- Taxes
            0,                           -- Fees
            0,                           -- OtherCharges
            @CompanyInstallmentID,
            GETDATE(),
            0,                           -- Not bound yet
            0                            -- Not fully earned
        );
        
        -- =============================================
        -- CREATE PREMIUM RECORD
        -- =============================================
        
        INSERT INTO tblPremiums (
            QuoteOptionGuid,
            StateID,
            Premium,
            AgentCommission,
            ProducerContactGuid,
            ProducerLocationID,
            CompanyLocationGuid,
            OfficeID,
            CostCenterID,
            PolicyNumber,
            InsuredName,
            OriginalQuoteGuid
        )
        VALUES (
            @NewQuoteOptionGuid,
            @StateID,
            @ReinstatementPremium,
            0,                           -- Will be calculated separately
            @ProducerContactGuid,
            @ProducerLocationID,
            @CompanyLocationGuid,
            @OfficeID,
            @CostCenterID,
            @PolicyNumber,
            COALESCE(@InsuredCorporationName, @InsuredFirstName + ' ' + @InsuredLastName),
            @OriginalQuoteGuid
        );
        
        -- =============================================
        -- UNBIND CANCELLATION (Optional - based on business rules)
        -- =============================================
        
        -- Uncomment if you need to unbind the cancellation
        /*
        UPDATE tblQuoteOptions 
        SET Bound = 0, DateBound = NULL
        WHERE QuoteGuid = @CancellationQuoteGuid;
        
        UPDATE tblQuotes
        SET QuoteStatusID = 7  -- Keep as cancelled but unbound
        WHERE QuoteGuid = @CancellationQuoteGuid;
        */
        
        -- =============================================
        -- RETURN RESULTS
        -- =============================================
        
        -- Calculate premium change from cancellation
        DECLARE @CancellationPremium MONEY = 0;
        SELECT @CancellationPremium = ISNULL(Premium, 0)
        FROM tblQuoteOptions
        WHERE QuoteGuid = @CancellationQuoteGuid;
        
        -- Return success with details
        SELECT 
            1 AS Result,
            'Reinstatement created successfully' AS Message,
            @NewQuoteGuid AS NewQuoteGuid,
            @NewQuoteOptionGuid AS QuoteOptionGuid,
            @OriginalQuoteGuid AS OriginalQuoteGuid,
            @CancellationQuoteGuid AS CancellationQuoteGuid,
            @PolicyNumber AS PolicyNumber,
            @NextReinstatementNum AS ReinstatementNumber,
            @ReinstatementPremium AS ReinstatementPremium,
            ABS(@CancellationPremium) AS CancellationRefund,
            (@ReinstatementPremium + ABS(@CancellationPremium)) AS NetPremiumChange
        
        COMMIT TRANSACTION;
        
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        
        -- Return error
        SELECT 
            0 AS Result,
            ERROR_MESSAGE() AS Message,
            NULL AS NewQuoteGuid,
            NULL AS QuoteOptionGuid,
            NULL AS OriginalQuoteGuid,
            NULL AS CancellationQuoteGuid,
            NULL AS PolicyNumber,
            NULL AS ReinstatementNumber,
            NULL AS ReinstatementPremium,
            NULL AS CancellationRefund,
            NULL AS NetPremiumChange
        
        THROW;
    END CATCH
END