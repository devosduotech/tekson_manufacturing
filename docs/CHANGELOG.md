# MES Changelog

**Document Type:** Implementation History  
**Version:** 1.0  
**Date:** 2026-08-01  
**Status:** Active  
**Project:** Tekson Manufacturing MES  

---

## Version 1.0.0 - Design Baseline

**Date:** 2026-08-01  
**Status:** Frozen  
**Type:** Design Baseline Release

### Overview

Complete design and architecture documentation for Phase 1 MES implementation.

### Documents Included

**Business Specifications (3):**
- MES_BUSINESS_RULES.md (85 rules)
- MES_EXCEPTION_HANDLING_RULES.md (46 scenarios)
- MES_SECURITY_MATRIX.md (10 roles, 75 permissions)

**Architecture & Design (5):**
- MES_ARCHITECTURE_IMPLEMENTATION.md
- WAREHOUSE_ARCHITECTURE_DECISION.md
- MES_STATE_MACHINE.md
- MES_EVENT_FLOW.md
- MES_SEQUENCE_DIAGRAMS.md

**Technical Specifications (5):**
- MES_DATA_DICTIONARY.md (27 custom fields)
- MES_SERVICE_INTERFACES.md (35 methods)
- MES_REPOSITORY_INTERFACES.md (4 repositories)
- MES_CONFIGURATION_MATRIX.md (40 settings)
- MES_LOGGING_STANDARD.md (7 categories)

**Implementation Planning (6):**
- MES_IMPLEMENTATION_MATRIX.md (10 sprints)
- MES_BUSINESS_RULE_CROSS_REFERENCE.md
- CODE_REVIEW_STANDARDS.md
- MES_PERFORMANCE_BUDGET.md (25+ targets)
- MES_MIGRATION_STRATEGY.md (5 phases)
- MES_TEST_SCENARIOS.md (40+ test cases)

**Project Status (3):**
- PROJECT_TIMELINE.md
- PHASE1_STATUS_REPORT.md
- MES_DESIGN_FREEZE_CHECKLIST.md

---

## Version 1.0.1 - Material Readiness Framework

**Date:** 2026-08-01  
**Status:** Complete  
**Type:** Implementation Milestone

### Sprint 1: Material Readiness Engine

**Business Rules Implemented:**
- MR-010: Stores to Production handoff
- MR-011: Cumulative availability check

**Code Delivered:**
- `tekson_manufacturing/readiness/material_readiness.py` (~1,500 lines)
- `tekson_manufacturing/services/stock_service.py` (~350 lines)
- `tekson_manufacturing/repositories/` (~1,200 lines, 4 repositories)
- `tekson_manufacturing/utils/exceptions.py` (~80 lines)
- `tekson_manufacturing/utils/__init__.py` (~200 lines)

**APIs Delivered:**
- `evaluate_material_readiness(work_order)`
- `can_job_card_start(job_card)`
- `get_transfer_suggestions(work_order)`
- `create_material_transfer_stock_entry(work_order)`

**Tests Delivered:**
- 11 unit tests in `test_material_readiness.py`
- Coverage: 100% of implemented code

**Documentation Delivered:**
- 11 technical specification documents
- Repository interfaces
- Service interfaces
- Data dictionary

---

## Version 1.0.2 - Sprint 2 Complete

**Date:** 2026-08-01  
**Status:** Complete  
**Type:** Implementation Milestone

### Sprint 2: Dependency Engine

**Implemented:**
- DV-001: Previous operation validation
- DV-002: Sequence validation

**Code:**
- `tekson_manufacturing/validation/dependency_engine.py` (800 lines)

**APIs:**
- `validate_previous_operation(job_card)`
- `validate_sequence(work_order)`
- `get_dependency_status(job_card)`
- `can_job_card_start(job_card)`

**Tests:**
- 11 unit tests in `test_dependency_engine.py`

**Integration:**
- Integrated with Sprint 1 (Material Readiness)
- Integrated with Execution Engine

---

## Version 1.0.3 - Sprint 3 Complete

**Date:** 2026-08-01  
**Status:** Complete  
**Type:** Implementation Milestone

### Sprint 3: Execution Engine

**Implemented:**
- JC-001: Job Card Start Permission
- JC-002: Job Card Completion Permission
- JC-003: Job Card Material Check
- JC-004: Job Card Auto-Refresh
- JC-005: Job Card Work Order Link
- WO-001: Auto-Completion Trigger
- WO-002: Duplicate Stock Entry Prevention

**Code:**
- `tekson_manufacturing/execution/execution_engine.py` (900 lines)

**APIs:**
- `can_start_job_card(job_card)`
- `can_complete_job_card(job_card)`
- `complete_work_order_api(work_order)`
- `refresh_job_card_status_api(job_card)`

**Tests:**
- 11 unit tests in `test_execution_engine.py`

**Integration:**
- Integrated with Sprint 1 (Material Readiness)
- Integrated with Sprint 2 (Dependency)
- Full core manufacturing flow complete

---

## Version 1.0.4 - Documentation Governance

**Date:** 2026-08-01  
**Status:** Complete  
**Type:** Documentation Update

### Added Documents

**Governance:**
- DOCUMENTATION_GOVERNANCE.md (baseline control policy)

**Tracking:**
- TECHNICAL_DEBT.md (7 items)
- KNOWN_LIMITATIONS.md (8 limitations)
- MES_INTEGRATION_MATRIX.md (integration tracking)
- CHANGELOG.md (this document)
- DECISION_LOG.md (design decisions)
- RELEASE_CHECKLIST.md (deployment checklist)
- VERSION_ROADMAP.md (version planning)

### Updated Documents

**PHASE1_STATUS_REPORT.md:**
- Realistic metrics (35% by effort, 13% by business rules)
- Executive dashboard
- Production readiness definition
- Integration status

**MES_IMPLEMENTATION_MATRIX.md:**
- Sprint completion summary
- Business rule implementation status
- Progress tracking with burndown charts

---

## Released Versions

### Version v15.1.5 - Customer UAT Release

**Date:** 2026-08-18
**Status:** ✅ Customer UAT Ready
**Branch:** `v15.1.5-uat` / Tag `v15.1.5`

Consolidates Phase 1 (MES Execution) + Phase 1.1 (Planning) with 12 critical bug fixes identified during internal testing.

**Critical Fixes:**
1. Department transfers trigger JC refresh (`purpose` field fix)
2. `custom_start_status` synced with readiness engine
3. Removed broken JS reference (Status column disappearing)
4. `complete_job_card` triggers downstream JC refresh
5. Refresh ALL parallel JCs (not just one)
6. JC status fields reflect lifecycle state (Open/WIP/Completed)
7. `validate_job_card_start` is single source of truth for `can_start`
8. WO status updates on Manufacture SE submit
9. Exploded multi-level BOM (memoization) for material requests
10. Proper SE insert + SLE verification (no silent stock failures)
11. Material readiness skips sub-assemblies (handled by child WO check)
12. `refresh_job_card_status` single evaluation (consistent with auto-update)

See `docs/V15.1.5_RELEASE_NOTES.md` for full details.

---

### Version 1.0.5 - Sprint 4 Complete

**Date:** 2026-08-01  
**Sprint:** 4  
**Focus:** Diagnostics & Messages  
**Business Rules:** DM-001 to DM-004  
**Status:** ✅ Complete

### Code Delivered

**New Modules:**
- `diagnostics/messages.py` (~650 lines)
  - `DiagnosticMessages` class
  - `DiagnosticCategory` enum (8 categories)
  - `SeverityLevel` enum (5 levels)
  - Message builders (6 types)
  - UI formatting methods
  - Context-aware messaging
  - Diagnostic logging

**APIs Delivered:**
- `get_diagnostic_message()` - Build diagnostic messages
- `format_diagnostics_for_ui()` - Format for UI display
- `log_diagnostic_message()` - Log diagnostics

**Tests Delivered:**
- `test_diagnostics.py` (11 tests)
  - DM-001 tests (4 tests)
  - DM-002 tests (6 tests)
  - DM-003 tests (6 tests)
  - DM-004 tests (5 tests)
  - Integration tests

### Business Rules Delivered

- ✅ DM-001: Clear Operator Messages (6 message types)
- ✅ DM-002: Diagnostic Categories (8 categories)
- ✅ DM-003: Severity Levels (5 levels)
- ✅ DM-004: UI-Friendly Formatting (color coding, context)

---

## Planned Versions

### Version 1.0.6 - Sprint 5 Complete

**Date:** 2026-08-01  
**Sprint:** 5  
**Focus:** Department Transfer Integration  
**Business Rules:** WH-001 to WH-005  
**Status:** ✅ Complete

### Code Delivered

**Enhanced Modules:**
- `services/stock_service.py` (~250 lines added)
  - `create_department_transfer()` - WH-004
  - `validate_department_transfer()` - WH-003
  - `is_department_warehouse()` - WH-001
  - `get_department_warehouse()` - WH-002
  - Department mapping (6 Teksons departments)

**APIs Delivered:**
- `create_department_transfer()` - Create inter-department transfers
- `validate_department_transfer()` - Validate transfer parameters

**Tests Delivered:**
- `test_department_transfer.py` (11 tests)
  - WH-001: Warehouse classification
  - WH-002: Department mapping (5 tests)
  - WH-003: Validation tests (2 tests)
  - WH-004: Transfer creation tests
  - WH-005: Naming convention tests

### Business Rules Delivered

- ✅ WH-001: Warehouse Type Classification
- ✅ WH-002: Department-to-Warehouse Mapping
- ✅ WH-003: Department Warehouse Validation
- ✅ WH-004: Department Transfer Creation
- ✅ WH-005: Teksons Naming Convention

---

### Version 1.0.7 - Sprint 6 Complete

**Date:** 2026-08-01  
**Sprint:** 6  
**Focus:** Exception Handling Integration  
**Business Rules:** 46 scenarios (EX-*)  
**Status:** ✅ Complete

### Code Delivered

**New Modules:**
- `diagnostics/exception_handler.py` (~650 lines)
  - Exception hierarchy (6 categories)
  - ExceptionHandler class
  - User-friendly message mapping
  - Context preservation
  - Logging integration
  - 6 convenience raise functions

**Exception Categories:**
- MaterialException (EX-MAT-001 to EX-MAT-008) - 8 scenarios
- ProductionException (EX-PROD-001 to EX-PROD-010) - 10 scenarios
- EquipmentException (EX-EQ-001 to EX-EQ-008) - 8 scenarios
- QualityException (EX-Q-001 to EX-Q-008) - 8 scenarios
- CancellationException (EX-CANCEL-001 to EX-CANCEL-006) - 6 scenarios
- SystemException (EX-SYS-001 to EX-SYS-006) - 6 scenarios

**APIs Delivered:**
- `handle_exception()` - Central exception handling

**Tests Delivered:**
- `test_exception_handling.py` (20 tests)
  - Category classification tests
  - Material exception tests (3)
  - Production exception tests (3)
  - Equipment exception tests (2)
  - Quality exception tests (2)
  - Cancellation exception tests (2)
  - System exception tests (1)
  - Exception handling tests (3)
  - Whitelisted method tests (3)

### Business Rules Delivered

- ✅ EX-MAT-* (8): Material exceptions
- ✅ EX-PROD-* (10): Production exceptions
- ✅ EX-EQ-* (8): Equipment exceptions
- ✅ EX-Q-* (8): Quality exceptions
- ✅ EX-CANCEL-* (6): Cancellation exceptions
- ✅ EX-SYS-* (6): System exceptions

### Version 1.0.8 - Sprint 7 Complete (Planned)

**Sprint:** 7  
**Focus:** Security & Permissions  
**Business Rules:** SEC-001 to SEC-005  
**Expected Date:** Week 6-7

### Version 1.0.9 - Sprints 8-9 Complete (Planned)

**Sprints:** 8-9  
**Focus:** MES UI  
**Expected Date:** Week 7-8

### Version 1.0.10 - Sprint 10 Complete (Planned)

**Sprint:** 10  
**Focus:** Integration Testing & UAT Prep  
**Expected Date:** Week 9  
**Milestone:** Production Ready

### Version 1.1.0 - Phase 1 Release (Planned)

**Focus:** Phase 1 Production Release  
**Milestone:** Customer Go-Live  
**Expected Date:** After successful UAT

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-08-01 | Development | Design baseline frozen |
| 1.0.1 | 2026-08-01 | Development | Sprint 1 complete |
| 1.0.2 | 2026-08-01 | Development | Sprint 2 complete |
| 1.0.3 | 2026-08-01 | Development | Sprint 3 complete |
| 1.0.4 | 2026-08-01 | Development | Documentation governance |
| 15.1.25 | 2026-09-12 | Development | MR qty double-counting fix |
| 15.1.26 | 2026-09-12 | Development | Source warehouse contains match fix |
| 15.1.27 | 2026-10-07 | Development | Work Order warehouse auto-set (WIP/FG/Source) |
| 15.1.28 | 2026-10-07 | Development | Work Order Scrap Warehouse auto-copied from WIP Warehouse |
| 15.1.29 | 2026-10-08 | Development | Raw Material Loss % (RM Loss %) on BOM Item for Material Request generation |
| 15.1.32 | 2026-10-21 | Development | Job Card slowness overhaul (readiness, batching, queued refresh) + Work Order cancel revert |
| 15.1.33 | 2026-10-21 | Development | Job Card dependency lookup includes draft JCs (docstatus != 2); start-blocked message fix |
| 15.1.34 | 2026-10-21 | Development | Allow Line Supervisor + Machine Operator roles for MES execution (JC complete / WO submit) |
| 15.1.35 | 2026-10-23 | Development | Role-model alignment: JC vs WO-release gates; workspace / pick list / BOM Bulk Creator audiences |

---

## Version 15.1.27 — Work Order Warehouse Auto-Set

**Date:** 2026-10-07  
**Status:** Released  
**Type:** Feature

### Changes
- Work Order warehouses auto-populated on creation via `before_insert` hook
- FG Warehouse from BOM's `target_fg_warehouse`
- WIP Warehouse from first operation's workstation → plant floor → department WIP
- Source Warehouse defaults to "Stores - TPL"

### Files Changed
- `tekson_manufacturing/services/work_order_service.py` — `set_warehouses()`
- `tekson_manufacturing/hooks.py` — Work Order `before_insert` event

---

## Version 15.1.28 — Work Order Scrap Warehouse Auto-Copy

**Date:** 2026-10-07  
**Status:** Released  
**Type:** Feature

### Changes
- Scrap Warehouse automatically set to WIP Warehouse during Work Order insertion
- Overrides any form default (e.g., "Scrap Stores - TPL") on save
- No synchronization after insertion — user changes to either warehouse are retained

### Logic
```python
if doc.wip_warehouse:
    doc.scrap_warehouse = doc.wip_warehouse
```

### Files Changed
- `tekson_manufacturing/services/work_order_service.py` — `set_warehouses()`

---

## Version 15.1.29 — Raw Material Loss % (RM Loss %) on BOM Item

**Date:** 2026-10-08  
**Status:** Released  
**Type:** Feature

### Changes
- **RM Loss % field on BOM Item**: New field `custom_rm_loss_pct` (Percent, 2 decimals, default 0%) to define expected raw material loss during manufacturing (cutting, trimming, forming wastage)
- **Material Request generation applies RM Loss**: Required Qty = Base Qty (BOM qty × WO qty) × (1 + RM Loss %)
- **New traceability fields on Material Request Item**:
  - `custom_bom_qty` (Qty as per BOM) — theoretical quantity from BOM without RM Loss %
  - `custom_rm_loss_pct` (RM Loss %) — read-only, from BOM Item
  - `custom_rm_loss_qty` (RM Loss Qty) — read-only, calculated loss quantity
  - `qty` — auto-calculated as Base Qty + RM Loss Qty (rounded up)
- **Manufacture Stock Entry applies RM Loss**: Raw material quantities in manufacture entry increased by RM Loss % to match transferred quantities
- **Sub-assembly support**: RM Loss % propagates through multi-level BOMs (skips sub-assemblies with own WOs)

### Files Changed
- `tekson_manufacturing/planning/material_planning_service.py` — Core MR generation logic with RM Loss %
- `tekson_manufacturing/execution/execution_engine.py` — `apply_rm_loss_to_manufacture_entry()` for manufacture entries
- `tekson_manufacturing/patches/create_rm_loss_pct_fields.py` — Custom fields patch (BOM Item + MR Item)
- `tekson_manufacturing/patches/update_rm_loss_fields.py` — Read-only UI fields patch
- `tekson_manufacturing/public/js/material_request_rm_loss.js` — Client script for read-only UI fields
- `tekson_manufacturing/tekson_manufacturing/doctype/bom_bulk_creator/bom_bulk_creator.py` — BOM Item field support

---

## Version 15.1.25 — MR Qty Double-Counting Fix

## Version 15.1.25 — MR Qty Double-Counting Fix

**Date:** 2026-09-12  
**Status:** Released  
**Type:** Bug Fix

### Problem
MR quantities were inflated (e.g., Aluminium Coil 0.2*110 = 74 kg instead of expected 5.736 kg).

### Root Cause
`_explode_bom` recursively expanded ALL sub-assemblies. When multiple WOs existed for the same Production Plan, raw materials were counted at every level of the BOM hierarchy.

### Fix
- Added `wo_bom_nos` parameter to `_explode_bom()` and `_get_raw_bom_items()`
- `generate_daily_material_requests()` builds set of BOMs with their own WOs
- When a sub-assembly's BOM is in `wo_bom_nos`, skip recursion — that WO requests its own materials

### Files Changed
- `planning/material_planning_service.py` — `_explode_bom()`, `_get_raw_bom_items()`, `generate_daily_material_requests()`

---

## Version 15.1.26 — Source Warehouse Contains Match Fix

**Date:** 2026-09-12  
**Status:** Released  
**Type:** Bug Fix

### Problem
After qty fix, MR still showed only 3 items (70 MISSING). `_is_source_warehouse` checked exact match "Raw Material Stores" but warehouse name was "Raw Material Stores - TPL".

### Fix
- `_is_source_warehouse()` now uses contains match: `"Raw Material Stores" in wh_name`
- `_get_default_source_warehouse()` uses contains fallback query
- Handles warehouse names with location suffixes (e.g., "- TPL")

### Files Changed
- `planning/material_planning_service.py` — `_is_source_warehouse()`, `_get_default_source_warehouse()`

## Version 15.1.30 — Work Order Completion & Job Card Status Fixes

**Date:** 2026-10-10  
**Status:** Released  
**Type:** Bug Fix / Feature

### Changes
- **WO Completion Fixes**: Fixed source warehouse logic to only override if material was actually transferred to WIP; otherwise preserves original source (e.g., Raw Materials Stores)
- **FG Warehouse Fix**: Finished goods now correctly set to BOM's `target_fg_warehouse` (via `wo.fg_warehouse`) with fallback to WIP warehouse
- **Manufacture Stock Entry Permissions**: Added `ignore_permissions=True` for system-generated Stock Entry creation, allowing line supervisors to complete WOs
- **RM Loss % in Manufacture Entry**: Applied RM Loss % from BOM to raw material quantities in manufacture stock entry to match transferred quantities
- **WO Status Auto-Update**: Work Order status now automatically changes to "In Process" when first Job Card transitions to "Work In Progress" (on Job Card `on_submit` hook)
- **Warehouse Query Fix**: Fixed `warehouse_group_name` → `warehouse_group` for Frappe 15.122.0 compatibility

### Files Changed
- `tekson_manufacturing/execution/execution_engine.py` — Fixed `complete_work_order()` source warehouse, FG warehouse, RM Loss %, permissions
- `tekson_manufacturing/utils/job_card_utils.py` — Added `update_wo_status_on_jc_start()` function
- `tekson_manufacturing/hooks.py` — Registered `update_wo_status_on_jc_start` in Job Card `on_submit` hook

---

## Version 15.1.31 — Material Transfer Pick List Report

**Date:** 2026-10-12
**Status:** On `develop` and `main` (v15.1.31)
**Type:** Bug Fix / Feature

### Problem
The report opened with no filter fields, then with filters but no rows
("Nothing to show"), even though the query returned 35 rows from the console.

### Root Causes
1. **Report JS never loaded.** Frappe reads Script Report JS from
   `<app>/<module>/report/<scrub(name)>/<scrub(name)>.js`
   (`frappe.desk.query_report.get_script`). The JS was not there, so
   `report_doc.filters` was never applied and the filter form was not built.
2. **Python module path did not resolve.** `Report.execute_module()` uses
   `get_report_module_dotted_path` →
   `<app>.<module>.report.<scrub(name)>.<scrub(name)>.execute`. The
   implementation only existed under `tekson_manufacturing/reports/`.
3. **Prepared-report flip.** `Report.execute_script_report()` arms a 15s timer
   that sets `prepared_report = 1`. The prepared branch returns no
   `columns`/`result`, which the UI shows as *"Nothing to show"*.
4. **Open WO filter too narrow.** `Closed` and `Cancelled` Work Orders were not
   excluded, so finished/closed orders still listed materials.

### Fixes
- Added the conventional report JS with `from_date` / `to_date` filters
- Added the conventional report `.py` entry point (re-exports the
  implementation in `reports/`)
- Pinned `prepared_report = 0` and `disable_prepared_report_automation = 1`
  in the report JSON
- Widened defaults to `2026-01-01` … `2026-12-31`
- Work Order filter is now `status NOT IN ('Completed','Closed','Stopped','Cancelled')`
  with `docstatus = 1`, so only **open** WOs build the material list

### Files Changed
- `tekson_manufacturing/tekson_manufacturing/report/material_transfer_pick_list/material_transfer_pick_list.js` — filter definitions
- `tekson_manufacturing/tekson_manufacturing/report/material_transfer_pick_list/material_transfer_pick_list.py` — Frappe entry point
- `tekson_manufacturing/tekson_manufacturing/report/__init__.py`
- `tekson_manufacturing/tekson_manufacturing/report/material_transfer_pick_list/__init__.py`
- `tekson_manufacturing/reports/material_transfer_pick_list/material_transfer_pick_list.py` — open-WO filter
- `tekson_manufacturing/reports/material_transfer_pick_list/material_transfer_pick_list.json` — `prepared_report`, `disable_prepared_report_automation`, `javascript`, filter defaults
- `docs/MATERIAL_TRANSFER_PICK_LIST_REPORT.md` — new report documentation

### Site Repair (required on already-deployed sites)
```python
frappe.db.set_value('Report', 'Material Transfer Pick List', {
    'prepared_report': 0,
    'disable_prepared_report_automation': 1,
    'javascript': '',
})
frappe.db.commit()
frappe.clear_cache()
```

---

## Version 15.1.31 — Demand-Driven Split Routing (Dual Target FG Warehouse)

**Date:** 2026-10-14
**Status:** On `develop` (v15.1.31)
**Type:** Feature

### Requirement
A single component BOM must be able to feed two destination warehouses
(e.g., Core End Plate 100x100x20 → one unit to direct Assembly at
`WIP-Ralu In`, one unit to Sr. No. punching at `WIP-RP`) without
doubling the BOM quantity (BOM qty stays 1 so a single unit can always
be produced as a replacement part).

### Design
- **`target_fg_warehouse` (Target FG Warehouse 1)** — mandatory, unchanged.
- **`target_fg_warehouse_2` (Target FG Warehouse 2)** — new, optional
  custom field on the BOM header.
- When both are configured, each **BOM Item child row's `source_warehouse`**
  decides the destination:
  - matches Warehouse 1 → demand routes to the primary warehouse
  - matches Warehouse 2 → demand routes to the secondary warehouse
  - matches neither → the existing warehouse-flow error/validation still applies
- The Production Plan keeps such demand as **separate sub-assembly rows**
  (the combine key already includes `fg_warehouse`), so it creates
  **one Work Order per destination with its own quantity**
  (e.g., WO 1 → Warehouse 1 qty 10, WO 2 → Warehouse 2 qty 5).
  Stock transfers follow each WO's qty — no intra-WO split required.
- Split demand is computed from **immediate** BOM Item rows only
  (no multi-level recursion); demands from multiple parent BOMs stay
  separate rows and are never merged across destinations.

### Changes
- New patch `add_target_fg_warehouse_2` creates
  `BOM.target_fg_warehouse_2` and `BOM Bulk Creator.target_fg_warehouse_2`
  (Link → Warehouse, non-mandatory)
- `TeksonProductionPlan.set_sub_assembly_items_based_on_level()` routes
  each sub-assembly row's `fg_warehouse` by matching the consuming
  BOM Item `source_warehouse` against primary/secondary targets
- BOM Bulk Creator copies `target_fg_warehouse_2` to every generated BOM
  (`BOM_FIELDS`)
- `verify_bom_flow` accepts parent `source_warehouse` matching **either**
  target as a valid flow; a source matching neither still reports the
  existing mismatch error; summary now counts split-configured BOMs

### Files Changed
- `tekson_manufacturing/patches/add_target_fg_warehouse_2.py` — new patch
- `tekson_manufacturing/patches.txt` — patch registered
- `tekson_manufacturing/overrides/production_plan.py` — split FG routing
- `tekson_manufacturing/tekson_manufacturing/doctype/bom_bulk_creator/bom_bulk_creator.py` — `BOM_FIELDS`
- `tekson_manufacturing/scripts/verify_bom_flow.py` — primary/secondary match

### Deployment
Run `bench migrate` (creates the two custom fields). Existing BOMs are
**not** modified — end users update `target_fg_warehouse_2` manually where
split routing is required.

---

## Version 15.1.31 — Split Routing Diagnostic & Unrouted-Demand Warning

**Date:** 2026-10-14
**Status:** On `develop` (v15.1.31)
**Type:** Tooling + Guard

### Problem
UAT: releasing Core Assembly (1 × core end plate + 1 × core end plate sr.no.)
created only **one** core end plate Work Order instead of two
(`WIP-Ralu In` + `WIP-RP`), blocking the sr.no. Job Card — no raw material
reached `WIP-RP`. The demand silently merged because its `source_warehouse`
matched neither target, and nothing reported it.

### Changes
- **New** `scripts/diagnose_split_routing.py` — read-only `bench execute`
  diagnostic (`diagnose` for a Production Plan, `diagnose_bom` for one BOM
  tree). Reports:
  1. Environment — custom field present, `TeksonProductionPlan` registered,
     `_route_split_fg_warehouse` deployed, app version
  2. BOM config — every dual-target demand vs its parent `source_warehouse`,
     plus rows with no BOM No linked (demand never exploded)
  3. Prediction — re-runs `Production Plan.get_sub_assembly_items()` in
     memory (**never saved**) and prints the Work Orders that would be created
  4. Verdict — `OK` / `CONFIG_MISMATCH` / `STALE_ROWS` (plan exploded before
     config or old workers — remedy: restart + re-run Get Sub Assembly Items)
     / `PATCH_NOT_RUN` / `OVERRIDE_NOT_ACTIVE`, each with concrete remedies
- **`overrides/production_plan.py`** — `_route_split_fg_warehouse` now shows a
  *Split Routing Warning* msgprint naming every dual-target demand whose
  source matches neither Target 1 nor Target 2, instead of silently keeping
  the default warehouse and merging into one Work Order
- Non-dual-target BOMs are untouched: one Work Order, primary target

### Files Changed
- `tekson_manufacturing/scripts/diagnose_split_routing.py` — new
- `tekson_manufacturing/overrides/production_plan.py` — unrouted-demand warning

### Usage
```
bench --site <site> execute tekson_manufacturing.scripts.diagnose_split_routing.diagnose --args '["<Production Plan>"]'
bench --site <site> execute tekson_manufacturing.scripts.diagnose_split_routing.diagnose_bom --args '["<BOM>"]'
```

---

## Version 15.1.32 — Job Card Slowness Overhaul & Work Order Cancel Revert

**Date:** 2026-10-21
**Status:** On `develop` (v15.1.32)
**Type:** Performance + Correctness

### Problem
UAT: Job Card **Start** and Job Card **execution** intermittently hung or threw
"server busy" errors. Root causes were all write amplification on the request
thread:

1. The five readiness status fields were recomputed and saved multiple times
   per Job Card save (validate hook + readiness cascade), and the readiness
   engine called `jc.save()` — re-entering the very validate hook that triggered it.
2. Inter-department Stock Entries were created **inline** during evaluation,
   so a shortage turned one Job Card start into a full Stock Entry submit.
3. `refresh_work_order` / `refresh_next_job_card` did a `frappe.get_doc` per
   Job Card, and material readiness ran per-item Bin / BOM / child-WO queries.
4. `frappe.log_error()` INSERTs an Error Log row on **every** call and it was
   used for ordinary success/skip breadcrumbs — an Error Log write per Job Card.
5. WO-wide readiness refreshes ran synchronously on the submit path.
6. **Cancel bug:** `ExecutionEngine.update_work_order_status` blind-wrote
   `status = "Completed"`, so cancelling a Job Card or Stock Entry marked the
   Work Order Completed — even though ERPNext core had just correctly reverted it.

### Changes
- **Single status mapping** — `JobCardService.compute_status_fields()` is now
  the one source of truth for the five readiness fields, shared by the validate
  hook and every refresh; evaluation is cached once per Job Card per save.
- **Read-only readiness** — `JobCardReadinessEngine.apply_result_to_job_card()`
  diffs only the changed readiness fields and writes them with `db.set_value`;
  it **never** calls `jc.save()`, so a refresh can no longer re-trigger validation.
- **Plan-only transfers** — evaluation plans inter-department transfers
  (BOM `target_fg_warehouse` / `_2`, live Bin check) and hands them to
  `execute_inter_department_transfer`, a deduplicated background job that
  re-reads live stock, is idempotent (outstanding = required − Bin(target) −
  draft SEs) and re-plans its source at run time.
- **Batched queries** — one Bin query, one BOM query and one child-WO SQL per
  evaluation replace the per-item loops; refresh paths use lightweight
  `get_all` instead of `get_doc` per Job Card.
- **Logging cleanup** — `log_mes_event()` routes ERROR/CRITICAL to
  `frappe.log_error` and everything else to the logger; success/skip
  breadcrumbs demoted to `logger.debug/info`. Real failures and security
  audit events still hit the Error Log.
- **Queued refreshes** — WO-submit, SE-submit and Job Card completion now
  enqueue `refresh_work_order_job` on the short queue
  (`mes-wo-refresh::{wo}`, deduplicated, after-commit, synchronous under
  `bench run-tests`); a re-entrancy guard prevents nested loops.
- **Work Order cancel reverts** — `update_work_order_status` /
  `refresh_work_order_status` now delegate to ERPNext's canonical
  `WorkOrder.update_status()` (docstatus / produced qty / transferred qty)
  instead of force-writing "Completed". `on_job_card_cancel` and
  `on_stock_entry_cancel` recompute the status **and** queue a readiness
  refresh so downstream Job Cards revert too. Closed/Stopped Work Orders are
  left untouched. `api.work_order.refresh_work_order_status` returns the
  resulting status. Fixed `WorkOrderService.refresh_status`, which called a
  non-existent `wo.set_status()` (Work Order is a plain `Document`, not a
  `StatusUpdater`) and raised `AttributeError`.
- **New diagnostics** — `scripts/diagnose_mes_performance.py`, a read-only
  `bench execute` report: retired Server Scripts, Error Log volume, index
  candidates, queue health, readiness snapshot and a consistency spot-check
  comparing stored `custom_*` fields against a live evaluation.

### Files Changed
- `tekson_manufacturing/services/job_card_service.py` — `compute_status_fields`, cached evaluation, `refresh_status` fix
- `tekson_manufacturing/readiness/job_card_readiness.py` — field-diff apply, transfer enqueue, queued WO refresh
- `tekson_manufacturing/readiness/material_readiness.py` — batched queries, transfer planning/execution, queue helper
- `tekson_manufacturing/execution/execution_engine.py` — status recompute (cancel revert), cancel readiness refresh
- `tekson_manufacturing/api/work_order.py` — `refresh_work_order_status` recompute + returned status
- `tekson_manufacturing/mes/mes_coordinator.py`, `mes/dataclasses.py`, `utils/`, `services/permission_service.py`, `services/stock_service.py`, `api/job_card_start.py` — queued refreshes, `pending_transfers`, logging cleanup
- `tekson_manufacturing/scripts/diagnose_mes_performance.py` — new
- `tekson_manufacturing/tests/test_status_mapping.py` — new (pure unit tests, no DB)

### Usage
```
bench --site <site> execute tekson_manufacturing.scripts.diagnose_mes_performance.run
bench --site <site> run-tests --module tekson_manufacturing.tests.test_status_mapping
```

---

## Version 15.1.33 — Job Card Dependency Lookup on Draft Job Cards

**Date:** 2026-10-21
**Status:** On `develop` (v15.1.33)
**Type:** Bug Fix

### Problem
Starting a Job Card failed with:

```
Cannot start Punching: Previous operation Job Card not found.
Complete None first.
```

Site diagnosis (WO of `JC-WO/261021/0113-002`): sequences were correct
(`1, 2`), but **both Job Cards were draft (`docstatus = 0`)** — this project
starts Job Cards before submitting them (status `Open` → `Work In Progress`).
The previous-operation queries filtered `AND docstatus = 1`, so the
predecessor was invisible and returned "not found".

The same `None` also poisoned the status mapping
(`dependency_ok = not previous_operation or ... == "Completed"`), which read a
failed lookup as "first operation" — which is why
**"Awaiting Previous Operation" never appeared** and only material-driven
statuses were shown.

### Changes
- `JobCardRepository.get_previous_operation`, `JobCardRepository.get_next_operation`
  and `JobCardService.get_previous_operation_status` now filter
  `docstatus != 2` (include draft + submitted, exclude cancelled) — matching
  the readiness refresh chain (`refresh_work_order` / `refresh_next_job_card`),
  which already used `docstatus != 2`.
- Start-blocked message no longer prints "Complete None first." — when no
  previous Job Card name exists it falls back to the dependency diagnostic
  ("Cannot find previous operation Job Card. Check Work Order routing
  configuration.").

### Files Changed
- `tekson_manufacturing/repositories/job_card_repository.py` — prev/next lookup filter
- `tekson_manufacturing/services/job_card_service.py` — display-path lookup filter
- `tekson_manufacturing/utils/job_card_utils.py` — start-blocked message

### Expected Behavior (reference WO .../0113)
- `JC-WO/261021/0113-002` (Punching, draft, seq 2) now finds
  `JC-WO/261021/0113-001` (Shearing, draft, status `Open`) →
  `custom_start_status` = "Awaiting Previous Operation"; start blocked with
  "Previous operation not complete: Open. Complete JC-WO/261021/0113-001 first."
- Once Shearing completes, the completion refresh finds sequence 2 (draft
  included) and JC-002 re-evaluates to Ready to Start / Awaiting Material.

---

## Version 15.1.34 — Floor Roles Allowed for MES Execution

**Date:** 2026-10-21
**Status:** On `develop` (v15.1.34)
**Type:** Bug Fix / Permission

### Problem
Completing a Job Card as a user with the custom role **Line Supervisor** failed:

```
Security Event: JOB_CARD_COMPLETE_ERROR
This action requires one of these roles: Manufacturing User,
Manufacturing Manager, Administrator
```

The MES execution gate (`validate_manufacturing_role`, called from the Job
Card-complete and Work-Order-submit coordinators) hardcoded ERPNext's
manufacturing roles only, while the production-floor executor roles on this
site are **Line Supervisor** and **Machine Operator**.

### Changes
- New `FLOOR_EXECUTION_ROLES` constant in `security/security_utils.py` —
  Manufacturing User, Manufacturing Manager, Line Supervisor, Machine
  Operator, Administrator — used by `validate_manufacturing_role` for both
  the JC-complete and WO-submit paths.

### Site setup reminder
The app gate only checks the role list. The two custom roles still need
standard DocType permissions in Role Permission Manager (Job Card:
read/write/submit; Work Order: read).

### Files Changed
- `tekson_manufacturing/security/security_utils.py`

---

## Version 15.1.35 — Role Model Alignment (Execution vs Release)

**Date:** 2026-10-23
**Status:** On `develop` (v15.1.35)
**Type:** Permission / Configuration

### Problem
The MES role gates and UI audiences still assumed ERPNext's stock
manufacturing roles, while the site now runs a 19-role hierarchy (Line
Supervisor, Machine Operator, Planning, Stores, Quality, Maintenance,
Design, ...):

- WO submit (production release) shared the JC-execution list, so Line
  Supervisor / Machine Operator could release Work Orders — outside their
  scope (operators execute JCs; JC submit auto-updates WO status server-side)
- The "Tekson Manufacturing" workspace was visible only to Stock/Manufacturing
  roles — none of the new roles saw the MES hub
- The Material Transfer Pick List report was similarly unreachable
- BOM Bulk Creator granted full CRUD including delete to Manufacturing User,
  while BOM ownership per the role model belongs to Design HOD / Engineer

### Changes
- `JC_EXECUTE_ROLES` — Line Supervisor, Machine Operator (+ legacy
  Manufacturing roles, Admin): Job Card complete path
- `WO_RELEASE_ROLES` — Planning HOD, Planning Engineer, Production
  Controller, General Manager (+ legacy, Admin): Work Order submit/release
  path; `validate_manufacturing_role()` now accepts an optional role list
- Workspace roles extended to the full management / planning / production /
  stores / quality / maintenance / design audience
- Material Transfer Pick List report: added Stores Manager/User, Receiving
  Stores User, Planning Engineer, Production Controller, Line Supervisor
- BOM Bulk Creator: added Design HOD (incl. delete) and Design Engineer
  (create/read/write)

### Deployment
`bench migrate` required (JSON role permissions sync on migrate), then
`bench restart`.

### Files Changed
- `tekson_manufacturing/security/security_utils.py` — role lists + optional arg
- `tekson_manufacturing/mes/mes_coordinator.py` — WO submit uses WO_RELEASE_ROLES
- `tekson_manufacturing/workspace/tekson_manufacturing/tekson_manufacturing.json`
- `tekson_manufacturing/reports/material_transfer_pick_list/material_transfer_pick_list.json`
- `tekson_manufacturing/tekson_manufacturing/doctype/bom_bulk_creator/bom_bulk_creator.json`

---

## Related Documents

- PHASE1_STATUS_REPORT.md - Overall project status
- MES_IMPLEMENTATION_MATRIX.md - Sprint tracking
- VERSION_ROADMAP.md - Future version planning
- DOCUMENTATION_GOVERNANCE.md - Version control policy
