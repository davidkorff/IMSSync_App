CREATE OR ALTER   PROCEDURE [dbo].[ProcessFlatReinstatement]
    @OriginalQuoteGuid UNIQUEIDENTIFIER,
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
        DECLARE @OriginalExpirationDate DATETIME;
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
       
        -- Get the cancelled quote details
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
       
        -- Verify quote is cancelled (Status 7=Pending Cancel, 12=Cancelled) to allow reinstatement
        IF @CurrentQuoteStatusID NOT IN (7, 12)
        BEGIN
            RAISERROR('Quote must be in cancelled status to reinstate', 16, 1);
            RETURN;
        END
       
        -- Store original expiration date from the original bound policy
        -- Find the original bound quote to get the true expiration date
        SELECT TOP 1 @OriginalExpirationDate = ExpirationDate
        FROM tblQuotes
        WHERE ControlNo = @ControlNo
            AND QuoteStatusID IN (3, 4)  -- Bound status
            AND TransactionTypeID IN ('N', 'R')  -- New business or renewal
        ORDER BY DateCreated DESC;
       
        -- If no original expiration found, use the expiration from cancelled quote
        IF @OriginalExpirationDate IS NULL
            SET @OriginalExpirationDate = @ExpirationDate;
       
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
        IF @ReinstatementEffectiveDate < @EffectiveDate
        BEGIN
            RAISERROR('Reinstatement date cannot be before original policy effective date', 16, 1);
            RETURN;
        END
       
        IF @ReinstatementEffectiveDate > @OriginalExpirationDate
        BEGIN
            RAISERROR('Reinstatement date cannot be after original policy expiration date', 16, 1);
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
        -- CREATE NEW QUOTE FOR REINSTATEMENT
        -- =============================================
       
        IF @NewQuoteGuid IS NULL
            SET @NewQuoteGuid = NEWID();
       
        -- Get UserID from UserGuid if provided
        DECLARE @UserID INT = NULL;
        IF @UserGuid IS NOT NULL
            SELECT @UserID = UserID FROM tblUsers WHERE UserGuid = @UserGuid;
       
        -- Insert the reinstatement quote as PENDING REINSTATEMENT (Status 8)
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
            'R',                         -- TransactionTypeID = 'R' for Reinstatement
            @SubmissionGroupGuid,
            @CompanyLocationGuid,
            @CompanyLineGuid,
            @LineGuid,
            @StateID,
            @ProducerContactGuid,
            @ProducerLocationID,
            @UnderwriterUserGuid,
            @RetailerGuid,
            8,                           -- QuoteStatusID = 8 (Pending Reinstatement)
            NULL,                        -- No status reason needed for reinstatement
            @EffectiveDate,              -- Preserve original policy effective date
            @OriginalExpirationDate,     -- Use original policy expiration
            @PolicyTypeID,
            @PolicyNumber,
            @QuotingLocationGuid,
            @IssuingLocationGuid,
            @ReinstatementEffectiveDate, -- Endorsement effective = reinstatement date
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
       
        -- Insert new quote option as UNBOUND initially
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
            0,                           -- NOT BOUND YET (to avoid trigger)
            0,
            'Flat Reinstatement - ' + @ReinstatementComment,
            @CompanyInstallmentID
        );
       
        -- =============================================
        -- SET UP REINSTATEMENT PREMIUM
        -- =============================================
       
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
       
        -- Calculate prorated premium if needed
        DECLARE @DaysRemaining INT;
        DECLARE @TotalDays INT;
        DECLARE @ProratedPremium MONEY;
       
        SET @DaysRemaining = DATEDIFF(DAY, @ReinstatementEffectiveDate, @OriginalExpirationDate);
        SET @TotalDays = DATEDIFF(DAY, @EffectiveDate, @OriginalExpirationDate);
       
        -- Use provided premium or calculate prorated
        IF @ReinstatementPremium IS NOT NULL
            SET @ProratedPremium = @ReinstatementPremium;
        ELSE
        BEGIN
            -- Calculate prorated premium based on original premium
            DECLARE @OriginalPremium MONEY = 0;
            SELECT @OriginalPremium = ISNULL(SUM(qop.Premium), 0)
            FROM tblQuoteOptionPremiums qop
            INNER JOIN tblQuoteOptions qo ON qop.QuoteOptionGuid = qo.QuoteOptionGuid
            WHERE qo.QuoteGuid = @OriginalQuoteGuid
                AND qo.Bound = 1;
           
            SET @ProratedPremium = (@OriginalPremium * @DaysRemaining) / NULLIF(@TotalDays, 0);
        END
       
        -- Insert the reinstatement premium record
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
            @ProratedPremium,            -- Reinstatement premium
            @ProratedPremium,            -- Annual = same as premium for flat
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
       
        COMMIT TRANSACTION;
       
        -- Return success with detailed information
        SELECT
            'Success' AS Result,
            @PolicyNumber AS PolicyNumber,
            @OriginalQuoteGuid AS OriginalQuoteGuid,
            @NewQuoteGuid AS NewQuoteGuid,
            @NextEndorsementNum AS EndorsementNumber,
            @ProratedPremium AS ReinstatementPremium,
            @ReinstatementEffectiveDate AS EffectiveDate,
            @OriginalExpirationDate AS ExpirationDate,
            @DaysRemaining AS DaysRemaining,
            @MainChargeCode AS ChargeCode,
            'Reinstatement created (Status 8 - Pending Reinstatement). Ready for binding via web service.' AS Instructions;
           
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






