# Pending Fixes — Phase 1 & Phase 1.1

**Date:** Sep 12, 2026
**Version:** v15.1.26
**Status:** HIGH items resolved

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

## Phase 1.1 — Planning (v15.1.x) — 4 remaining

### MEDIUM (2)
| ID | File | Issue |
|----|------|-------|
| M10 | `material_planning_service.py:96` | Raw SQL for duplicate MR check |
| M11 | `material_planning_service.py:47` | N+1 queries in generation loop |

### LOW (2)
| ID | File | Issue |
|----|------|-------|
| L7 | Page JS | Browser timezone date |
| L8 | Page JS | Inline HTML |

---

## Resolved This Session

| ID | Issue | Fixed In |
|----|-------|----------|
| ~~M12~~ | Page JS no `.fail()` on `frappe.call()` | v15.1.26 |
| ~~M13~~ | `production_plan_mr.js` loads globally | v15.1.26 |
| ~~NEW~~ | MR qty double-counting | v15.1.25 |
| ~~NEW~~ | Source warehouse exact match | v15.1.26 |

---

## Summary

| Phase | HIGH | MEDIUM | LOW | Total |
|-------|------|--------|-----|-------|
| Phase 1 (v15.0.x) | 0 | 8 | 3 | **11** |
| Phase 1.1 (v15.1.x) | 0 | 2 | 2 | **4** |
| **Total** | **0** | **10** | **5** | **15** |

### Already Fixed
- ✅ v15.1.2: 4 × `frappe.db.commit()` + JS hardening
- ✅ v15.1.25: MR qty double-counting (wo_bom_nos filter)
- ✅ v15.1.26: Source warehouse contains match fix
