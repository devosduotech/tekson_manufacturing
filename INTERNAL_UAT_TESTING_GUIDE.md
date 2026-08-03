# Internal UAT Testing Guide

**Purpose:** Step-by-step guide for conducting internal UAT on Local VM  
**Version:** 1.0  
**Date:** 2026-08-03  
**Tester:** [Your Name]  

---

## Pre-Testing Checklist

### ✅ Deployment Verification

Before starting UAT, ensure:

- [ ] Deployment script executed successfully
- [ ] All verification tests passed
- [ ] Bench restarted
- [ ] Browser can access ERPNext
- [ ] Test data available (Items, BOMs, Workstations)

### ✅ Test Data Requirements

**Minimum Required:**
- [ ] At least 1 Finished Good Item (e.g., R215)
- [ ] At least 2-3 Raw Material Items
- [ ] BOM for Finished Good (with 2-3 operations)
- [ ] Workstations for each operation
- [ ] Warehouses: Raw Materials, WIP, Finished Goods
- [ ] Opening stock for Raw Materials

---

## UAT Execution Steps

### Step 1: Access ERPNext

1. Open browser: `http://localhost:8000`
2. Login with Administrator or Manufacturing User
3. Navigate to: **Manufacturing → Work Order → List**

---

### Step 2: Create Test Work Order

**Test Case: TC-MFG-001 (Standard Production)**

**Steps:**
1. Click **Add Work Order**
2. Fill in:
   - **Production Item:** R215 (or your test item)
   - **Qty:** 10
   - **BOM:** Select default BOM
   - **Planned Start Date:** Today
   - **Company:** Teksons Industries Pvt Ltd
   - **WIP Warehouse:** Work In Progress - TIPL
   - **FG Warehouse:** Finished Goods - TIPL
3. Click **Save**
4. Click **Submit**

**Expected Results:**
- ✅ Work Order submitted successfully
- ✅ Job Cards auto-created (one per operation)
- ✅ All Job Cards show:
  - `custom_material_status` = "Waiting for Material"
  - `custom_readiness_status` = "Blocked"
  - `custom_can_start_operation` = Unchecked
  - `custom_blocked_by` = "Waiting for Material Transfer"

**Verification:**
```sql
-- Run in Query Report or Console
SELECT 
    name,
    operation,
    sequence_id,
    custom_material_status,
    custom_readiness_status,
    custom_can_start_operation,
    custom_blocked_by
FROM `tabJob Card`
WHERE work_order = '[WO_NUMBER]'
ORDER BY sequence_id;
```

**Screenshot:** Take screenshot of Job Card list

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________

---

### Step 3: Evaluate Readiness (No Stock)

**Test Case: TC-MFG-002 (Readiness Evaluation)**

**Steps:**
1. Open first Job Card (Sequence ID = 1)
2. Check custom fields
3. Open second Job Card
4. Check custom fields

**Expected Results:**
- ✅ All Job Cards show "Waiting for Material"
- ✅ All Job Cards blocked
- ✅ `custom_dependency_last_updated` has timestamp

**Verification:**
- Check each Job Card's custom fields
- Verify all show consistent status

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________

---

### Step 4: Create Material Transfer

**Test Case: TC-MFG-003 (Material Transfer Refresh)**

**Steps:**
1. Navigate to: **Stock → Stock Entry → Add Stock Entry**
2. Select:
   - **Purpose:** Material Transfer for Manufacture
   - **Work Order:** [Your WO Number]
   - **From BOM:** Checked
   - **Source Warehouse:** Raw Materials - TIPL
   - **Target Warehouse:** Work In Progress - TIPL
3. Items should auto-populate from BOM
4. Set quantities to match WO requirement
5. Click **Save**
6. Click **Submit**

**Expected Results:**
- ✅ Stock Entry submitted successfully
- ✅ Within 2-3 seconds, Job Cards refresh
- ✅ First Job Card shows:
  - `custom_material_status` = "Material Available"
  - `custom_readiness_status` = "Ready to Start"
  - `custom_can_start_operation` = Checked
  - `custom_blocked_by` = (empty)
- ✅ Subsequent Job Cards still blocked by previous operation

**Verification:**
- Refresh Job Card list
- Open first Job Card
- Verify fields updated automatically

**Performance:** Should complete in < 3 seconds

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________

---

### Step 5: Start First Operation

**Test Case: TC-MFG-004 (Start Button Validation)**

**Steps:**
1. Open first Job Card (should be "Ready to Start")
2. Click **Start** button
3. Enter:
   - **Actual Start Time:** Current time
   - **Operation Status:** Work In Progress
4. Click **Save**

**Expected Results:**
- ✅ Start button enabled (not disabled)
- ✅ Job Card status changes to "Work In Progress"
- ✅ Actual start time recorded
- ✅ No error messages

**Verification:**
- Check Job Card status
- Verify start time recorded

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________

---

### Step 6: Complete First Operation

**Test Case: TC-MFG-005 (Operation Complete → Downstream Refresh)**

**Steps:**
1. In first Job Card (already started)
2. Enter:
   - **Actual End Time:** Current time
   - **Completed Qty:** 10
   - **Operation Status:** Completed
3. Click **Save**
4. Click **Submit**

**Expected Results:**
- ✅ Job Card status = "Completed"
- ✅ Second Job Card automatically refreshes
- ✅ Second Job Card shows:
  - `custom_readiness_status` = "Ready to Start"
  - `custom_can_start_operation` = Checked
- ✅ Third Job Card (if exists) still blocked

**Verification:**
- Open second Job Card immediately after first completes
- Check readiness status
- Verify only next operation refreshed (not entire chain)

**Performance:** Should complete in < 1 second

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________

---

### Step 7: Start Second Operation

**Test Case: TC-MFG-006 (Sequential Operations)**

**Steps:**
1. Open second Job Card
2. Click **Start** button
3. Enter start time
4. Save

**Expected Results:**
- ✅ Start button enabled
- ✅ No dependency errors
- ✅ Operation starts successfully

**Verification:**
- Check Job Card status
- Verify no blocking messages

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________

---

### Step 8: Complete All Operations

**Test Case: TC-MFG-007 (End-to-End Flow)**

**Steps:**
1. Complete second Job Card
2. Complete third Job Card (if exists)
3. Continue until all operations complete

**Expected Results:**
- ✅ Each operation completes successfully
- ✅ Next operation becomes ready
- ✅ Final operation completion triggers WO completion readiness

**Verification:**
- All Job Cards show "Completed"
- Work Order status ready for "Completed"

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________

---

### Step 9: Create Stock Entry (Manufacture)

**Test Case: TC-MFG-008 (FG Stock Entry)**

**Steps:**
1. Navigate to Work Order
2. Click **Create → Stock Entry (Manufacture)**
3. Verify:
   - Items auto-populated
   - Qty matches completed qty
   - Source: WIP Warehouse
   - Target: Finished Goods Warehouse
4. Click **Save**
5. Click **Submit**

**Expected Results:**
- ✅ Stock Entry created
- ✅ FG stock increased
- ✅ Work Order status = "Completed"

**Verification:**
- Check Stock Ledger
- Verify FG warehouse has stock
- Check WO status

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________

---

### Step 10: Test Partial Production

**Test Case: TC-MFG-009 (Partial Production)**

**Steps:**
1. Create new Work Order for 100 qty
2. Submit (creates Job Cards)
3. Transfer materials for 100 qty
4. Complete first Job Card for only 40 qty
5. Create partial Stock Entry (Manufacture) for 40 qty

**Expected Results:**
- ✅ Partial completion allowed
- ✅ Partial FG stock created (40 qty)
- ✅ Remaining 60 qty still in progress
- ✅ Readiness correctly tracks partial qty

**Verification:**
- Check FG stock (should be 40)
- Check WO status (should be "Work In Progress")
- Check remaining Job Cards

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________

---

### Step 11: Test Dependency Blocking

**Test Case: TC-MFG-010 (Dependency Validation)**

**Steps:**
1. Create WO with 3 operations
2. Submit (all JCs created)
3. Transfer materials
4. Try to start Operation 2 (skip Operation 1)

**Expected Results:**
- ✅ Operation 2 cannot start
- ✅ Error message: "Cannot start - Waiting for Previous Operation"
- ✅ Start button disabled OR validation error

**Verification:**
- Attempt to start Op 2
- Verify blocking message
- Check `custom_blocked_by` field

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________

---

### Step 12: Performance Test

**Test Case: TC-MFG-011 (Large Work Order Performance)**

**Steps:**
1. Create Work Order with 40+ operations (or use existing large WO)
2. Start timer
3. Submit Work Order
4. Stop timer
5. Record time

**Expected Results:**
- ✅ WO Submit completes in < 5 seconds
- ✅ All Job Cards evaluated
- ✅ No timeout errors

**Performance Metrics:**
- WO Submit (40 JCs): Target < 2s, Acceptable < 5s
- Material Transfer: Target < 3s, Acceptable < 10s
- Job Card Complete: Target < 1s, Acceptable < 2s

**Actual Times:**
- WO Submit: _____ seconds
- Material Transfer: _____ seconds
- Job Card Complete: _____ seconds

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________

---

### Step 13: Test Cancel & Amend

**Test Case: TC-MFG-012 (Cancel & Amend Workflow)**

**Steps:**
1. Create and submit Work Order
2. Cancel Work Order
3. Amend Work Order
4. Re-submit Work Order

**Expected Results:**
- ✅ WO cancellation successful
- ✅ Job Cards cancelled/deleted
- ✅ Amend creates new Job Cards
- ✅ Re-submit evaluates readiness again

**Verification:**
- Check Job Card status after cancel
- Check new Job Cards after amend
- Verify readiness re-evaluated

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________

---

### Step 14: Test Multi-Level BOM

**Test Case: TC-MFG-013 (Multi-Level BOM)**

**Prerequisites:** Item with sub-assembly BOM

**Steps:**
1. Create WO for Finished Good (has sub-assembly)
2. Submit
3. Verify sub-assembly WO created
4. Complete sub-assembly WO
5. Complete parent WO

**Expected Results:**
- ✅ Sub-assembly WO auto-created
- ✅ Readiness evaluated for sub-assembly
- ✅ Parent WO waits for sub-assembly
- ✅ End-to-end flow works

**Verification:**
- Check both WOs
- Verify readiness at each level
- Track material flow

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** _______________

---

## Issue Tracking Template

### Issue Report

**Issue ID:** UAT-001  
**Date:** _______________  
**Reported By:** _______________  
**Severity:** ⬜ Critical / ⬜ High / ⬜ Medium / ⬜ Low  

**Test Case:** TC-_____  

**Steps to Reproduce:**
1. _______________
2. _______________
3. _______________

**Expected Result:**
_______________

**Actual Result:**
_______________

**Screenshot:** [Attach if applicable]

**Workaround:**
_______________

**Technical Details:**
- Work Order: _______________
- Job Cards: _______________
- Timestamp: _______________
- Error Message: _______________

**Status:** ⬜ Open / ⬜ In Progress / ⬜ Resolved / ⬜ Closed

---

## Daily UAT Summary

### Day 1 Summary

**Date:** _______________  
**Tester:** _______________  

**Test Cases Executed:**
- TC-MFG-001: ⬜ Pass / ⬜ Fail
- TC-MFG-002: ⬜ Pass / ⬜ Fail
- TC-MFG-003: ⬜ Pass / ⬜ Fail
- TC-MFG-004: ⬜ Pass / ⬜ Fail
- TC-MFG-005: ⬜ Pass / ⬜ Fail

**Issues Found:** _____  
**Critical:** _____  
**High:** _____  
**Medium:** _____  
**Low:** _____  

**Overall Status:** ⬜ On Track / ⬜ At Risk / ⬜ Blocked

**Comments:**
_______________

---

## UAT Completion Criteria

### Go/No-Go Decision

**Pass Criteria:**
- [ ] All Critical test cases pass (TC-MFG-001 to 008)
- [ ] ≥ 80% of all test cases pass
- [ ] Zero Critical severity bugs
- [ ] ≤ 2 High severity bugs
- [ ] Performance targets met (≥ 80%)
- [ ] User acceptance ≥ 80%

**Final Results:**
- Test Cases Passed: _____ / _____ (_____%)
- Critical Bugs: _____
- High Bugs: _____
- Performance: _____% targets met
- User Acceptance: _____%

**Decision:** ⬜ GO / ⬜ NO-GO

**Signed By:**
- Project Manager: _______________ Date: _______
- Technical Lead: _______________ Date: _______
- Business Owner: _______________ Date: _______

---

## Quick Reference Commands

### Console Access
```bash
bench --site teksons.dev console
```

### Verify Custom Fields
```python
from tekson_manufacturing.mes.dataclasses import MaterialResult
print("✅ Imports work")
```

### Manually Refresh Job Card
```python
from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
engine = JobCardReadinessEngine()
engine.refresh_job_card('JC-0001')
```

### Check Readiness Status
```python
jc = frappe.get_doc('Job Card', 'JC-0001')
print(f"Material: {jc.custom_material_status}")
print(f"Readiness: {jc.custom_readiness_status}")
print(f"Can Start: {jc.custom_can_start_operation}")
```

### View Error Logs
```bash
bench --site teksons.dev view-error-log
```

---

## Support Contacts

| Role | Name | Contact |
|------|------|---------|
| Technical Lead | [Name] | [Email/Phone] |
| MES Developer | [Name] | [Email/Phone] |
| Project Manager | [Name] | [Email/Phone] |

---

**Happy Testing!** 🎯
