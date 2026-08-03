# Implementation Quick Start Guide

**Status:** Documentation Complete ✅  
**Next Step:** Create Custom Fields  

---

## Quick Confirmation

### ❌ NOT Needed
- Client Script (we use whitelisted API)
- Server Script (we use proper Python hooks)
- Custom doctypes (using standard Job Card)

### ✅ Needed
- Custom Fields on Job Card (5 fields)
- Python module: `readiness/job_card_readiness.py`
- Hook registration in `hooks.py`
- API endpoint for Start button (already exists)

---

## Step 1: Create Custom Fields

### On VM Console:
```bash
bench --site teksons.dev console
```

### Paste Script:
Copy the script from `docs/scripts/create_job_card_readiness_fields.py`

### Expected Result:
```
✅ Created: 5 fields
  - custom_material_status (Select)
  - custom_readiness_status (Select)
  - custom_material_shortage_details (Text)
  - custom_dependency_last_updated (Datetime)
  - custom_blocked_by (Data)
```

### Clear Cache:
```bash
bench --site teksons.dev clear-cache
```

---

## Step 2: Implement Readiness Engine

**File:** `tekson_manufacturing/readiness/job_card_readiness.py`

**Key Methods:**
- `refresh_work_order(wo)` - Evaluate all JCs
- `refresh_job_card(jc)` - Evaluate single JC
- `refresh_downstream_job_cards(jc)` - Evaluate downstream only

**Code:** See `docs/JOB_CARD_READINESS_ENGINE.md` for full implementation

---

## Step 3: Register Hooks

**File:** `tekson_manufacturing/hooks.py`

**Add:**
```python
doc_events = {
    "Work Order": {
        "on_submit": "tekson_manufacturing.readiness.job_card_readiness.on_work_order_submit",
    },
    "Stock Entry": {
        "on_submit": "tekson_manufacturing.readiness.job_card_readiness.on_stock_entry_submit",
    },
    "Job Card": {
        "on_submit": "tekson_manufacturing.readiness.job_card_readiness.on_job_card_complete",
    },
}
```

---

## Step 4: Update Start Button (Optional)

**File:** `tekson_manufacturing/public/js/job_card_start.js`

**Update validation to use:**
```javascript
if (frm.doc.custom_readiness_status !== 'Ready to Start') {
    frappe.throw(__('Cannot start: {0}', [frm.doc.custom_blocked_by]));
}
```

---

## Step 5: Test

### Test Scenarios:
1. ✅ Create WO → Verify fields populated
2. ✅ Transfer material → Verify status updates
3. ✅ Complete operation → Verify downstream refresh
4. ✅ Click Start → Verify validation works

---

## Files to Create/Update

| File | Action | Priority |
|------|--------|----------|
| `readiness/job_card_readiness.py` | Create | High |
| `hooks.py` | Update | High |
| `public/js/job_card_start.js` | Update (optional) | Medium |
| Custom Fields | Create | High |

---

## Timeline

| Day | Task | Status |
|-----|------|--------|
| Day 1 | Create custom fields | ⏳ Pending |
| Day 2-3 | Implement Readiness Engine | ⏳ Pending |
| Day 4 | Register hooks & test | ⏳ Pending |
| Day 5 | Update Start button | ⏳ Pending |
| Day 6-7 | Full testing | ⏳ Pending |

---

## Success Criteria

- ✅ Fields created without errors
- ✅ WO Submit populates fields immediately
- ✅ Material Transfer refreshes status
- ✅ Start button shows correct validation
- ✅ Performance < 2 seconds for all operations

---

**Ready to proceed?** Run the field creation script now! 🎯
