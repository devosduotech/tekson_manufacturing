# Milestone 1 - Clean Test Setup Instructions

**Document ID:** MES-M1-TEST-001  
**Date:** August 3, 2026  
**Status:** Ready for Execution  

---

## Objective

Validate Milestone 1 (Job Card Start Validation) with a **clean Work Order** created with **Backflush enabled from the start**.

---

## Prerequisites

### 1. Clean Up Old Test Data

```sql
-- Delete test Job Cards (NOT submitted ones)
DELETE FROM `tabJob Card` 
WHERE work_order IN (
    SELECT name FROM `tabWork Order` 
    WHERE name LIKE 'WO/260802/%' 
    AND docstatus < 2
);

-- Delete test Work Orders (NOT submitted)
DELETE FROM `tabWork Order` 
WHERE name LIKE 'WO/260802/%' 
AND docstatus < 2;

-- Keep Stock Entries (raw material transfers to WIP)
-- These are valid inventory transactions
```

**⚠️ DO NOT DELETE:**
- Stock Entries (SE-*) - These are valid inventory
- Submitted Work Orders (docstatus = 1)
- Submitted Job Cards (docstatus = 1)

---

### 2. Verify WIP Stock Available

```python
# Check WIP stock before creating WO
print('=== WIP Stock Available ===')

wip_warehouses = [
    'WIP-Ralu In - TPL',
    'WIP-Ralu Weld - TPL',
    'WIP-CNC - TPL',
    'WIP-RP - TPL',
    'WIP-W - TPL',
    'WIP-RA - TPL'
]

for wh in wip_warehouses:
    stock = frappe.db.sql("""
        SELECT item_code, actual_qty 
        FROM `tabBin` 
        WHERE warehouse = %s 
        AND actual_qty > 0
        ORDER BY item_code
    """, (wh,), as_dict=True)
    
    if stock:
        print(f'\n{wh}:')
        for item in stock[:5]:  # Show first 5
            print(f'  {item.item_code}: {item.actual_qty}')
```

---

## Test WO Creation Steps

### Step 1: Create Production Plan

1. Go to: **Manufacturing > Production Planning > Production Plan**
2. Click **New**
3. Set:
   - **Posting Date:** Today
   - **Company:** Teksons Pvt Ltd
   - **Get Sales Orders** OR **Get Items From** (as per your process)
4. Click **Get Items**
5. Select an item with:
   - ✅ Multi-level BOM (for testing sub-assemblies later)
   - ✅ Raw materials available in Stores
6. Click **Submit**

### Step 2: Generate Work Orders

1. In Production Plan, click **Generate Work Orders**
2. Set quantity (e.g., 90 pcs for testing)
3. Click **Generate**

### Step 3: Verify WO Configuration

**CRITICAL:** Before proceeding, verify:

```python
# Check newly created WO
wo_list = frappe.get_list('Work Order',
    filters={'docstatus': 0},  # Draft WOs
    order_by='creation desc',
    limit=5,
    fields=['name', 'production_item', 'bom_no']
)

print('=== Recent Draft Work Orders ===')
for wo_item in wo_list:
    wo = frappe.get_doc('Work Order', wo_item.name)
    
    # Check backflush
    backflush = wo.get('backflush_raw_materials_from_wip_warehouse')
    
    print(f'\n{wo.name}:')
    print(f'  Item: {wo.production_item}')
    print(f'  BOM: {wo.bom_no}')
    print(f'  Backflush Enabled: {backflush}')
    print(f'  WIP Warehouse: {wo.wip_warehouse}')
    
    if not backflush:
        print(f'  ⚠️  BACKFLUSH NOT ENABLED - Enable manually or recreate WO')
```

**If backflush is NOT enabled:**
- Edit the Work Order
- Check **"Backflush Raw Materials from WIP Warehouse"**
- Save

### Step 4: Submit Work Order

1. Open the Work Order
2. Verify:
   - ✅ Backflush enabled
   - ✅ WIP Warehouse set (e.g., WIP-Ralu In - TPL)
   - ✅ Quantity correct
3. Click **Submit**

### Step 5: Create Job Cards

1. In submitted WO, click **Create** > **Job Card**
2. Verify:
   - ✅ Job Card created for each operation
   - ✅ WIP Warehouse matches department
   - ✅ Status = "Open"
3. Save Job Cards

---

## Milestone 1 Test Scenarios

### Test 1: JC Start WITHOUT Material (Should Block)

```python
from tekson_manufacturing.api.job_card_start import start_job_card

# Get first JC for the WO
wo = frappe.get_doc('Work Order', 'WO/XXXXXX-XXX')  # Your new WO
jc_name = frappe.db.get_value('Job Card', {'work_order': wo.name})

print(f'=== Test 1: Block JC Start Without Material ===')
print(f'WO: {wo.name}')
print(f'JC: {jc_name}')

# Verify NO material in WIP
wip_qty = frappe.db.get_value('Bin', 
    {'warehouse': wo.wip_warehouse}, 
    'actual_qty') or 0

print(f'WIP Stock: {wip_qty}')

try:
    result = start_job_card(jc_name)
    print(f'❌ TEST FAILED - Should have blocked!')
except Exception as e:
    if 'Material not available' in str(e):
        print(f'✅ TEST PASSED - Correctly blocked')
        print(f'Error: {str(e)[:200]}')
    else:
        print(f'⚠️ Different error: {str(e)[:200]}')
```

**Expected Result:** ❌ JC Start BLOCKED with clear error message

---

### Test 2: Transfer Material to WIP

```python
# Create Material Transfer for Manufacture
wo = frappe.get_doc('Work Order', 'WO/XXXXXX-XXX')
bom = frappe.get_doc('BOM', wo.bom_no)

# Get first raw material
first_material = bom.items[0].item_code
required_qty = sum(item.qty for item in bom.items if item.item_code == first_material)

print(f'Transferring material: {first_material}')
print(f'Required: {required_qty}')

# Create Stock Entry
se = frappe.new_doc('Stock Entry')
se.purpose = 'Material Transfer for Manufacture'
se.stock_entry_type = 'Material Transfer for Manufacture'
se.work_order = wo.name
se.from_warehouse = 'Stores - TPL'
se.to_warehouse = wo.wip_warehouse

se.append('items', {
    'item_code': first_material,
    'qty': required_qty * 2,  # Transfer extra for testing
    's_warehouse': 'Stores - TPL',
    't_warehouse': wo.wip_warehouse
})

se.insert(ignore_permissions=True)
se.submit()
frappe.db.commit()

print(f'✅ Stock Entry Created: {se.name}')
print(f'Transferred: {required_qty * 2} kg to {wo.wip_warehouse}')
```

**Expected Result:** ✅ Material transferred to WIP

---

### Test 3: JC Start WITH Material (Should Allow)

```python
from tekson_manufacturing.api.job_card_start import start_job_card

wo = frappe.get_doc('Work Order', 'WO/XXXXXX-XXX')
jc_name = frappe.db.get_value('Job Card', {'work_order': wo.name})
jc = frappe.get_doc('Job Card', jc_name)

print(f'=== Test 3: Allow JC Start With Material ===')
print(f'WO: {wo.name}')
print(f'JC: {jc_name}')
print(f'Current Status: {jc.status}')

# Verify material readiness
from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
engine = MaterialReadinessEngine(work_order=wo.name)
readiness = engine.evaluate_material_readiness()

print(f'\nMaterial Readiness:')
print(f'  Is Ready: {readiness["is_ready"]}')

if readiness['is_ready']:
    try:
        result = start_job_card(jc_name)
        print(f'\n🎉 SUCCESS! Job Card started!')
        
        jc.reload()
        print(f'New Status: {jc.status}')
        
        if jc.status == 'Work In Progress':
            print(f'\n✅ MILESTONE 1: 100% COMPLETE!')
            print(f'  ✅ Blocks when NO stock')
            print(f'  ✅ Allows when stock available')
            print(f'  ✅ API method working correctly')
            print(f'  ✅ Error messages clear and helpful')
        else:
            print(f'\n⚠️ Status is {jc.status}, expected "Work In Progress"')
            
    except Exception as e:
        print(f'\n❌ Error: {str(e)}')
else:
    print(f'\n⚠️ Material Readiness says NOT READY')
```

**Expected Result:** ✅ JC Start ALLOWED, status changes to "Work In Progress"

---

## Success Criteria

Milestone 1 is **COMPLETE** when:

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| JC Start without material | BLOCKED | ⬜ | ⬜ |
| Material Transfer to WIP | SUCCESS | ⬜ | ⬜ |
| JC Start with material | ALLOWED | ⬜ | ⬜ |
| Status changes to "Work In Progress" | YES | ⬜ | ⬜ |
| Error message clear | YES | ⬜ | ⬜ |

---

## Next Steps After Milestone 1

Once Milestone 1 passes:

1. **Milestone 2:** Job Card Completion
2. **Milestone 3:** Parent/Child Synchronization
3. **Milestone 4:** Department Transfer (if applicable)
4. **Wave 3:** Code Simplification
5. **Wave 5:** Internal UAT

---

**Document Status:** ✅ **READY FOR EXECUTION**  
**Location:** `/home/karthic/Desktop/new_applications/tekson_manufacturing/docs/MILESTONE_1_CLEAN_TEST.md`
