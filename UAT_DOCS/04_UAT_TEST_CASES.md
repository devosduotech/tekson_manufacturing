# Tekson MES — UAT Test Cases

**Version:** v15.0.1
**Date:** August 2026

---

## Test Environment Setup

Before executing test cases:
- [ ] App installed and migrated
- [ ] All 72 BOMs configured (Items: Source Warehouse + Operation, Operations: Workstation Type)
- [ ] Workstations configured with Plant Floor
- [ ] Opening stock created in Raw Material Stores and BOF Stores
- [ ] Test user accounts created (Planner, Stores, Supervisor, Operator)

---

## Day 1 — Core Production Flow

### TC-001: Standard Production (Single-Level BOM)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create WO for "OC Inlet & Outlet Block 101X66X30", Qty=5 | WO created, JCs auto-generated |
| 2 | Submit WO | JCs show `custom_readiness_status = "Blocked"` |
| 3 | Transfer raw materials to WIP-CNC (Aluminium) and WIP-Ralu Weld (Helicoil) | Stock available in WIP |
| 4 | Refresh JC-001 (Size Cutting) | Shows "Ready to Start", Can Start = 1 |
| 5 | Start JC-001 | JC starts, status = "Work In Progress" |
| 6 | Complete and Submit JC-001 | JC status = "Completed" |
| 7 | Check JC-002 (Helicoil Insert) | Shows "Ready to Start" |

**Pass Criteria:** ✅ JC-001 starts only after materials transferred. ✅ JC-002 becomes ready after JC-001 completes.

---

### TC-002: Material Shortage — Blocked at Start

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create WO, submit | JCs show "Blocked" |
| 2 | Do NOT transfer materials | |
| 3 | Attempt to Start JC-001 | **BLOCKED** with "Material Not Available" error |
| 4 | Error message lists all missing items with quantities | Clear, actionable message |

**Pass Criteria:** ✅ JC cannot start without materials in WIP.

---

### TC-003: Previous Operation Dependency

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | WO with 3 operations, all materials in WIP | |
| 2 | Attempt to Start JC-002 (skip JC-001) | **BLOCKED** with "Complete JC-001 first" error |
| 3 | Start and complete JC-001 | JC-001 completed |
| 4 | Attempt to Start JC-003 (skip JC-002) | **BLOCKED** with "Complete JC-002 first" |
| 5 | Start and complete JC-002 | JC-002 completed |
| 6 | Start JC-003 | JC-003 starts normally |

**Pass Criteria:** ✅ Operations must be completed in sequence.

---

## Day 2 — Advanced Flows

### TC-004: Multi-Level BOM — Child WO Dependency

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create Production Plan for R215 RAD Core (has 8 child components) | |
| 2 | Release WOs | All child WOs + parent WO created |
| 3 | Submit all WOs | |
| 4 | Attempt to Start parent JC-001 | **BLOCKED** — lists incomplete child WOs |
| 5 | Complete one child WO | Parent still blocked for remaining child WOs |
| 6 | Complete all child WOs | Parent JC-001 now shows "Ready to Start" |
| 7 | Complete parent WOs | Parent WO auto-completes |

**Pass Criteria:** ✅ Parent JC blocked until ALL child WOs are completed.

---

### TC-005: Auto Work Order Completion

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | WO with 2 operations, materials, child WOs complete | |
| 2 | Complete and submit JC-001 | JC-001 completed, JC-002 becomes ready |
| 3 | Complete and submit JC-002 | Wait 2-3 seconds, refresh page |
| 4 | Check WO status | WO status = "Completed" |
| 5 | Check Stock Entry | One Manufacture SE created for the WO |

**Pass Criteria:** ✅ WO auto-completes after last JC submitted. ✅ Only one SE created.

---

### TC-006: Batch Quantity Rounding

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create PP for R215 Combi Cooler, Qty=1 | |
| 2 | Check sub-assembly items | Tank End Plate 110×5×595 shows qty=1 (not 0.666) |
| 3 | Release WOs | All WOs have whole-number quantities |

**Pass Criteria:** ✅ No fractional Work Order quantities. ✅ Batch rounding applied automatically.

---

### TC-007: Multi-Department WIP

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | WO with JC-001 (CNC dept) and JC-002 (Weld dept) | |
| 2 | Transfer Aluminium to WIP-CNC | JC-001 becomes ready |
| 3 | Start and complete JC-001 | |
| 4 | JC-002 checks only WIP-Ralu Weld | Does NOT check WIP-CNC |
| 5 | Helicoil transferred to WIP-Ralu Weld | JC-002 becomes ready |

**Pass Criteria:** ✅ Each JC checks only its own department WIP warehouse.

---

### TC-008: Production Plan → End-to-End

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create PP for R215 Combi Cooler, Qty=1 | |
| 2 | Get Items → all sub-assemblies listed | |
| 3 | Submit PP → Release WOs | 70+ WOs created, all with correct WIP/FG warehouses |
| 4 | Submit each child WO first (bottom-up) | Child JCs start/complete without errors |
| 5 | Parent WOs start only after children complete | Dependency enforced |
| 6 | All parent WOs complete | Full manufacturing cycle executed |

**Pass Criteria:** ✅ Full multi-level BOM production cycle completes. ✅ No manual SE needed.

---

## UAT Sign-Off

| Test Case | Result | Tester | Date |
|-----------|--------|--------|------|
| TC-001 | ⬜ Pass / ⬜ Fail | | |
| TC-002 | ⬜ Pass / ⬜ Fail | | |
| TC-003 | ⬜ Pass / ⬜ Fail | | |
| TC-004 | ⬜ Pass / ⬜ Fail | | |
| TC-005 | ⬜ Pass / ⬜ Fail | | |
| TC-006 | ⬜ Pass / ⬜ Fail | | |
| TC-007 | ⬜ Pass / ⬜ Fail | | |
| TC-008 | ⬜ Pass / ⬜ Fail | | |

**Overall Result:** ⬜ Pass / ⬜ Fail

**Signed:** ________________________ **Date:** ________________
