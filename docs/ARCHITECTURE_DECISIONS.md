# Architecture Decisions

**Document Type:** Architecture Reference  
**Version:** 1.0  
**Date:** 2026-08-01  
**Status:** Frozen  
**Project:** Tekson Manufacturing MES  

---

## Overview

This document captures the technical rationale behind key architectural choices for the Tekson Manufacturing MES implementation.

**Purpose:** Explain WHY we chose this architecture, not just WHAT the architecture is.

**Audience:** Developers, Technical Leads, Future Maintainers, V16 Migration Team

---

## Decision 1: Repository Pattern

### Decision

Use Repository Pattern for all data access instead of direct ERPNext ORM calls.

### Alternatives Considered

1. **Direct ORM Access:** `frappe.get_doc()` in services and engines
2. **Active Record Pattern:** ERPNext DocType methods
3. **Repository Pattern:** Encapsulated data access layer

### Rationale

**Chosen: Repository Pattern**

**Reasons:**

1. **Testability:** Repositories can be mocked for unit testing
   ```python
   # With Repository Pattern - Easy to test
   repo_mock = Mock(spec=JobCardRepository)
   service = JobCardService()
   service._repo = repo_mock
   # Test without database
   
   # Without Repository - Hard to test
   # Requires database for every test
   ```

2. **Separation of Concerns:** Data access separate from business logic
   ```python
   # Repository: HOW to get data
   repo.get_by_name("JC-2026-001")
   
   # Service: WHAT to do with data
   service.start_job_card("JC-2026-001")
   ```

3. **ERP Version Independence:** Repository layer abstracts ERPNext API changes
   ```python
   # V15: frappe.get_doc()
   # V16: frappe.db.get_value() or new API
   # Repository implementation changes, service code unchanged
   ```

4. **Single Responsibility:** Each repository handles one entity type
   - JobCardRepository: Job Cards only
   - WorkOrderRepository: Work Orders only
   - StockRepository: Stock Entries only

5. **Consistent Interface:** All repositories follow same pattern
   ```python
   repo.get_by_name(name)
   repo.get_list(filters)
   repo.create(data)
   repo.update(name, data)
   repo.delete(name)
   ```

### Impact

- **Positive:** Easier testing, cleaner code, future-proof
- **Negative:** More files, slight learning curve
- **Mitigation:** Repository Coverage Matrix documents all repositories

### Status

✅ Implemented (Sprints 1-3)  
🔒 Frozen Interface (4 repositories)

---

## Decision 2: Service Layer

### Decision

Implement Service Layer between Engines and Repositories.

### Alternatives Considered

1. **Two-Layer Architecture:** Engines → Repositories
2. **Three-Layer Architecture:** Engines → Services → Repositories
3. **Transaction Script:** All logic in hooks.py

### Rationale

**Chosen: Three-Layer Architecture (Engines → Services → Repositories)**

**Reasons:**

1. **Business Logic Separation:**
   - **Engines:** Pure business logic, no ERP dependencies
   - **Services:** ERP integration, transaction management
   - **Repositories:** Data access only

2. **Event Handler Simplicity:**
   ```python
   # hooks.py - Simple delegation
   def on_job_card_update(doc, method):
       service = JobCardService()
       service.process_job_card_completion(doc)
   
   # NOT 50 lines of business logic in hooks.py
   ```

3. **Reusability:** Services can be called from multiple contexts
   - Event handlers
   - API endpoints
   - Scheduled jobs
   - Manual execution

4. **Transaction Management:** Services handle transactions
   ```python
   @frappe.whitelist()
   def process_department_transfer(work_order):
       frappe.db.begin()
       try:
           # Multiple operations
           frappe.db.commit()
       except Exception:
           frappe.db.rollback()
           raise
   ```

5. **Testability:** Services can be tested independently
   - Mock repositories
   - Test service logic
   - Verify ERP interactions

### Impact

- **Positive:** Clean architecture, testable, maintainable
- **Negative:** More layers, more files
- **Mitigation:** Clear interface definitions, coding standards

### Status

✅ Implemented (Sprints 1-3)  
🔒 Frozen Interface (3 services)

---

## Decision 3: Department Warehouse Model

### Decision

Use Department-based WIP warehouses (WIP-W, WIP-RA, WIP-RP, etc.) instead of Operation-based warehouses.

### Alternatives Considered

1. **Operation-Based Warehouses:** One warehouse per operation (Welding-Op1, Welding-Op2, etc.)
2. **Department-Based Warehouses:** One warehouse per department (WIP-W, WIP-RA, etc.)
3. **Single WIP Warehouse:** All WIP in one warehouse with operation tracking

### Rationale

**Chosen: Department-Based Warehouses**

**Reasons:**

1. **Teksons Process Match:** Aligns with physical factory layout
   - Welding Department (W)
   - Rail Assembly Department (RA)
   - Rail Polish Department (RP)
   - CNC Department
   - Ralu Weld Department
   - Ralu In Department

2. **Simplified Material Tracking:**
   ```python
   # Department Model: Track material in department warehouse
   warehouse = "WIP-W"  # Welding department
   
   # Operation Model: Track material in operation warehouse
   warehouse = "WIP-Welding-Op10"  # Too granular
   ```

3. **Reduced Warehouse Count:**
   - Department Model: 6 department warehouses
   - Operation Model: 50+ operation warehouses (impractical)

4. **Easier Transfers:**
   ```python
   # Department Transfer: W → RA
   Stock Entry from "WIP-W" to "WIP-RA"
   
   # Operation Transfer: Complex routing
   # Multiple transfers within same department
   ```

5. **Job Card Flexibility:** Operations can be reordered within department without warehouse changes
   - Operation 10 → 20 → 30 (all in WIP-W)
   - No warehouse reconfiguration needed

6. **Reporting Simplicity:**
   - WIP by Department: Easy (query warehouse)
   - WIP by Operation: Job Card based (not warehouse based)

### Impact

- **Positive:** Matches physical layout, simpler, scalable
- **Negative:** Less granular warehouse tracking
- **Mitigation:** Job Cards track operations, warehouses track departments

### Status

✅ Implemented (Sprints 1-3)  
🔒 Frozen (6 department warehouses defined)

---

## Decision 4: Cumulative Material Readiness

### Decision

Evaluate material readiness cumulatively (parent WO completed qty + current stock) instead of current stock only.

### Alternatives Considered

1. **Stock-Only Check:** Check current warehouse stock
2. **Cumulative Check:** Current stock + parent WO completed qty
3. **Full Supply Chain Check:** Stock + parent WO + purchase orders + production orders

### Rationale

**Chosen: Cumulative Check (Current Stock + Parent WO Completed)**

**Reasons:**

1. **Parent-Child WO Relationship:**
   ```python
   # Parent WO produces component
   # Child WO consumes component
   # Child availability depends on parent completion
   
   available_qty = (
       current_stock 
       + parent_wo_completed_qty  # Critical!
       - reserved_qty
   )
   ```

2. **Accurate Availability:**
   - Stock-only: Shows shortage even when parent is producing
   - Cumulative: Shows true availability including parent output

3. **Prevents False Negatives:**
   ```python
   # Example:
   # Child WO needs 100 units
   # Current stock: 20 units
   # Parent WO completed: 80 units
   # Stock-only check: SHORTAGE (20 < 100) ❌
   # Cumulative check: READY (20 + 80 = 100) ✅
   ```

4. **Business Rule MR-011:**
   - Cumulative availability check
   - Includes parent WO output
   - Accurate readiness assessment

5. **Reduces Manual Intervention:**
   - No need to manually adjust stock for parent output
   - System automatically includes parent completion

### Impact

- **Positive:** Accurate availability, fewer false shortages
- **Negative:** More complex calculation
- **Mitigation:** MaterialReadinessEngine encapsulates logic

### Status

✅ Implemented (Sprint 1 - MR-011)  
🔒 Frozen (Business Rule MR-011)

---

## Decision 5: Diagnostics Separation

### Decision

Separate Diagnostics & Messages (Sprint 4) from Execution Engine (Sprint 3) instead of combining them.

### Alternatives Considered

1. **Combined:** Execution engine handles diagnostics and messages
2. **Separate Sprint:** Dedicated sprint for diagnostics framework
3. **Utility Functions:** Diagnostic functions in utils/

### Rationale

**Chosen: Separate Sprint (Diagnostics Framework)**

**Reasons:**

1. **Separation of Concerns:**
   - **Execution Engine:** Business logic (JC-001 to JC-005, WO-001, WO-002)
   - **Diagnostics:** User messages, error formatting, UI integration

2. **Reusability:**
   ```python
   # Diagnostics used by multiple components
   diagnostics.format_error(exception)  # Used by Execution, Validation, Readiness
   diagnostics.build_user_message(rule)  # Used by all engines
   ```

3. **UI Integration:**
   - Diagnostics layer handles ERPNext UI formatting
   - Execution layer remains UI-agnostic
   - Easier to update UI without changing business logic

4. **Business Rules DM-001 to DM-004:**
   - DM-001: Diagnostic message builders
   - DM-002: Error categorization
   - DM-003: UI message formatting
   - DM-004: Message logging

5. **Testability:**
   - Test execution logic separately
   - Test message formatting separately
   - Mock diagnostics for execution tests

### Impact

- **Positive:** Cleaner separation, reusable, testable
- **Negative:** Extra sprint, more code
- **Mitigation:** Diagnostics framework benefits all subsequent sprints

### Status

📋 Planned (Sprint 4)  
🔒 Frozen (Business Rules DM-001 to DM-004)

---

## Decision 6: Department-Based WIP Model

### Decision

Track WIP by Department (via warehouse) and Operation (via Job Card) instead of single tracking method.

### Alternatives Considered

1. **Warehouse-Only Tracking:** Track WIP location in warehouse only
2. **Job Card-Only Tracking:** Track WIP progress in Job Card only
3. **Dual Tracking:** Warehouse (department) + Job Card (operation)

### Rationale

**Chosen: Dual Tracking (Warehouse + Job Card)**

**Reasons:**

1. **Physical + Logical Tracking:**
   - **Warehouse:** Where is the material physically? (Department)
   - **Job Card:** What operation is being performed? (Operation)

2. **Material Tracking:**
   ```python
   # Physical Location
   material_location = "WIP-W"  # Welding department
   
   # Logical Progress
   operation_status = "Op 20 Complete, Op 30 In Progress"
   ```

3. **WIP Valuation:**
   - Warehouse stock for financial valuation
   - Job Card progress for production reporting

4. **Exception Handling:**
   - Material in wrong warehouse → Exception
   - Operation out of sequence → Exception
   - Both checks required for complete validation

5. **Reporting:**
   - WIP by Department: Warehouse query
   - WIP by Operation: Job Card query
   - Combined: Full WIP visibility

### Impact

- **Positive:** Complete visibility, accurate tracking
- **Negative:** More complex validation
- **Mitigation:** Validation engine (Sprint 2) handles dual checks

### Status

✅ Implemented (Sprints 1-3)  
🔒 Frozen (Architecture decision)

---

## Decision 7: 5-Layer Architecture

### Decision

Use 5-layer architecture (API → Services → Engines → Repositories → ERPNext ORM) instead of simpler patterns.

### Alternatives Considered

1. **3-Layer:** Hooks → Services → ORM (simpler)
2. **4-Layer:** Hooks → Services → Repositories → ORM (common)
3. **5-Layer:** API → Services → Engines → Repositories → ORM (chosen)

### Rationale

**Chosen: 5-Layer Architecture**

**Reasons:**

1. **Engine Layer Benefits:**
   - Pure business logic (no ERP dependencies)
   - Easily testable (mock repositories)
   - Reusable across contexts (API, events, scheduled jobs)

2. **Service Layer Benefits:**
   - ERP integration (transactions, permissions, events)
   - API endpoints (whitelisted methods)
   - Event handlers (hooks.py delegation)

3. **Clear Responsibilities:**
   ```
   API Layer      → HTTP endpoints, UI integration
   Service Layer  → ERP integration, transactions
   Engine Layer   → Business logic, validation
   Repository     → Data access, ORM abstraction
   ERPNext ORM    → Database operations
   ```

4. **Scalability:**
   - Add new engines without changing services
   - Add new services without changing engines
   - Independent testing of each layer

5. **V16 Migration Path:**
   - Only Repository layer changes for V16
   - Engines, Services, API remain unchanged

### Impact

- **Positive:** Clean architecture, testable, maintainable, future-proof
- **Negative:** More complex, more files, learning curve
- **Mitigation:** Architecture documentation, coding standards

### Status

✅ Implemented (Sprints 1-3)  
🔒 Frozen (Architecture foundation)

---

## Decision 8: Exception Handling Framework

### Decision

Implement comprehensive Exception Handling Framework (Sprint 6) with 46 scenarios instead of ad-hoc error handling.

### Alternatives Considered

1. **Ad-Hoc Handling:** Try/except in each function
2. **Centralized Handler:** Single exception handler
3. **Comprehensive Framework:** Exception hierarchy + handlers + logging (chosen)

### Rationale

**Chosen: Comprehensive Framework**

**Reasons:**

1. **Consistent Error Messages:**
   ```python
   # Ad-Hoc: Inconsistent
   raise Exception("Error")
   raise MESValidationError("Validation failed")
   raise frappe.FrappeError("Frappe error")
   
   # Framework: Consistent
   raise MESMaterialError("MR-010", context)
   raise MESDependencyError("DV-001", context)
   raise MESExecutionError("JC-001", context)
   ```

2. **Business Rule Traceability:**
   - Each exception references business rule
   - Easy to identify violated rule
   - Audit trail for compliance

3. **User-Friendly Messages:**
   - Technical exception → User message
   - Context included (work order, job card, items)
   - Actionable guidance

4. **Logging Integration:**
   - All exceptions logged centrally
   - Stack trace preserved
   - Business rule context included

5. **46 Scenarios Covered:**
   - Material errors
   - Dependency errors
   - Execution errors
   - Configuration errors
   - Validation errors
   - Permission errors

### Impact

- **Positive:** Consistent, traceable, user-friendly
- **Negative:** More code, upfront investment
- **Mitigation:** Exception handling rules documented, framework reusable

### Status

📋 Planned (Sprint 6)  
🔒 Frozen (46 scenarios defined)

---

## Decision 9: Security Framework

### Decision

Implement Security Framework (Sprint 7) with department-scoped permissions instead of ERPNext default permissions.

### Alternatives Considered

1. **ERPNext Default Permissions:** Role-based only
2. **Custom Permissions:** Department + Role based (chosen)
3. **No Permissions:** Open access (not considered)

### Rationale

**Chosen: Department + Role Based Permissions**

**Reasons:**

1. **Teksons Requirement:** Department managers see only their department
   ```python
   # Welding Manager
   - Can see: WIP-W warehouse, Welding Job Cards
   - Cannot see: WIP-RA warehouse, RA Job Cards
   
   # ERPNext Default: Role-based only (no department scope)
   # Custom: Role + Department scope
   ```

2. **10 Roles Defined:**
   - MES Administrator
   - Production Manager
   - Department Manager (W, RA, RP, CNC, Ralu)
   - Stores Manager
   - Quality Manager
   - Operator
   - Viewer

3. **75 Permissions Matrix:**
   - Read, Write, Submit, Cancel for each DocType
   - Department scope enforced
   - Warehouse scope enforced

4. **Security Rules:**
   - Department managers restricted to their department
   - Stores managers restricted to Stores warehouses
   - Production managers have cross-department visibility

### Impact

- **Positive:** Granular security, data isolation, compliance
- **Negative:** Complex permission setup
- **Mitigation:** Security matrix documented, automated setup

### Status

📋 Planned (Sprint 7)  
🔒 Frozen (10 roles, 75 permissions defined)

---

## Decision 10: Sprint-Based Implementation

### Decision

Implement in 10 sprints (Sprint 1-10) with business rule groups instead of monolithic development.

### Alternatives Considered

1. **Monolithic:** Build all features, then test
2. **Module-Based:** Build by module (Material, Execution, Quality)
3. **Sprint-Based:** Build by business rule groups (chosen)

### Rationale

**Chosen: Sprint-Based Implementation**

**Reasons:**

1. **Incremental Delivery:**
   - Sprint 1: Material Readiness (MR-010, MR-011) ✅
   - Sprint 2: Dependency Validation (DV-001, DV-002) ✅
   - Sprint 3: Execution Engine (JC-*, WO-*) ✅
   - Sprint 4-10: Remaining features

2. **Early Testing:**
   - Each sprint tested independently
   - Integration tested after each sprint
   - Issues found early

3. **Business Rule Traceability:**
   - Each sprint implements specific business rules
   - Clear what's done vs. pending
   - Easy to track progress

4. **Flexibility:**
   - Sprint priorities can be adjusted
   - Business rules can be reprioritized
   - Minimal impact on completed sprints

5. **Weighted Effort Tracking:**
   - Sprint 1: 10% effort
   - Sprint 2: 10% effort
   - Sprint 3: 15% effort
   - ...
   - Total: 100% effort

### Impact

- **Positive:** Incremental, testable, trackable
- **Negative:** More planning overhead
- **Mitigation:** Implementation matrix tracks sprint progress

### Status

✅ In Progress (Sprints 1-3 complete, 4-10 planned)  
🔒 Frozen (Sprint boundaries defined)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-01 | Development | Initial architecture decisions documentation |

---

## Related Documents

- DECISION_LOG.md - Design decisions (operational)
- MES_ARCHITECTURE_OVERVIEW.md - Architecture description
- BUSINESS_RULES_SPECIFICATION.md - Business rules
- MES_IMPLEMENTATION_MATRIX.md - Sprint tracking

---

## Notes

**This document vs. DECISION_LOG.md:**

| Aspect | ARCHITECTURE_DECISIONS.md | DECISION_LOG.md |
|--------|---------------------------|-----------------|
| Focus | Technical architecture rationale | Operational design decisions |
| Audience | Architects, Tech Leads, Future maintainers | Developers, Project team |
| Content | WHY we chose this architecture | WHAT decisions were made |
| Update Frequency | Rarely (only major architecture changes) | Regularly (each sprint) |
| Examples | Repository Pattern, Service Layer, Department Warehouse | Version policy, File structure, Naming |

**Both documents complement each other:**
- ARCHITECTURE_DECISIONS.md: Deep technical rationale
- DECISION_LOG.md: Operational decision tracking
