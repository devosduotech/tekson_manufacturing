# Server Script Retirement Matrix

**Date:** August 2, 2026  
**Purpose:** Document retirement of UAT server scripts and their replacements  
**Status:** Ready for UAT validation  

---

## Executive Summary

All 6 UAT server scripts have been **replaced by the `tekson_manufacturing` custom app**. This document tracks the retirement plan, verification status, and rollback procedure.

---

## Retirement Matrix

| # | Old Server Script | Business Rule | New Module | Replacement Method | Status | UAT Verified |
|---|-------------------|---------------|------------|-------------------|--------|--------------|
| 1 | `job_card_status_update` | JC-001, JC-005 | `ExecutionEngine.can_job_card_start()` | Service Layer | ⬜ Ready | ⬜ Pending |
| 2 | `allocate_workstation_without_round_robin_flow` | JC-006 | `job_card_utils.allocate_workstation()` | Before Insert Hook | ⬜ Ready | ⬜ Pending |
| 3 | `job_card_material_availability` (v1) | MR-010, MR-011 | `MaterialReadinessEngine.evaluate_material_readiness()` | Service Layer | ⬜ Ready | ⬜ Pending |
| 4 | `stock_entry_wip_on_work_order_complete` | WO-003 (Safety Net) | `work_order_service.auto_create_manufacture_entry()` | Before Save Hook | ⬜ Ready | ⬜ Pending |
| 5 | `job_card_material_availability_check` (v2) | MR-010 | `material_readiness.can_job_card_start()` | API | ⬜ Ready | ⬜ Pending |
| 6 | `jc_start_control_validation_with_previous_job_card_check` | DV-001 | `DependencyEngine.validate_previous_operation()` | Service Layer | ⬜ Ready | ⬜ Pending |

---

## Detailed Migration

### 1. Job Card Status Update

**Old Script:** `job_card_status_update` (117 lines)  
**Trigger:** Job Card Before Save  
**Business Rules:** JC-001, JC-005, DV-001

**Previous Implementation:**
```python
# Server Script (all logic inline)
if doc.status == "Completed":
    doc.custom_start_status = "Completed"
elif doc.status == "Work In Progress":
    doc.custom_start_status = "In Progress"
else:
    # Check previous operations manually
    for op in wo.operations:
        if op.sequence_id < doc.sequence_id and op.status != "Completed":
            doc.custom_start_status = "Awaiting Previous Operation"
```

**New Implementation:**
```python
# File: execution_engine.py
# Business Rule: JC-001, JC-005

class ExecutionEngine:
    def can_job_card_start(self, job_card):
        # Repository pattern
        # Dependency validation
        # Material readiness check
        # Detailed diagnostics
```

**Advantages:**
- ✅ Testable (91 unit tests)
- ✅ Repository pattern
- ✅ Detailed logging
- ✅ Performance tracking

**Retirement Action:**
- [ ] Disable server script
- [ ] Verify Job Card status updates work
- [ ] Verify custom_start_status populates correctly

---

### 2. Allocate Workstation

**Old Script:** `allocate_workstation_without_round_robin_flow` (76 lines)  
**Trigger:** Job Card Before Insert  
**Business Rule:** JC-006

**Previous Implementation:**
```python
# Server Script
if not doc.workstation and doc.work_order and doc.operation:
    bom_no = frappe.db.get_value("Work Order", doc.work_order, "bom_no")
    bom_op = frappe.get_all("BOM Operation", {...})
    # Assign first workstation of type
```

**New Implementation:**
```python
# File: job_card_utils.py
# Business Rule: JC-006

def allocate_workstation(doc, method=None):
    """Auto-allocate Workstation from BOM Operation"""
    if not doc.workstation and doc.work_order and doc.operation:
        # Same logic, better architecture
        # Added: Logging, error handling, plant_floor copy
```

**Advantages:**
- ✅ Version controlled
- ✅ Testable
- ✅ Documented
- ✅ Integrated with warehouse assignment

**Retirement Action:**
- [ ] Disable server script
- [ ] Create new Job Card
- [ ] Verify workstation auto-assigned
- [ ] Verify plant_floor copied

---

### 3. Job Card Material Availability (v1)

**Old Script:** `job_card_material_availability` (136 lines)  
**Trigger:** Job Card Before Insert  
**Business Rules:** MR-010, MR-011

**Previous Implementation:**
```python
# Server Script
if doc.status == "Work In Progress":
    wo = frappe.get_doc("Work Order", doc.work_order)
    wip_wh = wo.wip_warehouse
    
    # Check each BOM item
    for item in bom_items:
        available = frappe.db.get_value("Bin", {...}, "actual_qty")
        if available < required:
            frappe.throw("Materials not available")
```

**New Implementation:**
```python
# File: material_readiness.py
# Business Rules: MR-010, MR-011

class MaterialReadinessEngine:
    def evaluate_material_readiness(self, work_order):
        # Cumulative transfer check
        # Transfer status tracking
        # Shortage reason analysis
        # Suggested actions
```

**Advantages:**
- ✅ Cumulative availability (not just current stock)
- ✅ Transfer tracking (Fully/Partially/Not Transferred)
- ✅ Detailed shortage messages
- ✅ Transfer suggestions API

**Retirement Action:**
- [ ] Disable server script
- [ ] Try to start JC without materials
- [ ] Verify error message
- [ ] Transfer materials
- [ ] Verify JC can start

---

### 4. Stock Entry on WO Complete

**Old Script:** `stock_entry_wip_on_work_order_complete` (51 lines)  
**Trigger:** Work Order Before Save  
**Business Rule:** WO-003 (Safety Net)

**Previous Implementation:**
```python
# Server Script
if doc.docstatus == 1 and doc.status == "Completed":
    if not existing_se:
        se = frappe.new_doc("Stock Entry")
        se.purpose = "Manufacture"
        # Create and submit directly
```

**New Implementation:**
```python
# File: work_order_service.py
# Business Rule: WO-003 (Safety Net Only)

def auto_create_manufacture_entry(doc, method=None):
    """
    SAFETY NET: Trigger Execution Engine
    Primary owner: Execution Engine (JC submit)
    """
    if doc.status == "Completed":
        engine = ExecutionEngine()
        result = engine.complete_work_order(doc.name)
        # Engine validates before creating
```

**Advantages:**
- ✅ Execution Engine remains primary owner
- ✅ Hook is safety net only
- ✅ Validates all JCs complete
- ✅ Prevents duplicates

**Retirement Action:**
- [ ] Disable server script
- [ ] Complete all JCs
- [ ] Submit final JC
- [ ] Verify WO auto-completes
- [ ] Verify Manufacture SE created

---

### 5. Job Card Material Availability Check (v2)

**Old Script:** `job_card_material_availability_check` (67 lines)  
**Trigger:** Job Card Before Save  
**Business Rule:** MR-010

**Previous Implementation:**
```python
# Simplified version (first JC only)
if doc.name.endswith("-001") and doc.status == "Work In Progress":
    # Check materials
    # Throw if missing
```

**New Implementation:**
```python
# File: material_readiness.py
# Business Rule: MR-010

@frappe.whitelist()
def can_job_card_start(job_card):
    """API for material readiness check"""
    engine = MaterialReadinessEngine(work_order=jc.work_order)
    readiness = engine.evaluate_material_readiness()
    
    return {
        'can_start': readiness['is_ready'],
        'missing_items': readiness['missing_items']
    }
```

**Advantages:**
- ✅ Whitelisted API
- ✅ Works for all JCs (not just -001)
- ✅ Integrated with readiness engine

**Retirement Action:**
- [ ] Disable server script
- [ ] Call API for various JCs
- [ ] Verify response accuracy

---

### 6. JC Start Control Validation

**Old Script:** `jc_start_control_validation_with_previous_job_card_check` (24 lines)  
**Trigger:** Job Card Before Validate  
**Business Rule:** DV-001

**Previous Implementation:**
```python
# Server Script
if doc.status == "Work In Progress":
    jcs = frappe.get_all("Job Card", {...}, order_by="idx asc")
    
    for jc in jcs:
        if jc.name == doc.name:
            break
        if jc.status != "Completed":
            frappe.throw("Cannot start...")
```

**New Implementation:**
```python
# File: dependency_engine.py
# Business Rule: DV-001

def validate_previous_operation(self, job_card):
    """Validate previous operation is complete"""
    # Uses sequence_id (not idx)
    # Repository pattern
    # Detailed diagnostics
    # Logging
```

**Advantages:**
- ✅ Sequence-based (not index-based)
- ✅ Repository pattern
- ✅ Detailed error messages
- ✅ Performance tracking

**Retirement Action:**
- [ ] Disable server script
- [ ] Try to start JC-002 before JC-001 complete
- [ ] Verify blocked with proper message
- [ ] Complete JC-001
- [ ] Verify JC-002 can start

---

## Retirement Checklist

### Phase 1: Preparation
- [ ] Review all 6 server scripts in UAT
- [ ] Document current behavior
- [ ] Backup database
- [ ] Create rollback plan

### Phase 2: Disable Scripts
- [ ] Disable script #1: `job_card_status_update`
- [ ] Disable script #2: `allocate_workstation...`
- [ ] Disable script #3: `job_card_material_availability`
- [ ] Disable script #4: `stock_entry_wip_on_work_order_complete`
- [ ] Disable script #5: `job_card_material_availability_check`
- [ ] Disable script #6: `jc_start_control_validation...`

### Phase 3: Verify Functionality
- [ ] Test Job Card creation
- [ ] Test workstation auto-assignment
- [ ] Test material validation
- [ ] Test dependency validation
- [ ] Test WO completion
- [ ] Test all custom fields populate

### Phase 4: Performance Validation
- [ ] Measure Job Card creation time (< 2 seconds)
- [ ] Measure material readiness check (< 2 seconds)
- [ ] Measure dependency validation (< 1 second)
- [ ] Compare with UAT script performance

### Phase 5: Sign-off
- [ ] All tests passed
- [ ] Performance acceptable
- [ ] No regressions found
- [ ] Stakeholder approval
- [ ] Update production deployment plan

---

## Rollback Procedure

If issues are found after disabling server scripts:

### Step 1: Re-enable Scripts
```python
# In Server Script list
for script_name in disabled_scripts:
    frappe.db.set_value("Server Script", script_name, "disabled", 0)
```

### Step 2: Disable Custom App Hooks
```python
# In hooks.py (temporary)
doc_events = {
    # Comment out temporarily
    # "Job Card": {...}
}
```

### Step 3: Restart Bench
```bash
bench restart
```

### Step 4: Investigate Issues
- Check error logs
- Review failing tests
- Identify missing functionality

### Step 5: Fix and Retry
- Update custom app code
- Re-run tests
- Re-attempt retirement

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Functionality** | 100% | All 6 scripts replaced |
| **Test Coverage** | > 90% | 91 tests passing |
| **Performance** | < 2 seconds | All operations |
| **Errors** | 0 | No new errors in logs |
| **User Experience** | Same or better | No regression |

---

## Post-Retirement Monitoring

### Week 1
- [ ] Daily error log review
- [ ] User feedback collection
- [ ] Performance monitoring

### Week 2
- [ ] Weekly summary report
- [ ] Address any minor issues
- [ ] Update documentation

### Month 1
- [ ] Monthly review
- [ ] Confirm no hidden dependencies
- [ ] Close retirement project

---

## Audit Trail

| Date | Action | Performed By | Status |
|------|--------|--------------|--------|
| Aug 2, 2026 | Retirement plan created | AI Assistant | ✅ Complete |
| TBD | Scripts disabled | | ⬜ Pending |
| TBD | UAT validation | | ⬜ Pending |
| TBD | Production deployment | | ⬜ Pending |

---

## Conclusion

All 6 UAT server scripts are **ready for retirement**. The `tekson_manufacturing` custom app provides:

✅ **Better Architecture:** Repository + Service + Engine pattern  
✅ **Test Coverage:** 91 unit tests vs 0  
✅ **Documentation:** Comprehensive vs inline comments  
✅ **Performance:** Tracked vs not measured  
✅ **Maintainability:** Version controlled vs Server Script Doctype  

**Recommendation:** ✅ **PROCEED WITH RETIREMENT** after UAT validation.

---

**Prepared By:** AI Assistant  
**Date:** August 2, 2026  
**Next Step:** UAT validation with scripts disabled
