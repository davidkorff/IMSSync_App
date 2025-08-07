# TODO

## Critical Fixes

### Cancellation Issues
- [ ] Fix cancellation stuck in "Pending Cancellation" status
- [ ] Fix premium not calculating for cancellations
- [ ] Get refund amount working

### Transaction Storage
- [ ] Make sure all transaction types are being saved to tblTritonTransactionData

## Endorsement Improvements (from before)
- [ ] Add endorsement_premium and endorsement_effective_date fields to payload/database
- [ ] Use dedicated fields instead of overloading gross_premium and transaction_date