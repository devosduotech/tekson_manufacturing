# Tekson MES — User Manual

**Version:** v15.0.1
**For:** Production Planner, Stores Person, Production Supervisor, Operator
**Date:** August 2026

---

## Roles & Responsibilities

| Role | Actions |
|------|---------|
| **Production Planner** | Create Production Plan, Release Work Orders |
| **Stores Person** | Transfer materials from Stores to Department WIP |
| **Production Supervisor** | Monitor readiness, resolve blocking issues |
| **Operator** | Start and complete Job Cards |

---

## Production Planner

### Creating a Production Plan

1. **Manufacturing → Production Plan → Add Production Plan**
2. Select the finished good item and quantity
3. Click **Get Items**
4. Review sub-assembly requirements
5. **Save → Submit**

### Releasing Work Orders

1. Open the submitted Production Plan
2. Click **Create Work Order**
3. All WOs are created with correct warehouses and quantities
4. WIP warehouse is auto-assigned from the BOM's first operation

### Quantity Rounding

Some BOMs produce multiple units from one manufacturing cycle. The system automatically rounds Work Order quantities up to the nearest batch multiple. Example:
- BOM produces 6 pieces per cycle
- Demand = 4 → WO created for 6 (1 batch)
- Excess goes to WIP inventory

---

## Stores Person

### Transferring Materials to WIP

1. **Stock → Stock Entry → Add Stock Entry**
2. Purpose: **Material Transfer**
3. Do NOT link to a specific Work Order
4. Source Warehouse: Raw Material Stores / BOF Stores
5. Target Warehouse: Department WIP (e.g., WIP-CNC - TPL)
6. Add items and quantities
7. **Save → Submit**

### Which WIP to Use?

Each Work Order's Job Cards show their department WIP. Transfer materials for the first operation to that operation's WIP. The MES checks stock in the JC's WIP warehouse.

---

## Production Supervisor

### Checking Readiness

1. Open a Work Order
2. View the Job Cards list
3. Each JC shows:
   - **Can Start Operation** — checked when ready
   - **Material Available** — checked when materials are in WIP
   - **Readiness Status** — "Ready to Start" or "Blocked"

### Resolving Blocked JCs

If a JC shows "Blocked":
- Check `custom_blocked_by` field for the reason
- "Waiting for Previous Operation" → complete the previous JC first
- "Materials not available" → transfer materials to WIP
- "Child WO not completed" → complete sub-assembly work orders first

### Monitoring Work Order Progress

```
WO → Operations table shows completion status per operation
JC → Individual JC shows status, start/end times, completed qty
```

---

## Operator

### Starting a Job Card

1. Open the assigned Job Card
2. Review the readiness indicators
3. Click **Start**
4. If blocked, a message explains exactly what's missing
5. Enter actual start time
6. **Save**

### Completing a Job Card

1. Open the in-progress Job Card
2. Enter:
   - Actual end time
   - Completed quantity
3. Set status to **Completed**
4. Click **Submit**

The next Job Card in the sequence automatically becomes ready (if dependencies are met).

### Auto-Completion

When the **last** Job Card of a Work Order is submitted:
- A Manufacture Stock Entry is automatically created
- The Work Order status changes to "Completed"
- This may take 2-3 seconds

---

## Common Error Messages

| Message | What To Do |
|---------|------------|
| "Cannot start: Previous Operation Not Complete" | Complete the earlier JC first |
| "Cannot start: Materials not available in WIP-xxx" | Ask Stores to transfer materials |
| "Child WO status: In Process" | Complete the sub-assembly WO first |
| "Required X, Available Y" | X units needed, only Y in WIP — transfer more |

---

## Quick Reference

### Job Card Status Flow

```
Open → Start → Work In Progress → Complete → Submit → Done
```

### Work Order Status Flow

```
Draft → Submit → In Process → (All JCs done) → Completed
```
