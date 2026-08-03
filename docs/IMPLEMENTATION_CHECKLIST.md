# Implementation Checklist - Job Card Readiness Engine

**Status:** Architecture Finalized ✅  
**Date:** 2026-08-03  
**Version:** 3.0

---

## Phase 1: Custom Fields ✅ COMPLETE

- [x] `custom_material_status` (Select) - Options updated
- [x] `custom_readiness_status` (Select) - Options updated
- [x] `custom_material_shortage_details` (Text)
- [x] `custom_dependency_last_updated` (Datetime)
- [x] `custom_blocked_by` (Data)

**Additional Fields (Already Exist):**
- [x] `custom_material_available_for_operation` (Check)
- [x] `custom_can_start_operation` (Check)
- [x] `custom_dependency_status` (Small Text)
- [x] `custom_start_status` (Select)
- [x] `custom_refresh_dependency_status` (Button)

---

## Phase 2: Readiness Engine Implementation

### File: `tekson_manufacturing/readiness/job_card_readiness.py`

**Class:** `JobCardReadinessEngine`

**Methods to Implement:**
- [ ] `__init__()` - Initialize material and dependency engines
- [ ] `refresh_work_order(work_order)` - Evaluate all JCs in WO
- [ ] `refresh_job_card(job_card)` - Evaluate single JC
- [ ] `refresh_downstream_job_cards(job_card)` - Evaluate downstream only
- [ ] `evaluate_material_status(job_card)` - Set material_status field
- [ ] `evaluate_readiness_status(job_card)` - Set readiness_status field
- [ ] `get_shortage_message(material_result)` - Format shortage details

**Logic:**
```python
def evaluate_material_status(self, jc):
    material_result = self.material_engine.evaluate(jc.work_order)
    
    if material_result.is_ready:
        jc.custom_material_status = "Material Available"
    elif material_result.has_partial_stock():
        jc.custom_material_status = "Material Short"
        jc.custom_blocked_by = self.get_shortage_message(material_result)
    else:
        jc.custom_material_status = "Waiting for Material"
        jc.custom_blocked_by = "Waiting for Material Transfer"

def evaluate_readiness_status(self, jc):
    if jc.status == "Completed":
        jc.custom_readiness_status = "Completed"
        return
    
    if jc.status == "Work In Progress":
        jc.custom_readiness_status = "In Progress"
        return
    
    deps_result = self.dependency_engine.evaluate(jc)
    
    if jc.custom_material_status == "Material Available":
        if deps_result.previous_complete:
            jc.custom_readiness_status = "Ready to Start"
            jc.custom_blocked_by = ""
        else:
            jc.custom_readiness_status = "Waiting for Previous Operation"
            jc.custom_blocked_by = f"Waiting for: {deps_result.previous_jc_name}"
    else:
        jc.custom_readiness_status = "Blocked"
```

---

## Phase 3: Hook Registration

### File: `tekson_manufacturing/hooks.py`

**Hooks to Add:**
```python
doc_events = {
    "Work Order": {
        "on_submit": "tekson_manufacturing.readiness.job_card_readiness.on_work_order_submit",
    },
    "Stock Entry": {
        "on_submit": "tekson_manufacturing.readiness.job_card_readiness.on_stock_entry_submit",
    },
    "Job Card": {
        "on_submit": "tekson_manufacturing.readiness.job_card_readiness.on_job_card_complete",
    },
}
```

**Helper Functions:**
```python
# In job_card_readiness.py

def on_work_order_submit(doc, method):
    """WO Submit = Production Release"""
    engine = JobCardReadinessEngine()
    engine.refresh_work_order(doc)

def on_stock_entry_submit(doc, method):
    """Material Transfer - Refresh only that WO"""
    if doc.purpose != "Material Transfer for Manufacture":
        return
    
    if not doc.work_order:
        return
    
    wo = frappe.get_doc('Work Order', doc.work_order)
    engine = JobCardReadinessEngine()
    engine.refresh_work_order(wo)

def on_job_card_complete(doc, method):
    """Operation Complete - Refresh downstream only"""
    if doc.status != "Completed":
        return
    
    engine = JobCardReadinessEngine()
    engine.refresh_downstream_job_cards(doc)
```

---

## Phase 4: Start Button Update (Optional)

### File: `tekson_manufacturing/public/js/job_card_start.js`

**Update Validation:**
```javascript
function start_job_with_validation(frm) {
    // Check cached readiness status (instant)
    if (frm.doc.custom_readiness_status !== 'Ready to Start') {
        frappe.throw(__('Cannot start: {0} - {1}', [
            frm.doc.custom_readiness_status,
            frm.doc.custom_blocked_by
        ]));
    }
    
    // Quick validation (protect against changes)
    if (frm.doc.status === 'Work In Progress') {
        frappe.throw(__('Job Card already in progress'));
    }
    
    // Start
    frappe.call({
        method: 'tekson_manufacturing.api.job_card_start.start_job_card',
        args: { job_card_name: frm.doc.name },
        freeze: true,
        freeze_message: __('Starting Job Card...'),
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.msgprint({
                    title: __('Success'),
                    message: __('Job Card started successfully'),
                    indicator: 'green'
                });
                frm.refresh();
            }
        }
    });
}
```

---

## Phase 5: Testing

### Test Scenarios

| ID | Scenario | Expected Result | Status |
|----|----------|-----------------|--------|
| TC-001 | WO Submit (no WIP stock) | `material_status` = "Waiting for Material", `readiness_status` = "Blocked" | ⏳ |
| TC-002 | WO Submit (WIP stock exists) | `material_status` = "Material Available", `readiness_status` = "Ready to Start" (if first op) | ⏳ |
| TC-003 | Material Transfer (sufficient) | `material_status` = "Material Available", `readiness_status` updates | ⏳ |
| TC-004 | Material Transfer (insufficient) | `material_status` = "Material Short", shortage details in `blocked_by` | ⏳ |
| TC-005 | Operation 1 Complete | Operation 2 `readiness_status` = "Ready to Start" (if material available) | ⏳ |
| TC-006 | Start Button (ready JC) | Starts successfully | ⏳ |
| TC-007 | Start Button (blocked JC) | Shows error with readiness_status and blocked_by | ⏳ |
| TC-008 | Material Transfer refreshes only that WO | Other WOs NOT refreshed | ⏳ |
| TC-009 | Operation Complete refreshes downstream only | Upstream JCs NOT refreshed | ⏳ |

---

## Phase 6: Department Dashboards

### Required Reports

**File:** `tekson_manufacturing/report/department_production_dashboard/`

**Columns:**
- Work Order
- Job Card
- Operation
- Department
- `custom_material_status`
- `custom_readiness_status`
- `custom_blocked_by`
- `custom_dependency_last_updated`

**Filters:**
- Department
- Readiness Status
- Material Status
- Date Range

---

## Success Criteria

### Functional
- [ ] WO Submit evaluates current WIP stock immediately
- [ ] Material Transfer refreshes only that WO
- [ ] Operation Complete refreshes downstream only
- [ ] Start button uses cached status (< 100ms)
- [ ] Status is accurate and human-readable

### Performance
- [ ] WO Submit < 2 seconds
- [ ] Material Transfer < 3 seconds
- [ ] Operation Complete < 1 second
- [ ] Start Button < 100ms

### User Experience
- [ ] Operators see clear status (Ready/Blocked/Waiting)
- [ ] Supervisors see shortage details
- [ ] Audit trail with timestamps

---

## Implementation Order

1. ✅ **Custom Fields** - COMPLETE
2. ⏳ **Readiness Engine** - Core logic
3. ⏳ **Hook Registration** - Event triggers
4. ⏳ **Start Button Update** - Optional enhancement
5. ⏳ **Testing** - All 9 scenarios
6. ⏳ **Dashboards** - Department views

---

## Next Step

**Implement Phase 2: Readiness Engine**

Shall I create the `JobCardReadinessEngine` class now? 🎯
