# CRITICAL HARDCODED VALUES AUDIT
## Full Codebase Analysis for Production Deployment

---

## 🚨 CRITICAL VALUES THAT MUST BE CONFIGURED

### 1. LINE GUIDs (Business Critical - Controls Program Assignment)

These GUIDs determine which insurance program gets assigned!

| GUID | Description | Found In | Environment Variable Needed |
|------|-------------|----------|----------------------------|
| `07564291-CBFE-4BBE-88D1-0548C88ACED4` | Primary Line | config.py:44<br>quote_service.py:253<br>ALL SQL procedures | `TRITON_PRIMARY_LINE_GUID` |
| `08798559-321C-4FC0-98ED-A61B92215F31` | Excess Line | quote_service.py:254<br>SQL procedures | `TRITON_EXCESS_LINE_GUID` |

**ACTION REQUIRED:** 
```env
# Add to .env.production
TRITON_PRIMARY_LINE_GUID=07564291-CBFE-4BBE-88D1-0548C88ACED4  # Verify with IMS team
TRITON_EXCESS_LINE_GUID=08798559-321C-4FC0-98ED-A61B92215F31   # Verify with IMS team
```

### 2. PROGRAM IDs (Critical - Determines Policy Processing)

These are hardcoded in SQL and Python - MUST match between systems!

| Program ID | Market + Line | Found In | Status |
|------------|---------------|----------|--------|
| 11615 | RT + Primary | SQL procs, Python tests | Hardcoded in SQL |
| 11613 | WL + Primary | SQL procs, Python tests | Hardcoded in SQL |
| 11612 | RT + Excess | SQL procs | Hardcoded in SQL |
| 11614 | WL + Excess | SQL procs | Hardcoded in SQL |

**ACTION REQUIRED:** 
- Verify these Program IDs are correct for PRODUCTION
- Consider making them configurable in stored procedures

### 3. LOCATION GUIDs (Organization Structure)

| GUID | Description | Current Location | Config Key |
|------|-------------|------------------|------------|
| `C5C006BB-6437-42F3-95D4-C090ADD3B37D` | Quoting/Issuing Location | config.py:41-42 | `IMS_QUOTING_LOCATION` |
| `DF35D4C7-C663-4974-A886-A1E18D3C9618` | Company Location | config.py:43 | `IMS_COMPANY_LOCATION` |

**ACTION REQUIRED:** Confirm these are the same in DEV and PROD or update accordingly

---

## ⚠️ HARDCODED VALUES BY FILE

### `/app/services/ims/quote_service.py`

```python
Line 253: primary_line_guid = "07564291-CBFE-4BBE-88D1-0548C88ACED4"  # HARDCODED!
Line 254: excess_line_guid = "08798559-321C-4FC0-98ED-A61B92215F31"   # HARDCODED!
Line 256-265: Program ID logic (11615, 11613, 11612, 11614)          # HARDCODED!
```

**FIX NEEDED:**
```python
# Replace with:
primary_line_guid = os.getenv("TRITON_PRIMARY_LINE_GUID")
excess_line_guid = os.getenv("TRITON_EXCESS_LINE_GUID")

# Or better, use config:
primary_line_guid = QUOTE_CONFIG["primary_line_guid"]
excess_line_guid = QUOTE_CONFIG["excess_line_guid"]
```

### `/app/services/ims/auth_service.py`

```python
Line 14: base_url="http://10.64.32.234"  # HARDCODED IP!
```

**FIX NEEDED:** Should use IMS_CONFIG["base_url"] from config.py

### `/app/services/ims/payload_processor_service.py`

Multiple hardcoded values for field mappings and transformations.
- Various status mappings
- Field name mappings
- Default values

**ASSESSMENT:** These are probably OK as hardcoded - they're business logic, not config

### SQL Stored Procedures

**Critical hardcoded values in SQL:**
- Line GUIDs in ALL procedures
- Program IDs (11612, 11613, 11614, 11615)
- Status values
- Table names (OK to hardcode)

---

## 📊 HARDCODED VALUES SUMMARY

### By Category:

| Category | Count | Critical? | Action Required |
|----------|-------|-----------|-----------------|
| GUIDs | 6 unique | YES | Move to env variables |
| Program IDs | 4 | YES | Verify for production |
| IP Addresses | 1 | YES | Already in config |
| Port Numbers | 2 | Medium | Already configurable |
| API Endpoints | 8 | Low | OK as hardcoded |
| Table Names | 4 | No | OK as hardcoded |
| Status Values | ~20 | No | Business logic, OK |

---

## ✅ ALREADY CONFIGURED (Good!)

These are already using environment variables:
- Database connection (DB_SERVER, DB_NAME, etc.)
- IMS credentials (IMS_ONE_USERNAME, IMS_ONE_PASSWORD)
- IMS base URL (mostly - one hardcoded instance found)
- Port numbers (PORT env variable)
- Debug settings (DEBUG env variable)

---

## 🔧 IMMEDIATE FIXES REQUIRED

### Priority 1: Add to Environment Files

```env
# Add these to both .env.development and .env.production

# Line GUIDs (verify these are correct for each environment!)
TRITON_PRIMARY_LINE_GUID=07564291-CBFE-4BBE-88D1-0548C88ACED4
TRITON_EXCESS_LINE_GUID=08798559-321C-4FC0-98ED-A61B92215F31

# Program IDs (may differ between environments)
PROGRAM_ID_RT_PRIMARY=11615
PROGRAM_ID_WL_PRIMARY=11613  
PROGRAM_ID_RT_EXCESS=11612
PROGRAM_ID_WL_EXCESS=11614

# Locations (verify for each environment)
IMS_QUOTING_LOCATION=C5C006BB-6437-42F3-95D4-C090ADD3B37D
IMS_ISSUING_LOCATION=C5C006BB-6437-42F3-95D4-C090ADD3B37D
IMS_COMPANY_LOCATION=DF35D4C7-C663-4974-A886-A1E18D3C9618
```

### Priority 2: Fix Code Files

1. **quote_service.py** - Replace hardcoded Line GUIDs
2. **auth_service.py** - Remove hardcoded IP address
3. **SQL procedures** - Document which values are environment-specific

### Priority 3: Validation Script

Create a script to validate all required environment variables are set before starting.

---

## 🎯 DEPLOYMENT CHECKLIST

Before deploying to production:

- [ ] Verify ALL Line GUIDs are correct for production
- [ ] Verify ALL Program IDs match production IMS setup
- [ ] Verify Location GUIDs are correct for production
- [ ] Remove hardcoded IP from auth_service.py
- [ ] Update quote_service.py to use config values
- [ ] Document all environment variables
- [ ] Test with production-like values in staging
- [ ] Create validation script for startup

---

## 🚨 RISK ASSESSMENT

### HIGH RISK Items:
1. **Wrong Line GUIDs** = Policies assigned to wrong program
2. **Wrong Program IDs** = Incorrect pricing/processing
3. **Wrong Location GUIDs** = Organizational routing errors

### MEDIUM RISK Items:
1. **Hardcoded IPs** = Can't switch environments easily
2. **Missing env variables** = Application won't start

### LOW RISK Items:
1. **API endpoint paths** = Unlikely to change
2. **Table names** = Database structure stable
3. **Status values** = Business logic, not config

---

## QUESTIONS FOR THE TEAM

1. Are the Line GUIDs the same in DEV and PROD?
2. Are the Program IDs (11612-11615) the same in DEV and PROD?
3. Are the Location GUIDs the same in DEV and PROD?
4. Should we have different IMS servers for DEV vs PROD?
5. Do we need different API keys for DEV vs PROD?

---

## NEXT STEPS

1. **IMMEDIATE**: Add missing environment variables to .env files
2. **URGENT**: Fix hardcoded values in Python files
3. **IMPORTANT**: Document all configuration requirements
4. **NICE TO HAVE**: Create configuration validation on startup