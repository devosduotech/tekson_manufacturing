# Phase 1 Implementation Hardening Plan

**Document ID:** MES-IHP-001  
**Version:** 1.1  
**Date:** August 3, 2026  
**Status:** Active  
**Owner:** Technical Lead  

---

## Phase 1 Implementation Principle

> **Prefer ERPNext Standard over Custom Code. Customize only where Teksons' manufacturing process cannot be achieved through ERPNext configuration or standard workflows.**

**Rationale:**
- Leverages ERPNext's proven manufacturing engine
- Reduces custom code maintenance
- Ensures upgrade compatibility
- Maintains Teksons' operational differentiation where it matters

**Decision Framework:**
For every implementation decision, ask:
1. Is ERPNext already doing this?
2. Can we configure ERPNext instead?
3. Is this business intelligence rather than inventory logic?
4. Does this justify customization?

---

## ERPNext vs MES Responsibility Matrix

| Responsibility | ERPNext | MES | Notes |
|----------------|---------|-----|-------|
| **Inventory Management** | ✅ | ❌ | ERPNext owns all stock transactions |
| **Costing & Valuation** | ✅ | ❌ | ERPNext standard costing |
| **Backflush Consumption** | ✅ | ❌ | ERPNext consumes BOM qty from WIP |
| **Stock Ledger Entries** | ✅ | ❌ | Never modify SLE directly |
| **Bin Quantities** | ✅ | ❌ | Never modify Bin directly |
| **GL Entries** | ✅ | ❌ | Never create GL entries |
| **Material Readiness** | ❌ | ✅ | MES evaluates WIP availability |
| **Dependency Validation** | ❌ | ✅ | MES validates operation sequence |
| **Production Sequencing** | ❌ | ✅ | MES controls JC start workflow |
| **Department Visibility** | ❌ | ✅ | MES provides shop-floor intelligence |
| **Diagnostics** | ❌ | ✅ | MES provides production messages |
| **Shop Floor UI** | ❌ | ✅ | MES provides operator interface |
| **Work Order Lifecycle** | ✅ | ❌ | ERPNext status auto-updates |
| **Manufacture Entry** | ✅ | ❌ | ERPNext creates Stock Entry |

**Key Principle:** MES = Business Intelligence Layer, NOT Inventory Engine

---

## ERPNext Boundaries (Never Override)

The MES **must NEVER**:

- ❌ Modify Stock Ledger Entries directly
- ❌ Calculate valuation or costing
- ❌ Modify Bin quantities directly
- ❌ Create GL Entries
- ❌ Bypass ERPNext manufacturing validation
- ❌ Override ERPNext Work Order status logic
- ❌ Create custom inventory tracking parallel to ERPNext

**When inventory operations are needed:**
```
Call ERPNext standard APIs
    ↓
Let ERPNext handle transactions
    ↓
MES reads results for intelligence
```

---

## MES Business Intelligence Layer

The MES provides **information and workflow orchestration**, not inventory ownership:

### Intelligence Provided
- ✅ Ready to Start status
- ✅ Awaiting Material alerts
- ✅ Awaiting Previous Operation status
- ✅ Material Shortage diagnostics
- ✅ Transfer suggestions
- ✅ Supervisor dashboards
- ✅ Production visibility
- ✅ Dependency status

### Workflow Orchestration
- ✅ JC Start validation
- ✅ JC Complete workflow
- ✅ Dependency refresh
- ✅ Material readiness evaluation
- ✅ Department workflow enforcement

---

## Hook Responsibility Contract

All hooks follow this pattern:

```
ERPNext Hook
    ↓
Receive Event (before_insert, validate, on_submit, etc.)
    ↓
Call Service (single line delegation)
    ↓
Exit (no business logic in hook)
```

**Hook Implementation Rules:**
- ❌ No SQL queries in hooks
- ❌ No business rules in hooks
- ❌ No calculations in hooks
- ❌ No inventory logic in hooks
- ✅ Only delegate to Service layer
- ✅ Keep hooks under 10 lines of code

**Example:**
```python
def validate_job_card_start(doc, method=None):
    """Hook: Job Card validate event"""
    if doc.is_new() or doc.flags.ignore_validate:
        return
    
    # Delegate to service (no logic here)
    from tekson_manufacturing.utils.job_card_utils import validate_job_card_start
    validate_job_card_start(doc)
```

---

## Executive Summary

The Phase 1 MES has completed feature development and validated the core architecture. This document defines the transition from **feature development** to **implementation hardening** leading to Customer UAT.

**Current State:**
- ✅ Business Process Frozen (v1.0)
- ✅ Architecture Frozen (v1.1)
- ✅ Core Modules Implemented
- ✅ Department WIP + Backflush Validated (2026-08-03)
- 🔄 Integration & Stabilization Needed

**Target State:**
- ✅ Zero Python exceptions
- ✅ All hooks working
- ✅ All server scripts migrated
- ✅ End-to-end workflows validated
- ✅ Ready for Customer UAT

---

## Implementation Gates & Waves

### Gate 1 – Framework Stable
**Prerequisite for Wave 2**

**Exit Criteria:**
- ✅ No ImportError exceptions
- ✅ No hook failures
- ✅ All services load correctly
- ✅ All 8 server scripts disabled
- ✅ Configuration validated
- ✅ Clean error logs

**Approval:** Technical Lead sign-off required before Wave 2

---

### Gate 2 – Workflow Stable
**Prerequisite for Wave 3**

**Exit Criteria:**
- ✅ All 6 workflows pass
- ✅ No critical defects
- ✅ Material Readiness working (100% accuracy)
- ✅ Backflush verified (consumes exact BOM qty)
- ✅ Excess material reuse validated

**Approval:** Project Manager sign-off required before Wave 3

---

## Implementation Waves

### Wave 1 – Stabilization + Server Script Migration + Configuration (2–3 days)

**Objective:** Eliminate all implementation regressions, migrate legacy server scripts, and validate configuration.

**Tasks:**

#### Stabilization
1. Fix import issues (e.g., `WorkOrderService`)
2. Remove obsolete imports from Sprint refactoring
3. Remove dead code from old server script migration
4. Ensure all service classes instantiate correctly
5. Validate all hooks execute without errors

#### Server Script Migration
Replace all legacy server scripts with custom app services:

| Old Server Script | Business Purpose | New Service | Status |
|-------------------|------------------|-------------|--------|
| First Operation Initialization | Initialize first JC | `JobCardService.allocate_workstation()` | ✅ Migrated |
| Job Card Start Validation | Material check | `validate_job_card_start()` hook | ✅ Migrated |
| Refresh Dependency | Dependency update | `DependencyEngine.refresh()` | ✅ Migrated |
| WO Completion | Last JC completion | `ExecutionEngine.complete_work_order()` | ✅ Migrated |
| Material Status | Readiness display | `MaterialReadinessEngine.evaluate_material_readiness()` | ✅ Migrated |
| Job Card Material Availability | WIP stock check | `MaterialReadinessEngine` | ✅ Migrated |
| JC Start Control Validation | Previous JC check | `DependencyEngine.validate_previous_operation()` | ✅ Migrated |
| Allocate Workstation (Round Robin) | Workstation assignment | `JobCardService.allocate_workstation()` | ✅ Migrated |

#### Configuration Validation
Checklist:
- ✅ Manufacturing Settings
- ✅ Company Defaults
- ✅ Warehouses (6 Department WIP + Stores + FG)
- ✅ Workstations (with plant_floor)
- ✅ Plant Floors (CNC, RA, Ralu In, Ralu Weld, RP, W)
- ✅ BOMs (with operations)
- ✅ Routing
- ✅ Item Defaults

**Exit Criteria:**
- ✅ No ImportError exceptions
- ✅ No hook failures
- ✅ All services load correctly
- ✅ All 8 server scripts disabled
- ✅ Configuration validated
- ✅ Clean error logs

---

### Wave 2 – Workflow Integration & Validation (3–4 days)

**Objective:** Validate complete manufacturing workflows using actual Teksons BOMs, with priority on Material Shortage scenario.

**Workflow Tests (in priority order):**

#### WF-006: Production Priority Change (Validates No-Reservation Model)
```
WO-1 Released
    ↓
Planner changes priority
    ↓
WO-2 Released
    ↓
Stores transfers material to WIP
    ↓
Production starts WO-2 (higher priority)
    ↓
WO-1 remains waiting (Material Readiness = Not Ready)
    ↓
Later: WO-1 resumes when material available
```

**Acceptance:**
- ✅ Material Readiness reflects current Department WIP (real-time)
- ✅ No reservation conflicts (first-come, first-consume)
- ✅ ERPNext Backflush works correctly for both WOs
- ✅ Priority change handled without system issues

**Rationale:** Validates why we rejected inventory reservation

---

#### WF-002: Material Shortage Flow (CRITICAL - Test First)

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
- ✅ Backflush consumes exact BOM qty
- ✅ Excess remains in WIP

---

#### WF-002: Material Shortage Flow (CRITICAL - Test First)
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

#### WF-005: Excess Material Reuse (Validates Inventory Model)
```
Stores
    ↓
Transfer 30.0 kg to WIP
    ↓
WO-1: Produce 30 Fins
    ↓
Backflush: Consumes 6.45 kg
    ↓
Remaining: 23.55 kg in WIP
    ↓
WO-2: Material Readiness Check
    ↓
Ready: 23.55 kg available
```

**Acceptance:**
- ✅ Remaining WIP stock immediately available for next WO
- ✅ No material return to Stores required
- ✅ No reservation required
- ✅ ERPNext Backflush consumes only BOM qty
- ✅ Department WIP = operational inventory

---

**Exit Criteria:**
- ✅ All 6 workflows pass
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

### Wave 5 – Internal UAT (2–3 days)

**Objective:** Ensure each service has single, clear responsibility and follows architectural contracts.

**Implementation Contract:**

```
Services may call Repositories
Repositories must never call Services
Hooks should call Services only
No business logic inside Hooks
```

**Service Boundaries:**

#### MaterialReadinessService
**Should Answer:**
- Can production start?
- Why not?
- What is missing?

**Should NOT:**
- Track inventory (ERPNext responsibility)
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

**ERPNext Boundary Validation:**

For every service method, ask:
1. Is ERPNext already doing this?
2. Can we configure ERPNext instead?
3. Is this business intelligence rather than inventory logic?

**Exit Criteria:**
- ✅ Each service has single responsibility
- ✅ Clear delegation between services
- ✅ No circular dependencies
- ✅ Service interfaces documented
- ✅ No ERPNext functionality duplicated

---

### Wave 5A – Business Freeze Validation (0.5 day)

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

### Wave 6 – Customer UAT Preparation (1 day)

**Validation Checklist:**

#### Business Process Alignment
- ✅ Planner flow matches BUSINESS_PROCESS_FREEZE_v1.0
- ✅ Stores flow matches frozen process
- ✅ Production flow matches frozen process
- ✅ QC flow matches frozen process
- ✅ Department WIP model validated
- ✅ ERPNext Backflush model validated

#### Operational Decisions Compliance
- ✅ OD-003: Material Transfer for Manufacture
- ✅ OD-004: Department WIP as Operational Inventory
- ✅ OD-005: ERPNext Backflush for Consumption
- ✅ OD-025: WO Status is Informational
- ✅ OA-001: Concurrent JC Starts assumption accepted

**Exit Criteria:**
- ✅ All business rules match frozen documentation
- ✅ No scope drift detected
- ✅ Architecture principles followed

---

### Wave 6A – Business Freeze Validation (0.5 day)

**Objective:** Confirm no implementation has changed the agreed business process.

**Validation Checklist:**

#### Business Process Alignment
- ✅ Planner flow matches BUSINESS_PROCESS_FREEZE_v1.0
- ✅ Stores flow matches frozen process
- ✅ Production flow matches frozen process
- ✅ QC flow matches frozen process
- ✅ Department WIP model validated
- ✅ ERPNext Backflush model validated

#### Operational Decisions Compliance
- ✅ OD-003: Material Transfer for Manufacture
- ✅ OD-004: Department WIP as Operational Inventory
- ✅ OD-005: ERPNext Backflush for Consumption
- ✅ OD-025: WO Status is Informational
- ✅ OA-001: Concurrent JC Starts assumption accepted

**Exit Criteria:**
- ✅ All business rules match frozen documentation
- ✅ No scope drift detected
- ✅ Architecture principles followed

---

### Wave 7 – Customer UAT Preparation (1 day)

**Objective:** Prepare environment and materials for Customer UAT.

**Tasks:**
1. Switch to Production Mode
2. Create UAT test data (actual WOs)
3. Prepare user training materials
4. Set up UAT tracking spreadsheet
5. Schedule UAT sessions with users
6. Calculate UAT Readiness Score

**Customer UAT Readiness Scorecard:**

| Area | Weight | Score (0-100) | Weighted |
|------|--------|---------------|----------|
| Workflow Validation (5 workflows pass) | 30% | TBD | TBD |
| Functional Defects (0 critical) | 20% | TBD | TBD |
| Performance (< 2 sec per operation) | 15% | TBD | TBD |
| Stability (no crashes in 100 operations) | 15% | TBD | TBD |
| User Experience (clear messages) | 10% | TBD | TBD |
| Documentation (complete & accurate) | 10% | TBD | TBD |

**Minimum Score Before Customer UAT:** ≥ 90%

**Exit Criteria:**
- ✅ Production Mode enabled
- ✅ Test data ready
- ✅ Users trained
- ✅ UAT schedule confirmed
- ✅ Readiness Score ≥ 90%

---

## Known Accepted Limitations (Phase 1 Design Choices)

These are **intentional design decisions**, not defects:

| Limitation | Rationale | Target Phase |
|------------|-----------|--------------|
| No inventory reservation | First-come, first-consume model matches operations | Phase 2 (if needed) |
| Concurrent JC starts not synchronized | Operationally rare; ERPNext safety net exists | Phase 2 (if needed) |
| No Stores Picking List | Operational efficiency, not MES core | Phase 1.1 |
| No Consolidated Material Issue | Operational efficiency | Phase 1.1 |
| No barcode scanning | Productivity improvement | Phase 2 |
| No mobile/handheld UI | Future enhancement | Phase 2 |
| Limited department transfer automation | Approved workflow only | Phase 2 |

**Note:** These limitations were explicitly deferred to maintain Phase 1 focus and will be evaluated post-UAT.

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Import errors during UAT | Low | High | Wave 1 stabilization |
| Server script functionality lost | Medium | High | Wave 2 traceability matrix |
| Backflush not working as expected | Low | High | Already validated (2026-08-03) |
| Concurrent JC starts cause issues | Low | Medium | Monitor during UAT, enhance if needed |
| User confusion on terminology | Medium | Low | Clear training materials |
| Performance issues with large BOMs | Low | Medium | Profile during Wave 5 |

---

## Success Metrics

### Technical Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Python Exceptions | 0 | TBD |
| Hook Failures | 0 | TBD |
| Server Scripts Disabled | 8 | 5 disabled |
| Workflow Tests Pass | 100% | TBD |
| Code Lines Removed | 500+ | TBD |
| Service Review Complete | 4 services | TBD |

### Business Metrics (Critical for UAT)

| Metric | Target | Current |
|--------|--------|---------|
| Material Readiness Accuracy | 100% | TBD |
| False JC Start Approvals | 0 | TBD |
| False JC Start Blocks | 0 | TBD |
| Backflush Accuracy | 100% | TBD |
| Department WIP Balance Accuracy | 100% | TBD |
| Manual Interventions Required | 0 | TBD |
| WO Completion Accuracy | 100% | TBD |
| Parent/Child Synchronization | 100% | TBD |
| Dependency Validation Accuracy | 100% | TBD |
| Diagnostic Message Accuracy | 100% | TBD |

### Internal UAT Pass Criteria

| Scenario | Target |
|----------|--------|
| WF-001: Standard Production | ✅ Pass |
| WF-002: Material Shortage | ✅ Pass (CRITICAL) |
| WF-003: Sub-Assembly | ✅ Pass |
| WF-004: Partial Production | ✅ Pass |
| WF-005: Excess Material Reuse | ✅ Pass |

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

## Phase 1 Architecture Freeze

The following architectural components are **FROZEN** and shall not be modified without approved change request:

- ✅ Repository Pattern
- ✅ Service Layer
- ✅ Department WIP Model
- ✅ ERPNext Backflush
- ✅ Material Readiness Engine
- ✅ Dependency Engine
- ✅ Execution Engine
- ✅ Diagnostics Framework
- ✅ ERPNext Inventory Ownership Principle

**Rationale:** Protects the project during implementation and UAT, preventing architectural drift.

---

## Phase 1 Success Definition

Phase 1 is considered **COMPLETE** when:

1. ✅ All workflow validations pass (6/6 workflows)
2. ✅ Internal UAT passes (all scenarios)
3. ✅ Customer UAT completes successfully (sign-off received)
4. ✅ No critical or high-priority defects remain
5. ✅ The agreed business process is executable without manual workaround
6. ✅ Customer UAT Readiness Score ≥ 90%

This provides a **single completion criterion** for management.

---

## Governance

**Change Control:**
From this point onward, every change must be justified by:
1. A defect found during internal testing, OR
2. Feedback received during customer UAT, OR
3. Formally approved change request

**No new features** will be added until after Customer UAT sign-off.

**Daily Standup:**
- Review Wave progress
- Identify blockers
- Update success metrics
- Verify against Implementation Gates

**Weekly Report:**
- Wave completion status
- Defects found/fixed
- Risk status
- UAT readiness score
- Architecture compliance

---

## Phase 1 Closure

After Customer UAT sign-off:

1. **Code Freeze:**
   - Tag Git Release: `v1.0.0`
   - Archive implementation documents
   - Lock develop branch (production only)

2. **Documentation:**
   - Update Technical Debt register
   - Prepare Phase 1 Lessons Learned
   - Archive UAT test results

3. **Transition:**
   - Open Phase 1 Enhancement Backlog
   - Start Phase 2 planning
   - Handover to operations team

4. **Celebration:**
   - Team recognition
   - Customer sign-off ceremony
   - Project closure report

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Aug 3, 2026 | Project Team | Initial implementation hardening plan |
| 1.1 | Aug 3, 2026 | Project Team | Added 10 refinements, gates, workflows, metrics |
| | | | |

**Next Review:** After Wave 2 (Workflow Integration & Validation)  
**Status:** ✅ **FROZEN** (changes only via approved change request)

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
