# Tekson MES — Project Status & Session Handoff

**Date:** 2026-10-29
**Session:** Workstation Type Rotation — BOM Operation type → LRU machine allocation → v15.1.40 released
**Status:** ✅ **v15.1.40 TAGGED + ON `develop` / `main` — Test Server validated; UAT deployment pending**

---

## Current Version: v15.1.40 (main + develop)

| Branch | Version | Status |
|--------|---------|--------|
| main | v15.1.40 | ✅ Released (tag `v15.1.40`) |
| develop | v15.1.40 | ✅ Released + docs |
| bom-bulk-creator | v15.1.39 | ✅ Released (side branch) |

---

## ✅ COMPLETED — This Session

### Workstation Type Rotation (v15.1.40)
- **Problem:** every Job Card for a Workstation Type went to the first machine alphabetically (`get_workstations(type)[0]`); siblings stayed idle and one machine became the bottleneck.
- **Fix:** the BOM Operation's **Workstation Type** is the routing key. New shared `pick_workstation(workstation_type, reasons, candidates=...)` in `utils/job_card_utils.py` rotates across the eligible machines: not at capacity (`active_load < production_capacity`) → fewest queued cards (`open_load`) → least recently used → name. `candidates` is the seam for the future capacity planner.
- **`last_used` is real use:** `actual_end_date`, or `NOW()` while a Job Card is running. Queued cards never worked do not count, cancelled cards are ignored, never-used machines sort first. `open_load` is ordered before `last_used` so a batch of new cards spreads across the type instead of stacking on one machine; it is not a hard availability filter.
- **Eligibility:** `Maintenance` / `Problem` / `Setup` are excluded; `Off` / `Idle` / `Production` remain eligible. Status follows the Job Card: **starting a card sets its machine to `Production`**, **completing it sets the machine back to `Off`**. `Setup` = new machine setup/commissioning, `Problem` = reported fault, `Maintenance` = under maintenance. A queued card is not started immediately, so `Production` on a busy machine does not prevent planning the next card there.
- **No scheduling override:** pre-assigned / planner-chosen workstations are kept and `scheduled_time_logs` are never touched. With capacity planning enabled, ERPNext's scheduling pick wins — so **keep `Manufacturing Settings → Disable Capacity Planning` ticked**.
- **Legacy machine-in-BOM rows** are a preference: honoured when eligible, otherwise fall back to that machine's type and log the blocked machine.
- **All machines at capacity:** the least loaded card count is still assigned (Work Order submission never blocked) with a warning; the diagnostic reports the overflow.
- **Diagnostics:** section 7 "Workstation routing" — capacity-planning setting, recent Job Cards that still carry scheduled time logs, BOM Operations without a Workstation Type, types with no usable machine, types spanning multiple plant floors, machines excluded by `Maintenance` / `Problem` / `Setup`, and workstations above `production_capacity`.
- **Test Server result:** 134 Job Cards from a bulk concurrent submission of 91 Work Orders rotated evenly — Accurate Cutting 2 per machine across 4, Corner Cutting 5/5/5, Helicoil 5/4 across 2 with the third in `Maintenance`, Fin Forming 2/2/1/1 across 4 with the fifth in `Setup`. Both excluded machines received nothing. Single-machine types stayed on their machine. No rotation warning, no capacity overflow, consistency spot-check clean, no new MES errors under concurrent allocation.
- **Files:** `utils/job_card_utils.py`, `services/job_card_service.py`, `scripts/diagnose_mes_performance.py`
- **Review document:** `V15.1.40_REVIEW_SUMMARY.md` (problem, rules, validation, limitations, deployment, commits)
- **Release state:** tag `v15.1.40` → `0ccf71b`; `develop` and `main` both at the docs commit after it

### Tests
- Offline stub suites for `pick_workstation()` / `allocate_workstation()`: rotation, queued-vs-active, `production_capacity > 1`, candidates filter, blocked statuses, all-at-capacity, cancelled exclusion, type-first vs legacy routing, pre-assigned preservation, blocked-machine fallback
- `py_compile` + `ruff` clean on changed files; no doctype/field/permission changes → `git pull` + `bench restart` only

---

## ✅ COMPLETED — Previous Session (v15.1.36–v15.1.39)

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
Branches: develop / main at v15.1.40 (in sync with origin); bom-bulk-creator at v15.1.39
Status: ✅ Synced — only SESSION_LOG_Oct23_2026.md untracked (intentionally)
```

### Test Server (teksons.dev)
```
Status: ✅ Validated on v15.1.40 — 134 Job Cards from a bulk concurrent submit of 91 Work Orders
Required setting: Manufacturing Settings → Disable Capacity Planning = ticked
Pull: git pull upstream develop + bench restart (no migrate/build for v15.1.40)
```

### UAT VM (tekson.site)
```
Last observed: v15.1.37/38 (skip warnings + _comments error, 2026-10-26/27)
Status: ⏳ v15.1.40 released; UAT pull pending
Note: jump from v15.1.37/38 carries v15.1.39 + v15.1.35 permission JSON →
      bench migrate + bench build --force + bench restart are required
Rollback: git checkout v15.1.39 && bench restart (no schema change to reverse)
```

### Dev Machine (karthic@teksons-development)
```
Remote: upstream (not origin)
Branch: develop
Site: teksons.dev
Status: ✅ Running v15.1.40 (validated)
```

### UAT Machine (cwd_admin@cwd)
```
Remote: origin
Branch: main
Site: tekson.site
Status: ⏳ v15.1.40 released on main; deploy pending (currently v15.1.37/38)
```

---

## Deployment Commands

### Dev Machine
```bash
cd ~/frappe-bench/apps/tekson_manufacturing
git pull upstream develop
cd ~/frappe-bench && sudo systemctl restart frappe-bench.target
bench --site teksons.dev execute tekson_manufacturing.scripts.diagnose_mes_performance.run \
  --args '[{"assignment_hours": 1}]'
```

### UAT Machine
```bash
cd ~/cwd-bench/apps/tekson_manufacturing
git fetch origin && git checkout main && git pull origin main
cd ~/cwd-bench && bench --site tekson.site migrate && bench build --force && bench restart
bench --site tekson.site execute tekson_manufacturing.scripts.diagnose_mes_performance.run \
  --args '[{"assignment_hours": 24}]'
```

---

## Key Files Modified This Session

| File | Changes |
|------|---------|
| `tekson_manufacturing/utils/job_card_utils.py` | Workload metrics, eligibility helper, shared `pick_workstation()`, type-first allocation (v15.1.40) |
| `tekson_manufacturing/scripts/diagnose_mes_performance.py` | Section 7 workstation routing + capacity overflow; `tabJob Card` index candidate |
| `tekson_manufacturing/utils/operation_warehouse.py` | New operation → target WIP resolver (v15.1.37) |
| `tekson_manufacturing/planning/material_planning_service.py` | Daily aggregation qty fix; operation-driven target; warnings; `source_bom` on leaves |
| `tekson_manufacturing/reports/material_transfer_pick_list/material_transfer_pick_list.py` | Operation-driven target + Operation column |
| `tekson_manufacturing/tests/test_material_planning_qty.py` | 30-test suite (22 new across v15.1.37–39) |
| `tekson_manufacturing/__init__.py`, `pyproject.toml` | Version 15.1.40 |
| `V15.1.40_REVIEW_SUMMARY.md` | Full review document for v15.1.40 |
| `docs/CHANGELOG.md`, `docs/V15.1.40_RELEASE_NOTES.md`, `docs/END_USER_MANUAL.md`, `PROJECT_STATUS.md`, `README.md` | Documentation refresh |

---

## Next Session Goals

1. **UAT deploy** (`tekson.site`): pull `main`, `bench migrate`, `bench build --force`, `bench restart` — the jump from v15.1.37/38 carries v15.1.39 + the v15.1.35 permission JSON
2. Confirm `Manufacturing Settings → Disable Capacity Planning` is ticked on UAT
3. Run the diagnostic (`--args '[{"assignment_hours": 24}]'`); section 7 must show the planning setting, no recent scheduled time logs, valid Workstation Types, excluded machines listed, no capacity overflow
4. Submit one Work Order on UAT and confirm its Job Cards rotate across the eligible machines of each operation's Workstation Type; do not delete open cards — cancel instead
5. Update `PROJECT_STATUS.md` / this file to mark UAT deployed; then Live with the same commands
6. Re-run the standalone unit suite: `python3 tekson_manufacturing/tests/test_material_planning_qty.py` (30 tests)
7. Work down `PENDING_FIXES.md` (P1 N+1 Bin lookups in the Pick List, dashboards)
