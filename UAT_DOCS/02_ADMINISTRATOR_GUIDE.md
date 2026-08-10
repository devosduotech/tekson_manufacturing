# Tekson MES — Administrator Guide

**Version:** v15.0.1
**Date:** August 2026

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Custom Fields](#custom-fields)
3. [BOM Configuration](#bom-configuration)
4. [Warehouse Setup](#warehouse-setup)
5. [Workstation Configuration](#workstation-configuration)
6. [Troubleshooting](#troubleshooting)

---

## System Overview

The Tekson MES extends ERPNext Manufacturing with three key controls:

| Control | What It Does |
|---------|-------------|
| **Dependency Validation** | Blocks a Job Card from starting until all previous operations are complete |
| **Material Readiness** | Checks that raw materials exist in the department's WIP warehouse before allowing JC start |
| **Child WO Completion** | Blocks parent Work Order until all sub-assembly Work Orders are finished |

### Architecture

```
ERPNext (Inventory, Costing, Backflush)
        ↓
MES Layer (Readiness, Dependency, Workflow)
        ↓
Operator (Start/Complete Job Cards)
```

The MES does NOT replace ERPNext. It adds shop-floor controls.

---

## Custom Fields

### Job Card Fields

| Field | Type | Purpose |
|-------|------|---------|
| `custom_can_start_operation` | Check | Set by system — operator cannot edit |
| `custom_material_available_for_operation` | Check | Set by system |
| `custom_readiness_status` | Select | Ready to Start / Blocked / Waiting |
| `custom_material_status` | Select | Material Available / Waiting / Short |
| `custom_blocked_by` | Data | Shows what's blocking this JC |
| `custom_start_status` | Select | Operator status indicator |
| `custom_material_status_details` | Text | Detailed shortage message |
| `custom_operation_item_code` | Data | What's being produced |

**Important:** These fields are **system-managed**. Do not add them to user-editable forms. The MES engine populates them automatically.

---

## BOM Configuration

### Required Settings per BOM

#### Items Table

| Field | Required | Purpose |
|-------|----------|---------|
| `Item Code` | ✅ | Standard |
| `Qty` | ✅ | Per-unit consumption |
| `Source Warehouse` | ✅ | Where material comes FROM |
| `Operation` | ✅ | Which BOM operation consumes this item |

#### Operations Table

| Field | Required | Purpose |
|-------|----------|---------|
| `Operation` | ✅ | Operation name |
| `Workstation Type` | ✅ | Which type of workstation performs this |

**Example:**

| Item | Qty | Source Warehouse | Operation |
|------|-----|-----------------|-----------|
| Aluminium Extrusion | 0.487 | Raw Material Stores - TPL | Size Cutting |
| Helicoil Insert M10 | 4.0 | BOF Stores - TPL | Helicoil Insert |

### Multi-Level BOM

For sub-assemblies, the child BOM's `Target FG Warehouse` should match the parent BOM item's `Source Warehouse`. This ensures child WO output flows to where the parent expects it.

---

## Warehouse Setup

### Required Warehouses

| Warehouse | Type | Purpose |
|-----------|------|---------|
| `Stores - TPL` | Raw Material | Main stores |
| `BOF Stores - TPL` | Raw Material | BOF parts |
| `WIP-CNC - TPL` | WIP | CNC department |
| `WIP-Ralu Weld - TPL` | WIP | Welding department |
| `WIP-Ralu In - TPL` | WIP | Assembly input |
| `WIP-RP - TPL` | WIP | Press department |
| `WIP-RA - TPL` | WIP | Assembly |
| `Finish Goods Stores - TPL` | Finished Goods | Completed products |

### Department WIP Model

Each department has its own WIP warehouse. Materials are transferred from Stores to the relevant department WIP. The MES checks stock in the department WIP before allowing a Job Card to start.

---

## Workstation Configuration

Each Workstation must have:
- `Workstation Type` — used to auto-assign during JC creation
- `Plant Floor` — used to derive the WIP warehouse name

Example:
```
Workstation: W-26 Accurate Cutting Machine
Type: Accurate Cutting
Plant Floor: CNC
→ WIP Warehouse: WIP-CNC - TPL
```

---

## Troubleshooting

### JC shows "Can Start = 0" but operator can start it

This is normal. "Can Start" is a display indicator. The actual block happens server-side when the operator clicks Start. If materials + dependencies are met, the JC starts.

### "Material Not Available" error when starting JC

Check:
1. Have materials been transferred to the department WIP warehouse?
2. For manufactured components — are the child Work Orders completed?
3. Is the previous JC in the sequence completed?

### Work Order stays "In Process" after all JCs completed

Wait 2-3 seconds and refresh the page. The auto-complete runs via a background worker. If still In Process after 30 seconds, check:
1. All JCs show `status = "Completed"` and `docstatus = 1`
2. Stock exists in WIP warehouses for all raw materials

### BOM Item Operation field is blank

This is required. Edit the BOM and set the `Operation` field on each row in the Items table.
