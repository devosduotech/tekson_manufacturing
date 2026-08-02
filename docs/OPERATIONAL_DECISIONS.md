# Operational Decisions - Phase 1 MES

**Document ID:** MES-OD-001  
**Version:** 1.0  
**Date:** August 2, 2026  
**Status:** ✅ **FROZEN**  
**Review Date:** Post-UAT (30-day stabilization)  

---

## Purpose

This document captures **operational decisions** made during Phase 1 design and implementation. These are not software requirements or business rules, but rather **manufacturing policies** that guide how Teksons operates.

**Why This Matters:**
Six months from now, someone will ask: *"Why did we decide to do it this way?"* This document provides the answer.

---

## Architectural Principles

### OD-001: MES Augments ERPNext, Does Not Replace

**Decision:** The MES shall augment ERPNext Manufacturing, not replace it.

**Rationale:**
- Leverage ERPNext's standard manufacturing capabilities
- Add only execution intelligence that Teksons needs
- Minimize customizations for easier upgrades
- Maintain compatibility with ERPNext V16+

**Examples:**
- ✅ Use: Standard Work Orders, Job Cards, Stock Entries, BOM Explosion, Backflush
- ✅ Custom: Material Readiness, Dependency Validation, Diagnostics, Department Workflow
- ❌ Avoid: Custom WO/JC doctypes, custom consumption logic, custom inventory movements

**Owner:** Technical Lead  
**Status:** ✅ **FUNDAMENTAL PRINCIPLE**

---

## Department WIP Management

### OD-002: Department WIP is Operational Inventory

**Decision:** Department WIP warehouses are treated as operational inventory, not temporary holding.

**Rationale:**
- Matches real shop floor behavior
- Departments manage their working stock
- Enables cumulative material availability
- Supports multi-WO material sharing

**Implications:**
- Material remains in WIP after transfer
- Excess from one WO available for next WO
- No automatic return to Stores
- Production owns WIP after transfer

**Owner:** Production Manager  
**Status:** ✅ **FROZEN**

---

### OD-003: Production Owns Department WIP After Transfer

**Decision:** Once Stores transfers material to Department WIP, Production assumes ownership and control.

**Rationale:**
- Clear separation of responsibilities
- Stores supplies, Production consumes
- Production decides material usage priority
- Matches organizational structure

**Implications:**
- Stores cannot access Department WIP without Production approval
- Production decides whether excess remains or returns
- Material Return requires Production initiation
- Stores replenishes on request, not by assumption

**Owner:** Production Manager / Stores Manager  
**Status:** ✅ **FROZEN**

---

### OD-004: No Stock Reservation in Department WIP

**Decision:** Department WIP stock is NOT reserved for specific Work Orders.

**Rationale:**
- Production priorities change dynamically
- Management may reprioritize WOs mid-day
- Physical stock is shared in department
- First-come, first-consume matches reality

**Implications:**
- Multiple WOs may show "Ready" simultaneously
- Production supervisor decides which to start
- Material Readiness evaluates real-time availability
- No artificial blocking from reservations

**Exception:** None

**Owner:** Production Manager  
**Status:** ✅ **FROZEN**

---

### OD-005: Excess Material Remains in Department WIP

**Decision:** Excess material from Work Orders remains in Department WIP unless Production explicitly returns it.

**Rationale:**
- Reduces unnecessary Stock Entries
- Matches shop floor practice
- Available for next WO requiring same material
- Production decides when to return

**Example:**
```
WO requires: 6 sheets
Stores transfers: 10 sheets
Production consumes: 6 sheets
Remaining: 4 sheets → Stays in WIP
```

**Owner:** Production Manager  
**Status:** ✅ **FROZEN**

---

### OD-006: Material Readiness Based on WIP Availability

**Decision:** Material Readiness evaluates current stock in Department WIP, not transfer history against specific WO.

**Rationale:**
- Source of truth is physical availability
- Supports multi-WO material sharing
- Independent of transfer timing
- Real-time decision support

**Formula:**
```
Available = Current WIP Stock - Reserved (if any)
Ready if: Available >= Required
```

**Owner:** Production Manager  
**Status:** ✅ **FROZEN**

---

## Work Order Management

### OD-007: Planner Controls WO Quantity Revisions

**Decision:** Only the Planner can revise Work Order quantities.

**Rationale:**
- Planned partial production requires formal revision
- Prevents confusion between planned vs actual
- Clear accountability for quantity changes
- ERPNext standard WO revision process

**Scenarios:**
- **Planned Partial:** Planner revises WO qty before production (e.g., 100 → 60)
- **Short Production:** WO remains "In Process" until qty achieved or revised
- **Over Production:** Requires Planner approval and WO revision

**Owner:** Planning Manager  
**Status:** ✅ **FROZEN**

---

### OD-008: Work Order Completion Only on Planned Quantity

**Decision:** Work Orders are completed only when planned quantity is produced OR Planner formally revises quantity.

**Rationale:**
- Clear completion criteria
- Prevents premature WO closure
- Accurate production tracking
- Cost accounting accuracy

**Owner:** Planning Manager  
**Status:** ✅ **FROZEN**

---

### OD-009: Parent WO Readiness Based on Child Availability

**Decision:** Parent Work Order material readiness considers child sub-assembly availability in WIP.

**Rationale:**
- Multi-level BOM support
- Sub-assemblies treated as materials
- Production visibility into dependencies
- Accurate readiness evaluation

**Owner:** Planning Manager  
**Status:** ✅ **FROZEN**

---

## Stores Operations

### OD-010: Stores Supplies Departments, Not Individual Job Cards

**Decision:** Stores transfers material to Department WIP based on daily production schedule, not individual Job Card requests.

**Rationale:**
- Efficient batch picking
- Reduces transaction count
- Department manages distribution
- Matches organizational structure

**Process:**
```
Daily Production Schedule
    ↓
Stores Picking List (Phase 1.1)
    ↓
Material Transfer to WIP
    ↓
Department executes production
```

**Owner:** Stores Manager  
**Status:** ✅ **FROZEN**

---

### OD-011: Stores Picking List Deferred to Phase 1.1

**Decision:** Consolidated Stores Picking List is deferred to Phase 1.1 (post-UAT operational enhancement).

**Rationale:**
- Not required for MES functional validation
- Operational efficiency feature
- Can use manual process temporarily
- Post-UAT implementation based on real usage

**Interim Solution:** Stores opens individual Work Orders or uses temporary report.

**Owner:** Stores Manager / Project Manager  
**Status:** ✅ **FROZEN** (Deferred)

---

### OD-012: Material Return Requires Production Initiation

**Decision:** Material returns from Department WIP to Stores require Production initiation and approval.

**Rationale:**
- Production owns WIP inventory
- Prevents unauthorized returns
- Clear accountability
- Standard ERPNext Stock Entry sufficient

**Process:**
```
Production identifies excess
    ↓
Production creates Material Return request
    ↓
Stores approval (if required)
    ↓
Stock Entry: WIP → Raw Material Stores
```

**Owner:** Production Manager / Stores Manager  
**Status:** ✅ **FROZEN**

---

## Production Execution

### OD-013: First-Come, First-Consume Material Model

**Decision:** Materials in Department WIP are consumed on first-come, first-consume basis.

**Rationale:**
- Matches physical reality
- No artificial allocation
- Production supervisor controls priority
- Simplest operational model

**Example:**
```
WIP Stock: 20 sheets
WO-1 needs: 15 → Starts → Consumes 15
WO-2 needs: 15 → Checks availability → 5 remaining → Awaiting Material
```

**Owner:** Production Manager  
**Status:** ✅ **FROZEN**

---

### OD-014: Production Supervisor Controls Priority

**Decision:** Production supervisor decides which Work Order to execute when multiple WOs are ready.

**Rationale:**
- Dynamic priority changes common
- Management can override verbally
- System does not enforce priority
- Flexibility for urgent orders

**Implications:**
- No "Blocked by Management" status in Phase 1
- Priority changes handled outside system
- Material Readiness shows all ready WOs
- Supervisor decides start sequence

**Owner:** Production Manager  
**Status:** ✅ **FROZEN**

---

### OD-015: ERPNext Standard Backflush for Consumption

**Decision:** Raw material consumption uses ERPNext standard backflush (Manufacture Stock Entry).

**Rationale:**
- Standard ERPNext functionality
- Consumes BOM quantity for actual production
- Excess remains in WIP automatically
- No custom consumption logic required

**Process:**
```
Job Card Complete (all operations)
    ↓
Execution Engine creates Manufacture Entry
    ↓
ERPNext backflush consumes from WIP
    ↓
FG received to warehouse
    ↓
Excess remains in WIP
```

**Owner:** Technical Lead  
**Status:** ✅ **FROZEN**

---

## Scrap & Quality

### OD-016: Scrap Transferred to Scrap Store

**Decision:** Scrap generated during production is transferred to Scrap Store via Material Transfer.

**Rationale:**
- Clear scrap tracking
- Inventory accuracy
- Cost accounting
- Standard ERPNext Stock Entry

**Process:**
```
Scrap generated
    ↓
Production creates Material Transfer
    ↓
From: Department WIP
    ↓
To: Scrap Store
```

**Phase:** Phase 2 (formal workflow)  
**Interim:** Manual Stock Entry

**Owner:** Production Manager  
**Status:** ✅ **FROZEN** (Process), ⬜ Deferred (Workflow)

---

### OD-017: Rework Flow Deferred to Phase 2

**Decision:** Formal rework Job Card workflow is deferred to Phase 2.

**Rationale:**
- Not required for Phase 1 validation
- Quality processes need more analysis
- Can handle manually in Phase 1
- Lower priority than core MES

**Interim:** Manual rework handling

**Owner:** Quality Manager / Project Manager  
**Status:** ✅ **DEFERRED** to Phase 2

---

## Multi-WO Coordination

### OD-018: Shared Sub-Assemblies Managed by Planning

**Decision:** When multiple parent WOs share common sub-assemblies, Planning determines allocation priority.

**Rationale:**
- System should not auto-allocate
- Management decides based on orders
- Material Readiness shows availability
- Manual decision for shared components

**Example:**
```
Core Sub-Assembly: 20 produced
WO-R215 needs: 8
WO-R216 needs: 6
WO-R217 needs: 10
Total demand: 24 > Available: 20

Decision: Planning allocates manually
```

**Owner:** Planning Manager  
**Status:** ✅ **FROZEN**

---

### OD-019: WO Cancellation Leaves Material in WIP

**Decision:** When Work Order is cancelled, material remains in Department WIP unless Stores explicitly returns it.

**Rationale:**
- Operationally simpler
- Material available for other WOs
- No automatic returns
- Production decides disposition

**Owner:** Planning Manager / Production Manager  
**Status:** ✅ **FROZEN**

---

## System Behavior

### OD-020: Live Material Evaluation at Job Card Start

**Decision:** Material Readiness evaluates availability at the moment Job Card is started, not in advance.

**Rationale:**
- Real-time decision support
- Reflects actual consumption
- No stale reservations
- Matches dynamic production environment

**Owner:** Technical Lead  
**Status:** ✅ **FROZEN**

---

### OD-021: Transaction Validation Prevents Over-Consumption

**Decision:** System validates material availability at Job Card start through transaction validation, not reservation.

**Rationale:**
- Database handles concurrency naturally
- First valid transaction succeeds
- Second transaction sees updated stock
- No custom locking required

**Owner:** Technical Lead  
**Status:** ✅ **FROZEN**

---

### OD-022: Custom Fields Auto-Populated

**Decision:** Job Card custom fields are auto-populated by system hooks, not manually entered.

**Rationale:**
- Reduces operator data entry
- Ensures consistency
- Real-time status updates
- Better user experience

**Fields:**
- `custom_item_code`
- `custom_actual_production_item`
- `custom_start_status`
- `custom_plant_floor`
- etc.

**Owner:** Technical Lead  
**Status:** ✅ **FROZEN**

---

## Deferred Decisions

### OD-023: Barcode Scanning (Phase 2)

**Decision:** Barcode scanning for material issue and Job Card execution is deferred to Phase 2.

**Rationale:**
- Requires hardware infrastructure
- Operational enhancement
- Manual entry sufficient for Phase 1
- Lower priority

**Owner:** Project Manager  
**Status:** ✅ **DEFERRED** to Phase 2

---

### OD-024: Handheld Shop Floor Interface (Phase 2)

**Decision:** Mobile/tablet interface for operators is deferred to Phase 2.

**Rationale:**
- Requires hardware procurement
- Desktop/laptop sufficient for Phase 1
- Operational enhancement
- Lower priority

**Owner:** Project Manager  
**Status:** ✅ **DEFERRED** to Phase 2

---

### OD-025: Planner Production Buckets (Phase 2)

**Decision:** Shift-wise and daily production bucket planning is deferred to Phase 2.

**Rationale:**
- Advanced planning feature
- Phase 1 uses standard WO dates
- Operational enhancement
- Lower priority

**Owner:** Planning Manager / Project Manager  
**Status:** ✅ **DEFERRED** to Phase 2

---

## Summary by Category

| Category | Decisions | Frozen | Deferred |
|----------|-----------|--------|----------|
| Architectural Principles | 1 | 1 | 0 |
| Department WIP Management | 5 | 5 | 0 |
| Work Order Management | 3 | 3 | 0 |
| Stores Operations | 3 | 3 | 0 |
| Production Execution | 3 | 3 | 0 |
| Scrap & Quality | 2 | 1 | 1 |
| Multi-WO Coordination | 2 | 2 | 0 |
| System Behavior | 3 | 3 | 0 |
| Deferred Decisions | 3 | 0 | 3 |
| **TOTAL** | **25** | **21** | **4** |

---

## Review & Maintenance

**Review Frequency:** Quarterly  
**Next Review:** Post-UAT (30-day stabilization period)  
**Owner:** Project Manager  
**Change Process:** Steering Committee approval required

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Aug 2, 2026 | AI Assistant | Initial creation |
| | | | |

---

**Status:** ✅ **FROZEN** - Changes require Steering Committee approval  
**Distribution:** All Stakeholders

---

**END OF DOCUMENT**
