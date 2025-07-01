# IMS Services Test Suite

Comprehensive test suite for IMS (Insurance Management System) integration services.

## Overview

This test suite validates all IMS service functionality including:
- Authentication and token management
- Insured management with fuzzy matching
- Producer and underwriter lookup
- Quote/submission/policy lifecycle
- Document management
- Data access and queries
- End-to-end workflow orchestration

## Prerequisites

1. **Environment Configuration**
   - Valid IMS credentials in environment variables
   - Access to IMS test environment (ims_one or iscmga_test)
   - Network connectivity to IMS SOAP endpoints

2. **Required Environment Variables**
   ```bash
   IMS_ONE_USERNAME=your_username
   IMS_ONE_PASSWORD=your_password
   IMS_ONE_ENVIRONMENT=your_environment
   ```

## Running Tests

### Run All Tests
```bash
python run_tests.py
```

### Run Specific Test Module
```bash
python run_tests.py -t test_insured_service
```

### Run Specific Test Case
```bash
python run_tests.py -t test_insured_service.TestIMSInsuredService.test_01_create_insured
```

### Run Tests with Pattern
```bash
python run_tests.py -p insured  # Runs all tests with "insured" in the name
```

### Additional Options
```bash
# Verbose output
python run_tests.py -v

# List available tests
python run_tests.py -l

# Choose environment
python run_tests.py -e iscmga_test

# Skip binding/issuance tests (for restricted environments)
python run_tests.py --skip-binding

# Skip Excel rater tests
python run_tests.py --skip-excel
```

## Test Modules

### 1. test_authentication.py
- Token acquisition and caching
- Token refresh logic
- Environment switching
- Concurrent authentication handling

### 2. test_insured_service.py
- Create new insureds
- Search existing insureds
- Fuzzy matching algorithms
- Update insured information
- Location and contact management

### 3. test_producer_service.py
- Producer search and matching
- Underwriter lookup by name
- Producer contact management
- Default producer assignment

### 4. test_quote_service.py
- Submission creation
- Quote creation and options
- Premium calculation
- Quote binding
- Policy issuance
- Excel rater integration

### 5. test_document_service.py
- Folder management
- Document upload and retrieval
- Associated document handling
- Document templates
- Batch operations

### 6. test_data_access_service.py
- Execute queries
- Parameterized queries
- Lookup data retrieval
- Program-specific data storage
- Entity search by external ID

### 7. test_workflow_orchestrator.py
- Complete transaction workflows
- Field mapping integration
- Entity matching in workflows
- State transitions
- Error handling

## Test Data Management

The test suite automatically:
- Generates unique test IDs to avoid conflicts
- Tracks created entities for cleanup
- Uses test-specific naming conventions
- Handles test data isolation

## Logging

Test execution logs are saved to:
```
tests/ims_services/logs/test_run_YYYYMMDD_HHMMSS.log
```

Logs include:
- Test execution details
- API requests/responses
- Entity GUIDs created
- Error messages and stack traces

## Best Practices

1. **Test Isolation**
   - Each test creates its own test data
   - Tests don't depend on external data
   - Unique IDs prevent conflicts

2. **Error Handling**
   - Tests gracefully handle API failures
   - Skip tests when features unavailable
   - Clear error messages for debugging

3. **Performance**
   - Reuse authentication tokens
   - Minimize API calls
   - Use cached lookup data when possible

## Troubleshooting

### Authentication Failures
- Verify environment variables are set
- Check credentials are valid
- Ensure correct environment selected

### Test Failures
- Check logs for detailed error messages
- Verify IMS service availability
- Ensure test data permissions

### Network Issues
- Verify firewall/proxy settings
- Check IMS endpoint accessibility
- Review SSL certificate validation

## Extending Tests

To add new tests:

1. Create test class inheriting from `IMSServiceTestBase`
2. Use provided helper methods for common operations
3. Follow naming convention: `test_XX_description`
4. Add module to `get_test_modules()` in run_tests.py

Example:
```python
class TestNewFeature(IMSServiceTestBase):
    def test_01_new_functionality(self):
        """Test description"""
        # Test implementation
        self.assertIsGuid(some_guid)
```

## CI/CD Integration

The test suite can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run IMS Tests
  env:
    IMS_ONE_USERNAME: ${{ secrets.IMS_USERNAME }}
    IMS_ONE_PASSWORD: ${{ secrets.IMS_PASSWORD }}
  run: |
    python tests/ims_services/run_tests.py --skip-binding
```

## Notes

- Some tests may be skipped in restricted environments
- Binding/issuance tests require special permissions
- Excel rater tests need template availability
- Test execution time varies by environment load