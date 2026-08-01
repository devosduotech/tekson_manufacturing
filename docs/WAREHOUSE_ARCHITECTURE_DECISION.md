# Warehouse Architecture Decision

**Document Type:** Architecture Decision Record  
**Date:** 2026-07-31  
**Status:** Approved for Implementation  
**Related Rules:** WH-001, WH-002, WH-003, WH-004, WH-005

---

## Decision: Department-Centric Warehouse Model with Teksons Structure

The Tekson MES will use a **department-centric warehouse model** leveraging ERPNext's Warehouse Group feature and Plant Floor hierarchy, with Teksons-specific naming convention.

---

## Context

### Initial Approach (Rejected)

Originally, the MES design considered operation-specific warehouses:

```
Operation 10 → WIP-Operation-10
Operation 20 → WIP-Operation-20
Operation 30 → WIP-Operation-30
```

**Problems:**
- Excessive stock transfers between operations
- Doesn't match physical shop-floor reality
- Complex configuration
- Difficult to maintain

### Revised Approach (Adopted)

Department-based warehouses matching physical factory layout:

```
CNC Department
├── Operation 10: Cutting
├── Operation 20: Drilling
└── Operation 30: Deburring
↓
Single Warehouse: CNC Department Store
```

**Benefits:**
- Matches actual material flow
- Reduces unnecessary transfers
- Simpler configuration
- Enables department-level reporting
- Leverages ERPNext standard fields

---

## Warehouse Hierarchy

### Teksons Warehouse Structure (Using ERPNext Warehouse Groups)

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

### ERPNext Standard Mapping

| ERPNext Object | Tekson Usage | Purpose |
|----------------|--------------|---------|
| **Plant Floor** | Manufacturing Department | W, RA, RP, CNC, Ralu Weld, Ralu In |
| **Warehouse** (on Workstation) | WIP Warehouse | WIP-W, WIP-RA, WIP-RP, WIP-CNC, WIP-Ralu Weld, WIP-Ralu In |
| **Workstation Type** | Capability Group | Groups workstations that can perform same operation |
| **Workstation** | Actual Machine/Station | Tube Expander-01, Brazing Station-01, etc. |
| **Operation** | Standard Operation | Cutting, Drilling, Brazing, etc. |
| **Job Card** | Execution Record | Links to Workstation and Operation |

**Note:** Department and Plant Floor are the same in Teksons context.

### Department to Warehouse Mapping

| Plant Floor (Department) | Warehouse | Parent Group |
|--------------------------|-----------|--------------|
| W | WIP-W | Work In Progress Stores |
| RA | WIP-RA | Work In Progress Stores |
| RP | WIP-RP | Work In Progress Stores |
| CNC | WIP-CNC | Work In Progress Stores |
| Ralu Weld | WIP-Ralu Weld | Work In Progress Stores |
| Ralu In | WIP-Ralu In | Work In Progress Stores |

### Material Flow

#### Incoming Material Flow (Receipt and Dispatch)

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

#### Production Material Flow

```
Raw Materials Stores / BOF Stores
        │
        ▼
Material Transfer for Manufacture
        │
        ▼
WIP-CNC (for CNC Department)
        │
        ▼
[All CNC Job Cards]
        │
        ▼
Department Transfer
        │
        ▼
WIP-Ralu Weld (for Ralu Weld Department)
        │
        ▼
[All Ralu Weld Job Cards]
        │
        ▼
Department Transfer
        │
        ▼
WIP-Assembly
        │
        ▼
[Final Assembly Job Cards]
        │
        ▼
Manufacture Stock Entry
        │
        ▼
Finished Goods
```

**Key Principle:** Materials move between **departments** (WIP warehouses), not between individual operations.

---

## Configuration Model

### Workstation Configuration

Each Workstation in ERPNext is configured with:

```
Workstation: Tube Expander-01
├── Workstation Type: Tube Expansion
├── Plant Floor: CNC
└── Warehouse: CNC Department Store
```

### Teksons Department Structure

```
W Department (Plant Floor)
├── Workstation: Press-01 → WIP-W
└── Workstation: Press-02 → WIP-W

RA Department (Plant Floor)
├── Workstation: Station-01 → WIP-RA
└── Workstation: Station-02 → WIP-RA

RP Department (Plant Floor)
├── Workstation: Station-01 → WIP-RP
└── Workstation: Station-02 → WIP-RP

CNC Department (Plant Floor)
├── Workstation: Tube Expander-01 → WIP-CNC
├── Workstation: Tube Expander-02 → WIP-CNC
├── Workstation: Lathe-01 → WIP-CNC
└── Workstation: Lathe-02 → WIP-CNC

Ralu Weld Department (Plant Floor)
├── Workstation: Brazing-01 → WIP-Ralu Weld
└── Workstation: Brazing-02 → WIP-Ralu Weld

Ralu In Department (Plant Floor)
├── Workstation: Station-01 → WIP-Ralu In
└── Workstation: Station-02 → WIP-Ralu In
```

All workstations within same department point to same WIP warehouse.

---

## MES Logic

### Material Readiness Engine

When checking material readiness for a Job Card:

```python
def get_job_card_warehouse(job_card):
    workstation = frappe.get_doc("Workstation", job_card.workstation)
    return workstation.warehouse  # Department Store

def check_material_readiness(job_card):
    warehouse = get_job_card_warehouse(job_card)
    # Check availability in department warehouse
    return check_cumulative_transfers(item_code, warehouse)
```

### Department Transfer Logic

When last Job Card of a department completes:

```python
def on_department_completion(job_card):
    if is_last_job_card_in_department(job_card):
        next_department = get_next_department(job_card.work_order)
        suggest_transfer(
            from_warehouse = job_card.warehouse,
            to_warehouse = next_department.warehouse
        )
```

---

## Benefits

### Operational Benefits

1. **Reflects Physical Reality**
   - Matches actual shop-floor material movement
   - Operators understand "CNC Department Store" intuitively

2. **Reduced Transactions**
   - No stock transfers between operations in same department
   - Only department-to-department transfers

3. **Simplified Configuration**
   - One warehouse per department
   - Easy to understand and maintain

### Reporting Benefits

Enables department-level analytics:
- Department-wise WIP inventory
- Department production queues
- Department supervisor dashboards
- Department capacity planning
- Department efficiency reports
- Department-level scheduling
- Workstation utilization within department

### MES Benefits

1. **Simpler Validation Logic**
   ```
   Job Card → Workstation → Plant Floor → Department Warehouse
   ```
   Instead of maintaining operation-to-warehouse mappings

2. **Natural Department Grouping**
   - All operations in CNC use CNC Department Store
   - Automatic inheritance through Workstation

3. **Future-Ready**
   - Department dashboards map naturally
   - Department capacity monitoring
   - Department-wise scheduling

---

## Alternatives Considered

### Alternative 1: Operation-Specific Warehouses

**Approach:** Each operation has dedicated WIP warehouse

**Rejected because:**
- Excessive stock transfers
- Doesn't match physical layout
- Complex configuration
- Difficult reporting

### Alternative 2: Plant Floor-Level Warehouse (Future Enhancement)

**Approach:** Store warehouse on Plant Floor, workstations inherit automatically

**Logic:**
```
if Workstation.warehouse exists:
    use Workstation.warehouse
else:
    use PlantFloor.warehouse
```

**Decision:** Defer to future release

**Rationale:**
- Current workstation configuration is manageable
- Need to validate frequency of workstation movement
- ERPNext V16 may provide native support
- Keep Phase 1 focused on core MES functionality

**Backlog Item:** If workstation movement between departments becomes frequent, implement Plant Floor-level warehouse configuration with workstation override capability.

---

## Implementation Impact

### Material Readiness Engine

Must determine warehouse from Job Card's Workstation:

```python
# readiness/material_readiness.py
def get_department_warehouse(job_card):
    workstation = frappe.get_doc("Workstation", job_card.workstation)
    return workstation.warehouse
```

### Dependency Engine

No change needed - operates at Job Card level

### Execution Engine

Department completion detection:

```python
# execution/execution_engine.py
def is_last_operation_in_department(job_card):
    current_dept = get_job_card_department(job_card)
    next_jc = get_next_job_card(job_card)
    
    if not next_jc:
        return True
    
    next_dept = get_job_card_department(next_jc)
    return current_dept != next_dept
```

### Configuration

Warehouse naming convention:
- `CNC Department Store`
- `W Department Store`
- `Ralu In Department Store`
- `Ralu Weld Department Store`
- `RP Department Store`
- `Assembly Department Store`
- `Testing Department Store`
- `Painting Department Store`

Avoid generic "WIP" naming.

---

## Testing Implications

Test scenarios must validate:

1. **Department Warehouse Inheritance**
   - TC-WH-001: Job Card inherits warehouse from Workstation
   - TC-WH-002: All workstations in department use same warehouse

2. **Department Transfer**
   - TC-WH-003: Transfer suggested when leaving department
   - TC-WH-004: No transfer within same department

3. **Material Readiness**
   - TC-WH-005: Checks department warehouse, not operation warehouse
   - TC-WH-006: Cumulative transfers to department warehouse

---

## Future Considerations

### V16 Evaluation

When migrating to ERPNext V16:
- Evaluate native Plant Floor warehouse configuration
- Assess if customization is still needed
- Consider standard features before customizing

### Enhancement Backlog

If operational experience indicates frequent workstation movement:

**Enhancement:** Plant Floor-level warehouse configuration

```
Plant Floor: CNC
├── Default Warehouse: CNC Department Store
├── Workstation: Tube Expander-01 (inherits)
├── Workstation: Lathe-01 (inherits)
└── Workstation: Special Machine-01 (override: Special Store)
```

**Decision Criteria:**
- Frequency of workstation reassignment
- Operational complexity
- ERPNext V16 capabilities

---

## References

- **Business Rules:** WH-001, WH-002, WH-003, WH-004, WH-005
- **Implementation:** `readiness/material_readiness.py`, `execution/execution_engine.py`
- **Test Scenarios:** TC-WH-001 through TC-WH-006

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-31 | OSDuo Tech LLP | Initial architecture decision |

**Approved By:** ___________________  
**Date:** ___________________

**Next Review:** During ERPNext V16 migration planning

---

*This decision is documented in the architecture and should be referenced when implementing warehouse-related functionality.*
