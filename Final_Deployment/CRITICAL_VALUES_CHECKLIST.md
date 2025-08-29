# CRITICAL VALUES VERIFICATION CHECKLIST
## Must Verify Before Production Deployment

---

## 🔴 STOP! VERIFY THESE VALUES WITH YOUR TEAM

### 1. LINE GUIDs - Do These Change Between Environments?

**Current Values Found in Code:**
- Primary Line: `07564291-CBFE-4BBE-88D1-0548C88ACED4`
- Excess Line: `08798559-321C-4FC0-98ED-A61B92215F31`

**ASK YOUR IMS TEAM:**
- [ ] Are these GUIDs the same in DEV and PROD?
- [ ] If different, what are the PROD values?
- [ ] What happens if we use the wrong GUID?

**RISK:** Wrong GUID = Policies go to wrong program = MAJOR ISSUE

---

### 2. PROGRAM IDs - Hardcoded in SQL Procedures

**Current Mapping in SQL:**
```
RT + Primary Line (07564291) = Program 11615
WL + Primary Line (07564291) = Program 11613
RT + Excess Line (08798559) = Program 11612
WL + Excess Line (08798559) = Program 11614
```

**ASK YOUR IMS TEAM:**
- [ ] Are these Program IDs correct for PRODUCTION?
- [ ] Do these IDs exist in the production IMS system?
- [ ] What happens if we use the wrong Program ID?

**FILES CONTAINING THESE:**
- `/sql/Procs_8_25_25/spProcessTritonPayload_WS.sql`
- `/sql/Procs_8_25_25/ProcessFlatEndorsement.sql`
- `/sql/Procs_8_25_25/ProcessFlatCancellation.sql`

**RISK:** Wrong Program ID = Wrong pricing/coverage = FINANCIAL IMPACT

---

### 3. LOCATION GUIDs - Organization Structure

**Current Values:**
- Quoting Location: `C5C006BB-6437-42F3-95D4-C090ADD3B37D`
- Issuing Location: `C5C006BB-6437-42F3-95D4-C090ADD3B37D`
- Company Location: `DF35D4C7-C663-4974-A886-A1E18D3C9618`

**ASK YOUR IMS TEAM:**
- [ ] Are these the correct PRODUCTION location GUIDs?
- [ ] Do these need to change for different environments?
- [ ] What organizational units do these represent?

**RISK:** Wrong Location = Policies routed to wrong department

---

### 4. IMS SERVER CONFIGURATION

**Current Value:**
- Base URL: `http://10.64.32.234/ims_one`

**ASK YOUR IT TEAM:**
- [ ] Is this the PRODUCTION IMS server?
- [ ] Is there a separate DEV/TEST server?
- [ ] Should we use HTTPS in production?
- [ ] Are there different endpoints for dev vs prod?

**RISK:** Wrong server = Testing against production data

---

### 5. DATABASE NAMES

**Expected Pattern:**
- Development: `IMS_TEST` or `IMS_DEV`
- Production: `IMS_PRODUCTION` or similar

**ASK YOUR DBA:**
- [ ] What is the exact PRODUCTION database name?
- [ ] What is the TEST database name?
- [ ] Are the table structures identical?
- [ ] Do both have the Triton tables?

**RISK:** Wrong database = Data loss or corruption

---

## 📋 QUICK VALIDATION SCRIPT

Run this SQL to verify Program IDs exist:

```sql
-- Run on PRODUCTION database
SELECT ProgramID, ProgramName 
FROM tblPrograms 
WHERE ProgramID IN (11612, 11613, 11614, 11615);

-- Should return 4 rows
```

Run this SQL to verify GUIDs exist:

```sql
-- Check Line GUIDs
SELECT CompanyLineGuid, LineName 
FROM tblCompanyLines
WHERE CompanyLineGuid IN (
    '07564291-CBFE-4BBE-88D1-0548C88ACED4',
    '08798559-321C-4FC0-98ED-A61B92215F31'
);

-- Check Location GUIDs  
SELECT LocationGuid, LocationName
FROM tblLocations
WHERE LocationGuid IN (
    'C5C006BB-6437-42F3-95D4-C090ADD3B37D',
    'DF35D4C7-C663-4974-A886-A1E18D3C9618'
);
```

---

## ⚠️ ENVIRONMENT-SPECIFIC VALUES SUMMARY

| Value Type | Dev Environment | Prod Environment | Verified? |
|------------|----------------|------------------|-----------|
| Database Name | IMS_TEST | IMS_PRODUCTION | [ ] |
| IMS Server URL | http://10.64.32.234/ims_test | http://10.64.32.234/ims_one | [ ] |
| Primary Line GUID | 07564291-CBFE-4BBE-88D1-0548C88ACED4 | ??? | [ ] |
| Excess Line GUID | 08798559-321C-4FC0-98ED-A61B92215F31 | ??? | [ ] |
| Program ID (RT+Primary) | 11615 | ??? | [ ] |
| Program ID (WL+Primary) | 11613 | ??? | [ ] |
| Program ID (RT+Excess) | 11612 | ??? | [ ] |
| Program ID (WL+Excess) | 11614 | ??? | [ ] |
| Quoting Location | C5C006BB-6437-42F3-95D4-C090ADD3B37D | ??? | [ ] |
| Company Location | DF35D4C7-C663-4974-A886-A1E18D3C9618 | ??? | [ ] |
| API Port | 8000 | 8001 | [ ] |
| Debug Mode | True | False | [ ] |

---

## 🚨 DO NOT DEPLOY UNTIL:

1. [ ] ALL GUIDs verified with IMS team
2. [ ] ALL Program IDs verified in production database
3. [ ] Database names confirmed with DBA
4. [ ] Server URLs confirmed with IT
5. [ ] Test transaction run in staging environment
6. [ ] Rollback plan reviewed and ready

---

## CONTACTS FOR VERIFICATION

Add your team contacts here:
- IMS Team Lead: ____________
- Database Admin: ____________
- IT/Infrastructure: ____________
- Business Analyst (for Program IDs): ____________