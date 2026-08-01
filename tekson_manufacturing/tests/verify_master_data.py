"""
Verify Master Data

Verifies that all required master data is properly set up before running integration tests.

Usage:
    bench --site [site-name] execute tekson_manufacturing.tests.verify_master_data.verify_master_data
"""

import frappe
from frappe import _


def verify_master_data():
    """Verify all master data is ready for integration testing"""
    
    print("=" * 80)
    print("MASTER DATA VERIFICATION")
    print("=" * 80)
    print(f"Started: {frappe.utils.now()}")
    
    verification_results = {
        'passed': 0,
        'failed': 0,
        'warnings': 0
    }
    
    # 1. Verify Warehouses
    print("\n1. Verifying Warehouses...")
    required_warehouses = [
        'Raw Materials Stores',
        'WIP-W', 'WIP-RA', 'WIP-RP', 'WIP-CNC',
        'WIP-Ralu Weld', 'WIP-Ralu In',
        'Finished Goods'
    ]
    
    for wh_name in required_warehouses:
        if frappe.db.exists('Warehouse', wh_name):
            print(f"  ✅ {wh_name}")
            verification_results['passed'] += 1
        else:
            print(f"  ❌ {wh_name} - MISSING!")
            verification_results['failed'] += 1
    
    # 2. Verify Departments
    print("\n2. Verifying Departments...")
    required_departments = ['W', 'RA', 'RP', 'CNC', 'Ralu Weld', 'Ralu In']
    
    for dept in required_departments:
        if frappe.db.exists('Department', {'department_name': dept}):
            print(f"  ✅ {dept}")
            verification_results['passed'] += 1
        else:
            print(f"  ❌ {dept} - MISSING!")
            verification_results['failed'] += 1
    
    # 3. Verify Workstations have warehouses assigned
    print("\n3. Verifying Workstations...")
    workstations = frappe.db.get_all('Workstation',
        filters={'department': ['in', required_departments]},
        fields=['name', 'warehouse', 'department'])
    
    if workstations:
        for ws in workstations[:10]:  # Show first 10
            if ws.warehouse:
                print(f"  ✅ {ws.name} → {ws.warehouse} ({ws.department})")
                verification_results['passed'] += 1
            else:
                print(f"  ❌ {ws.name} - NO WAREHOUSE ASSIGNED!")
                verification_results['failed'] += 1
        
        if len(workstations) > 10:
            print(f"  ... and {len(workstations) - 10} more workstations")
    else:
        print(f"  ❌ No workstations found!")
        verification_results['failed'] += 1
    
    # 4. Verify Items exist
    print("\n4. Verifying Items...")
    fg_items = ['R215', 'R216', 'R217']
    
    for item_prefix in fg_items:
        items = frappe.db.get_all('Item',
            filters={'item_code': ['like', f'{item_prefix}%']},
            limit=5)
        
        if items:
            print(f"  ✅ Found {len(items)} items matching {item_prefix}*")
            verification_results['passed'] += 1
        else:
            print(f"  ❌ No items found matching {item_prefix}*")
            verification_results['failed'] += 1
    
    # 5. Verify BOMs exist and are active
    print("\n5. Verifying BOMs...")
    for fg_item in fg_items:
        boms = frappe.db.get_all('BOM',
            filters={'item': ['like', f'{fg_item}%'], 'docstatus': 1, 'is_active': 1},
            limit=1)
        
        if boms:
            print(f"  ✅ BOM exists for {fg_item}*")
            verification_results['passed'] += 1
        else:
            print(f"  ❌ No active BOM found for {fg_item}*")
            verification_results['failed'] += 1
    
    # 6. Verify stock levels
    print("\n6. Verifying Stock Levels...")
    stock_items = frappe.db.sql("""
        SELECT COUNT(DISTINCT item_code) as item_count
        FROM `tabStock Ledger Entry`
        WHERE warehouse = 'Raw Materials Stores'
        AND actual_qty > 0
    """, as_dict=True)
    
    if stock_items and stock_items[0].item_count > 0:
        print(f"  ✅ Found {stock_items[0].item_count} items with stock in Raw Materials Stores")
        verification_results['passed'] += 1
    else:
        print(f"  ⚠️ No stock found in Raw Materials Stores")
        print(f"     You may need to create opening stock")
        verification_results['warnings'] += 1
    
    # 7. Verify Work Orders exist
    print("\n7. Verifying Work Orders...")
    wo_count = frappe.db.count('Work Order',
        filters={'production_item': ['like', '%R21%'], 'status': ['!=', 'Cancelled']})
    
    if wo_count > 0:
        print(f"  ✅ Found {wo_count} Work Orders for R21x items")
        verification_results['passed'] += 1
    else:
        print(f"  ⚠️ No Work Orders found for R21x items")
        print(f"     You may need to create test Work Orders")
        verification_results['warnings'] += 1
    
    # 8. Verify Job Cards exist
    print("\n8. Verifying Job Cards...")
    wo_names = frappe.db.sql("""
        SELECT name FROM `tabWork Order`
        WHERE production_item LIKE '%%R21%%'
        AND status != 'Cancelled'
    """, as_dict=True)
    
    if wo_names:
        jc_count = frappe.db.count('Job Card',
            filters={'work_order': ['in', [wo.name for wo in wo_names]]})
        
        if jc_count > 0:
            print(f"  ✅ Found {jc_count} Job Cards")
            verification_results['passed'] += 1
        else:
            print(f"  ⚠️ No Job Cards found for existing Work Orders")
            verification_results['warnings'] += 1
    else:
        print(f"  ⚠️ No Work Orders to check for Job Cards")
        verification_results['warnings'] += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"Passed: {verification_results['passed']}")
    print(f"Failed: {verification_results['failed']}")
    print(f"Warnings: {verification_results['warnings']}")
    print("=" * 80)
    
    if verification_results['failed'] > 0:
        print("\n❌ CRITICAL: Some required master data is missing!")
        print("   Please fix the failed items before running integration tests.")
        return False
    elif verification_results['warnings'] > 0:
        print("\n⚠️  WARNING: Some data is missing but tests may still run.")
        print("   Consider creating the missing data for complete testing.")
        return True
    else:
        print("\n✅ SUCCESS: All master data is ready for integration testing!")
        print("   You can now run the validation script.")
        return True


if __name__ == '__main__':
    verify_master_data()
