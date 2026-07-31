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

**Exception:** First operation (sequence_id = 1) has no previous dependency.

---

### JC-002: Job Card Completion Permission

**Rule:** A Job Card can only be completed if the for_quantity has been produced.

**Validation:**
- Check total_completed_qty >= for_quantity

---

### JC-003: Job Card Material Check

**Rule:** A Job Card should not start if required materials are not available.

**Validation:**
- Check Material Readiness for parent Work Order
- All materials must be available or transferred to WIP

**Severity:** Warning (can be overridden with Strict Validation disabled)

---

### JC-004: Job Card Auto-Refresh

**Rule:** When a Job Card is submitted, dependent Job Cards must be refreshed.

**Action:**
- Find next Job Card (sequence_id + 1)
- Update custom_start_status
- Trigger diagnostic refresh

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

### MR-010: Planning vs. Execution Boundary

**Rule:** The source of a material is determined by **ERPNext planning**. The MES only validates **readiness**.

**Principle:**
- Planning decides: Internal vs Purchase vs Subcontract
- Execution checks: Is quantity available?
- MES does not modify planning decisions

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

### WH-001: Warehouse Type Classification

**Rule:** Warehouses must be classified by type to match physical factory structure.

**Types:**
- **Incoming Stores:**
  - RM Store (Raw Materials: sheets, tubes, copper, steel)
  - BOF Parts Store (Bought-out Parts)
- **Department Stores:** Department WIP warehouses
  - CNC Department Store
  - W Department Store
  - Ralu In Department Store
  - Ralu Weld Department Store
  - RP Department Store
  - Assembly Department Store
  - Testing Department Store
  - Painting Department Store
- **Finished Goods Store:** Completed products
- **Quality Stores:**
  - Rework Store
  - Reject Store

**Rationale:** Department stores reflect actual shop-floor movement. Materials move between departments, not between every operation.

---

### WH-002: Department-Centric Warehouse Model

**Rule:** Warehouse configuration follows ERPNext standard hierarchy using Plant Floor.

**Hierarchy:**
```
Plant Floor (Department)
        │
        ▼
Workstation Type
        │
        ▼
Workstation → Warehouse (inherits from Plant Floor)
        │
        ▼
Job Card
```

**ERPNext Standard Mapping:**
| ERPNext Object | Tekson Usage |
|----------------|--------------|
| Plant Floor | Manufacturing Department (CNC, W, Ralu In, Ralu Weld, RP, Assembly, Testing, Painting) |
| Warehouse | Department WIP Store |
| Workstation Type | Capability group (same operation) |
| Workstation | Actual machine or station |
| Operation | Standard ERPNext manufacturing operation |
| Job Card | Execution record |

**Configuration:**
- Plant Floor defines the manufacturing department
- Workstation.Warehouse points to Department Store
- All workstations in same department use same warehouse
- Job Card inherits warehouse from Workstation

**Exception:** If workstation movement between departments becomes frequent, Plant Floor-level warehouse configuration may be added as future enhancement.

---

### WH-003: Department Warehouse Validation Scope

**Rule:** Job Cards validate materials in their **Department Warehouse**.

**Logic:**
```
Job Card
    ↓
Workstation
    ↓
Plant Floor
    ↓
Department Warehouse
```

**Material Readiness:**
- All operations within same department use same warehouse
- No stock movement between operations in same department
- Stock moves only when transferring between departments

**Example:**
```
CNC Department (Warehouse: CNC Department Store)
├── Operation 10: Cutting
├── Operation 20: Drilling
└── Operation 30: Deburring

Material Flow:
RM Store → CNC Department Store → [JC-10 → JC-20 → JC-30] → Ralu Weld Department Store
```

**Exception:** Common components check global stock across all departments.

---

### WH-004: Department-to-Department Material Flow

**Rule:** Material transfers occur between departments, not between individual operations.

**Flow:**
```
Incoming Quality
        │
        ├── RM Store
        └── BOF Parts Store
                 │
        Material Transfer for Manufacture
                 │
        CNC Department Store
                 │
        [All CNC Job Cards]
                 │
        Department Transfer
                 │
        Ralu Weld Department Store
                 │
        [All Ralu Weld Job Cards]
                 │
        Department Transfer
                 │
        Assembly Department Store
                 │
        [Final Assembly Job Cards]
                 │
        Manufacture Stock Entry
                 │
        Finished Goods Store
```

**MES Behavior:**
- When last Job Card of department completes, MES suggests transfer to next department
- No unnecessary stock movement between operations within same department
- Reflects actual physical shop-floor movement

---

### WH-005: Warehouse Naming Convention

**Rule:** Warehouse names must explicitly indicate their purpose.

**Naming Standard:**
- `[Department Name] Department Store` (e.g., "CNC Department Store")
- `RM Store` (Raw Material Store)
- `BOF Parts Store` (Bought-out Parts Store)
- `FG Store` (Finished Goods Store)
- `Rework Store`
- `Reject Store`

**Avoid:** Generic "WIP" naming without department context.

**Rationale:** Clear naming helps operators and supervisors understand inventory ownership and location.

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
