# Job Card Custom Fields - Categorization & Ownership

**Date:** August 2, 2026  
**Purpose:** Categorize custom fields by ownership and update frequency  

---

## Architecture Principle

Custom fields are categorized by **who owns the logic** and **when they update**.

```
Category A: Business State (Service Layer)
Category B: System State (Service Layer)
Category C: Display Only (Hook Layer)
```

---

## Category A: Business State

**Owned By:** `JobCardService`  
**Update Trigger:** Status changes, manual refresh  
**Purpose:** Core MES business logic state

| Field | Type | Owner | Update Logic |
|-------|------|-------|--------------|
| `custom_start_status` | Select | `JobCardService.update_start_status()` | On status change, refresh |
| `custom_dependency_status` | Select | `JobCardService.update_dependency_status()` | On dependency check |

**Business Rules:**
- `custom_start_status`: 7-state workflow (Awaiting → Completed)
- `custom_dependency_status`: 3-state (Waiting, Ready, Completed)

**Implementation:**
```python
# File: job_card_service.py
# Method: refresh_status()

def refresh_status(self, job_card):
    """Update all business state fields"""
    self.update_start_status(job_card)
    self.update_dependency_status(job_card)
    # Category B also updated here
```

---

## Category B: System State

**Owned By:** `JobCardService`  
**Update Trigger:** Material/Dependency changes  
**Purpose:** Real-time system readiness flags

| Field | Type | Owner | Update Logic |
|-------|------|-------|--------------|
| `custom_can_start_operation` | Check | `JobCardService.update_dependency_status()` | On dependency + material check |
| `custom_dependency_check` | Check | `JobCardService.update_dependency_status()` | On previous operation complete |
| `custom_material_available_for_operation` | Check | `JobCardService.update_material_status()` | On material readiness |

**Business Rules:**
- `custom_can_start_operation` = 1 IF (dependency_check = 1 AND material_available = 1)
- `custom_dependency_check` = 1 IF (previous operation complete OR first operation)
- `custom_material_available_for_operation` = 1 IF (MaterialReadinessEngine.is_ready = True)

**Implementation:**
```python
# File: job_card_service.py
# Method: update_dependency_status()

def update_dependency_status(self, job_card):
    """Update system state flags"""
    # Check dependencies
    prev_op = self.get_previous_operation_status(job_card)
    
    job_card.custom_dependency_check = 1 if (
        not prev_op or prev_op.get('status') == 'Completed'
    ) else 0
    
    # Can start = dependencies met + materials ready
    if job_card.custom_dependency_check == 1:
        readiness = self.get_material_readiness(job_card.work_order)
        job_card.custom_can_start_operation = 1 if readiness['is_ready'] else 0
    else:
        job_card.custom_can_start_operation = 0
```

---

## Category C: Display Only

**Owned By:** `job_card_utils` (hooks)  
**Update Trigger:** Job Card creation, rare updates  
**Purpose:** Information display, no business logic

| Field | Type | Owner | Update Logic |
|-------|------|-------|--------------|
| `custom_item_code` | Link | `job_card_utils.populate_job_card_fields()` | Once on creation |
| `custom_actual_production_item` | Float | `job_card_utils.populate_job_card_fields()` | Once on creation |
| `custom_material_status_details` | Text | `JobCardService.update_material_status()` | On material check |
| `custom_plant_floor` | Link | `job_card_utils.allocate_workstation()` | On workstation assignment |

**Note:** `custom_material_status_details` is display-only but updated by service layer for real-time accuracy.

**Implementation:**
```python
# File: job_card_utils.py
# Method: populate_job_card_fields()
# Trigger: Job Card Before Insert

def populate_job_card_fields(doc, method=None):
    """Set display-only fields once on creation"""
    
    # JC-007: Item visibility
    if doc.work_order and not doc.get('custom_item_code'):
        doc.custom_item_code = frappe.db.get_value(
            "Work Order", doc.work_order, "production_item"
        )
    
    # JC-008: Quantity visibility
    if doc.work_order and not doc.get('custom_actual_production_item'):
        wo = frappe.get_doc("Work Order", doc.work_order)
        doc.custom_actual_production_item = doc.for_quantity or wo.qty
```

---

## Update Frequency Matrix

| Field | Category | On Create | On Status Change | On Refresh API | On Submit |
|-------|----------|-----------|------------------|----------------|-----------|
| `custom_item_code` | C | ✅ | ❌ | ❌ | ❌ |
| `custom_actual_production_item` | C | ✅ | ❌ | ❌ | ❌ |
| `custom_start_status` | A | ✅ | ✅ | ✅ | ✅ |
| `custom_dependency_status` | A | ✅ | ✅ | ✅ | ✅ |
| `custom_can_start_operation` | B | ✅ | ✅ | ✅ | ❌ |
| `custom_dependency_check` | B | ✅ | ✅ | ✅ | ❌ |
| `custom_material_available_for_operation` | B | ✅ | ✅ | ✅ | ❌ |
| `custom_material_status_details` | C | ✅ | ✅ | ✅ | ❌ |
| `custom_plant_floor` | C | ✅ | ❌ | ❌ | ❌ |

---

## Ownership Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  Job Card DocType                        │
├─────────────────────────────────────────────────────────┤
│  Category A: Business State                              │
│  ├─ custom_start_status ──┐                             │
│  └─ custom_dependency_status ──┤ JobCardService         │
│                                └─ update_start_status() │
│                                └─ update_dependency()   │
├─────────────────────────────────────────────────────────┤
│  Category B: System State                                │
│  ├─ custom_can_start_operation ─┐                       │
│  ├─ custom_dependency_check ────┤ JobCardService       │
│  └─ custom_material_available ──┘                       │
│                                └─ update_material()     │
│                                └─ MaterialReadinessEngine│
├─────────────────────────────────────────────────────────┤
│  Category C: Display Only                                │
│  ├─ custom_item_code ──────────────┐                    │
│  ├─ custom_actual_production_item ─┤ job_card_utils    │
│  ├─ custom_plant_floor ────────────┘                    │
│  └─ custom_material_status_details ─ JobCardService     │
└─────────────────────────────────────────────────────────┘
```

---

## Hook Execution Order

### Job Card Before Insert
```
1. populate_job_card_fields() → Category C (item_code, qty)
2. allocate_workstation() → Category C (plant_floor)
3. set_wip_warehouse() → Uses plant_floor to set wip_warehouse
```

### Job Card Validate
```
1. set_wip_warehouse() → Ensure wip_warehouse matches plant_floor
```

### Job Card On Submit
```
1. Execution Engine → Updates Category A (start_status, dependency_status)
2. Execution Engine → Updates Category B (can_start, dependency_check, material_available)
3. Execution Engine → Triggers refresh of next Job Card
```

### Manual Refresh (API)
```
1. JobCardService.refresh_status() → Updates Category A + B
```

---

## Testing Strategy by Category

### Category A (Business State)
**Test:** Status workflow
```python
def test_start_status_workflow():
    jc = create_job_card()
    assert jc.custom_start_status == "Awaiting"
    
    start_jc(jc)
    assert jc.custom_start_status == "In Progress"
    
    complete_jc(jc)
    assert jc.custom_start_status == "Completed"
```

### Category B (System State)
**Test:** Readiness flags
```python
def test_can_start_operation():
    jc = create_job_card()
    
    # No materials transferred
    assert jc.custom_can_start_operation == 0
    
    # Transfer materials
    create_material_transfer(jc.work_order)
    refresh_status(jc)
    
    assert jc.custom_can_start_operation == 1
```

### Category C (Display Only)
**Test:** Field population
```python
def test_display_fields_populated():
    jc = create_job_card()
    
    assert jc.custom_item_code == "ITEM-001"
    assert jc.custom_actual_production_item == 100
    assert jc.custom_plant_floor == "CNC"
```

---

## Maintenance Guidelines

### When to Update Each Category

**Category A (Business State):**
- ✅ Change when business rules change
- ✅ Change when workflow states change
- ❌ Never update directly in hooks
- ❌ Never update in UI controllers

**Category B (System State):**
- ✅ Change when validation logic changes
- ✅ Change when readiness criteria change
- ❌ Never hardcode values
- ❌ Never update without engine validation

**Category C (Display Only):**
- ✅ Change when UI requirements change
- ✅ Change when display format changes
- ❌ Never use for business logic
- ❌ Never use for validation

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Updating Business State in Hooks
```python
# WRONG: Hook updating business state
def set_wip_warehouse(doc, method):
    doc.custom_start_status = "Ready to Start"  # ❌ Business logic in hook
```

**Fix:**
```python
# CORRECT: Hook only sets display fields
def set_wip_warehouse(doc, method):
    doc.wip_warehouse = f"WIP-{plant_floor} - TPL"  # ✅ Display/structural only
```

### ❌ Mistake 2: Hardcoding System State
```python
# WRONG: Hardcoded flag
doc.custom_can_start_operation = 1  # ❌ Bypasses validation
```

**Fix:**
```python
# CORRECT: Use service layer
service = JobCardService()
service.update_dependency_status(doc)  # ✅ Validates before setting
```

### ❌ Mistake 3: Mixing Categories
```python
# WRONG: Display field used for logic
if doc.custom_material_status_details:  # ❌ Display field in condition
    start_production()
```

**Fix:**
```python
# CORRECT: Use system state flag
if doc.custom_material_available_for_operation == 1:  # ✅ System state
    start_production()
```

---

## API Reference

### Get All Custom Fields
```python
from tekson_manufacturing.services.job_card_service import JobCardService

service = JobCardService()
details = service.get_job_card_details("JC-2026-001")

# Category A
print(details['job_card'].custom_start_status)
print(details['job_card'].custom_dependency_status)

# Category B
print(details['job_card'].custom_can_start_operation)
print(details['job_card'].custom_dependency_check)
print(details['job_card'].custom_material_available_for_operation)

# Category C
print(details['job_card'].custom_item_code)
print(details['job_card'].custom_actual_production_item)
print(details['job_card'].custom_material_status_details)
print(details['job_card'].custom_plant_floor)
```

### Refresh All Fields
```python
from tekson_manufacturing.services.job_card_service import JobCardService

service = JobCardService()
service.refresh_status("JC-2026-001")
# Updates Category A + B
# Category C updated only on creation
```

---

## Summary

| Category | Fields | Owner | Update Frequency | Purpose |
|----------|--------|-------|------------------|---------|
| **A** | 2 | `JobCardService` | On status change | Business workflow state |
| **B** | 3 | `JobCardService` | On validation change | System readiness flags |
| **C** | 4 | `job_card_utils` | Once on creation | Display/information |

**Total:** 9 custom fields, properly categorized and owned.

---

**Prepared By:** AI Assistant  
**Date:** August 2, 2026  
**Status:** ✅ Categorized by ownership
