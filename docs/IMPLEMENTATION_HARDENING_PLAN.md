# Phase 1 Implementation Hardening Plan

**Document ID:** MES-IHP-001  
**Version:** 1.0  
**Date:** August 3, 2026  
**Status:** Active  
**Owner:** Technical Lead  

---

## Executive Summary

The Phase 1 MES has completed feature development and validated the core architecture. This document defines the transition from **feature development** to **implementation hardening** leading to Customer UAT.

**Current State:**
- ✅ Business Process Frozen (v1.0)
- ✅ Architecture Frozen (v1.1)
- ✅ Core Modules Implemented
- ✅ Department WIP + Backflush Validated
- 🔄 Integration & Stabilization Needed

**Target State:**
- ✅ Zero Python exceptions
- ✅ All hooks working
- ✅ All server scripts migrated
- ✅ End-to-end workflows validated
- ✅ Ready for Customer UAT

---

## Implementation Waves

### Wave 1 – Stabilization (1–2 days)

**Objective:** Eliminate all implementation regressions.

**Tasks:**
1. Fix `WorkOrderService` import issues
2. Remove obsolete imports from Sprint refactoring
3. Remove dead code from old server script migration
4. Ensure all service classes instantiate correctly
5. Validate all hooks execute without errors

**Exit Criteria:**
- ✅ No ImportError exceptions
- ✅ No hook failures
- ✅ All services load correctly
- ✅ Clean error logs

---

### Wave 2 – Server Script Migration (2–3 days)

**Objective:** Replace all legacy server scripts with custom app services.

**Legacy Server Script Traceability Matrix:**

| Old Server Script | Business Purpose | New Service | Status | Verified |
|-------------------|------------------|-------------|--------|----------|
| First Operation Initialization | Initialize first JC | `JobCardService.allocate_workstation()` | ✅ Migrated | ⬜ |
| Job Card Start Validation | Material check | `validate_job_card_start()` hook | ✅ Migrated | ⬜ |
| Refresh Dependency | Dependency update | `DependencyEngine.refresh()` | ✅ Migrated | ⬜ |
| WO Completion | Last JC completion | `ExecutionEngine.complete_work_order()` | ✅ Migrated | ⬜ |
| Material Status | Readiness display | `MaterialReadinessEngine.evaluate_material_readiness()` | ✅ Migrated | ⬜ |
| Job Card Material Availability | WIP stock check | `MaterialReadinessEngine` | ✅ Migrated | ⬜ |
| JC Start Control Validation | Previous JC check | `DependencyEngine.validate_previous_operation()` | ✅ Migrated | ⬜ |
| Allocate Workstation (Round Robin) | Workstation assignment | `JobCardService.allocate_workstation()` | ✅ Migrated | ⬜ |

**Exit Criteria:**
- ✅ All 8 server scripts disabled
- ✅ All business rules verified in new services
- ✅ No functionality lost in migration
- ✅ Traceability matrix complete

---

### Wave 3 – End-to-End Integration (3–5 days)

**Objective:** Validate complete manufacturing workflows using actual Teksons BOMs.

**Workflow Tests:**

#### WF-001: Standard Production Flow
```
Planner → Release WO
    ↓
Stores → Material Transfer for Manufacture
    ↓
WIP → Material Available
    ↓
Production → Start JC → Complete JC
    ↓
MES → Create Manufacture Entry
    ↓
ERPNext → Backflush (consume BOM qty)
    ↓
ERPNext → WO Completed
```

**Acceptance:**
- ✅ WO status: Submitted → In Process → Completed
- ✅ JC Start blocked if WIP insufficient
- ✅ Backflush consumes exact BOM qty
- ✅ Excess remains in WIP

---

#### WF-002: Material Shortage Flow
```
WO Released
    ↓
WIP Empty
    ↓
Production → Try Start JC
    ↓
MES → BLOCKED
    ↓
Diagnostic → "Material not available in WIP"
    ↓
Stores → Transfer to WIP
    ↓
Refresh
    ↓
MES → Ready
    ↓
Production → Start JC
```

**Acceptance:**
- ✅ JC Start blocked with clear message
- ✅ No production begins without material
- ✅ After transfer, JC becomes ready
- ✅ Diagnostic messages user-friendly

---

#### WF-003: Sub-Assembly Flow
```
Child WO (Fin) → Complete
    ↓
Backflush → Child WIP
    ↓
Parent WIP Updated
    ↓
Parent JC → Material Ready
    ↓
Parent JC → Start
```

**Acceptance:**
- ✅ Child output to parent dept WIP
- ✅ Parent material readiness updates
- ✅ Multi-level BOM coordination

---

#### WF-004: Partial Production Flow
```
WO: 60 Fins
    ↓
Produce: 30 Fins
    ↓
WO Status: In Process
    ↓
Planner: Revise to 30
    ↓
WO Status: Completed
```

**Acceptance:**
- ✅ Partial production tracked
- ✅ WO remains In Process
- ✅ Quantity revision works
- ✅ WO completes on revised qty

---

**Exit Criteria:**
- ✅ All 4 workflows pass
- ✅ Using actual Teksons BOMs (R215 series)
- ✅ No manual workarounds needed
- ✅ All diagnostics clear

---

### Wave 4 – Code Simplification (1–2 days)

**Objective:** Remove obsolete code now that Backflush is validated.

**Code to Remove:**
- ❌ Custom inventory calculations
- ❌ Custom consumption logic
- ❌ Duplicate stock tracking
- ❌ Reservation code (if any)
- ❌ Temporary UAT workarounds
- ❌ Dead code from Sprint refactoring

**Files to Review:**
- `tekson_manufacturing/readiness/material_readiness.py`
- `tekson_manufacturing/execution/execution_engine.py`
- `tekson_manufacturing/services/stock_service.py`
- `tekson_manufacturing/utils/` (all utilities)

**Exit Criteria:**
- ✅ Codebase simplified
- ✅ No duplicate calculations
- ✅ Clear responsibility boundaries
- ✅ All tests still pass

---

### Wave 5 – Service Review (1 day)

**Objective:** Ensure each service has single, clear responsibility.

**Service Boundaries:**

#### MaterialReadinessService
**Should Answer:**
- Can production start?
- Why not?
- What is missing?

**Should NOT:**
- Track inventory
- Create Stock Entries
- Manage WO status

---

#### ExecutionEngine
**Should Manage:**
- JC Completion workflow
- Refresh dependencies
- Refresh material readiness
- Last JC detection
- Create Manufacture Entry

**Should NOT:**
- Validate material (delegates to MaterialReadiness)
- Check dependencies (delegates to DependencyEngine)

---

#### DependencyEngine
**Should Manage:**
- Previous operation validation
- Next operation identification
- Parent/Child WO coordination

**Should NOT:**
- Check material availability
- Create Stock Entries

---

#### StockService
**Should Do:**
- Create Material Transfer
- Create Manufacture Entry (via ExecutionEngine)
- Department Transfer

**Should NOT:**
- Calculate consumption (ERPNext Backflush)
- Track reservations

---

**Exit Criteria:**
- ✅ Each service has single responsibility
- ✅ Clear delegation between services
- ✅ No circular dependencies
- ✅ Service interfaces documented

---

### Wave 6 – Internal UAT (2–3 days)

**Objective:** Execute realistic production scenarios with actual Teksons products.

**Test Products:**
- R215 External Fin For CAC
- R215 CAC Core
- R215 Combi Cooler (final assembly)

**Scenarios:**
1. Single WO production (Fin Forming)
2. Multi-level BOM (Core + Fin → Assembly)
3. Multiple WOs sharing WIP inventory
4. Priority change mid-production
5. Partial production + quantity revision

**Exit Criteria:**
- ✅ All scenarios pass
- ✅ Using actual BOMs
- ✅ Performance acceptable (< 2 sec per operation)
- ✅ User messages clear

---

### Wave 7 – Customer UAT Preparation (1 day)

**Objective:** Prepare environment and materials for Customer UAT.

**Tasks:**
1. Switch to Production Mode
2. Create UAT test data (actual WOs)
3. Prepare user training materials
4. Set up UAT tracking spreadsheet
5. Schedule UAT sessions with users

**Exit Criteria:**
- ✅ Production Mode enabled
- ✅ Test data ready
- ✅ Users trained
- ✅ UAT schedule confirmed

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Import errors during UAT | Low | High | Wave 1 stabilization |
| Server script functionality lost | Medium | High | Wave 2 traceability matrix |
| Backflush not working as expected | Low | High | Already validated (2026-08-03) |
| Concurrent JC starts cause issues | Low | Medium | Monitor during UAT, enhance if needed |
| User confusion on terminology | Medium | Low | Clear training materials |
| Performance issues with large BOMs | Low | Medium | Profile during Wave 6 |

---

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Python Exceptions | 0 | TBD |
| Hook Failures | 0 | TBD |
| Server Scripts Disabled | 8 | 5 disabled |
| Workflow Tests Pass | 100% | TBD |
| Code Lines Removed | 500+ | TBD |
| Service Review Complete | 4 services | TBD |
| Internal UAT Pass | 5 scenarios | TBD |

---

## Timeline

| Wave | Duration | Start Date | End Date |
|------|----------|------------|----------|
| 1 - Stabilization | 1-2 days | Aug 4 | Aug 5 |
| 2 - Server Script Migration | 2-3 days | Aug 5 | Aug 7 |
| 3 - End-to-End Integration | 3-5 days | Aug 7 | Aug 11 |
| 4 - Code Simplification | 1-2 days | Aug 11 | Aug 12 |
| 5 - Service Review | 1 day | Aug 12 | Aug 12 |
| 6 - Internal UAT | 2-3 days | Aug 12 | Aug 14 |
| 7 - Customer UAT Prep | 1 day | Aug 14 | Aug 14 |
| **Customer UAT** | **5 days** | **Aug 18** | **Aug 22** |

---

## Governance

**Change Control:**
From this point onward, every change must be justified by:
1. A defect found during internal testing, OR
2. Feedback received during customer UAT

**No new features** will be added until after Customer UAT sign-off.

**Daily Standup:**
- Review Wave progress
- Identify blockers
- Update success metrics

**Weekly Report:**
- Wave completion status
- Defects found/fixed
- Risk status
- UAT readiness score

---

## Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Project Manager | | | |
| Technical Lead | | | |
| Customer Representative | | | |

---

**Document Status:** ✅ **ACTIVE**  
**Next Review:** After Wave 3 (End-to-End Integration)
