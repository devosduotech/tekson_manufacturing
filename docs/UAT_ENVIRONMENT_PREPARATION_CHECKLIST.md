# UAT Environment Preparation Checklist

**Date:** August 2, 2026  
**Environment:** Local VM (Development Mode)  
**Purpose:** Prepare environment for Phase 1 MES Internal Integration Testing  

---

## Testing Strategy

| Phase | Mode | Dates | Purpose |
|-------|------|-------|---------|
| **Internal Integration Testing** | Development | Aug 5-7 | Debug-friendly, detailed errors |
| **Customer UAT** | Production | Aug 8-22 | Realistic user experience |
| **Production Deployment** | Production | Post sign-off | Live environment |

**Current Phase:** Internal Integration Testing (Development Mode) ✅

---

## Part 1: Pull Latest Code from GitHub

```bash
# Navigate to bench directory
cd ~/frappe-bench  # (or your bench path)

# Navigate to app
cd apps/tekson_manufacturing

# Pull latest code from develop branch
git pull origin develop

# Verify latest commit
git log --oneline -1

# Expected: 413d099 or newer
```

**✅ Checkpoint:** Latest code pulled successfully

---

## Part 2: Ensure Development Mode is Active

```bash
# Navigate to bench
cd ~/frappe-bench

# Check developer mode
bench --site [site-name] console
```

```python
import frappe
print(frappe.conf.developer_mode)  # Should print: True or 1
```

**If not in development mode:**
```bash
bench set-config developer_mode 1
bench restart
```

**✅ Checkpoint:** Development mode confirmed

---

## Part 3: Clean Transactional Data (Manual from UI)

### Step 3.1: Navigate to Each Doctype

Go to: **Home > Manufacturing > [Doctype]** or use **List View**

### Step 3.2: Delete in This Order

**⚠️ IMPORTANT:** Delete in this specific order to avoid dependency errors:

#### 1. Stock Entries
- **Path:** Home > Stock > Stock Entry > List
- **Filter:** 
  - Purpose = "Material Transfer for Manufacture" OR "Manufacture"
  - OR docstatus = 1 (Submitted)
- **Action:** 
  - Select all submitted (docstatus = 1) → Actions → Cancel → Delete
  - Select all drafts (docstatus = 0) → Actions → Delete
- **Expected:** 0 Stock Entries remaining
- **✅ Checkpoint:** Stock Entries cleaned

#### 2. Job Cards
- **Path:** Home > Manufacturing > Job Card > List
- **Filter:** Status ≠ "Cancelled" OR docstatus = 1
- **Action:**
  - Select all submitted → Actions → Cancel → Delete
  - Select all drafts → Actions → Delete
- **Expected:** 0 Job Cards remaining
- **✅ Checkpoint:** Job Cards cleaned

#### 3. Work Orders
- **Path:** Home > Manufacturing > Work Order > List
- **Filter:** Status ≠ "Cancelled" OR docstatus = 1
- **Action:**
  - Select all submitted → Actions → Cancel → Delete
  - Select all drafts → Actions → Delete
- **Expected:** 0 Work Orders remaining
- **✅ Checkpoint:** Work Orders cleaned

#### 4. Production Plans
- **Path:** Home > Manufacturing > Production Plan > List
- **Filter:** Status ≠ "Cancelled" OR docstatus = 1
- **Action:**
  - Select all submitted → Actions → Cancel → Delete
  - Select all drafts → Actions → Delete
- **Expected:** 0 Production Plans remaining
- **✅ Checkpoint:** Production Plans cleaned

#### 5. Material Requests (Optional - if test data)
- **Path:** Home > Stock > Material Request > List
- **Filter:** Request Type = "Material Transfer for Manufacture"
- **Action:**
  - Select all submitted → Actions → Cancel → Delete
  - Select all drafts → Actions → Delete
- **Expected:** 0 test Material Requests remaining
- **✅ Checkpoint:** Material Requests cleaned

---

## Part 4: Verify Master Data (Should Remain Intact)

### Check These Counts:

| Doctype | Expected Count | Path | Status |
|---------|----------------|------|--------|
| **Items** | 1660 | Home > Stock > Item > List | ⬜ |
| **Workstations** | 132 | Home > Manufacturing > Workstation > List | ⬜ |
| **Warehouses** | 21 | Home > Stock > Warehouse > List | ⬜ |
| **BOMs (Active)** | 81 | Home > Manufacturing > BOM > List | ⬜ |

**Verification Command (optional):**
```bash
bench --site [site-name] console
```
```python
print(f"Items: {frappe.db.count('Item')}")
print(f"Workstations: {frappe.db.count('Workstation')}")
print(f"Warehouses: {frappe.db.count('Warehouse')}")
print(f"BOMs: {frappe.db.count('BOM', {'is_active': 1})}")
```

**✅ Checkpoint:** Master data counts match

---

## Part 5: Restart Bench & Clear Cache

```bash
# Navigate to bench
cd ~/frappe-bench

# Restart bench
bench restart

# Clear cache
bench --site [site-name] clear-cache

# Clear website cache
bench --site [site-name] clear-website-cache

# Reload browser (Ctrl+Shift+R or Cmd+Shift+R)
```

**✅ Checkpoint:** Bench restarted, cache cleared

---

## Part 6: Verify Hooks Are Active

### Test 1: Create Test Work Order

1. **Create Work Order:**
   - Go to: Home > Manufacturing > Work Order > New
   - Production Item: Any finished good
   - Qty: 10
   - Save

2. **Verify:**
   - No errors on save
   - Work Order created successfully

3. **Check Console for Hook Execution:**
   ```bash
   tail -f logs/*.log
   ```
   - Look for any errors related to `auto_create_manufacture_entry`

**✅ Checkpoint:** Work Order creation works

---

### Test 2: Create Test Job Card

1. **Create Job Card Manually:**
   - Go to: Home > Manufacturing > Job Card > New
   - Work Order: Select the WO created above
   - Operation: Select any operation
   - Save (don't submit yet)

2. **Verify Auto-Population:**
   - [ ] `custom_item_code` populated from WO
   - [ ] `custom_actual_production_item` populated
   - [ ] `workstation` auto-assigned (if BOM has operation)
   - [ ] `wip_warehouse` auto-assigned based on workstation
   - [ ] `custom_plant_floor` populated

3. **Check Console for Errors:**
   ```bash
   tail -f logs/*.log
   ```
   - Look for any hook execution errors

**✅ Checkpoint:** Job Card hooks working

---

### Test 3: Verify hooks.py Configuration

```bash
cd apps/tekson_manufacturing
cat tekson_manufacturing/hooks.py | grep -A 15 "doc_events"
```

**Expected output:**
```python
doc_events = {
    "Job Card": {
        "before_insert": [
            "tekson_manufacturing.utils.job_card_utils.populate_job_card_fields",
            "tekson_manufacturing.utils.job_card_utils.allocate_workstation",
        ],
        "validate": "tekson_manufacturing.utils.job_card_utils.set_wip_warehouse",
        "on_submit": "tekson_manufacturing.execution.execution_engine.on_job_card_submit",
        "on_cancel": "tekson_manufacturing.execution.execution_engine.on_job_card_cancel",
    },
    "Work Order": {
        "before_save": "tekson_manufacturing.services.work_order_service.auto_create_manufacture_entry",
    },
    "Stock Entry": {
        "on_submit": "tekson_manufacturing.execution.execution_engine.on_stock_entry_submit",
        "on_cancel": "tekson_manufacturing.execution.execution_engine.on_stock_entry_cancel",
    }
}
```

**✅ Checkpoint:** hooks.py configured correctly

---

## Part 7: Verify Custom Fields

### Check on Job Card Form:

Open the test Job Card created in Part 6 and verify:

- [ ] `custom_item_code` (Link/Read) - Visible
- [ ] `custom_actual_production_item` (Float) - Visible
- [ ] `custom_start_status` (Select) - Visible
- [ ] `custom_dependency_check` (Check) - Visible
- [ ] `custom_material_available_for_operation` (Check) - Visible
- [ ] `custom_material_status_details` (Text) - Visible
- [ ] `custom_plant_floor` (Link) - Visible

**All fields visible:** ✅ Custom fields installed correctly  
**Fields missing:** ⚠️ Run `bench migrate` and clear cache

---

## Part 8: Enable Scheduler (For Background Jobs)

```bash
# Enable scheduler
bench --site [site-name] enable-scheduler

# Verify scheduler status
bench --site [site-name] scheduler status
```

**Expected:** Scheduler enabled

**✅ Checkpoint:** Scheduler active

---

## Part 9: Final Verification

### Quick Smoke Test Checklist:

```
[✅] Code updated from GitHub (develop branch)
[✅] Development mode active
[✅] Bench restarted
[✅] Cache cleared
[✅] All transactional data cleaned
[✅] Master data intact (1660 items, 132 workstations, 21 warehouses, 81 BOMs)
[✅] Custom fields visible on Job Card
[✅] Hooks working (tested with WO and JC creation)
[✅] Scheduler enabled
[✅] No errors in logs
```

**Status:** ✅ **READY FOR INTERNAL INTEGRATION TESTING**

---

## Part 10: Document Test Results

### Test Execution Log:

| Test # | Scenario | Status | Defect ID | Notes |
|--------|----------|--------|-----------|-------|
| 1 | Workstation Auto-Assignment | ⬜ | | |
| 2 | Job Card WIP Assignment | ⬜ | | |
| 3 | Material Transfer Creation | ⬜ | | |
| 4 | Material Availability Check | ⬜ | | |
| 5 | Operation Sequence Validation | ⬜ | | |
| 6 | Job Card Start/Complete Flow | ⬜ | | |
| 7 | Auto-Manufacture on WO Complete | ⬜ | | |
| 8 | Multi-Department Flow | ⬜ | | |
| 9 | Stock Entry Submission | ⬜ | | |
| 10 | Production Plan to WO Flow | ⬜ | | |

**Defect Log Location:** `docs/UAT_DEFECT_LOG.md` (create if needed)

---

## Troubleshooting

### Issue: Custom fields not visible

**Solution:**
```bash
bench --site [site-name] migrate
bench --site [site-name] clear-cache
bench restart
```

Then reload browser (Ctrl+Shift+R)

---

### Issue: Hooks not triggering

**Solution:**
1. Verify hooks.py syntax (no indentation errors)
2. Check app is installed: `bench --site [site-name] list-apps`
3. Reinstall app: `bench --site [site-name] install-app tekson_manufacturing`
4. Restart bench: `bench restart`
5. Check logs: `tail -f logs/*.log`

---

### Issue: Master data counts don't match

**Solution:**
- Verify you're on the correct site
- Check if master data import was successful
- Look for filters in list view hiding data
- Run verification command in console

---

### Issue: Getting errors in logs

**Solution:**
1. Copy full error from logs
2. Check if it's a hook execution error
3. Verify all imports in Python files
4. Run `bench --site [site-name] migrate`
5. Restart bench
6. If persists, log as defect

---

## Next Steps After Preparation

### Internal Integration Testing (Aug 5-7)
1. Execute all 10 test scenarios
2. Log defects in defect tracker
3. Fix critical defects immediately
4. Retest fixes
5. Prepare UAT readiness report

### After Internal Testing
1. **If all tests pass:** Switch to production mode for Customer UAT
2. **If defects found:** Fix and retest in development mode
3. **Before Customer UAT:** Switch to production mode

---

## Production Mode Switch (Before Customer UAT)

**When:** After internal testing complete (Aug 7)

```bash
# Switch to production mode
bench set-config developer_mode 0

# Enable scheduler
bench --site [site-name] enable-scheduler

# Clear all caches
bench --site [site-name] clear-cache
bench --site [site-name] clear-website-cache

# Restart all services
supervisorctl restart all

# Verify
bench --site [site-name] console
>>> import frappe
>>> print(frappe.conf.developer_mode)  # Should be: False
```

**✅ Checkpoint:** Production mode ready for Customer UAT

---

**Checklist Version:** 1.1  
**Last Updated:** August 2, 2026  
**Owner:** QA Lead / IT Admin  
**Current Mode:** Development ✅

---

**END OF CHECKLIST**
