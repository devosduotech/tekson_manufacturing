# MES Decision Log

**Document Type:** Design Decision Register  
**Version:** 1.0  
**Date:** 2026-08-01  
**Status:** Active  
**Project:** Tekson Manufacturing MES  

---

## Overview

This document records all significant architectural and design decisions made during the MES implementation. Each decision includes context, alternatives considered, and rationale.

---

## Decision Log

### Decision 001: Service-Oriented Architecture

**Date:** 2026-07-31  
**Category:** Architecture  
**Status:** ✅ Implemented

**Title:** 5-Layer Service-Oriented Architecture

**Context:**
Need to separate business logic from ERPNext implementation details for maintainability and future migration.

**Decision:**
Implement 5-layer architecture:
1. API Layer (whitelisted methods)
2. Service Layer (business orchestration)
3. Engine Layer (business logic)
4. Repository Layer (data access)
5. ERPNext ORM (database)

**Alternatives Considered:**
- Direct ERPNext customization (Rejected: tight coupling)
- 3-layer architecture (Rejected: insufficient separation)

**Rationale:**
- Clear separation of concerns
- Easy ERPNext version migration
- Testable business logic
- Reusable services

**Impact:**
- All code follows this pattern
- Repository and Service interfaces frozen

---

### Decision 002: Department-Centric Warehouse Model

**Date:** 2026-07-31  
**Category:** Architecture  
**Status:** ✅ Implemented

**Title:** Department Warehouses Instead of Operation Warehouses

**Context:**
Initial design considered operation-specific warehouses, but this doesn't match physical shop floor reality.

**Decision:**
Use department-centric warehouses:
- WIP-W, WIP-RA, WIP-RP, WIP-CNC, WIP-Ralu Weld, WIP-Ralu In
- Materials move between departments, not operations

**Alternatives Considered:**
- Operation-specific warehouses (Rejected: excessive transfers)
- Single WIP warehouse (Rejected: no department tracking)

**Rationale:**
- Matches physical material flow
- Reduces unnecessary stock transfers
- Enables department-level reporting
- Simpler configuration

**Impact:**
- Warehouse architecture frozen
- All material movements follow this pattern

---

### Decision 003: Stores-Production Handoff (MR-010)

**Date:** 2026-07-31  
**Category:** Business Rules  
**Status:** ✅ Implemented

**Title:** Stores Transfers Materials Before Production Starts

**Context:**
Need clear separation between Stores and Production responsibilities.

**Decision:**
Stores must transfer materials to Department Warehouse before Job Cards can start.

**Alternatives Considered:**
- Production requests materials on-demand (Rejected: delays)
- Automatic material reservation (Rejected: complex)

**Rationale:**
- Clear accountability separation
- Stores control inventory issuance
- Production focuses on manufacturing
- Material readiness based on actual stock

**Impact:**
- MR-010 frozen as core business rule
- Material Readiness Engine implements this logic

---

### Decision 004: Cumulative Availability (MR-011)

**Date:** 2026-07-31  
**Category:** Business Rules  
**Status:** ✅ Implemented

**Title:** Multiple Transfers Allowed with Cumulative Check

**Context:**
Large Work Orders may receive materials in multiple partial transfers.

**Decision:**
Validate cumulative quantity across all Stock Entries, not single transfer.

**Alternatives Considered:**
- Single transfer required (Rejected: inflexible)
- Manual consolidation (Rejected: error-prone)

**Rationale:**
- Flexibility for Stores
- Production starts when sufficient material available
- Reflects real-world material issuance
- Supports batch transfers

**Impact:**
- MR-011 frozen as core business rule
- get_cumulative_transferred_qty() implements this

---

### Decision 005: Repository Pattern for Data Access

**Date:** 2026-08-01  
**Category:** Architecture  
**Status:** ✅ Implemented

**Title:** All Data Access Through Repositories

**Context:**
Need to isolate ERPNext database operations from business logic.

**Decision:**
All database operations go through Repository layer. Services and Engines must NOT use frappe.db directly.

**Alternatives Considered:**
- Direct frappe.db in services (Rejected: tight coupling)
- Active Record pattern (Rejected: less testable)

**Rationale:**
- Isolates ERPNext dependencies
- Easier testing with mocks
- Clear separation of concerns
- Future ERP migration easier

**Impact:**
- 4 repositories implemented
- All services use repositories
- No direct frappe.db in services/engines

---

### Decision 006: Business Rule-Driven Implementation

**Date:** 2026-07-31  
**Category:** Implementation Strategy  
**Status:** ✅ Implemented

**Title:** Implement by Business Rules, Not DocTypes

**Context:**
Traditional ERP implementations organize by DocType (Job Card, Work Order, etc.).

**Decision:**
Organize implementation by business rules (MR-010, DV-001, etc.) with traceability to code and tests.

**Alternatives Considered:**
- DocType-driven (Rejected: scattered business logic)
- Module-driven (Rejected: unclear ownership)

**Rationale:**
- Clear business value per sprint
- Complete traceability
- Easier UAT validation
- Business-friendly organization

**Impact:**
- 10 sprints organized by business rules
- MES_IMPLEMENTATION_MATRIX.md traces rules to code to tests

---

### Decision 007: No Version Numbering Until UAT

**Date:** 2026-07-31  
**Category:** Release Strategy  
**Status:** Active

**Title:** Version 1.0 Only After Successful UAT

**Context:**
Premature version numbering creates false expectations.

**Decision:**
No version numbers (1.0, 1.1, etc.) until after successful UAT and bug fixes. Use sprint numbers during development.

**Alternatives Considered:**
- Semantic versioning from start (Rejected: premature)
- Date-based versioning (Rejected: unclear)

**Rationale:**
- Avoids commitment to untested features
- Focus on functionality over version numbers
- Clear "production ready" milestone

**Impact:**
- Development versions use sprint numbers
- Version 1.0 reserved for post-UAT release

---

### Decision 008: Documentation Baseline Frozen

**Date:** 2026-08-01  
**Category:** Governance  
**Status:** Active

**Title:** Freeze Documentation Version 1.0

**Context:**
Continuous documentation changes during implementation create confusion.

**Decision:**
Freeze all business and technical specifications as Version 1.0 on 2026-08-01. Only living documents (status, tracking) can change.

**Alternatives Considered:**
- Continuous updates (Rejected: moving target)
- No freezing (Rejected: scope creep)

**Rationale:**
- Stable baseline for development
- Clear change management
- Prevents scope creep
- Easier impact analysis

**Impact:**
- 22 documents frozen as v1.0
- Change requests required for modifications
- Living documents updated after each sprint

---

### Decision 009: Weighted Sprint Planning

**Date:** 2026-08-01  
**Category:** Project Management  
**Status:** Active

**Title:** Weight Sprints by Effort, Not Equal

**Context:**
Sprint 6 (46 exceptions) is significantly larger than Sprint 2 (2 rules).

**Decision:**
Weight sprints by effort:
- Sprint 6: 20% (largest)
- Sprint 9: 4% (smallest)
- Others: 8-13%

**Alternatives Considered:**
- Equal weight per sprint (Rejected: misleading)
- Story points (Rejected: too granular)

**Rationale:**
- Realistic progress tracking
- Better resource allocation
- Accurate completion percentage

**Impact:**
- Overall progress: 35% (weighted)
- Not 30% (equal sprints)

---

### Decision 010: Integration Tracking Separate from Implementation

**Date:** 2026-08-01  
**Category:** Quality Assurance  
**Status:** Active

**Title:** Track "Implemented" vs "Integrated" Separately

**Context:**
Code implemented doesn't mean integrated and tested with other components.

**Decision:**
Track implementation and integration separately in MES_INTEGRATION_MATRIX.md.

**Alternatives Considered:**
- Single status (Rejected: hides integration gaps)
- Integration after all implementation (Rejected: late discovery)

**Rationale:**
- Early integration issue detection
- Clear integration testing plan
- Realistic readiness assessment

**Impact:**
- Integration matrix created
- Each sprint includes integration tests
- "Integrated" status tracked separately

---

## Decision Categories

| Category | Count | Examples |
|----------|-------|----------|
| Architecture | 4 | Service-Oriented, Repository Pattern |
| Business Rules | 2 | MR-010, MR-011 |
| Implementation Strategy | 1 | Business Rule-Driven |
| Release Strategy | 1 | No Version Until UAT |
| Governance | 1 | Documentation Baseline |
| Project Management | 1 | Weighted Sprints |
| Quality Assurance | 1 | Integration Tracking |
| **Total** | **11** | |

---

## Pending Decisions

| ID | Title | Category | Sprint | Status |
|----|-------|----------|--------|--------|
| D-012 | Exception Handling Strategy | Business Rules | Sprint 6 | ⏳ Pending |
| D-013 | Security Role Configuration | Security | Sprint 7 | ⏳ Pending |
| D-014 | UI Framework Selection | UI | Sprint 8 | ⏳ Pending |
| D-015 | Performance Optimization Approach | Performance | Sprint 10 | ⏳ Pending |

---

## Decision Change Process

To modify a decision:

1. **Submit Change Request:** Document proposed change
2. **Impact Analysis:** Assess impact on implementation
3. **Technical Review:** Review by Technical Lead
4. **Approval:** Business/Technical approval
5. **Update Decision Log:** Record new decision with version
6. **Communicate:** Notify all stakeholders

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-01 | Development | Initial creation with 11 decisions |

---

## Related Documents

- DOCUMENTATION_GOVERNANCE.md - Decision management policy
- PHASE1_STATUS_REPORT.md - Project status
- TECHNICAL_DEBT.md - Technical debt items
- CHANGELOG.md - Implementation history
