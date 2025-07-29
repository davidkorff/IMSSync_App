-- =============================================
-- Stored Procedure: spGetQuoteByExpiringPolicyNumber_WS
-- Description: Find quote information by expiring policy number for renewals
-- Purpose: Used to link renewal quotes to their expiring policies
-- =============================================

IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[spGetQuoteByExpiringPolicyNumber_WS]') AND type in (N'P', N'PC'))
    DROP PROCEDURE [dbo].[spGetQuoteByExpiringPolicyNumber_WS]
GO

CREATE PROCEDURE [dbo].[spGetQuoteByExpiringPolicyNumber_WS]
    @ExpiringPolicyNumber NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Find the most recent quote with this policy number
    -- This will be used as the RenewalOfQuoteGuid for the new renewal quote
    SELECT TOP 1
        tqd.QuoteGuid,
        tqd.QuoteOptionGuid,
        tqd.policy_number,
        tqd.insured_name,
        tqd.opportunity_id,
        tqd.effective_date,
        tqd.expiration_date,
        tqd.created_date,
        q.QuoteStatusID,
        q.DateBound,
        q.DateIssued
    FROM tblTritonQuoteData tqd
    INNER JOIN tblQuotes q ON tqd.QuoteGuid = q.QuoteGuid
    WHERE tqd.policy_number = @ExpiringPolicyNumber
    ORDER BY tqd.created_date DESC;  -- Get the most recent
END
GO

-- Grant execute permission to IMS user
GRANT EXECUTE ON [dbo].[spGetQuoteByExpiringPolicyNumber_WS] TO [IMS_User]
GO

PRINT 'Stored procedure spGetQuoteByExpiringPolicyNumber_WS created successfully';