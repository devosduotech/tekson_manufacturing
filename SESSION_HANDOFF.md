# Session Handoff

**Date:** Sep 12, 2026
**Version:** v15.1.26
**Status:** MR Qty Bug Fixed — Ready for UAT Testing

---

## What Was Done This Session

### 1. MR Qty Double-Counting Fix (v15.1.25)
**Problem:** MR showed inflated quantities (e.g., Aluminium Coil 0.2*110 = 74 kg instead of expected 5.736 kg).

**Root Cause:** `_explode_bom` recursively expanded ALL sub-assemblies. When multiple WOs existed for the same PP (e.g., 72 WOs), raw materials were counted at every level of the BOM hierarchy — parent WO counted sub-assembly materials, child WO also counted the same materials.

**Fix:** Pass `wo_bom_nos` set (BOMs with their own WOs) to `_explode_bom`. When encountering a sub-assembly whose BOM is in that set, skip recursion — that WO will request its own materials.

**File:** `planning/material_planning_service.py` — `_explode_bom()`, `_get_raw_bom_items()`

### 2. Source Warehouse Contains Match Fix (v15.1.26)
**Problem:** After the qty fix, MR still only showed 3 items (70 MISSING). `_is_source_warehouse` checked for exact match `"Raw Material Stores"` but actual warehouse name was `"Raw Material Stores - TPL"`.

**Fix:** Changed `_is_source_warehouse` to use contains match: `"Raw Material Stores" in wh_name`. Also fixed `_get_default_source_warehouse` with contains fallback.

**File:** `planning/material_planning_service.py` — `_is_source_warehouse()`, `_get_default_source_warehouse()`

### 3. Confirmed Correct Behavior
**After both fixes:** MR correctly shows only items with actual shortage (required qty - WIP stock > 0). Most materials already available in WIP warehouses → only 5 items need requesting. This is expected and correct.

---

## Version History (This Session)

| Version | Branch | Changes |
|---------|--------|---------|
| v15.1.25 | bom-bulk-creator → main | MR qty double-counting fix |
| v15.1.26 | main → develop, bom-bulk-creator | Source warehouse contains match |

---

## Current State

### Branches
- `main` — v15.1.26 (latest release)
- `develop` — v15.1.26 (merged from main)
- `bom-bulk-creator` — v15.1.26 (merged from main)

### Instances
- **Dev** (karthic@teksons-development) — `bom-bulk-creator` branch, teksons.dev site
- **UAT** (cwd_admin@cwd) — `main` branch, tekson.site site
- **Local** — `main` branch (this machine)

---

## What's Next

### Immediate
- Pull v15.1.26 on UAT and test MR generation
- Customer UAT testing

### Future Considerations
- Consider making source warehouse names configurable (not hardcoded contains match)
- MR generation performance with large number of WOs (72+ WOs per PP)
- Consider adding MR preview before generation

---

## Key Debug Commands

### Check MR Expected vs Actual
```python
import frappe, math
from tekson_manufacturing.planning.material_planning_service import _explode_bom

pp = 'PP/2609/37/0004'
wos = frappe.get_all('Work Order', {'production_plan': pp, 'docstatus': 1, 'status': ['!=', 'Completed']},
    ['name', 'bom_no', 'qty', 'wip_warehouse'])
wo_bom_nos = {w.bom_no for w in wos if w.bom_no}

expected = {}
for wo in wos:
    if not wo.bom_no: continue
    for item in _explode_bom(wo.bom_no, wo_bom_nos=wo_bom_nos):
        key = item['item_code']
        expected[key] = expected.get(key, 0) + item['qty'] * wo.qty

for k, v in sorted(expected.items()):
    print(f'{k}: {v:.3f} -> ceil: {math.ceil(v)}')
```

### Check Source Warehouse
```python
from tekson_manufacturing.planning.material_planning_service import _is_source_warehouse
print(_is_source_warehouse("Raw Material Stores - TPL"))  # True
print(_is_source_warehouse("BOF Stores - TPL"))           # True
print(_is_source_warehouse("Some WIP Warehouse"))         # False
```

### Check WO BOMs in Set
```python
wos = frappe.get_all('Work Order', {'production_plan': 'PP/2609/37/0004', 'docstatus': 1}, ['bom_no'])
wo_bom_nos = {w.bom_no for w in wos}
print(f'WO BOMs: {len(wo_bom_nos)}')
```
