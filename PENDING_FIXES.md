# Pending Fixes — Phase 1 & Phase 1.1

**Date:** Aug 10, 2026
**Version:** v15.2.0-dev
**Fixed in v15.2.0:** 4 HIGH + 2 MEDIUM + 2 LOW items

---

## Phase 1 — MES Execution (v15.0.x) — 11 remaining

### MEDIUM (8)
| ID | File | Issue |
|----|------|-------|
| M1 | `api/job_card_start.py` | No `frappe.db.exists()` before `get_doc()` |
| M2 | `diagnostics/messages.py:571` | Bare `except Exception` swallows errors |
| M3 | `diagnostics/messages.py:230` | No WO existence check before `get_doc()` |
| M4 | `reports/pick_list.py:149` | N+1 query in report loop |
| M5 | `overrides/production_plan.py:20` | Stringified date as tuple key |
| M6 | `security/security_utils.py:196` | Returns False instead of raising |
| M7 | `material_readiness.py` | Module ~1000 lines — split |
| M8 | `stock_service.py` | Module ~700 lines — split |

### LOW (3)
| ID | File | Issue |
|----|------|-------|
| L1 | Multiple | Unused imports |
| L2 | `diagnostics/messages.py` | Unicode emojis |
| L3 | `mes/dataclasses.py` | Dead `HOLD` constant |

---

## Phase 1.1 — Planning (v15.1.x) — 7 remaining

### MEDIUM (4)
| ID | File | Issue |
|----|------|-------|
| M10 | `material_planning_service.py:96` | Raw SQL for duplicate MR check |
| M11 | `material_planning_service.py:47` | N+1 queries in generation loop |
| M12 | Page JS | No `.fail()` on `frappe.call()` |
| M13 | `hooks.py` | `production_plan_mr.js` loads globally |

### LOW (3)
| ID | File | Issue |
|----|------|-------|
| L6 | `material_planning_service.py` | Redundant `target_wh` assignment |
| L7 | Page JS | Browser timezone date |
| L8 | Page JS | Inline HTML |

---

## Summary

| Phase | HIGH | MEDIUM | LOW | Total |
|-------|------|--------|-----|-------|
| Phase 1 (v15.0.x) | 0 | 8 | 3 | **11** |
| Phase 1.1 (v15.1.x) | 0 | 4 | 3 | **7** |
| **Total** | **0** | **12** | **6** | **18** |

### Already Fixed
- ✅ v15.1.2: 4 × `frappe.db.commit()` + JS hardening
- ✅ v15.2.0: H1-H4 (permission doc, warehouse match, UI consolidation, dead code)
