# Pending Fixes — Phase 1 & Phase 1.1

**Date:** Aug 10, 2026
**Current Version:** v15.1.2
**Target:** v15.2.0

---

## Phase 1 — MES Execution (v15.0.x)

### HIGH
| ID | File | Issue | Effort |
|----|------|-------|--------|
| H2 | `api/job_card_start.py` | `save(ignore_permissions=True)` — review if PermissionService validates first | 30 min |
| H5 | `public/js/job_card_list.js` | `setInterval()` with max retry — done in v15.1.2 | ✅ Fixed |

### MEDIUM
| ID | File | Issue | Effort |
|----|------|-------|--------|
| M1 | `api/job_card_start.py` | No `frappe.db.exists()` check before `get_doc()` | 15 min |
| M2 | `diagnostics/messages.py` | Bare `except Exception` swallows errors | 1 hr |
| M3 | `diagnostics/messages.py` | No WO existence check before `get_doc()` | 15 min |
| M4 | `reports/pick_list.py` | N+1 query in report | 1 hr |
| M5 | `overrides/production_plan.py` | Stringified date as dict key | 15 min |
| M6 | `security/security_utils.py` | Returns False instead of raising | 15 min |
| R-001 | `material_readiness.py` | Module approaching 1000 lines — split | 3 hrs |
| S-001 | `stock_service.py` | Module ~700 lines — split services | 2 hrs |
| E-002 | `execution_engine.py` | Review runtime `frappe.db.commit()` | 30 min |

### LOW
| ID | File | Issue | Effort |
|----|------|-------|--------|
| L1 | Multiple | Unused imports (~10 files) | 30 min |
| L2 | `diagnostics/messages.py` | Unicode emojis in strings | 10 min |
| L3 | `diagnostics/exception_handler.py` | Convenience functions never called | 15 min |
| L4 | `material_readiness.py` | Unused `datetime` import | 5 min |
| L5 | `mes/dataclasses.py` | Dead `HOLD` constant | 5 min |

---

## Phase 1.1 — Planning (v15.1.x)

### HIGH
| ID | File | Issue | Effort |
|----|------|-------|--------|
| C1 | Multiple | Triple UI duplication (PP button + desk page + web page) | 3 hrs |
| H3 | `planning/material_planning_service.py` | Hardcoded warehouse substring match | 1 hr |
| H4 | `planning/material_planning_service.py` | `_needs_whole_qty()` — dead code | 5 min |

### MEDIUM
| ID | File | Issue | Effort |
|----|------|-------|--------|
| M7 | `planning/material_planning_service.py` | Raw SQL bypasses ORM for duplicate MR check | 1 hr |
| M8 | `planning/material_planning_service.py` | N+1 queries in generation loop | 2 hrs |
| M9 | Page JS files | No `.fail()` error handlers on `frappe.call()` | 1 hr |
| M10 | `hooks.py` | `production_plan_mr.js` loads globally via `app_include_js` | 15 min |
| M11 | `patches.txt` | Orphan patch `setup_pick_list_report.py` not registered | 5 min |
| S-003 | `planning/material_planning_service.py` | Split into focused functions | 2 hrs |

### LOW
| ID | File | Issue | Effort |
|----|------|-------|--------|
| L6 | `planning/material_planning_service.py` | `Optional` import unused | 5 min |
| L7 | `planning/material_planning_service.py` | Redundant `target_wh` assignment | 5 min |
| L8 | Page JS | Date uses browser timezone not server timezone | 15 min |
| L9 | Page JS | Inline HTML string — move to template | 15 min |
| L10 | `patches/create_pp_mr_link.py` | `print()` instead of logging | 5 min |
| L11 | `batch_planning.py` | `_uom_must_be_whole_number()` makes 2 queries per call | 30 min |

---

## Summary

| Phase | HIGH | MEDIUM | LOW | Total |
|-------|------|--------|-----|-------|
| Phase 1 (v15.0.x) | 1 | 8 | 5 | **14** |
| Phase 1.1 (v15.1.x) | 3 | 6 | 5 | **14** |
| **Total** | **4** | **14** | **10** | **28** |

### Already Fixed in v15.1.2
- ✅ `frappe.db.commit()` removed from API + Services (4 calls)
- ✅ JS dead code removed + `setInterval()` memory leak fixed
- ✅ JS merge-safe listview override

### Estimated Effort for v15.2.0
- HIGH: ~5 hours
- MEDIUM: ~14 hours  
- LOW: ~4 hours
- **Total: ~23 hours**
