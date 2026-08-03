# Job Card Readiness Engine - Technical Specification

**Version:** 4.0 (Final)  
**Date:** 2026-08-03  
**Status:** Ready for Implementation  
**Architecture:** Separation of Concerns

---

## Core Design Principles

### 1. Dual Field Strategy ✅

| Field Type | Purpose | Example |
|------------|---------|---------|
| **Boolean** | Program logic, queries, filters | `custom_can_start_operation` |
| **Select** | UI, dashboards, reporting | `custom_readiness_status` |
| **Text/Data** | Diagnostics, user messages | `custom_blocked_by` |

**Rationale:**
```python
# Boolean for logic (fast, clean)
if not jc.custom_can_start_operation:
    frappe.throw(...)

# SQL queries (indexed, efficient)
WHERE custom_can_start_operation = 1

# Select for UI (human-readable)
"Ready to Start" vs "Blocked"

# Text for diagnostics (specific)
"Aluminium Coil 0.2×110: Required 30 kg, Available 10 kg"
```

---

### 2. Separation: Evaluation vs Persistence ✅

```
┌─────────────────────────────────────────────────────────────┐
│                    EVALUATION (Pure)                        │
│                                                             │
│  evaluate_job_card()                                        │
│        ↓                                                    │
│  Returns: ReadinessResult (dataclass)                       │
│        ↓                                                    │
│  No database writes                                         │
│  No side effects                                            │
│  Easy to unit test                                          │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    PERSISTENCE (Orchestrated)               │
│                                                             │
│  apply_result_to_job_card()                                 │
│        ↓                                                    │
│  Uses frappe.db.set_value() (no validations/notifications) │
│        ↓                                                    │
│  Batch updates where possible                               │
│        ↓                                                    │
│  Save only if changed                                       │
└─────────────────────────────────────────────────────────────┘
```

---

### 3. Engine Responsibilities ✅

```
┌─────────────────────────────────────────────────────────────┐
│              Material Readiness Engine                      │
│                                                             │
│  Input: Work Order, Job Card                                │
│  Output: MaterialResult (dataclass)                         │
│                                                             │
│  Checks:                                                    │
│  - Available qty in WIP                                     │
│  - Required qty from BOM                                    │
│  - Shortage details                                         │
│                                                             │
│  Does NOT:                                                  │
│  - Set Job Card fields                                      │
│  - Check dependencies                                       │
│  - Know about readiness                                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                Dependency Engine                            │
│                                                             │
│  Input: Job Card                                            │
│  Output: DependencyResult (dataclass)                       │
│                                                             │
│  Checks:                                                    │
│  - Previous operation complete?                             │
│  - Sequence integrity                                       │
│  - Reason/diagnostic                                        │
│                                                             │
│  Does NOT:                                                  │
│  - Check material availability                              │
│  - Set Job Card fields                                      │
│  - Know about readiness                                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              Job Card Readiness Engine                      │
│                                                             │
│  Input: Job Card                                            │
│  Output: ReadinessResult (dataclass)                        │
│                                                             │
│  Orchestrates:                                              │
│  - Calls Material Engine                                    │
│  - Calls Dependency Engine                                  │
│  - Combines results                                         │
│  - Applies to Job Card                                      │
│                                                             │
│  Sets:                                                      │
│  - custom_material_status (Select)                          │
│  - custom_readiness_status (Select)                         │
│  - custom_material_available_for_operation (Boolean)        │
│  - custom_can_start_operation (Boolean)                     │
│  - custom_blocked_by (Data)                                 │
│  - custom_dependency_last_updated (Datetime)                │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Classes

### Constants (No Hardcoding)

```python
# Material Status Constants
class MaterialStatus:
    WAITING = "Waiting for Material"
    AVAILABLE = "Material Available"
    SHORT = "Material Short"

# Readiness Status Constants
class ReadinessStatus:
    READY = "Ready to Start"
    WAITING_MATERIAL = "Waiting for Material"
    WAITING_PREVIOUS_OP = "Waiting for Previous Operation"
    BLOCKED = "Blocked"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    HOLD = "On Hold"  # Reserved for future: QC Hold, Engineering Hold, etc.
```

**Rationale:** Prevents spelling mistakes, enables refactoring, single source of truth.

### MaterialResult

```python
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class MaterialResult:
    is_ready: bool
    status: str  # "Waiting for Material", "Material Available", "Material Short"
    available_qty: float
    required_qty: float
    shortage_qty: float
    shortage_details: List[dict]  # [{item_code, required, available, shortage}]
    warehouse: str
    message: str
```

### DependencyResult

```python
@dataclass
class DependencyResult:
    can_start: bool
    previous_complete: bool
    previous_jc_name: Optional[str]
    reason: str
    diagnostic: str
```

### ReadinessResult

```python
@dataclass
class ReadinessResult:
    material_status: str
    readiness_status: str
    can_start: bool
    blocked_by: str
    material_available: bool
    previous_operation_complete: bool
    last_updated: datetime  # Native datetime, formatted on persistence
    warnings: List[str]     # Non-blocking warnings
    errors: List[str]       # Blocking errors
    messages: List[str]     # Informational messages
```

**Rationale:**
- `warnings` → For dashboards (e.g., "Material expires in 2 days")
- `errors` → For diagnostics (e.g., "BOM item missing")
- `messages` → For logging/audit (e.g., "Evaluated on WO submit")
- `last_updated: datetime` → Native type, formatted on persistence

---

## Implementation Pattern

### Evaluation (Pure Function)

```python
def evaluate_job_card(self, job_card: 'JobCard') -> ReadinessResult:
    """
    Evaluate Job Card readiness without modifying database.
    
    Args:
        job_card: Job Card document
    
    Returns:
        ReadinessResult with all evaluation data
    """
    # Get material status
    material_result = self.material_engine.evaluate(
        work_order=job_card.work_order,
        job_card=job_card.name
    )
    
    # Get dependency status
    dependency_result = self.dependency_engine.evaluate(job_card)
    
    # Combine results
    return self._combine_results(material_result, dependency_result, job_card)

def _combine_results(
    self,
    material_result: MaterialResult,
    dependency_result: DependencyResult,
    job_card: 'JobCard'
) -> ReadinessResult:
    """Combine engine results into ReadinessResult"""
    
    # Determine material status
    if material_result.is_ready:
        material_status = "Material Available"
        material_available = True
    elif material_result.shortage_qty > 0:
        material_status = "Material Short"
        material_available = False
    else:
        material_status = "Waiting for Material"
        material_available = False
    
    # Determine readiness status
    if job_card.status == "Completed":
        readiness_status = "Completed"
        can_start = False
    elif job_card.status == "Work In Progress":
        readiness_status = "In Progress"
        can_start = False
    elif material_status == "Material Available":
        if dependency_result.previous_complete:
            readiness_status = "Ready to Start"
            can_start = True
        else:
            readiness_status = "Waiting for Previous Operation"
            can_start = False
    else:
        readiness_status = "Blocked"
        can_start = False
    
    # Determine blocked_by message
    if can_start:
        blocked_by = ""
    elif material_status == "Waiting for Material":
        blocked_by = "Waiting for Material Transfer"
    elif material_status == "Material Short":
        blocked_by = material_result.message
    elif not dependency_result.previous_complete:
        blocked_by = f"Waiting for: {dependency_result.previous_jc_name}"
    else:
        blocked_by = "Unknown reason"
    
    return ReadinessResult(
        material_status=material_status,
        readiness_status=readiness_status,
        can_start=can_start,
        blocked_by=blocked_by,
        material_available=material_available,
        previous_operation_complete=dependency_result.previous_complete,
        last_updated=now(),
        messages=[]
    )
```

### Persistence (Optimized)

```python
def apply_result_to_job_card(
    self,
    job_card_name: str,
    result: ReadinessResult
):
    """
    Apply ReadinessResult to Job Card without full document load/save.
    
    Uses frappe.db.set_value() for efficiency (no validations/notifications).
    
    Args:
        job_card_name: Job Card name
        result: ReadinessResult from evaluation
    """
    # Check if values actually changed (avoid unnecessary updates)
    current_values = frappe.db.get_value('Job Card', job_card_name, [
        'custom_material_status',
        'custom_readiness_status',
        'custom_can_start_operation',
        'custom_material_available_for_operation',
        'custom_blocked_by'
    ], as_dict=True)
    
    # Build update dict only for changed fields
    updates = {}
    
    if current_values.custom_material_status != result.material_status:
        updates['custom_material_status'] = result.material_status
    
    if current_values.custom_readiness_status != result.readiness_status:
        updates['custom_readiness_status'] = result.readiness_status
    
    if current_values.custom_can_start_operation != result.can_start:
        updates['custom_can_start_operation'] = result.can_start
    
    if current_values.custom_material_available_for_operation != result.material_available:
        updates['custom_material_available_for_operation'] = result.material_available
    
    if current_values.custom_blocked_by != result.blocked_by:
        updates['custom_blocked_by'] = result.blocked_by
    
    # Always update timestamp
    updates['custom_dependency_last_updated'] = result.last_updated
    
    # Apply updates if any changed
    if updates:
        frappe.db.set_value('Job Card', job_card_name, updates)
```

---

## Event Handlers

### WO Submit (Production Release)

```python
def on_work_order_submit(doc, method):
    """
    WO Submit = Production Release
    
    Evaluates ALL Job Cards immediately against current WIP stock.
    """
    engine = JobCardReadinessEngine()
    
    # Get all Job Cards for this WO
    job_cards = frappe.get_all('Job Card',
        filters={'work_order': doc.name, 'docstatus': ['!=', 2]},
        order_by='sequence_id')
    
    # Evaluate each Job Card
    for jc_data in job_cards:
        jc = frappe.get_doc('Job Card', jc_data.name)
        result = engine.evaluate_job_card(jc)
        engine.apply_result_to_job_card(jc.name, result)
    
    frappe.db.commit()
```

### Material Transfer (Optimized)

```python
def on_stock_entry_submit(doc, method):
    """
    Material Transfer for Manufacture
    
    Refreshes only Job Cards that consume transferred items.
    Phase 1: Refresh all JCs in WO (simpler)
    Phase 2: Refresh only affected JCs (optimization)
    """
    if doc.purpose != "Material Transfer for Manufacture":
        return
    
    if not doc.work_order:
        return
    
    engine = JobCardReadinessEngine()
    wo = frappe.get_doc('Work Order', doc.work_order)
    
    # Phase 1: Refresh all JCs in WO
    job_cards = frappe.get_all('Job Card',
        filters={'work_order': wo.name, 'docstatus': ['!=', 2]},
        order_by='sequence_id')
    
    for jc_data in job_cards:
        jc = frappe.get_doc('Job Card', jc_data.name)
        result = engine.evaluate_job_card(jc)
        engine.apply_result_to_job_card(jc.name, result)
    
    frappe.db.commit()
    
    # Phase 2 Optimization (TODO):
    # Get items transferred in this Stock Entry
    # Get BOM items for WO
    # Match items → refresh only JCs that consume those items
```

### Operation Complete (Downstream Only)

```python
def on_job_card_complete(doc, method):
    """
    Job Card Completed
    
    Refreshes ONLY next operation (not entire downstream chain).
    
    Rationale:
    - JC-20 complete → refresh JC-30
    - JC-30 will refresh JC-40 when it completes
    - No need to refresh JC-40 now (still blocked by JC-30)
    """
    if doc.status != "Completed":
        return
    
    engine = JobCardReadinessEngine()
    
    # Find NEXT operation only (not all downstream)
    next_jc = frappe.db.get_value('Job Card',
        filters={
            'work_order': doc.work_order,
            'sequence_id': doc.sequence_id + 1,
            'docstatus': ['!=', 2]
        },
        fieldname='name')
    
    if next_jc:
        jc = frappe.get_doc('Job Card', next_jc)
        result = engine.evaluate_job_card(jc)
        engine.apply_result_to_job_card(next_jc, result)
    
    frappe.db.commit()
```

---

## Start Button Validation

### Configurable Strictness

```python
# Manufacturing Settings
- enable_strict_start_validation (Check)

# If ON: Quick stock check before start
# If OFF: Trust cached status
```

### Implementation

```python
def start_job_card(job_card_name):
    """
    Start Job Card with configurable validation.
    
    Strict Validation OFF (default):
    - Trust cached status
    - Quick checks only
    
    Strict Validation ON:
    - Quick bin check (stock still exists)
    - All cached checks
    """
    jc = frappe.get_doc('Job Card', job_card_name)
    
    # Check cached readiness (instant)
    if not jc.custom_can_start_operation:
        frappe.throw(f"Cannot start: {jc.custom_readiness_status} - {jc.custom_blocked_by}")
    
    # Quick validation (protect against changes)
    if jc.status == 'Work In Progress':
        frappe.throw("Already in progress")
    
    if jc.work_order_status != 'Submitted':
        frappe.throw("Work Order is not active")
    
    # Optional: Quick stock check (configurable)
    mes_settings = frappe.get_doc('Manufacturing Settings')
    if mes_settings.enable_strict_start_validation:
        if not quick_bin_check(jc):
            frappe.throw("Material no longer available in WIP")
    
    # Start
    jc.status = 'Work In Progress'
    jc.actual_start_date = now()
    jc.save()
    
    return {'success': True}
```

---

## Performance Optimizations

### Current Approach (Inefficient)
```python
for jc in job_cards:
    jc = frappe.get_doc('Job Card', jc.name)
    # ... evaluate ...
    jc.save()  # 40 saves = 40 validations + 40 notifications
```

### Optimized Approach
```python
# Batch read
jc_data = frappe.get_all('Job Card',
    filters={'work_order': wo.name},
    fields=['name', 'custom_material_status', ...])

# Evaluate all
results = {}
for jc_row in jc_data:
    jc = frappe.get_doc('Job Card', jc_row.name)
    results[jc.name] = engine.evaluate_job_card(jc)

# Batch write (only changed fields)
for jc_name, result in results.items():
    engine.apply_result_to_job_card(jc_name, result)
    # Uses frappe.db.set_value() - no validations/notifications
```

### Performance Targets

| Operation | Target | Optimization |
|-----------|--------|--------------|
| WO Submit (40 JCs) | < 2 seconds | Batch read/write |
| Material Transfer | < 3 seconds | Only affected JCs (Phase 2) |
| Operation Complete | < 1 second | Next JC only |
| Start Button | < 100ms | Cached status only |

---

## Testing Strategy

### Unit Tests (Pure Evaluation)

```python
def test_evaluate_job_card_material_available():
    jc = create_test_job_card()
    result = engine.evaluate_job_card(jc)
    
    assert result.material_status == "Material Available"
    assert result.readiness_status == "Ready to Start"
    assert result.can_start == True
    assert result.blocked_by == ""

def test_evaluate_job_card_material_short():
    jc = create_test_job_card()
    result = engine.evaluate_job_card(jc)
    
    assert result.material_status == "Material Short"
    assert result.readiness_status == "Blocked"
    assert result.can_start == False
    assert "Aluminium Coil" in result.blocked_by
```

### Integration Tests (With Persistence)

```python
def test_wo_submit_refreshes_all_jcs():
    wo = create_test_work_order()
    wo.submit()
    
    for jc in wo.job_cards:
        jc.reload()
        assert jc.custom_dependency_last_updated is not None

def test_material_transfer_refreshes_only_that_wo():
    wo1 = create_test_work_order()
    wo2 = create_test_work_order()
    
    transfer = create_material_transfer(wo1)
    transfer.submit()
    
    # WO1 JCs refreshed
    assert wo1.job_cards[0].custom_dependency_last_updated > original_time
    
    # WO2 JCs NOT refreshed
    assert wo2.job_cards[0].custom_dependency_last_updated == original_time
```

---

## Implementation Order

| Phase | Component | Priority | Estimated Effort |
|-------|-----------|----------|------------------|
| 1 | Custom Fields | ✅ Complete | - |
| 2 | Material Engine (pure evaluation) | High | 2 days |
| 3 | Dependency Engine (pure evaluation) | High | 1 day |
| 4 | Readiness Engine (orchestration) | High | 2 days |
| 5 | WO Submit Hook | High | 0.5 day |
| 6 | Material Transfer Hook | High | 0.5 day |
| 7 | JC Complete Hook | High | 0.5 day |
| 8 | Start Button Update | Medium | 0.5 day |
| 9 | Unit Tests | High | 2 days |
| 10 | Integration Tests | High | 2 days |
| 11 | Department Dashboards | Medium | 3 days |

**Total:** ~15 days (3 weeks)

---

## Success Criteria

### Code Quality
- [ ] All engines are pure (evaluation only)
- [ ] Data classes used for all results
- [ ] No direct field setting in engines
- [ ] frappe.db.set_value() for persistence
- [ ] Batch updates where possible

### Functional
- [ ] WO Submit evaluates all JCs immediately
- [ ] Material Transfer refreshes only that WO
- [ ] Operation Complete refreshes next JC only
- [ ] Start button uses cached status
- [ ] Strict validation is configurable

### Performance
- [ ] WO Submit (40 JCs) < 2 seconds
- [ ] Material Transfer < 3 seconds
- [ ] Operation Complete < 1 second
- [ ] Start Button < 100ms

### Testing
- [ ] Unit tests for all engines
- [ ] Integration tests for all hooks
- [ ] Performance tests for all operations

---

**Ready for Implementation:** This specification provides complete guidance for implementing the Readiness Engine with proper separation of concerns, optimized persistence, and clear testing strategy.
