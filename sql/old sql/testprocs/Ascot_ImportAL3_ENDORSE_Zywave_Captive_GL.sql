USE [Greyhawk_Test]
GO
/****** Object:  StoredProcedure [dbo].[Ascot_ImportAL3_ENDORSE_Zywave_Captive_GL]    Script Date: 7/17/2025 10:19:50 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
ALTER PROC  [dbo].[Ascot_ImportAL3_ENDORSE_Zywave_Captive_GL] 
	@ImportLogID INT
AS
BEGIN
	DECLARE @TransType VARCHAR(25)
	DECLARE @EnteredDate DATETIME 
	DECLARE @WrittenPremium MONEY
	DECLARE @PolicyNumber VARCHAR(50)
	DECLARE @PolicyTransactionID INT -- TFS 70502  USed to prevent duplicate trasnaction from being created should the feed run multiple times on same policy
	DECLARE @CompanyLocationCode INT
	DECLARE @UniqueTransactionID varchar(200) -- TFS 90577 -- Used to identify duplicate transaction uploads
	DECLARE @UniqueTransactionIDExists INT
	DECLARE @AccounNumber VARCHAR(50)

	DECLARE @ImportSource INT
	SELECT @ImportSource = ImportSource
	FROM Ascot_AL3ImportLog
	WHERE ID = @ImportLogID

	IF OBJECT_ID('tempdb..#PolsToEnd') IS NOT NULL BEGIN DROP TABLE #PolsToEnd END
	SELECT	--TOP 500
				* 
	INTO		#PolsToEnd
	FROM		[dbo].Ascot_AL3PolicyMasterTable_v2
	WHERE		ImportLogID = @ImportLogID
	AND			ISNULL(Error, 0) = 0
				AND DateProcessed IS NULL
				AND PolicyIndicator IN ('E', 'C', 'W')				
				--AND policynumber= 'HABX2010000001-01'--'HABP2010000001-01'
	ORDER BY	TransactionEffectiveDate

	DECLARE @DnlTrId UNIQUEIDENTIFIER

	IF OBJECT_ID('Cur') IS NOT NULL 
	BEGIN 
		CLOSE Cur 
		DEALLOCATE Cur
	END

	DECLARE Cur Cursor FAST_FORWARD FORWARD_ONLY
	FOR SELECT DnlTrId FROM #PolsToEnd ORDER BY AccountNumber, PolicyTransactionID

	OPEN Cur
	FETCH Cur INTO @DnlTrId

	DECLARE @preblocking int
	SET @preblocking=1

	WHILE @preblocking > 0
		BEGIN
			SELECT @preblocking=COUNT(*) 
			FROM master.sys.dm_exec_requests
			WHERE blocking_session_id <> 0
			
			IF @preblocking > 0 
			BEGIN
				raiserror('Something is pre-blocking wait 5 seconds', 0, 1) with nowait;
				WAITFOR DELAY '00:00:05' --5 SECONDS
			END
		END
		

		IF OBJECT_ID('tempdb..#ConfigurationsTable') IS NOT NULL
		BEGIN

			DROP TABLE #ConfigurationsTable

		END

		CREATE TABLE #ConfigurationsTable
		(
			ID int,
			StartingOnPoliciesEffective smalldatetime,
			QuotingLocationGuid uniqueidentifier,
			IssuingLocationGuid uniqueidentifier,
			UnderwriterGuid uniqueidentifier,
			IssuedByUserID int,
			BoundByUserID int,
			CostCenterID int,
			BrokerCommissionFeeChargeCode int,
			UnderwritingAssistantGuid uniqueidentifier,
			AutoApplyFees bit,
			CompanyLocationCode INT,
			UseUWCloseDate BIT
		)

		WHILE @@Fetch_status=0
			BEGIN
				BEGIN TRY		
					BEGIN TRAN

						SELECT	@TransType = PolicyIndicator, 
								@EnteredDate = DateIssued,
								@WrittenPremium = ISNULL(PremiumAmount, 0), 
								@PolicyNumber = Ascot_AL3PolicyMasterTable_v2.PolicyNumber,
								@PolicyTransactionID = Ascot_AL3PolicyMasterTable_v2.PolicyTransactionID,  --TFS 70502 
								@CompanyLocationCode = Ascot_AL3PolicyMasterTable_v2.CompanyCode,
								@UniqueTransactionID = Ascot_AL3PolicyMasterTable_v2.UniqueTransactionID, -- TFS 91066 added logic to use UniqueTransactionID
								@AccounNumber = Ascot_AL3PolicyMasterTable_v2.AccountNumber
						FROM Ascot_AL3PolicyMasterTable_v2 
						WHERE Ascot_AL3PolicyMasterTable_v2.DnlTrId=@DnlTrId
						
						Declare @IssuingLocationGuid UNIQUEIDENTIFIER, @QuotingLocationguid UNIQUEIDENTIFIER
						SELECT @QuotingLocationguid=OfficeGUID from tblclientoffices  where Location in(Select SUBSTRING(Company, 1, CHARINDEX('(', Company) - 2) from ASCOT_AL3ImportPolicy_Zywave where importlogid=@importlogId)
						
						Select @IssuingLocationGuid =ParentOfficeGuid from tblclientoffices  where OfficeGUID=@QuotingLocationguid

						INSERT INTO #ConfigurationsTable
						SELECT		Ascot_tblAL3ProgramConfigurations_v2.ID,
									Ascot_tblAL3ProgramConfigurations_v2.StartingOnPoliciesEffective,
									--Ascot_tblAL3ProgramConfigurations_v2.QuotingLocationguid,
									@QuotingLocationguid,
									@IssuingLocationGuid,
									--Ascot_tblAL3ProgramConfigurations_v2.IssuingLocationguid,
									Ascot_tblAL3ProgramConfigurations_v2.UnderwriterGuid,
									Ascot_tblAL3ProgramConfigurations_v2.IssuedByUserID,
									Ascot_tblAL3ProgramConfigurations_v2.BoundByUserID,
									Ascot_tblAL3ProgramConfigurations_v2.CostCenterID,
									Ascot_tblAL3ProgramConfigurations_v2.BrokerCommissionFeeChargeCode,
									Ascot_tblAL3ProgramConfigurations_v2.UnderwritingAssistantGuid,
									Ascot_tblAL3ProgramConfigurations_v2.AutoApplyFees,																		
									ASCOT_tblAL3ProgramConfigurations_V2.CompanyLocationCode,
									ASCOT_tblAL3ProgramConfigurations_V2.UseUWCloseDate

						FROM		Ascot_tblAL3ProgramConfigurations_v2
						INNER JOIN	Ascot_AL3PolicyMasterTable_v2 P ON P.ProducerCode = ISNULL(NULLIF(Ascot_tblAL3ProgramConfigurations_v2.ProducerLocationID, 0), P.ProducerCode)
							AND		P.LineCode = Ascot_tblAL3ProgramConfigurations_v2.LineID
							AND		P.CompanyCode = Ascot_tblAL3ProgramConfigurations_v2.CompanyLocationCode
							AND		DATEDIFF(d, P.PolicyEffectiveDate, Ascot_tblAL3ProgramConfigurations_v2.StartingOnPoliciesEffective) <= 0
							AND		Ascot_tblAL3ProgramConfigurations_v2.SourceID = @ImportSource
						WHERE		P.DnlTrId = @DnlTrId

						DECLARE @ConfigurationID int

						SELECT TOP 1 @ConfigurationID = C.ID
						FROM #ConfigurationsTable C
						WHERE C.CompanyLocationCode = @CompanyLocationCode						
						ORDER BY C.StartingOnPoliciesEffective DESC

						---DECLARE @QuotingLocationGuid uniqueidentifier
						--DECLARE @IssuingLocationGuid uniqueidentifier
						DECLARE @UnderwriterGuid uniqueidentifier
						DECLARE @IssuedByUserID int
						DECLARE @BoundByUserID int
						DECLARE @CostCenterID int
						DECLARE @BrokerCommissionFeeChargeCode int
						DECLARE @UnderwritingAssistantGuid uniqueidentifier
						DECLARE @AutoApplyFees bit
						DECLARE @UseUWCloseDate BIT = 0 -- TFS 92747

						SELECT	@QuotingLocationGuid = QuotingLocationGuid,
								@IssuingLocationGuid = IssuingLocationGuid,
								@UnderwriterGuid = UnderwriterGuid,
								@IssuedByUserID = IssuedByUserID,
								@BoundByUserID = BoundByUserID,
								@CostCenterID = CostCenterID,
								@BrokerCommissionFeeChargeCode = BrokerCommissionFeeChargeCode,
								@UnderwritingAssistantGuid = UnderwritingAssistantGuid,
								@AutoApplyFees = AutoApplyFees,
								@UseUWCloseDate = UseUWCloseDate
						FROM #ConfigurationsTable
						WHERE ID = @ConfigurationID

						IF @ConfigurationID IS NULL
						BEGIN
							raiserror('No configuration found for ProducerCode, LineCode, CompanyCode, StartingOnPoliciesEffective combination', 15, 1) with nowait;
						END
											   
						/*TFS 90900  
						add logic to determine if the transaction was already imported					
						*/
							SET @UniqueTransactionIDExists = 0

							SELECT @UniqueTransactionIDExists = 1 
								FROM Ascot_AL3PolicyMasterTable_v2 SubT
								join ASCOT_AL3ImportLog l on l.ID = SubT.ImportLogID
								WHERE SubT.AccountNumber = @AccounNumber
								AND SubT.UniqueTransactionID = @UniqueTransactionID -- TFS 91066  Added logic to use new column on Ascot_AL3PolicyMasterTable_v2 to identify duplicate transactions 
								AND (SubT.DateProcessed IS NOT NULL	)								
								AND SubT.DnlTrId <> @DnlTrId
								and l.ImportSource = @ImportSource
								and @UniqueTransactionID IS NOT NULL -- Use this logic only for feeds that populate the Ascot_AL3PolicyMasterTable_v2.@UniqueTransactionID, otherwise ignore thsi check.

						IF @UniqueTransactionIDExists = 1 	
						BEGIN
							raiserror('Policy Transaction previously imported', 15, 1) with nowait;
						END
						

						--TFS 87326
						DECLARE @MaxCtrlNum  int
						DECLARE @MaxCtrlNumEffective smalldatetime
						DECLARE @QuoteGuid uniqueidentifier
						DECLARE @CurrentQuoteStatusID int

						--TFS 88331  This quoting location clause is neccessary as BOLT policies (Excess Casualty) because they need to identify the  specific transaction 
						--as the source and destimation polcies are both in Ascot database but under different quoting office.
						--SELECT    top 1  @MaxCtrlNum = controlno , @MaxCtrlNumEffective = EffectiveDate, @QuoteGuid = QuoteGUID, @CurrentQuoteStatusID = QuoteStatusID from tblQuotes 
						SELECT    top 1  @MaxCtrlNum = controlno , @MaxCtrlNumEffective = EffectiveDate, @CurrentQuoteStatusID = QuoteStatusID from tblQuotes 
						where PolicyNumber = @PolicyNumber  
						and QuotingLocationGuid = @QuotingLocationGuid  																					
						order by ControlNo desc, QuoteID desc						

						--make sure no prev errors
						DECLARE @PrevErrors int
						SELECT @PrevErrors=COUNT(*) 
						FROM		Ascot_AL3PolicyMasterTable_v2 
						WHERE		Error=1 
									AND DateProcessed IS NULL 									
									AND PolicyNumber = @PolicyNumber
									AND ErrorMessage NOT IN ('Ignore 0 Premium Endorsement')
									-- TFS 70502 
									AND PolicyTransactionID < @PolicyTransactionID -- TFS 70502 Thsi will check the previous transaction id
									and Note = @MaxCtrlNum
									AND		DATEDIFF(d, PolicyEffectiveDate, @MaxCtrlNumEffective) <= 0
									
									
									-- TFS 87326  The purpose is for the  error to only check errors on the latest control number. This will occur for rewrites and in come cases renewals.
									-- 1:  Get the latest control number for the policy being processed that also has the  same policy  effective date
									-- 2:  Add the control number here in where clause to limit the prcessing to the  latest ctrl
									---3:  compare the control number from step 2 to the note of teh master table for the polciy being processed and make sure he master note is equal controlnumber


						IF @PrevErrors > 0
							BEGIN
								raiserror('Previous transactions had errors.', 15, 1) with nowait;
							END
							
						
						DECLARE @QuoteID int
						DECLARE @TransEffDate datetime
						DECLARE @EndorsementComment varchar(50)						
						DECLARE @EndorsementCalcType char(1)
						DECLARE @NewPremium money
						DECLARE @TerrorismPremium money
						DECLARE @QuoteStatusID int						
						DECLARE @DateBound datetime
						DECLARE @UserGuid uniqueidentifier
						DECLARE @BillingCode char(5)						
						DECLARE @ControlNo int
						DECLARE @ExpirationDate datetime
						DECLARE @BillingTypeID INT
						DECLARE @producerComm DECIMAL(13,10) = NULL
						DECLARE @companyComm DECIMAL(13,10) = NULL
						
						
						
						SELECT TOP 1
							  @ControlNo = q.ControlNo,	
							  @QuoteID = q.QuoteID,			
							  @QuoteGuid = q.QuoteGUID, --TFS 90900
							  @TransEffDate = t.TransactionEffectiveDate,
							  @EndorsementComment = t.EndorsementComment, 							  
							  @EndorsementCalcType = 'F',         
							  @NewPremium = ISNULL(PremiumAmount, 0),
							  @TerrorismPremium = ISNULL(TerrorismPremium, 0),
							  @QuoteStatusID = 9,             							  
							  @DateBound = GETDATE(),
							  @UserGuid = '5be2621d-4bff-44de-b7d7-17fd01c90c85',							  
							  @BillingTypeID = q.BillingTypeID, -- TFS 87790  getting this dynamically
							  @ExpirationDate = t.PolicyExpirationDate,
							  @producerComm = t.producerComm,
							  @companyComm = t.companyComm
						FROM
							  Ascot_AL3PolicyMasterTable_v2 t WITH (NOLOCK)							  
							  INNER JOIN tblQuotes q ON q.AccountNumber = t.AccountNumber--on endorsements use account number/control number as the policy number can change
							  INNER JOIN tblMaxQuoteIDs mb ON mb.MaxBoundQuoteID=q.QuoteID
							  INNER JOIN tblCompanyLocations ON q.CompanyLocationGuid = tblCompanyLocations.CompanyLocationGUID
						WHERE t.DnlTrId=@DnlTrId
						AND		tblCompanyLocations.CompanyLocationCode = @CompanyLocationCode						
						order by q.quoteid desc 

						/*
					TFS 92747-- Don't allow a policy to be inserted if the underwriting  close date is prior the policy invoice posting date
					*/

					IF @UseUWCloseDate = 1
					BEGIN
		     			 DECLARE @policyUW_Closedate DATETIME
						 DECLARE @INVOICE_GLCOMPANYID INT 
						 DECLARE @IDATE DATETIME					 
						 DECLARE @Effectivedate datetime
						 DECLARE @ErrorMessage_UWCloseDate VARCHAR(500)						 
						 DECLARE @datebilled datetime					 
						 
						 --For endts, cancels, etc, the @datebound being passed to spaccoutingtransfer is the billdate and the policy effective date is @TransEffDate which what is being pased in to spcopyquote for polciy effective date
						 SET @datebilled = @DateBound
						 SET @Effectivedate = @TransEffDate

						SELECT @policyUW_Closedate = f.UWCloseDate, @INVOICE_GLCOMPANYID = co.OfficeID , @Effectivedate = v.PolicyEffectiveDate
						FROM dbo.Ascot_AL3PolicyMasterTable v
						JOIN dbo.lstlines l ON l.LineID = v.LineCode
						JOIN dbo.Ascot_tblAL3ProgramConfigurations c ON c.LineID = v.LineCode
						JOIN dbo.tblClientOffices co ON co.OfficeGUID = c.QuotingLocationGuid
						JOIN dbo.tblfin_AccountingLocks f ON f.GlCompanyId = co.OfficeID					
						WHERE v.DnlTrId = @DnlTrId

						 --NEW CODE TO DETERMINE WHTHER OR NOT TO USE THE INVOICE DATE OR THE EFFECTIVE DATE OF COVERAGE
						 --This logic is taken from base code spFin_PostInvoice column (postdate)
						DECLARE @POSTDATECONFIG CHAR(1)
						SELECT @POSTDATECONFIG = ISNULL(SETTINGSTRINGVALUE, 'B') FROM TBLFIN_EXTENDEDSETTINGS WHERE 
						GLCOMPANYID = @INVOICE_GLCOMPANYID AND SETTING = 'PostDateConfiguration' 
						SET @IDATE = (SELECT CASE WHEN @POSTDATECONFIG = 'B' THEN @datebilled ELSE CASE WHEN @datebilled > @EFFECTIVEDATE THEN @datebilled ELSE @EFFECTIVEDATE END END)
					
						 IF @IDATE < @policyUW_Closedate 
							BEGIN
								SET @ErrorMessage_UWCloseDate = 'The policy did not import because the bill date / invoice post date is prior to the underwriting close date'
								RAISERROR(@ErrorMessage_UWCloseDate,15,1)
							END
					END

						
						select top 1 @BillingCode = BillingCode from lstBillingTypes where BillingTypeID = @BillingTypeID

						DECLARE @TotalPremium money
						DECLARE @CopyOptions bit = 0
															
						IF @TransType='E'
							BEGIN								
								exec dbo.Ascot_EndorsePolicyGL_v2 @QuoteGuid, @TransEffDate, @EndorsementComment, @EndorsementCalcType, @NewPremium, @QuoteStatusID, 20, @DateBound, @UserGuid, @BillingCode, @AutoApplyFees, @DnlTrId, @BrokerCommissionFeeChargeCode, @ExpirationDate, @TerrorismPremium, @CopyOptions								
							END
							
						DECLARE @PremiumChange money
						
						IF @TransType='C'
							BEGIN							
								
							IF @CurrentQuoteStatusID=12
								raiserror('Policy is already cancelled.', 15, 1) with nowait;						

							exec dbo.Ascot_CancelPolicyGL_v2 @QuoteGuid, @TransEffDate, @EndorsementComment, @EndorsementCalcType, @WrittenPremium, 99, @DateBound, @UserGuid, @BillingCode, @AutoApplyFees, @DnlTrId, @BrokerCommissionFeeChargeCode, @TerrorismPremium, @CopyOptions								

							END
							
						IF @TransType='W'
							BEGIN	
								IF @CurrentQuoteStatusID<>12
									raiserror('Cannot reinstate non-cancelled policy.', 15, 1) with nowait;									
									Select @TransType 'transtype_Testing'
								exec dbo.Ascot_ReinstatePolicyGL_v2 @QuoteGuid, @TransEffDate, @EndorsementComment, @EndorsementCalcType, @WrittenPremium, 100, @DateBound, @UserGuid, @BillingCode, @AutoApplyFees, @DnlTrId, @BrokerCommissionFeeChargeCode, @TerrorismPremium, @CopyOptions
								
							END
					
						--update sucess
						UPDATE      Ascot_AL3PolicyMasterTable_v2
						SET         Error=0,
									ErrorMessage=NULL,
									ErrorTime=NULL,
									DateProcessed=getdate(),
									ProcessedBy='MGA',
									Note=@ControlNo
						WHERE		DnlTrId=@DnlTrId

					-- TFS 70502 Record the committed controls in this table to be used for custom client processing

					DECLARE @tmpContext VARCHAR(200)
					SET @tmpContext = 'Ascot Policy Import V2 for importLogID:' + convert(varchar(10),@ImportLogID)

					EXEC dbo.LogAction 
					@userid = 1,
					@action = 'Policy transaction was imported into IMS via Ascot Policy Import',
					@identifierID = @ImportLogID,
					@identifierguid = @QuoteGuid,
					@context = @tmpContext
					
					COMMIT TRAN
					
					if @@trancount<>0 COMMIT TRAN
				END TRY
				BEGIN CATCH
					ROLLBACK TRAN
					if @@trancount<>0 ROLLBACK TRAN
					
					UPDATE      Ascot_AL3PolicyMasterTable_v2
					SET         Error=1,
								ErrorMessage = ERROR_MESSAGE(),
								ErrorTime=getdate()
					WHERE		DnlTrId=@DnlTrId
				END CATCH
				
				FETCH Cur INTO @DnlTrId
				
				IF @@Fetch_status=0
					BEGIN 
						raiserror('Wait 5 seconds', 0, 1) with nowait;
						WAITFOR DELAY '00:00:05' --5 seconds
						
						DECLARE @postblocking int
						SET @postblocking=1

						WHILE @postblocking > 0
							BEGIN
								SELECT @postblocking=COUNT(*) 
								FROM master.sys.dm_exec_requests
								WHERE blocking_session_id <> 0
								
								IF @postblocking > 0 
								BEGIN
									raiserror('Something is post-blocking wait 5 seconds', 0, 1) with nowait;
									WAITFOR DELAY '00:00:05' --20 SECONDS
								END
							END	
					END
			END

	CLOSE Cur 
	DEALLOCATE Cur

	DROP TABLE #ConfigurationsTable
END

