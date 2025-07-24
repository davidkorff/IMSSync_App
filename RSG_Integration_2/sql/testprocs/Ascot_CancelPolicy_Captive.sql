USE [Greyhawk_Test]
GO
/****** Object:  StoredProcedure [dbo].[Ascot_CancelPolicy_Captive]    Script Date: 7/17/2025 10:15:16 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

ALTER PROCEDURE [dbo].[Ascot_CancelPolicy_Captive]
(
      @QuoteGuid UNIQUEIDENTIFIER,
      @TransEffDate DATETIME,
      @Comment VARCHAR(50),
      @EndorsementCalcType CHAR(1),
      @NewPremium MONEY,
      @QuoteStatusReasonID INT,
      @DateBound DATETIME,
      @UserGuid UNIQUEIDENTIFIER,
      @BillingCode CHAR(5),
      @AutoApplyFees bit,
	  @DnlTrId uniqueidentifier,
	  @BrokerCommissionFeeChargeCode int,
	  @TerrorismPremium money,
	  @CopyOptions BIT

)
AS
BEGIN

      SET NOCOUNT ON

      DECLARE @ControlNumber INT
	  DECLARE @EndorsementQuoteID INT
	  DECLARE @EndorsementQuoteGuid UNIQUEIDENTIFIER
      DECLARE @OfficeID INT
	  DECLARE @CompanyLineGuid uniqueidentifier
	  DECLARE @PolicyEffectiveDate datetime

      SELECT
            @ControlNumber = Q.ControlNo,
            @OfficeID = tblClientOffices.OfficeID,
			@CompanyLineGuid = Q.CompanyLineGuid,
			@PolicyEffectiveDate = Q.EffectiveDate
		FROM	tblQuotes Q
		INNER JOIN tblClientOffices ON Q.QuotingLocationGuid = tblClientOffices.OfficeGuid
		WHERE	Q.QuoteGuid = @QuoteGuid

	  --Check for data errors and throw exception
	  IF (NOT EXISTS(SELECT * FROM lstQuoteStatusReasons where QuoteStatusID = 7 AND ID = @QuoteStatusReasonID))
		RAISERROR('Invalid Quote Status Reason Id',15,1)

      BEGIN TRANSACTION

		IF OBJECT_ID('tempdb..#InvoiceInstallmentsTable') IS NOT NULL
		BEGIN

			DROP TABLE #InvoiceInstallmentsTable

		END

		CREATE TABLE #InvoiceInstallmentsTable
		(
			QuoteID int,
			EffectiveDate datetime,
			ExpirationDate datetime,
			NumInstallments int,
			Installment int,
			InstallmentDueDate datetime,
			BillingCode varchar(100),
			InstallmentMod decimal(20, 19)
		)

      DECLARE @CatchNewQuoteGuid TABLE
	(
		NewQuoteGuid uniqueidentifier
	)

    --Create the endorsement record
	INSERT INTO @CatchNewQuoteGuid
      EXEC  spCopyQuote
                  @QuoteGuid = @QuoteGuid,
                  @TransactionTypeID = 'C',
                  @QuoteStatusID = 7,
                  @QuoteStatusReasonID = @QuoteStatusReasonID,
                  @EndorsementEffective = @TransEffDate,
                  @EndtRequestDate = @DateBound,
                  @EndorsementComment = @Comment,
                  @EndorsementCalculationType = @EndorsementCalcType,
				  @copyOptions = @copyOptions
	  
      --Get the Endorsement Quote Guid
      SELECT TOP 1 @EndorsementQuoteGuid = Q.QuoteGuid, @EndorsementQuoteID = Q.QuoteID FROM tblQuotes Q WHERE ControlNo = @ControlNumber ORDER BY QuoteId DESC

	 --TFS 87687  Call Ascot custom spcopyquote.	
	EXEC  GreyHawk_spCopyQuote
			@newQuoteGuid = @EndorsementQuoteGuid,
			@OldQuoteGuid = @QuoteGuid
    

    --Copy forward the quote option
	INSERT INTO
    tblQuoteOptions
    (
            QuoteOptionGUID,
            OriginalQuoteOptionGUID,
            QuoteGUID,
            LineGUID,
            CompanyLocationID,
            DateCreated,
            Bound,
            Quote,
            AdditionalComments,
            CompanyInstallmentID,
            AutoApplyFeeLog
    )
    SELECT
            NEWID(),
            QuoteOptionGUID,
            @EndorsementQuoteGuid,
            LineGUID,
            CompanyLocationID,
            GETDATE(),
            1,
            0,
            AdditionalComments,
            CompanyInstallmentID,
            AutoApplyFeeLog
    FROM
            tblQuoteOptions
    WHERE
            QuoteGUID = @QuoteGuid


	DECLARE @PremiumCursorQuoteOptionGuid uniqueidentifier
	DECLARE @PremiumCursorChargeCode int
	DECLARE @PremiumCursorOfficeID int
	DECLARE @PremiumCursorPremium money
	DECLARE @PremiumCursorCommissionable bit
	DECLARE @PremiumCursorAddedDate datetime


	DECLARE EndorsePremiumCursor Cursor FAST_FORWARD FORWARD_ONLY
	FOR SELECT	NewQuoteOptions.QuoteOptionGuid,
				ISNULL(ChargeCodeTable.ChargeCode, OptionPremiumTable.ChargeCode) AS ChargeCode,
				OptionPremiumTable.OfficeId,
				CASE WHEN NewPremiumTable.CompanyLocationCode IS NULL
					THEN CASE WHEN OptionPremiumTable.ChargeID = 'TERR' THEN @TerrorismPremium ELSE @NewPremium END
					ELSE CASE WHEN ChargeCodeTable.ChargeID = 'TERR' THEN NewPremiumTable.Terrorism ELSE NewPremiumTable.Premium END
				END,
				OptionPremiumTable.Commissionable,
				GETDATE()
		FROM	tblQuotes
		INNER JOIN tblQuoteOptions ON tblQuotes.QuoteGUID = tblQuoteOptions.QuoteGUID
		INNER JOIN tblQuoteOptions NewQuoteOptions ON NewQuoteOptions.OriginalQuoteOptionGuid = tblQuoteOptions.QuoteOptionGuid
		INNER JOIN tblQUotes NewQuoteOptionsQuote ON NewQuoteOptions.QuoteGuid = NewQuoteOptionsQuote.QuoteGuid -- TFS 89958  Added additional check to make sure quoteoptions are comming from the right control number.  We were getting
		-- duplicate quoteoptions prem error on some polciies prior to thsi additional check in BOLT policies.
		CROSS APPLY (
						SELECT TOP 1 SubQ.QuoteID
						FROM tblQuotes SubQ
						INNER JOIN tblQuoteOptions SubQO ON SubQ.QuoteGUID = SubQO.QuoteGUID
						INNER JOIN tblQuoteOptionPremiums ON SubQO.QuoteOptionGUID = tblQuoteOptionPremiums.QuoteOptionGuid
						WHERE SubQ.ControlNo = tblQuotes.ControlNo
						AND SubQ.QuoteID <= tblQuotes.QuoteID
						AND SubQO.LineGuid = tblQuoteOptions.LineGUID
					) As TopQuoteIDWithPremiumTable
		CROSS APPLY (
						SELECT DISTINCT SubPC.ChargeID
						FROM tblQuotes SubQ
						INNER JOIN tblQuoteOptions SubQO ON SubQ.QuoteGUID = SubQO.QuoteGUID
						INNER JOIN tblQuoteOptionPremiums ON SubQO.QuoteOptionGUID = tblQuoteOptionPremiums.QuoteOptionGuid
						INNER JOIN tblFin_PolicyCharges SubPC ON tblQuoteOptionPremiums.ChargeCode = SubPC.ChargeCode
						WHERE SubQ.QuoteID = TopQuoteIDWithPremiumTable.QuoteID
					) AS DistinctChargeIDsTable
		CROSS APPLY (
						SELECT TOP 1 tblQuoteOptionPremiums.OfficeID,
									tblQuoteOptionPremiums.Commissionable,
									tblFin_PolicyCharges.ChargeCode,
									tblFin_PolicyCharges.ChargeID,
									tblFin_PolicyCharges.StateID
						FROM tblQuotes SubQ
						INNER JOIN tblQuoteOptions SubQO ON SubQ.QuoteGUID = SubQO.QuoteGUID
						INNER JOIN tblQuoteOptionPremiums ON SubQO.QuoteOptionGUID = tblQuoteOptionPremiums.QuoteOptionGuid
						INNER JOIN tblFin_PolicyCharges ON tblQuoteOptionPremiums.ChargeCode = tblFin_PolicyCharges.ChargeCode
						WHERE SubQ.QuoteID = TopQuoteIDWithPremiumTable.QuoteID
						AND SubQO.LineGUID = tblQuoteOptions.LineGUID
						AND tblFin_PolicyCharges.ChargeID = DistinctChargeIDsTable.ChargeID
					) AS OptionPremiumTable
		INNER JOIN lstLines ON tblQuoteOptions.LineGuid = lstLines.LineGuid
		OUTER APPLY (
						SELECT	Ascot_AL3QuoteDetailTable_V2.Premium,
								Ascot_AL3QuoteDetailTable_V2.Terrorism,
								Ascot_AL3QuoteDetailTable_V2.CompanyLocationCode,
								Ascot_AL3QuoteDetailTable_V2.LineCode,
								Ascot_AL3QuoteDetailTable_V2.StateID
						FROM	Ascot_AL3QuoteDetailTable_V2
						WHERE	Ascot_AL3QuoteDetailTable_V2.DnlTrId = @DnlTrID
					) AS NewPremiumTable
		OUTER APPLY (
						SELECT TOP 1 SubPC.ChargeCode,
									SubPC.ChargeID
						FROM tblFin_PolicyCharges SubPC
						WHERE SubPC.ChargeID = OptionPremiumTable.ChargeID
						AND SubPC.StateID = NewPremiumTable.StateID
					) AS ChargeCodeTable
		OUTER APPLY (
						SELECT ASCOT_AL3PolicyMasterTable_V2.CompanyCode AS CompanyLocationCode,
								ASCOT_AL3PolicyMasterTable_V2.LineCode,
								ASCOT_AL3PolicyMasterTable_V2.PremiumState
						FROM ASCOT_AL3PolicyMasterTable_V2
						WHERE ASCOT_AL3PolicyMasterTable_V2.DnlTrId = @DnlTrId
					) AS PolicyLevelImportTable
		WHERE	tblQuotes.QuoteGuid = @QuoteGuid
		AND		CASE WHEN NewPremiumTable.LineCode IS NULL
					THEN CASE WHEN lstLines.LineID = PolicyLevelImportTable.LineCode THEN 1 ELSE 0 END
					ELSE CASE WHEN lstLines.LineID = NewPremiumTable.LineCode THEN 1 ELSE 0 END
				END = 1
		AND		CASE WHEN NewPremiumTable.CompanyLocationCode IS NULL
					THEN CASE WHEN tblQuoteOptions.CompanyLocationID = PolicyLevelImportTable.CompanyLocationCode THEN 1 ELSE 0 END
					ELSE CASE WHEN tblQuoteOptions.CompanyLocationID = NewPremiumTable.CompanyLocationCode THEN 1 ELSE 0 END
				END = 1
		AND		CASE WHEN NewPremiumTable.StateID IS NULL
					THEN CASE WHEN OptionPremiumTable.StateID = PolicyLevelImportTable.PremiumState THEN 1 ELSE 0 END
					ELSE CASE WHEN OptionPremiumTable.StateID = NewPremiumTable.StateID THEN 1 ELSE 0 END
				END = 1
		AND		NewQuoteOptionsQuote.ControlNo = tblQuotes.ControlNo -- TFS 89958  Added additional check to make sure quoteoptions are comming from the right control number.  We were getting
		-- duplicate quoteoptions prem error on some polciies prior to thsi additional check in BOLT policies.

	/*
		SELECT	NewQuoteOptions.QuoteOptionGuid,
				ISNULL(ChargeCodeTable.ChargeCode, tblFin_PolicyCharges.ChargeCode) AS ChargeCode,
				tblQuoteOptionPremiums.OfficeId,
				CASE WHEN NewPremiumTable.CompanyLocationCode IS NULL
					THEN CASE WHEN tblFin_PolicyCharges.ChargeID = 'TERR' THEN @TerrorismPremium ELSE @NewPremium END
					ELSE CASE WHEN ChargeCodeTable.ChargeID = 'TERR' THEN NewPremiumTable.Terrorism ELSE NewPremiumTable.Premium END
				END,
				tblQuoteOptionPremiums.Commissionable,
				GETDATE()
		FROM	tblQuoteOptions 
		INNER JOIN tblQuoteOptions NewQuoteOptions ON NewQuoteOptions.OriginalQuoteOptionGuid = tblQuoteOptions.QuoteOptionGuid
		INNER JOIN tblQuoteOptionPremiums ON tblQuoteOptions.QuoteOptionGuid = tblQuoteOptionPremiums.QuoteOptionGuid
		INNER JOIN tblFin_PolicyCharges ON tblQuoteOptionPremiums.ChargeCode = tblFin_PolicyCharges.ChargeCode
		INNER JOIN lstLines ON tblQuoteOptions.LineGuid = lstLines.LineGuid
		OUTER APPLY (
						SELECT	ISNULL(Ascot_AL3QuoteDetailTable_v2.Premium, 0) AS Premium,
								ISNULL(Ascot_AL3QuoteDetailTable_v2.Terrorism, 0) AS Terrorism,
								Ascot_AL3QuoteDetailTable_v2.CompanyLocationCode,
								Ascot_AL3QuoteDetailTable_v2.LineCode,
								Ascot_AL3QuoteDetailTable_v2.StateID
						FROM	Ascot_AL3QuoteDetailTable_v2
						WHERE	Ascot_AL3QuoteDetailTable_v2.DnlTrId = @DnlTrID
					) AS NewPremiumTable
		OUTER APPLY (
						SELECT TOP 1 SubPC.ChargeCode,
									SubPC.ChargeID
						FROM tblFin_PolicyCharges SubPC
						WHERE SubPC.ChargeID = tblFin_PolicyCharges.ChargeID
						AND SubPC.StateID = NewPremiumTable.StateID
					) AS ChargeCodeTable
		OUTER APPLY (
						SELECT Ascot_AL3PolicyMasterTable_v2.CompanyCode AS CompanyLocationCode,
								Ascot_AL3PolicyMasterTable_v2.LineCode
						FROM Ascot_AL3PolicyMasterTable_v2
						WHERE Ascot_AL3PolicyMasterTable_v2.DnlTrId = @DnlTrId
					) AS PolicyLevelImportTable
		WHERE	tblQuoteOptions.QuoteGuid = @QuoteGuid
		AND		CASE WHEN NewPremiumTable.LineCode IS NULL
					THEN CASE WHEN lstLines.LineID = PolicyLevelImportTable.LineCode THEN 1 ELSE 0 END
					ELSE CASE WHEN lstLines.LineID = NewPremiumTable.LineCode THEN 1 ELSE 0 END
				END = 1
		AND		CASE WHEN NewPremiumTable.CompanyLocationCode IS NULL
					THEN CASE WHEN tblQuoteOptions.CompanyLocationID = PolicyLevelImportTable.CompanyLocationCode THEN 1 ELSE 0 END
					ELSE CASE WHEN tblQuoteOptions.CompanyLocationID = NewPremiumTable.CompanyLocationCode THEN 1 ELSE 0 END
				END = 1
	*/
	
	

	OPEN EndorsePremiumCursor
	FETCH EndorsePremiumCursor INTO @PremiumCursorQuoteOptionGuid, @PremiumCursorChargeCode, @PremiumCursorOfficeID, @PremiumCursorPremium, @PremiumCursorCommissionable, @PremiumCursorAddedDate

	WHILE @@Fetch_status=0
	BEGIN

		INSERT INTO tblQuoteOptionPremiums
		(
			QuoteOptionGuid,
			ChargeCode,
			OfficeID,
			Premium,
			AnnualPremium,
			Commissionable,
			Added
		)
		VALUES
		(
			@PremiumCursorQuoteOptionGuid,
			@PremiumCursorChargeCode,
			@PremiumCursorOfficeID,
			@PremiumCursorPremium,
			@PremiumCursorPremium,
			@PremiumCursorCommissionable,
			@PremiumCursorAddedDate
		)

		FETCH EndorsePremiumCursor INTO @PremiumCursorQuoteOptionGuid, @PremiumCursorChargeCode, @PremiumCursorOfficeID, @PremiumCursorPremium, @PremiumCursorCommissionable, @PremiumCursorAddedDate
	END--WHILE @@Fetch_status=0

	CLOSE EndorsePremiumCursor 
	DEALLOCATE EndorsePremiumCursor
		
	--for imports wherre fee amounts are given by the import source
	IF EXISTS(SELECT * FROM Ascot_AL3FeesTable WHERE Ascot_AL3FeesTable.DnlTrId = @DnlTrId)
	BEGIN

		INSERT INTO tblQuoteOptionCharges(QuoteOptionGuid, CompanyFeeID, ChargeCode, OfficeID, CompanyLineGuid, FeeTypeID, Payable, FlatRate, Splittable, AutoApplied)
		SELECT	qo.QuoteOptionGUID,
				CompanyLineFeeSetupIDTable.CompanyFeeID,
				Ascot_AL3FeesTable.ChargeCode,
				@OfficeID,
				tblCompanyLines.CompanyLineGUID,
				3,
				--(4/2/24) updated to dynamically set payable bit
				CompanyLineFeeSetupIDTable.Payable,	--payable
				Ascot_AL3FeesTable.FeeAmount, 
				0,
				0
		FROM		Ascot_AL3FeesTable
		INNER JOIN	lstLines FeeLine ON Ascot_AL3FeesTable.LineID = FeeLine.LineID
		INNER JOIN	tblCompanyLocations FeeCompanyLocation ON FeeCompanyLocation.CompanyLocationCode = Ascot_AL3FeesTable.CompanyLocationCode
		INNER JOIN	tblQuotes q ON q.QuoteGUID = @EndorsementQuoteGuid
		INNER JOIN	tblQuoteOptions qo ON q.QuoteGUID = qo.QuoteGUID
			AND		qo.LineGUID = FeeLine.LineGUID
			AND		qo.CompanyLocationID = Ascot_AL3FeesTable.CompanyLocationCode
		INNER JOIN	tblCompanyLines ON tblCompanyLines.LineGUID = FeeLine.LineGUID
			AND		tblCompanyLines.CompanyLocationGUID = FeeCompanyLocation.CompanyLocationGUID
			AND		tblCompanyLines.StateID = Ascot_AL3FeesTable.StateID
			AND		CASE WHEN FeeLine.LineGUID <> q.LineGUID
						THEN CASE WHEN tblCompanyLines.ParentCompanyLineGUID IS NOT NULL THEN 1 ELSE 0 END
						ELSE CASE WHEN tblCompanyLines.ParentCompanyLineGUID IS NULL THEN 1 ELSE 0 END
					END = 1
		CROSS APPLY (
						SELECT TOP 1 tblCompanyPolicyCharges.CompanyFeeID,
										tblCompanyPolicyCharges.Payable
						FROM tblCompanyPolicyCharges
						WHERE tblCompanyPolicyCharges.ChargeCode = Ascot_AL3FeesTable.ChargeCode
						AND ISNULL(tblCompanyPolicyCharges.CompanyLocationGuid, FeeCompanyLocation.CompanyLocationGUID) = FeeCompanyLocation.CompanyLocationGUID
						AND ISNULL(tblCompanyPolicyCharges.LineGuid, FeeLine.LineGUID) = FeeLine.LineGUID
						AND ISNULL(tblCompanyPolicyCharges.StateID, Ascot_AL3FeesTable.StateID) = Ascot_AL3FeesTable.StateID
						AND DATEDIFF(d, tblCompanyPolicyCharges.Effective, q.EffectiveDate) >= 0
						ORDER BY tblCompanyPolicyCharges.Effective DESC,
									(CASE WHEN tblCompanyPolicyCharges.CompanyLocationGuid IS NOT NULL THEN 1 ELSE 0 END +
									CASE WHEN tblCompanyPolicyCharges.LineGuid IS NOT NULL THEN 1 ELSE 0 END +
									CASE WHEN tblCompanyPolicyCharges.StateID IS NOT NULL THEN 1 ELSE 0 END) DESC
					) AS CompanyLineFeeSetupIDTable
		WHERE Ascot_AL3FeesTable.DnlTrId = @DnlTrId

	END

	--TFS 89800  SQL Ascot added spautoapplyfees
	--it can be controlled via @SkipTaxesAndFees 
	IF @AutoApplyFees=1
	BEGIN
		
		DECLARE @FeeCursorQuoteOptionGuid uniqueidentifier

		DECLARE EndorseFeeCursor Cursor FAST_FORWARD FORWARD_ONLY
		FOR SELECT	tblQuoteOptions.QuoteOptionGuid
			FROM	tblQuotes
			INNER JOIN tblQuoteOptions ON tblQuotes.QuoteGUID = tblQuoteOptions.QuoteGUID
			WHERE	tblQuotes.QuoteGuid = @EndorsementQuoteGuid

		OPEN EndorseFeeCursor
		FETCH EndorseFeeCursor INTO @FeeCursorQuoteOptionGuid

		WHILE @@Fetch_status=0
		BEGIN

			exec spAutoApplyFees @PremiumCursorQuoteOptionGuid

			FETCH EndorseFeeCursor INTO @FeeCursorQuoteOptionGuid
		END--WHILE @@Fetch_status=0

		CLOSE EndorseFeeCursor 
		DEALLOCATE EndorseFeeCursor
		
	END
	
	IF @BrokerCommissionFeeChargeCode IS NOT NULL
	BEGIN

		DECLARE @BrokerCommissionPercent decimal(9, 8)
		DECLARE @BrokerFeeAppliesToLineGuid uniqueidentifier
		DECLARE @BrokerFeeAppliesToCompanyLineGuid uniqueidentifier

		SELECT	@BrokerCommissionPercent = Ascot_AL3PolicyMasterTable_v2.BrokerCommissionPercent,
				@BrokerFeeAppliesToLineGuid = lstLines.LineGUID,
				@BrokerFeeAppliesToCompanyLineGuid = CL.CompanyLineGuid
		FROM Ascot_AL3PolicyMasterTable_v2
		INNER JOIN lstLines ON Ascot_AL3PolicyMasterTable_v2.LineCode = lstLines.LineID
		Inner Join  tblCompanyLocations on tblCompanyLocations.CompanyLocationCode = Ascot_AL3PolicyMasterTable_v2.CompanyCode
		Inner Join  tblCompanyLines CL on CL.LineGUID = lstLines.LineGUID and CL.CompanyLocationGUID = tblCompanyLocations.CompanyLocationGUID and Ascot_AL3PolicyMasterTable_v2.StateOfIssuance = CL.StateID
		WHERE	DnlTrId = @DnlTrId

		DECLARE @BrokerCommissionCompanyFeeID int
		SELECT @BrokerCommissionCompanyFeeID = CompanyFeeID
		FROM tblCompanyPolicyCharges
		WHERE tblCompanyPolicyCharges.ChargeCode = @BrokerCommissionFeeChargeCode
		AND tblCompanyPolicyCharges.LineGuid = @BrokerFeeAppliesToLineGuid

		IF @BrokerCommissionCompanyFeeID IS NULL
		BEGIN

			raiserror('No CompanyFeeID setup found for ChargeCode and Line', 15, 1) with nowait;

		END

		INSERT INTO tblQuoteOptionCharges(QuoteOptionGuid, CompanyFeeID, ChargeCode, OfficeID, CompanyLineGuid, FeeTypeID, Payable, PercentageRate, Splittable, AutoApplied)
		SELECT	tblQuoteOptions.QuoteOptionGuid,
				@BrokerCommissionCompanyFeeID,
				@BrokerCommissionFeeChargeCode,
				@OfficeID,
				@BrokerFeeAppliesToCompanyLineGuid,
				3,
				0,
				@BrokerCommissionPercent, 
				0,
				0
		FROM	tblQuoteOptions
		WHERE	tblQuoteOptions.QuoteGuid = @EndorsementQuoteGuid

	END

	--Update Quote Option Data
	UPDATE tblQuoteOptions SET Bound = 1 WHERE QuoteGuid = @EndorsementQuoteGuid

	--If we have premium in tblQuoteOptionsPremiums or fees in tblQuoteOptionCharges that add up to something other than 0 then continue with the invoice generation and transfer to accounting
	DECLARE @QuoteOptionPremium money = 0
	SELECT @QuoteOptionPremium = SUM(tblQuoteOptionPremiums.Premium)
	FROM tblQuotes
	INNER JOIN tblQuoteOptions ON tblQuotes.QuoteGUID = tblQuoteOptions.QuoteGUID
	INNER JOIN tblQuoteOptionPremiums ON tblQuoteOptions.QuoteOptionGUID = tblQuoteOptionPremiums.QuoteOptionGuid
	WHERE tblQuotes.QuoteGuid = @EndorsementQuoteGuid

	DECLARE @QuoteOptionCharges money = 0
	SELECT @QuoteOptionCharges = SUM(tblQuoteOptionCharges.amount)
	FROM tblQuotes
	INNER JOIN tblQuoteOptions ON tblQuotes.QuoteGUID = tblQuoteOptions.QuoteGUID
	INNER JOIN tblQuoteOptionCharges ON tblQuoteOptions.QuoteOptionGUID = tblQuoteOptionCharges.QuoteOptionGuid
	WHERE tblQuotes.QuoteGuid = @EndorsementQuoteGuid

	IF @QuoteOptionPremium <> 0 OR @QuoteOptionCharges <> 0
	BEGIN

		--Send invoices to accounting (AccountingTransfer.vb)
		DECLARE @InvoiceNum INT


		DECLARE @NumInstallments int
		DECLARE @ExpirationDate datetime
		DECLARE @IMSInstallmentPlanID int = NULL

		SELECT @NumInstallments = ISNULL(P.NumInstallments, 1),
				@ExpirationDate = P.PolicyExpirationDate
		FROM Ascot_AL3PolicyMasterTable_v2 P
		WHERE P.DnlTrId = @DnlTrId

		DECLARE @InstallmentPlanMappingTable TABLE
		(
			OptionName varchar(200),
			SafeHarborNumInstallments int
		)

		INSERT INTO @InstallmentPlanMappingTable VALUES('Quarterly', 4)
		INSERT INTO @InstallmentPlanMappingTable VALUES('Semi-Annual', 2)

		SELECT TOP 1 @IMSInstallmentPlanID = tblCompanyLineInstallments.ID
		FROM tblCompanyLineInstallments
		INNER JOIN tblCompanyLines ON tblCompanyLineInstallments.CompanyLineID = tblCompanyLines.CompanyLineID
		INNER JOIN @InstallmentPlanMappingTable T ON tblCompanyLineInstallments.OptionName = T.OptionName
		WHERE tblCompanyLines.CompanyLineGUID = @CompanyLineGuid
		AND T.SafeHarborNumInstallments = @NumInstallments
		

		DECLARE @FirstInvoicePercentage decimal(20, 19)
		DECLARE @FirstInvoiceTerm int
		DECLARE @FirstInvoiceBillingCode varchar(100)
		DECLARE @FirstInvoiceFromEffectiveDate bit
		DECLARE @FirstInvoiceFromBillingDate bit
		DECLARE @InstallmentPercentage decimal(20, 19)
		DECLARE @InstallmentTerms int--how many days/months between installments
		DECLARE @InstallmentFromEffectiveDate datetime
		DECLARE @InstallmentFromBillingDate datetime
		DECLARE @UseMonth bit--defines if months are used for @InstallmentTerms instead of days

		IF @IMSInstallmentPlanID IS NOT NULL
		BEGIN

			SELECT	@FirstInvoicePercentage = tblCompanyLineInstallments.DownpaymentPercentage,
					@FirstInvoiceTerm = tblCompanyLineInstallments.DownpaymentTerm,
					@FirstInvoiceBillingCode = lstBillingTypes.BillingCode,
					@FirstInvoiceFromEffectiveDate = tblCompanyLineInstallments.DownpaymentFromEffectiveDate,
					@FirstInvoiceFromBillingDate = tblCompanyLineInstallments.DownpaymentFromDateBilled,
									
					@InstallmentPercentage = ((1.0000 - tblCompanyLineInstallments.DownpaymentPercentage) / tblCompanyLineInstallments.NumPayments),
					@InstallmentTerms = tblCompanyLineInstallments.InstallmentTerms,
					@InstallmentFromEffectiveDate = tblCompanyLineInstallments.InstallmentFromEffectiveDate,
					@InstallmentFromBillingDate = tblCompanyLineInstallments.InstallmentFromDateBilled,
					@UseMonth = tblCompanyLineInstallments.UseMonth

			FROM	tblCompanyLineInstallments
			LEFT JOIN lstBillingTypes ON tblCompanyLineInstallments.DownpaymentBillingTypeID = lstBillingTypes.BillingTypeID
			WHERE	ID = @IMSInstallmentPlanID

		END
		ELSE
		BEGIN

			DECLARE @ProducerPaymentMeasuredFrom_Endorsement varchar(10)
			DECLARE @ProducerPaymentTermDays int = 0
			SELECT @ProducerPaymentMeasuredFrom_Endorsement = tblCompanyLineTermsOfPayment.ProducerPaymentMeasuredFrom_Endorsement,
					@ProducerPaymentTermDays = tblCompanyLineTermsOfPayment.DefaultProducerTermsOfPayment_Endorsement
			FROM tblCompanyLines
			INNER JOIN tblCompanyLineTermsOfPayment ON tblCompanyLines.CompanyLineID = tblCompanyLineTermsOfPayment.CompanyLineID
			WHERE tblCompanyLines.CompanyLineGUID = @CompanyLineGuid
			AND DATEDIFF(d, tblCompanyLineTermsOfPayment.Effective, @PolicyEffectiveDate) >= 0
			ORDER BY Effective DESC
			--E=Effective
			--G=GAAP
			--M=End of Month (billed?)
			--B=Billed

			DECLARE @TransactionMonths int = DATEDIFF(m, @TransEffDate, @ExpirationDate)

			SET @FirstInvoicePercentage = 1.0000 / @NumInstallments
			SET @FirstInvoiceTerm = @ProducerPaymentTermDays
			SET @FirstInvoiceBillingCode = @BillingCode
			SET @FirstInvoiceFromEffectiveDate = 1
			SET @FirstInvoiceFromBillingDate = 0

			SET @InstallmentPercentage = @FirstInvoicePercentage
			SET @InstallmentTerms = @TransactionMonths / @NumInstallments
			SET @InstallmentFromEffectiveDate = 1
			SET @InstallmentFromBillingDate = 0
			SET @UseMonth = 1

			IF @ProducerPaymentMeasuredFrom_Endorsement = 'E'
			BEGIN

				SET @FirstInvoiceFromEffectiveDate = 1
				SET @FirstInvoiceFromBillingDate = 0

				SET @InstallmentFromEffectiveDate = 1
				SET @InstallmentFromBillingDate = 0

			END
						
			IF @ProducerPaymentMeasuredFrom_Endorsement = 'B'
			BEGIN

				SET @FirstInvoiceFromEffectiveDate = 0
				SET @FirstInvoiceFromBillingDate = 1

				SET @InstallmentFromEffectiveDate = 0
				SET @InstallmentFromBillingDate = 1

			END

			IF @InstallmentTerms < 1
			BEGIN

				DECLARE @TransactionDays int = DATEDIFF(d, @TransEffDate, @ExpirationDate)
				SET @InstallmentTerms = @TransactionDays / @NumInstallments
				SET @UseMonth = 0

			END

		END

		IF EXISTS(SELECT * FROM #InvoiceInstallmentsTable)
		BEGIN

			DELETE FROM #InvoiceInstallmentsTable

		END

		WHILE (SELECT COUNT(*) FROM #InvoiceInstallmentsTable) < @NumInstallments
		BEGIN

			IF (SELECT COUNT(*) FROM #InvoiceInstallmentsTable) = 0
			BEGIN

				DECLARE @CalculatedDueDate datetime

				IF @FirstInvoiceFromEffectiveDate = 1
				BEGIN

					SET @CalculatedDueDate = DATEADD(d, @FirstInvoiceTerm, @TransEffDate)

				END
				ELSE IF @FirstInvoiceFromBillingDate = 1
				BEGIN

					SET @CalculatedDueDate = DATEADD(d, @FirstInvoiceTerm, @DateBound)

				END

				--downpayment info or single invoice, use first invoice vars
				INSERT INTO #InvoiceInstallmentsTable VALUES
				(
					@EndorsementQuoteID, 
					@TransEffDate, 
					@ExpirationDate, 
					@NumInstallments, 
					(SELECT COUNT(*) FROM #InvoiceInstallmentsTable) + 1, 
					@CalculatedDueDate,
					@FirstInvoiceBillingCode,
					@FirstInvoicePercentage
				)

			END
			ELSE
			BEGIN

				DECLARE @CurrentInstallmentNumber int = (SELECT COUNT(*) FROM #InvoiceInstallmentsTable) + 1

				IF @InstallmentFromEffectiveDate = 1
				BEGIN

					IF @UseMonth = 1
					BEGIN
									
						SET @CalculatedDueDate = DATEADD(m, @InstallmentTerms * (@CurrentInstallmentNumber - 1), @TransEffDate)

					END
					ELSE
					BEGIN
									
						SET @CalculatedDueDate = DATEADD(d, @InstallmentTerms * (@CurrentInstallmentNumber - 1), @TransEffDate)

					END

				END
				ELSE IF @InstallmentFromBillingDate = 1
				BEGIN

					IF @UseMonth = 1
					BEGIN
									
						SET @CalculatedDueDate = DATEADD(m, @InstallmentTerms * (@CurrentInstallmentNumber - 1), @DateBound)

					END
					ELSE
					BEGIN
									
						SET @CalculatedDueDate = DATEADD(d, @InstallmentTerms * (@CurrentInstallmentNumber - 1), @DateBound)

					END

				END

				INSERT INTO #InvoiceInstallmentsTable VALUES
				(
					@EndorsementQuoteID, 
					@TransEffDate, 
					@ExpirationDate, 
					@NumInstallments, 
					@CurrentInstallmentNumber, 
					@CalculatedDueDate,
					@BillingCode,
					@InstallmentPercentage
				)

			END

		END
		
		DECLARE @ProcessedInvoiceCount int = 0
		WHILE @ProcessedInvoiceCount < @NumInstallments
		BEGIN

			DECLARE @InvoiceProcessInstallmentMod decimal(20, 19) = 1.0
			DECLARE @InvoiceProcessInstallmentDueDate datetime = NULL
			DECLARE @InvoiceProcessInstallmentBillingCode varchar(100) = NULL

			SELECT @InvoiceProcessInstallmentMod = I.InstallmentMod,
					@InvoiceProcessInstallmentDueDate = I.InstallmentDueDate,
					@InvoiceProcessInstallmentBillingCode = I.BillingCode

			FROM #InvoiceInstallmentsTable I
			WHERE (I.Installment - 1) = @ProcessedInvoiceCount
			  

			EXECUTE spAccountingTransfer
			0, --@Debug
			@EndorsementQuoteGuid, --@QuoteGuid
			@UserGuid, --@UserGuid
			@OfficeID, --@OfficeID
			1, --@IsEndorsement
			@InvoiceProcessInstallmentMod, --@InstallmentBillingPremiumModFactor
			@InvoiceProcessInstallmentDueDate, --@DueDate
			@DateBound, --@DateBilled
			NULL, --@Amount
			@InvoiceProcessInstallmentBillingCode, --@BillingCode
			'', --@InvoiceComments
			NULL, --@ModifiesInvoiceNum
			NULL, --@BillToAdditionalInterestID
			--NULL, --@AccountCurrent
			@InvoiceNum OUTPUT

	
			--Loop through all the fees on the policy
			DECLARE @QuoteOptionChargeAmount MONEY
			DECLARE @QuoteOptionFeeID INT

			DECLARE db_cursor CURSOR FOR  
				SELECT DISTINCT tblQuoteOptionCharges.Amount, tblQuoteOptionCharges.OptionFeeID
				FROM tblQuotes
				INNER JOIN tblQuoteOptions ON tblQuotes.QuoteGUID = tblQuoteOptions.QuoteGUID
				INNER JOIN tblQuoteOptionCharges ON tblQuoteOptions.QuoteOptionGUID = tblQuoteOptionCharges.QuoteOptionGuid
				INNER JOIN tblQuoteDetails ON tblQuotes.QuoteGUID = tblQuoteDetails.QuoteGUID
				INNER JOIN tblCompanyLines ON tblQuoteDetails.CompanyLineGUID = tblCompanyLines.CompanyLineGUID AND tblQuoteOptions.LineGUID = tblCompanyLines.LineGUID
				WHERE (tblQuotes.QuoteGUID = @EndorsementQuoteGuid)
				AND (tblQuoteOptions.Bound = 1)
				AND (tblQuoteOptionCharges.WaivedByUserGuid IS NULL)

			OPEN db_cursor   
			FETCH NEXT FROM db_cursor INTO @QuoteOptionChargeAmount, @QuoteOptionFeeID

			WHILE @@FETCH_STATUS = 0   
			BEGIN   

					EXEC spAccountingTransfer_Fees
					0, --@Debug
					@QuoteOptionFeeID, --@OptionFeeID
					@InvoiceNum, --@InvoiceNum
					@QuoteOptionChargeAmount, --@Amount
					@InvoiceProcessInstallmentBillingCode --@BillingCode

			FETCH NEXT FROM db_cursor INTO @QuoteOptionChargeAmount, @QuoteOptionFeeID
			END   

			CLOSE db_cursor   
			DEALLOCATE db_cursor


			--Post to Journal
			EXEC spFin_PostInvoice @InvoiceNum
	  
			exec GreyHawk_AfterPostInvoice @invoicenum--Posts reinsurance data

			SET @ProcessedInvoiceCount = @ProcessedInvoiceCount + 1

		END--WHILE @ProcessedInvoiceCount < @NumInstallments

	--Verify Premiums
		EXEC spAccountingTransfer_VerifyPremiumsTransferred
				@EndorsementQuoteGuid, --@quoteGuid
				0, --@debug
				0 --@reVerify

		--Verify Fees
		EXEC spAccountingTransfer_VerifyFeesTransferred	@EndorsementQuoteGuid --@quoteGuid

	--Verify Invoices were created
	  DECLARE @InvoiceCount INT
	  SELECT @InvoiceCount = COUNT(*) FROM tblFin_Invoices WHERE QuoteID = (SELECT QuoteID FROM tblQuotes WHERE QuoteGuid = @EndorsementQuoteGuid) AND Failed = 0

	  IF (@InvoiceCount <> @NumInstallments)
	  BEGIN
		ROLLBACK TRANSACTION
		RAISERROR('Invoice Count Incorrect.',15,1)
		RETURN
	  END

	END--IF @QuoteOptionPremium <> 0 OR @QuoteOptionCharges <> 0

		DECLARE @OptionPremiumCheck money
		DECLARE @BilledPremiumCheck money

		SELECT @OptionPremiumCheck = SUM(tblQuoteOptionPremiums.Premium)
		FROM tblQuotes
		INNER JOIN tblQuoteOptions ON tblQuotes.QuoteGuid = tblQuoteOptions.QuoteGuid
		INNER JOIN tblQuoteOptionPremiums ON tblQuoteOptions.QuoteOptionGUID = tblQuoteOptionPremiums.QuoteOptionGuid
		WHERE tblQuotes.QuoteID = @EndorsementQuoteID

		SELECT @BilledPremiumCheck = SUM(tblFIn_InvoiceDetails.AmtBilled)
		FROM tblFin_Invoices
		INNER JOIN tblFin_InvoiceDetails ON tblFin_Invoices.InvoiceNum = tblFin_InvoiceDetails.InvoiceNum
		WHERE tblFin_Invoices.Failed = 0
		AND tblFin_InvoiceDetails.ChargeType = 'P'
		AND tblFin_Invoices.QuoteID = @EndorsementQuoteID

		DECLARE @BadPremiumErrorMessage varchar(200)
		SET @BadPremiumErrorMessage = 'Invoice premium is too different from option premium.' +
										' InvoicePremium: ' + dbo.FormatNumber(@BilledPremiumCheck, 2) + 
										'; OptionPremium ' + dbo.FormatNumber(@OptionPremiumCheck, 2) +
										'; InstallmentMod: ' + dbo.FormatNumber(@InvoiceProcessInstallmentMod, 10)

		IF ABS(@OptionPremiumCheck - @BilledPremiumCheck) > 3
		BEGIN

			RAISERROR(@BadPremiumErrorMessage,15,1)

		END

	  --Update Quote Data
	  UPDATE
			tblQuotes
	  SET
			DateIssued = GETDATE(),
			IssuedByUserID = (SELECT TOP 1 UserId FROM tblUsers WHERE UserGuid = @UserGuid),
			DateBound = GETDATE(),
			BoundByUserId = (SELECT TOP 1 UserId FROM tblUsers WHERE UserGuid = @UserGuid),
			QuoteStatusId = 12
	  WHERE
			QuoteGuid = @EndorsementQuoteGuid
			AND DateIssued IS NULL
		
	  UPDATE Ascot_AL3PolicyMasterTable_v2 SET CreatedQuoteID = @EndorsementQuoteID
	  FROM Ascot_AL3PolicyMasterTable_v2
	  WHERE DnlTrID = @DnlTrID

	  --update the expiration date
	  DECLARE @QuoteID int
	  SELECT @QuoteID=QuoteID FROM tblQuotes WHERE QuoteGuid=@EndorsementQuoteGuid
	  UPDATE tblQuotes2 SET OriginalExpirationDate=(SELECT ExpirationDate FROM tblQuotes WHERE QuoteID=@QuoteID) WHERE QuoteID=@QuoteID 
	  UPDATE tblQuotes SET ExpirationDate=@TransEffDate WHERE QuoteID=@QuoteID

	  DROP TABLE #InvoiceInstallmentsTable

      COMMIT TRANSACTION

END



