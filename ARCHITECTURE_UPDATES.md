# Architecture Review Updates (Post Project Status Review)

**Document Type:** Architectural Decisions & Direction Changes  
**Version:** 1.0  
**Date:** 2026-07-31 (Post-Status Review)  
**Status:** Approved for Implementation  
**Supersedes:** Sections in UAT_REVIEW_ARCHITECTURE.md and PROJECT_TIMELINE.md

---

## Executive Summary

This document captures critical architectural decisions made **after** the initial project status review. These decisions refine the scope, reduce implementation risk, and establish clear boundaries between Planning and Execution layers.

**Key Decision:** The `tekson_manufacturing` custom application will focus **exclusively on Manufacturing Execution (MES)** in Phase 1, while Planning enhancements are deferred to Phase 2.

---

## 1. Clear Separation Between Planning and Manufacturing Execution

The project scope has been formally divided into two independent layers.

### 1.1 Phase 1 – Manufacturing Execution System (Current Scope)

**Focus:** Stabilizing and improving shop floor execution **after Work Orders are generated**.

**Scope Includes:**
- ✅ Material Readiness Engine
- ✅ Previous Operation Validation
- ✅ Material Availability Validation
- ✅ Warehouse Validation
- ✅ Job Card Execution
- ✅ Work Order Completion
- ✅ Manufacturing Traceability
- ✅ Operator Diagnostics

**Objective:** Make manufacturing execution reliable **without modifying ERPNext's Production Planning logic**.

---

### 1.2 Phase 2 – Manufacturing Planning Enhancements (Future Scope)

**Focus:** Planning improvements after execution is stable.

**Scope Will Include:**
- 📋 Production Bucket concept
- 📋 Enhanced Work Order consolidation
- 📋 Date-wise Work Order generation
- 📋 Planner Workbench
- 📋 Capacity-aware planning
- 📋 Production Release optimization

**Timeline:** After Phase 1 successful UAT completion.

---

## 2. Production Plan Will Remain Standard ERPNext Functionality

After reviewing ERPNext Production Planning in detail, it has been decided:

| Component | Decision |
|-----------|----------|
| Production Plan | ✅ Use standard ERPNext |
| MRP Logic | ✅ No replacement |
| BOM Explosion | ✅ No modifications |
| Purchase Planning | ✅ Unchanged |
| Work Order Generation | ✅ Standard ERPNext |

**Custom Application Boundary:** `tekson_manufacturing` begins responsibility **only after Work Orders are created**.

**Rationale:**
- Preserves upgrade compatibility
- Reduces implementation risk
- Leverages tested ERPNext functionality
- Allows future planning enhancements without breaking execution

---

## 3. Work Orders Become the Manufacturing Execution Boundary

The architectural boundary has been revised.

### Old Understanding
```
Production Plan
        ↓
Manufacturing Execution Begins
```

### Revised Architecture
```
Production Plan
        │
Generate Work Orders
        │
Draft Work Orders
        │
Planner submits Work Order
        │
──────────────────────────────
Manufacturing Execution Begins  ← tekson_manufacturing starts here
──────────────────────────────
        │
Material Readiness
        │
Execution
```

**Benefits:**
- Clean separation between Planning and Execution
- Clear responsibility boundaries
- Independent evolution of each layer
- Easier troubleshooting and support

---

## 4. Production Release Uses Standard ERPNext Workflow

It has been confirmed that ERPNext already provides an adequate release mechanism.

### Current Workflow (Sufficient)

```
Production Plan
        │
        ↓
Generates Work Orders (Draft)
        │
        ↓
Planner reviews Work Orders
        │
        ↓
Planner submits individual Work Orders
        │
        ↓
Submitted Work Orders available for execution
```

### Decision

A separate **Production Release document is NOT required**.

The existing **Draft → Submit** workflow is sufficient for Teksons' needs.

**Implementation Impact:**
- No custom doctype needed for Production Release
- Training focuses on standard ERPNext workflow
- Planner controls execution start timing via submission

---

## 5. Material Readiness Confirmed as Core Engine

Material Readiness is now confirmed as the **primary execution engine**.

### Responsibilities

| Function | Description |
|----------|-------------|
| Material Availability | Check cumulative transfers and stock |
| Previous Operation Completion | Validate routing sequence |
| Warehouse Readiness | Confirm WIP warehouse configuration |
| Material Transfer Validation | Verify transfers to WIP |
| Dependency Validation | Check sub-assembly availability |
| Diagnostic Messages | Provide actionable feedback |
| Operator Start Permission | Final gate before production |

### Execution Flow

```
Operator clicks "Start" on Job Card
        │
        ↓
Material Readiness Engine
        │
        ├─ Previous Operation Complete?
        ├─ Materials Available?
        ├─ Warehouse Configured?
        └─ Dependencies Met?
        │
        ↓
All YES → Allow Start
Any NO  → Show Diagnostic Message
```

**Every Job Card execution will pass through this validation layer.**

---

## 6. Planning Optimization Deferred to Phase 2

### Issue Identified

Current ERPNext behaviour consolidates Work Orders by item only, not by date.

**Example:**

| Date | Item | Qty |
|------|------|-----|
| 01-Aug | R215 | 10 |
| 01-Aug | R216 | 5 |
| 01-Aug | R217 | 5 |
| 02-Aug | R215 | 10 |
| 02-Aug | R217 | 5 |
| 02-Aug | R221 | 3 |

**Current Consolidation:**
```
Core A: 38 Nos (01-Aug)
```

**Desired Behaviour:**
```
Core A: 20 Nos (01-Aug)
Core A: 18 Nos (02-Aug)
```

### Decision

This enhancement has been:
- ✅ Accepted conceptually
- ⏸️ Postponed until Manufacturing Execution is complete

**Rationale:**
- Execution stability is higher priority
- Planning changes are more complex
- Can be added later without breaking execution
- Reduces Phase 1 scope and risk

---

## 7. Future Work Order Consolidation Strategy

The future planning engine (Phase 2) will consolidate Work Orders using:

### New Consolidation Key

```
(Item Code, Production Bucket)
```

Instead of:

```
(Item Code)
```

### Production Bucket Evolution

| Phase | Bucket Type |
|-------|-------------|
| Initial | Planned Production Date |
| Later | Daily Bucket |
| Later | Shift Bucket |
| Later | Campaign Bucket |
| Later | Planner-defined Batch |

**Benefits:**
- Reduces unnecessary WIP
- Preserves consolidation benefits
- Enables date-wise planning
- Supports capacity-aware scheduling

---

## 8. Phase 1 Exclusions (Planning Logic)

To minimize implementation risk, **Phase 1 will NOT include:**

| Component | Status | Reason |
|-----------|--------|--------|
| Production Plan customization | ❌ Excluded | Use standard ERPNext |
| BOM explosion changes | ❌ Excluded | Standard logic sufficient |
| Work Order generation changes | ❌ Excluded | Boundary starts after WO creation |
| Consolidation algorithm changes | ❌ Excluded | Phase 2 feature |
| MRP logic changes | ❌ Excluded | Standard ERPNext |

**Result:** Phase 1 implementation stays close to standard ERPNext while allowing future planning improvements.

---

## 9. Revised Project Roadmap

### Phase 1 – Manufacturing Execution (Current Focus)

**Duration:** 3-4 weeks  
**Priority:** Critical

- [ ] Material Readiness Engine
- [ ] Dependency Engine
- [ ] Warehouse Validation
- [ ] Material Consumption Validation
- [ ] Job Card Workflow
- [ ] Work Order Completion
- [ ] Traceability
- [ ] Diagnostics

**Entry Point:** Submitted Work Order  
**Exit Point:** Finished Goods Receipt

---

### Phase 2 – Manufacturing Planning (Future)

**Duration:** 6-8 weeks (after Phase 1)  
**Priority:** High

- [ ] Production Bucket
- [ ] Date-wise Work Order Consolidation
- [ ] Planner Workbench
- [ ] Capacity-aware Work Order Planning
- [ ] Production Release Optimization

**Entry Point:** Production Plan  
**Exit Point:** Submitted Work Order

---

### Phase 3 – Advanced Planning (Long-term)

**Duration:** 10-12 weeks (after Phase 2)  
**Priority:** Medium

- [ ] Capacity Planning
- [ ] Finite Scheduling
- [ ] Automatic Production Bucket Generation
- [ ] Shop Floor Load Balancing
- [ ] Planner Recommendations
- [ ] WIP Optimization

**Entry Point:** Demand Forecast  
**Exit Point:** Optimized Production Plan

---

## 10. Long-Term Product Vision

The project architecture has evolved into **two complementary systems**.

### 10.1 Manufacturing Planning System (MPS)

**Responsible For:**
- Production Planning
- Work Order Generation
- Production Buckets
- Capacity Planning
- Scheduling
- Work Order Consolidation

**Entry Point:** Demand (Sales Orders, Forecasts)  
**Exit Point:** Submitted Work Orders

**Tools:**
- ERPNext Production Plan (standard)
- Custom Planning Enhancements (Phase 2+)

---

### 10.2 Manufacturing Execution System (MES)

**Responsible For:**
- Material Readiness
- Shop Floor Execution
- Job Cards
- Material Validation
- Manufacturing Traceability
- Work Order Completion
- Operator Guidance

**Entry Point:** Submitted Work Order  
**Exit Point:** Finished Goods Receipt

**Tools:**
- `tekson_manufacturing` custom app (Phase 1)

---

### 10.3 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Manufacturing Planning (MPS)          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Production  │  │ Work Order  │  │ Capacity    │     │
│  │ Planning    │  │ Generation  │  │ Planning    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                      ERPNext Standard + Phase 2+         │
└─────────────────────────────────────────────────────────┘
                          │
                          │ Submitted Work Orders
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   Manufacturing Execution (MES)          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Material    │  │ Job Card    │  │ Work Order  │     │
│  │ Readiness   │  │ Execution   │  │ Completion  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                  tekson_manufacturing Phase 1            │
└─────────────────────────────────────────────────────────┘
                          │
                          ↓
                  Finished Goods Receipt
```

---

## 11. Impact Assessment

### Compared to Previous Project Status Document

| Aspect | Before | After |
|--------|--------|-------|
| Scope | Planning + Execution | Execution only (Phase 1) |
| Production Plan | Custom enhancements considered | Standard ERPNext |
| Work Order Generation | Potential modifications | Standard ERPNext |
| Boundary | Production Plan | Submitted Work Order |
| Phase 1 Complexity | High | Medium |
| Implementation Risk | Higher | Lower |
| Upgrade Compatibility | Concern | Preserved |

### Benefits of Revised Architecture

1. **Reduced Implementation Risk**
   - Smaller Phase 1 scope
   - Standard ERPNext for planning
   - Clear boundaries

2. **Preserved Upgrade Compatibility**
   - No modifications to core ERPNext
   - Custom app isolated to execution
   - Future ERPNext upgrades safer

3. **Scalable Architecture**
   - Planning and execution evolve independently
   - Phase 2 can add planning features
   - No breaking changes to Phase 1

4. **Clearer Responsibilities**
   - Planning team focuses on MPS
   - Execution team focuses on MES
   - Easier troubleshooting

5. **Faster Phase 1 Delivery**
   - Reduced scope = faster delivery
   - Critical execution issues addressed first
   - Planning enhancements can wait

---

## 12. Implementation Implications

### Code Organization

```
tekson_manufacturing/
│
├── execution/              ← Phase 1 focus
│   ├── material_readiness.py
│   ├── job_card_execution.py
│   ├── work_order_completion.py
│   └── traceability.py
│
├── planning/               ← Phase 2 (future)
│   ├── production_bucket.py
│   ├── work_order_consolidation.py
│   └── planner_workbench.py
│
└── settings/
    ├── manufacturing_settings.py
    └── warehouse_config.py
```

### Database Impact

**Phase 1:**
- New custom fields on Job Card
- New custom fields on Work Order
- Manufacturing Settings (Single)
- No changes to Production Plan tables

**Phase 2:**
- Production Bucket doctype (new)
- Planner Workbench (new)
- Enhanced Work Order custom fields

---

## 13. Testing Strategy

### Phase 1 Testing Focus

| Test Area | Scope |
|-----------|-------|
| Material Readiness | Submitted WOs only |
| Job Card Execution | Standard ERPNext JCs |
| Work Order Completion | Standard ERPNext WOs |
| Traceability | Within execution boundary |

**Not Tested in Phase 1:**
- Production Plan modifications
- BOM explosion changes
- Work Order generation logic
- Consolidation algorithms

### Phase 2 Testing Focus

| Test Area | Scope |
|-----------|-------|
| Production Bucket | New doctype |
| Work Order Consolidation | Generation logic |
| Planner Workbench | UI + logic |
| Capacity Planning | Scheduling algorithms |

---

## 14. Migration Path

### For Existing Installations

**Phase 1:**
1. Install `tekson_manufacturing` v1.1.0
2. Configure Manufacturing Settings
3. Configure Warehouse mappings
4. Existing Work Orders continue normally
5. New Work Orders use execution engine

**Phase 2:**
1. Upgrade to `tekson_manufacturing` v1.2.0
2. Enable Production Bucket feature
3. Migrate existing Production Plans (optional)
4. Train planners on new workbench

---

## 15. Approval & Sign-Off

### Technical Team Approval

**Architect:** ___________________  
**Date:** ___________________

**Development Lead:** ___________________  
**Date:** ___________________

### Customer Approval

**Production Manager:** ___________________  
**Date:** ___________________

**Planning Manager:** ___________________  
**Date:** ___________________

---

## 16. Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-31 | OSDuo Tech LLP | Initial architecture review updates |

**Related Documents:**
- UAT_REVIEW_ARCHITECTURE.md
- PROJECT_TIMELINE.md
- DEVELOPMENT_SUMMARY.md

**Next Review:** After Phase 1 completion

---

## 17. Glossary

| Term | Definition |
|------|------------|
| MPS | Manufacturing Planning System |
| MES | Manufacturing Execution System |
| Production Bucket | Time-based production planning unit (day, shift, campaign) |
| WIP | Work In Progress |
| WO | Work Order |
| JC | Job Card |

---

*This document supersedes conflicting architectural decisions in earlier documents. All Phase 1 development should follow this revised architecture.*

**Last Updated:** 2026-07-31  
**Next Review:** After Phase 1 UAT
