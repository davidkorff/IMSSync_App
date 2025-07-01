# Triton Integration Notes

## Field Mappings

### Business Type Confusion
In TEST.json, the field `business_type` contains "Renewal" which indicates the transaction type (New Business vs Renewal), NOT the insured's entity type (LLC, Corporation, etc.).

**Current Mapping:**
- `business_type: "Renewal"` → Sets `is_renewal: true` in policy_data
- For insured entity type, we default to Corporation (ID: 13) unless specified differently

**To properly handle entity types, Triton should provide:**
- `insured_entity_type` or similar field with values like "LLC", "Corporation", "Partnership", etc.
- OR include it in the insured name parsing (e.g., "Ruby's Nursing Care LLC" → LLC)

### AdditionalInformation Field
The IMS AddQuote API accepts an AdditionalInformation parameter as an array of strings. We use this to store:

1. **TritonOpportunityId** - Links back to Triton's opportunity
2. **OriginalBoundDate** - Preserves the original bound date from Triton
3. **PriorLimits** - For comparing limit changes
4. **UMR, AgreementNumber, SectionNumber** - Additional references
5. **EndorsementId, EndorsementDesc** - For endorsements
6. **AdditionalInsureds** - JSON array of additional insureds (for future use)

Format: `Key:Value` strings in the array

### Date Handling
- All dates converted from MM/DD/YYYY to YYYY-MM-DD
- Bound date is used as-is (no backdating restrictions found)

### Business Type IDs (IMS)
```
2  - Partnership
3  - Limited Liability Partnership (LLP)
4  - Individual
5  - Other
9  - Limited Liability Corporation (LLC)
10 - Joint Venture
11 - Trust
13 - Corporation
```

### Additional Insureds
Currently stored in AdditionalInformation as JSON. Future implementation options:
1. Create separate insured records and link to policy
2. Use custom IMS fields/tables
3. Include only in policy documents

### Endorsements
For `transaction_type = "MIDTERM ENDORSEMENT"`:
- `midterm_endt_id` - Endorsement identifier
- `midterm_endt_description` - Description of changes
- `midterm_endt_effective_from` - Endorsement effective date (converted to YYYY-MM-DD)
- `midterm_endt_endorsement_number` - IMS endorsement number

## Testing

Run these tests to verify the integration:
1. `python3 test_final_integration.py` - Tests all field mappings
2. `python3 test_complete_triton_flow.py` - Tests API endpoint (requires service running)

## Deployment Notes

When deploying to an environment with IMS access:
1. Update `.env` with proper IMS credentials
2. Configure producer/underwriter mappings
3. Test with actual IMS responses
4. Monitor AdditionalInformation field storage/retrieval