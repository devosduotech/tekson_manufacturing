# MES Service Interfaces

**Document Type:** Technical Specification  
**Version:** 1.0  
**Date:** 2026-07-31  
**Status:** Frozen for Implementation  
**Project:** Tekson Manufacturing MES  

---

## Overview

This document defines all public service interfaces in the MES system. All inter-module communication MUST go through these service interfaces. Direct database queries or cross-module imports are prohibited except within the same module.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer                             │
│              (Whitelisted Methods)                       │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│                   Service Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │JobCard   │  │WorkOrder │  │  Stock   │              │
│  │Service   │  │ Service  │  │ Service  │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│                  Engine Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │Execution │  │Material  │  │Dependency│              │
│  │Engine    │  │Readiness │  │Engine    │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│                 Repository Layer                         │
│            (ERPNext ORM / Database)                      │
└─────────────────────────────────────────────────────────┘
```

---

## Service Layer Interfaces

### JobCardService

**Module:** `tekson_manufacturing.services.job_card_service`  
**Purpose:** All Job Card operations

```python
class JobCardService:
    """
    Job Card Service - Central interface for Job Card operations
    
    All Job Card reads, writes, and validations go through this service.
    No direct Job Card access from other modules.
    """
    
    def get_job_card(self, job_card: str) -> frappe.Document:
        """
        Get Job Card document
        
        Args:
            job_card: Job Card name
        
        Returns: Job Card document
        
        Raises:
            frappe.DoesNotExistError: If Job Card not found
        """
        pass
    
    def get_job_card_details(self, job_card: str) -> dict:
        """
        Get complete Job Card details with related info
        
        Args:
            job_card: Job Card name
        
        Returns: dict with job_card, work_order, previous_operation, material_readiness
        
        Example:
            {
                'job_card': {...},
                'work_order': {...},
                'previous_operation': {...},
                'material_readiness': {...}
            }
        """
        pass
    
    def can_start(self, job_card: str) -> dict:
        """
        Check if Job Card can start
        
        Args:
            job_card: Job Card name
        
        Returns: dict with can_start, reason, validations
        
        Example:
            {
                'can_start': True,
                'reason': 'All validations passed',
                'validations': {
                    'dependencies': True,
                    'materials': True,
                    'permissions': True
                }
            }
        """
        pass
    
    def can_complete(self, job_card: str) -> dict:
        """
        Check if Job Card can complete
        
        Args:
            job_card: Job Card name
        
        Returns: dict with can_complete, reason, validations
        """
        pass
    
    def start(self, job_card: str, user: str = None) -> dict:
        """
        Start Job Card
        
        Args:
            job_card: Job Card name
            user: User starting (optional, defaults to frappe.session.user)
        
        Returns: dict with success, message, timestamp
        
        Raises:
            MESValidationError: If Job Card cannot start
        """
        pass
    
    def complete(self, job_card: str, quantity: float, user: str = None) -> dict:
        """
        Complete Job Card
        
        Args:
            job_card: Job Card name
            quantity: Completed quantity
            user: User completing (optional)
        
        Returns: dict with success, message, completed_qty
        
        Raises:
            MESValidationError: If Job Card cannot complete
        """
        pass
    
    def refresh_status(self, job_card: str) -> dict:
        """
        Refresh Job Card status fields
        
        Args:
            job_card: Job Card name
        
        Returns: dict with updated fields
        """
        pass
    
    def get_previous_operation(self, job_card: str) -> dict:
        """
        Get previous operation details
        
        Args:
            job_card: Job Card name
        
        Returns: dict with name, operation, sequence_id, status or None
        """
        pass
    
    def get_next_operation(self, job_card: str) -> dict:
        """
        Get next operation details
        
        Args:
            job_card: Job Card name
        
        Returns: dict with name, operation, sequence_id, status or None
        """
        pass
    
    def get_job_cards_for_work_order(self, work_order: str, 
                                      filters: dict = None) -> list:
        """
        Get all Job Cards for Work Order
        
        Args:
            work_order: Work Order name
            filters: Additional filters (optional)
        
        Returns: list of Job Card summaries
        """
        pass
    
    def update_material_status(self, job_card: str, 
                               material_result: dict) -> dict:
        """
        Update Job Card material status fields
        
        Args:
            job_card: Job Card name
            material_result: Material readiness result dict
        
        Returns: dict with updated fields
        """
        pass
    
    def update_dependency_status(self, job_card: str, 
                                 dependency_result: dict) -> dict:
        """
        Update Job Card dependency status fields
        
        Args:
            job_card: Job Card name
            dependency_result: Dependency validation result dict
        
        Returns: dict with updated fields
        """
        pass
```

---

### WorkOrderService

**Module:** `tekson_manufacturing.services.work_order_service`  
**Purpose:** All Work Order operations

```python
class WorkOrderService:
    """
    Work Order Service - Central interface for Work Order operations
    """
    
    def get_work_order(self, work_order: str) -> frappe.Document:
        """Get Work Order document"""
        pass
    
    def get_work_order_details(self, work_order: str) -> dict:
        """
        Get complete Work Order details
        
        Returns: dict with work_order, job_cards, material_readiness, progress
        """
        pass
    
    def get_material_readiness(self, work_order: str) -> dict:
        """
        Get material readiness status
        
        Returns: dict with is_ready, missing_items, transfer_summary
        """
        pass
    
    def refresh_material_status(self, work_order: str) -> dict:
        """
        Refresh material readiness status
        
        Returns: dict with updated status
        """
        pass
    
    def get_progress(self, work_order: str) -> dict:
        """
        Get Work Order progress
        
        Returns: dict with planned_qty, produced_qty, percent_complete
        """
        pass
    
    def complete(self, work_order: str, user: str = None) -> dict:
        """
        Complete Work Order
        
        Returns: dict with success, message, stock_entry
        """
        pass
    
    def get_job_cards(self, work_order: str, 
                      filters: dict = None) -> list:
        """Get all Job Cards for Work Order"""
        pass
    
    def update_custom_fields(self, work_order: str, 
                            fields: dict) -> dict:
        """
        Update Work Order custom fields
        
        Args:
            fields: dict of field_name: value
        """
        pass
```

---

### StockService

**Module:** `tekson_manufacturing.services.stock_service`  
**Purpose:** All Stock Entry and inventory operations

```python
class StockService:
    """
    Stock Service - Central interface for Stock Entry operations
    """
    
    def get_stock_balance(self, item_code: str, 
                         warehouse: str = None) -> float:
        """
        Get actual stock balance
        
        Args:
            item_code: Item code
            warehouse: Warehouse (optional, defaults to all warehouses)
        
        Returns: Actual stock quantity
        """
        pass
    
    def get_cumulative_transfers(self, item_code: str, 
                                 work_order: str,
                                 warehouse: str) -> float:
        """
        Get cumulative quantity transferred to warehouse
        
        Args:
            item_code: Item code
            work_order: Work Order name
            warehouse: Target warehouse
        
        Returns: Cumulative transferred quantity
        """
        pass
    
    def get_transfer_entries(self, item_code: str,
                            work_order: str,
                            warehouse: str) -> list:
        """
        Get all Stock Entries that transferred material
        
        Returns: list of Stock Entry details
        """
        pass
    
    def create_material_transfer(self, work_order: str,
                                items: list,
                                from_warehouse: str,
                                to_warehouse: str,
                                user: str = None) -> dict:
        """
        Create Material Transfer Stock Entry
        
        Args:
            work_order: Work Order name
            items: list of dicts with item_code, qty
            from_warehouse: Source warehouse
            to_warehouse: Target warehouse
            user: User creating (optional)
        
        Returns: dict with stock_entry, success, message
        
        Raises:
            MESValidationError: If creation fails
        """
        pass
    
    def create_manufacture_entry(self, work_order: str,
                                quantity: float,
                                user: str = None) -> dict:
        """
        Create Manufacture Stock Entry
        
        Args:
            work_order: Work Order name
            quantity: Quantity to manufacture
            user: User creating (optional)
        
        Returns: dict with stock_entry, success, message
        """
        pass
    
    def get_warehouse_type(self, warehouse: str) -> str:
        """
        Get warehouse type (WIP, Raw Material, etc.)
        
        Returns: Warehouse type
        """
        pass
    
    def get_department_warehouse(self, work_order: str) -> str:
        """
        Get Department Warehouse for Work Order
        
        Returns: Department warehouse name
        """
        pass
```

---

### WarehouseService

**Module:** `tekson_manufacturing.services.warehouse_service`  
**Purpose:** All Warehouse operations

```python
class WarehouseService:
    """
    Warehouse Service - Central interface for Warehouse operations
    """
    
    def get_department_warehouse(self, department: str) -> str:
        """
        Get warehouse for department
        
        Args:
            department: Department name
        
        Returns: Warehouse name
        
        Raises:
            MESValidationError: If warehouse not found
        """
        pass
    
    def get_department_from_warehouse(self, warehouse: str) -> str:
        """
        Get department for warehouse
        
        Args:
            warehouse: Warehouse name
        
        Returns: Department name
        """
        pass
    
    def get_warehouse_details(self, warehouse: str) -> dict:
        """
        Get warehouse details
        
        Returns: dict with name, warehouse_group, plant_floor, department
        """
        pass
    
    def get_all_department_warehouses(self) -> list:
        """
        Get all department warehouses
        
        Returns: list of warehouse dicts
        """
        pass
    
    def validate_warehouse_access(self, warehouse: str, 
                                 user: str) -> bool:
        """
        Validate user has access to warehouse
        
        Returns: True if user has access
        """
        pass
```

---

## Engine Layer Interfaces

### MaterialReadinessEngine

**Module:** `tekson_manufacturing.readiness.material_readiness`  
**Purpose:** Material readiness evaluation

```python
class MaterialReadinessEngine:
    """
    Material Readiness Engine
    
    Business Rules: MR-010, MR-011
    """
    
    def __init__(self, work_order: str = None, 
                 job_card: str = None):
        """Initialize with Work Order or Job Card"""
        pass
    
    def evaluate_material_readiness(self, 
                                   work_order: str = None) -> dict:
        """
        Evaluate material readiness
        
        Returns: dict with is_ready, missing_items, transferred_items, 
                shortage_details, transfer_summary
        """
        pass
    
    def get_department_warehouse(self, 
                                work_order: frappe.Document) -> str:
        """Get Department Warehouse for Work Order"""
        pass
    
    def get_cumulative_transferred_qty(self, item_code: str,
                                       work_order: str,
                                       warehouse: str) -> float:
        """Get cumulative transferred quantity (MR-011)"""
        pass
    
    def get_transfer_entries(self, item_code: str,
                            work_order: str,
                            warehouse: str) -> list:
        """Get all Stock Entry details for transfers"""
        pass
```

---

### DependencyEngine

**Module:** `tekson_manufacturing.validation.dependency_engine`  
**Purpose:** Dependency validation

```python
class DependencyEngine:
    """
    Dependency Engine
    
    Business Rules: DV-001, DV-002
    """
    
    def __init__(self, job_card: str = None,
                 work_order: str = None):
        """Initialize with Job Card or Work Order"""
        pass
    
    def validate_previous_operation(self, 
                                   job_card: str = None) -> dict:
        """
        Validate previous operation is complete (DV-001)
        
        Returns: dict with is_valid, message, previous_operation
        """
        pass
    
    def validate_sequence(self, work_order: str = None) -> dict:
        """
        Validate operation sequence (DV-002)
        
        Returns: dict with is_valid, message, sequence_details
        """
        pass
    
    def get_sequence_details(self, work_order: str) -> list:
        """
        Get operation sequence details
        
        Returns: list of operations with sequence_id, status
        """
        pass
```

---

### ExecutionEngine

**Module:** `tekson_manufacturing.execution.execution_engine`  
**Purpose:** Central MES orchestrator

```python
class ExecutionEngine:
    """
    Execution Engine - Central MES orchestrator
    
    Coordinates all MES operations.
    """
    
    def can_job_card_start(self, job_card: str) -> dict:
        """
        Check if Job Card can start
        
        Returns: dict with can_start, reason, validations
        """
        pass
    
    def can_job_card_complete(self, job_card: str) -> dict:
        """
        Check if Job Card can complete
        
        Returns: dict with can_complete, reason, validations
        """
        pass
    
    def complete_work_order(self, work_order: str) -> dict:
        """
        Complete Work Order (WO-001)
        
        Returns: dict with success, message, stock_entry
        """
        pass
    
    def get_department_warehouse(self, 
                                work_order: frappe.Document) -> str:
        """Get Department Warehouse"""
        pass
```

---

## API Layer (Whitelisted Methods)

### Material Readiness APIs

```python
@frappe.whitelist()
def evaluate_material_readiness(work_order: str) -> dict:
    """Evaluate material readiness for Work Order"""
    pass

@frappe.whitelist()
def can_job_card_start(job_card: str) -> dict:
    """Check if Job Card can start"""
    pass

@frappe.whitelist()
def get_transfer_suggestions(work_order: str) -> list:
    """Get material transfer suggestions for Stores"""
    pass

@frappe.whitelist()
def create_material_transfer_stock_entry(work_order: str,
                                        items: list = None) -> dict:
    """Create Material Transfer Stock Entry"""
    pass
```

### Job Card APIs

```python
@frappe.whitelist()
def get_job_card_details(job_card: str) -> dict:
    """Get Job Card details"""
    pass

@frappe.whitelist()
def start_job_card(job_card: str) -> dict:
    """Start Job Card"""
    pass

@frappe.whitelist()
def complete_job_card(job_card: str, quantity: float) -> dict:
    """Complete Job Card"""
    pass
```

### Work Order APIs

```python
@frappe.whitelist()
def get_work_order_details(work_order: str) -> dict:
    """Get Work Order details"""
    pass

@frappe.whitelist()
def complete_work_order(work_order: str) -> dict:
    """Complete Work Order"""
    pass
```

---

## Exception Classes

```python
class MESValidationError(frappe.ValidationError):
    """
    Base exception for MES validation errors
    
    Use for business rule violations.
    """
    pass

class MESMaterialError(MESValidationError):
    """
    Exception for material-related errors
    
    Use for MR-010, MR-011 violations.
    """
    pass

class MESDependencyError(MESValidationError):
    """
    Exception for dependency validation errors
    
    Use for DV-001, DV-002 violations.
    """
    pass

class MESPermissionError(frappe.PermissionError):
    """
    Exception for permission errors
    
    Use for SEC-001 to SEC-005 violations.
    """
    pass

class MESConfigurationError(frappe.ValidationError):
    """
    Exception for configuration errors
    
    Use when required configuration is missing.
    """
    pass
```

---

## Usage Examples

### Example 1: Check Material Readiness

```python
from tekson_manufacturing.services.job_card_service import JobCardService

service = JobCardService()
result = service.can_start("JC-2026-001")

if result['can_start']:
    # Start Job Card
    service.start("JC-2026-001")
else:
    frappe.msgprint(result['reason'])
```

### Example 2: Create Material Transfer

```python
from tekson_manufacturing.services.stock_service import StockService

service = StockService()

# Get transfer suggestions
suggestions = get_transfer_suggestions("WO-2026-001")

# Create transfer
result = service.create_material_transfer(
    work_order="WO-2026-001",
    items=[{'item_code': 'ITEM-001', 'qty': 100}],
    from_warehouse="Raw Materials Stores",
    to_warehouse="WIP-CNC"
)

if result['success']:
    frappe.msgprint(f"Transfer created: {result['stock_entry']}")
```

---

## Revision History

| Version | Date       | Author      | Changes                          |
|---------|------------|-------------|----------------------------------|
| 1.0     | 2026-07-31 | Development | Initial creation                 |

---

## Related Documents

- MES_DATA_DICTIONARY.md - Field definitions
- MES_EVENT_FLOW.md - Event triggers
- CODE_REVIEW_STANDARDS.md - Implementation standards
