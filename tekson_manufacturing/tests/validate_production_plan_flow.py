"""
Production Plan to Job Card Flow Validation

Tests the complete flow from Production Plan → Work Order → Job Cards

Usage:
    bench --site [site] execute tekson_manufacturing.tests.validate_production_plan_flow.run_validation
"""

import frappe
from frappe import _
from datetime import datetime


def run_validation(item_code=None, qty=5):
    """
    Validate Production Plan to Job Card flow
    
    Args:
        item_code: Item to test (default: R215 Combi Cooler)
        qty: Quantity to produce
    
    Returns: dict with validation results
    """
    print("=" * 80)
    print("PRODUCTION PLAN TO JOB CARD FLOW VALIDATION")
    print("=" * 80)
    print(f"Date: {datetime.now()}")
    print()
    
    # Default test item
    if not item_code:
        item_code = "R215 Combi Cooler"
    
    print(f"Test Item: {item_code}")
    print(f"Quantity: {qty}")
    print()
    
    results = {
        'success': True,
        'work_order': None,
        'job_cards': [],
        'issues': []
    }
    
    try:
        # Step 1: Check if BOM exists
        print("STEP 1: Checking BOM...")
        bom = frappe.db.get_value('BOM', 
            {'item': item_code, 'is_active': 1, 'docstatus': 1}, 
            'name')
        
        if not bom:
            print(f"  ❌ No active BOM found for {item_code}")
            results['success'] = False
            results['issues'].append(f"No BOM for {item_code}")
            return results
        
        print(f"  ✅ BOM Found: {bom}")
        print()
        
        # Step 2: Create Work Order
        print("STEP 2: Creating Work Order...")
        wo = frappe.get_doc({
            'doctype': 'Work Order',
            'production_item': item_code,
            'qty': qty,
            'bom_no': bom,
            'company': 'Teksons Pvt Ltd',
            'source_warehouse': 'Raw Material Stores - TPL',
            'wip_warehouse': None,  # Will be set from BOM operations
            'fg_warehouse': 'Finish Goods Stores - TPL',
            'planned_start_date': frappe.utils.today()
        })
        wo.insert()
        wo.submit()
        frappe.db.commit()
        
        print(f"  ✅ Work Order Created: {wo.name}")
        print(f"  Source Warehouse: {wo.source_warehouse}")
        print(f"  WIP Warehouse: {wo.wip_warehouse}")
        print(f"  FG Warehouse: {wo.fg_warehouse}")
        print()
        
        results['work_order'] = wo.name
        
        # Step 3: Verify Work Order warehouses
        print("STEP 3: Verifying Work Order Warehouses...")
        
        expected_source = 'Raw Material Stores - TPL'
        expected_fg = 'Finish Goods Stores - TPL'
        
        if wo.source_warehouse != expected_source:
            print(f"  ❌ Source Warehouse: Expected {expected_source}, Got {wo.source_warehouse}")
            results['issues'].append(f"Wrong source warehouse: {wo.source_warehouse}")
        else:
            print(f"  ✅ Source Warehouse: {wo.source_warehouse}")
        
        if wo.fg_warehouse != expected_fg:
            print(f"  ❌ FG Warehouse: Expected {expected_fg}, Got {wo.fg_warehouse}")
            results['issues'].append(f"Wrong FG warehouse: {wo.fg_warehouse}")
        else:
            print(f"  ✅ FG Warehouse: {wo.fg_warehouse}")
        
        if wo.wip_warehouse:
            if wo.wip_warehouse.startswith('WIP-') and wo.wip_warehouse.endswith(' - TPL'):
                print(f"  ✅ WIP Warehouse: {wo.wip_warehouse}")
            else:
                print(f"  ⚠️  WIP Warehouse format unusual: {wo.wip_warehouse}")
        else:
            print(f"  ⚠️  WIP Warehouse not set (will use first operation)")
        print()
        
        # Step 4: Check Job Cards
        print("STEP 4: Checking Job Cards...")
        jcs = frappe.get_all('Job Card',
            filters={'work_order': wo.name},
            fields=['name', 'operation', 'workstation', 'status', 'wip_warehouse', 'custom_plant_floor']
        )
        
        if not jcs:
            print(f"  ❌ No Job Cards created")
            results['issues'].append("No Job Cards created")
            results['success'] = False
        else:
            print(f"  ✅ {len(jcs)} Job Card(s) created")
            print()
            
            # Verify each Job Card
            for jc in jcs:
                results['job_cards'].append(jc.name)
                
                print(f"  {jc.name}:")
                print(f"    Operation: {jc.operation}")
                print(f"    Workstation: {jc.workstation or 'Not assigned'}")
                print(f"    Status: {jc.status}")
                print(f"    WIP Warehouse: {jc.wip_warehouse}")
                print(f"    Plant Floor: {jc.custom_plant_floor or 'Not set'}")
                
                # Verify warehouse matches workstation
                if jc.workstation and jc.wip_warehouse:
                    ws = frappe.get_doc('Workstation', jc.workstation)
                    expected_wh = f"WIP-{ws.plant_floor} - TPL" if ws.plant_floor else None
                    
                    if expected_wh and jc.wip_warehouse == expected_wh:
                        print(f"    ✅ Warehouse matches workstation plant_floor")
                    elif expected_wh:
                        print(f"    ❌ Warehouse mismatch: Expected {expected_wh}, Got {jc.wip_warehouse}")
                        results['issues'].append(f"JC {jc.name}: Wrong WIP warehouse")
        
        print()
        
        # Summary
        print("=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        
        if results['success'] and not results['issues']:
            print("✅ ALL CHECKS PASSED")
            print(f"   Work Order: {wo.name}")
            print(f"   Job Cards: {len(jcs)}")
        else:
            print("⚠️  ISSUES FOUND")
            for issue in results['issues']:
                print(f"   - {issue}")
        
        print("=" * 80)
        
        return results
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
        results['success'] = False
        results['issues'].append(str(e))
        return results


if __name__ == '__main__':
    run_validation()
