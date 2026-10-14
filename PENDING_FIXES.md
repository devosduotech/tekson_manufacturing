# Pending Fixes — Phase 1 & Phase 1.1

**Date:** Oct 12, 2026
**Version:** v15.1.31 (on `develop`, pending tag)
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

## Material Transfer Pick List Report — outstanding (v15.1.31 candidate)

Report now loads, filters render, open-WO filter applied. Remaining work:

### MEDIUM (3)
| ID | File | Issue |
|----|------|-------|
| P1 | `reports/material_transfer_pick_list/material_transfer_pick_list.py` | N+1 `Bin` lookups (2 per BOM Item) — batch into one query keyed by `(item_code, warehouse)` |
| P2 | `reports/material_transfer_pick_list/material_transfer_pick_list.py` | `get_columns()` returns 9 columns, report JSON declares 10 (`wip_warehouse` duplicates `target_warehouse`) — align them |
| P3 | `reports/material_transfer_pick_list/material_transfer_pick_list.py` | Rows with `balance_to_transfer = 0` are still listed — decide whether to hide or add a "Show fully transferred" filter |

### LOW (2)
| ID | File | Issue |
|----|------|-------|
| P4 | `reports/material_transfer_pick_list/material_transfer_pick_list.py` | Debug `frappe.logger()` calls left in from the UI investigation — move behind a debug flag or drop |
| P5 | `reports/material_transfer_pick_list/material_transfer_pick_list.js` | Hard-coded `2026-01-01` / `2026-12-31` defaults — switch to `frappe.datetime.add_months(today, -12)` / `today` so the report does not need editing next year |

---

## Release Preparation Checklist (v15.1.31)

- [x] Decide the version number and bump `pyproject.toml` + `tekson_manufacturing/__init__.py` (15.1.31)
- [ ] Land P1–P5 above (or explicitly defer them in the release notes)
- [ ] Apply the site repair snippet on **every** deployed site
      (`prepared_report = 0`, `disable_prepared_report_automation = 1`)
- [ ] Confirm `git pull` on each site is on `develop` or `main`, not a side branch
      (one server was left on `bom-bulk-creator`, `ahead 29`)
- [ ] Restore `tekson_manufacturing/public/js/material_request_rm_loss.js` —
      shows as deleted in one working tree and is referenced by
      `hooks.doctype_js["Material Request"]`
- [ ] Run `bench --site <site> migrate` and `bench build`
- [ ] Smoke-test on UAT: report filters render, 9 columns, row count matches
      open WOs only (Completed / Closed / Stopped / Cancelled excluded)
- [ ] Tag `v15.1.31` and create the GitHub release
- [ ] Sync `develop` → `main`

---

## Resolved This Session

| ID | Issue | Fixed In |
|----|-------|----------|
| ~~M12~~ | Page JS no `.fail()` on `frappe.call()` | v15.1.26 |
| ~~M13~~ | `production_plan_mr.js` loads globally | v15.1.26 |
| ~~NEW~~ | MR qty double-counting | v15.1.25 |
| ~~NEW~~ | Source warehouse exact match | v15.1.26 |
| ~~NEW~~ | BOM Bulk Creator bom_no links to Draft BOMs | v15.1.27 |
| ~~NEW~~ | Pick List report filter fields not rendered (JS at wrong path) | Unreleased |
| ~~NEW~~ | Pick List report "Nothing to show" (prepared-report flip) | Unreleased |
| ~~NEW~~ | Pick List report listed Completed / Closed / Cancelled WOs | Unreleased |

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
- ✅ v15.1.27: BOM Bulk Creator bom_no fix (child BOM links left blank)
