# Tekson Manufacturing MES

**Phase 1 — Manufacturing Execution System for ERPNext V15**

---

## Overview

Manufacturing Execution System (MES) for Teksons, built on ERPNext V15. Extends standard ERPNext Manufacturing with readiness evaluation, dependency validation, and automated workflow controls — without replacing ERPNext's inventory, costing, or backflush engine.

**Status:** ✅ Phase 1 Complete — Internal UAT Passed  
**Version:** v15.0.1  
**Last Updated:** August 9, 2026

---

## Features

- Material Readiness Engine — per-operation WIP stock evaluation
- Dependency Engine — sequential operation blocking
- Child Work Order validation — parent blocked until sub-assemblies complete
- Auto Work Order completion — last JC triggers Manufacture SE + WO closure
- Batch production rounding — fixed-yield BOM support
- Multi-department WIP — per-operation warehouse assignment
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

## Documentation

All documentation in `docs/` folder:

| Document | Description |
|----------|-------------|
| `PHASE1_COMPLETION_REPORT.md` | Phase 1 definitive handoff document |
| `MES_BUSINESS_RULES.md` | Business rules specification |
| `WAREHOUSE_ARCHITECTURE_DECISION.md` | Department WIP model |
| `JOB_CARD_READINESS_ENGINE_TECHNICAL_SPEC.md` | Technical specification |
| `BUSINESS_PROCESS_FREEZE_v1.0.md` | Frozen manufacturing process |

---

## Versioning

| Version | Purpose |
|---------|---------|
| **v15.0.1** | Internal UAT Baseline |
| v15.0.2 | Critical Audit Fixes |
| v15.0.3 | Code Hardening |
| v15.1.0 | Phase 1 Production Release |

`MAJOR.MINOR.PATCH` — Major = ERPNext version, Minor = feature set, Patch = bug fix.

---

## License

Proprietary — Teksons

---

## Contact

OSDuo Tech LLP — Tekson Manufacturing MES — ERPNext V15
