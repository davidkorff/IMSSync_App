# TODO: Midterm Endorsement Improvements

## Database Schema Updates
- [ ] Add `endorsement_premium` column to `tblTritonQuoteData` table
- [ ] Add `endorsement_effective_date` column to `tblTritonQuoteData` table

## JSON Payload Format Updates
- [ ] Add `endorsement_premium` field to JSON payload format (instead of using `gross_premium`)
- [ ] Add `endorsement_effective_date` field to JSON payload format (instead of using `transaction_date`)

## Code Updates

### transaction_handler.py
- [ ] Update to read `endorsement_premium` from payload for midterm_endorsement transactions
- [ ] Update to read `endorsement_effective_date` from payload for midterm_endorsement transactions
- [ ] Fall back to current fields if new fields not present (backward compatibility)

### Triton_EndorsePolicy_WS stored procedure
- [ ] Update to insert `endorsement_premium` into `tblTritonQuoteData`
- [ ] Update to insert `endorsement_effective_date` into `tblTritonQuoteData`
- [ ] Use these dedicated fields when available

## Testing
- [ ] Create test JSON with new `endorsement_premium` and `endorsement_effective_date` fields
- [ ] Test midterm endorsement with new fields
- [ ] Verify backward compatibility with old payload format
- [ ] Test edge cases (dates outside policy period, negative premiums, etc.)

## Documentation
- [ ] Update API documentation with new fields
- [ ] Document the endorsement workflow
- [ ] Add examples of endorsement payloads

## Future Enhancements
- [ ] Support for multiple endorsements on same policy
- [ ] Support for endorsement reversal/cancellation
- [ ] Support for retroactive endorsements
- [ ] Add validation for endorsement premium changes (min/max limits)
- [ ] Add support for endorsement reason codes
- [ ] Generate endorsement documents automatically