# Repository Coverage Matrix

**Document Type:** Architecture Reference  
**Version:** 1.0  
**Date:** 2026-08-01  
**Status:** Frozen  
**Project:** Tekson Manufacturing MES  

---

## Overview

This document maps all repositories to their corresponding ERPNext objects. All data access MUST go through repositories - no direct `frappe.get_doc` calls in services or engines.

**Purpose:** Ensure data access encapsulation, maintain architectural integrity, simplify testing.

---

## Repository Coverage

### Sprint 1-3 Repositories (Implemented)

| Repository | ERP Objects | Methods Implemented | Status |
|------------|-------------|---------------------|--------|
| **JobCardRepository** | Job Card | `get_by_name()`, `get_list()`, `get_pending()`, `get_completed()`, `update_status()` | ✅ Complete |
| **WorkOrderRepository** | Work Order | `get_by_name()`, `get_list()`, `get_parent()`, `get_children()`, `get_pending()`, `get_completed()` | ✅ Complete |
| **StockRepository** | Stock Entry | `get_by_name()`, `get_list()`, `get_stores_transfers()`, `get_department_transfers()`, `get_pending_transfers()` | ✅ Complete |
| **WarehouseRepository** | Warehouse | `get_by_name()`, `get_list()`, `get_department_warehouses()`, `get_parent_warehouse()`, `is_department_warehouse()` | ✅ Complete |

---

## Detailed Repository Mapping

### JobCardRepository

**File:** `tekson_manufacturing/repositories/job_card_repository.py`  
**ERP Object:** Job Card  
**Business Rules:** JC-001, JC-002, JC-003, JC-004, JC-005

| Method | Purpose | Returns | Business Rule |
|--------|---------|---------|---------------|
| `get_by_name(name)` | Get Job Card by name | JobCard | JC-001 |
| `get_list(filters)` | Get Job Cards with filters | List[JobCard] | - |
| `get_pending(work_order)` | Get pending Job Cards | List[JobCard] | JC-001 |
| `get_completed(work_order)` | Get completed Job Cards | List[JobCard] | JC-003 |
| `update_status(name, status)` | Update Job Card status | None | JC-002 |
| `get_current_operation(work_order)` | Get current operation | JobCard | JC-001 |
| `get_last_completed_operation(work_order)` | Get last completed operation | JobCard | JC-005 |
| `exists(name)` | Check if Job Card exists | bool | - |

**Example Usage:**
```python
repo = JobCardRepository()
job_card = repo.get_by_name("JC-2026-001")
pending = repo.get_pending("WO-2026-001")
repo.update_status("JC-2026-001", "Work In Progress")
```

---

### WorkOrderRepository

**File:** `tekson_manufacturing/repositories/work_order_repository.py`  
**ERP Object:** Work Order  
**Business Rules:** WO-001, WO-002

| Method | Purpose | Returns | Business Rule |
|--------|---------|---------|---------------|
| `get_by_name(name)` | Get Work Order by name | WorkOrder | - |
| `get_list(filters)` | Get Work Orders with filters | List[WorkOrder] | - |
| `get_parent(name)` | Get parent Work Order | WorkOrder | WO-002 |
| `get_children(name)` | Get child Work Orders | List[WorkOrder] | WO-002 |
| `get_pending()` | Get pending Work Orders | List[WorkOrder] | - |
| `get_completed()` | Get completed Work Orders | List[WorkOrder] | WO-001 |
| `get_by_production_item(item_code)` | Get WO for production item | WorkOrder | - |
| `exists(name)` | Check if Work Order exists | bool | - |
| `count(filters)` | Count Work Orders | int | - |

**Example Usage:**
```python
repo = WorkOrderRepository()
wo = repo.get_by_name("WO-2026-001")
parent = repo.get_parent("WO-2026-002")
children = repo.get_children("WO-2026-001")
completed = repo.get_completed()
```

---

### StockRepository

**File:** `tekson_manufacturing/repositories/stock_repository.py`  
**ERP Object:** Stock Entry  
**Business Rules:** MR-010, MR-011

| Method | Purpose | Returns | Business Rule |
|--------|---------|---------|---------------|
| `get_by_name(name)` | Get Stock Entry by name | StockEntry | - |
| `get_list(filters)` | Get Stock Entries with filters | List[StockEntry] | - |
| `get_stores_transfers(work_order)` | Get Stores → Dept transfers | List[StockEntry] | MR-010 |
| `get_department_transfers(work_order)` | Get Dept → Dept transfers | List[StockEntry] | - |
| `get_pending_transfers(work_order)` | Get pending transfers | List[StockEntry] | - |
| `get_balance(warehouse, item_code)` | Get stock balance | float | MR-011 |
| `get_available_qty(warehouse, item_code)` | Get available quantity | float | MR-011 |
| `get_transfers_for_wo(work_order)` | Get all transfers for WO | List[StockEntry] | MR-010 |

**Example Usage:**
```python
repo = StockRepository()
transfers = repo.get_stores_transfers("WO-2026-001")
balance = repo.get_balance("WIP-W", "ITEM-001")
pending = repo.get_pending_transfers("WO-2026-001")
```

---

### WarehouseRepository

**File:** `tekson_manufacturing/repositories/warehouse_repository.py`  
**ERP Object:** Warehouse  
**Business Rules:** Department warehouse model

| Method | Purpose | Returns | Business Rule |
|--------|---------|---------|---------------|
| `get_by_name(name)` | Get Warehouse by name | Warehouse | - |
| `get_list(filters)` | Get Warehouses with filters | List[Warehouse] | - |
| `get_department_warehouses()` | Get all department warehouses | List[Warehouse] | - |
| `get_parent_warehouse(name)` | Get parent warehouse | Warehouse | - |
| `is_department_warehouse(name)` | Check if department warehouse | bool | - |
| `get_warehouse_for_department(department)` | Get warehouse for department | Warehouse | - |
| `get_child_warehouses(parent)` | Get child warehouses | List[Warehouse] | - |
| `exists(name)` | Check if warehouse exists | bool | - |

**Example Usage:**
```python
repo = WarehouseRepository()
dept_warehouses = repo.get_department_warehouses()
is_dept = repo.is_department_warehouse("WIP-W")
warehouse = repo.get_warehouse_for_department("Welding")
```

---

## Future Repositories (Sprints 4-10)

### MessageRepository (Sprint 4)

| Repository | ERP Objects | Methods Planned | Status |
|------------|-------------|-----------------|--------|
| **MessageRepository** | Message Log | `create()`, `get_by_user()`, `get_by_type()`, `clear()` | 📋 Planned |

### TransferRepository (Sprint 5)

| Repository | ERP Objects | Methods Planned | Status |
|------------|-------------|-----------------|--------|
| **TransferRepository** | Stock Entry, Warehouse | `validate_transfer()`, `process_transfer()`, `reverse_transfer()` | 📋 Planned |

### ExceptionRepository (Sprint 6)

| Repository | ERP Objects | Methods Planned | Status |
|------------|-------------|-----------------|--------|
| **ExceptionRepository** | Error Log, Exception Log | `log_exception()`, `get_by_type()`, `get_unresolved()` | 📋 Planned |

### SecurityRepository (Sprint 7)

| Repository | ERP Objects | Methods Planned | Status |
|------------|-------------|-----------------|--------|
| **SecurityRepository** | User Permission, Role Permission | `check_permission()`, `get_user_roles()`, `validate_department_scope()` | 📋 Planned |

### UIRepository (Sprints 8-9)

| Repository | ERP Objects | Methods Planned | Status |
|------------|-------------|-----------------|--------|
| **UIRepository** | Custom Form, Workspace | `get_form_config()`, `get_workspace_config()`, `save_layout()` | 📋 Planned |

---

## Repository Pattern Enforcement

### ✅ CORRECT Usage

```python
# Service layer uses repository
class JobCardService:
    def __init__(self):
        self._repo = JobCardRepository()
    
    def start_job_card(self, job_card: str) -> None:
        jc = self._repo.get_by_name(job_card)
        self._repo.update_status(job_card, "Work In Progress")
```

### ❌ INCORRECT Usage

```python
# Service layer directly accesses ERP - NOT ALLOWED
class JobCardService:
    def start_job_card(self, job_card: str) -> None:
        jc = frappe.get_doc("Job Card", job_card)  # ❌ Direct access
        jc.status = "Work In Progress"
        jc.save()
```

---

## Data Access Rules

### Rule 1: Repository Encapsulation

**All data access MUST go through repositories**

- Services cannot call `frappe.get_doc()` directly
- Engines cannot call `frappe.get_all()` directly
- Only repositories can access ERP objects

### Rule 2: Repository Dependencies

**Repositories can only depend on:**
- ERPNext ORM (`frappe.get_doc`, `frappe.get_all`, `frappe.db`)
- Other repositories (for cross-entity queries)

**Repositories cannot depend on:**
- Services
- Engines
- Business logic

### Rule 3: Service Dependencies

**Services can only depend on:**
- Repositories
- Other services
- Exceptions

**Services cannot:**
- Access ERP objects directly
- Contain business logic (belongs in engines)

### Rule 4: Engine Dependencies

**Engines can only depend on:**
- Services
- Repositories (read-only)
- Exceptions

**Engines cannot:**
- Access ERP objects directly
- Modify data (use services)

---

## Testing Strategy

### Repository Testing

```python
class TestJobCardRepository(unittest.TestCase):
    def setUp(self):
        self.repo = JobCardRepository()
        self.job_card = create_test_job_card()
    
    def test_get_by_name(self):
        result = self.repo.get_by_name(self.job_card.name)
        self.assertEqual(result.name, self.job_card.name)
    
    def test_get_pending(self):
        result = self.repo.get_pending(self.job_card.work_order)
        self.assertGreater(len(result), 0)
```

### Service Testing (Mocked Repositories)

```python
class TestJobCardService(unittest.TestCase):
    def setUp(self):
        self.repo_mock = Mock(spec=JobCardRepository)
        self.service = JobCardService()
        self.service._repo = self.repo_mock
    
    def test_start_job_card(self):
        self.service.start_job_card("JC-2026-001")
        self.repo_mock.update_status.assert_called_once_with(
            "JC-2026-001", "Work In Progress"
        )
```

---

## Performance Considerations

### Query Optimization

| Pattern | Performance | Recommendation |
|---------|-------------|----------------|
| `get_by_name()` | O(1) | Use for single object retrieval |
| `get_list()` | O(n) | Use filters to limit results |
| `get_all()` | O(n) | Avoid - use `get_list()` with filters |
| N+1 Query | O(n²) | NEVER use - batch fetch instead |

### Caching Strategy

```python
# Cache frequently accessed data
@frappe.cache().hget("mes_repository", "warehouse_hierarchy", user=True)
def get_department_warehouses(self) -> List[Warehouse]:
    return self._get_warehouses_from_db()
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-01 | Development | Initial repository coverage matrix |

---

## Related Documents

- MES_ARCHITECTURE_OVERVIEW.md - Architecture layers
- MES_SERVICE_INTERFACES.md - Service definitions
- PYTHON_CODING_STANDARDS.md - Repository method naming
- MES_INTEGRATION_MATRIX.md - Component integration
