# Tekson Manufacturing MES

**Phase 1 — Manufacturing Execution System for ERPNext V15**

---

## Overview

Manufacturing Execution System (MES) for Teksons, built on ERPNext V15. Extends standard ERPNext Manufacturing with readiness evaluation, dependency validation, and automated workflow controls — without replacing ERPNext's inventory, costing, or backflush engine.

**Status:** ✅ Released (`main` + `develop`) — UAT deployment pending
**Version:** v15.1.40
**Last Updated:** October 29, 2026

---

## Features

- Material Readiness Engine — per-operation WIP stock evaluation
- Dependency Engine — sequential operation blocking
- Child Work Order validation — parent blocked until sub-assemblies complete
- Auto Work Order completion — last JC triggers Manufacture SE + WO closure
- Multi-department WIP — per-operation warehouse assignment
- Workstation Type rotation — Job Cards rotate across the eligible machines of the BOM Operation's type (capacity-aware, least-recently-used, never overrides a schedule) — see [Workstation allocation](#workstation-allocation)
- WO Consolidation — sub-assemblies grouped by planned start date
- Daily Material Planning — Material Requests per department WIP, quantities net of WIP stock, target warehouse driven by each BOM item's operation
- Material Transfer Pick List — open-WO raw material transfers, source → operation-driven department WIP
- Batch production rounding — fixed-yield BOM support
- Clear operator error messages — shows exactly what's blocking

### Workstation allocation

v15.1.40 makes the **Workstation Type** on the BOM Operation the routing key. A
Job Card is never pinned to one machine by the BOM:

- **Rotation:** machines not at concurrent capacity → fewest queued Job Cards →
  least recently used → name
- **Load model:** `active_load` (`Work In Progress` / `On Hold`) is compared with
  `Workstation.production_capacity`; `open_load` (any non-closed card) is the
  queue and is never a hard availability filter
- **`last_used` is real production activity** (`actual_end_date`, or "now" while
  running) — not Job Card creation; cancelled and never-started cards do not count
- **Excluded machines:** `Maintenance`, `Problem`, `Setup`. Status follows the
  Job Card lifecycle: **starting a card sets its machine to `Production`** and
  **completing it sets the machine back to `Off`**, so `Off`, `Idle` and
  `Production` can all take new work. `Setup` means a **new machine being set
  up / commissioned**, `Problem` means a fault has been reported and
  `Maintenance` means the machine is under maintenance — those three are skipped
  until cleared.
- **Status is not availability:** the allocator counts open and active Job Cards
  on each machine; a free machine is never skipped just because its status is
  `Off`.
- **Never overridden:** user / planner / ERPNext scheduled picks are respected and
  `scheduled_time_logs` are not touched
- **Legacy machine-in-BOM rows** are a preference: fall back to that machine's
  type with a logged warning
- **All machines at capacity:** the least loaded machine is still assigned so Work
  Order submission is never blocked, with a warning reported by the diagnostic
- **Requires** `Manufacturing Settings → Disable Capacity Planning`; verify with
  `diagnose_mes_performance` section 7

Set up: give every **Workstation** a `workstation_type`, `plant_floor` and
`production_capacity`, and give every **BOM Operation** a `workstation_type`.
Details: `docs/V15.1.40_RELEASE_NOTES.md`, `docs/END_USER_MANUAL.md` §6.6.

---

## Architecture

```
ERPNext Hooks (thin delegation)
    ↓
MES Coordinator (single entry point)
    ↓
Readiness Engine (Material + Dependency + Child WO)
    ↓
Execution Engine (SE creation + WO completion)
```

**Key Principles:**
- ERPNext remains system of record for inventory, costing, backflush
- MES governs execution, readiness, dependency validation
- Department WIP model (shared across WOs, Bin-level stock)
- No stock reservation — first-come, first-consume
- Production Plan immutable — demand vs production qty separate

---

## Installation

```bash
bench get-app https://github.com/devosduotech/tekson_manufacturing --branch main
bench --site [site-name] install-app tekson_manufacturing
bench --site [site-name] migrate
```

---

## License

Proprietary — Teksons

---

## Contact

OSDuo Tech LLP — Tekson Manufacturing MES — ERPNext V15
