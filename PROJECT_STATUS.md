# Tekson Manufacturing - Project Status

## Current Version: v15.1.26 (main) | v15.1.26 (develop)

---

## Completed Features

### 1. MES Execution Engine (Phase 1 — v15.0.x)
**Status: ✅ Complete**

- Material Readiness Engine — checks stock before JC start
- Dependency Engine — enforces operation sequence
- Job Card Readiness Engine — auto-updates JC status
- MES Coordinator — single entry point for all hooks
- Stock Entry hook — auto-updates JC on material transfer

**Key Files:**
- `mes/mes_coordinator.py` — Hook coordinator
- `readiness/material_readiness.py` — Material check
- `readiness/job_card_readiness.py` — JC readiness
- `validation/dependency_engine.py` — Operation dependencies

### 2. Daily Material Planning (Phase 1.1 — v15.1.x)
**Status: ✅ Complete (v15.1.26)**

- Generates Material Requests grouped by department WIP warehouse
- Source warehouse fallback chain: `item.source_warehouse → wo.source_warehouse → default warehouse`
- Circular BOM guard (`_seen` set) to prevent infinite recursion
- Company field added to Material Request (required in ERPNext v15)
- Frontend error handlers fixed for frappe v15 (`xhr.responseText` parsing)

**v15.1.25 — MR Qty Double-Counting Fix:**
- `_explode_bom` now receives `wo_bom_nos` set (BOMs with their own WOs)
- Skips recursion into sub-assemblies that have their own Work Orders
- Each leaf WO only requests its direct raw materials
- Prevents same raw material from being counted at every level of hierarchy

**v15.1.26 — Source Warehouse Filter Fix:**
- `_is_source_warehouse` now uses contains match (`"Raw Material Stores" in wh_name`)
- Handles warehouse names with suffixes (e.g., "Raw Material Stores - TPL")
- `_get_default_source_warehouse` also uses contains match with fallback
- MR now correctly checks WIP stock and only requests actual shortages

**Key Files:**
- `planning/material_planning_service.py` — MR generation logic
- `public/js/production_plan_mr.js` — Production Plan MR button
- `page/material_planning/material_planning.js` — Material Planning page

### 3. BOM Bulk Creator (v15.1.20–v15.1.24)
**Status: ✅ Complete**

- Creates multi-level BOM hierarchies as Draft only
- Routing field on parent and child doctypes
- Routing reads from child rows where `fg_item == item_code`
- Operation field with routing-based filtering via `routing_utils.py`
- `do_not_explode` set to 0 for expandable items, 1 for RMs
- `parent_row_no` editable (user enters manually)
- Item deduplication — first occurrence only
- BOM quantity fixed to 1

**Key Files:**
- `tekson_manufacturing/doctype/bom_bulk_creator/bom_bulk_creator.py`
- `tekson_manufacturing/doctype/bom_bulk_creator/bom_bulk_creator.js`
- `tekson_manufacturing/utils/routing_utils.py`

### 4. BOM Routing Corrections (R215 Combi Cooler)
**Status: ✅ Applied**

Corrected department routing for 7 end plate BOMs:
- **Shearing** → W Dept (WIP-W)
- **Sr. No. Punching** → RA Dept (WIP-RA)
- **Folding** → RP Dept (WIP-RP)
- **Core Assembly** → Ralu In Dept (WIP-Ralu In)

### 5. custom_start_status Field Standardization
**Status: ✅ Applied**

Reduced from 7 values to 5:
1. `Awaiting Material` — raw materials not in WIP warehouse
2. `Awaiting Previous Operation` — previous JC not completed
3. `Ready to Start` — both material available AND previous op complete
4. `In Progress` — JC status is "Work In Progress"
5. `Completed` — JC status is "Completed"

### 6. Stock Entry Hook - custom_start_status Auto-Update
**Status: ✅ Working**

After Material Transfer to department WIP, Job Cards now auto-update:
- `custom_start_status` → "Ready to Start" (if first JC with materials available)
- `custom_can_start_operation` → 1
- `custom_material_available_for_operation` → 1

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v15.0.1–v15.0.3 | Aug 2026 | Core MES engine, hooks, tests |
| v15.1.1–v15.1.9 | Aug 2026 | Planning module, MR generation, status standardization |
| v15.1.20–v15.1.24 | Sep 2026 | BOM Bulk Creator, routing, operation field |
| v15.1.25 | Sep 12, 2026 | MR qty double-counting fix (wo_bom_nos filter) |
| v15.1.26 | Sep 12, 2026 | Source warehouse contains match fix |

---

## Deployment

### Dev Machine (karthic@teksons-development)
```bash
cd ~/frappe-bench/apps/tekson_manufacturing
git fetch upstream && git merge upstream/bom-bulk-creator --no-edit
cd ~/frappe-bench && bench --site teksons.dev migrate
```

### UAT Machine (cwd_admin@cwd)
```bash
cd ~/cwd-bench/apps/tekson_manufacturing
git pull origin main
cd ~/cwd-bench && bench --site tekson.site migrate && bench build --app tekson_manufacturing
```

### Local Development
```bash
cd /home/karthic/Desktop/new_applications/tekson_manufacturing
git pull origin main
```

---

## Testing Checklist

### Material Planning
- [x] MR generation from Production Plan (PP)
- [x] MR grouped by department WIP warehouse
- [x] Source warehouse contains match (- TPL suffix)
- [x] MR only requests actual shortages (WIP stock deducted)
- [x] No double-counting of sub-assembly materials
- [x] Leaf WOs request only direct raw materials

### BOM Bulk Creator
- [x] Create multi-level BOM hierarchy as Draft
- [x] Routing field on parent/child doctypes
- [x] Operation field filtered by routing
- [x] `do_not_explode` logic (0 for expandable, 1 for RMs)
- [x] Item deduplication
- [x] Grid list view columns forced on refresh

### MES Execution
- [x] Job Card readiness status updates
- [x] Stock Entry hook triggers JC refresh
- [x] Dependency blocking (previous op must complete)
- [x] Material availability check before JC start
