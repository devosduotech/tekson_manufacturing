# MES Repository Interfaces

**Document Type:** Technical Specification  
**Version:** 1.0  
**Date:** 2026-07-31  
**Status:** Frozen for Implementation  
**Project:** Tekson Manufacturing MES  

---

## Overview

This document defines the Repository Layer contract. All data access goes through repositories. Services and engines MUST NOT access ERPNext ORM directly.

---

## Repository Responsibilities

### What Repositories Do

1. **Data Access:** All CRUD operations for their DocType
2. **Query Abstraction:** Complex queries hidden behind simple methods
3. **Data Transformation:** Raw database results → structured objects
4. **Caching:** Optional caching for frequently accessed data
5. **Transaction Boundaries:** Database transaction management

### What Repositories Don't Do

1. **Business Logic:** No validation, no business rules
2. **Orchestration:** No calling other repositories (except for joins)
3. **API Logic:** No HTTP/request handling
4. **Exception Handling:** No business exceptions (only data exceptions)

---

## Repository Pattern

```
┌─────────────────┐
│    Service      │
└────────┬────────┘
         │ Uses
         ▼
┌─────────────────┐
│   Repository    │
└────────┬────────┘
         │ Uses
         ▼
┌─────────────────┐
│  ERPNext ORM    │
│  (frappe.db)    │
└─────────────────┘
```

---

## Repository Interfaces

### IJobCardRepository

**Module:** `tekson_manufacturing.repositories.job_card_repository`  
**DocType:** `Job Card`

```python
class IJobCardRepository:
    """
    Interface for Job Card Repository
    
    All methods must be implemented by JobCardRepository
    """
    
    # Read Operations
    
    def get(name: str) -> Optional[frappe.Document]:
        """Get Job Card by name"""
        pass
    
    def get_by_work_order(work_order: str, 
                         order_by: str = "sequence_id") -> List[frappe.Document]:
        """Get all Job Cards for Work Order"""
        pass
    
    def get_by_filters(filters: Dict, 
                      fields: List[str] = None,
                      order_by: str = None,
                      limit: int = None) -> List[Dict]:
        """Get Job Cards by filters"""
        pass
    
    def get_previous_operation(job_card_name: str) -> Optional[Dict]:
        """Get previous operation for Job Card"""
        pass
    
    def get_next_operation(job_card_name: str) -> Optional[Dict]:
        """Get next operation for Job Card"""
        pass
    
    def get_sequence_details(work_order: str) -> List[Dict]:
        """Get operation sequence details"""
        pass
    
    # Write Operations
    
    def create(jc_dict: Dict) -> frappe.Document:
        """Create Job Card"""
        pass
    
    def update(name: str, fields: Dict) -> frappe.Document:
        """Update Job Card fields"""
        pass
    
    def submit(name: str) -> frappe.Document:
        """Submit Job Card"""
        pass
    
    def cancel(name: str) -> frappe.Document:
        """Cancel Job Card"""
        pass
    
    def delete(name: str, force: bool = False) -> bool:
        """Delete Job Card"""
        pass
    
    # Utility Operations
    
    def exists(name: str) -> bool:
        """Check if Job Card exists"""
        pass
    
    def count(filters: Dict = None) -> int:
        """Count Job Cards"""
        pass
```

---

### IWorkOrderRepository

**Module:** `tekson_manufacturing.repositories.work_order_repository`  
**DocType:** `Work Order`

```python
class IWorkOrderRepository:
    """Interface for Work Order Repository"""
    
    # Read Operations
    
    def get(name: str) -> Optional[frappe.Document]:
        """Get Work Order by name"""
        pass
    
    def get_by_filters(filters: Dict, 
                      fields: List[str] = None,
                      order_by: str = None,
                      limit: int = None) -> List[Dict]:
        """Get Work Orders by filters"""
        pass
    
    def get_by_department(department: str) -> List[Dict]:
        """Get Work Orders by department"""
        pass
    
    def get_by_plant_floor(plant_floor: str) -> List[Dict]:
        """Get Work Orders by plant floor"""
        pass
    
    def get_production_progress(work_order: str) -> Dict:
        """Get production progress"""
        pass
    
    # Write Operations
    
    def create(wo_dict: Dict) -> frappe.Document:
        """Create Work Order"""
        pass
    
    def update(name: str, fields: Dict) -> frappe.Document:
        """Update Work Order fields"""
        pass
    
    def submit(name: str) -> frappe.Document:
        """Submit Work Order"""
        pass
    
    def cancel(name: str) -> frappe.Document:
        """Cancel Work Order"""
        pass
    
    # Utility Operations
    
    def exists(name: str) -> bool:
        """Check if Work Order exists"""
        pass
    
    def count(filters: Dict = None) -> int:
        """Count Work Orders"""
        pass
```

---

### IStockRepository

**Module:** `tekson_manufacturing.repositories.stock_repository`  
**DocTypes:** `Stock Entry`, `Stock Ledger Entry`, `Stock Entry Detail`

```python
class IStockRepository:
    """Interface for Stock Repository"""
    
    # Read Operations
    
    def get_stock_entry(name: str) -> Optional[frappe.Document]:
        """Get Stock Entry by name"""
        pass
    
    def get_stock_balance(item_code: str, 
                         warehouse: str = None) -> float:
        """Get actual stock balance"""
        pass
    
    def get_cumulative_transfers(item_code: str, 
                                work_order: str,
                                warehouse: str) -> float:
        """Get cumulative transfers (MR-011)"""
        pass
    
    def get_transfer_entries(item_code: str,
                            work_order: str,
                            warehouse: str) -> List[Dict]:
        """Get all transfer Stock Entries"""
        pass
    
    def get_entries_by_work_order(work_order: str) -> List[Dict]:
        """Get all Stock Entries for Work Order"""
        pass
    
    def get_stock_ledger_entries(item_code: str,
                                warehouse: str = None,
                                from_date: str = None,
                                to_date: str = None) -> List[Dict]:
        """Get Stock Ledger Entries"""
        pass
    
    # Write Operations
    
    def create_stock_entry(se_dict: Dict) -> frappe.Document:
        """Create Stock Entry"""
        pass
    
    def submit_stock_entry(name: str) -> frappe.Document:
        """Submit Stock Entry"""
        pass
    
    def cancel_stock_entry(name: str) -> frappe.Document:
        """Cancel Stock Entry"""
        pass
    
    # Utility Operations
    
    def exists(name: str) -> bool:
        """Check if Stock Entry exists"""
        pass
    
    def count_entries_by_work_order(work_order: str,
                                   purpose: str = None) -> int:
        """Count Stock Entries for Work Order"""
        pass
```

---

### IWarehouseRepository

**Module:** `tekson_manufacturing.repositories.warehouse_repository`  
**DocType:** `Warehouse`

```python
class IWarehouseRepository:
    """Interface for Warehouse Repository"""
    
    # Read Operations
    
    def get(name: str) -> Optional[frappe.Document]:
        """Get Warehouse by name"""
        pass
    
    def get_by_department(department: str) -> Optional[frappe.Document]:
        """Get warehouse for department"""
        pass
    
    def get_by_plant_floor(plant_floor: str) -> Optional[frappe.Document]:
        """Get warehouse for plant floor"""
        pass
    
    def get_by_warehouse_group(warehouse_group: str,
                              is_group: bool = False) -> List[Dict]:
        """Get warehouses by group"""
        pass
    
    def get_all_department_warehouses() -> List[Dict]:
        """Get all department warehouses"""
        pass
    
    def get_department_warehouse(work_order) -> Optional[str]:
        """Get Department Warehouse for Work Order (WH-002)"""
        pass
    
    def get_finished_goods_warehouse(work_order) -> Optional[str]:
        """Get Finished Goods Warehouse"""
        pass
    
    def get_warehouse_type(warehouse: str) -> str:
        """Get warehouse type"""
        pass
    
    def validate_warehouse_access(warehouse: str, user: str) -> bool:
        """Validate user has access"""
        pass
    
    # Write Operations
    
    def create(wh_dict: Dict) -> frappe.Document:
        """Create Warehouse"""
        pass
    
    # Utility Operations
    
    def exists(name: str) -> bool:
        """Check if Warehouse exists"""
        pass
```

---

## ORM Access Rules

### Rule 1: No Direct frappe.db Calls Outside Repositories

**Correct:**

```python
# In Service
from tekson_manufacturing.repositories.job_card_repository import JobCardRepository

repo = JobCardRepository()
jc = repo.get("JC-2026-001")
```

**Incorrect:**

```python
# In Service - DON'T DO THIS
jc = frappe.get_doc("Job Card", "JC-2026-001")
```

### Rule 2: No SQL Queries Outside Repositories

**Correct:**

```python
# In Repository
result = frappe.db.sql("""
    SELECT SUM(qty) FROM `tabStock Entry Detail`
    WHERE item_code = %s
""", (item_code,))
```

**Incorrect:**

```python
# In Service - DON'T DO THIS
result = frappe.db.sql("""
    SELECT SUM(qty) FROM `tabStock Entry Detail`
    WHERE item_code = %s
""", (item_code,))
```

### Rule 3: No frappe.get_all Outside Repositories

**Correct:**

```python
# In Repository
job_cards = frappe.get_all(
    "Job Card",
    filters={"work_order": work_order},
    fields=["name", "status"]
)
```

**Incorrect:**

```python
# In Service - DON'T DO THIS
job_cards = frappe.get_all(
    "Job Card",
    filters={"work_order": work_order}
)
```

---

## Caching Strategy

### When to Cache

| Data Type                  | Cache | TTL     | Invalidation Trigger            |
|----------------------------|-------|---------|---------------------------------|
| Warehouse Mapping          | Yes   | 1 hour  | Warehouse update                |
| Department Configuration   | Yes   | 1 hour  | Department update               |
| Stock Balance              | No    | -       | Too volatile                    |
| Job Card Status            | No    | -       | Too volatile                    |
| MES Settings               | Yes   | 5 min   | Settings update                 |

### Cache Implementation

```python
class WarehouseRepository:
    
    @frappe.cache()
    def get_by_plant_floor(self, plant_floor: str):
        """Cached warehouse lookup"""
        name = frappe.db.get_value(
            "Warehouse",
            {"custom_plant_floor": plant_floor, "is_group": 0},
            "name"
        )
        return self.get(name) if name else None
    
    @classmethod
    def invalidate_cache(cls, plant_floor: str):
        """Invalidate cache on update"""
        frappe.cache().delete_key(f"WarehouseRepository::get_by_plant_floor:{plant_floor}")
```

---

## Transaction Boundaries

### Single Operation

```python
# Repository methods are atomic
repo.update("JC-2026-001", {"status": "Completed"})
# Implicit transaction
```

### Multiple Operations

```python
# Service layer manages transactions
@frappe.whitelist()
def complete_job_card(job_card, quantity):
    try:
        frappe.db.begin()
        
        # Multiple repository calls
        jc_repo.update(job_card, {"status": "Completed"})
        wo_repo.update(work_order, {"produced_qty": new_qty})
        
        frappe.db.commit()
    except Exception:
        frappe.db.rollback()
        raise
```

### Transaction Rules

1. **Repository methods:** Single transaction (implicit)
2. **Service methods:** Manage explicit transactions
3. **Engine methods:** Delegate transactions to services
4. **API methods:** Wrap service calls with try-catch

---

## Locking Strategy

### Pessimistic Locking

Use for high-contention operations:

```python
# Lock Job Card during update
jc = frappe.get_doc("Job Card", job_card, for_update=True)
jc.status = "Completed"
jc.save()
```

### Optimistic Locking

Use for low-contention operations:

```python
# Check version before update
jc = repo.get(job_card)
if jc.modified != cached_modified:
    raise frappe.ValidationError("Document was modified by another user")
```

### Locking Guidelines

| Operation              | Lock Type     | Reason                        |
|------------------------|---------------|-------------------------------|
| Job Card Start         | Pessimistic   | High contention               |
| Job Card Complete      | Pessimistic   | High contention               |
| Material Readiness     | Optimistic    | Read-heavy                    |
| Stock Entry Creation   | Pessimistic   | Inventory accuracy            |
| Status Refresh         | None          | Read-only                     |

---

## Error Handling

### Repository Exceptions

```python
class RepositoryError(frappe.ValidationError):
    """Base repository exception"""
    pass

class DoesNotExistError(RepositoryError):
    """Document does not exist"""
    pass

class DatabaseError(RepositoryError):
    """Database operation failed"""
    pass
```

### Exception Handling Pattern

```python
class JobCardRepository:
    
    def get(self, name: str):
        try:
            return frappe.get_doc(self.doctype, name)
        except frappe.DoesNotExistError:
            return None  # Don't throw, return None
        except Exception as e:
            frappe.log_error(f"Repository error: {str(e)}")
            raise RepositoryError(f"Failed to get Job Card: {str(e)}")
```

---

## Testing Repositories

### Unit Test Pattern

```python
import unittest
from unittest.mock import patch, MagicMock

class TestJobCardRepository(unittest.TestCase):
    
    def setUp(self):
        self.repo = JobCardRepository()
    
    @patch('frappe.get_doc')
    def test_get_job_card(self, mock_get):
        """Test get method"""
        mock_jc = MagicMock()
        mock_jc.name = "JC-2026-001"
        mock_get.return_value = mock_jc
        
        result = self.repo.get("JC-2026-001")
        
        self.assertEqual(result.name, "JC-2026-001")
        mock_get.assert_called_once_with("Job Card", "JC-2026-001")
    
    def test_get_nonexistent_job_card(self):
        """Test get returns None for nonexistent"""
        result = self.repo.get("JC-NONEXISTENT")
        self.assertIsNone(result)
```

---

## Performance Guidelines

### Query Optimization

**Do:**

```python
# ✅ Use indexed fields
repo.get_by_filters({"work_order": wo, "docstatus": 1})

# ✅ Select only needed fields
repo.get_by_filters(filters, fields=["name", "status"])

# ✅ Use limit for large result sets
repo.get_by_filters(filters, limit=100)
```

**Don't:**

```python
# ❌ Unindexed fields
repo.get_by_filters({"custom_department": "CNC"})

# ❌ Select all fields
repo.get_by_filters(filters)  # Returns all fields

# ❌ No limit on large tables
repo.get_by_filters({})  # Could return thousands
```

---

## Repository Registration

### Service Locator Pattern

```python
# repositories/__init__.py
from .job_card_repository import JobCardRepository
from .work_order_repository import WorkOrderRepository
from .stock_repository import StockRepository
from .warehouse_repository import WarehouseRepository

__all__ = [
    'JobCardRepository',
    'WorkOrderRepository',
    'StockRepository',
    'WarehouseRepository'
]

# Usage
from tekson_manufacturing.repositories import JobCardRepository

repo = JobCardRepository()
```

---

## Revision History

| Version | Date       | Author      | Changes                          |
|---------|------------|-------------|----------------------------------|
| 1.0     | 2026-07-31 | Development | Initial creation                 |

---

## Related Documents

- MES_SERVICE_INTERFACES.md - Service layer interfaces
- MES_DATA_DICTIONARY.md - Field definitions
- CODE_REVIEW_STANDARDS.md - Repository code standards
