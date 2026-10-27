# Material Transfer Pick List — Query Report

**Report Name:** Material Transfer Pick List
**Type:** Script Report
**Reference DocType:** Work Order
**Module:** Tekson Manufacturing
**Status:** Released on `develop` / `main` (operation-driven target + Operation column since v15.1.37)

---

## Purpose

Gives the store team a single list of raw materials that still have to be moved
from source warehouses into the department WIP warehouse for every **open**
Work Order.

Entry points:

- Desk → Reports → **Material Transfer Pick List**
- Workspace **Tekson Manufacturing**
- Work Order List → row action **Pick List** (`public/js/material_transfer_pick_list.js`)

---

## Filters

| Filter | Type | Default | Notes |
|---|---|---|---|
| From Date | Date | `2026-01-01` | Inclusive |
| To Date | Date | `2026-12-31` | Inclusive |

Both are mandatory. The range is applied to **Work Order `planned_start_date`**
(not `creation`), so an open WO scheduled outside the window is not listed.

---

## Columns

| Column | Field | Source |
|---|---|---|
| Work Order | `work_order` | `Work Order.name` |
| Item | `item_code` | `BOM Item.item_code` |
| Item Name | `item_name` | `BOM Item.item_name` |
| Operation | `operation` | `BOM Item.operation` (added v15.1.37) |
| Qty/Piece | `required_per_piece` | `BOM Item.qty` |
| Required | `required_total` | `BOM Item.qty × Work Order.qty` |
| From Warehouse | `source_warehouse` | see resolution below |
| Available | `available_qty` | `Bin.actual_qty` at source |
| To Transfer | `balance_to_transfer` | `required_total − already_in_wip` (min 0) |
| To (WIP) | `target_warehouse` | see resolution below (operation-driven since v15.1.37) |

---

## Which Work Orders are included

`reports/material_transfer_pick_list/material_transfer_pick_list.py`:

```sql
WHERE wo.docstatus = 1
  AND wo.status NOT IN ('Completed', 'Closed', 'Stopped', 'Cancelled')
  AND DATE(wo.planned_start_date) BETWEEN %s AND %s
```

- `docstatus = 1` → Draft and Cancelled documents are already excluded
- `status NOT IN (...)` → **Completed, Closed, Stopped and Cancelled** are excluded
- Remaining open statuses in practice: **Not Started**, **In Process**, **Submitted**

Each included WO contributes one row per **BOM Item** of its `bom_no`.
A WO with no BOM, or a BOM that no longer exists, is skipped and logged as a
warning.

---

## Warehouse resolution and balance

1. **Source** — `BOM Item.source_warehouse` → `Work Order.source_warehouse` → `''`
2. **Target (WIP)** — driven by the BOM Item's operation (v15.1.37):
   `BOM Item.operation` → matching `BOM Operation` row (case/whitespace
   tolerant, v15.1.38) → `workstation_type` (or direct workstation) → first
   `Workstation` → `plant_floor` → `WIP-{plant_floor} - TPL` (must exist).
   If configuration
   cannot be resolved, the Job Card's `wip_warehouse` for that
   (WO, operation) is used, and failing that the Job Card's
   `workstation` → `plant_floor` (v15.1.39). A *unique* `WIP-{floor}` naming
   variant is accepted when `WIP-{floor} - TPL` does not exist; ambiguous
   matches are never guessed. **`Work Order.wip_warehouse` (the first-operation
   warehouse) is never used for items that carry an operation** — only for
   items with no operation, and if no target can be resolved the target cell
   is left blank and the reason is logged
   (`frappe.logger().warning`). Shared resolver:
   `utils/operation_warehouse.py`.
3. `already_in_wip` — `Bin.actual_qty` for the item in the **target** WIP warehouse
4. `balance_to_transfer = max(0, required_total − already_in_wip)`

`available_qty` is informational only; the report does **not** hide rows that
are short of stock or that are already fully transferred.

---

## Known limitations

- **N+1 Bin lookups** — two `Bin` queries per BOM Item. With many open WOs the
  report can exceed 15s, which triggers Frappe's prepared-report automation
  (see below). Tracked in `PENDING_FIXES.md`.
- Rows with `balance_to_transfer = 0` (material already in WIP) are still listed.
- `get_columns()` returns 10 columns (Operation added in v15.1.37); the report
  JSON still declares its original 10 — a legacy `wip_warehouse` column
  (equals `target_warehouse`) instead of `operation`. The Python columns are
  what render. Tracked as P2 in `PENDING_FIXES.md`.

---

## Frappe wiring (do not move these files)

Frappe looks for a Script Report in two exact places — both are required:

| Purpose | Required path |
|---|---|
| Filter definitions (JS) | `<app>/<module>/report/<scrub(name)>/<scrub(name)>.js` |
| Execution (Python) | `<app>.<module>.report.<scrub(name)>.<scrub(name)>.execute` |

For this report that is:

```
tekson_manufacturing/tekson_manufacturing/report/material_transfer_pick_list/material_transfer_pick_list.js
tekson_manufacturing/tekson_manufacturing/report/material_transfer_pick_list/material_transfer_pick_list.py
```

The `.py` at that path only re-exports; the implementation lives in
`tekson_manufacturing/reports/material_transfer_pick_list/material_transfer_pick_list.py`.

### Prepared-report automation

`Report.execute_script_report()` starts a 15-second timer that flips
`Report.prepared_report = 1`. The prepared branch returns **no `columns` /
`result` keys**, which the UI renders as *"Nothing to show"*.

The report JSON pins:

```json
"prepared_report": 0,
"disable_prepared_report_automation": 1
```

To repair an already-flipped site:

```python
frappe.db.set_value('Report', 'Material Transfer Pick List', {
    'prepared_report': 0,
    'disable_prepared_report_automation': 1,
    'javascript': '',
})
frappe.db.commit()
frappe.clear_cache()
```

`db.set_value` is required — `Report.validate()` rejects saves when
`developer_mode` is off.

---

## Verification

```python
# bench --site <site> console
from frappe.desk.query_report import run

res = run('Material Transfer Pick List', {'from_date': '2026-01-01', 'to_date': '2026-12-31'})
print(len(res['columns']), len(res['result']))
```

Expected on the UAT data set: `10 35` (10 columns since v15.1.37; the row
count was measured before the open-WO filter and drops once
Completed/Closed WOs are excluded).
