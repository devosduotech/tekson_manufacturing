# Tekson Manufacturing MES

**Phase 1 — Manufacturing Execution System for ERPNext V15**

---

## Overview

Manufacturing Execution System (MES) for Teksons, built on ERPNext V15. Extends standard ERPNext Manufacturing with readiness evaluation, dependency validation, and automated workflow controls — without replacing ERPNext's inventory, costing, or backflush engine.

**Status:** ✅ Customer UAT Ready
**Version:** v15.1.5
**Last Updated:** August 18, 2026

---

## Features

- Material Readiness Engine — per-operation WIP stock evaluation
- Dependency Engine — sequential operation blocking
- Child Work Order validation — parent blocked until sub-assemblies complete
- Auto Work Order completion — last JC triggers Manufacture SE + WO closure
- Multi-department WIP — per-operation warehouse assignment
- WO Consolidation — sub-assemblies grouped by planned start date
- Daily Material Planning — Material Requests per department WIP
- Batch production rounding — fixed-yield BOM support
- Clear operator error messages — shows exactly what's blocking

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
