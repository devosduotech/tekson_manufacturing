# Manufacturing Execution System (MES) – Business Rules

**Document Type:** Business Rules Specification  
**Version:** 1.0  
**Date:** 2026-07-31  
**Status:** Approved for Implementation  
**Project:** Tekson Manufacturing MES  
**ERPNext Version:** V15

---

## Overview

This document captures the **business rules** for the Tekson Manufacturing Execution System (MES). These rules are **independent of implementation** and serve as the single source of truth for manufacturing logic.

All code implementations must adhere to these rules.

---

## Rule Categories

1. **Job Card Execution Rules** (JC-001 to JC-010)
2. **Material Readiness Rules** (MR-001 to MR-010)
3. **Work Order Completion Rules** (WO-001 to WO-010)
4. **Dependency Validation Rules** (DV-001 to DV-010)
5. **Diagnostics & Messaging Rules** (DM-001 to DM-010)
6. **Warehouse & Inventory Rules** (WH-001 to WH-010)

---

## Job Card Execution Rules

### JC-001: Job Card Start Permission

**Rule:** A Job Card cannot start until all previous operations are complete.

**Validation:**
- Check sequence_id
- Find previous Job Card (sequence_id - 1)
- Verify status = "Completed"
- Check cached field: `custom_can_start_operation` = 1

**Exception:** First operation (sequence_id = 1) has no previous dependency.

**Implementation Note:** Start permission is pre-calculated when WO is submitted and refreshed on events (material transfer, operation complete). Start button performs lightweight validation only.

---

### JC-002: Job Card Completion Permission

**Rule:** A Job Card can only be completed if the for_quantity has been produced.

**Validation:**
- Check total_completed_qty >= for_quantity

---

### JC-003: Job Card Material Check

**Rule:** A Job Card should not start if required materials are not available.

**Validation:**
- Check cached field: `custom_material_available` = 1
- Quick stock verification (< 100ms)
- Material must be in WO.wip_warehouse

**Severity:** Warning (can be overridden with Strict Validation disabled)

**Implementation Note:** Material availability is evaluated during **Execution Phase** only:
- **Planning Phase (WO Submit):** Status = "Waiting for Material Transfer"
- **Execution Phase (Material Transfer):** Evaluate actual WIP stock
- **Operation Complete:** Refresh downstream JCs (optional stock check)

---

### JC-003A: Job Card Readiness Engine

**Rule:** Job Card readiness is determined by a dedicated engine that evaluates all conditions **immediately on WO submit**.

**WO Submit = Production Release:**

When a Work Order is submitted, it is **released to production** (not just planned). The Readiness Engine:
1. Creates Job Cards
2. Evaluates **current WIP stock** immediately
3. Populates all cached custom fields
4. Sets status to "Ready to Start" if conditions met

**Material Status vs Readiness Status:**

| Material Status | Readiness Status | Meaning |
|----------------|------------------|---------|
| Waiting for Material | Waiting for Material | No stock in WIP yet |
| Material Available | Ready to Start* | Stock exists, dependencies met |
| Material Short | Blocked | Insufficient stock in WIP |
| N/A | Waiting for Previous Operation | Stock available, waiting on prior op |
| N/A | In Progress | Currently running |
| N/A | Completed | Already finished |

*Readiness Status = "Ready to Start" only if ALL conditions met:
- Material Available
- Previous Operation Complete
- Work Order Submitted
- Job Card Not Completed
- Workstation Available (optional)

**Evaluation Triggers:**
1. **WO Submit** → Create JCs + Evaluate ALL conditions (including current WIP stock)
2. **Material Transfer** → Refresh that WO's JCs only (via `SE.work_order` link)
3. **Operation Complete** → Refresh downstream JCs only (dependency check, material optional)
4. **Manual Refresh** → On-demand evaluation

**Timestamp Tracking:**
- `custom_dependency_last_updated` tracks when readiness was last evaluated
- Provides audit trail and confidence in status accuracy

**Rationale:** WO submission is **production release**, not just planning. Material may already be in WIP (transferred earlier or excess from previous WO). Immediate evaluation provides accurate status from the moment of release.

---

### JC-004: Job Card Auto-Refresh

**Rule:** Job Card readiness status must be refreshed on key execution events.

**Action:**
- Trigger Job Card Readiness Engine
- Update cached fields:
  - `custom_material_status`
  - `custom_readiness_status`
  - `custom_material_shortage_details`
  - `custom_blocked_by`
  - `custom_dependency_last_updated`

**Event-Driven Refresh Triggers:**

| Event | Trigger | Scope | Material Check |
|-------|---------|-------|----------------|
| WO Submit | Production Release | All JCs in WO | ✅ Yes (Current WIP) |
| Material Transfer Submit | Inventory Commitment | All JCs in that WO | ✅ Yes |
| Material Return | Inventory Adjustment | All JCs in that WO | ✅ Yes |
| Operation Complete | Dependency Change | Downstream JCs only | Optional |
| Stock Reconciliation (WIP) | Exception | Affected JCs | ✅ Yes |
| Manual Refresh | User Action | Selected JCs | ✅ Yes |

**Implementation Principle:** Work Order is immutable after submission. No refresh needed for WO edits.

---

### JC-005: Job Card Work Order Link

**Rule:** Every Job Card must be linked to a Work Order.

**Validation:**
- work_order field is required
- Cannot submit Job Card without work_order

---

## Material Readiness Rules

### MR-001: Cumulative Transfer Validation

**Rule:** Material availability is based on **cumulative available quantity**, not individual Stock Entries.

**Calculation:**
```
Available Qty = Sum(all Material Transfer entries to WIP)
              + Sum(Stock Balance in WIP)
              - Sum(Reserved Qty)
```

**Example:**
```
Required: 10 kg
Transfer 1: 4 kg
Transfer 2: 3 kg
Transfer 3: 3 kg
Total Available: 10 kg ✅ (Ready)
```

---

### MR-002: Material Classification

**Rule:** Materials must be classified by type for appropriate validation.

**Classification:**
- **Raw Material:** Purchased, no BOM
- **Purchased Component:** Purchased, used in assembly
- **Manufactured Component:** Has BOM, produced internally
- **Common Component:** Used in 3+ different BOMs
- **Sub Assembly:** Has BOM, intermediate product
- **Subcontracted Item:** is_sub_contracted_item = True

---

### MR-003: Source-Agnostic Availability

**Rule:** MES validates material **readiness**, not **source**.

**Principle:**
- MES does not care if material came from:
  - Internal manufacturing
  - Purchase order
  - Subcontract receipt
  - Existing inventory
  
- MES only checks: **Is the quantity available?**

**Exception:** Planning layer determines source.

---

### MR-004: Common Component Handling

**Rule:** Common components (Fins, Turbulators) are validated against **global stock**, not specific Work Orders.

**Validation:**
- Check total stock in Common Component Warehouse
- Do not check which Work Order produced it
- Allow consumption from any source

**Rationale:** Common components are produced in bulk and consumed across multiple Finished Goods.

---

### MR-005: Existing Inventory Priority

**Rule:** Existing inventory has **equal priority** with newly manufactured stock.

**Principle:**
- If 100 units exist in stock, they can be used immediately
- Do not insist on production from a new Child Work Order
- MES validates availability, not production source

**Exception:** Traceability requirements (tracked separately)

---

### MR-006: Warehouse-Specific Validation

**Rule:** Each operation validates materials in its **assigned WIP warehouse**.

**Configuration:**
- Operation.default_wip_warehouse (overrides company default)
- Manufacturing Settings.default_wip_warehouse (company default)

**Validation:**
- Check material availability in specific WIP warehouse
- Do not check other warehouses unless configured

---

### MR-007: Material Shortage Diagnostics

**Rule:** When material is not available, provide **actionable diagnostics**.

**Required Information:**
- Item code and name
- Required quantity
- Available quantity
- Shortage quantity
- Reason (e.g., "Pending transfer from PO-2026-001")
- Action (e.g., "Check with warehouse")

**Format:** Clear, operator-friendly message

---

### MR-008: Multiple Transfer Support

**Rule:** Materials can be transferred in **multiple Stock Entries**.

**Example:**
```
Required: 100 kg
Transfer 1: 40 kg (SE-001)
Transfer 2: 35 kg (SE-002)
Transfer 3: 25 kg (SE-003)
Status: Ready (100 kg cumulative)
```

**Validation:** Sum all transfers, not check individual entries.

---

### MR-009: Material Type Validation Strategy

**Rule:** Different material types use different validation approaches.

| Material Type | Validation Approach |
|---------------|---------------------|
| Raw Material | Check cumulative transfers to WIP |
| Purchased Component | Check cumulative transfers to WIP |
| Manufactured Component | Check available stock in WIP/Stores |
| Common Component | Check global stock regardless of source WO |
| Sub Assembly | Check available quantity |
| Subcontracted Item | Check subcontract receipt status |

---

### MR-010: Material Transfer from Stores to Production

**Rule:** Production starts only after required materials have been transferred by Stores to the Department Warehouse.

**Business Process:**
```
Production Plan
        │
Generate Work Orders
        │
Planner submits Work Order
        │
────────────────────────────────────────
Stores Responsibility Begins
────────────────────────────────────────
        │
Transfer Material
RM / BOF Store
        │
Department Warehouse (WIP)
        │
────────────────────────────────────────
Production Responsibility Begins
────────────────────────────────────────
        │
Material Readiness Validation
        │
Release Job Cards
        │
Execute Production
```

**Ownership:**

| Activity | Department |
|----------|------------|
| Production Planning | Planning |
| Work Order Release | Planning |
| Material Picking | Stores |
| Material Transfer to WIP | Stores |
| Material Availability Validation | MES |
| Job Card Execution | Production |
| Production Reporting | Production |
| Finished Goods Receipt | Production |

**Material Flow:**
```
Incoming Inspection
        │
───────────────
RM Store
───────────────
        │
        │
───────────────
BOF Store
───────────────
        │
        │
Material Transfer (By Stores)
        │
        ▼
Department Warehouse (CNC / W / Ralu Weld / RP ...)
        │
Material Readiness
        │
Job Card Start
        │
Manufacturing
```

**MES Principle:**
The Material Readiness Engine shall not determine readiness based solely on BOM requirements. Instead, it shall validate that required materials have already been transferred into the **Department Warehouse** assigned to the Work Order. Only then shall the Job Card become eligible for execution.

**Benefits:**
- Clear separation of responsibilities between Planning, Stores, and Production
- Stores control inventory issuance and accountability
- Production focuses solely on manufacturing execution
- Material Readiness is based on **actual stock available in the production department**, not on planned BOM requirements
- Aligns MES with physical flow of materials on shop floor
- Reduces operator workload by eliminating material issue transactions from production process

---

### MR-011: Stores Completeness Rule (Cumulative Availability)

**Rule:** Material Transfer against a Work Order is treated as a **working set**, not necessarily a single transaction.

**Principle:**
The MES must evaluate **cumulative material availability** in the Department Warehouse for the Work Order, regardless of whether Stores transfers the material:
- In a single Stock Entry
- In multiple partial Stock Entries
- Over multiple days

**Validation Logic:**
```
Required Qty for WO = 100 kg

Transfer 1 = 40 kg (SE-001)
Transfer 2 = 35 kg (SE-002)
Transfer 3 = 25 kg (SE-003)
─────────────────────────────
Cumulative Available = 100 kg ✅

Material Readiness = Ready
Job Cards can start
```

**Rationale for Teksons:**
- Raw materials and BOF parts may arrive or be issued at different times
- Common sub-assemblies may be manufactured and transferred in batches
- Large Work Orders may be supplied in multiple stages
- Production should begin as soon as required materials for current stage are available
- Should not depend on a single transfer document

**MES Implementation:**
The Material Readiness Engine shall validate:
```
Sum(all Material Transfer entries to Department Warehouse for WO)
>=
Work Order Required Quantity
```

**Not:**
```
Check if single Stock Entry exists for full quantity
```

**Example:**
```
Work Order: WO-2026-001
Item: Copper Tube
Required: 100 kg

Stock Entries:
SE-001: 40 kg (01-Aug)
SE-002: 35 kg (02-Aug)
SE-003: 25 kg (03-Aug)

Status after SE-003:
Cumulative = 100 kg ✅
Material Readiness = Ready
Job Cards can start
```

**Benefits:**
- Flexibility for Stores to issue materials in stages
- Production can start as soon as sufficient material is available
- No artificial dependency on single Stock Entry
- Reflects real-world material issuance practices
- Supports partial deliveries and batch transfers

---

## Work Order Completion Rules

### WO-001: Auto-Completion Trigger

**Rule:** When all Job Cards for a Work Order are completed, the Work Order should auto-complete.

**Conditions:**
- All Job Cards status = "Completed"
- Produced qty >= Planned qty
- No pending operations

**Action:**
- Create Manufacture Stock Entry
- Submit Stock Entry
- Update Work Order status to "Completed"

---

### WO-002: Duplicate Stock Entry Prevention

**Rule:** Do not create duplicate Manufacture Stock Entries for the same Work Order.

**Validation:**
- Check if Stock Entry exists with:
  - work_order = current WO
  - purpose = "Manufacture"
  - docstatus = 1 (submitted)

**Action:** If exists, skip creation and update status only.

---

### WO-003: Work Order Status Update

**Rule:** Work Order status must reflect actual completion progress.

**Status Values:**
- Not Started: No Job Cards submitted
- In Process: Some Job Cards completed
- Completed: All Job Cards completed + Stock Entry submitted

**Update Trigger:**
- Job Card submit/cancel
- Stock Entry submit/cancel

---

### WO-004: Production Quantity Achievement

**Rule:** Work Order cannot complete until produced qty >= planned qty.

**Validation:**
```
Sum(Job Card for_quantity where status = "Completed") >= Work Order qty
```

---

### WO-005: Work Order Release Boundary

**Rule:** MES begins execution only **after Work Order submission**.

**Principle:**
- Draft Work Orders: Planning layer
- Submitted Work Orders: Execution layer (MES)
- MES does not intervene in Draft → Submit workflow

---

## Dependency Validation Rules

### DV-001: Previous Operation Completion

**Rule:** An operation cannot start until its immediate previous operation is completed.

**Validation:**
- Get Job Card with sequence_id = current - 1
- Check status = "Completed"

**Exception:** First operation (sequence_id = 1)

---

### DV-002: Operation Sequence Integrity

**Rule:** Job Cards must follow sequential operation order.

**Validation:**
- sequence_id must be consecutive (1, 2, 3...)
- No gaps in sequence
- No duplicate sequence_ids

---

### DV-003: Multiple Dependencies (Future)

**Rule:** Reserved for future enhancement where an operation may depend on multiple previous operations.

**Status:** Not implemented in Phase 1

---

### DV-004: Dependency Refresh

**Rule:** When a Job Card completes, all dependent Job Cards must be refreshed.

**Action:**
- Find next Job Card (sequence_id + 1)
- Update custom_start_status
- Recalculate material readiness
- Update diagnostics

---

## Diagnostics & Messaging Rules

### DM-001: Clear Operator Messages

**Rule:** Never show generic errors like "Cannot Start" or "Material Not Available".

**Required Format:**
```
[Issue Title]

Item: [Item Code/Name]
Required: [Qty]
Available: [Qty]
Shortage: [Qty]

Reason: [Specific reason]
Action: [Actionable step]
```

---

### DM-002: Diagnostic Categories

**Rule:** All diagnostics must be categorized.

**Categories:**
- `material_shortage` - Material not available
- `dependency_blocking` - Previous operation not complete
- `wo_not_started` - Work Order not submitted
- `validation_passed` - All checks passed
- `warning` - Non-blocking issue
- `error` - Blocking issue

---

### DM-003: Severity Levels

**Rule:** Diagnostics must indicate severity.

**Levels:**
- `none` - Information only
- `low` - Minor issue, can proceed
- `medium` - Warning, review recommended
- `high` - Error, cannot proceed

---

### DM-004: UI-Friendly Formatting

**Rule:** Diagnostics must be formatted for UI display.

**Requirements:**
- Color coding (red=error, orange=warning, green=success)
- Clear title
- Bullet points for details
- Actionable next steps

---

## Warehouse & Inventory Rules

### WH-001: Warehouse Type Classification (Teksons Structure)

**Rule:** Warehouses must use ERPNext Warehouse Group feature with parent-child hierarchy matching Teksons factory structure.

**Warehouse Hierarchy:**

```
Work In Progress Stores (Warehouse Group)
├── WIP-W
├── WIP-RA
├── WIP-RP
├── WIP-CNC
├── WIP-Ralu Weld
└── WIP-Ralu In

Stores (Warehouse Group)
├── Raw Materials Stores
└── BOF Stores

Receipt and Dispatch Stores (Warehouse Group)
├── Incoming Quality Hold Stores
└── Incoming Quality Rejected Stores

Finished Goods (Standalone Warehouse)

Rejected Stores (Standalone Warehouse)

Scrap Stores (Standalone Warehouse)
```

**Department to Warehouse Mapping:**
| Department (Plant Floor) | Warehouse |
|--------------------------|-----------|
| W | WIP-W |
| RA | WIP-RA |
| RP | WIP-RP |
| CNC | WIP-CNC |
| Ralu Weld | WIP-Ralu Weld |
| Ralu In | WIP-Ralu In |

**Rationale:** Warehouse groups provide organizational structure. Materials move between departments, not between every operation.

---

### WH-002: Department-to-Warehouse Mapping

**Rule:** Each department (Plant Floor) maps to its corresponding WIP warehouse under Work In Progress Stores group.

**Mapping:**
```
Plant Floor (Department)
        │
        ▼
Workstation Type
        │
        ▼
Workstation → Warehouse
        │
        ▼
Job Card
```

**Teksons Mapping Table:**
| Plant Floor (Department) | Warehouse | Parent Group |
|--------------------------|-----------|--------------|
| W | WIP-W | Work In Progress Stores |
| RA | WIP-RA | Work In Progress Stores |
| RP | WIP-RP | Work In Progress Stores |
| CNC | WIP-CNC | Work In Progress Stores |
| Ralu Weld | WIP-Ralu Weld | Work In Progress Stores |
| Ralu In | WIP-Ralu In | Work In Progress Stores |

**Configuration:**
- Plant Floor = Department (W, RA, RP, CNC, Ralu Weld, Ralu In)
- Workstation.Warehouse = Corresponding WIP warehouse
- All workstations in same department use same warehouse
- Job Card inherits warehouse from Workstation

**Note:** Department and Plant Floor are the same in Teksons context.

---

### WH-003: Department Warehouse Validation Scope

**Rule:** Job Cards validate materials in their **assigned WIP warehouse** based on Plant Floor.

**Logic:**
```
Job Card
    ↓
Workstation
    ↓
Plant Floor (Department)
    ↓
WIP Warehouse
```

**Material Readiness:**
- All operations within same department use same WIP warehouse
- No stock movement between operations in same department
- Stock moves only when transferring between departments

**Example:**
```
CNC Department (Warehouse: WIP-CNC)
├── Operation 10: Cutting
├── Operation 20: Drilling
└── Operation 30: Deburring

Material Flow:
Raw Materials Stores → WIP-CNC → [JC-10 → JC-20 → JC-30] → WIP-Ralu Weld
```

**Exception:** Common components check global stock across all departments.

---

### WH-004: Incoming Material Flow (Receipt and Dispatch)

**Rule:** All incoming materials flow through Receipt and Dispatch Stores with quality inspection.

**Incoming Material Flow:**
```
Supplier Delivery
        │
        ▼
Receipt and Dispatch Stores
        │
        ▼
Incoming Quality Hold Stores
        │
    Inspection
        │
    ┌───┴─────────────┐
    │                 │
Accepted          Rejected
    │                 │
    ▼                 ▼
┌───┴───────┐    Incoming Quality
│           │    Rejected Stores
Raw Materials  (under Receipt and
Stores       Dispatch Stores)
    │
BOF Stores
(under Stores)
```

**Quality Inspection Process:**
1. Material received in Receipt and Dispatch Stores
2. Transferred to Incoming Quality Hold Stores for inspection
3. If accepted:
   - Raw materials → Raw Materials Stores
   - BOF parts → BOF Stores
4. If rejected → Incoming Quality Rejected Stores (under Receipt and Dispatch Stores)

**MES Behavior:**
- Material Readiness Engine checks appropriate store based on material type
- Only accepted materials in Raw Materials Stores or BOF Stores are available for production

---

### WH-005: Teksons Warehouse Naming Convention

**Rule:** Warehouse names must follow Teksons naming convention with parent-child structure.

**Warehouse Groups (Parent):**
- Work In Progress Stores
- Stores
- Receipt and Dispatch Stores

**Child Warehouses:**
- **WIP Warehouses:** WIP-W, WIP-RA, WIP-RP, WIP-CNC, WIP-Ralu Weld, WIP-Ralu In
- **Stores:** Raw Materials Stores, BOF Stores
- **Receipt and Dispatch:** Incoming Quality Hold Stores, Incoming Quality Rejected Stores
- **Standalone:** Finished Goods, Rejected Stores, Scrap Stores

**Naming Pattern:**
- WIP warehouses: `WIP-[Department]` (e.g., WIP-CNC, WIP-W)
- Quality warehouses: `Incoming Quality [Status] Stores`
- Material stores: `[Material Type] Stores`

**Rationale:** Consistent naming aligned with Teksons operational terminology helps operators and supervisors quickly identify warehouse purposes and material locations.

---

### WH-006: Logical WIP Warehouse Model

**Rule:** The Work Order WIP Warehouse represents a **logical production holding warehouse**, not a physical location for each department.

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

**Key Principles:**
1. Material transferred **once** from Stores to WIP at production start
2. Intermediate department movement tracked via **Job Cards**, not Stock Entries
3. Backflush consumes from WIP and produces to FG
4. Total Stock Entries per WO: **2** (Transfer + Manufacture)

**Benefits:**
- Minimal stock entries (reduced from 4-6 to 2)
- Production progress visible via Job Card status
- Matches supervisor mental model ("in production" vs "in warehouse")
- Simpler configuration and maintenance

---

### WH-007: Warehouse Resolution Priority

**Rule:** Work Order warehouses are auto-populated based on priority hierarchy.

**FG Warehouse Priority:**
1. Production Plan `fg_warehouse` (override)
2. BOM `target_fg_warehouse` (mandatory field)
3. Manufacturing Settings Default FG

**WIP Warehouse Priority:**
1. Production Plan `for_warehouse` (override)
2. First Operation's Department WIP (from Process Plan)
3. Manufacturing Settings Default WIP

**Implementation:**
```python
# FG Warehouse
if production_plan.fg_warehouse:
    wo.fg_warehouse = production_plan.fg_warehouse
elif bom.target_fg_warehouse:
    wo.fg_warehouse = bom.target_fg_warehouse
else:
    wo.fg_warehouse = manufacturing_settings.default_fg_warehouse

# WIP Warehouse
if production_plan.for_warehouse:
    wo.wip_warehouse = production_plan.for_warehouse
elif first_operation.workstation:
    department = workstation.department
    wo.wip_warehouse = f'WIP-{department.split("-")[0]} - TPL'
else:
    wo.wip_warehouse = manufacturing_settings.default_wip_warehouse
```

---

### WH-008: BOM Target FG Warehouse

**Rule:** Every BOM must specify a Target FG Warehouse (mandatory field).

**Purpose:** Defines where finished goods from this BOM should be transferred upon completion.

**Examples:**
- Core Assembly BOM → `WIP-Ralu Weld - TPL` (next department)
- Tank Assembly BOM → `WIP-Ralu Weld - TPL` (next department)
- Final Radiator BOM → `Finished Goods Stores - TPL` (final destination)
- Purchased Sub-assembly BOM → `Incoming Quality Hold Stores - TPL` (QC first)

**Configuration:**
- Custom Field: `target_fg_warehouse` (Link to Warehouse, Mandatory)
- Location: BOM form, after `fg_warehouse` field

**Rationale:** Separates product definition (BOM) from execution details (Process Plan), allowing process changes without modifying BOMs.

---

### WH-009: Cached Material Status

**Rule:** Job Cards maintain cached material availability status to avoid repeated calculations.

**Custom Fields:**
- `custom_material_available` (Check) - Is material available?
- `custom_can_start_operation` (Check) - Can this JC start?
- `custom_material_status_details` (Text) - Human-readable status
- `custom_last_evaluated` (Datetime) - When was this calculated
- `custom_blocked_by` (Data) - Reason if can't start

**Refresh Triggers:**
1. Work Order submission
2. Material Transfer completion
3. Material Return
4. Operation completion (Job Card submit)
5. Production quantity change

**Start Button Validation:**
- Check cached field: `custom_can_start_operation`
- Quick stock verification (< 100ms)
- Confirm JC not already running

**Rationale:** Provides immediate feedback to operators without server-side recalculation on every click.

---

### WH-010: Stock Entry Validation

**Rule:** Stock Entries must validate warehouse existence and material availability before submission.

**Material Transfer Validation:**
- ✅ Material available in source warehouse
- ✅ WIP warehouse exists and is not a group node
- ✅ Work Order is submitted
- ✅ Quantity <= WO required qty

**Manufacture Entry Validation:**
- ✅ All Job Cards completed
- ✅ Material available in WIP warehouse
- ✅ FG warehouse exists and is not a group node
- ✅ Quantity <= WO pending qty

**Error Messages:**
- "Material not available in {warehouse}. Required: {qty}, Available: {available_qty}"
- "Warehouse {warehouse} is a group node. Please select a child warehouse."
- "Work Order {wo} is not submitted. Please submit before creating Stock Entry."

---

## Configuration Rules

### CFG-001: Manufacturing Settings

**Rule:** All MES features must be configurable.

**Settings:**
- Enable MES (master switch)
- Enable Material Readiness
- Enable Dependency Validation
- Enable Diagnostics
- Enable Auto Completion
- Strict Validation (error vs warning)
- Debug Logging (development mode)

---

### CFG-002: Warehouse Configuration

**Rule:** All warehouses must be configurable.

**Configuration:**
- Raw Material Warehouse
- Common Component Warehouse
- Default WIP Warehouse
- Finished Goods Warehouse
- Reject Warehouse
- Rework Warehouse

---

### CFG-003: Execution Settings

**Rule:** Execution behavior must be configurable.

**Settings:**
- Allow Partial Completion
- Allow Over Production
- Auto Refresh Job Cards
- Diagnostic Level (basic/detailed)

---

## Architectural Principles

### ARCH-001: Separation of Responsibilities

**Rule:** Planning and Execution are separate layers.

**Principle:**
- **Planning Layer:** Decides source (Internal/Purchase/Subcontract)
- **Execution Layer (MES):** Validates availability
- **Monitoring Layer:** Provides diagnostics

---

### ARCH-002: Service-Oriented Architecture

**Rule:** All business logic lives in Services, not in overrides.

**Principle:**
- Controllers call services
- APIs call services
- UI calls services
- No duplicated logic

---

### ARCH-003: Configuration Over Hard-Coding

**Rule:** Use Manufacturing Settings for flexibility.

**Principle:**
- Enable/disable features via settings
- Configure warehouses via settings
- Avoid hard-coded values

---

### ARCH-004: Clear Diagnostics

**Rule:** Never return generic errors.

**Principle:**
- Provide detailed, actionable messages
- Include reason and action
- Format for UI display

---

### ARCH-005: Backward Compatibility

**Rule:** Maintain compatibility with existing functionality.

**Principle:**
- New features don't break existing workflows
- Provide migration path
- Support graceful degradation

---

## Rule Change Management

### Change Process

1. **Propose:** Submit rule change request
2. **Review:** Technical team reviews impact
3. **Approve:** Customer approves (if business impact)
4. **Implement:** Update code and documentation
5. **Test:** Validate with test cases
6. **Deploy:** Release with version increment

### Version Control

- Rules are versioned independently
- Each rule has version history
- Deprecated rules marked but retained for reference

---

## Traceability Matrix

| Rule ID | Implemented In | Test Case | Status |
|---------|---------------|-----------|--------|
| JC-001 | dependency_engine.py | TC-JC-001 | ✅ Implemented |
| JC-002 | execution_engine.py | TC-JC-002 | ✅ Implemented |
| MR-001 | material_readiness.py | TC-MR-001 | ✅ Implemented |
| MR-002 | material_readiness.py | TC-MR-002 | ✅ Implemented |
| WO-001 | execution_engine.py | TC-WO-001 | ✅ Implemented |
| DV-001 | dependency_engine.py | TC-DV-001 | ✅ Implemented |
| DM-001 | messages.py | TC-DM-001 | ✅ Implemented |

*(To be expanded as implementation progresses)*

---

## Glossary

| Term | Definition |
|------|------------|
| MES | Manufacturing Execution System |
| WIP | Work In Progress |
| BOM | Bill of Materials |
| WO | Work Order |
| JC | Job Card |
| SE | Stock Entry |
| FG | Finished Goods |
| RM | Raw Material |
| OEE | Overall Equipment Effectiveness |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-31 | OSDuo Tech LLP | Initial business rules specification |

**Approved By:** ___________________  
**Date:** ___________________

**Next Review:** After Phase 1 UAT completion

---

*This document is maintained in the repository and updated as business rules evolve. All code implementations must adhere to these rules.*
