# Tekson MES — Project Status & Session Handoff

**Date:** 2026-09-16
**Session:** BOM Bulk Creator bom_no Fix → v15.1.27 Release
**Status:** ✅ **FIX RELEASED — READY FOR UAT**

---

## Current Version: v15.1.27

| Branch | Version | Status |
|--------|---------|--------|
| main | v15.1.27 | ✅ Released |
| develop | v15.1.27 | ✅ Merged |
| bom-bulk-creator | v15.1.27 | ✅ Merged |

---

## ✅ COMPLETED — This Session

### BOM Bulk Creator bom_no Fix (v15.1.27)
- **Problem:** `bom.save()` threw `ValidationError: BOM BOM-xxx must be submitted`
- **Root Cause:** Code populated `BOM Item.bom_no` from `bom_queue` for expandable items. ERPNext validates that any referenced BOM must be submitted — but all bulk-created BOMs are Draft.
- **Fix:** Replaced conditional `bom_no` assignment with unconditional `item_args["bom_no"] = ""`
- **Result:** All generated BOMs are independent Draft BOMs. Users manually link child BOMs after review.
- **File:** `tekson_manufacturing/doctype/bom_bulk_creator/bom_bulk_creator.py` — `create_bom()` method

### Cache/Version Persistence Fix
- **Problem:** Dev VM still showed v15.1.26 after git pull despite correct `__init__.py` on disk
- **Root Cause:** Old Python processes holding stale module in memory; `systemctl restart` alone didn't kill them
- **Fix:** `bench build --clear && bench restart` (or full `systemctl stop/start` cycle)
- **Note:** Always verify with `bench version` after deploy; if stale, run `bench build --clear` first

---

## Deployment Status

### Dev Machine (karthic@teksons-development)
```
Remote: upstream (not origin)
Branch: bom-bulk-creator
Version: v15.1.27
Status: ✅ Deployed and verified
Site: teksons.dev
```

### UAT Machine (cwd_admin@cwd)
```
Remote: origin
Branch: main
Version: v15.1.27
Status: ✅ Deployed and verified
Site: tekson.site
```

### Local Development
```
Remote: origin
Branch: main, develop, bom-bulk-creator
Version: v15.1.27
Status: ✅ All branches synced
```

---

## Deployment Commands

### Dev Machine
```bash
cd ~/frappe-bench/apps/tekson_manufacturing
git fetch upstream && git reset --hard upstream/bom-bulk-creator
cd ~/frappe-bench && bench --site teksons.dev migrate && bench build --clear && bench restart
```

### UAT Machine
```bash
cd ~/cwd-bench/apps/tekson_manufacturing
git pull origin main
cd ~/cwd-bench && bench --site tekson.site migrate && bench build --clear && bench restart
```

---

## Key Files Modified This Session

| File | Changes |
|------|---------|
| `tekson_manufacturing/doctype/bom_bulk_creator/bom_bulk_creator.py` | `bom_no` left blank, docstrings updated |
| `tekson_manufacturing/__init__.py` | Version 15.1.27 |
| `pyproject.toml` | Version 15.1.27 |

---

## Next Session Goals

1. Customer UAT testing with v15.1.27
2. Monitor BOM Bulk Creator with real production data
3. Verify child BOM manual linking workflow
4. Production go-live preparation
