# Tekson MES — Project Status & Session Handoff

**Date:** 2026-09-12  
**Session:** MR Qty Bug Fix → v15.1.26 Release  
**Status:** ✅ **FIX RELEASED — READY FOR UAT**

---

## Current Version: v15.1.26

| Branch | Version | Status |
|--------|---------|--------|
| main | v15.1.26 | ✅ Released |
| develop | v15.1.26 | ✅ Merged |
| bom-bulk-creator | v15.1.26 | ✅ Merged |

---

## ✅ COMPLETED — This Session

### MR Qty Double-Counting Fix (v15.1.25)
- **Problem:** MR showed inflated quantities (74 kg instead of 5.736 kg)
- **Root Cause:** `_explode_bom` recursed into sub-assemblies with their own WOs
- **Fix:** Added `wo_bom_nos` parameter to skip recursion for WOs in the batch
- **Result:** Each leaf WO only requests its direct raw materials

### Source Warehouse Filter Fix (v15.1.26)
- **Problem:** MR only showed 3 items (70 MISSING)
- **Root Cause:** `_is_source_warehouse` used exact match, failed for "- TPL" suffix
- **Fix:** Contains match for warehouse names
- **Result:** All items pass source warehouse check

### Verified Correct Behavior
- MR correctly checks WIP stock (shortage = required - stock)
- Only items with actual shortage appear in MR
- Most materials already in WIP → only 5 items need requesting

---

## Deployment Status

### Dev Machine (karthic@teksons-development)
```
Branch: bom-bulk-creator
Version: v15.1.26
Status: ✅ Deployed and tested
Site: teksons.dev
```

### UAT Machine (cwd_admin@cwd)
```
Branch: main
Version: v15.1.26 (ready to pull)
Status: ⏳ Awaiting pull and customer testing
Site: tekson.site
```

### Local Development
```
Branch: main
Version: v15.1.26
Status: ✅ All branches synced
```

---

## UAT Pull Command

```bash
ssh cwd_admin@cwd
cd ~/cwd-bench/apps/tekson_manufacturing && git pull origin main
cd ~/cwd-bench && bench --site tekson.site migrate && bench build --app tekson_manufacturing
```

---

## Key Files Modified This Session

| File | Changes |
|------|---------|
| `planning/material_planning_service.py` | `_explode_bom()` wo_bom_nos, `_is_source_warehouse()` contains match |
| `tekson_manufacturing/__init__.py` | Version 15.1.26 |
| `pyproject.toml` | Version 15.1.26 |

---

## Test Data Reference

### Production Plan: PP/2609/37/0004
- **Total WOs:** 72
- **Unique BOMs:** 72
- **Leaf WOs (raw materials):** 57
- **Parent WOs (sub-assemblies):** 15

### Expected MR Quantities (after fix)
| Item | Expected | WIP Stock | Shortage |
|------|----------|-----------|----------|
| Aluminium Coil 0.2*110 | 5.736 | 7.554 | 0 (covered) |
| Ms Plate 22x22x3 | 12 | 0 | 12 |
| Ms Plate 22x22x2 | 12 | 0 | 12 |
| Aluminium Plate 110*5*2250MM | 1 | 0 | 1 |
| HEX Head Bolt M10 | 28 | ? | ? |

---

## Next Session Goals

1. Pull v15.1.26 on UAT
2. Customer UAT testing
3. Monitor for edge cases
4. Production go-live preparation
