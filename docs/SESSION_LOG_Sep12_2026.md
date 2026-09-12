# Session Log — Sep 12, 2026

**Date:** Sep 12, 2026
**Duration:** ~3 hours
**Version:** v15.1.24 → v15.1.26
**Focus:** MR Qty Double-Counting Bug Fix

---

## Session Objectives

1. Investigate and fix doubled MR quantities for PP/2609/37/0004
2. Fix source warehouse filter that was dropping items
3. Release and deploy fixes to dev and UAT

---

## Discussion Summary

### Problem Identified
Customer reported MR quantities were inflated (e.g., Aluminium Coil 0.2*110 = 74 kg vs expected ~5.7 kg).

### Investigation Process

1. **Initial analysis:** Ran debug script to compute BOM explosion per WO. Found 72 WOs for PP/2609/37/0004.

2. **Root cause discovered:** `_explode_bom` recursed into ALL sub-assemblies, including those with their own WOs. For a 3-level hierarchy (Combi Cooler → OC → OC Core), raw materials were counted 3 times.

3. **First fix (v15.1.25):** Added `wo_bom_nos` parameter to `_explode_bom`. When a sub-assembly's BOM is in the set of WO BOMs, skip recursion.

4. **Second issue found:** After qty fix, MR still showed only 3 items (70 MISSING). Debug showed `skipped_source=0` but `skipped_shortage=88`.

5. **Root cause #2:** `_is_source_warehouse` checked exact match `"Raw Material Stores"` but warehouse name was `"Raw Material Stores - TPL"`.

6. **Second fix (v15.1.26):** Changed to contains match. Also fixed `_get_default_source_warehouse`.

7. **Final verification:** After both fixes, MR correctly shows only items with actual shortage (5 items). Most materials already in WIP.

---

## Technical Details

### BOM Hierarchy for PP/2609/37/0004
```
R215 Combi Cooler (WO/260912/0001)
├── R215 OC (WO/260912/0034) → R215 OC Core → Raw Materials
├── R215 RAD (WO/260912/0051) → R215 RAD Core → Raw Materials
├── R215 CAC (WO/260912/0002) → R215 CAC Core → Raw Materials
├── R215 Fan Cowl (WO/260912/0030) → Raw Materials
├── R215 Top/Bottom Flyscreen assemblies → Raw Materials
└── Direct raw materials (bolts, foam, stickers, etc.)
```

Total: 72 WOs, 72 unique BOMs, 57 leaf WOs contributing raw materials.

### Key Data Points
- Before fix: Aluminium Coil 0.2*110 = 74 kg (doubled)
- After fix: Aluminium Coil 0.2*110 = 5.736 kg (correct)
- WIP stock: Aluminium Coil 0.2*110 = 7.554 kg (already covers requirement)
- Final MR: Only 5 items with actual shortage

### Files Modified
- `tekson_manufacturing/planning/material_planning_service.py`
  - `_explode_bom()` — added `wo_bom_nos` parameter
  - `_get_raw_bom_items()` — passes `wo_bom_nos`
  - `generate_daily_material_requests()` — builds `wo_bom_nos` set
  - `_is_source_warehouse()` — contains match
  - `_get_default_source_warehouse()` — contains fallback

---

## Deployment History

| Action | Branch | Version | Date |
|--------|--------|---------|------|
| Commit qty fix | bom-bulk-creator | v15.1.25 | Sep 12 |
| Merge to main | main | v15.1.25 | Sep 12 |
| Commit src wh fix | main | v15.1.26 | Sep 12 |
| Merge to bom-bulk-creator | bom-bulk-creator | v15.1.26 | Sep 12 |
| Merge to develop | develop | v15.1.26 | Sep 12 |
| Push all branches | origin | v15.1.26 | Sep 12 |

---

## Issues Encountered

1. **Git merge conflicts** in `__init__.py` and `pyproject.toml` — resolved by keeping v15.1.26
2. **Dev machine remote** is `upstream` (not `origin`) — had to push to `bom-bulk-creator` branch for dev to pull
3. **`bench execute` syntax** — multi-line strings don't work; used `bench console` instead
4. **Module not installed error** — `bench execute` with file path fails; need dotted method path

---

## Testing Results

### Debug Script Output (Expected vs MR)
```
Item                           Expected    MR Qty    Match
-----------------------------------------------------------
Aluminium Coil 0.2*110              6         0    MISSING (before fix)
Aluminium Coil 0.2*110              6         6    YES (after fix, if shortage)
Ms Plate 22(L)x22(W)x3(T)         12        12    YES
Ms Plate 22(L)x22(W)x2(T)         12        12    YES
Aluminium Plate 110*5*2250MM        1         1    YES
```

### Verification Script
```python
from tekson_manufacturing.planning.material_planning_service import _is_source_warehouse
print(_is_source_warehouse("Raw Material Stores - TPL"))  # True ✓
print(_is_source_warehouse("BOF Stores - TPL"))           # True ✓
print(_is_source_warehouse("Some WIP Warehouse"))         # False ✓
```

---

## Lessons Learned

1. **BOM explosion must respect WO hierarchy** — if a sub-assembly has its own WO, don't count its materials in the parent WO
2. **Warehouse names often have suffixes** — use contains match instead of exact match
3. **Shortage calculation is correct** — MR should only request what's actually needed (required - stock > 0)
4. **Always test with real data** — synthetic test cases missed the hierarchy issue

---

## Next Session Tasks

1. Pull v15.1.26 on UAT and verify MR generation
2. Customer UAT testing
3. Monitor for any edge cases with different PP configurations
