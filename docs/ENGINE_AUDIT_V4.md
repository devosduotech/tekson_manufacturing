# Engine Audit Against V4.0 Specification

**Date:** 2026-08-03  
**Version:** 4.0  
**Status:** Pre-Implementation Audit  

---

## Audit Summary

| Engine | File | Status | Compliance | Action Required |
|--------|------|--------|------------|-----------------|
| Material Readiness | `readiness/material_readiness.py` | ✅ Exists | 85% | Refactor to return dataclass |
| Dependency Engine | `validation/dependency_engine.py` | ✅ Exists | 90% | Refactor to return dataclass |
| Job Card Readiness | `readiness/job_card_readiness.py` | ❌ Missing | 0% | Create new |
| MES Coordinator | `mes/mes_coordinator.py` | ❌ Missing | 0% | Create new |

---

## 1. Material Readiness Engine

**File:** `tekson_manufacturing/readiness/material_readiness.py`  
**Class:** `MaterialReadinessEngine`  
**V4.0 Compliance:** 85%

### ✅ What's Correct

- [x] Pure evaluation logic (no field setting)
- [x] Checks WIP warehouse stock
- [x] Returns dict with `is_ready`, `shortage_details`
- [x] No dependency on Job Card state
- [x] Works with Work Order level

### ❌ What Needs Refactoring

| Issue | Current | V4.0 Required | Priority |
|-------|---------|---------------|----------|
| Return type | `dict` | `MaterialResult` dataclass | High |
| Constants | Hardcoded strings | `MaterialStatus` class | Medium |
| Method names | `evaluate_material_readiness()` | Keep (good) | - |
| Type hints | Partial | Full type hints | Medium |
| Docstrings | Good | Keep | - |

### Refactoring Plan

**Before:**
```python
def evaluate_material_readiness(self, work_order):
    return {
        'is_ready': True,
        'shortage_details': [],
        ...
    }
```

**After:**
```python
from tekson_manufacturing.mes.dataclasses import MaterialResult, MaterialStatus

def evaluate_material_readiness(self, work_order: str, job_card: str = None) -> MaterialResult:
    # ... evaluation logic ...
    
    return MaterialResult(
        is_ready=True,
        status=MaterialStatus.AVAILABLE,
        available_qty=100.0,
        required_qty=50.0,
        shortage_qty=0.0,
        shortage_details=[],
        warehouse="WIP-Ralu In - TPL",
        message="Material available",
        warnings=[],
        errors=[]
    )
```

**Impact:** Low (only Readiness Engine calls this)

---

## 2. Dependency Engine

**File:** `tekson_manufacturing/validation/dependency_engine.py`  
**Class:** `DependencyEngine`  
**V4.0 Compliance:** 90%

### ✅ What's Correct

- [x] Pure evaluation logic
- [x] Checks previous operation completion
- [x] Returns dict with `can_start`, `reason`
- [x] No knowledge of material
- [x] Works at Job Card level

### ❌ What Needs Refactoring

| Issue | Current | V4.0 Required | Priority |
|-------|---------|---------------|----------|
| Return type | `dict` | `DependencyResult` dataclass | High |
| Constants | Hardcoded strings | Use constants | Low |
| Type hints | Partial | Full type hints | Medium |
| Method names | `evaluate()` | Keep (good) | - |

### Refactoring Plan

**Before:**
```python
def evaluate(self, job_card):
    return {
        'can_start': True,
        'reason': 'Previous operation complete',
        ...
    }
```

**After:**
```python
from tekson_manufacturing.mes.dataclasses import DependencyResult

def evaluate(self, job_card: 'JobCard') -> DependencyResult:
    # ... evaluation logic ...
    
    return DependencyResult(
        can_start=True,
        previous_complete=True,
        previous_jc_name=None,
        reason='Previous operation complete',
        diagnostic='All dependencies met',
        warnings=[],
        errors=[]
    )
```

**Impact:** Low (only Readiness Engine calls this)

---

## 3. Job Card Readiness Engine

**File:** `tekson_manufacturing/readiness/job_card_readiness.py`  
**Class:** `JobCardReadinessEngine`  
**V4.0 Compliance:** 0% (Does not exist yet)

### Required Implementation

```python
# tekson_manufacturing/readiness/job_card_readiness.py

from dataclasses import dataclass
from datetime import datetime
from typing import List

from frappe import _

from tekson_manufacturing.mes.dataclasses import (
    MaterialResult,
    DependencyResult,
    ReadinessResult,
    MaterialStatus,
    ReadinessStatus
)
from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
from tekson_manufacturing.validation.dependency_engine import DependencyEngine


class JobCardReadinessEngine:
    """
    Job Card Readiness Engine
    
    Orchestrates Material and Dependency engines to evaluate
    Job Card readiness without setting fields directly.
    
    Separates evaluation from persistence.
    """
    
    def __init__(self):
        self.material_engine = MaterialReadinessEngine()
        self.dependency_engine = DependencyEngine()
    
    def refresh_work_order(self, work_order):
        """Evaluate all Job Cards in Work Order"""
        job_cards = frappe.get_all('Job Card',
            filters={'work_order': work_order.name, 'docstatus': ['!=', 2]},
            order_by='sequence_id')
        
        for jc_data in job_cards:
            jc = frappe.get_doc('Job Card', jc_data.name)
            result = self.evaluate_job_card(jc)
            self.apply_result_to_job_card(jc.name, result)
    
    def evaluate_job_card(self, job_card: 'JobCard') -> ReadinessResult:
        """Pure evaluation - no database writes"""
        # Get material status
        material_result = self.material_engine.evaluate_material_readiness(
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
        
        # Handle completed/in-progress states first
        if job_card.status == "Completed":
            return ReadinessResult(
                material_status=material_result.status,
                readiness_status=ReadinessStatus.COMPLETED,
                can_start=False,
                blocked_by="",
                material_available=material_result.is_ready,
                previous_operation_complete=dependency_result.previous_complete,
                last_updated=datetime.now(),
                warnings=[],
                errors=[],
                messages=["Job Card completed"]
            )
        
        if job_card.status == "Work In Progress":
            return ReadinessResult(
                material_status=material_result.status,
                readiness_status=ReadinessStatus.IN_PROGRESS,
                can_start=False,
                blocked_by="",
                material_available=material_result.is_ready,
                previous_operation_complete=dependency_result.previous_complete,
                last_updated=datetime.now(),
                warnings=[],
                errors=[],
                messages=["Job Card in progress"]
            )
        
        # Determine readiness
        if material_result.is_ready and dependency_result.previous_complete:
            readiness_status = ReadinessStatus.READY
            can_start = True
            blocked_by = ""
        elif not material_result.is_ready:
            readiness_status = ReadinessStatus.WAITING_MATERIAL
            can_start = False
            blocked_by = material_result.message
        elif not dependency_result.previous_complete:
            readiness_status = ReadinessStatus.WAITING_PREVIOUS_OP
            can_start = False
            blocked_by = f"Waiting for: {dependency_result.previous_jc_name}"
        else:
            readiness_status = ReadinessStatus.BLOCKED
            can_start = False
            blocked_by = "Unknown reason"
        
        return ReadinessResult(
            material_status=material_result.status,
            readiness_status=readiness_status,
            can_start=can_start,
            blocked_by=blocked_by,
            material_available=material_result.is_ready,
            previous_operation_complete=dependency_result.previous_complete,
            last_updated=datetime.now(),
            warnings=material_result.warnings + dependency_result.warnings,
            errors=material_result.errors + dependency_result.errors,
            messages=[]
        )
    
    def apply_result_to_job_card(self, job_card_name: str, result: ReadinessResult):
        """Apply ReadinessResult to Job Card (optimized persistence)"""
        
        # Get current values
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
    
    def refresh_next_job_card(self, job_card: 'JobCard'):
        """Refresh only next operation (not entire downstream chain)"""
        next_jc_name = frappe.db.get_value('Job Card',
            filters={
                'work_order': job_card.work_order,
                'sequence_id': job_card.sequence_id + 1,
                'docstatus': ['!=', 2]
            },
            fieldname='name')
        
        if next_jc_name:
            next_jc = frappe.get_doc('Job Card', next_jc_name)
            result = self.evaluate_job_card(next_jc)
            self.apply_result_to_job_card(next_jc_name, result)
```

---

## 4. MES Coordinator

**File:** `tekson_manufacturing/mes/mes_coordinator.py`  
**Class:** `MESExecutionCoordinator`  
**V4.0 Compliance:** 0% (Does not exist yet)

### Required Implementation

```python
# tekson_manufacturing/mes/mes_coordinator.py

from frappe import _


class MESExecutionCoordinator:
    """
    Central coordinator for MES execution events.
    
    Orchestrates multiple engines:
    - Readiness Engine (current)
    - Machine Availability Engine (future)
    - Quality Hold Engine (future)
    - OEE Engine (future)
    - Notification Engine (future)
    
    Hooks call Coordinator, Coordinator calls Engines.
    Hooks remain stable as MES grows.
    """
    
    @staticmethod
    def on_work_order_submit(work_order):
        """
        WO Submit = Production Release
        
        Evaluates all Job Cards immediately.
        """
        from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
        engine = JobCardReadinessEngine()
        engine.refresh_work_order(work_order)
    
    @staticmethod
    def on_material_transfer(stock_entry):
        """
        Material Transfer for Manufacture
        
        Refreshes Job Cards for affected Work Order.
        """
        if stock_entry.purpose != "Material Transfer for Manufacture":
            return
        
        if not stock_entry.work_order:
            return
        
        from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
        engine = JobCardReadinessEngine()
        engine.refresh_work_order(stock_entry.work_order)
    
    @staticmethod
    def on_job_card_complete(job_card):
        """
        Job Card Completed
        
        Refreshes only next Job Card in sequence.
        """
        if job_card.status != "Completed":
            return
        
        from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
        engine = JobCardReadinessEngine()
        engine.refresh_next_job_card(job_card)
```

---

## 5. Data Classes

**File:** `tekson_manufacturing/mes/dataclasses.py`  
**V4.0 Compliance:** 0% (Does not exist yet)

### Required Implementation

```python
# tekson_manufacturing/mes/dataclasses.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


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
    HOLD = "On Hold"  # Reserved for future holds


@dataclass
class MaterialResult:
    """Result from Material Readiness Engine"""
    is_ready: bool
    status: str  # MaterialStatus constant
    available_qty: float
    required_qty: float
    shortage_qty: float
    shortage_details: List[dict]
    warehouse: str
    message: str
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class DependencyResult:
    """Result from Dependency Engine"""
    can_start: bool
    previous_complete: bool
    previous_jc_name: Optional[str]
    reason: str
    diagnostic: str
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class ReadinessResult:
    """Result from Readiness Engine"""
    material_status: str  # MaterialStatus constant
    readiness_status: str  # ReadinessStatus constant
    can_start: bool
    blocked_by: str
    material_available: bool
    previous_operation_complete: bool
    last_updated: datetime
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)
```

---

## Implementation Order

### Phase 1: Foundation (Day 1-2)
1. ✅ Create `mes/dataclasses.py` (constants + dataclasses)
2. ✅ Refactor `MaterialReadinessEngine` to return `MaterialResult`
3. ✅ Refactor `DependencyEngine` to return `DependencyResult`

### Phase 2: Readiness Engine (Day 3-4)
4. ✅ Create `readiness/job_card_readiness.py`
5. ✅ Implement evaluation logic
6. ✅ Implement optimized persistence

### Phase 3: Coordinator (Day 5)
7. ✅ Create `mes/mes_coordinator.py`
8. ✅ Wire up all three event handlers

### Phase 4: Hook Registration (Day 6)
9. ✅ Update `hooks.py` to use Coordinator
10. ✅ Test all three triggers

### Phase 5: Testing (Day 7-10)
11. ✅ Unit tests for all engines
12. ✅ Integration tests for all hooks
13. ✅ Performance testing

---

## Audit Conclusion

**Current State:**
- ✅ Material Engine exists (85% compliant)
- ✅ Dependency Engine exists (90% compliant)
- ❌ Readiness Engine missing
- ❌ Coordinator missing
- ❌ Data classes missing

**Action Required:**
1. Create data classes and constants
2. Refactor existing engines to return dataclasses
3. Create Readiness Engine
4. Create Coordinator
5. Register hooks

**Estimated Effort:** 10 days (as per implementation checklist)

**Risk:** Low (existing engines are mostly compliant, just need refactoring)

---

**Ready to proceed with Phase 1: Foundation?** 🎯
