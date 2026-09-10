# Tekson Manufacturing - Project Status

## Current Version: v15.1.9 (develop + main)

---

## Completed Features

### 1. Daily Material Planning (MR Generation)
**Status: ✅ Working**

- Generates Material Requests grouped by department WIP warehouse
- Source warehouse fallback chain: `item.source_warehouse → wo.source_warehouse → default warehouse`
- Circular BOM guard (`_seen` set) to prevent infinite recursion
- Company field added to Material Request (required in ERPNext v15)
- Frontend error handlers fixed for frappe v15 (`xhr.responseText` parsing)

**Key Files:**
- `planning/material_planning_service.py` — MR generation logic
- `public/js/production_plan_mr.js` — Production Plan MR button
- `page/material_planning/material_planning.js` — Material Planning page

### 2. BOM Routing Corrections (R215 Combi Cooler)
**Status: ✅ Applied**

Corrected department routing for 7 end plate BOMs:
- **Shearing** → W Dept (WIP-W)
- **Sr. No. Punching** → RA Dept (WIP-RA)
- **Folding** → RP Dept (WIP-RP)
- **Core Assembly** → Ralu In Dept (WIP-Ralu In)

**Key Files:**
- `BOMs/BOM_full r215 combi cooler.csv` — Corrected BOM data
- `BOMs/R215_Combi_Cooler_Workflow.drawio` — Workflow diagram

### 3. custom_start_status Field Standardization
**Status: ✅ Applied**

Reduced from 7 values to 5:
1. `Awaiting Material` — raw materials not in WIP warehouse
2. `Awaiting Previous Operation` — previous JC not completed
3. `Ready to Start` — both material available AND previous op complete
4. `In Progress` — JC status is "Work In Progress"
5. `Completed` — JC status is "Completed"

**Key Files:**
- `mes/dataclasses.py` — ReadinessStatus enum aligned to display values
- `readiness/job_card_readiness.py` — Status mapping in `apply_result_to_job_card`
- `services/job_card_service.py` — `update_start_status` logic
- `execution/execution_engine.py` — Material check before "Ready to Start"
- `patches/update_job_card_start_status_options.py` — DB patch for Select field options

### 4. Stock Entry Hook - custom_start_status Auto-Update
**Status: ✅ Working**

After Material Transfer to department WIP, Job Cards now auto-update:
- `custom_start_status` → "Ready to Start" (if first JC with materials available)
- `custom_can_start_operation` → 1
- `custom_material_available_for_operation` → 1

**Root Causes Fixed:**
1. `validate_manufacturing_role()` blocked Stock Users — removed from SE hook
2. `apply_result_to_job_card` used `frappe.db.set_value()` bypassing validate hook — changed to `doc.save()`
3. SE hook only handled "Material Transfer for Manufacture" — now also handles "Material Transfer" (MR flow)
4. For "Material Transfer" SEs (no work_order linked), finds WOs by matching `t_warehouse` against Job Card `wip_warehouse`

**Key Files:**
- `mes/mes_coordinator.py` — `on_stock_entry_submit` hook handler
- `readiness/job_card_readiness.py` — `apply_result_to_job_card` (uses `doc.save()`)
- `utils/job_card_utils.py` — `update_job_card_status` validate hook

---

## Architecture Summary

### MES Hook Chain (Stock Entry Submit)
```
Stock Entry on_submit
  → mes_coordinator.on_stock_entry_submit()
    → validate_stock_entry_permission()
    → Find affected WOs (by work_order or target warehouse)
    → JobCardReadinessEngine.refresh_work_order()
      → For each JC: evaluate_job_card() → apply_result_to_job_card()
        → doc.save() triggers validate hook
          → update_job_card_status()
            → update_start_status() — sets custom_start_status
            → update_dependency_status() — sets custom_can_start_operation
            → update_material_status() — sets custom_material_available_for_operation
```

### JC Start Validation
```
Job Card before_save
  → validate_job_card_start()
    → Check previous operation (DependencyEngine)
    → Check material availability (MaterialReadinessEngine)
    → Block start if either fails
```

---

## Testing Checklist

### UAT Testing
- [ ] Material Request generation from Production Plan
- [ ] Stock Entry creation from Material Request
- [ ] custom_start_status updates to "Ready to Start" after SE submit
- [ ] JC start blocked when materials not available
- [ ] JC start allowed when materials available
- [ ] JC completion updates status to "Completed"
- [ ] Multiple WOs in same WIP warehouse refresh correctly

---

## Known Issues (Resolved)
1. ~~MR Generation "Error: undefined"~~ — Fixed frappe v15 error handlers
2. ~~MR Generation "no MRs generated"~~ — Fixed source_warehouse fallback
3. ~~custom_start_status not updating after SE~~ — Fixed SE hook purpose handling
4. ~~"Refresh Dependency Status" button not working~~ — Not implemented (validate hook handles this on save)

---

## Deployment Notes

```bash
git pull origin main
bench build --app tekson_manufacturing
bench migrate  # Runs patches including custom_start_status options update
bench restart
```

---

## Git History (Recent)
- `aab8f12` — Handle Material Transfer purpose in SE hook
- `395883f` — Add diagnostic logging to update_start_status and validate hook
- `02d4afe` — Fix apply_result_to_job_card to use doc.save()
- `6429540` — Remove validate_manufacturing_role from SE hook
- `c6e2372` — Patch: update custom_start_status options from 7 to 5 values
- `d601343` — Align custom_start_status to 5 values
