# Tekson Manufacturing - Project Status

## Current Version: v15.1.40 (main + develop)

---

## Current Status (October 29, 2026)

- **v15.1.40 tagged `v15.1.40` and merged to `main`** (Test Server validated; UAT pull pending) — Job Card allocation now routes by **BOM Operation Workstation Type** and rotates across the eligible machines of that type instead of always picking the first. New shared `pick_workstation()` service with a `candidates` seam for future capacity planning; workload split into `active_load` (compared with `production_capacity`), `open_load` (queue, balanced before LRU) and `last_used` (real production activity, not Job Card creation). `Maintenance` / `Problem` / `Setup` machines are excluded. No doctype/field/permission changes: `git pull` + `bench restart` (no migrate/build). **Capacity planning must stay disabled** (`Manufacturing Settings → Disable Capacity Planning`) — ERPNext's scheduling pick runs before the Job Card hook and is respected. Verify with diagnostic section 7. Full review: `V15.1.40_REVIEW_SUMMARY.md`.
- **v15.1.39 released** — UAT skip warnings now name the broken configuration link (`routing row … has no workstation / workstation type`, `no Workstation of type …`, `Workstation … has no plant floor`, `warehouse WIP-RP - TPL does not exist for plant floor RP`, `no Job Card WIP warehouse …`). Also adds a Job Card `workstation` → `plant_floor` fallback and accepts a unique `WIP-{floor}` naming variant instead of dropping the material. The planning fixes (v15.1.36–39) need no `bench migrate`, but this release also carries v15.1.35 role/permission JSON (Pick List report, BOM Bulk Creator, workspace) — sites upgrading from `v15.1.33` **must** run `bench migrate`: `git pull` + `bench --site <site> migrate` + `bench build --force` + `bench restart`
- **v15.1.38** — case/whitespace-insensitive operation matching across BOM Item, BOM Operation row and Job Card (`normalize_operation`)
- **v15.1.36 (MR qty fix) + v15.1.37 (operation-driven target WIP) released** — pushed to `develop`, `main`, and `bom-bulk-creator` as commit `971c005`
- **UAT deployment pending for v15.1.40** — last observed running **v15.1.37/38** (Oct 27: operation skip warnings + `_comments` list error). Pull `main` + `bench --site tekson.site migrate` + `bench build --force` + restart. v15.1.40 itself has no schema/asset changes, but the jump from v15.1.37/38 carries v15.1.39 and the v15.1.35 permission JSON, so migrate + build are required; `--force` also clears the `_comments` stale-asset error
- **User trial confirmed** the target-warehouse bug: a Job Card lookup miss (whitespace in the operation key) sent WO-2's materials to the first-operation WIP — fixed in v15.1.37
- **UAT `Field not permitted in query: tabJob Card._comments`** — upstream Frappe security change (Sep 10, 2026 removed `_comments` from standard list fields) colliding with **stale frontend assets**; not a tekson_manufacturing issue. Fix: rebuild assets (`bench build --force`) + `bench clear-cache` + `bench restart`, then hard-refresh the browser
- **Stock workspace `ImportError` (`_get_item_details` from `erpnext`)** — stale Python worker processes after an ERPNext-side update, *not* a tekson_manufacturing issue; resolved by server reboot
- **Unit suite (no bench site needed):** `python3 tekson_manufacturing/tests/test_material_planning_qty.py` — 30 tests: 8 quantity + 12 target-resolution + 10 resolver contract

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
**Status: ✅ Complete (v15.1.39)**

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

**v15.1.36 — Required Qty Bug Fix:**
- Requirements aggregated per (target WIP, item) across ALL of the day's WOs
- MR `qty` = ceil(required incl. RM Loss − stock already in target WIP)
- Bin lookup uses the exact target warehouse (was `LIKE '%WIP%'`)
- Skips surfaced as `warnings` on the Material Planning page

**v15.1.37 — Operation-Driven Target WIP:**
- Target warehouse resolved from the BOM Item's operation: `BOM Operation → workstation → plant floor → WIP-{floor} - TPL` (never the WO header / first-operation warehouse)
- Job Card `wip_warehouse` as fallback; configuration wins over a stale JC (mismatch warned)
- Unresolvable operation warehouse → item skipped with a visible warning
- jc_map keys whitespace-trimmed; `source_bom` propagated by `_explode_bom` for child-BOM routing
- Pick List report uses the same rule + new Operation column
- Resolver: `utils/operation_warehouse.py` (shared by planning + pick list)

**v15.1.38 — Case-Insensitive Operation Matching:**
- Operation names compared case- and whitespace-insensitively across BOM Item, BOM Operation and Job Card (`normalize_operation`)
- Fixes UAT skips where `Tank Assembly` vs `TANK ASSEMBLY` produced "warehouse for operation … could not be resolved"
- Job Card WIP fallback map uses the same normalised key in Material Planning and the Pick List

**v15.1.39 — Actionable Skip Warnings + Extra Fallbacks:**
- Skip warnings now state *which* link of the chain failed (routing row without a workstation, unknown workstation type, workstation without `plant_floor`, missing `WIP-{floor} - TPL` warehouse, no Job Card WIP)
- Job Card `workstation` → `plant_floor` → WIP used as a fallback when the Job Card's `wip_warehouse` is blank (same rule as `set_wip_warehouse` on Job Card save)
- A *unique* `WIP-{floor}` naming variant (e.g. `WIP - RP - TPL`) is accepted when the convention name is missing; ambiguous matches are never guessed
- Pick List report logs the same reasons and now calls the shared `resolve_target_warehouse()`

**Key Files:**
- `planning/material_planning_service.py` — MR generation logic
- `utils/operation_warehouse.py` — operation → target WIP resolver
- `public/js/production_plan_mr.js` — Production Plan MR button
- `page/material_planning/material_planning.js` — Material Planning page

### 3. BOM Bulk Creator (v15.1.20–v15.1.27)
**Status: ✅ Complete**

- Creates multi-level BOM hierarchies as Draft only
- Routing field on parent and child doctypes
- Routing reads from child rows where `fg_item == item_code`
- Operation field with routing-based filtering via `routing_utils.py`
- `do_not_explode` set to 0 for expandable items, 1 for RMs
- `parent_row_no` editable (user enters manually)
- Item deduplication — first occurrence only
- BOM quantity fixed to 1

**v15.1.27 — Child BOM Link Fix:**
- `bom_no` intentionally left blank during bulk creation
- ERPNext requires referenced BOMs to be submitted — Draft BOMs cannot link to each other
- Users manually select/link child BOMs after review
- `bom_queue` still tracks generated BOM names internally for sequencing

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

### 7. Job Card Workstation Allocation (v15.1.40)
**Status: ✅ Complete — tagged `v15.1.40`, on `develop` + `main`; UAT deployment pending**

- Allocation key is the BOM Operation **Workstation Type**, resolved to a group of interchangeable machines; the Job Card's copied `workstation_type` is the fallback
- `pick_workstation()` is the single selection service; its `candidates` argument is the seam for the future capacity planner
- Selection order: not at concurrent capacity → fewest queued Job Cards → least recently used → name
- `active_load` (`Work In Progress` / `On Hold`) is compared with `production_capacity`; `open_load` (anything not `Completed` / `Cancelled`) is the queue and is never a hard availability filter
- `last_used` comes from `actual_end_date` (or `NOW()` for a running card), not Job Card creation; queued-never-started and cancelled cards are ignored; never-used machines sort first
- Only `Maintenance` / `Problem` / `Setup` are excluded; `Off` / `Idle` / `Production` stay eligible (`Off` is set automatically on completion; a queued card is not started immediately)
- Pre-assigned and capacity-planner workstations are never replaced; `scheduled_time_logs` are never overridden
- Legacy machine-in-BOM rows are a preference: fall back to the machine's type with a logged warning
- All machines at capacity still assigns the least loaded one (Work Order submission is never blocked) and warns; the diagnostic reports the overflow
- Job Card save now evaluates material readiness for its **own operation**, matching the readiness refresh (previously the save replaced it with the whole Work Order's list)
- Diagnostic section 7 reports capacity-planning status, recent scheduled time logs, missing Workstation Types, unusable and rotation-ready types, multi-floor types, machines excluded by `Maintenance` / `Problem` / `Setup`, recent assignment spread and capacity overflow

**Key Files:**
- `utils/job_card_utils.py` — workload metrics, eligibility helper, shared `pick_workstation()`, type-first allocation
- `services/job_card_service.py` — operation-scoped readiness on Job Card save
- `scripts/diagnose_mes_performance.py` — section 7 routing / assignment diagnostics
- `tests/test_status_mapping.py` — operation-scope regression test
- `V15.1.40_REVIEW_SUMMARY.md` — full review (problem, rules, validation, limitations)

**Validation (Test Server):** 134 Job Cards from a bulk concurrent submission of 91 Work Orders rotated evenly — Accurate Cutting 2/2/2/2 across 4, Corner Cutting 5/5/5, Helicoil & Tapping 5/4 across 2 with the third machine in `Maintenance`, Fin Forming 2/2/1/1 across 4 with the fifth in `Setup`. Both excluded machines received nothing. Consistency spot-check clean, no rotation warning, no capacity overflow, queue `failed=0`, no new MES errors.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v15.0.1–v15.0.3 | Aug 2026 | Core MES engine, hooks, tests |
| v15.1.1–v15.1.9 | Aug 2026 | Planning module, MR generation, status standardization |
| v15.1.20–v15.1.24 | Sep 2026 | BOM Bulk Creator, routing, operation field |
| v15.1.25 | Sep 12, 2026 | MR qty double-counting fix (wo_bom_nos filter) |
| v15.1.26 | Sep 12, 2026 | Source warehouse contains match fix |
| v15.1.27 | Sep 16, 2026 | BOM Bulk Creator bom_no fix (child BOM links blank) |
| v15.1.32 | Oct 21, 2026 | Job Card readiness performance overhaul; WO cancel revert |
| v15.1.33 | Oct 21, 2026 | Dependency lookup includes draft JCs; start-blocked message fix |
| v15.1.34 | Oct 21, 2026 | Floor roles allowed for MES execution (JC complete / WO submit) |
| v15.1.35 | Oct 23, 2026 | Role-model alignment (execution vs release gates) |
| v15.1.36 | Oct 26, 2026 | Daily Material Planning required-qty fix (aggregate, deduct WIP stock once) |
| v15.1.37 | Oct 26, 2026 | Operation-driven transfer target warehouse (never first-operation WIP) |
| v15.1.38 | Oct 27, 2026 | Case/whitespace-insensitive operation matching (UAT "could not be resolved" skips) |
| v15.1.39 | Oct 27, 2026 | Skip warnings name the broken link; Job Card workstation fallback; tolerant WIP naming |
| v15.1.40 | Oct 29, 2026 | Workstation Type rotation (LRU, capacity-aware, no scheduling override); routing diagnostics |

---

## Pending Features (Not Yet Implemented)

### 1. MES Dashboard
**Status: ❌ Not Started**

Planned URL: `/mes/dashboard`

Planned features:
- Production status counts (WOs + JCs by status)
- KPIs (on-time %, efficiency, quality, material availability)
- Active alerts (negative stock, stale JCs, material shortages)
- Recent activity (completed JCs, recent SEs)
- Department-wise production summary

**Backend APIs exist** (`www/mes/dashboard.py`) but no frontend dashboard page has been built.

### 2. Material Transfer Pick List Report
**Status: ✅ Released (report work completed v15.1.31; operation-driven target + Operation column since v15.1.37)**

- Open-WO transfer rows: required, available at source, balance-to-transfer
- Filters: From Date / To Date on `planned_start_date`
- Target WIP resolved from the BOM Item's operation (same rule as Material Planning)
- Documented in `docs/MATERIAL_TRANSFER_PICK_LIST_REPORT.md` and END_USER_MANUAL §5.2
- Remaining polish tracked in `PENDING_FIXES.md` (P1 N+1 Bin lookups, P3 zero-balance rows, P5 hard-coded date defaults)

### 3. Planner Intelligence / Analytics
**Status: ❌ Not Started**

Planned features:
- Planner KPIs (on-time %, readiness %, WO counts)
- Production Calendar (upcoming WOs by date)
- Exceptions (overdue WOs, blocked JCs, material shortages)
- Department Workload (WO count + qty per WIP warehouse)
- Stores KPIs (MR count, items short per department)

**Backend APIs exist** (`api/intelligence.py`) but no frontend dashboard or page has been built.

### 4. Job Card Start/Complete API
**Status: ❌ Not Started**

Planned features:
- `start_job_card(name)` — validated start with material + dependency checks
- `complete_job_card(name)` — validated complete with next-JC refresh + auto WO completion

**API definitions exist** (`api/job_card_start.py`) but not yet wired to UI or tested end-to-end.

---

## Deployment

### Dev / Test Server (karthic@teksons-development)
```bash
cd ~/frappe-bench/apps/tekson_manufacturing
git pull upstream develop
cd ~/frappe-bench && sudo systemctl restart frappe-bench.target
# configure once, then verify:
# Manufacturing Settings -> Disable Capacity Planning = ticked
bench --site teksons.dev execute tekson_manufacturing.scripts.diagnose_mes_performance.run \
  --args '[{"assignment_hours": 1}]'
```

### UAT Machine (cwd_admin@cwd)
```bash
cd ~/cwd-bench/apps/tekson_manufacturing
git fetch origin && git checkout main && git pull origin main
cd ~/cwd-bench && bench --site tekson.site migrate && bench build --force && bench restart
bench --site tekson.site execute tekson_manufacturing.scripts.diagnose_mes_performance.run \
  --args '[{"assignment_hours": 24}]'
```

v15.1.40 itself is Python-only, but UAT is still on v15.1.37/38, so this jump
carries v15.1.39 and the v15.1.35 permission JSON — `bench migrate` and
`bench build --force` are required. Keep capacity planning disabled.

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
- [x] MR qty = required (incl. RM Loss) − stock in target WIP, aggregated across the day's WOs (v15.1.36)
- [x] Target WIP resolved from BOM Item operation — never the first-operation WO header (v15.1.37)
- [x] Unresolvable operation warehouse → item skipped with a visible warning (v15.1.37)
- [x] Config vs stale Job Card WIP mismatch → warning shown (v15.1.37)
- [x] Operation matching ignores case/whitespace (v15.1.38)
- [x] Unresolvable target → warning names the broken configuration link (v15.1.39)
- [x] Job Card `workstation` → plant floor used when its WIP is blank (v15.1.39)

### Material Transfer Pick List
- [x] Open-WO filter (Completed / Closed / Stopped / Cancelled excluded)
- [x] Operation column + operation-driven target WIP (v15.1.37)

### BOM Bulk Creator
- [x] Create multi-level BOM hierarchy as Draft
- [x] Routing field on parent/child doctypes
- [x] Operation field filtered by routing
- [x] `do_not_explode` logic (0 for expandable, 1 for RMs)
- [x] Item deduplication
- [x] Grid list view columns forced on refresh
- [x] Child BOM Item.bom_no left blank during bulk creation

### MES Execution
- [x] Job Card readiness status updates
- [x] Stock Entry hook triggers JC refresh
- [x] Dependency blocking (previous op must complete)
- [x] Material availability check before JC start

### Job Card Workstation Allocation (v15.1.40)
- [x] Job Cards route by the BOM Operation's Workstation Type, never a hard-coded machine
- [x] A batch spreads across eligible machines (capacity → queue depth → least recently used → name)
- [x] `active_load` respects `production_capacity`
- [x] `Maintenance` / `Problem` / `Setup` machines receive no new cards
- [x] `Off` / `Idle` / `Production` machines remain eligible
- [x] Pre-assigned / planner workstation and `scheduled_time_logs` are never overridden
- [x] Legacy machine-in-BOM row falls back to its type with a logged warning
- [x] Bulk concurrent submission of 91 Work Orders → 134 cards, all typed, excluded machines untouched, no new errors
- [x] Diagnostic section 7 clean: capacity planning disabled, no scheduled-log leakage, no capacity overflow
- [x] Job Card save evaluates readiness for its own operation
- [ ] UAT verification (pending)
