# FINANCIAL HARDCODED VALUES - DEEP DIVE AUDIT
## Critical Fee, Charge, and Commission Configuration

---

## 🚨 CRITICAL FINANCIAL HARDCODED VALUES

### 1. POLICY FEE CONFIGURATION (High Risk!)

**ChargeCode: `12374`** - Policy Fee Charge Code
- Found in: `spApplyTritonPolicyFee_WS.sql` (line 10)
- Found in: `Triton_ProcessFlatCancellation_WS.sql` (line 283)
- Purpose: Identifies the policy fee charge in IMS

**CompanyFeeID: `37277712`** - Triton Policy Fee ID
- Found in: `spApplyTritonPolicyFee_WS.sql` (lines 52, 79)
- Found in: `Triton_ProcessFlatCancellation_WS.sql` (line 284)
- Purpose: Links to specific fee configuration in IMS

```sql
-- From spApplyTritonPolicyFee_WS.sql
DECLARE
    @Policy_FeeCode SMALLINT = 12374,  -- Charge code for Policy Fee
    @CompanyFeeID INT = 37277712;      -- Triton Policy Fee CompanyFeeID
```

**RISK:** If these IDs don't exist in production or are different, policy fees won't be applied correctly!

### 2. FEE TYPE IDs

**FeeTypeID: `2`** - Flat Fee Type
- Found in: `spApplyTritonPolicyFee_WS.sql` (line 100)
- Purpose: Indicates this is a flat fee, not percentage-based

```sql
FeeTypeID,
2,  -- Flat fee type
```

### 3. DEFAULT CHARGE CODES

**Default ChargeCode: `1`** - Used as fallback
- Found in: `ProcessFlatEndorsement.sql` (line 360)
- Found in: `ProcessFlatCancellation.sql` (line 371)
- Found in: `ProcessFlatReinstatement.sql` (line 370)

```sql
IF @MainChargeCode IS NULL
    SET @MainChargeCode = 1;  -- Default charge code
```

### 4. COMMISSION RATES

**Default Company Commission: `0.25` (25%)**
- Found in: `config.py` (line 49)
- Used as default when not specified in payload

```python
"default_company_commission": 0.25
```

### 5. POLICY FEE AMOUNTS (From Test Data)

**Common Policy Fee Values:**
- `250.00` - Used in many test files
- `350.00` - Found in CSV imports

These appear to be coming from Triton payload, not hardcoded.

---

## 📊 FINANCIAL CONFIGURATION MAPPING

| Value | Type | Location | Environment-Specific? | Risk Level |
|-------|------|----------|---------------------|------------|
| 12374 | Policy Fee ChargeCode | SQL Procs | YES - Must exist in IMS | **CRITICAL** |
| 37277712 | CompanyFeeID | SQL Procs | YES - Must match IMS | **CRITICAL** |
| 2 | FeeTypeID (Flat) | SQL Procs | Probably same | Medium |
| 1 | Default ChargeCode | SQL Procs | Probably same | Low |
| 0.25 | Company Commission | config.py | Maybe different | Medium |

---

## ⚠️ PRODUCTION VERIFICATION REQUIRED

### SQL Queries to Verify in Production:

```sql
-- 1. Verify Policy Fee Charge Code exists
SELECT * FROM tblCharges 
WHERE ChargeCode = 12374;

-- 2. Verify Company Fee ID exists
SELECT * FROM tblCompanyFees 
WHERE CompanyFeeID = 37277712;

-- 3. Check if charge code is linked to correct fee
SELECT cf.*, c.*
FROM tblCompanyFees cf
JOIN tblCharges c ON cf.ChargeID = c.ChargeID
WHERE cf.CompanyFeeID = 37277712
  AND c.ChargeCode = 12374;

-- 4. Verify Fee Type
SELECT * FROM tblFeeTypes 
WHERE FeeTypeID = 2;

-- 5. Check default charge code
SELECT * FROM tblCharges 
WHERE ChargeCode = 1;
```

---

## 🔧 RECOMMENDED SOLUTIONS

### Option 1: Configuration Table (BEST)
```sql
CREATE TABLE tblTritonFinancialConfig (
    ConfigKey NVARCHAR(100) PRIMARY KEY,
    ConfigValue NVARCHAR(500),
    Environment NVARCHAR(50)
);

INSERT INTO tblTritonFinancialConfig VALUES
('POLICY_FEE_CHARGE_CODE', '12374', 'PROD'),
('POLICY_FEE_COMPANY_ID', '37277712', 'PROD'),
('FLAT_FEE_TYPE_ID', '2', 'PROD'),
('DEFAULT_CHARGE_CODE', '1', 'PROD'),
('DEFAULT_COMMISSION_RATE', '0.25', 'PROD');
```

### Option 2: Parameters in Stored Procedures
```sql
ALTER PROCEDURE spApplyTritonPolicyFee_WS
    @QuoteGuid UNIQUEIDENTIFIER,
    @PolicyFeeChargeCode SMALLINT = 12374,
    @CompanyFeeID INT = 37277712
AS
```

### Option 3: Environment Variables (For Python)
```env
# Financial Configuration
POLICY_FEE_CHARGE_CODE=12374
POLICY_FEE_COMPANY_ID=37277712
FLAT_FEE_TYPE_ID=2
DEFAULT_CHARGE_CODE=1
DEFAULT_COMPANY_COMMISSION=0.25
```

---

## 🚨 CRITICAL QUESTIONS FOR DEPLOYMENT

1. **ChargeCode 12374**
   - Does this exist in production?
   - Is it the same code for policy fees?
   - Is it active/enabled?

2. **CompanyFeeID 37277712**
   - Does this exist in production?
   - Is it linked to the correct charge code?
   - Is it configured for all states/programs?

3. **Commission Rate 0.25**
   - Is 25% the correct default commission?
   - Does this vary by program or producer?
   - Should this be configurable per environment?

4. **Fee Amounts**
   - Are policy fees always $250 or $350?
   - Do these vary by program?
   - Should these be configurable?

---

## 📝 AFFECTED FILES LIST

### SQL Stored Procedures:
1. `spApplyTritonPolicyFee_WS.sql` - **CRITICAL** - Contains policy fee logic
2. `Triton_ProcessFlatCancellation_WS.sql` - Handles cancellation fees
3. `ProcessFlatEndorsement.sql` - Default charge codes
4. `ProcessFlatCancellation.sql` - Default charge codes
5. `ProcessFlatReinstatement.sql` - Default charge codes

### Python Files:
1. `config.py` - Default commission rate
2. `quote_service.py` - Uses commission from config

---

## ⚡ IMMEDIATE ACTION ITEMS

### Before Production Deployment:

1. **Run verification queries** on production database
2. **Confirm ChargeCode 12374** exists and is correct
3. **Confirm CompanyFeeID 37277712** exists and is correct
4. **Test fee application** with a test quote
5. **Document any differences** between environments

### If Values Are Different:

1. Update SQL procedures with correct values
2. Update config.py with correct commission
3. Create mapping document for all environments
4. Test thoroughly in staging

---

## 🎯 RISK ASSESSMENT

### HIGH RISK:
- **Wrong ChargeCode** = Fees not applied or applied incorrectly
- **Wrong CompanyFeeID** = Fee configuration mismatch
- **Missing IDs** = Stored procedures will fail

### MEDIUM RISK:
- **Wrong commission rate** = Incorrect producer payments
- **Wrong FeeTypeID** = Fees calculated incorrectly

### LOW RISK:
- **Default ChargeCode** = Only used as fallback

---

## TESTING CHECKLIST

- [ ] Verify ChargeCode 12374 in production
- [ ] Verify CompanyFeeID 37277712 in production
- [ ] Test policy fee application
- [ ] Test commission calculation
- [ ] Test cancellation with fees
- [ ] Test endorsement with fees
- [ ] Verify fee amounts in invoices