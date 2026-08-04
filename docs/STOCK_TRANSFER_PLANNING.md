# Stock Transfer Planning Guide

**Date:** 2026-08-04  
**Status:** Ready for Execution  
**Phase:** Pre-UAT Stock Movement  

---

## Objective

Create opening stock in Raw Material/BOF Stores and execute department transfers to enable multi-department manufacturing testing.

---

## Stock Movement Flow

```
Step 1: Raw Material Receipt
   Raw Material Stores - TPL
   BOF Stores - TPL
         ↓ (Opening Stock Creation)
         
Step 2: Department Allocation
   WIP-W - TPL (Prep Dept)
   WIP-Ralu In - TPL (Inflation)
   WIP-Ralu Weld - TPL (Assembly)
         ↓ (Inter-department Transfers)
         
Step 3: Production Flow
   WIP-W → WIP-Ralu In → WIP-Ralu Weld
```

---

## Step 1: Create Opening Stock

### Option A: Minimal Stock (Recommended for Testing)

```bash
bench --site teksons.dev execute tekson_manufacturing.scripts.create_opening_stock.create_minimal_opening_stock --args '["Raw Material Stores - TPL"]'
```

**Result:** 10 units of each raw material component

### Option B: Scaled Stock

```bash
bench --site teksons.dev execute tekson_manufacturing.scripts.create_opening_stock.create_opening_stock --args '["Raw Material Stores - TPL", 100]'
```

**Result:** BOM qty × 100 units per item

### Option C: BOF Stores Stock

```bash
bench --site teksons.dev execute tekson_manufacturing.scripts.create_opening_stock.create_minimal_opening_stock --args '["BOF Stores - TPL"]'
```

---

## Step 2: Manual Department Transfers (For Testing)

### Transfer 1: Stores → WIP-W (Prep Department)

**Purpose:** Stock Core End Plate raw materials

**Stock Entry Type:** Material Transfer  
**From Warehouse:** Raw Material Stores - TPL  
**To Warehouse:** WIP-W - TPL  

**Items to Transfer:**
- Aluminium Coil (for Core End Plates)
- Other raw materials for WIP-W production

### Transfer 2: Stores → WIP-Ralu In (Inflation)

**Purpose:** Stock Fin, Spacer, Tube Sheet materials

**Stock Entry Type:** Material Transfer  
**From Warehouse:** Raw Material Stores - TPL  
**To Warehouse:** WIP-Ralu In - TPL  

### Transfer 3: WIP-W → WIP-Ralu In (Inter-department)

**Purpose:** Transfer Core End Plates to Inflation dept

**Stock Entry Type:** Material Transfer  
**From Warehouse:** WIP-W - TPL  
**To Warehouse:** WIP-Ralu In - TPL  
**Items:** Core End Plates (produced in WIP-W)

### Transfer 4: WIP-Ralu In → WIP-Ralu Weld (Inter-department)

**Purpose:** Transfer all sub-assemblies to Welding

**Stock Entry Type:** Material Transfer  
**From Warehouse:** WIP-Ralu In - TPL  
**To Warehouse:** WIP-Ralu Weld - TPL  
**Items:** Fins, Spacers, Tube Sheets, Core End Plates

---

## Step 3: Verify Stock Levels

### Check Raw Material Stores

```sql
SELECT item_code, actual_qty 
FROM `tabBin` 
WHERE warehouse = 'Raw Material Stores - TPL' 
AND actual_qty > 0
ORDER BY item_code;
```

### Check Department WIP

```sql
-- WIP-W Stock
SELECT item_code, actual_qty 
FROM `tabBin` 
WHERE warehouse = 'WIP-W - TPL' 
AND actual_qty > 0;

-- WIP-Ralu In Stock
SELECT item_code, actual_qty 
FROM `tabBin` 
WHERE warehouse = 'WIP-Ralu In - TPL' 
AND actual_qty > 0;

-- WIP-Ralu Weld Stock
SELECT item_code, actual_qty 
FROM `tabBin` 
WHERE warehouse = 'WIP-Ralu Weld - TPL' 
AND actual_qty > 0;
```

---

## Step 4: Create Test Work Order

### Test Case: R215 CAC Core

**Work Order Details:**
- **Item:** R215 CAC Core
- **Qty:** 1
- **BOM:** BOM-R215 CAC Core-001
- **WIP Warehouse:** WIP-Ralu Weld - TPL
- **Source Warehouse:** Raw Material Stores - TPL

**Expected Job Cards:**
1. **Job Card 1:** Core End Plate production (WIP-W)
2. **Job Card 2:** Fin/Spacer production (WIP-Ralu In)
3. **Job Card 3:** Core Assembly (WIP-Ralu Weld)

**Validation Points:**
- ✅ All 3 Job Cards created
- ✅ Job Card 1: Material ready (stock in WIP-W)
- ✅ Job Card 2: Waiting for Core End Plates transfer
- ✅ Job Card 3: Waiting for all parts from Ralu In
- ✅ Inter-department transfers update readiness
- ✅ Sequential completion possible

---

## Stock Entry Commands

### Create Stock Entry via Console

```python
import frappe
from datetime import datetime

# Create Material Transfer
stock_entry = frappe.new_doc('Stock Entry')
stock_entry.stock_entry_type = 'Material Transfer'
stock_entry.posting_date = datetime.now().strftime('%Y-%m-%d')
stock_entry.posting_time = datetime.now().strftime('%H:%M:%S')

# Add items
stock_entry.append('items', {
    'item_code': 'Aluminium Coil 0.2*110',
    'qty': 30.0,
    's_warehouse': 'Raw Material Stores - TPL',
    't_warehouse': 'WIP-W - TPL'
})

stock_entry.insert()
stock_entry.submit()
print(f"Stock Entry created: {stock_entry.name}")
```

### Verify Stock After Transfer

```python
import frappe

# Check stock in WIP-W
bins = frappe.get_all('Bin', 
    filters={'warehouse': 'WIP-W - TPL', 'actual_qty': ['>', 0]},
    fields=['item_code', 'actual_qty'])

for bin in bins:
    print(f"{bin.item_code}: {bin.actual_qty}")
```

---

## Transfer SOP (Standard Operating Procedure)

### Who Can Transfer?

- **Stores → Department:** Stores Keeper
- **Department → Department:** Production Supervisor

### When to Transfer?

1. **After Operation Completion:** Transfer produced parts immediately
2. **Batch Transfers:** End of shift/day batch transfers
3. **On Demand:** When downstream department requests

### Transfer Documentation

- **Stock Entry Name:** Record for tracking
- **Transfer Reason:** Note in "Remarks" field
- **Quantity Verification:** Double-check before submit

### Error Handling

- **Wrong Warehouse:** Cancel and reverse transfer
- **Wrong Quantity:** Adjust with additional transfer
- **Missing Item:** Verify production completion first

---

## Checklist

### Before Starting

- [ ] Opening stock script ready
- [ ] Test items identified
- [ ] Warehouse codes verified
- [ ] User permissions checked

### During Execution

- [ ] Opening stock created in Raw Material Stores
- [ ] Opening stock created in BOF Stores (if needed)
- [ ] Transfer 1: Stores → WIP-W completed
- [ ] Transfer 2: Stores → WIP-Ralu In completed
- [ ] Stock levels verified in each warehouse
- [ ] Transfer 3: WIP-W → WIP-Ralu In completed
- [ ] Transfer 4: WIP-Ralu In → WIP-Ralu Weld completed

### After Completion

- [ ] All WIP warehouses have stock
- [ ] Stock balances verified
- [ ] Test Work Order created
- [ ] Job Cards show correct material status
- [ ] Inter-department flow validated

---

## Troubleshooting

### Issue: "Warehouse not found"

**Solution:** Verify warehouse name exactly matches (including hyphen vs en-dash)

### Issue: "Insufficient stock"

**Solution:** Check source warehouse has adequate quantity before transfer

### Issue: "Permission denied"

**Solution:** Verify user has Stock Entry create/submit permissions

### Issue: "Item not allowed in warehouse"

**Solution:** Check item has correct default warehouse settings

---

## Next Steps After Stock Transfer

1. ✅ Create test Work Order
2. ✅ Verify Job Card creation
3. ✅ Test material readiness checks
4. ✅ Execute Job Cards in sequence
5. ✅ Validate inter-department transfers
6. ✅ Complete FG receipt
7. ✅ Document UAT results

---

## References

- `MULTI_DEPARTMENT_BOM_FLOW_ANALYSIS.md` - Detailed flow analysis
- `PHASE1_IMPLEMENTATION_SUMMARY.md` - Warehouse structure
- `BUSINESS_PROCESS_FREEZE_v1.0.md` - Department WIP rules
- `create_opening_stock.py` - Stock creation script

---

**Ready to Execute:** YES  
**Approval Required:** Production Manager confirmation on quantities  
**Estimated Time:** 30-45 minutes for complete flow
