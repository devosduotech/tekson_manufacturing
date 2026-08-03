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

### OD-003: Material Transfer for Manufacture to Department WIP

**Decision:** Stores shall use ERPNext's standard **"Material Transfer for Manufacture"** Stock Entry type to transfer raw materials from Stores to Department WIP warehouses.

**Rationale:**
- Maintains ERPNext Work Order lifecycle (WO status → "In Process")
- Uses standard ERPNext inventory transactions
- Enables accurate WIP valuation and costing
- Aligns with ERPNext manufacturing best practices

**Implications:**
- User sees: "Material Transfer to WIP" (simplified terminology)
- System creates: "Material Transfer for Manufacture" (ERPNext standard)
- Work Order status automatically changes to "In Process"
- Stock Entry purpose = "Material Transfer for Manufacture"
- Department WIP becomes the consumption source for Backflush

**Validation (Internal Test 2026-08-03):**
- ✅ Transfer to WIP sets WO status = "In Process"
- ✅ Department WIP correctly configured as consumption source
- ✅ Backflush consumes from Department WIP warehouse

**Owner:** Stores Manager / Technical Lead  
**Status:** ✅ **FROZEN** (Validated)

---

### OD-004: Department WIP is Operational Inventory

**Decision:** Department WIP warehouses are treated as **operational inventory owned by Production**, not temporary holding or WO-specific allocation.

**Rationale:**
- Matches real shop floor behavior at Teksons
- Departments manage their working stock
- Enables cumulative material availability across WOs
- Supports multi-WO material sharing in same department
- Excess from one WO available for next WO

**Implications:**
- Material remains in WIP after transfer (not consumed until Backflush)
- Excess from one WO automatically available for next WO
- No automatic return to Stores after WO completion
- Production decides whether excess remains or returns
- WIP valuation reflects actual department inventory

**Validation (Internal Test 2026-08-03):**
- ✅ Transfer 30.0 kg to WIP
- ✅ Consume 6.45 kg via Backflush
- ✅ **23.55 kg remains in WIP** (available for next WO)

**Owner:** Production Manager  
**Status:** ✅ **FROZEN** (Validated)

**Exception:** None

**Owner:** Production Manager  
**Status:** ✅ **FROZEN**

---

### OD-005: ERPNext Backflush for Material Consumption

**Decision:** Material consumption shall use **ERPNext's standard Backflush** from Department WIP warehouse. Only the BOM-required quantity shall be consumed during Manufacture Entry. Excess material shall remain in Department WIP.

**Rationale:**
- Leverages ERPNext's proven manufacturing engine
- Automatic consumption based on actual production quantity
- No custom consumption logic required
- Accurate costing and valuation
- Excess automatically remains available

**How It Works:**
```
Stores transfers:  30.0 kg to WIP
WO produces:       30 Fins
BOM rate:          0.215 kg per Fin
Backflush:         30 × 0.215 = 6.45 kg consumed
Remaining:         30.0 - 6.45 = 23.55 kg in WIP ✅
```

**Implications:**
- MES does NOT control consumption logic
- MES controls **when** production can start (Material Readiness)
- ERPNext controls **how much** is consumed (Backflush)
- Clear separation: MES = readiness, ERPNext = inventory
- No custom inventory tracking required

**Validation (Internal Test 2026-08-03):**
- ✅ Transfer 30.0 kg to WIP-Ralu In
- ✅ Produce 30 Fins
- ✅ Backflush consumed 6.45 kg (exact BOM qty)
- ✅ 23.55 kg remains in WIP (available for next WO)
- ✅ WO status updated to "In Process" → "Completed"

**Owner:** Technical Lead / Production Manager  
**Status:** ✅ **FROZEN** (Validated 2026-08-03)

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

### OD-025: ERPNext Work Order Status is Informational

**Decision:** The MES shall **not derive production readiness** from ERPNext Work Order status (`Submitted`, `In Process`, `Completed`). Production readiness is determined **only** by:

1. **Material Readiness** (current WIP stock availability)
2. **Dependency Validation** (previous operations complete)
3. **Job Card Status** (operational state)

**Rationale:**
- ERPNext WO status reflects inventory transactions, not shop-floor execution readiness
- WO can be "In Process" but materials not yet transferred
- WO can be "In Process" but previous operations incomplete
- Production supervisors need real-time execution intelligence, not inventory status

**Implications:**
- MES Material Readiness Engine evaluates WIP stock independently
- Dependency Engine validates sequence independently
- JC Start allowed only when BOTH conditions met
- ERPNext WO status updated automatically by inventory transactions (informational only)

**Example:**
```
WO Status: In Process (after Material Transfer)
    ↓
Material Readiness: NOT READY (WIP stock = 0)
    ↓
JC Start: BLOCKED ❌
```

**Owner:** Production Manager / Technical Lead  
**Status:** ✅ **FROZEN**

---

### OD-026: Planner Production Buckets (Phase 2)

**Decision:** Shift-wise and daily production bucket planning is deferred to Phase 2.

**Rationale:**
- Advanced planning feature
- Phase 1 uses standard WO dates
- Operational enhancement
- Lower priority

**Owner:** Planning Manager / Project Manager  
**Status:** ✅ **DEFERRED** to Phase 2

---

## Operational Assumptions

### OA-001: Concurrent Job Card Starts

**Assumption:** Department supervisors coordinate Job Card starts. Simultaneous starts of multiple Job Cards competing for the exact same Department WIP inventory are considered **operationally rare** and are not specifically synchronized in Phase 1.

**Rationale:**
- Single supervisor per department coordinates work
- Work Orders released by planned start dates
- Management priorities communicated before execution
- Common raw materials typically used within same department for similar sub-assemblies
- Same workstation handling concurrent WOs is uncommon

**Safety Net:** Even if concurrent starts occur:
- Material Readiness validates at JC Start time
- ERPNext Backflush will reject Manufacture Entry if insufficient stock
- No inventory corruption possible

**Observed Behavior at Teksons:**
- Operations are department-based
- Common materials consumed within same department
- Production engineer/supervisor coordinates daily work
- Simultaneous starts on exact same material: **rare**

**Future Enhancement (if needed):**
If concurrent starts become a practical issue during production:
- Introduce short-lived "material lock" (30 seconds) at JC Start
- Revalidate stock immediately before allowing "In Progress" transition
- NOT inventory reservation, just transaction synchronization

**Owner:** Production Manager  
**Status:** ✅ **ACCEPTED ASSUMPTION** (Phase 1)

---

## Summary by Category

| Category | Decisions | Frozen | Deferred |
|----------|-----------|--------|----------|
| Architectural Principles | 1 | 1 | 0 |
| Department WIP Management | 6 | 6 | 0 |
| Work Order Management | 3 | 3 | 0 |
| Stores Operations | 3 | 3 | 0 |
| Production Execution | 4 | 4 | 0 |
| Scrap & Quality | 2 | 1 | 1 |
| Multi-WO Coordination | 2 | 2 | 0 |
| System Behavior | 3 | 3 | 0 |
| Operational Assumptions | 1 | 1 | 0 |
| Deferred Decisions | 3 | 0 | 3 |
| **TOTAL** | **26** | **22** | **4** |

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
| 1.0 | Aug 2, 2026 | Project Team | Initial creation |
| | | | |

---

**Status:** ✅ **FROZEN** - Changes require Steering Committee approval  
**Distribution:** All Stakeholders

---

**END OF DOCUMENT**
