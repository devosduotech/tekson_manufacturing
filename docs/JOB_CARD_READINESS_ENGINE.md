# Job Card Readiness Engine

**Document Type:** Technical Specification  
**Date:** 2026-08-03  
**Version:** 1.0  
**Status:** Ready for Implementation  
**Related:** JC-003A, JC-004, WH-009

---

## Overview

The **Job Card Readiness Engine** determines whether each Job Card is executable based on all relevant conditions. 

**WO Submit = Production Release** (not just planning). The engine evaluates **current WIP stock immediately** upon WO submission.

---

## Architecture

### Core Principle

**Work Order Submission = Production Release**  
**Material Transfer = Additional Stock Commitment**

```
┌─────────────────────────────────────────────────────────────┐
│              WO SUBMIT (PRODUCTION RELEASE)                 │
│                                                             │
│  Planner submits WO                                         │
│        ↓                                                    │
│  Job Cards created                                          │
│        ↓                                                    │
│  Readiness Engine evaluates CURRENT WIP stock               │
│        ↓                                                    │
│  If stock exists:                                           │
│    custom_material_status = "Material Available"            │
│    custom_readiness_status = "Ready to Start" (if deps met) │
│  If no stock:                                               │
│    custom_material_status = "Waiting for Material"          │
│    custom_readiness_status = "Blocked"                      │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│          MATERIAL TRANSFER (ADDITIONAL STOCK)               │
│                                                             │
│  Stores transfers material                                  │
│        ↓                                                    │
│  WIP stock updated                                          │
│        ↓                                                    │
│  Readiness Engine refreshes that WO's JCs only              │
│        ↓                                                    │
│  Update status based on new stock                           │
└─────────────────────────────────────────────────────────────┘
```

### Material Status vs Readiness Status

**Material Status** (What's in WIP):
- `Waiting for Material` - No stock in WIP yet
- `Material Available` - Sufficient stock exists
- `Material Short` - Insufficient stock

**Readiness Status** (Can operator start?):
- `Ready to Start` - ALL conditions met
- `Waiting for Previous Operation` - Material ready, waiting on prior op
- `Blocked` - Material shortage or other issue
- `In Progress` - Currently running
- `Completed` - Already finished

**Readiness Calculation:**
```python
custom_readiness_status = 
  if material_status == "Material Available":
    if previous_operation_complete:
      "Ready to Start"
    else:
      "Waiting for Previous Operation"
  else if material_status == "Waiting for Material":
    "Waiting for Material"
  else:
    "Blocked"
```

---

## Readiness Conditions

### `custom_can_start_operation`

Calculated as:

```python
custom_can_start_operation = (
    custom_material_available == 1
    AND
    previous_operation_complete == True
    AND
    work_order_status == "Submitted"
    AND
    job_card_status != "Completed"
    AND
    workstation_available == True (optional)
)
```

### `custom_material_available`

Evaluated based on:

```python
custom_material_available = (
    WIP_stock_qty >= required_qty
    AND
    work_order.wip_warehouse is set
    AND
    material_transferred == True
)
```

---

## Event Triggers

### Trigger 1: Work Order Submit

**When:** Planner submits Work Order (Production Release)

**Action:**
```python
def on_work_order_submit(wo):
    # Create Job Cards
    create_job_cards(wo)
    
    # Run Readiness Engine immediately
    from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
    engine = JobCardReadinessEngine()
    engine.refresh_work_order(wo)
```

**Scope:** All Job Cards in WO

**Material Check:** ✅ **Yes** (evaluate CURRENT WIP stock)

**Rationale:** Material may already be in WIP (transferred earlier or excess from previous WO). Immediate evaluation provides accurate status from moment of release.

---

### Trigger 2: Material Transfer for Manufacture

**When:** Stores submits Material Transfer Stock Entry

**Action:**
```python
def on_material_transfer_submit(stock_entry):
    if stock_entry.purpose != "Material Transfer for Manufacture":
        return
    
    # Refresh ONLY this WO's Job Cards (optimization)
    wo = frappe.get_doc('Work Order', stock_entry.work_order)
    
    from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
    engine = JobCardReadinessEngine()
    engine.refresh_work_order(wo)
```

**Scope:** All Job Cards in **that WO only** (via `SE.work_order` link)

**Material Check:** ✅ Yes (WIP stock updated)

**Optimization:** Don't refresh all WOs using same warehouse - only the WO linked to the Stock Entry.

**Readiness Engine Logic:**
```python
def refresh_work_order(self, wo):
    for jc in wo.job_cards:
        # Check material
        material_result = self.check_material_readiness(jc)
        jc.custom_material_available = 1 if material_result.is_ready else 0
        
        # Check dependencies
        dependency_result = self.check_dependencies(jc)
        
        # Calculate can_start
        jc.custom_can_start_operation = (
            jc.custom_material_available
            and dependency_result.previous_complete
            and wo.status == "Submitted"
            and jc.status != "Completed"
        )
        
        # Update status details
        if jc.custom_can_start_operation:
            jc.custom_material_status_details = "Ready to Start"
            jc.custom_blocked_by = ""
        else:
            if not jc.custom_material_available:
                jc.custom_blocked_by = "Material Not Available"
            elif not dependency_result.previous_complete:
                jc.custom_blocked_by = f"Waiting for: {dependency_result.previous_jc}"
        
        jc.custom_dependency_last_updated = now()
        jc.save()
```

---

### Trigger 3: Operation Complete

**When:** Job Card is submitted (completed)

**Action:**
```python
def on_job_card_complete(jc):
    # Find downstream Job Cards
    downstream_jcs = get_downstream_job_cards(jc)
    
    # Refresh only downstream
    for downstream_jc in downstream_jcs:
        refresh_job_card_readiness(downstream_jc)
```

**Scope:** Downstream Job Cards only (sequence_id > current)

**Material Check:** Optional (only if strict validation enabled)

---

### Trigger 4: Material Return

**When:** Material Return Stock Entry is submitted

**Action:** Same as Material Transfer (Trigger 2)

**Scope:** All Job Cards in WO

---

### Trigger 5: Stock Reconciliation (WIP)

**When:** Stock Reconciliation affects WIP warehouse (optional)

**Action:** Same as Material Transfer (Trigger 2)

**Scope:** Affected Job Cards only (based on item code)

---

### Trigger 6: Manual Refresh

**When:** User clicks "Refresh Status" button

**Action:** Same as Material Transfer (Trigger 2)

**Scope:** Selected Job Cards

---

## Implementation

### File Structure

```
tekson_manufacturing/
├── readiness/
│   ├── job_card_readiness.py       # Main engine
│   └── material_readiness.py       # Existing material check
├── utils/
│   └── job_card_utils.py           # Helper functions
└── hooks.py                        # Event registration
```

### Job Card Readiness Engine

```python
# readiness/job_card_readiness.py

import frappe
from frappe.utils import now
from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
from tekson_manufacturing.validation.dependency_engine import DependencyEngine

class JobCardReadinessEngine:
    """
    Job Card Readiness Engine
    
    Evaluates whether Job Cards are ready to start based on:
    - Material availability
    - Operation dependencies
    - Work Order status
    
    Triggered by:
    - Work Order submit
    - Material Transfer submit
    - Operation complete
    - Manual refresh
    """
    
    def __init__(self):
        self.material_engine = MaterialReadinessEngine()
        self.dependency_engine = DependencyEngine()
    
    def refresh_work_order(self, work_order):
        """
        Refresh readiness for all Job Cards in Work Order
        
        Args:
            work_order: Work Order document
        """
        job_cards = frappe.get_all('Job Card',
            filters={'work_order': work_order.name, 'docstatus': ['!=', 2]},
            order_by='sequence_id')
        
        for jc_data in job_cards:
            jc = frappe.get_doc('Job Card', jc_data.name)
            self.refresh_job_card(jc)
    
    def refresh_job_card(self, job_card):
        """
        Refresh readiness for single Job Card
        
        Args:
            job_card: Job Card document
        """
        # Check material
        material_result = self.material_engine.evaluate_material_readiness(
            job_card.work_order,
            job_card=job_card.name
        )
        
        job_card.custom_material_available = 1 if material_result.get('is_ready') else 0
        
        # Check dependencies
        dependency_result = self.dependency_engine.evaluate(job_card)
        previous_complete = dependency_result.get('can_start', False)
        
        # Get WO status
        wo_status = frappe.db.get_value('Work Order', job_card.work_order, 'status')
        
        # Calculate can_start
        job_card.custom_can_start_operation = (
            job_card.custom_material_available
            and previous_complete
            and wo_status == "Submitted"
            and job_card.status != "Completed"
        )
        
        # Update status details
        if job_card.custom_can_start_operation:
            job_card.custom_material_status_details = "Ready to Start"
            job_card.custom_blocked_by = ""
        else:
            if not job_card.custom_material_available:
                job_card.custom_material_status_details = "Material Not Available"
                job_card.custom_blocked_by = self.get_material_shortage_message(material_result)
            elif not previous_complete:
                job_card.custom_material_status_details = "Waiting for Previous Operation"
                job_card.custom_blocked_by = dependency_result.get('reason', 'Dependency not met')
            elif wo_status != "Submitted":
                job_card.custom_material_status_details = "Work Order Not Active"
                job_card.custom_blocked_by = f"Work Order status: {wo_status}"
            else:
                job_card.custom_material_status_details = "Not Ready"
                job_card.custom_blocked_by = "Unknown reason"
        
        # Update timestamp
        job_card.custom_dependency_last_updated = now()
        
        job_card.save()
    
    def get_material_shortage_message(self, material_result):
        """
        Build human-readable shortage message
        
        Args:
            material_result: Material readiness result dict
        
        Returns:
            str: Shortage message
        """
        shortages = material_result.get('shortage_details', [])
        if not shortages:
            return "Material Not Available"
        
        messages = []
        for shortage in shortages:
            item = shortage.get('item_code')
            required = shortage.get('required_qty')
            available = shortage.get('available_qty')
            messages.append(f"{item}: Required {required}, Available {available}")
        
        return "; ".join(messages)
```

### Hook Registration

```python
# hooks.py

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

# readiness/job_card_readiness.py (additional functions)

def on_work_order_submit(doc, method):
    """Trigger Readiness Engine on WO submit"""
    from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
    engine = JobCardReadinessEngine()
    engine.initialize_work_order(doc)

def on_stock_entry_submit(doc, method):
    """Trigger Readiness Engine on Material Transfer"""
    if doc.purpose != "Material Transfer for Manufacture":
        return
    
    if not doc.work_order:
        return
    
    wo = frappe.get_doc('Work Order', doc.work_order)
    from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
    engine = JobCardReadinessEngine()
    engine.refresh_work_order(wo)

def on_job_card_complete(doc, method):
    """Trigger Readiness Engine on JC complete"""
    if doc.status != "Completed":
        return
    
    from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
    engine = JobCardReadinessEngine()
    engine.refresh_downstream_job_cards(doc)
```

---

## Custom Fields

### Job Card Fields

| Field | Type | Label | Description |
|-------|------|-------|-------------|
| `custom_material_status` | Select | Material Status | `Waiting for Material` / `Material Available` / `Material Short` |
| `custom_readiness_status` | Select | Readiness Status | `Ready to Start` / `Waiting for Previous Operation` / `Blocked` / `In Progress` / `Completed` |
| `custom_material_shortage_details` | Text | Shortage Details | Human-readable shortage message (if any) |
| `custom_dependency_last_updated` | Datetime | Last Updated | When readiness was last evaluated |
| `custom_blocked_by` | Data | Blocked By | Specific reason if blocked |

### Field Values

**Material Status:**
- `Waiting for Material` - No stock in WIP yet
- `Material Available` - Sufficient stock exists
- `Material Short` - Insufficient stock

**Readiness Status:**
- `Ready to Start` - ALL conditions met
- `Waiting for Material` - No stock in WIP yet
- `Waiting for Previous Operation` - Material ready, waiting on prior op
- `Blocked` - Material shortage or other issue
- `In Progress` - Currently running
- `Completed` - Already finished

**Blocked By (Specific Reason):**
- Item code: "Aluminium Coil 0.2×110"
- Job Card: "JC-00045"
- Workstation: "CNC-03"
- Status: "WO Cancelled", "QC Hold"
- Shortage: "Required: 30 kg, Available: 10 kg"

**Usage Pattern:**
- `custom_readiness_status` → For dashboards, filtering, high-level status
- `custom_blocked_by` → For operator messages, specific diagnostic details

### Field Evaluation

**On WO Submit:**
```python
# Evaluate CURRENT WIP stock immediately
material_result = engine.check_material_readiness(jc)

if material_result.is_ready:
    jc.custom_material_status = "Material Available"
    jc.custom_readiness_status = "Ready to Start" if dependencies_met else "Waiting for Previous Operation"
else:
    jc.custom_material_status = "Waiting for Material"
    jc.custom_readiness_status = "Blocked"
    jc.custom_blocked_by = "Waiting for Material Transfer"

jc.custom_dependency_last_updated = now()
jc.save()
```

**On Material Transfer:**
```python
# Re-evaluate with new stock
material_result = engine.check_material_readiness(jc)

if material_result.is_ready:
    jc.custom_material_status = "Material Available"
    # Re-evaluate readiness
    if dependencies_met:
        jc.custom_readiness_status = "Ready to Start"
        jc.custom_blocked_by = ""
    else:
        jc.custom_readiness_status = "Waiting for Previous Operation"
        jc.custom_blocked_by = f"Waiting for: {previous_jc_name}"
else:
    jc.custom_material_status = "Material Short"
    jc.custom_readiness_status = "Blocked"
    jc.custom_material_shortage_details = engine.get_shortage_message(material_result)

jc.custom_dependency_last_updated = now()
jc.save()
```

---

## Start Button Implementation

### Client Script

```javascript
// Client Script: Job Card Start Validation
// Doctype: Job Card

frappe.ui.form.on('Job Card', {
    refresh: function(frm) {
        if (frm.doc.status === 'Open' && frm.doc.docstatus === 0) {
            frm.page.clear_inner_toolbar();
            
            // Show status indicator
            if (frm.doc.custom_can_start_operation) {
                frm.page.set_indicator('Ready to Start', 'green');
            } else {
                frm.page.set_indicator(frm.doc.custom_blocked_by || 'Not Ready', 'red');
            }
            
            // Add Start button
            frm.page.add_inner_button(__('Start Job'), function() {
                start_job_with_validation(frm);
            }, 'Primary');
        }
    }
});

function start_job_with_validation(frm) {
    // Check cached status (instant)
    if (!frm.doc.custom_can_start_operation) {
        frappe.throw(__('Cannot start: {0}', [frm.doc.custom_blocked_by]));
    }
    
    // Lightweight validation (protect against changes)
    if (frm.doc.status === 'Work In Progress') {
        frappe.throw(__('Job Card already in progress'));
    }
    
    // Optional: Quick stock check
    frappe.call({
        method: 'tekson_manufacturing.api.job_card_start.quick_stock_check',
        args: { job_card_name: frm.doc.name },
        callback: function(r) {
            if (r.message && r.message.available) {
                // Proceed with start
                start_job_card(frm);
            } else {
                frappe.throw(__('Material no longer available in WIP'));
            }
        }
    });
}

function start_job_card(frm) {
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

## Testing

### Test Scenarios

| Test ID | Scenario | Expected Result |
|---------|----------|-----------------|
| TC-JCR-001 | WO Submit | JCs initialized with "Waiting for Transfer" |
| TC-JCR-002 | Material Transfer (sufficient stock) | `custom_material_available` = 1, `custom_can_start` = 1 (if first op) |
| TC-JCR-003 | Material Transfer (insufficient stock) | `custom_material_available` = 0, shortage message |
| TC-JCR-004 | Operation 1 Complete | Operation 2 `custom_can_start` = 1 (if material available) |
| TC-JCR-005 | Material Return | Refresh all JCs, update availability |
| TC-JCR-006 | Start Button (ready JC) | Starts successfully |
| TC-JCR-007 | Start Button (blocked JC) | Shows error with `custom_blocked_by` message |

---

## Performance

### Target Response Times

| Operation | Target | Notes |
|-----------|--------|-------|
| WO Submit | < 2 seconds | Initialize all JCs |
| Material Transfer | < 3 seconds | Refresh all JCs in WO |
| Operation Complete | < 1 second | Refresh downstream JCs only |
| Start Button | < 100ms | Cached validation only |

### Optimization Strategies

1. **Cache material readiness results** per WO (not per JC)
2. **Refresh downstream only** on operation complete
3. **Use database queries** instead of document loads where possible
4. **Batch save** multiple JC updates

---

## Monitoring

### Logging

```python
# Log readiness evaluation
frappe.log_error(
    title="Job Card Readiness Evaluated",
    message=f"JC: {jc.name}, Can Start: {jc.custom_can_start_operation}, Updated: {jc.custom_dependency_last_updated}"
)
```

### Audit Trail

Fields tracked:
- `custom_dependency_last_updated` - When evaluated
- `custom_blocked_by` - Why blocked (if applicable)
- `custom_material_status_details` - Human-readable status

---

## References

- **Business Rules:** JC-003, JC-003A, JC-004, WH-009
- **Implementation:** `readiness/job_card_readiness.py`, `utils/job_card_utils.py`
- **Related Docs:** `WAREHOUSE_ARCHITECTURE_DECISION.md`, `MES_BUSINESS_RULES.md`

---

*This specification separates Planning (WO creation) from Execution (material commitment), ensuring accurate Job Card readiness status without unnecessary calculations.*
