# Tekson MES — Project Status & Session Handoff

**Date:** 2026-10-27
**Session:** Daily Material Planning — MR Qty + Operation-Driven Target WIP → v15.1.36–v15.1.39
**Status:** ✅ **v15.1.39 RELEASED — AWAITING UAT PULL + RETRY**

---

## Current Version: v15.1.39

| Branch | Version | Status |
|--------|---------|--------|
| main | v15.1.39 | ✅ Released |
| develop | v15.1.39 | ✅ Released |
| bom-bulk-creator | v15.1.39 | ✅ Released |

---

## ✅ COMPLETED — This Session

### Daily Material Planning — Required Qty Fix (v15.1.36)
- **Problem:** MR `qty` ignored stock already in the target WIP (regression from `e998206`); requirements vanished when stock covered one WO but not the day's total; the same stock was deducted per source warehouse; Bin lookup used `warehouse LIKE '%WIP%'`
- **Fix:** Aggregate requirements per `(target WIP, item)` across ALL of the day's WOs first, then `qty = ceil(required incl. RM Loss − stock in target WIP)` once; loss-ratio split keeps `custom_bom_qty + custom_rm_loss_qty = balance`; Bin lookup uses exact warehouse names; skips surfaced as warnings on the Material Planning page
- **File:** `planning/material_planning_service.py`

### Operation-Driven Transfer Target WIP (v15.1.37)
- **Problem:** MRs (and the Pick List report) fell back to `Work Order.wip_warehouse` — derived from the BOM's **first** operation — whenever the Job Card lookup missed (operation key whitespace, duplicate/split JCs, no JC yet). On multi-floor BOMs material landed on the wrong plant-floor WIP. Pick List never read `BOM Item.operation` at all
- **Fix:** New shared resolver `utils/operation_warehouse.py`: `BOM Item.operation` → `BOM Operation` (whitespace tolerant) → `workstation_type` → first `Workstation` → `plant_floor` → `WIP-{floor} - TPL` (must exist); Job Card `wip_warehouse` as fallback; **never** the WO header for operation-bearing items; unresolvable → item skipped with a visible warning; config-vs-stale-JC mismatch warned; Pick List gets the same rule + an **Operation** column
- **Files:** `utils/operation_warehouse.py` (new), `planning/material_planning_service.py`, `reports/material_transfer_pick_list/material_transfer_pick_list.py`

### Case-Insensitive Operation Matching (v15.1.38)
- **Problem:** UAT reported `Item … on Work Order …: warehouse for operation Tank Assembly could not be resolved — material skipped` while the same BOM resolved on the Test VM. The resolver only trimmed whitespace, so casing differences between the BOM Item's operation, the `BOM Operation` routing row and the Job Card (duplicate Operation masters) caused a miss — including the Job Card fallback
- **Fix:** `normalize_operation()` (collapse whitespace + casefold) used for `BOM Operation` matching and for the Job Card `wip_warehouse` map in both Material Planning and the Pick List. Resolution chain and warnings unchanged
- **Files:** `utils/operation_warehouse.py`, `planning/material_planning_service.py`, `reports/material_transfer_pick_list/material_transfer_pick_list.py`

### Actionable Skip Warnings + Extra Fallbacks (v15.1.39)
- **Problem:** UAT still skipped items after v15.1.38 (`warehouse for operation Tank Assembly could not be resolved`), and the message gave no clue which of the five links was missing — routing row without a workstation, unknown workstation type, workstation without `plant_floor`, missing `WIP-{floor} - TPL`, or no Job Card yet
- **Fix:** the resolver collects a reason per failed link and the warning now names them; the Job Card's `workstation` → `plant_floor` is used when its `wip_warehouse` is blank; a *unique* `WIP-{floor}` naming variant is accepted (ambiguous matches are never guessed); the Pick List calls the shared `resolve_target_warehouse()` and logs the same reasons
- **Files:** `utils/operation_warehouse.py`, `planning/material_planning_service.py`, `reports/material_transfer_pick_list/material_transfer_pick_list.py`

### Tests
- `tekson_manufacturing/tests/test_material_planning_qty.py` — 30 tests, runs standalone (no bench site): 8 quantity + 12 target-resolution + 10 resolver contract. 7 of the 8 v15.1.37 target tests and all 3 v15.1.38 tests fail against the pre-fix code
- Lint: new/touched files clean; `material_planning_service.py` rule profile unchanged vs baseline

### Operational Notes
- **Stock workspace `ImportError` (`_get_item_details` from `erpnext`)** — stale Python worker processes after an ERPNext-side update; **not** a tekson issue. Resolved by server reboot. If it recurs: `bench build --force && bench restart`, full reboot if workers persist
- **`Field not permitted in query: tabJob Card._comments`** — upstream Frappe commit `2b29354` (2026-09-10) removed `_comments` from the standard/optional list fields; older desk JS still requested it. **Not** a tekson issue. Fix: `bench build --force && bench clear-cache && bench restart`, then hard-refresh the browser. Full detail + diagnostics in `PENDING_FIXES.md` → Environment / UAT Troubleshooting
- Version bump lesson (from earlier): after `git pull`, verify with `bench version`; use `bench build --force` before restart when the version changed

---

## Deployment Status

### Local Development (this workspace)
```
Remote: origin
Branches: main, develop, bom-bulk-creator — all at v15.1.37 (971c005), pushed
Status: ✅ Synced
```

### Test / UAT VM
```
Last observed: v15.1.37/38 (skip warnings + _comments error, 2026-10-26/27)
Status: ⏳ Pull pending — git pull + bench build --force + bench restart for v15.1.39
Note: no bench migrate needed (no doctype changes)
```

### Dev Machine (karthic@teksons-development)
```
Remote: upstream (not origin)
Branch: bom-bulk-creator
Site: teksons.dev
Status: Check current version; pull + restart if behind v15.1.39
```

### UAT Machine (cwd_admin@cwd)
```
Remote: origin
Branch: main
Site: tekson.site
Status: Check current version; pull + restart if behind v15.1.39
```

---

## Deployment Commands

### Dev Machine
```bash
cd ~/frappe-bench/apps/tekson_manufacturing
git fetch upstream && git reset --hard upstream/bom-bulk-creator
cd ~/frappe-bench && bench --site teksons.dev migrate && bench build --force && bench restart
```

### UAT Machine
```bash
cd ~/cwd-bench/apps/tekson_manufacturing
git pull origin main
cd ~/cwd-bench && bench --site tekson.site migrate && bench build --force && bench restart
```

---

## Key Files Modified This Session

| File | Changes |
|------|---------|
| `tekson_manufacturing/utils/operation_warehouse.py` | New operation → target WIP resolver |
| `tekson_manufacturing/planning/material_planning_service.py` | Daily aggregation qty fix; operation-driven target; warnings; `source_bom` on leaves |
| `tekson_manufacturing/reports/material_transfer_pick_list/material_transfer_pick_list.py` | Operation-driven target + Operation column |
| `tekson_manufacturing/tests/test_material_planning_qty.py` | 30-test suite (22 new across v15.1.37–39) |
| `tekson_manufacturing/__init__.py`, `pyproject.toml` | Version 15.1.39 |
| `docs/CHANGELOG.md`, `docs/END_USER_MANUAL.md`, `docs/MATERIAL_TRANSFER_PICK_LIST_REPORT.md`, `PROJECT_STATUS.md`, `README.md`, `PENDING_FIXES.md` | Documentation refresh |

---

## Next Session Goals

1. On UAT: `git pull` + `bench build --force` + `bench clear-cache` + `bench restart`; hard-refresh the browser to clear the `_comments` list-view error
2. Re-run the Material Planning trial for `WO/261027/0321`; the skip warning now names the broken link — fix that configuration (routing workstation, `plant_floor`, or the `WIP-{floor} - TPL` warehouse) and re-run
3. Re-run the standalone unit suite: `python3 tekson_manufacturing/tests/test_material_planning_qty.py` (30 tests)
4. Work down `PENDING_FIXES.md` (P1 N+1 Bin lookups in the Pick List, dashboards)
5. Customer UAT → production go-live preparation
