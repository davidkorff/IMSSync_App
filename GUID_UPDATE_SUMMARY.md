# GUID Configuration Update Summary

## Changes Made

### 1. IMS Workflow Service (`app/services/ims_workflow_service.py`)

Updated the `_extract_quote_data` method to use valid IMS GUIDs:
- **Line GUID**: `07564291-CBFE-4BBE-88D1-0548C88ACED4` (AHC Primary)
- **Quoting Location GUID**: `C5C006BB-6437-42F3-95D4-C090ADD3B37D`
- **Issuing Location GUID**: `C5C006BB-6437-42F3-95D4-C090ADD3B37D`
- **Company Location GUID**: `DF35D4C7-C663-4974-A886-A1E18D3C9618`

Also updated all extraction methods to use `processed_data` from transformers when available:
- `_extract_insured_data`: Now checks for transformed data structure
- `_extract_submission_data`: Uses transformed policy_data and producer_data
- `_extract_quote_data`: Uses transformed dates and state from proper sections
- `_extract_premium_data`: Uses transformed premium_data and coverages

### 2. Triton Transformer (`app/integrations/triton/transformer.py`)

Updated the default line GUID:
```python
default_guid = self.config.get("default_line_guid", "07564291-CBFE-4BBE-88D1-0548C88ACED4")  # AHC Primary LineGUID
```

### 3. Triton Flat Transformer (`app/integrations/triton/flat_transformer.py`)

Updated the default line GUID in the transform_to_ims_format method:
```python
"line_guid": self.config.get("default_line_guid", "07564291-CBFE-4BBE-88D1-0548C88ACED4"),  # AHC Primary LineGUID
```

## How the Flat Transformer Works

The flat transformer is automatically used when the Triton service detects a flat JSON structure (like TEST.json):

1. **Detection**: The `TritonTransformer._is_flat_structure()` method checks for flat field indicators
2. **Transformation**: If flat structure is detected, it delegates to `TritonFlatTransformer`
3. **Structure**: The flat transformer converts flat fields into the nested IMS structure:
   - `insured_name` → `insured_data.name`
   - `gross_premium` → `premium_data.gross_premium`
   - `producer_name` → `producer_data.name`
   - etc.

## Integration Flow

When TEST.json is sent to the API:
1. API receives the flat JSON structure
2. Transaction is created with `parsed_data` = the flat JSON
3. TritonIntegrationService processes the transaction
4. TritonTransformer detects flat structure and uses TritonFlatTransformer
5. Transformed data is stored in `transaction.processed_data`
6. IMS Workflow Service uses `processed_data` (falling back to `parsed_data` if needed)

## Remaining All-Zeros GUIDs

These are intentionally left as defaults and will be replaced during processing:
- **Producer GUID**: Looked up based on producer name via ProducerSearch
- **Underwriter GUID**: Looked up based on underwriter name via GetUserByName

## Testing

Run the verification script to confirm all GUIDs are configured:
```bash
python3 test_guid_simple.py
```

To test the flat transformer with TEST.json:
```bash
python3 test_json_simple.py
```

This will send TEST.json through the entire integration flow, using the flat transformer automatically.