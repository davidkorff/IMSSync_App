# Program Launch Checklist - IMS Integration

## Overview

This document provides a comprehensive checklist for launching new insurance programs that integrate with IMS using direct premium pass-through from source systems. This architecture supports multiple insurance programs with program-specific data storage while avoiding Excel rater calculations.

## Architecture Summary

```
Source System (Triton) → RSG Integration Service → IMS (One_IMS)
                           ↓
                    Custom Program Tables
                    (Program-specific data storage)
```

### Key Design Principles:
- **Direct Premium Pass-Through**: Premiums from source systems are passed directly to IMS without calculation
- **Program-Specific Storage**: Each program has custom tables for additional data storage
- **External ID Linking**: Use UpdateExternalQuoteId for subsequent transaction linking
- **No Excel Raters**: Direct data storage in custom IMS tables using stored procedures

---

## Phase 1: Pre-Launch Planning

### 📋 **1.1 Business Requirements**
- [ ] Define program name and identifier (e.g., "RSG_Triton", "RSG_Xuber")
- [ ] Identify source system and data format
- [ ] Document line of business and coverage types
- [ ] Confirm states where program will operate
- [ ] Define producer(s) and underwriter(s)
- [ ] Establish premium calculation ownership (source system vs IMS)

### 📋 **1.2 Data Mapping Requirements**
- [ ] Complete field mapping using `IMS_INTEGRATION_FIELD_MAPPING.md`
- [ ] Identify minimum required fields for IMS
- [ ] Document additional program-specific fields
- [ ] Define data transformation rules
- [ ] Establish lookup procedures for entities (Producer, Underwriter, Line)

### 📋 **1.3 Technical Architecture**
- [ ] Choose integration method:
  - [ ] Database polling (recommended for Triton-like systems)
  - [ ] Webhook/API push (for real-time systems)
  - [ ] Batch file processing
- [ ] Define transaction types to support:
  - [ ] New Business (required)
  - [ ] Endorsements (optional)
  - [ ] Cancellations (optional)

---

## Phase 2: IMS Environment Setup

### 🔧 **2.1 IMS Configuration**
- [ ] **Create Producer Records** (if new)
  - [ ] Add producer using `AddProducer` / `AddProducerWithLocation`
  - [ ] Document Producer GUID for configuration
  - [ ] Set up producer licensing information

- [ ] **Create Underwriter Records** (if new)
  - [ ] Add underwriter to IMS
  - [ ] Document Underwriter GUID for configuration
  - [ ] **Create custom stored procedure** `FindUnderwriterByName_WS` (see template below)

- [ ] **Line of Business Setup**
  - [ ] Verify line exists in IMS or create new
  - [ ] Document Line GUID for configuration
  - [ ] Set up line-specific settings

- [ ] **Program/Rater Configuration**
  - [ ] Create program entry in IMS
  - [ ] Document Program ID and Factor Set GUID
  - [ ] Configure billing and location defaults

### 🔧 **2.2 Custom Database Objects**

#### **Custom Tables for Program Data Storage**
```sql
-- Example for RSG Triton program
CREATE TABLE [dbo].[RSG_Triton_PolicyData] (
    [QuoteGUID] UNIQUEIDENTIFIER NOT NULL,
    [ExternalPolicyID] NVARCHAR(50),
    [VehicleCount] INT,
    [LocationCount] INT,
    [BusinessDescription] NVARCHAR(500),
    [IndustryCode] NVARCHAR(10),
    [PayrollAmount] DECIMAL(18,2),
    [SalesAmount] DECIMAL(18,2),
    [OriginalPremium] DECIMAL(18,2),
    [SourceSystemData] NVARCHAR(MAX), -- JSON storage
    [CreatedDate] DATETIME2 DEFAULT GETUTCDATE(),
    [UpdatedDate] DATETIME2 DEFAULT GETUTCDATE(),
    CONSTRAINT [PK_RSG_Triton_PolicyData] PRIMARY KEY ([QuoteGUID])
);

CREATE TABLE [dbo].[RSG_Triton_Vehicles] (
    [ID] INT IDENTITY(1,1) NOT NULL,
    [QuoteGUID] UNIQUEIDENTIFIER NOT NULL,
    [VehicleSequence] INT NOT NULL,
    [VIN] NVARCHAR(20),
    [Year] INT,
    [Make] NVARCHAR(50),
    [Model] NVARCHAR(50),
    [VehicleType] NVARCHAR(50),
    [GVW] INT,
    [Radius] INT,
    [CreatedDate] DATETIME2 DEFAULT GETUTCDATE(),
    CONSTRAINT [PK_RSG_Triton_Vehicles] PRIMARY KEY ([ID]),
    CONSTRAINT [FK_RSG_Triton_Vehicles_PolicyData] 
        FOREIGN KEY ([QuoteGUID]) REFERENCES [RSG_Triton_PolicyData]([QuoteGUID])
);

CREATE TABLE [dbo].[RSG_Triton_Locations] (
    [ID] INT IDENTITY(1,1) NOT NULL,
    [QuoteGUID] UNIQUEIDENTIFIER NOT NULL,
    [LocationSequence] INT NOT NULL,
    [Address] NVARCHAR(255),
    [City] NVARCHAR(100),
    [State] NVARCHAR(2),
    [ZipCode] NVARCHAR(10),
    [LocationType] NVARCHAR(50),
    [Payroll] DECIMAL(18,2),
    [Sales] DECIMAL(18,2),
    [CreatedDate] DATETIME2 DEFAULT GETUTCDATE(),
    CONSTRAINT [PK_RSG_Triton_Locations] PRIMARY KEY ([ID]),
    CONSTRAINT [FK_RSG_Triton_Locations_PolicyData] 
        FOREIGN KEY ([QuoteGUID]) REFERENCES [RSG_Triton_PolicyData]([QuoteGUID])
);
```

#### **Custom Stored Procedures** (Required suffix: `_WS`)
```sql
-- Underwriter lookup procedure
CREATE PROCEDURE [dbo].[FindUnderwriterByName_WS]
    @UnderwriterName NVARCHAR(255),
    @LineGuid UNIQUEIDENTIFIER = NULL
AS
BEGIN
    SELECT 
        UnderwriterGuid,
        FirstName,
        LastName,
        Email,
        Phone,
        Active
    FROM tblUnderwriters 
    WHERE (FirstName + ' ' + LastName LIKE '%' + @UnderwriterName + '%'
           OR Email LIKE '%' + @UnderwriterName + '%')
    AND Active = 1
    ORDER BY 
        CASE WHEN (FirstName + ' ' + LastName) = @UnderwriterName THEN 1 ELSE 2 END,
        LastName, FirstName
END

-- Program data storage procedure
CREATE PROCEDURE [dbo].[StoreRSGTritonData_WS]
    @QuoteGUID UNIQUEIDENTIFIER,
    @ExternalPolicyID NVARCHAR(50),
    @VehicleData NVARCHAR(MAX), -- JSON array
    @LocationData NVARCHAR(MAX), -- JSON array
    @PolicyData NVARCHAR(MAX), -- JSON object
    @OriginalPremium DECIMAL(18,2)
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Store main policy data
    MERGE [RSG_Triton_PolicyData] AS target
    USING (SELECT @QuoteGUID AS QuoteGUID) AS source
    ON target.QuoteGUID = source.QuoteGUID
    WHEN MATCHED THEN
        UPDATE SET 
            ExternalPolicyID = @ExternalPolicyID,
            OriginalPremium = @OriginalPremium,
            SourceSystemData = @PolicyData,
            UpdatedDate = GETUTCDATE()
    WHEN NOT MATCHED THEN
        INSERT (QuoteGUID, ExternalPolicyID, OriginalPremium, SourceSystemData)
        VALUES (@QuoteGUID, @ExternalPolicyID, @OriginalPremium, @PolicyData);
    
    -- Store vehicles and locations using JSON parsing
    -- (Implementation depends on specific JSON structure)
    
    SELECT 'SUCCESS' AS Result, @QuoteGUID AS QuoteGUID;
END
```

### 🔧 **2.3 Lookup Table Setup**
- [ ] **Create Line GUID lookup**
  ```sql
  -- Document these values for configuration
  SELECT LineGuid, LineName FROM tblLines WHERE Active = 1;
  ```

- [ ] **Create Producer GUID lookup**
  ```sql
  -- Test producer search
  EXEC ProducerSearch @searchString = 'Producer Name', @startWith = 0;
  ```

- [ ] **Create Business Type mapping**
  ```sql
  -- Document business type IDs
  SELECT BusinessTypeID, BusinessTypeName FROM tblBusinessTypes;
  ```

---

## Phase 3: Integration Service Configuration

### ⚙️ **3.1 Environment Configuration** (`.env` file)
```env
# IMS Environment Settings
DEFAULT_ENVIRONMENT=test
IMS_CONFIG_PATH=./IMS_Configs

# Program-Specific Settings (Example: RSG_Triton)
RSG_TRITON_PRODUCER_GUID=12345678-1234-1234-1234-123456789012
RSG_TRITON_UNDERWRITER_GUID=87654321-4321-4321-4321-210987654321
RSG_TRITON_LINE_GUID=11111111-2222-3333-4444-555555555555
RSG_TRITON_PROGRAM_ID=1001
RSG_TRITON_FACTOR_SET_GUID=aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee

# Source System Settings (Triton MySQL example)
TRITON_MYSQL_HOST=your-triton-host
TRITON_MYSQL_PORT=3306
TRITON_MYSQL_DATABASE=triton_db
TRITON_MYSQL_USERNAME=integration_user
TRITON_MYSQL_PASSWORD=secure_password

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

### ⚙️ **3.2 Program-Specific Service Configuration**
- [ ] **Create transformer class** for data mapping
  ```python
  # app/integrations/your_program/transformer.py
  class YourProgramTransformer:
      def transform_to_ims_format(self, source_data: dict) -> dict:
          # Convert source data to IMS format
          # Implement direct premium pass-through
          return ims_data
  ```

- [ ] **Configure polling/extraction service**
- [ ] **Set up webhook endpoints** (if applicable)
- [ ] **Configure error handling and logging**

---

## Phase 4: Code Implementation

### 💻 **4.1 Integration Service Updates**

#### **Add Program-Specific Route** (`app/api/routes.py`)
```python
@router.post("/programs/rsg_triton/process")
async def process_rsg_triton_transaction(
    transaction_data: dict, 
    background_tasks: BackgroundTasks
):
    """Process RSG Triton transaction with direct premium pass-through"""
    # Validate transaction data
    # Transform to IMS format
    # Process through workflow service
    # Store additional data in custom tables
```

#### **Update Workflow Service** (`app/services/ims_workflow_service.py`)
```python
def _process_program_specific_data(self, transaction: Transaction, program: str):
    """Store program-specific data in custom tables"""
    if program == "rsg_triton":
        # Call custom stored procedure
        self.soap_client.execute_command(
            "StoreRSGTritonData",
            parameters=[
                ("QuoteGUID", transaction.ims_processing.quote.guid),
                ("ExternalPolicyID", transaction.external_id),
                ("PolicyData", json.dumps(transaction.parsed_data))
            ]
        )
```

#### **Direct Premium Pass-Through Implementation**
```python
def _process_manual_rating(self, transaction: Transaction) -> None:
    """Process rating manually with direct premium pass-through"""
    # Extract premium directly from source system
    source_premium = transaction.parsed_data.get("premium", 0.0)
    
    # NO CALCULATION - Direct pass-through
    self.soap_client.add_premium(
        transaction.ims_processing.quote.guid,
        transaction.ims_processing.quote.quote_option_id,
        source_premium,  # Use source premium directly
        "Premium from source system (direct pass-through)"
    )
```

### 💻 **4.2 External ID Linking Setup**
```python
def _finalize_policy_creation(self, transaction: Transaction) -> None:
    """Link IMS policy back to source system"""
    # Use UpdateExternalQuoteId for future lookups
    self.soap_client.update_external_quote_id(
        transaction.ims_processing.quote.guid,
        transaction.external_id,  # Source system policy ID
        "RSG_Triton"  # External system identifier
    )
```

---

## Phase 5: Testing & Validation

### 🧪 **5.1 Unit Testing**
- [ ] Test producer lookup functionality
- [ ] Test underwriter lookup (custom procedure)
- [ ] Test data transformation accuracy
- [ ] Test premium pass-through (no calculation)
- [ ] Test custom data storage procedures

### 🧪 **5.2 Integration Testing**
- [ ] Test complete workflow: Insured → Submission → Quote → Rating → Bind → Issue
- [ ] Test custom data storage in program-specific tables
- [ ] Test external ID linking functionality
- [ ] Verify data accuracy in IMS after processing

### 🧪 **5.3 End-to-End Testing**
- [ ] Process sample transactions from source system
- [ ] Verify policies created correctly in IMS
- [ ] Confirm custom data stored in program tables
- [ ] Test subsequent transaction processing (endorsements/cancellations)

---

## Phase 6: Deployment

### 🚀 **6.1 Pre-Deployment Checklist**
- [ ] All GUIDs configured correctly in `.env`
- [ ] Custom stored procedures deployed to IMS database
- [ ] Custom tables created in IMS database
- [ ] Producer/Underwriter records exist in IMS
- [ ] Line of business configured
- [ ] Integration service code tested

### 🚀 **6.2 Production Deployment**
- [ ] Deploy integration service to IMS network computer
- [ ] Update `.env` with production IMS credentials
- [ ] Configure source system connections
- [ ] Set up monitoring and logging
- [ ] Establish error alerting

### 🚀 **6.3 Go-Live Process**
- [ ] Process test transactions in production
- [ ] Monitor for errors and performance
- [ ] Validate data accuracy
- [ ] Enable automatic processing
- [ ] Document any issues and resolutions

---

## Phase 7: Post-Launch Support

### 📊 **7.1 Monitoring**
- [ ] Set up transaction volume monitoring
- [ ] Monitor error rates and types
- [ ] Track processing performance
- [ ] Monitor IMS system impact

### 📊 **7.2 Maintenance**
- [ ] Regular log review and cleanup
- [ ] Database maintenance for custom tables
- [ ] Configuration updates as needed
- [ ] Source system integration maintenance

---

## Quick Reference: Required GUIDs for New Program

### **Critical Configuration Values to Obtain:**

1. **Producer GUID**: From `ProducerSearch` or IMS admin
   ```xml
   <ProducerSearch>
       <searchString>Your Producer Name</searchString>
   </ProducerSearch>
   ```

2. **Underwriter GUID**: From custom `FindUnderwriterByName_WS` procedure

3. **Line GUID**: From IMS line configuration
   ```sql
   SELECT LineGuid, LineName FROM tblLines WHERE LineName = 'Your Line of Business';
   ```

4. **Program/Factor Set GUID**: From IMS program configuration

5. **Default Location GUIDs**: Company office locations for quoting/issuing

### **Custom Stored Procedure Requirements:**
- All custom procedures must end with `_WS` suffix
- Use `ExecuteCommand` or `ExecuteDataSet` for calling from integration service
- Return structured data for easy parsing

---

## Risk Management

### ⚠️ **Common Pitfalls to Avoid:**
- **Don't use Excel raters** - Implement direct premium pass-through
- **Don't calculate pro-rata** - Use source system premiums directly
- **Always create custom tables** for program-specific data
- **Use UpdateExternalQuoteId** for linking subsequent transactions
- **Test producer/underwriter lookups** before go-live
- **Validate all GUID configurations** in test environment first

### ⚠️ **Backup Plans:**
- Maintain manual policy creation procedures
- Document rollback procedures for failed integrations
- Keep source system data for reprocessing if needed
- Plan for IMS downtime scenarios

---

## Success Metrics

### 📈 **Key Performance Indicators:**
- **Processing Speed**: < 30 seconds per policy
- **Error Rate**: < 1% of transactions
- **Data Accuracy**: 100% of required fields populated
- **Integration Uptime**: > 99% availability

This checklist ensures comprehensive planning and execution for launching new insurance program integrations with IMS while maintaining the direct premium pass-through architecture.