# UAT Environment Preparation Checklist

**Date:** August 2, 2026  
**Environment:** Local VM  
**Purpose:** Prepare clean environment for Phase 1 MES UAT  

---

## Part 1: Pull Latest Code from GitHub

```bash
# Navigate to bench directory
cd ~/frappe-bench  # (or your bench path)

# Get latest code from develop branch
bench get-app https://github.com/devosduotech/tekson_manufacturing --branch develop

# Or if app already exists
cd apps/tekson_manufacturing
git pull origin develop

# Go back to bench
cd ~/frappe-bench
```

**Expected:** Latest commit `66192c0` or newer

---

## Part 2: Clean Transactional Data (Manual from UI)

### Step 2.1: Navigate to Each Doctype

Go to: **Home > Manufacturing > [Doctype]**

### Step 2.2: Delete in This Order

**⚠️ IMPORTANT:** Delete in this specific order to avoid dependency errors:

#### 1. Stock Entries
- **Path:** Home > Stock > Stock Entry
- **Filter:** Purpose = "Material Transfer for Manufacture" OR "Manufacture"
- **Action:** 
  - Select all submitted (docstatus = 1) → Cancel → Delete
  - Select all drafts (docstatus = 0) → Delete
- **Expected:** 0 Stock Entries remaining

#### 2. Job Cards
- **Path:** Home > Manufacturing > Job Card
- **Filter:** Status ≠ "Cancelled"
- **Action:**
  - Select all submitted → Cancel → Delete
  - Select all drafts → Delete
- **Expected:** 0 Job Cards remaining

#### 3. Work Orders
- **Path:** Home > Manufacturing > Work Order
- **Filter:** Status ≠ "Cancelled"
- **Action:**
  - Select all submitted → Cancel → Delete
  - Select all drafts → Delete
- **Expected:** 0 Work Orders remaining

#### 4. Production Plans
- **Path:** Home > Manufacturing > Production Plan
- **Filter:** Status ≠ "Cancelled"
- **Action:**
  - Select all submitted → Cancel → Delete
  - Select all drafts → Delete
- **Expected:** 0 Production Plans remaining

#### 5. Material Requests (Optional - if test data)
- **Path:** Home > Stock > Material Request
- **Filter:** Request Type = "Material Transfer for Manufacture" OR "Manufacture"
- **Action:**
  - Select all submitted → Cancel → Delete
  - Select all drafts → Delete
- **Expected:** 0 test Material Requests remaining

---

## Part 3: Verify Master Data (Should Remain Intact)

### Check These Counts:

| Doctype | Expected Count | Path |
|---------|----------------|------|
| **Items** | 1660 | Home > Stock > Item |
| **Workstations** | 132 | Home > Manufacturing > Workstation |
| **Warehouses** | 21 | Home > Stock > Warehouse |
| **BOMs (Active)** | 81 | Home > Manufacturing > BOM |

**If counts match:** ✅ Master data preserved  
**If counts don't match:** ⚠️ Investigate before proceeding

---

## Part 4: Restart Bench & Clear Cache

```bash
# Restart bench
bench restart

# Clear cache
bench --site [your-site-name] clear-cache

# Clear website cache
bench --site [your-site-name] clear-website-cache
```

---

## Part 5: Verify Hooks Are Active

### Manual Verification:

1. **Open a Work Order**
   - Create a new Work Order
   - Save it
   - Check if any messages appear (WO-003 safety net)

2. **Create a Job Card** (test)
   - Create a new Job Card manually
   - Check if:
     - `custom_item_code` auto-populates
     - `custom_actual_production_item` auto-populates
     - `workstation` auto-assigns (if BOM has operations)
     - `wip_warehouse` auto-assigns based on workstation

3. **Check hooks.py** (technical verification)
   ```bash
   cd apps/tekson_manufacturing
   cat tekson_manufacturing/hooks.py | grep -A 10 "doc_events"
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
           ...
       },
       "Work Order": {
           "before_save": "tekson_manufacturing.services.work_order_service.auto_create_manufacture_entry",
       },
       ...
   }
   ```

---

## Part 6: Verify Custom Fields

### Check on Job Card Form:

Open any Job Card (or create new test one) and verify these fields exist:

- [ ] `custom_item_code` (Link/Read)
- [ ] `custom_actual_production_item` (Float)
- [ ] `custom_start_status` (Select)
- [ ] `custom_dependency_check` (Check)
- [ ] `custom_material_available_for_operation` (Check)
- [ ] `custom_material_status_details` (Text)
- [ ] `custom_plant_floor` (Link)

**All fields visible:** ✅ Hooks and custom fields working  
**Fields missing:** ⚠️ Check custom field installation

---

## Part 7: Create Test Data (Optional)

### Create 1 Test Production Plan:

1. **Create Production Plan**
   - Item: Any finished good
   - Quantity: 10
   - Planned Start Date: Today

2. **Release Work Order**
   - Submit Production Plan
   - Click "Create Work Orders"

3. **Verify Work Order Created**
   - Check WIP warehouse assigned
   - Check Job Cards auto-created
   - Check custom fields populated

---

## Part 8: Final Verification

### Quick Smoke Test:

```
✅ Code updated from GitHub (develop branch)
✅ Bench restarted
✅ Cache cleared
✅ All transactional data cleaned
✅ Master data intact (1660 items, 132 workstations, 21 warehouses, 81 BOMs)
✅ Custom fields visible on Job Card
✅ Hooks appear to be working
✅ Test Work Order created successfully (optional)
```

**Status:** ✅ **READY FOR UAT**

---

## Troubleshooting

### Issue: Custom fields not visible

**Solution:**
```bash
bench --site [site-name] clear-cache
bench --site [site-name] migrate
bench restart
```

### Issue: Hooks not triggering

**Solution:**
1. Verify hooks.py syntax
2. Check app is installed: `bench --site [site-name] list-apps`
3. Reinstall app: `bench --site [site-name] install-app tekson_manufacturing`
4. Restart bench

### Issue: Master data counts don't match

**Solution:**
- Check if you're on the correct site
- Verify master data import was successful
- Check for filters in list view

---

## Next Steps After Preparation

1. **Internal Integration Testing** (Aug 5-7)
   - Execute 10 test scenarios
   - Log any defects
   - Fix critical issues

2. **Customer UAT** (Aug 8-22)
   - Customer executes tests
   - Daily defect triage
   - Status reporting

3. **Phase 1 Sign-off** (Aug 25-30)

---

**Checklist Version:** 1.0  
**Last Updated:** August 2, 2026  
**Owner:** QA Lead / IT Admin

---

**END OF CHECKLIST**
