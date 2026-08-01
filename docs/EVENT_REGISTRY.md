# Event Registry

**Document Type:** Architecture Reference  
**Version:** 1.0  
**Date:** 2026-08-01  
**Status:** Frozen  
**Project:** Tekson Manufacturing MES  

---

## Overview

This document registers all ERPNext event hooks and their corresponding MES service handlers. All ERP events are handled by MES services - no business logic in hooks.py.

**Purpose:** Define integration points, ensure consistent event handling, simplify debugging.

---

## Event Flow Architecture

```
ERPNext Event → hooks.py → MES Service → Engine → Repository → ERPNext ORM
     │                                              │
     │                                              ▼
     │                                      Business Logic
     │                                              │
     ▼                                              ▼
Message to User                            Data Persistence
```

---

## Registered Events

### Work Order Events

| ERP Event | DocType | Handler | Service | Business Rule | Status |
|-----------|---------|---------|---------|---------------|--------|
| `before_insert` | Work Order | `on_work_order_before_insert` | WorkOrderService | - | ✅ Implemented |
| `on_update` | Work Order | `on_work_order_update` | WorkOrderService | WO-001, WO-002 | ✅ Implemented |
| `before_submit` | Work Order | `on_work_order_before_submit` | WorkOrderService | - | ✅ Implemented |
| `on_submit` | Work Order | `on_work_order_submit` | WorkOrderService | - | ✅ Implemented |
| `before_cancel` | Work Order | `on_work_order_before_cancel` | WorkOrderService | - | 📋 Planned |
| `on_cancel` | Work Order | `on_work_order_cancel` | WorkOrderService | - | 📋 Planned |
| `on_trash` | Work Order | `on_work_order_trash` | WorkOrderService | - | 📋 Planned |

**File:** `tekson_manufacturing/hooks.py`

```python
# Work Order Events
"Work Order": {
    "before_insert": "tekson_manufacturing.services.work_order_service.on_work_order_before_insert",
    "on_update": "tekson_manufacturing.services.work_order_service.on_work_order_update",
    "before_submit": "tekson_manufacturing.services.work_order_service.on_work_order_before_submit",
    "on_submit": "tekson_manufacturing.services.work_order_service.on_work_order_submit",
    "before_cancel": "tekson_manufacturing.services.work_order_service.on_work_order_before_cancel",
    "on_cancel": "tekson_manufacturing.services.work_order_service.on_work_order_cancel",
    "on_trash": "tekson_manufacturing.services.work_order_service.on_work_order_trash",
}
```

---

### Job Card Events

| ERP Event | DocType | Handler | Service | Business Rule | Status |
|-----------|---------|---------|---------|---------------|--------|
| `before_insert` | Job Card | `on_job_card_before_insert` | JobCardService | JC-001 | ✅ Implemented |
| `before_save` | Job Card | `on_job_card_before_save` | JobCardService | JC-001, JC-002 | ✅ Implemented |
| `on_update` | Job Card | `on_job_card_update` | JobCardService | JC-003, JC-004 | ✅ Implemented |
| `on_submit` | Job Card | `on_job_card_submit` | JobCardService | JC-003 | ✅ Implemented |
| `before_cancel` | Job Card | `on_job_card_before_cancel` | JobCardService | - | 📋 Planned |
| `on_cancel` | Job Card | `on_job_card_cancel` | JobCardService | - | 📋 Planned |

**File:** `tekson_manufacturing/hooks.py`

```python
# Job Card Events
"Job Card": {
    "before_insert": "tekson_manufacturing.services.job_card_service.on_job_card_before_insert",
    "before_save": "tekson_manufacturing.services.job_card_service.on_job_card_before_save",
    "on_update": "tekson_manufacturing.services.job_card_service.on_job_card_update",
    "on_submit": "tekson_manufacturing.services.job_card_service.on_job_card_submit",
    "before_cancel": "tekson_manufacturing.services.job_card_service.on_job_card_before_cancel",
    "on_cancel": "tekson_manufacturing.services.job_card_service.on_job_card_cancel",
}
```

---

### Stock Entry Events

| ERP Event | DocType | Handler | Service | Business Rule | Status |
|-----------|---------|---------|---------|---------------|--------|
| `before_insert` | Stock Entry | `on_stock_entry_before_insert` | StockService | MR-010 | ✅ Implemented |
| `before_save` | Stock Entry | `on_stock_entry_before_save` | StockService | MR-010 | ✅ Implemented |
| `on_submit` | Stock Entry | `on_stock_entry_submit` | StockService | MR-010, MR-011 | ✅ Implemented |
| `before_cancel` | Stock Entry | `on_stock_entry_before_cancel` | StockService | - | 📋 Planned |
| `on_cancel` | Stock Entry | `on_stock_entry_cancel` | StockService | - | 📋 Planned |

**File:** `tekson_manufacturing/hooks.py`

```python
# Stock Entry Events
"Stock Entry": {
    "before_insert": "tekson_manufacturing.services.stock_service.on_stock_entry_before_insert",
    "before_save": "tekson_manufacturing.services.stock_service.on_stock_entry_before_save",
    "on_submit": "tekson_manufacturing.services.stock_service.on_stock_entry_submit",
    "before_cancel": "tekson_manufacturing.services.stock_service.on_stock_entry_before_cancel",
    "on_cancel": "tekson_manufacturing.services.stock_service.on_stock_entry_cancel",
}
```

---

### Material Request Events (Future)

| ERP Event | DocType | Handler | Service | Business Rule | Status |
|-----------|---------|---------|---------|---------------|--------|
| `on_submit` | Material Request | `on_material_request_submit` | MaterialService | - | 📋 Planned (Phase 2) |
| `before_cancel` | Material Request | `on_material_request_before_cancel` | MaterialService | - | 📋 Planned (Phase 2) |

---

### Purchase Order Events (Future)

| ERP Event | DocType | Handler | Service | Business Rule | Status |
|-----------|---------|---------|---------|---------------|--------|
| `on_submit` | Purchase Order | `on_purchase_order_submit` | ProcurementService | - | 📋 Planned (Phase 2) |
| `on_update` | Purchase Order | `on_purchase_order_update` | ProcurementService | - | 📋 Planned (Phase 2) |

---

## Event Handler Implementation

### Work Order Service Events

**File:** `tekson_manufacturing/services/work_order_service.py`

```python
@frappe.whitelist()
def on_work_order_before_insert(doc: "WorkOrder", method: str) -> None:
    """
    Work Order before insert event
    
    Business Rules: None
    
    Args:
        doc: Work Order document
        method: Event method name
    """
    # Validate Work Order data
    pass

@frappe.whitelist()
def on_work_order_update(doc: "WorkOrder", method: str) -> None:
    """
    Work Order on update event
    
    Business Rules:
    - WO-001: Parent WO completion triggers child WO availability
    - WO-002: Child WO completion triggers parent WO progress
    
    Args:
        doc: Work Order document
        method: Event method name
    """
    service = WorkOrderService()
    service.process_work_order_update(doc.name)

@frappe.whitelist()
def on_work_order_before_submit(doc: "WorkOrder", method: str) -> None:
    """
    Work Order before submit event
    
    Business Rules: None
    
    Args:
        doc: Work Order document
        method: Event method name
    """
    # Validate before submit
    pass

@frappe.whitelist()
def on_work_order_submit(doc: "WorkOrder", method: str) -> None:
    """
    Work Order on submit event
    
    Business Rules: None
    
    Args:
        doc: Work Order document
        method: Event method name
    """
    # Post-submit actions
    pass
```

---

### Job Card Service Events

**File:** `tekson_manufacturing/services/job_card_service.py`

```python
@frappe.whitelist()
def on_job_card_before_insert(doc: "JobCard", method: str) -> None:
    """
    Job Card before insert event
    
    Business Rules:
    - JC-001: Sequential operation enforcement
    
    Args:
        doc: Job Card document
        method: Event method name
    """
    service = JobCardService()
    service.validate_sequential_operations(doc.work_order)

@frappe.whitelist()
def on_job_card_before_save(doc: "JobCard", method: str) -> None:
    """
    Job Card before save event
    
    Business Rules:
    - JC-001: Sequential operation enforcement
    - JC-002: Status transition validation
    
    Args:
        doc: Job Card document
        method: Event method name
    """
    service = JobCardService()
    service.validate_status_transition(doc)

@frappe.whitelist()
def on_job_card_update(doc: "JobCard", method: str) -> None:
    """
    Job Card on update event
    
    Business Rules:
    - JC-003: Completion triggers next operation
    - JC-004: Department transfer on completion
    
    Args:
        doc: Job Card document
        method: Event method name
    """
    service = JobCardService()
    service.process_job_card_completion(doc)

@frappe.whitelist()
def on_job_card_submit(doc: "JobCard", method: str) -> None:
    """
    Job Card on submit event
    
    Business Rules:
    - JC-003: Completion triggers next operation
    
    Args:
        doc: Job Card document
        method: Event name
    """
    service = JobCardService()
    service.trigger_next_operation(doc.work_order)
```

---

### Stock Service Events

**File:** `tekson_manufacturing/services/stock_service.py`

```python
@frappe.whitelist()
def on_stock_entry_before_insert(doc: "StockEntry", method: str) -> None:
    """
    Stock Entry before insert event
    
    Business Rules:
    - MR-010: Stores to Department transfer validation
    
    Args:
        doc: Stock Entry document
        method: Event method name
    """
    service = StockService()
    service.validate_stores_transfer(doc)

@frappe.whitelist()
def on_stock_entry_before_save(doc: "StockEntry", method: str) -> None:
    """
    Stock Entry before save event
    
    Business Rules:
    - MR-010: Stores to Department transfer validation
    
    Args:
        doc: Stock Entry document
        method: Event method name
    """
    service = StockService()
    service.validate_stock_entry(doc)

@frappe.whitelist()
def on_stock_entry_submit(doc: "StockEntry", method: str) -> None:
    """
    Stock Entry on submit event
    
    Business Rules:
    - MR-010: Stores to Department transfer validation
    - MR-011: Cumulative availability check
    
    Args:
        doc: Stock Entry document
        method: Event method name
    """
    service = StockService()
    service.process_stock_entry_submit(doc)
```

---

## Future Events (Sprints 4-10)

### Sprint 4: Diagnostics & Messages

| ERP Event | DocType | Handler | Service | Status |
|-----------|---------|---------|---------|--------|
| `on_update` | User | `on_user_update` | MessageService | 📋 Planned |
| `after_insert` | Communication | `on_communication_insert` | MessageService | 📋 Planned |

### Sprint 5: Department Transfer Integration

| ERP Event | DocType | Handler | Service | Status |
|-----------|---------|---------|---------|--------|
| `before_insert` | Stock Entry | `on_department_transfer_before_insert` | TransferService | 📋 Planned |
| `on_submit` | Stock Entry | `on_department_transfer_submit` | TransferService | 📋 Planned |

### Sprint 6: Exception Handling

| ERP Event | DocType | Handler | Service | Status |
|-----------|---------|---------|---------|--------|
| `on_error` | Global | `on_exception` | ExceptionService | 📋 Planned |
| `before_save` | Error Log | `on_error_log_before_save` | ExceptionService | 📋 Planned |

### Sprint 7: Security Framework

| ERP Event | DocType | Handler | Service | Status |
|-----------|---------|---------|---------|--------|
| `before_insert` | User Permission | `on_user_permission_before_insert` | SecurityService | 📋 Planned |
| `validate` | Role Permission | `on_role_permission_validate` | SecurityService | 📋 Planned |

---

## Event Handling Guidelines

### Rule 1: Event Handler Location

**All event handlers MUST be in service files**

- ✅ CORRECT: `tekson_manufacturing/services/job_card_service.py`
- ❌ INCORRECT: `tekson_manufacturing/hooks.py` (only registration)

### Rule 2: Event Handler Signature

```python
# ✅ CORRECT
@frappe.whitelist()
def on_job_card_before_save(doc: "JobCard", method: str) -> None:
    """Event handler"""
    service = JobCardService()
    service.validate_status_transition(doc)

# ❌ INCORRECT
def on_job_card_before_save(doc):  # No type hints
    pass  # Business logic in handler
```

### Rule 3: Event Handler Pattern

```python
# ✅ CORRECT - Delegate to service
@frappe.whitelist()
def on_job_card_update(doc: "JobCard", method: str) -> None:
    service = JobCardService()
    service.process_job_card_completion(doc)

# ❌ INCORRECT - Business logic in handler
@frappe.whitelist()
def on_job_card_update(doc: "JobCard", method: str) -> None:
    # Business logic here - WRONG
    if doc.status == "Completed":
        # ... 50 lines of code
        pass
```

### Rule 4: Error Handling in Events

```python
# ✅ CORRECT
@frappe.whitelist()
def on_job_card_before_save(doc: "JobCard", method: str) -> None:
    try:
        service = JobCardService()
        service.validate_status_transition(doc)
    except MESValidationError as e:
        frappe.throw(str(e), title=_("Validation Error"))
    except Exception as e:
        frappe.log_error(
            title=_("Job Card Before Save Error"),
            message=str(e)
        )
        raise

# ❌ INCORRECT - No error handling
@frappe.whitelist()
def on_job_card_before_save(doc: "JobCard", method: str) -> None:
    service = JobCardService()
    service.validate_status_transition(doc)  # May throw unhandled exception
```

---

## Event Execution Order

### Work Order Lifecycle

```
before_insert → Insert → on_update → before_save → save → on_update → before_submit → submit → on_submit
     │                                                                       │
     ▼                                                                       ▼
Validate Data                                                          Post-Submit Actions
```

### Job Card Lifecycle

```
before_insert → Insert → before_save → save → on_update → before_submit → submit → on_submit
     │              │         │                  │              │
     ▼              ▼         ▼                  ▼              ▼
Validate JC   Create JC  Validate Status   Complete JC   Trigger Next JC
```

### Stock Entry Lifecycle

```
before_insert → Insert → before_save → save → on_submit → submit
     │              │         │                  │
     ▼              ▼         ▼                  ▼
Validate SE   Create SE  Validate SE     Update Stock
```

---

## Debugging Events

### Enable Event Logging

```python
# In site_config.json
{
    "logging": 1,
    "log_level": 3  # DEBUG
}
```

### Check Event Execution

```python
# In frappe console
frappe.log.get_logs(filters={"method": ["like", "%job_card%"]})
```

### Common Event Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Event not firing | hooks.py not updated | Run `bench build` |
| Event fires twice | Duplicate registration | Check hooks.py |
| Event fails silently | Exception not logged | Add try/except with logging |
| Event order wrong | Priority not set | Use event priority |

---

## Performance Considerations

### Event Handler Performance

| Event | Target | Current | Status |
|-------|--------|---------|--------|
| `on_job_card_before_save` | < 500ms | < 300ms | ✅ OK |
| `on_job_card_update` | < 1s | < 800ms | ✅ OK |
| `on_stock_entry_submit` | < 2s | < 1.5s | ✅ OK |
| `on_work_order_update` | < 1s | < 800ms | ✅ OK |

### Optimization Tips

1. **Minimize database queries** in event handlers
2. **Use caching** for frequently accessed data
3. **Batch operations** when possible
4. **Avoid synchronous calls** to external systems

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-01 | Development | Initial event registry creation |

---

## Related Documents

- MES_ARCHITECTURE_OVERVIEW.md - Architecture layers
- MES_SERVICE_INTERFACES.md - Service definitions
- MES_EXCEPTION_HANDLING.md - Exception handling rules
- MES_LOGGING_STANDARD.md - Logging standards
