# Phase 1 Implementation Plan

**Version:** 1.0  
**Date:** 2026-07-31  
**Priority:** Critical  
**Estimated Duration:** 2-3 weeks

---

## Overview

Phase 1 focuses on fixing the critical issues identified during UAT and implementing the foundational Material Readiness Engine.

---

## Critical Issues to Fix

### Issue 1: Work Order Status Not Updating
**Affected WOs:**
- WO/260714/0034
- WO/260714/0051
- WO/260714/0063
- WO/260714/0001
- WO/260714/0025

**Problem:** All Job Cards completed but WO status remains "In Process"

**Root Cause:** `complete_work_order()` function not triggering correctly or missing completion conditions

**Fix Required:**
1. Review current `work_order.py` implementation
2. Ensure `evaluate_work_order_status()` triggers on:
   - Job Card submit
   - Job Card cancel
   - Stock Entry submit
   - Stock Entry cancel
3. Add comprehensive logging for debugging
4. Test with affected WO data

---

### Issue 2: Parent WO Starts Before Child Components Complete
**Example:** CORE Assembly started before child components completed

**Problem:** System checks individual Stock Entry instead of cumulative availability

**Fix Required:**
1. Implement cumulative material checking
2. Sum all Material Transfer Stock Entries for each item
3. Compare against required quantity
4. Distinguish between:
   - Raw materials (check transfers)
   - Manufactured components (check available stock)
   - Common components (check global stock)

---

### Issue 3: Material Validation Not Differentiating Types
**Problem:** All materials treated the same way

**Fix Required:**
1. Classify materials by type:
   - Purchased Raw Material
   - Purchased Component
   - Internal Manufactured Component
   - Common Manufactured Component
   - Sub Assembly
2. Apply appropriate validation logic per type
3. Configure warehouse mapping per type

---

## Deliverables

### 1. Material Readiness Engine
**File:** `tekson_manufacturing/readiness/material_engine.py`

**Functions:**
```python
def evaluate_material_readiness(work_order):
    """
    Check if all materials are available for production.
    Returns: (is_ready, missing_items_details)
    """
    
def get_cumulative_transferred_qty(item_code, warehouse, work_order=None):
    """
    Sum all Material Transfer Stock Entries for an item.
    """
    
def get_available_stock(item_code, warehouse):
    """
    Get actual stock balance from Stock Ledger.
    """
    
def classify_material_type(item_code, work_order):
    """
    Determine if item is Raw, Component, Sub-Assembly, or Common.
    """
```

**Priority:** HIGH  
**Estimated Time:** 3-4 days

---

### 2. Work Order Completion Engine
**File:** `tekson_manufacturing/readiness/workorder_engine.py`

**Functions:**
```python
def evaluate_work_order_status(work_order_name):
    """
    Evaluate and update Work Order status based on:
    - Job Card completion
    - Production quantity
    - Pending operations
    """
    
def check_all_operations_completed(work_order):
    """
    Verify all operations are marked as Completed.
    """
    
def check_production_qty_achieved(work_order):
    """
    Verify manufactured qty >= planned qty.
    """
```

**Hook Integration:**
```python
# In hooks.py
doc_events = {
    "Job Card": {
        "on_submit": "tekson_manufacturing.readiness.workorder_engine.on_job_card_submit",
        "on_cancel": "tekson_manufacturing.readiness.workorder_engine.on_job_card_cancel",
    },
    "Stock Entry": {
        "on_submit": "tekson_manufacturing.readiness.workorder_engine.on_stock_entry_submit",
        "on_cancel": "tekson_manufacturing.readiness.workorder_engine.on_stock_entry_cancel",
    }
}
```

**Priority:** HIGH  
**Estimated Time:** 2-3 days

---

### 3. Material Traceability Engine
**File:** `tekson_manufacturing/monitoring/traceability.py`

**Functions:**
```python
def get_material_shortage_reason(item_code, work_order):
    """
    Diagnose why material is not available.
    Returns detailed message for operator.
    """
    
def get_pending_transfers(item_code, work_order):
    """
    List all pending Material Transfer entries.
    """
    
def get_manufacturing_status(item_code):
    """
    Check if item is being manufactured (WO In Process).
    """
```

**Priority:** MEDIUM  
**Estimated Time:** 2 days

---

### 4. Warehouse Configuration
**File:** `tekson_manufacturing/settings/manufacturing_settings.py`

**Doctype:** Manufacturing Settings (Single)

**Fields:**
- Raw Material Warehouse (Link: Warehouse)
- Common Component Warehouse (Link: Warehouse)
- Default WIP Warehouse (Link: Warehouse)
- Finished Goods Warehouse (Link: Warehouse)
- Reject Warehouse (Link: Warehouse)
- Rework Warehouse (Link: Warehouse)

**Operation Override:**
- Add custom field to Operation: `default_wip_warehouse`

**Priority:** MEDIUM  
**Estimated Time:** 2 days

---

### 5. Enhanced Diagnostic Messages
**File:** `tekson_manufacturing/manufacturing/work_order.py`

**Improve feedback to operators:**

**Current:**
```
"Material not available"
```

**Improved:**
```
"Cannot start Operation 'Brazing':
- Copper Tube (15 kg required, 8 kg available)
  Reason: 7 kg pending transfer from Purchase Order PO-2026-001
- Brazing Rod (5 kg required, 0 kg available)
  Reason: Child WO/260714/0035 still In Process (60% complete)"
```

**Priority:** HIGH  
**Estimated Time:** 1-2 days

---

## Testing Plan

### Test Scenario 1: Work Order Completion
**Setup:**
- Create WO with 3 operations
- Complete all Job Cards

**Expected:**
- WO status automatically updates to "Completed"
- Stock Entry created and submitted
- Produced qty updated

**Test Data:** Use existing affected WOs from UAT

---

### Test Scenario 2: Cumulative Material Transfer
**Setup:**
- Create WO requiring 10 units of Item A
- Create 3 Stock Entries: 4 + 3 + 3 units

**Expected:**
- System recognizes total 10 units available
- Job Card allowed to start after 3rd transfer

**Test Data:** New test WO

---

### Test Scenario 3: Common Component
**Setup:**
- FG1 requires Fins (100 units)
- FG2 requires Fins (50 units)
- Fins WO produces 200 units
- Complete Fins WO

**Expected:**
- Both FG1 and FG2 can start (sufficient stock)
- No dependency on specific Fins WO

**Test Data:** New test WOs

---

### Test Scenario 4: Parent-Child Dependency
**Setup:**
- Parent WO requires Core Assembly
- Core Assembly WO not started

**Expected:**
- Parent WO Job Card shows "Awaiting Material"
- Diagnostic: "Core Assembly not available - Child WO/XXX not started"

**Test Data:** New test WOs

---

## Migration Plan

### Step 1: Backup Current State
```bash
bench --site [site-name] backup --with-files
```

### Step 2: Deploy New Code
```bash
cd apps/tekson_manufacturing
git pull origin develop
bench build
bench restart
```

### Step 3: Run Migration Script
```python
# Migrate existing WOs to new status evaluation
for wo in frappe.get_all("Work Order", 
                         filters={"status": "In Process"},
                         fields=["name"]):
    evaluate_work_order_status(wo.name)
```

### Step 4: Verify Affected WOs
Check status update for:
- WO/260714/0034
- WO/260714/0051
- WO/260714/0063
- WO/260714/0001
- WO/260714/0025

### Step 5: User Acceptance Testing
- Share test results with customer
- Conduct demo session
- Collect feedback

---

## Success Criteria

Phase 1 is complete when:

✅ All affected Work Orders show correct status  
✅ New Work Orders auto-complete when all JCs done  
✅ Material validation checks cumulative transfers  
✅ Operators see clear diagnostic messages  
✅ Common components work across multiple WOs  
✅ Parent WOs correctly wait for child availability  
✅ No regression in existing functionality  

---

## Risks & Mitigation

### Risk 1: Performance Impact
**Concern:** Cumulative stock checking may be slow

**Mitigation:**
- Add database indexes on Stock Ledger
- Cache material availability results
- Use background jobs for non-critical checks

---

### Risk 2: Backward Compatibility
**Concern:** Existing WOs may not work with new logic

**Mitigation:**
- Test thoroughly with UAT data
- Provide migration script
- Keep old logic as fallback (commented code)

---

### Risk 3: User Confusion
**Concern:** New diagnostic messages may confuse operators

**Mitigation:**
- Use simple, clear language
- Provide training documentation
- Include screenshots in user guide

---

## Timeline

| Week | Tasks |
|------|-------|
| Week 1 | - Material Readiness Engine<br>- Work Order Completion Engine |
| Week 2 | - Warehouse Configuration<br>- Material Traceability<br>- Diagnostic Messages |
| Week 3 | - Testing<br>- Bug fixes<br>- UAT preparation |

---

## Team Assignments

| Task | Assigned To | Status |
|------|-------------|--------|
| Material Readiness Engine | TBD | Pending |
| Work Order Completion Engine | TBD | Pending |
| Warehouse Configuration | TBD | Pending |
| Material Traceability | TBD | Pending |
| Testing | TBD | Pending |
| Documentation | TBD | Pending |

---

## Next Steps

1. **Review this plan** with development team
2. **Assign tasks** to team members
3. **Set up development environment**
4. **Create feature branches** for each deliverable
5. **Begin implementation**

---

*Document created: 2026-07-31*  
*Next update: After task assignments*
