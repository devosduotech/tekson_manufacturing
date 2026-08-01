# Python Coding Standards

**Document Type:** Development Standards  
**Version:** 1.0  
**Date:** 2026-08-01  
**Status:** Frozen  
**Project:** Tekson Manufacturing MES  

---

## Overview

This document defines Python coding conventions for the Tekson Manufacturing MES implementation. All developers must follow these standards to ensure code consistency, maintainability, and quality.

**Applies to:** All Python code in `tekson_manufacturing/` directory

---

## 1. File Structure

### 1.1 Module Organization

```python
# 1. Docstring (module description)
"""
Module description

Purpose: Brief description of module purpose
Business Rules: MR-010, MR-011
"""

# 2. Imports (standard library)
from __future__ import annotations
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

# 3. Imports (third-party)
import frappe
from frappe import _

# 4. Imports (local)
from tekson_manufacturing.exceptions import MESMaterialError
from tekson_manufacturing.repositories.stock_repository import StockRepository

# 5. Constants
CONSTANT_NAME = "value"

# 6. Classes
class ClassName:
    pass

# 7. Functions
def function_name():
    pass
```

### 1.2 File Naming

| Type | Convention | Example |
|------|------------|---------|
| Module | snake_case | `material_readiness.py` |
| Class | PascalCase | `MaterialReadinessEngine` |
| Test File | snake_case with prefix | `test_material_readiness.py` |

---

## 2. Naming Conventions

### 2.1 Variables and Functions

```python
# ✅ CORRECT
def evaluate_material_readiness(work_order: str) -> dict:
    """Evaluate material readiness"""
    missing_items = []
    is_ready = True
    return {"is_ready": is_ready, "missing_items": missing_items}

# ❌ INCORRECT
def evalMR(WO):  # Too abbreviated
    missingItems = []  # camelCase
    return {"isReady": True}  # camelCase keys
```

### 2.2 Constants

```python
# ✅ CORRECT
MES_SETTINGS_DOCTYPE = "MES Settings"
DEFAULT_WAREHOUSE_GROUP = "Work In Progress Stores"

# ❌ INCORRECT
mesSettings = "MES Settings"  # Not constant case
```

### 2.3 Classes

```python
# ✅ CORRECT
class MaterialReadinessEngine:
    """Engine for material readiness evaluation"""
    
class StockRepository:
    """Repository for stock operations"""

# ❌ INCORRECT
class materialReadinessEngine:  # Not PascalCase
class stock_repo:  # snake_case
```

### 2.4 Exceptions

```python
# ✅ CORRECT
class MESMaterialError(MESBaseError):
    """Base exception for material errors"""

class MaterialNotAvailableError(MESMaterialError):
    """Raised when material is not available"""

# ❌ INCORRECT
class mesMaterialError:  # Not PascalCase
class MaterialError(Exception):  # Should inherit from MESBaseError
```

---

## 3. Repository Method Naming

### 3.1 Standard Patterns

| Operation | Pattern | Example |
|-----------|---------|---------|
| Get single | `get_by_name()` | `get_by_name(name: str) -> WorkOrder` |
| Get list | `get_list()` | `get_list(filters: dict) -> List[WorkOrder]` |
| Create | `create()` | `create(data: dict) -> WorkOrder` |
| Update | `update()` | `update(name: str, data: dict) -> WorkOrder` |
| Delete | `delete()` | `delete(name: str) -> None` |
| Exists | `exists()` | `exists(name: str) -> bool` |
| Count | `count()` | `count(filters: dict) -> int` |

### 3.2 Business-Specific Methods

```python
# ✅ CORRECT
def get_work_order_by_production_item(work_order: str, item_code: str) -> WorkOrder:
    """Get Work Order for specific production item"""

def get_pending_job_cards(work_order: str) -> List[JobCard]:
    """Get all pending job cards for work order"""

def get_stock_balance(warehouse: str, item_code: str) -> float:
    """Get current stock balance"""

# ❌ INCORRECT
def fetchWO(w, i):  # Too abbreviated
def get_pending_jc(wo):  # Inconsistent naming
```

---

## 4. Service Method Naming

### 4.1 Standard Patterns

| Operation | Pattern | Example |
|-----------|---------|---------|
| Validate | `validate_*()` | `validate_material_availability()` |
| Process | `process_*()` | `process_department_transfer()` |
| Execute | `execute_*()` | `execute_job_card_start()` |
| Complete | `complete_*()` | `complete_work_order()` |
| Evaluate | `evaluate_*()` | `evaluate_readiness()` |
| Check | `check_*()` | `check_dependencies()` |

### 4.2 Business-Specific Methods

```python
# ✅ CORRECT
def validate_stores_transfer(work_order: str) -> bool:
    """Validate Stores to Department transfer"""

def process_job_card_start(job_card: str) -> None:
    """Process job card start operation"""

def complete_work_order(work_order: str) -> None:
    """Complete work order and trigger parent completion"""

# ❌ INCORRECT
def do_stores_check(wo):  # Too informal
def processJCStart(jc):  # Abbreviated
```

---

## 5. Type Hints

### 5.1 Function Signatures

```python
# ✅ CORRECT
def evaluate_material_readiness(
    work_order: str,
    include_shortages: bool = True
) -> Dict[str, Any]:
    """Evaluate material readiness"""
    return {"is_ready": True, "shortages": []}

def get_work_orders(
    status: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get work orders"""
    return []

# ❌ INCORRECT
def evaluate_material_readiness(work_order, include_shortages=True):  # No types
    pass
```

### 5.2 Return Types

```python
from typing import Dict, List, Optional, Tuple, Any

# ✅ CORRECT
def get_result() -> Dict[str, Any]:
    """Returns dictionary"""
    return {}

def get_items() -> List[str]:
    """Returns list"""
    return []

def get_optional_value() -> Optional[str]:
    """Returns string or None"""
    return None

def get_multiple_values() -> Tuple[str, int]:
    """Returns tuple"""
    return ("value", 42)

# ❌ INCORRECT
def get_result():  # No return type
    pass
```

---

## 6. Docstring Template

### 6.1 Function Docstring

```python
def evaluate_material_readiness(
    self,
    work_order: str,
    include_shortages: bool = True
) -> Dict[str, Any]:
    """
    Evaluate material readiness for a Work Order
    
    Business Rules:
    - MR-010: Stores transfers materials to Department Warehouse
    - MR-011: Cumulative availability check
    
    Args:
        work_order: Work Order name (e.g., "WO-2026-001")
        include_shortages: Include shortage details in result (default: True)
    
    Returns:
        Dictionary with keys:
        - is_ready (bool): True if all materials available
        - missing_items (List[str]): List of missing item codes
        - shortage_details (List[dict]): Detailed shortage information
    
    Raises:
        MESMaterialError: If Work Order not found
        MESConfigurationError: If MES Settings not configured
    
    Example:
        >>> result = engine.evaluate_material_readiness("WO-2026-001")
        >>> result['is_ready']
        True
        >>> result['missing_items']
        []
    
    Test Cases:
        - test_mr_010_stores_transfer_validation
        - test_mr_011_cumulative_availability_check
    
    Performance:
        Target: < 3 seconds for 100 items
    """
```

### 6.2 Class Docstring

```python
class MaterialReadinessEngine:
    """
    Engine for evaluating material readiness
    
    Purpose:
    Evaluate whether materials are available for production
    
    Business Rules:
    - MR-010: Stores transfers materials to Department Warehouse
    - MR-011: Cumulative availability check
    
    Dependencies:
    - StockRepository: Stock balance queries
    - WarehouseRepository: Warehouse hierarchy
    
    Example:
        >>> engine = MaterialReadinessEngine()
        >>> result = engine.evaluate_material_readiness("WO-2026-001")
    """
```

---

## 7. Logging Style

### 7.1 Log Levels

```python
import logging

logger = logging.getLogger(__name__)

# ✅ CORRECT
logger.debug("Evaluating material readiness for %s", work_order)
logger.info("Material readiness evaluated successfully for %s", work_order)
logger.warning("Material shortage detected for %s: %s", work_order, item_code)
logger.error("Failed to evaluate material readiness for %s", work_order, exc_info=True)
logger.critical("MES Settings not configured, system cannot function")

# ❌ INCORRECT
print("Evaluating material readiness")  # No logging
logger.info("Evaluated MR for " + work_order)  # String concatenation
logger.error("Error occurred")  # No context
```

### 7.2 Log Message Format

```python
# ✅ CORRECT
logger.info("Operation completed: %s for %s in %s ms", operation, entity, duration)
logger.error("Failed to %s: %s", operation, error_message, exc_info=True)

# ❌ INCORRECT
logger.info(f"Operation {operation} completed for {entity}")  # f-string in logs
```

---

## 8. Return Object Format

### 8.1 Success Response

```python
# ✅ CORRECT - Consistent structure
return {
    "success": True,
    "data": {...},
    "message": "Operation completed successfully"
}

# ✅ CORRECT - For evaluations
return {
    "is_ready": True,
    "missing_items": [],
    "shortage_details": []
}

# ❌ INCORRECT - Inconsistent
return True  # No context
return result  # Unclear structure
```

### 8.2 Error Response

```python
# ✅ CORRECT
raise MESMaterialError(
    "Materials not available for {0}".format(work_order),
    extra_context={
        "work_order": work_order,
        "missing_items": missing_items
    }
)

# ❌ INCORRECT
raise Exception("Error")  # Generic exception
raise MESMaterialError("Error")  # No context
```

---

## 9. Exception Handling

### 9.1 Exception Hierarchy

```python
# ✅ CORRECT
class MESBaseError(frappe.FrappeError):
    """Base exception for all MES errors"""

class MESMaterialError(MESBaseError):
    """Material-related errors"""

class MaterialNotAvailableError(MESMaterialError):
    """Specific material error"""

# ❌ INCORRECT
raise Exception("Error")  # Generic Python exception
raise frappe.FrappeError("Error")  # Direct Frappe exception
```

### 9.2 Exception Messages

```python
# ✅ CORRECT
raise MESMaterialError(
    "Materials not available for Work Order {0}: Missing {1}".format(
        work_order, ", ".join(missing_items)
    )
)

# ❌ INCORRECT
raise MESMaterialError("Material error")  # Too vague
raise MESMaterialError(f"Error for {work_order}")  # f-string (use .format)
```

---

## 10. Code Organization

### 10.1 Line Length

```python
# ✅ CORRECT - Max 100 characters
result = self._evaluate_material_readiness(
    work_order=work_order,
    include_shortages=True
)

# ❌ INCORRECT - Too long
result = self._evaluate_material_readiness(work_order=work_order, include_shortages=True, include_details=True, validate_warehouse=True)
```

### 10.2 Blank Lines

```python
# ✅ CORRECT
class ClassName:
    """Docstring"""
    
    def __init__(self):
        """Initialize"""
        pass
    
    def method_one(self):
        """Method one"""
        pass
    
    def method_two(self):
        """Method two"""
        pass

# ❌ INCORRECT - Inconsistent spacing
class ClassName:
    """Docstring"""
    def __init__(self):
        """Initialize"""
        pass
    def method_one(self):
        """Method one"""
        pass
```

---

## 11. Import Order

### 11.1 Import Groups

```python
# ✅ CORRECT - Ordered imports
# 1. Future imports
from __future__ import annotations

# 2. Standard library
from typing import Dict, List, Optional
from datetime import datetime
import logging

# 3. Third-party
import frappe
from frappe import _

# 4. Local application
from tekson_manufacturing.exceptions import MESMaterialError
from tekson_manufacturing.repositories.stock_repository import StockRepository

# 5. Relative imports (within package)
from .utils import helper_function

# ❌ INCORRECT - Mixed imports
import frappe
from typing import Dict
from tekson_manufacturing.exceptions import MESMaterialError
import logging
```

---

## 12. Testing Standards

### 12.1 Test Naming

```python
# ✅ CORRECT
def test_mr_010_stores_transfer_validation(self):
    """Test MR-010: Stores transfer validation"""

def test_mr_011_cumulative_availability_check(self):
    """Test MR-011: Cumulative availability check"""

# ❌ INCORRECT
def test_mr_010(self):  # Too vague
def testStoresTransfer(self):  # camelCase
```

### 12.2 Test Structure (AAA Pattern)

```python
# ✅ CORRECT
def test_mr_010_stores_transfer_validation(self):
    """Test MR-010: Stores transfer validation"""
    # Arrange
    work_order = create_work_order()
    transfer = create_stores_transfer(work_order)
    
    # Act
    result = self.engine.evaluate_material_readiness(work_order)
    
    # Assert
    self.assertTrue(result["is_ready"])
    self.assertEqual(len(result["missing_items"]), 0)

# ❌ INCORRECT - No structure
def test_mr_010(self):
    wo = create_wo()
    result = self.engine.evaluate(wo)
    self.assertTrue(result["is_ready"])
```

---

## 13. Performance Considerations

### 13.1 Database Queries

```python
# ✅ CORRECT - Efficient query
items = frappe.get_all(
    "Item",
    filters={"disabled": 0},
    fields=["name", "item_name", "stock_uom"],
    limit_page_length=100
)

# ❌ INCORRECT - N+1 query
items = frappe.get_all("Item", filters={"disabled": 0})
for item in items:
    details = frappe.get_doc("Item", item.name)  # N queries

# ✅ CORRECT - Batch fetch
items = frappe.get_all("Item", filters={"disabled": 0}, fields=["*"])
```

### 13.2 Caching

```python
# ✅ CORRECT - Cache frequently accessed data
@frappe.cache().hget("mes_settings", "default", user=True)
def get_mes_settings() -> Dict:
    return frappe.get_doc("MES Settings", "MES Settings")

# ❌ INCORRECT - Query every time
def get_mes_settings():
    return frappe.get_doc("MES Settings", "MES Settings")
```

---

## 14. Security Considerations

### 14.1 Input Validation

```python
# ✅ CORRECT - Validate inputs
def evaluate_material_readiness(self, work_order: str) -> Dict:
    if not work_order:
        raise MESValidationError("Work Order is required")
    
    if not frappe.db.exists("Work Order", work_order):
        raise MESMaterialError("Work Order {0} not found".format(work_order))

# ❌ INCORRECT - No validation
def evaluate_material_readiness(self, work_order):
    wo = frappe.get_doc("Work Order", work_order)  # May not exist
```

### 14.2 Permission Checks

```python
# ✅ CORRECT - Check permissions
def process_department_transfer(self, work_order: str) -> None:
    if not frappe.has_permission("Work Order", "read"):
        frappe.throw(_("No permission to access Work Order"), frappe.PermissionError)

# ❌ INCORRECT - No permission check
def process_department_transfer(self, work_order: str) -> None:
    wo = frappe.get_doc("Work Order", work_order)  # No permission check
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-01 | Development | Initial coding standards creation |

---

## Related Documents

- CODE_REVIEW_STANDARDS.md - Code review checklist
- SPRINT_DEFINITION_OF_DONE.md - Sprint completion criteria
- MES_LOGGING_STANDARD.md - Logging standards
- MES_EXCEPTION_HANDLING.md - Exception handling rules

---

## Enforcement

### Pre-Commit Hooks

```bash
# Run before each commit
bench lint  # Linting
bench run-tests  # Tests
```

### CI/CD Pipeline

- Automated linting on every push
- Automated testing on every push
- Code coverage reporting
- Security scanning

### Code Review

All code must pass code review against these standards before merge.
