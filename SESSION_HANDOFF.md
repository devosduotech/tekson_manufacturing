# Session Handoff

**Date:** Sep 16, 2026
**Version:** v15.1.27
**Status:** BOM Bulk Creator bom_no Fix — Released & Verified

---

## What Was Done This Session

### 1. BOM Bulk Creator bom_no Fix (v15.1.27)
**Problem:** `bom.save()` threw `ValidationError: BOM BOM-TUBE SHEET 0.6X140X500-001 must be submitted`.

**Root Cause:** At line 396-400, the code populated `BOM Item.bom_no` from `bom_queue` for expandable items:
```python
if item.is_expandable and item.item_code in bom_queue:
    item_args["bom_no"] = bom_queue[item.item_code].bom_no
```
ERPNext's `validate_materials()` checks that any referenced BOM must be submitted. Since all bulk-created BOMs are Draft, this fails.

**Fix:** Replaced conditional assignment with unconditional blank:
```python
# Do not establish child BOM links during bulk creation.
# The queue tracks generated BOMs, but BOM Item.bom_no remains blank.
# Users manually establish the required sub-assembly links after review.
item_args["bom_no"] = ""
```

**File:** `tekson_manufacturing/doctype/bom_bulk_creator/bom_bulk_creator.py` — `create_bom()` method

**Key Design Decision:** `bom_queue[item_code].bom_no` is still tracked internally (for BOM name sequencing and duplicate detection) but is NOT used to populate the ERPNext `BOM Item.bom_no` field.

### 2. Cache/Version Persistence Issue
**Problem:** Dev VM showed v15.1.26 despite `__init__.py` containing v15.1.27 on disk.

**Root Cause:** Old Python worker processes held the old module in memory. `systemctl restart frappe-bench.target` alone didn't fully kill all processes.

**Fix:** `bench build --clear && bench restart` (or full `systemctl stop/start` cycle).

**Lesson:** Always run `bench build --clear` before restart when bumping versions. Verify with `bench version` after restart.

### 3. Git Remote Naming
**Observation:** Dev VM uses `upstream` as the remote name, not `origin`. This caused `git fetch origin` to fail on the dev VM.

**Fix:** Use `git fetch upstream && git reset --hard upstream/bom-bulk-creator` on the dev VM.

---

## Version History (This Session)

| Version | Branch | Changes |
|---------|--------|---------|
| v15.1.27 | develop, main, bom-bulk-creator | BOM Bulk Creator bom_no fix, docstrings updated |

---

## Current State

### Branches
- `main` — v15.1.27 (latest release)
- `develop` — v15.1.27 (merged from main)
- `bom-bulk-creator` — v15.1.27 (merged from main)

### Instances
- **Dev** (karthic@teksons-development) — `bom-bulk-creator` branch, teksons.dev site, remote: `upstream`
- **UAT** (cwd_admin@cwd) — `main` branch, tekson.site site, remote: `origin`
- **Local** — `main` branch (this machine)

---

## What's Next

### Immediate
- Customer UAT testing with v15.1.27
- Verify BOM Bulk Creator creates all child BOMs as independent Drafts
- User manually links child BOMs after review before submission

### Future Considerations
- Consider adding BOM submission workflow (auto-submit after link review)
- Consider batch submit for child BOMs
- MR generation performance with large number of WOs (72+ WOs per PP)

---

## Key Debug Commands

### Verify BOM Item.bom_no is Blank After Bulk Creation
```python
import frappe
bom = frappe.get_doc("BOM", "BOM-JCB VM 116 RAD CORE 500X309X140-001")
for item in bom.items:
    print(f"{item.item_code}: bom_no='{item.bom_no}'")
```

### Check BOM Queue Tracking (Internal Only)
```python
# bom_queue tracks BOM names internally but does NOT populate BOM Item.bom_no
# This is expected and correct
```

### Force Cache Clear After Version Bump
```bash
bench build --clear
bench --site <site-name> migrate
bench restart
bench version  # verify version
```
