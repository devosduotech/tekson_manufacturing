# Tekson MES Phase 1 — Status

**Version:** v15.1.27
**Date:** September 16, 2026
**Status:** Phase 1.1 Complete — Ready for UAT

---

## Releases

| Version | Date | Features |
|---------|------|----------|
| **v15.1.27** | Sep 16 | BOM Bulk Creator bom_no fix (child BOM links left blank) |
| v15.1.26 | Sep 12 | Source warehouse contains match fix |
| v15.1.25 | Sep 12 | MR qty double-counting fix |
| **v15.1.1** | Aug 10 | WO Consolidation + Daily Material Planning |
| v15.0.3 | Aug 9 | Core MES + Code Hardening |
| v15.0.1 | Aug 7 | Internal UAT Baseline |

---

## v15.1.1 Features

| Feature | Description |
|---------|-------------|
| WO Consolidation | Sub-assembly WOs grouped by planned start date |
| Batch Planning | Fixed-yield BOM quantity rounding |
| Material Planning | Daily MR generation per department WIP |
| Standalone Page | `/app/material-planning` for stores person |
| PP Link | MR linked to Production Plan |
| Duplicate Prevention | Reuses existing draft MRs |

---

## v15.0.3 Core Features

| Feature | Status |
|---------|--------|
| Material Readiness | ✅ Working |
| Dependency Validation | ✅ Working |
| Child WO Blocking | ✅ Working |
| Auto WO Completion | ✅ Working |
| Per-operation WIP | ✅ Working |
| Batch Qty Rounding | ✅ Working |

---

## Quick Commands

### Dev Machine (remote: upstream)
```bash
cd ~/frappe-bench/apps/tekson_manufacturing
git fetch upstream && git reset --hard upstream/bom-bulk-creator
cd ~/frappe-bench && bench --site teksons.dev migrate && bench build --clear && bench restart
```

### UAT Machine (remote: origin)
```bash
cd ~/cwd-bench/apps/tekson_manufacturing
git pull origin main
cd ~/cwd-bench && bench --site tekson.site migrate && bench build --clear && bench restart
```
