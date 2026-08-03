# Warehouse Architecture Decision

**Document Type:** Architecture Decision Record  
**Date:** 2026-08-03  
**Status:** Approved for UAT  
**Version:** 2.0  
**Related Rules:** WH-001, WH-002, WH-003, WH-004, WH-005

---

## Executive Summary

The Tekson MES uses a **logical production holding warehouse** model where:
- Material is transferred **once** from Stores to Department WIP at production start
- Intermediate department movement is tracked via **Job Cards**, not Stock Entries
- Backflush consumes from WIP Warehouse and produces to FG Warehouse
- BOM defines **what** is made and **where** it goes (Target FG Warehouse)
- Process Plan defines **how** it's made (first operation determines WIP Warehouse)

This reduces stock entries from potentially 10+ per WO to **exactly 2**, while maintaining full production traceability through Job Cards.

---

## Decision: Logical WIP Warehouse with Cached Status

### Core Principle

The Work Order `wip_warehouse` represents a **logical production holding warehouse**, not a physical location tied to a specific department throughout production.

**Material Flow:**
```
Stores
    ↓ (Material Transfer - 1x)
WIP Warehouse (First Department)
    ↓ (Production tracked by Job Cards, NOT stock movements)
[Operation 1] → [Operation 2] → [Operation 3] → ...
    ↓ (Manufacture Entry - 1x, backflush)
FG Warehouse
```

**Total Stock Entries per WO:** 2 (Transfer + Manufacture)

---

## Context

### Initial Approach (V1.0 - Department Transfers)

Originally implemented with inter-department transfers:
```
Stores → WIP-CNC → WIP-Ralu Weld → WIP-Assembly → FG
```

**Problems Identified:**
- Excessive stock entries (4-6 per WO)
- Complex transfer logic between departments
- Operators confused about "where" material physically is
- System overhead for tracking each transfer
- Doesn't match how supervisors think about production

### Revised Approach (V2.0 - Logical Holding)

Single WIP warehouse with Job Card tracking:
```
Stores → WIP-Ralu In (logical holding)
    ↓
[All Operations tracked by Job Cards]
    ↓
FG Warehouse
```

**Benefits:**
- Only 2 stock entries per WO
- Production progress visible via Job Card status
- Matches supervisor mental model ("in production" vs "in warehouse")
- Simpler configuration and maintenance
- ERPNext standard backflush works without customization

---

## Warehouse Hierarchy

### Teksons Warehouse Structure

```
Work In Progress Stores (Warehouse Group)
├── WIP-Ralu In - TPL
├── WIP-Ralu Weld - TPL
├── WIP-CNC - TPL
├── WIP-RP - TPL
├── WIP-RA - TPL
└── WIP-W - TPL

Stores (Warehouse Group)
├── Raw Material Stores - TPL
└── BOF Stores - TPL

Receipt and Dispatch Stores (Warehouse Group)
├── Incoming Quality Hold Stores - TPL
└── Incoming Quality Rejected Stores - TPL

Finished Goods Stores - TPL (Standalone)

Rejected Stores - TPL (Standalone)

Scrap Stores - TPL (Standalone)
```

### ERPNext Standard Mapping

| ERPNext Object | Tekson Usage | Purpose |
|----------------|--------------|---------|
| **Plant Floor** | Manufacturing Department | Ralu In, Ralu Weld, CNC, RP, RA, W |
| **Warehouse** (on Workstation) | Department WIP | WIP-Ralu In, WIP-CNC, etc. |
| **Work Order.wip_warehouse** | Logical Production Holding | First department WIP |
| **Work Order.fg_warehouse** | Final Destination | FG Stores or next stage WIP |
| **Work Order.source_warehouse** | Raw Material Source | Raw Material Stores |

---

## Warehouse Resolution Logic

### FG Warehouse Priority

```
1. Production Plan FG Warehouse (override)
        ↓
2. BOM Target FG Warehouse (mandatory field)
        ↓
3. Manufacturing Settings Default FG
```

**Configuration:**
- BOM Custom Field: `target_fg_warehouse` (Mandatory)
- Examples:
  - Core Assembly BOM → `WIP-Ralu Weld - TPL`
  - Tank Assembly BOM → `WIP-Ralu Weld - TPL`
  - Final Radiator BOM → `Finished Goods Stores - TPL`

### WIP Warehouse Priority

```
1. Production Plan WIP Warehouse (override)
        ↓
2. First Operation's Department WIP (from Process Plan)
        ↓
3. Manufacturing Settings Default WIP
```

**Logic:**
```python
# Get first operation's workstation
first_op = work_order.operations[0]
workstation = frappe.get_doc('Workstation', first_op.workstation)
department = workstation.department

# Build WIP warehouse name
wip_warehouse = f'WIP-{department.split("-")[0]} - TPL'
```

---

## BOM Configuration

### Required Fields

| Field | Type | Mandatory | Purpose |
|-------|------|-----------|---------|
| `target_fg_warehouse` | Link (Warehouse) | Yes | Final destination of finished goods |
| `operations` | Table (BOM Operation) | Yes | Defines process plan / routing |

### Example Configuration

**BOM: R215 Radiator Core Assembly**
```yaml
Item: R215 Radiator Core
target_fg_warehouse: WIP-Ralu Weld - TPL
Operations:
  - Operation: Tube Cutting
    Workstation: CNC-01 (Department: Ralu In)
  - Operation: Core Assembly
    Workstation: Assembly-01 (Department: Ralu In)
  - Operation: Brazing
    Workstation: Brazing-01 (Department: Ralu Weld)
```

**Result:**
- `WO.wip_warehouse` = `WIP-Ralu In - TPL` (from first operation)
- `WO.fg_warehouse` = `WIP-Ralu Weld - TPL` (from BOM)

---

## Production Plan Overrides

Production Plan can override BOM defaults when needed:

| Field | Purpose | Example |
|-------|---------|---------|
| `fg_warehouse` | Override destination | Export FG Stores instead of regular FG |
| `for_warehouse` | Override WIP | Special project WIP |

**Priority:** Production Plan > BOM > Manufacturing Settings

---

## Work Order Configuration

### Auto-Populated Fields

```python
Work Order (after creation):
├── source_warehouse = Raw Material Stores - TPL
├── wip_warehouse = WIP-Ralu In - TPL (from first operation)
└── fg_warehouse = WIP-Ralu Weld - TPL (from BOM)
```

### Validation Rules

Before WO submission:
1. ✅ `wip_warehouse` must exist and not be a group node
2. ✅ `fg_warehouse` must exist and not be a group node
3. ✅ `source_warehouse` must exist (if specified)
4. ✅ All warehouses must belong to same company

---

## Stock Entry Flow

### 1. Material Transfer for Manufacture

**Trigger:** After WO submission, before production starts

```python
Stock Entry:
├── purpose = "Material Transfer for Manufacture"
├── from_warehouse = Raw Material Stores - TPL
├── to_warehouse = WIP-Ralu In - TPL (WO.wip_warehouse)
└── work_order = WO-001
```

**Validation:**
- Material available in source warehouse
- WIP warehouse exists
- WO is submitted

### 2. Manufacture (Backflush)

**Trigger:** When last Job Card is completed

```python
Stock Entry:
├── purpose = "Manufacture"
├── from_warehouse = WIP-Ralu In - TPL (WO.wip_warehouse)
├── to_warehouse = WIP-Ralu Weld - TPL (WO.fg_warehouse)
├── work_order = WO-001
└── bom_no = BOM-001
```

**Backflush Logic:**
- Consumes raw materials from `wip_warehouse` (BOM quantity)
- Produces finished goods to `fg_warehouse`
- Excess material remains in `wip_warehouse` for next WO

---

## Material Readiness & Caching

### Cached Status Architecture

**WO Submit = Production Release (Not Just Planning)**

When the planner submits a Work Order, it is **released to production**. The Job Card Readiness Engine evaluates **current WIP stock immediately**.

**Key Principle:** Material may already be in WIP (transferred earlier or excess from previous WO).

**WO Submit (Production Release):**
```
WO Submitted
    ↓
Create Job Cards
    ↓
Job Card Readiness Engine
    ↓
Evaluate CURRENT WIP Stock
    ↓
Update Custom Fields:
  - custom_material_status = "Material Available" / "Waiting for Material" / "Shortage"
  - custom_readiness_status = "Ready to Start" / "Waiting for Previous Operation" / "Blocked"
  - custom_dependency_last_updated = Now()
```

**Material Transfer (Additional Stock):**
```
Material Transfer Submitted
    ↓
WIP Stock Updated
    ↓
Job Card Readiness Engine
    ↓
Refresh WO's Job Cards Only
    ↓
Update Custom Fields with new stock status
```

**Operation Completion:**
```
Job Card Completed
    ↓
Refresh Downstream JCs Only
    ↓
Update dependency status (material check optional)
```

### Event-Driven Refresh Triggers

| Event | Action | Material Check | Scope |
|-------|--------|----------------|-------|
| WO Submit | Create JCs + Run Readiness Engine | ✅ Yes (current WIP) | All JCs in WO |
| Material Transfer Submit | Refresh Job Cards | ✅ Yes | All JCs in WO (from SE.work_order) |
| Material Return | Refresh Job Cards | ✅ Yes | All JCs in WO |
| Operation Complete | Refresh Downstream JCs | Optional | Downstream JCs only |
| Stock Reconciliation (WIP) | Refresh Affected JCs | ✅ Yes | Affected JCs only |
| Manual Refresh | On-demand | ✅ Yes | Selected JCs |

**Key Principles:**
1. Work Order is **immutable** after submission (Cancel & Amend for changes)
2. Material Transfer refreshes **only that WO's JCs** (via SE.work_order link)
3. Operation Complete refreshes **downstream JCs only** (efficiency)

### Start Button Validation

**Lightweight check (< 100ms):**
```python
def start_job_card(jc_name):
    jc = frappe.get_doc('Job Card', jc_name)
    
    # Check cached readiness status (instant)
    if jc.custom_readiness_status != "Ready to Start":
        frappe.throw(f"Cannot start: {jc.custom_readiness_status} - {jc.custom_blocked_by}")
    
    # Quick validation (protect against changes since last refresh)
    if jc.status == 'Work In Progress':
        frappe.throw("Already in progress")
    
    if jc.work_order_status != 'Submitted':
        frappe.throw("Work Order is not active")
    
    # Optional: Quick stock check (only if strict validation enabled)
    if strict_validation and not quick_bin_check(jc):
        frappe.throw("Material no longer available in WIP")
    
    # Start
    jc.status = 'Work In Progress'
    jc.actual_start_date = now
    jc.save()
    
    # No need to refresh - next operation will refresh on JC submit
```

**Key Principle:** Start button **consumes** cached status, doesn't recalculate it.

---

## Multi-Level BOM Support

### Sub-Assembly Flow

```
Sub-Assembly BOM (Core)
├── target_fg_warehouse: WIP-Ralu Weld - TPL
└── Operations: [Cutting, Assembly]

Parent BOM (Radiator)
├── target_fg_warehouse: Finished Goods Stores - TPL
├── Operations: [Final Assembly, Testing]
└── Items:
    └── Core Assembly (from sub-assembly WO)
```

**Result:**
- Sub-assembly WO produces to `WIP-Ralu Weld - TPL`
- Parent WO consumes from `WIP-Ralu Weld - TPL`
- Final production goes to `Finished Goods Stores - TPL`

---

## Department Dashboard

### Production Visibility

Since material location is "WIP Warehouse" throughout production, **Job Card status** becomes the authoritative source for "where is this item?"

**Department Dashboard shows:**
```
Pending (Material Available)
In Progress (Operation X)
Completed (Waiting for Transfer)
Blocked (Waiting for Previous Operation)
Waiting for Material
```

### Key Reports

1. **WIP Inventory Report**
   - Shows material in WIP warehouse by WO
   - Current operation (from Job Card)
   - Days in production

2. **Production Progress Report**
   - WO-wise completion %
   - Operation-wise status
   - Delayed operations

3. **Material Shortage Report**
   - JCs blocked due to material
   - Expected availability date

---

## Exceptions & Edge Cases

### Partial Production

**Scenario:** WO Qty = 100, Produce 40 today, 60 tomorrow

**Handling:**
- Stock Entry fg_completed_qty = 40 (first time)
- Remaining qty = 60 (stays in WIP)
- Next day: fg_completed_qty = 60
- Backflush proportional to actual production

### Scrap / Rejection

**Scenario:** 100 produced, 5 rejected

**Handling:**
- Stock Entry with scrap item row
- Scrap warehouse: `Scrap Stores - TPL`
- FG warehouse receives 95 good qty
- Costing adjusts automatically

### Rework

**Scenario:** QC failure, needs rework

**Options:**
1. **Same WO:** Create additional Job Card for rework operation
2. **New WO:** For major rework requiring different process

**Decision:** Based on rework complexity (to be finalized in UAT)

---

## Alternatives Considered

### Alternative 1: Inter-Department Transfers

**Approach:** Stock Entry for each department change
```
WIP-CNC → WIP-Ralu Weld → WIP-Assembly
```

**Rejected because:**
- 4-6 stock entries per WO
- Complex transfer logic
- Doesn't match supervisor mental model
- System overhead

### Alternative 2: Operation-Specific Warehouses

**Approach:** Each operation has dedicated warehouse
```
WIP-Op10, WIP-Op20, WIP-Op30
```

**Rejected because:**
- Excessive configuration
- Doesn't match physical layout
- Complex reporting

### Alternative 3: No WIP Warehouse (Direct Consumption)

**Approach:** Consume directly from Stores
```
Stores → FG (skip WIP)
```

**Rejected because:**
- No material tracking during production
- Can't handle partial production
- Doesn't support multi-level BOM
- ERPNext requires WIP for backflush

---

## Implementation Status

| Component | Status | Version |
|-----------|--------|---------|
| Warehouse Hierarchy | ✅ Implemented | v2.0 |
| BOM Custom Field | ✅ Implemented | v2.0 |
| WO Hook (set_warehouses) | ✅ Implemented | v2.0 |
| Material Transfer | ✅ Implemented | v2.0 |
| Backflush Logic | ✅ Implemented | v2.0 |
| Cached Status Fields | ⏳ In Progress | v2.0 |
| Event-Driven Refresh | ⏳ In Progress | v2.0 |
| Department Dashboard | ⏳ Planned | v2.0 |

---

## Testing Implications

### Critical Test Scenarios

1. **TC-WH-001: Warehouse Resolution**
   - WO from BOM with target_fg_warehouse
   - Verify wip_warehouse from first operation
   - Verify fg_warehouse from BOM

2. **TC-WH-002: Material Transfer**
   - Transfer from Stores to WIP
   - Verify stock ledger entries
   - Verify bin balances

3. **TC-WH-003: Backflush**
   - Complete all JCs
   - Trigger Manufacture Entry
   - Verify consumption from WIP
   - Verify production to FG

4. **TC-WH-004: Partial Production**
   - WO Qty = 100
   - Produce 40, verify remaining 60 in WIP
   - Produce 60, verify WO complete

5. **TC-WH-005: Multi-Level BOM**
   - Sub-assembly WO produces to WIP
   - Parent WO consumes from WIP
   - Verify warehouse flow

6. **TC-WH-006: Production Plan Override**
   - BOM target = FG Stores
   - PP override = Export FG
   - Verify WO uses PP override

---

## UAT Acceptance Criteria

### Must Pass Before UAT

1. ✅ WO creation with correct warehouses
2. ✅ Material Transfer validation
3. ✅ Backflush consumes from WIP
4. ✅ Partial production works
5. ✅ Multi-level BOM flow
6. ✅ Department dashboard shows correct status
7. ✅ Cached status updates on events
8. ✅ Start button uses lightweight validation

### Nice to Have (Post-UAT)

- Machine utilization reports
- Advanced analytics
- Mobile optimization

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-31 | OSDuo Tech LLP | Initial department-centric model |
| 2.0 | 2026-08-03 | OSDuo Tech LLP | Logical WIP warehouse with cached status |

**Approved By:** ___________________  
**Date:** ___________________

**Next Review:** After UAT completion (v2.1)

---

## References

- **Business Rules:** WH-001, WH-002, WH-003, WH-004, WH-005
- **Implementation:** 
  - `services/work_order_service.py` (set_warehouses)
  - `utils/job_card_utils.py` (cached status)
  - `execution/execution_engine.py` (backflush)
- **Test Scenarios:** TC-WH-001 through TC-WH-006
- **Related Docs:** 
  - `MES_BUSINESS_RULES.md`
  - `IMPLEMENTATION_HARDENING_PLAN.md`
  - `UAT_ACCEPTANCE_MATRIX.md`

---

*This architecture decision separates product definition (BOM) from execution (Process Plan), minimizes stock entries, and uses Job Cards as the authoritative source for production progress tracking.*
