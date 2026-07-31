# MES Code Review Standards

**Document Type:** Development Standards & Guidelines  
**Version:** 1.0  
**Date:** 2026-07-31  
**Status:** Approved for Implementation  
**Project:** Tekson Manufacturing MES  
**ERPNext Version:** V15

---

## Overview

This document defines coding standards, review requirements, and quality gates for Phase 1 MES implementation. All code must adhere to these standards before merging to develop.

---

## Folder Structure (Frozen)

```
tekson_manufacturing/
│
├── manufacturing/              # ERPNext Overrides (Thin Layer)
│   ├── custom_job_card.py
│   └── work_order.py
│
├── execution/                  # MES Engine
│   ├── execution_engine.py
│   ├── job_card_execution.py
│   └── work_order_completion.py
│
├── readiness/                  # Material Readiness
│   ├── material_readiness.py
│   ├── warehouse_validation.py
│   └── material_transfer.py
│
├── validation/                 # Dependency Validation
│   ├── dependency_engine.py
│   └── operation_validation.py
│
├── diagnostics/                # Operator Messages
│   ├── messages.py
│   └── status_builder.py
│
├── services/                   # Reusable Business Logic
│   ├── job_card_service.py
│   ├── work_order_service.py
│   ├── material_service.py
│   └── stock_service.py
│
├── api/                        # Whitelisted Methods
│   ├── job_card.py
│   ├── work_order.py
│   └── material.py
│
├── settings/                   # Configuration
│   ├── manufacturing_settings.py
│   └── warehouse_config.py
│
├── utils/                      # Utilities
│   └── helpers.py
│
└── tests/                      # Test Suite
    ├── unit/
    ├── integration/
    └── fixtures/
```

**Rule:** No new folders without architectural approval.

---

## Naming Conventions

### Python Files

- **Pattern:** `snake_case.py`
- **Examples:**
  - ✅ `material_readiness.py`
  - ✅ `execution_engine.py`
  - ❌ `MaterialReadiness.py`
  - ❌ `material-readiness.py`

### Classes

- **Pattern:** `PascalCase`
- **Examples:**
  - ✅ `MaterialReadinessEngine`
  - ✅ `ExecutionEngine`
  - ❌ `materialReadinessEngine`
  - ❌ `MATERIAL_READINESS_ENGINE`

### Functions & Methods

- **Pattern:** `snake_case`
- **Examples:**
  - ✅ `check_material_readiness()`
  - ✅ `validate_previous_operation()`
  - ❌ `checkMaterialReadiness()`
  - ❌ `CheckMaterialReadiness()`

### Variables

- **Pattern:** `snake_case`
- **Examples:**
  - ✅ `job_card`
  - ✅ `work_order`
  - ❌ `jobCard`
  - ❌ `JobCard`

### Constants

- **Pattern:** `UPPER_SNAKE_CASE`
- **Examples:**
  - ✅ `MAX_RETRY_COUNT`
  - ✅ `DEFAULT_WAREHOUSE`
  - ❌ `maxRetryCount`
  - ❌ `defaultWarehouse`

---

## Code Documentation

### Function Documentation (Required)

Every function MUST contain docstring with:

```python
def check_material_readiness(job_card):
    """
    Check if materials are ready for Job Card
    
    Business Rule: MR-010, MR-011
    
    Purpose:
        Validate that Stores has transferred required materials
        to Department Warehouse
    
    Args:
        job_card (Job Card): Job Card to check
    
    Returns:
        dict: {
            'is_ready': bool,
            'reason': str,
            'shortage_details': list
        }
    
    Raises:
        ValidationError: If validation fails
    
    Dependencies:
        - Stock Entry
        - Warehouse
    
    Test Case:
        TC-MR-010, TC-MR-011
    
    Example:
        >>> readiness = check_material_readiness(jc)
        >>> if readiness['is_ready']:
        ...     start_production()
    """
```

### Class Documentation (Required)

```python
class MaterialReadinessEngine:
    """
    Material Readiness Engine
    
    Purpose:
        Validate material availability for production
    
    Business Rules:
        - MR-001: Cumulative Transfer Validation
        - MR-002: Material Classification
        - MR-010: Stores to Production Handoff
        - MR-011: Stores Completeness Rule
    
    Usage:
        engine = MaterialReadinessEngine()
        readiness = engine.check_material(job_card)
    
    Dependencies:
        - Stock Entry
        - Warehouse
        - Item
    """
```

---

## Logging Standards

### Log Levels

```python
import frappe

# INFO - Normal operations
frappe.log_error(
    message=f"Material readiness checked for {job_card.name}",
    title="MES Material Readiness"
)

# ERROR - Exceptions
try:
    check_material(job_card)
except Exception as e:
    frappe.log_error(
        message=f"Material check failed for {job_card.name}: {str(e)}",
        title="MES Material Readiness Error"
    )
    raise

# WARNING - Potential issues
if available_qty < required_qty:
    frappe.log_error(
        message=f"Material shortage for {item_code}: {available_qty} < {required_qty}",
        title="MES Material Shortage Warning"
    )
```

### Logging Requirements

**Mandatory Logging:**
- Every business rule validation
- Every exception
- Every approval
- Every override
- Every Stock Entry creation
- Every Work Order completion

**Log Message Format:**
```
[MES Module] Action for Document: Details
```

**Examples:**
- ✅ `[MES Material Readiness] Checked for JC-001: Ready`
- ✅ `[MES Execution] Started JC-001: Success`
- ❌ `Checked material`
- ❌ `Error occurred`

---

## Exception Handling

### Standard Pattern

```python
from frappe import ValidationError

def validate_material(job_card):
    """Validate material for Job Card"""
    
    if not job_card.work_order:
        frappe.throw(
            "Work Order required for Job Card",
            ValidationError
        )
    
    if not material_available:
        frappe.throw(
            f"Material not available for {job_card.name}",
            ValidationError
        )
```

### Custom Exceptions

```python
class MESValidationError(ValidationError):
    """Base exception for MES validation errors"""
    pass

class MaterialNotReadyError(MESValidationError):
    """Raised when material is not ready for production"""
    pass

class DependencyNotMetError(MESValidationError):
    """Raised when dependency is not met"""
    pass
```

### Exception Rules

- ✅ Use `frappe.throw()` for user-facing errors
- ✅ Use `raise` for internal errors
- ✅ Always include context in error message
- ✅ Log exception before re-raising
- ❌ Never swallow exceptions
- ❌ Never use generic "Error occurred"

---

## Service Layer Pattern

### Service Class Structure

```python
class JobCardService:
    """Service for Job Card operations"""
    
    def __init__(self):
        self.engine = ExecutionEngine()
    
    def get_job_card_details(self, job_card_name):
        """
        Get complete Job Card details
        
        Args:
            job_card_name (str): Job Card name
        
        Returns:
            dict: Job Card details with related data
        """
        job_card = frappe.get_doc("Job Card", job_card_name)
        
        return {
            'job_card': job_card,
            'work_order': self.get_work_order(job_card.work_order),
            'material_readiness': self.check_material(job_card)
        }
    
    def can_start(self, job_card_name):
        """
        Check if Job Card can start
        
        Args:
            job_card_name (str): Job Card name
        
        Returns:
            dict: {
                'can_start': bool,
                'reason': str
            }
        """
        job_card = frappe.get_doc("Job Card", job_card_name)
        return self.engine.can_job_card_start(job_card)
```

### Service Rules

- ✅ Services contain business logic
- ✅ Services are reusable
- ✅ Services log all operations
- ✅ Services raise exceptions on error
- ❌ Services do NOT contain UI logic
- ❌ Services do NOT contain ERPNext overrides

---

## API Standards

### Whitelisted Method Pattern

```python
import frappe
from tekson_manufacturing.services.job_card_service import JobCardService

@frappe.whitelist()
def get_job_card_details(job_card):
    """
    Get Job Card details (API for client-side)
    
    Args:
        job_card (str): Job Card name
    
    Returns:
        dict: Job Card details
    """
    service = JobCardService()
    return service.get_job_card_details(job_card)
```

### API Rules

- ✅ All client-side calls use whitelisted methods
- ✅ Whitelisted methods call services (not engines directly)
- ✅ Whitelisted methods validate permissions
- ✅ Whitelisted methods log all calls
- ❌ Whitelisted methods do NOT contain business logic
- ❌ Whitelisted methods do NOT access database directly

---

## Testing Standards

### Unit Test Structure

```python
import unittest
from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine

class TestMaterialReadiness(unittest.TestCase):
    """Test Material Readiness Engine"""
    
    def setUp(self):
        """Setup test data"""
        self.engine = MaterialReadinessEngine()
        self.job_card = create_test_job_card()
    
    def test_mr010_department_transfer(self):
        """Test MR-010: Stores to Production handoff"""
        # Arrange
        transfer_material(self.job_card.work_order)
        
        # Act
        readiness = self.engine.check_material(self.job_card)
        
        # Assert
        self.assertTrue(readiness['is_ready'])
        self.assertEqual(readiness['reason'], 'Material available')
    
    def test_mr011_cumulative_availability(self):
        """Test MR-011: Cumulative availability check"""
        # Arrange
        transfer_partial(self.job_card.work_order, 40)
        transfer_partial(self.job_card.work_order, 35)
        transfer_partial(self.job_card.work_order, 25)
        
        # Act
        readiness = self.engine.check_material(self.job_card)
        
        # Assert
        self.assertTrue(readiness['is_ready'])
        self.assertEqual(readiness['available_qty'], 100)
```

### Test Naming Convention

- **Pattern:** `test_{rule_code}_{description}()`
- **Examples:**
  - ✅ `test_mr010_department_transfer()`
  - ✅ `test_mr011_cumulative_availability()`
  - ❌ `test_material()`
  - ❌ `test_readiness()`

### Test Coverage Requirements

- **Target:** >80% code coverage
- **Mandatory:** All business rules tested
- **Mandatory:** All exceptions tested
- **Mandatory:** All edge cases tested

---

## Code Review Checklist

### Pre-Review Requirements

Before requesting code review:

- [ ] Code complete
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] Documentation complete
- [ ] Logging added
- [ ] Exception handling added
- [ ] No linting errors
- [ ] No TODO comments
- [ ] Git commit message follows standard

### Review Checklist

**Code Quality:**
- [ ] Follows naming conventions
- [ ] Follows folder structure
- [ ] Functions documented
- [ ] Classes documented
- [ ] No duplicate code
- [ ] No hard-coded values
- [ ] Configuration-driven

**Business Logic:**
- [ ] Implements business rules correctly
- [ ] Handles all exception scenarios
- [ ] Logs all operations
- [ ] Raises appropriate exceptions
- [ ] Validates inputs

**Testing:**
- [ ] Unit tests cover all scenarios
- [ ] Integration tests cover end-to-end flow
- [ ] Edge cases tested
- [ ] Exception cases tested
- [ ] Tests are independent

**Security:**
- [ ] Permissions checked
- [ ] Department scope enforced
- [ ] Approvals logged
- [ ] Overrides logged
- [ ] No SQL injection risks

**Performance:**
- [ ] No N+1 queries
- [ ] Database indexes used
- [ ] Caching where appropriate
- [ ] No memory leaks
- [ ] Efficient loops

### Review Approval

**Required Approvals:**
- Technical Lead: ✅ Required
- Code Owner: ✅ Required
- QA: ✅ Required (for business logic)

**Merge Conditions:**
- All approvals received
- All tests passing
- No critical comments unresolved
- Coverage >80%

---

## Git Standards

### Branch Naming

- **Pattern:** `feature/{description}`
- **Examples:**
  - ✅ `feature/material-readiness`
  - ✅ `feature/dependency-engine`
  - ❌ `feature/new-stuff`
  - ❌ `feature/test`

### Commit Message Format

```
{type}: {subject}

{body}

{footer}
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Refactoring
- `test`: Tests
- `chore`: Maintenance

**Example:**
```
feat: Implement MR-010 department transfer logic

- Add check_department_material() to MaterialReadinessEngine
- Add get_cumulative_transfers() function
- Add unit tests for MR-010
- Add integration test with Stock Entry

Business Rule: MR-010
Test Case: TC-MR-010
```

### Pull Request Standards

**PR Title:**
- Clear and descriptive
- Follows commit message format

**PR Description:**
- What was changed
- Why it was changed
- Business rules implemented
- Test cases covered
- Screenshots (if UI)

**PR Review:**
- Respond to all comments
- Fix all issues
- Update tests if needed
- Rebase on develop before merge

---

## Quality Gates

### Gate 1: Pre-Development

- [ ] Business rules frozen
- [ ] Architecture frozen
- [ ] Module ownership assigned
- [ ] Test data prepared

### Gate 2: Pre-Merge

- [ ] Code complete
- [ ] Tests passing
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] No linting errors

### Gate 3: Pre-Release

- [ ] All business rules implemented
- [ ] >80% test coverage
- [ ] All integration tests passing
- [ ] UAT successful
- [ ] Zero critical bugs
- [ ] Performance tests passing

---

## Continuous Improvement

### Retrospective

After each sprint:
- What went well?
- What could be improved?
- Action items for next sprint

### Code Quality Metrics

Track:
- Code coverage %
- Number of bugs
- Number of exceptions
- Performance metrics
- Review turnaround time

### Documentation Updates

Update this document when:
- New patterns discovered
- Better practices identified
- Standards need clarification

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-31 | OSDuo Tech LLP | Initial code review standards |

**Approved By:** ___________________  
**Date:** ___________________

**Next Review:** After Sprint 3

---

*This document is maintained in the repository and updated as standards evolve.*
