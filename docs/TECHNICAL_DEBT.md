# Technical Debt Register

**Document Type:** Technical Debt Tracking  
**Version:** 1.0  
**Date:** 2026-08-01  
**Status:** Active  
**Project:** Tekson Manufacturing MES  

---

## Overview

This document tracks technical debt items identified during implementation. Each item is prioritized and scheduled for resolution.

---

## Technical Debt Items

### TD-001: Repository Layer Caching

**Priority:** Medium  
**Identified:** Sprint 1  
**Category:** Performance  
**Status:** ⏳ Deferred

**Description:**
Repository methods make direct database calls without caching. For frequently accessed data (warehouse mapping, department configuration), this could impact performance at scale.

**Current State:**
```python
def get_department_warehouse(self, work_order):
    warehouse = frappe.db.get_value(...)  # Direct DB call every time
```

**Recommended Fix:**
```python
@frappe.cache()
def get_department_warehouse(self, work_order):
    warehouse = frappe.db.get_value(...)
```

**Resolution Plan:**
- Implement caching in Sprint 7 (Security & Performance)
- Add cache invalidation on warehouse update
- Add performance monitoring

**Impact if Not Resolved:**
- Slower response times under high load
- Increased database load

---

### TD-002: Diagnostic Message API

**Priority:** Low  
**Identified:** Sprint 3  
**Category:** Code Quality  
**Status:** ⏳ Deferred

**Description:**
DiagnosticMessages class is used by ExecutionEngine but not fully integrated. Some diagnostic methods are stubs.

**Current State:**
```python
def build_material_shortage_message(self, shortage):
    # TODO: Implement full diagnostic message
    return {'type': 'warning', 'message': 'Material shortage'}
```

**Recommended Fix:**
- Complete all diagnostic message builders in Sprint 4
- Add unit tests for diagnostic generation
- Integrate with UI formatting

**Resolution Plan:**
- Sprint 4 (Diagnostics & Messages)

**Impact if Not Resolved:**
- Poor user experience
- Inconsistent error messages

---

### TD-003: Stock Query Optimization

**Priority:** High  
**Identified:** Sprint 1  
**Category:** Performance  
**Status:** ⏳ Deferred

**Description:**
`get_cumulative_transferred_qty()` uses raw SQL without indexes. May be slow with large Stock Entry volumes.

**Current State:**
```python
transfers = frappe.db.sql("""
    SELECT SUM(sed.qty) as qty
    FROM `tabStock Entry Detail` sed
    INNER JOIN `tabStock Entry` se ON sed.parent = se.name
    WHERE sed.item_code = %s
    AND se.work_order = %s
    ...
""", ...)
```

**Recommended Fix:**
- Add database index on `work_order` field in Stock Entry
- Add composite index on `(item_code, work_order)` in Stock Entry Detail
- Consider query optimization with EXPLAIN

**Resolution Plan:**
- Add to MES_MIGRATION_STRATEGY.md patches
- Implement in Sprint 10 (Performance Testing)

**Impact if Not Resolved:**
- Slow material readiness evaluation
- Timeout errors with large data volumes

---

### TD-004: Exception Handling Gaps

**Priority:** High  
**Identified:** Sprint 3  
**Category:** Completeness  
**Status:** ⏳ Deferred

**Description:**
46 exception scenarios defined in MES_EXCEPTION_HANDLING_RULES.md but not yet implemented. Current code has basic try-catch but no structured exception handling.

**Current State:**
```python
try:
    se = self.create_manufacture_stock_entry(wo)
except Exception as e:
    result['message'] = f"Error: {str(e)}"  # Generic handling
```

**Recommended Fix:**
- Implement structured exception handling in Sprint 6
- Create custom exception classes for each category
- Add exception logging and notification

**Resolution Plan:**
- Sprint 6 (Exception Handling Integration)

**Impact if Not Resolved:**
- Poor error handling in production
- Difficult debugging
- No exception tracking

---

### TD-005: Test Coverage Gaps

**Priority:** Medium  
**Identified:** Sprint 3  
**Category:** Testing  
**Status:** ⏳ Deferred

**Description:**
Current test coverage is 100% for implemented code, but integration tests are minimal. End-to-end scenarios not yet tested.

**Current State:**
- 33 unit tests (100% of implemented code)
- 0 integration tests
- 0 end-to-end tests

**Recommended Fix:**
- Add integration tests in Sprint 6
- Add end-to-end tests in Sprint 10
- Target >80% integration test coverage

**Resolution Plan:**
- Sprint 6: Integration tests for exceptions
- Sprint 10: Full end-to-end testing

**Impact if Not Resolved:**
- Integration bugs may slip to UAT
- Regression risk

---

### TD-006: Hardcoded Configuration Values

**Priority:** Low  
**Identified:** Sprint 1  
**Category:** Maintainability  
**Status:** ⏳ Deferred

**Description:**
Some configuration values are hardcoded instead of using MES Settings.

**Current State:**
```python
if jc.sequence_id == 1:  # Hardcoded
    # First operation logic
```

**Recommended Fix:**
- Move all configurable values to MES Settings
- Use constants from MES_CONFIGURATION_MATRIX.md
- Add configuration validation

**Resolution Plan:**
- Sprint 7 (Security & Configuration)

**Impact if Not Resolved:**
- Configuration changes require code changes
- Reduced flexibility

---

### TD-007: Logging Performance Overhead

**Priority:** Low  
**Identified:** Sprint 2  
**Category:** Performance  
**Status:** ⏳ Deferred

**Description:**
Every operation logs to frappe.log_error, which writes to database. High-frequency operations may create log table bloat.

**Current State:**
```python
log_mes_event(...)  # Called for every validation
```

**Recommended Fix:**
- Implement log level filtering
- Use async logging for non-critical events
- Add log rotation and cleanup

**Resolution Plan:**
- Sprint 7: Implement log level filtering
- Sprint 10: Add log cleanup scheduled job

**Impact if Not Resolved:**
- Large error_log table
- Slight performance overhead

---

## Technical Debt Summary

| Priority | Count | Status |
|----------|-------|--------|
| High | 2 | ⏳ Deferred |
| Medium | 2 | ⏳ Deferred |
| Low | 3 | ⏳ Deferred |
| **Total** | **7** | **All Deferred** |

## Resolution Schedule

| Sprint | Technical Debt Items |
|--------|---------------------|
| Sprint 4 | TD-002 (Diagnostics) |
| Sprint 6 | TD-004 (Exceptions), TD-005 (Integration Tests) |
| Sprint 7 | TD-001 (Caching), TD-006 (Configuration) |
| Sprint 10 | TD-003 (Query Optimization), TD-007 (Logging) |

---

## Prevention Strategy

To prevent new technical debt:

1. **Code Review Checklist:** Include technical debt check
2. **Definition of Done:** Must not introduce new debt without documentation
3. **Sprint Retrospectives:** Identify and document new debt items
4. **Refactoring Sprints:** Allocate 10% of each sprint to debt reduction

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-01 | Development | Initial creation |

---

## Related Documents

- CODE_REVIEW_STANDARDS.md - Development standards
- MES_PERFORMANCE_BUDGET.md - Performance targets
- MES_IMPLEMENTATION_MATRIX.md - Sprint planning
