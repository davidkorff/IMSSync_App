CREATE OR ALTER   PROCEDURE [dbo].[ProcessFlatEndorsement]
    @OriginalQuoteGuid UNIQUEIDENTIFIER,
    @NewPremium MONEY,
    @EndorsementEffectiveDate DATETIME,
    @EndorsementComment VARCHAR(500) = 'Flat Premium Endorsement',
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
       
        -- Get original quote details
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
       
        SELECT
            @ControlNo = ControlNo,
            @ControlGuid = ControlGuid,
            @PolicyNumber = PolicyNumber,
            @CompanyLocationGuid = CompanyLocationGuid,
            @LineGuid = LineGuid,
            @CompanyLineGuid = CompanyLineGuid,
            @StateID = StateID,
            @ProducerContactGuid = ProducerContactGuid,
            @ProducerLocationID = ProducerLocationID,
            @EffectiveDate = EffectiveDate,
            @ExpirationDate = ExpirationDate,
            @CurrentQuoteStatusID = QuoteStatusID,
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
            RAISERROR('Original quote not found', 16, 1);
            RETURN;
        END
       
        -- Verify quote is bound (Status 3 or 4) or cancelled (Status 12)
        IF @CurrentQuoteStatusID NOT IN (3, 4, 12)
        BEGIN
            RAISERROR('Quote must be in bound or cancelled status to endorse', 16, 1);
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
       
        -- Validate endorsement date
        IF @EndorsementEffectiveDate < @EffectiveDate OR @EndorsementEffectiveDate > @ExpirationDate
        BEGIN
            RAISERROR('Endorsement date must be within policy period', 16, 1);
            RETURN;
        END
       
        -- =============================================
        -- CALCULATE ENDORSEMENT NUMBER
        -- =============================================
       
        DECLARE @NextEndorsementNum INT;
        SELECT @NextEndorsementNum = ISNULL(MAX(EndorsementNum), 0) + 1
        FROM tblQuotes
        WHERE ControlNo = @ControlNo;
       
        -- =============================================
        -- CREATE NEW QUOTE FOR ENDORSEMENT (AS UNBOUND!)
        -- =============================================
       
        IF @NewQuoteGuid IS NULL
            SET @NewQuoteGuid = NEWID();
       
        -- Get UserID from UserGuid if provided
        DECLARE @UserID INT = NULL;
        IF @UserGuid IS NOT NULL
            SELECT @UserID = UserID FROM tblUsers WHERE UserGuid = @UserGuid;
       
        -- Insert the endorsement quote as UNBOUND (Status 9)
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
            @NextEndorsementNum,
            'E',
            @SubmissionGroupGuid,
            @CompanyLocationGuid,
            @CompanyLineGuid,
            @LineGuid,
            @StateID,
            @ProducerContactGuid,
            @ProducerLocationID,
            @UnderwriterUserGuid,
            @RetailerGuid,
            9,                           -- STATUS 9 = UNBOUND ENDORSEMENT
            NULL,
            @EffectiveDate,
            @ExpirationDate,
            @PolicyTypeID,
            @PolicyNumber,
            @QuotingLocationGuid,
            @IssuingLocationGuid,
            @EndorsementEffectiveDate,
            'F',                         -- Flat calculation
            @EndorsementComment,
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
        DECLARE @OriginalQuoteOptionGuid UNIQUEIDENTIFIER;
        DECLARE @CompanyLocationID INT;
       
        -- Get original quote option info
        SELECT TOP 1
            @OriginalQuoteOptionGuid = QuoteOptionGuid,
            @CompanyLocationID = CompanyLocationID,
            @CompanyInstallmentID = CompanyInstallmentID
        FROM tblQuoteOptions
        WHERE QuoteGuid = @OriginalQuoteGuid
            AND Bound = 1;
       
        -- Insert new quote option with CompanyInstallmentID
        INSERT INTO tblQuoteOptions (
            QuoteOptionGuid,
            OriginalQuoteOptionGuid,
            QuoteGuid,
            LineGuid,
            CompanyLocationID,
            DateCreated,
            Bound,
            Quote,
            AdditionalComments,
            CompanyInstallmentID
        )
        VALUES (
            @NewQuoteOptionGuid,
            @OriginalQuoteOptionGuid,
            @NewQuoteGuid,
            @LineGuid,
            @CompanyLocationID,
            GETDATE(),
            0,                           -- NOT BOUND YET
            0,
            'Flat Endorsement - ' + @EndorsementComment,
            @CompanyInstallmentID        -- Copy from original
        );
       
        -- =============================================
        -- SET UP PREMIUMS FOR ENDORSEMENT
        -- =============================================
       
        -- Calculate premium difference for endorsement
        DECLARE @OriginalPremium MONEY = 0;
        SELECT @OriginalPremium = ISNULL(SUM(qop.Premium), 0)
        FROM tblQuoteOptionPremiums qop
        INNER JOIN tblQuoteOptions qo ON qop.QuoteOptionGuid = qo.QuoteOptionGuid
        WHERE qo.QuoteGuid = @OriginalQuoteGuid
            AND qo.Bound = 1;
       
        DECLARE @PremiumChange MONEY = @NewPremium - @OriginalPremium;
       
        -- For flat endorsement, insert only the premium change
        -- Get the main charge code from original
        DECLARE @MainChargeCode INT;
        SELECT TOP 1 @MainChargeCode = qop.ChargeCode
        FROM tblQuoteOptionPremiums qop
        INNER JOIN tblQuoteOptions qo ON qop.QuoteOptionGuid = qo.QuoteOptionGuid
        WHERE qo.QuoteGuid = @OriginalQuoteGuid
            AND qo.Bound = 1
        ORDER BY qop.Premium DESC;
       
        -- Default charge code if none found
        IF @MainChargeCode IS NULL
            SET @MainChargeCode = 1;
       
        -- Insert the premium change record
        INSERT INTO tblQuoteOptionPremiums (
            QuoteOptionGuid,
            ChargeCode,
            OfficeID,
            Premium,
            AnnualPremium,
            Commissionable,
            Added
        )
        VALUES (
            @NewQuoteOptionGuid,
            @MainChargeCode,
            @OfficeID,
            @PremiumChange,              -- The CHANGE in premium
            @PremiumChange,              -- Annual = same as premium for flat
            1,                           -- Commissionable
            GETDATE()
        );
       
        -- =============================================
        -- COPY QUOTE DETAILS (For commission tracking)
        -- =============================================
       
        IF OBJECT_ID('tblQuoteDetails', 'U') IS NOT NULL
        BEGIN
            -- Copy quote details with existing commission rates
            INSERT INTO tblQuoteDetails (
                QuoteGuid,
                CompanyLineGuid,
                CompanyContactGuid,
                CompanyCommission,
                ProducerCommission,
                RaterID,
                TermsOfPayment,
                ProgramID
            )
            SELECT
                @NewQuoteGuid,
                CompanyLineGuid,
                CompanyContactGuid,
                CompanyCommission,
                ProducerCommission,
                RaterID,
                TermsOfPayment,
                ProgramID
            FROM tblQuoteDetails
            WHERE QuoteGuid = @OriginalQuoteGuid;
        END
       
        -- =============================================
        -- NOTE: NOT copying tblQuoteOptionCharges
        -- For flat endorsement, fees are typically not changed
        -- The web service will handle any necessary fee generation during binding
        -- =============================================
       
        COMMIT TRANSACTION;
       
        -- Return success with detailed information
        SELECT
            'Success' AS Result,
            @PolicyNumber AS PolicyNumber,
            @OriginalQuoteGuid AS OriginalQuoteGuid,
            @NewQuoteGuid AS NewQuoteGuid,
            @NextEndorsementNum AS EndorsementNumber,
            @OriginalPremium AS OriginalPremium,
            @NewPremium AS NewPremium,
            @PremiumChange AS PremiumChange,
            @EndorsementEffectiveDate AS EffectiveDate,
            @CompanyInstallmentID AS InstallmentID,
            @MainChargeCode AS ChargeCode,
            'Endorsement created (Status 9). Ready for binding via web service.' AS Instructions;
           
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
           
        -- Return error details
        SELECT
            'Error' AS Result,
            ERROR_MESSAGE() AS ErrorMessage,
            ERROR_LINE() AS ErrorLine,
            ERROR_PROCEDURE() AS ErrorProcedure,
            ERROR_NUMBER() AS ErrorNumber;
           
        -- Re-raise the error
        THROW;
    END CATCH
END






