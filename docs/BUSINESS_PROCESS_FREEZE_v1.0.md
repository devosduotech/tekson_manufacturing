# Phase 1 MES Functional Scope Freeze

**Document ID:** MES-PH1-FS-001  
**Version:** 1.0  
**Date:** August 2, 2026  
**Status:** ✅ **FROZEN**  
**Effective Until:** Customer UAT Sign-off + 30 days  

---

## Executive Summary

This document formally declares the **Phase 1 MES Functional Scope as FROZEN**. No new business enhancements will be introduced until Internal Integration Testing, Internal UAT, Customer UAT, and feedback review are complete.

**Freeze Rationale:**
- ✅ Functional scope has converged to stable model
- ✅ All major architectural decisions made
- ✅ Risk of analysis paralysis identified
- ✅ Implementation must begin for empirical validation

**Important Note:**
The term "Functional Scope Frozen" is used deliberately. The business process itself may evolve slightly during UAT based on real manufacturing observations. What is frozen includes:
- ✅ Functional Scope
- ✅ Architecture
- ✅ Business Rules
- ✅ Interfaces

Bug fixes and small workflow refinements discovered during UAT are still allowed and expected.

---

## Frozen Business Process

### 1. Manufacturing Flow (FROZEN)

```
Planner
    │
    ├─ Create Production Plan
    ├─ Review Work Orders
    └─ Release Work Orders
    │
    ▼
Stores Incharge
    │
    ├─ Review Released WOs
    ├─ Material Transfer for Manufacture
    │  (Raw Material / BOF → Department WIP)
    │  ⚠️ ERPNext: Sets WO status = "In Process"
    └─ No reservation, no allocation
    │
    ▼
Department WIP Warehouse
    │
    ├─ Becomes Source of Truth
    ├─ Operational Inventory (Production owns after transfer)
    └─ Excess remains available for future WOs
    │
    ▼
Material Readiness Engine
    │
    ├─ Check: Available Stock in WIP >= Required
    ├─ No reservation logic
    ├─ Real-time evaluation
    └─ First-come, first-consume
    │
    ▼
Production Engineer / Supervisor
    │
    ├─ Start First Job Card (if material ready)
    │  ⚠️ MES: Blocked if materials unavailable
    ├─ Execute remaining Job Cards (sequence enforced)
    └─ Decide priority dynamically
    │
    ▼
Execution Engine
    │
    ├─ On JC Complete: Refresh dependencies
    ├─ On JC Complete: Refresh material readiness
    ├─ On JC Complete: Update diagnostics
    ├─ On Last JC: Create Manufacture Stock Entry
    │  ⚠️ ERPNext Backflush: Consumes ONLY BOM qty
    ├─ On Last JC: Update Work Order
    └─ On Last JC: Refresh parent WO readiness
    │
    ▼
If Sub-Assembly
    │
    └─ Output to Parent Department WIP
       ↓
       Parent Job Card becomes Ready
    │
    ▼
If Finished Good
    │
    └─ Output to Finished Goods Store
       ↓
       Work Order Completed (ERPNext auto)
       ↓
       Production Plan updated
```

**Key Validation (Internal Test 2026-08-03):**
- ✅ Transfer 30.0 kg to WIP
- ✅ Produce 30 Fins (requires 6.45 kg)
- ✅ Backflush consumes 6.45 kg
- ✅ **23.55 kg remains in WIP** (available for next WO)

**Status:** ✅ **FROZEN** - No changes until post-UAT review

---

## 2. Business Rules (FROZEN)

### Material Readiness Engine

| Rule ID | Rule Name | Status |
|---------|-----------|--------|
| MR-010 | Stores transfers materials to Department WIP before production starts | ✅ FROZEN |
| MR-011 | Cumulative availability check across multiple Stock Entries | ✅ FROZEN |
| MR-012 | Department WIP Balance evaluation | ✅ FROZEN |
| MR-013 | Department WIP Live Availability Evaluation | ✅ FROZEN |
| MR-014 | Department WIP as Source of Truth | ✅ FROZEN |
| MR-015 | Live evaluation at Job Card start | ✅ FROZEN |
| MR-016 | Partial Production Readiness | ✅ FROZEN |

### Work Order Management

| Rule ID | Rule Name | Status |
|---------|-----------|--------|
| WO-001 | Auto-complete when all Job Cards complete | ✅ FROZEN |
| WO-002 | Duplicate Manufacture Entry prevention | ✅ FROZEN |
| WO-003 | Safety net for manual WO completion | ✅ FROZEN |
| WO-004 | Parent WO refresh on child completion | ✅ FROZEN |
| WO-005 | Multi-level BOM support | ✅ FROZEN |
| WO-006 | WO completion only on planned qty or revision | ✅ FROZEN |
| WO-007 | Department WIP Ownership | ✅ FROZEN |

### Job Card Execution

| Rule ID | Rule Name | Status |
|---------|-----------|--------|
| JC-001 | Previous operation validation | ✅ FROZEN |
| JC-002 | Quantity completion validation | ✅ FROZEN |
| JC-003 | Material readiness check | ✅ FROZEN |
| JC-004 | Auto-refresh dependent Job Cards | ✅ FROZEN |
| JC-005 | Work Order link required | ✅ FROZEN |
| JC-006 | Workstation auto-assignment | ✅ FROZEN |
| JC-007 | Item visibility (custom_item_code) | ✅ FROZEN |
| JC-008 | Quantity visibility | ✅ FROZEN |

### Dependency Validation

| Rule ID | Rule Name | Status |
|---------|-----------|--------|
| DV-001 | Previous operation complete validation | ✅ FROZEN |
| DV-002 | Sequence continuity validation | ✅ FROZEN |

### Warehouse Management

| Rule ID | Rule Name | Status |
|---------|-----------|--------|
| WH-001 | Department-centric warehouse structure | ✅ FROZEN |
| WH-002 | Plant Floor to Warehouse mapping | ✅ FROZEN |
| WH-003 | Multi-department flow support | ✅ FROZEN |
| WH-004 | WIP Warehouse naming convention | ✅ FROZEN |
| WH-005 | Department WIP as operational inventory | ✅ FROZEN |

**Status:** ✅ **ALL RULES FROZEN** - 24 business rules locked

---

## 3. Organizational Responsibilities (FROZEN)

| Role | Responsibilities | Authority |
|------|----------------|-----------|
| **Planner** | Production Plan, WO release, priority changes, qty revisions | Controls plan, not execution |
| **Stores Incharge** | Material Transfer to WIP, returns when requested | Supplies departments, not individual JCs |
| **Production Engineer/Supervisor** | Department WIP inventory, JC execution, priority decisions, scrap handling | Owns departmental inventory after transfer |
| **MES (System)** | Material Readiness, Dependency validation, Diagnostics, JC workflow, WO completion | Adds execution intelligence |

**Status:** ✅ **FROZEN** - Clear separation of duties

---

## 4. ERPNext Configuration (FROZEN)

| Feature | Configuration | Reason |
|---------|---------------|--------|
| Skip Material Transfer | **NO** | Department WIP is central to MES |
| WIP Warehouse | **YES** (6 dept-specific) | Department tracking required |
| Standard Backflush | **YES** | Consume only actual production qty |
| Material Readiness | **CUSTOM** | Based on WIP availability, not transfer history |
| Reservation | **NO** | First-come, first-consume model |
| Consumption Logic | **STANDARD ERPNext** | BOM explosion on Manufacture Entry |

**Status:** ✅ **FROZEN** - No ERPNext configuration changes

---

## 4.1 Architectural Principle

**PRINCIPLE-001: MES Augments ERPNext, Does Not Replace**

> **The MES shall augment ERPNext Manufacturing, not replace it.**

**Implementation:**
- ✅ Use: Standard Work Orders, Job Cards, Stock Entries, BOM Explosion, Backflush
- ✅ Custom: Material Readiness, Dependency Validation, Diagnostics, Department Workflow
- ❌ Avoid: Custom WO/JC doctypes, custom consumption logic, custom inventory movements

**Rationale:**
- Leverage ERPNext's standard manufacturing capabilities
- Add only execution intelligence that Teksons needs
- Minimize customizations for easier upgrades
- Maintain compatibility with ERPNext V16+

**Owner:** Technical Lead  
**Status:** ✅ **FUNDAMENTAL PRINCIPLE**

---

## 5. Custom Fields (FROZEN)

### Job Card Custom Fields

| Field | Category | Owner | Status |
|-------|----------|-------|--------|
| custom_item_code | C (Display) | Hooks | ✅ FROZEN |
| custom_actual_production_item | C (Display) | Hooks | ✅ FROZEN |
| custom_start_status | A (Business) | JobCardService | ✅ FROZEN |
| custom_dependency_status | A (Business) | JobCardService | ✅ FROZEN |
| custom_can_start_operation | B (System) | JobCardService | ✅ FROZEN |
| custom_dependency_check | B (System) | JobCardService | ✅ FROZEN |
| custom_material_available_for_operation | B (System) | JobCardService | ✅ FROZEN |
| custom_material_status_details | C (Display) | Service | ✅ FROZEN |
| custom_plant_floor | C (Display) | Hooks | ✅ FROZEN |

**Status:** ✅ **FROZEN** - 9 fields, no additions until post-UAT

---

## 6. Deferred Features (Enhancement Backlog)

| ID | Feature | Priority | Target Phase | Reason for Deferral |
|----|---------|----------|--------------|---------------------|
| EH-001 | Stores Picking List | High | Phase 1.1 | Operational efficiency, not MES core |
| EH-002 | Consolidated Material Issue | High | Phase 1.1 | Operational efficiency |
| EH-003 | Department Material Replenishment Dashboard | Medium | Phase 1.1 | Efficiency enhancement |
| EH-004 | Barcode Material Issue | Medium | Phase 2 | Productivity improvement |
| EH-005 | Handheld Shop Floor Interface | Low | Phase 2 | Future enhancement |
| EH-006 | Planner Production Buckets | Low | Phase 2 | Planning enhancement |
| EH-007 | Dynamic WO Consolidation | Low | Phase 2 | Advanced planning |
| EH-008 | Scrap Management Workflow | Medium | Phase 2 | Quality/Inventory enhancement |
| EH-009 | Rework Job Card Flow | Low | Phase 2 | Quality enhancement |
| EH-010 | Management Priority Override Status | Low | Phase 2 | Workflow enhancement |

**Status:** ✅ **DOCUMENTED** - All new ideas captured, not implemented

---

## 7. Change Control Policy (EFFECTIVE IMMEDIATELY)

### Not Allowed During Freeze

- ❌ New business features
- ❌ New workflow changes
- ❌ New custom fields (unless fixing critical defect)
- ❌ New document types
- ❌ New reports (unless required for UAT execution)
- ❌ New dashboards
- ❌ Process redesign
- ❌ Architecture changes

### Allowed During Freeze

- ✅ Bug fixes
- ✅ Logic corrections
- ✅ Integration fixes
- ✅ Performance improvements
- ✅ UI usability improvements (that do not alter business process)
- ✅ Customer UAT defect resolution
- ✅ Critical security fixes
- ✅ ERPNext compatibility fixes

### Change Request Process

1. **Identify Change** → Log in Issue Tracker
2. **Classify** → Bug Fix (allowed) or Enhancement (deferred)
3. **If Bug Fix** → Implement, Test, Deploy
4. **If Enhancement** → Add to Enhancement Backlog, Defer to Phase 1.1 or Phase 2
5. **Document** → Update change log

---

## 8. UAT Validation Scope (FROZEN)

### In Scope for Phase 1 UAT

- ✅ Material Readiness Engine
- ✅ Dependency Validation
- ✅ Job Card Execution (Start → Complete)
- ✅ Department WIP workflow
- ✅ ERPNext Backflush (Manufacture Entry)
- ✅ Work Order completion
- ✅ Parent/Child WO synchronization
- ✅ Diagnostics Framework
- ✅ Security Framework
- ✅ Department Transfers
- ✅ Multi-level BOM support
- ✅ Custom Fields population
- ✅ Workstation auto-assignment
- ✅ Material Transfer to WIP

### Out of Scope for Phase 1 UAT

- ❌ Stores Picking List
- ❌ Consolidated Material Issue
- ❌ Barcode scanning
- ❌ Handheld devices
- ❌ Advanced planning buckets
- ❌ Scrap workflow
- ❌ Rework flow
- ❌ Management override status

---

## 9. Exit Criteria for Freeze

The freeze will be lifted when **ALL** of the following are complete:

1. ✅ Internal Integration Testing complete (100% pass rate)
2. ✅ Internal UAT complete (all 10 scenarios pass)
3. ✅ Customer UAT complete (sign-off received)
4. ✅ Feedback reviewed and prioritized
5. ✅ Enhancement Backlog reviewed with stakeholders
6. ✅ Phase 1.1 / Phase 2 planning complete

**Expected Date:** [To be determined based on UAT schedule]

---

## 10. Known Limitations (Documented for UAT)

| Limitation | Workaround | Target Resolution |
|------------|------------|-------------------|
| No Stores Picking List | Stores opens individual WOs or uses temporary report | Phase 1.1 |
| No consolidated material issue | Manual consolidation by Stores | Phase 1.1 |
| No barcode scanning | Manual item entry | Phase 2 |
| No handheld interface | Desktop/laptop only | Phase 2 |
| No dynamic priority override | Management communicates verbally to Production | Phase 2 |
| Excess material remains in WIP | Production decides to keep or return | Working as designed |
| No reservation system | First-come, first-consume | Working as designed |
| Scrap requires manual Stock Entry | Create Material Transfer to Scrap Store | Phase 2 |

---

## 11. Approval & Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Project Manager | | | |
| Technical Lead | | | |
| Functional Consultant | | | |
| Customer Representative | | | |

**Next Review Date:** After Customer UAT Sign-off

---

## 12. Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Aug 2, 2026 | AI Assistant | Initial freeze declaration |
| | | | |

---

## Conclusion

**Phase 1 MES Business Process is now FROZEN.**

All implementation efforts must focus on delivering the agreed functionality. All new ideas, enhancements, and process improvements must be added to the **Enhancement Backlog** for post-UAT evaluation.

**Implementation Motto:**
> "Validate first, optimize later."

**Freeze Effective:** August 2, 2026  
**Freeze Lifts:** After Customer UAT Sign-off + 30 days  

---

**Document Status:** ✅ **ACTIVE**  
**Enforcement:** **MANDATORY** for all Phase 1 development
