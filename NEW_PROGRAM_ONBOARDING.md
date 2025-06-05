# New Program Onboarding Guide

## Overview

This guide provides step-by-step instructions for integrating a new insurance program/system with IMS. It covers both simple integrations (basic policy data) and complex scenarios (schedules, vehicle lists, custom data structures).

---

## 1. INTEGRATION ARCHITECTURE OPTIONS

### **Option A: Program-Specific Endpoints** (Current Triton approach)
```
POST /api/{program}/api/v1/transactions
POST /api/{program}/transaction/new
POST /api/{program}/transaction/update
```

**Pros:** 
- Custom validation per program
- Program-specific transformers
- Dedicated authentication

**Cons:**
- Code duplication
- Maintenance overhead
- Not scalable

### **Option B: Generic Endpoints** ⭐ **RECOMMENDED**
```
POST /api/transaction/new?source={program}
POST /api/transaction/update?source={program}
POST /api/transaction/{transaction_id}
```

**Pros:**
- Single endpoint for all programs
- Source identified via parameter
- Centralized processing
- Easier maintenance

**Cons:**
- Need flexible validation
- Complex data structures require planning

---

## 2. ONBOARDING CHECKLIST

### **Phase 1: Discovery & Planning** 📋

- [ ] **Program Information**
  - Program name and identifier
  - Line of business
  - States of operation
  - Expected transaction volume

- [ ] **Data Assessment**
  - [ ] Core policy fields mapping to IMS
  - [ ] Additional fields NOT in IMS (schedules, vehicles, etc.)
  - [ ] Data format (JSON, XML, CSV)
  - [ ] Unique identifiers and keys

- [ ] **Integration Method**
  - [ ] Push (webhook/API)
  - [ ] Pull (database polling)
  - [ ] Batch (file transfer)

### **Phase 2: IMS Configuration** 🔧

- [ ] **Create IMS Entities**
  ```sql
  -- 1. Verify/Create Producer records
  -- 2. Create Underwriter records
  -- 3. Set up Line of Business
  -- 4. Configure Programs/Products
  -- 5. Create Rater entries (if needed)
  ```

- [ ] **Obtain GUIDs**
  - [ ] Default Producer GUIDs
  - [ ] Line of Business GUIDs
  - [ ] Company Location GUIDs
  - [ ] Rater IDs and Factor Set GUIDs

- [ ] **Create Lookup Procedures**
  ```sql
  -- Example: Find underwriter by name
  CREATE PROCEDURE [dbo].[Find{Program}UnderwriterByName_WS]
      @UnderwriterName NVARCHAR(255)
  AS
  BEGIN
      -- Program-specific underwriter lookup logic
  END
  ```

### **Phase 3: Database Schema** 🗄️

#### **A. Core Transaction Storage** (Already exists)
```sql
-- Main transactions table (existing)
transactions (
    transaction_id,
    source,         -- 'triton', 'xuber', 'newprogram'
    type,
    status,
    raw_data,       -- Complete JSON/XML
    parsed_data,
    processed_data
)
```

#### **B. Program-Specific Tables** (Create new)
```sql
-- Example: Vehicle schedule for auto program
CREATE TABLE {program}_vehicles (
    id INT IDENTITY(1,1) PRIMARY KEY,
    transaction_id VARCHAR(255),
    vehicle_number INT,
    vin VARCHAR(50),
    year INT,
    make VARCHAR(50),
    model VARCHAR(50),
    garaging_address VARCHAR(255),
    garaging_city VARCHAR(100),
    garaging_state VARCHAR(2),
    garaging_zip VARCHAR(10),
    coverage_type VARCHAR(50),
    limit DECIMAL(12,2),
    deductible DECIMAL(12,2),
    premium DECIMAL(12,2),
    created_at DATETIME DEFAULT GETDATE(),
    
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
);

-- Example: Location schedule for property program
CREATE TABLE {program}_locations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    transaction_id VARCHAR(255),
    location_number INT,
    building_number INT,
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(2),
    zip VARCHAR(10),
    occupancy_type VARCHAR(100),
    construction_type VARCHAR(50),
    year_built INT,
    square_footage INT,
    building_value DECIMAL(15,2),
    contents_value DECIMAL(15,2),
    premium DECIMAL(12,2),
    created_at DATETIME DEFAULT GETDATE(),
    
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
);

-- Example: Dynamic data storage (IMS-linked)
CREATE TABLE dynamic_data_{program} (
    QuoteOptionGUID UNIQUEIDENTIFIER,
    {program}_policy_id VARCHAR(50),
    -- All program-specific fields
    additional_data NTEXT, -- JSON blob for flexibility
    created_at DATETIME DEFAULT GETDATE()
);
```

### **Phase 4: Code Implementation** 💻

#### **A. Create Program Service**
```python
# app/integrations/{program}/__init__.py
# app/integrations/{program}/service.py
# app/integrations/{program}/transformer.py

class {Program}IntegrationService:
    def __init__(self, environment=None, config=None):
        self.environment = environment
        self.config = config or {}
        self.ims_workflow_service = IMSWorkflowService(environment)
        self.transformer = {Program}Transformer(config)
    
    def process_transaction(self, transaction: Transaction) -> Transaction:
        # Program-specific processing logic
        pass
```

#### **B. Create Transformer**
```python
class {Program}Transformer:
    def transform_to_ims_format(self, source_data: Dict) -> Dict:
        """Transform program data to IMS format"""
        return {
            "insured": self._extract_insured(source_data),
            "producer": self._extract_producer(source_data),
            "quote": self._extract_quote(source_data),
            # Core IMS fields only
        }
    
    def extract_additional_data(self, source_data: Dict) -> Dict:
        """Extract program-specific data for storage"""
        return {
            "schedules": source_data.get("schedules", []),
            "vehicles": source_data.get("vehicles", []),
            "locations": source_data.get("locations", []),
            # All non-IMS fields
        }
```

#### **C. Update Transaction Processor**
```python
# In app/services/transaction_processor.py

def _get_integration_service(self, source: str):
    """Get the appropriate integration service based on source"""
    if source == "triton":
        return TritonIntegrationService(self.environment)
    elif source == "xuber":
        return XuberIntegrationService(self.environment)
    elif source == "{newprogram}":
        return {NewProgram}IntegrationService(self.environment)
    else:
        # Use generic service
        return GenericIntegrationService(self.environment)
```

#### **D. Store Additional Data**
```python
def store_program_schedules(self, transaction_id: str, schedules: List[Dict]):
    """Store program-specific schedule data"""
    
    # Option 1: Direct database storage
    for schedule in schedules:
        self.db.execute("""
            INSERT INTO {program}_vehicles 
            (transaction_id, vin, year, make, model, ...)
            VALUES (?, ?, ?, ?, ?, ...)
        """, [transaction_id, schedule['vin'], ...])
    
    # Option 2: IMS dynamic_data storage (after quote creation)
    if transaction.ims_processing.quote:
        self.soap_client.execute_command(
            "Store{Program}Data_WS",
            {
                "QuoteOptionGUID": transaction.ims_processing.quote.guid,
                "ScheduleData": json.dumps(schedules)
            }
        )
```

### **Phase 5: Configuration** ⚙️

#### **A. Environment Variables**
```bash
# .env additions
{PROGRAM}_DEFAULT_PRODUCER_GUID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
{PROGRAM}_DEFAULT_LINE_GUID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
{PROGRAM}_PRIMARY_RATER_ID=12345
{PROGRAM}_PRIMARY_FACTOR_SET_GUID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
{PROGRAM}_API_KEYS='["program-key-1","program-key-2"]'
{PROGRAM}_ENABLE_SCHEDULES=true
```

#### **B. Program Configuration**
```python
# In app/core/config.py
"{program}": {
    "default_producer_guid": os.getenv("{PROGRAM}_DEFAULT_PRODUCER_GUID"),
    "default_line_guid": os.getenv("{PROGRAM}_DEFAULT_LINE_GUID"),
    "enable_schedules": os.getenv("{PROGRAM}_ENABLE_SCHEDULES", "false") == "true",
    "schedule_tables": ["vehicles", "locations", "drivers"],
    "raters": {
        "Primary": {
            "rater_id": int(os.getenv("{PROGRAM}_PRIMARY_RATER_ID", "1")),
            "factor_set_guid": os.getenv("{PROGRAM}_PRIMARY_FACTOR_SET_GUID"),
            "template": "{program}_primary.xlsx"
        }
    }
}
```

### **Phase 6: Testing** 🧪

#### **A. Create Test Scripts**
```python
# test_{program}_integration.py
def test_{program}_integration():
    """Test complete {program} integration flow"""
    
    # 1. Test data transformation
    sample_data = load_sample_{program}_data()
    transformed = transformer.transform_to_ims_format(sample_data)
    assert_valid_ims_format(transformed)
    
    # 2. Test schedule extraction
    schedules = transformer.extract_additional_data(sample_data)
    assert len(schedules['vehicles']) > 0
    
    # 3. Test end-to-end flow
    response = client.post("/api/transaction/new?source={program}", 
                          json=sample_data)
    assert response.status_code == 200
```

#### **B. Sample Data Files**
```
test_data/
├── {program}_minimal.json    # Minimum required fields
├── {program}_complete.json   # All fields including schedules
├── {program}_vehicles.json   # Vehicle schedule sample
└── {program}_errors.json     # Invalid data for testing
```

### **Phase 7: Documentation** 📚

#### **A. Program-Specific Docs**
```
Documentation/{Program}/
├── FIELD_MAPPING.md         # Source fields → IMS mapping
├── SCHEDULE_FORMATS.md      # Additional data structures
├── BUSINESS_RULES.md        # Validation and requirements
├── SAMPLE_REQUESTS.md       # API examples
└── TROUBLESHOOTING.md       # Common issues
```

#### **B. Update Main Documentation**
- Add program to README.md
- Update API documentation
- Add to deployment requirements
- Update configuration templates

---

## 3. HANDLING COMPLEX DATA STRUCTURES

### **Scenario 1: Vehicle Schedules (Auto Programs)**
```json
{
  "policy": {
    "insured": {...},
    "coverage": {...}
  },
  "vehicles": [
    {
      "vehicle_number": 1,
      "vin": "1HGBH41JXMN109186",
      "year": 2023,
      "make": "Honda",
      "model": "Civic",
      "garaging_zip": "78701",
      "coverages": {
        "liability": {"limit": 1000000, "premium": 500},
        "collision": {"deductible": 1000, "premium": 300}
      }
    }
  ]
}
```

**Storage Strategy:**
1. Core policy data → IMS standard workflow
2. Vehicle schedule → `{program}_vehicles` table
3. Link via transaction_id and QuoteOptionGUID
4. Aggregate premiums for IMS total

### **Scenario 2: Location Schedules (Property Programs)**
```json
{
  "policy": {...},
  "locations": [
    {
      "location_number": 1,
      "address": "123 Main St",
      "buildings": [
        {
          "building_number": 1,
          "occupancy": "Office",
          "construction": "Frame",
          "value": 500000
        }
      ]
    }
  ]
}
```

**Storage Strategy:**
1. Hierarchical storage (locations → buildings)
2. Separate tables with foreign keys
3. Calculate location-level premiums
4. Roll up to policy total

### **Scenario 3: Named Insured Schedules**
```json
{
  "policy": {...},
  "additional_insureds": [
    {
      "name": "ABC Landlord LLC",
      "relationship": "Landlord",
      "address": "456 Oak St",
      "certificate_required": true
    }
  ]
}
```

**Storage Strategy:**
1. Store in `{program}_additional_insureds` table
2. Generate certificates post-binding
3. Link to IMS document storage

---

## 4. GENERIC ENDPOINT IMPLEMENTATION

### **Recommended Approach:**
```python
@router.post("/api/v2/policy/submit")
async def submit_policy(
    request: Request,
    source: str = Query(..., description="Source system identifier"),
    program: str = Query(..., description="Program identifier"),
    x_api_key: str = Header(..., description="API key for authentication")
):
    """
    Generic policy submission endpoint for all programs
    
    Query Parameters:
    - source: System sending data (triton, xuber, newsystem)
    - program: Insurance program (auto, property, liability)
    
    Body: Program-specific JSON structure
    """
    
    # Validate API key for source
    validate_source_api_key(x_api_key, source)
    
    # Get body
    data = await request.json()
    
    # Route to appropriate processor
    processor = get_program_processor(source, program)
    result = await processor.process(data)
    
    return result
```

### **Benefits:**
- Single endpoint for all programs
- Flexible validation based on source/program
- Easy to add new programs
- Consistent API interface

---

## 5. DEPLOYMENT STEPS

### **For New Program "{program}":**

1. **Database Setup**
   ```bash
   mysql -u root -p ims_integration < create_{program}_tables.sql
   ```

2. **Configuration**
   ```bash
   # Add to .env
   echo "{PROGRAM}_DEFAULT_PRODUCER_GUID=xxx" >> .env
   ```

3. **Code Deployment**
   ```bash
   # Copy program integration code
   cp -r app/integrations/{program} /opt/rsg-integration/app/integrations/
   
   # Restart service
   systemctl restart rsg-api
   ```

4. **Testing**
   ```bash
   # Run program-specific tests
   python test_{program}_integration.py
   
   # Test with sample data
   curl -X POST http://localhost:8000/api/transaction/new?source={program} \
     -H "X-API-Key: {program}-api-key" \
     -H "Content-Type: application/json" \
     -d @test_data/{program}_minimal.json
   ```

5. **Monitoring**
   ```bash
   # Check logs
   tail -f ims_integration.log | grep {program}
   
   # Verify database
   mysql -e "SELECT COUNT(*) FROM {program}_vehicles"
   ```

---

## 6. BEST PRACTICES

### **DO:**
- ✅ Use generic endpoints with source/program parameters
- ✅ Create program-specific tables for complex data
- ✅ Store complete source data for audit trail
- ✅ Implement proper error handling per program
- ✅ Document all field mappings thoroughly

### **DON'T:**
- ❌ Hardcode program-specific logic in core services
- ❌ Mix program data in shared tables
- ❌ Assume all programs have same fields
- ❌ Skip validation for "simple" programs
- ❌ Forget to test edge cases

---

## 7. QUICK START TEMPLATE

For a new program called "WorkComp":

1. **Create structure:**
   ```bash
   mkdir -p app/integrations/workcomp
   touch app/integrations/workcomp/__init__.py
   touch app/integrations/workcomp/service.py
   touch app/integrations/workcomp/transformer.py
   ```

2. **Copy template:**
   ```bash
   cp app/integrations/triton/*.py app/integrations/workcomp/
   # Then modify for WorkComp specifics
   ```

3. **Create tables:**
   ```sql
   CREATE TABLE workcomp_employees (
       id INT IDENTITY(1,1) PRIMARY KEY,
       transaction_id VARCHAR(255),
       employee_name VARCHAR(255),
       job_class_code VARCHAR(10),
       annual_payroll DECIMAL(12,2),
       -- etc.
   );
   ```

4. **Configure:**
   ```bash
   # .env
   WORKCOMP_DEFAULT_PRODUCER_GUID=xxx
   WORKCOMP_ENABLE_EMPLOYEE_SCHEDULE=true
   ```

5. **Test:**
   ```bash
   python test_workcomp_integration.py
   ```

---

This guide provides a complete framework for onboarding any new program, from simple to complex!