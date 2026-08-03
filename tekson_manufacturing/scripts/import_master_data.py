"""
Import Master Data to Local VM

Imports all master data exported from VPS:
- Departments
- Warehouses (Teksons structure)
- Workstations (with warehouse assignments)
- Items (R215, R216, R217 and all components)
- Operations
- BOMs (multi-level)
- BOM Items
- BOM Operations
- Opening Stock

Usage:
    bench --site [site-name] execute tekson_manufacturing.scripts.import_master_data.import_master_data --args '"/path/to/mes_master_data"'

Note: Run this on your LOCAL VM after copying exported data from VPS
"""

import frappe
import json
from pathlib import Path
from datetime import datetime


def import_master_data(import_dir):
    """Import master data to local VM"""
    
    print("=" * 80)
    print("IMPORTING MASTER DATA TO LOCAL VM")
    print("=" * 80)
    print(f"Started: {datetime.now()}")
    print(f"Import directory: {import_dir}")
    
    import_dir = Path(import_dir)
    
    if not import_dir.exists():
        print(f"❌ Import directory not found: {import_dir}")
        return
    
    import_count = {}
    error_count = 0
    
    # 1. Import Departments
    print("\n1. Importing Departments...")
    try:
        with open(import_dir / 'departments.json') as f:
            departments = json.load(f)
        
        for dept in departments:
            if not frappe.db.exists('Department', dept.get('department_name')):
                d = frappe.get_doc({
                    'doctype': 'Department',
                    'department_name': dept['department_name'],
                    'company': 'Teksons'
                })
                d.insert(ignore_permissions=True)
                print(f"  ✅ Created Department: {dept['department_name']}")
                import_count['departments'] = import_count.get('departments', 0) + 1
        
        if not departments:
            print(f"  ⚠️ No departments to import")
    except Exception as e:
        print(f"  ❌ Department import error: {str(e)}")
        error_count += 1
    
    # 2. Import Warehouses
    print("\n2. Importing Warehouses...")
    try:
        with open(import_dir / 'warehouses.json') as f:
            warehouses = json.load(f)
        
        # First create warehouse groups (is_group = 1)
        for wh in warehouses:
            if wh.get('is_group'):
                if not frappe.db.exists('Warehouse', wh['warehouse_name']):
                    w = frappe.get_doc({
                        'doctype': 'Warehouse',
                        'warehouse_name': wh['warehouse_name'],
                        'is_group': 1,
                        'company': 'Teksons'
                    })
                    w.insert(ignore_permissions=True)
                    print(f"  ✅ Created Warehouse Group: {wh['warehouse_name']}")
                    import_count['warehouses'] = import_count.get('warehouses', 0) + 1
        
        # Then create child warehouses
        for wh in warehouses:
            if not wh.get('is_group'):
                if not frappe.db.exists('Warehouse', wh['warehouse_name']):
                    w = frappe.get_doc({
                        'doctype': 'Warehouse',
                        'warehouse_name': wh['warehouse_name'],
                        'warehouse_group': wh.get('warehouse_group'),
                        'parent_warehouse': wh.get('parent_warehouse'),
                        'company': 'Teksons',
                        'is_group': 0
                    })
                    w.insert(ignore_permissions=True)
                    print(f"  ✅ Created Warehouse: {wh['warehouse_name']}")
                    import_count['warehouses'] = import_count.get('warehouses', 0) + 1
        
        if not warehouses:
            print(f"  ⚠️ No warehouses to import")
    except Exception as e:
        print(f"  ❌ Warehouse import error: {str(e)}")
        error_count += 1
    
    # 3. Import Items
    print("\n3. Importing Items...")
    try:
        with open(import_dir / 'items.json') as f:
            items = json.load(f)
        
        for item in items:
            if not frappe.db.exists('Item', item['item_code']):
                i = frappe.get_doc({
                    'doctype': 'Item',
                    'item_code': item['item_code'],
                    'item_name': item.get('item_name', item['item_code']),
                    'item_group': item.get('item_group', 'Products'),
                    'stock_uom': item.get('stock_uom', 'Nos'),
                    'is_stock_item': 1,
                    'is_manufactured_item': item.get('is_manufactured_item', 0),
                    'is_sub_contracted_item': item.get('is_sub_contracted_item', 0),
                    'default_warehouse': 'Raw Materials Stores',
                    'valuation_method': 'FIFO'
                })
                i.insert(ignore_permissions=True)
                print(f"  ✅ Created Item: {item['item_code']}")
                import_count['items'] = import_count.get('items', 0) + 1
        
        if not items:
            print(f"  ⚠️ No items to import")
    except Exception as e:
        print(f"  ❌ Item import error: {str(e)}")
        error_count += 1
    
    # 4. Import Operations
    print("\n4. Importing Operations...")
    try:
        with open(import_dir / 'operations.json') as f:
            operations = json.load(f)
        
        for op in operations:
            if not frappe.db.exists('Operation', op['operation']):
                o = frappe.get_doc({
                    'doctype': 'Operation',
                    'operation': op['operation'],
                    'workstation': op.get('workstation')
                })
                o.insert(ignore_permissions=True)
                print(f"  ✅ Created Operation: {op['operation']}")
                import_count['operations'] = import_count.get('operations', 0) + 1
        
        if not operations:
            print(f"  ⚠️ No operations to import")
    except Exception as e:
        print(f"  ❌ Operation import error: {str(e)}")
        error_count += 1
    
    # 5. Import Workstations (CRITICAL: with warehouse assignment)
    print("\n5. Importing Workstations...")
    try:
        with open(import_dir / 'workstations.json') as f:
            workstations = json.load(f)
        
        for ws in workstations:
            if not frappe.db.exists('Workstation', ws['workstation_name']):
                w = frappe.get_doc({
                    'doctype': 'Workstation',
                    'workstation_name': ws['workstation_name'],
                    'plant_floor': ws.get('plant_floor'),
                    'warehouse': ws.get('warehouse'),  # ⚠️ CRITICAL for material transfers
                    'hourly_rate': ws.get('hourly_rate', 0),
                    'company': 'Teksons'
                })
                w.insert(ignore_permissions=True)
                print(f"  ✅ Created Workstation: {ws['workstation_name']} (Warehouse: {ws.get('warehouse', 'NOT SET')})")
                import_count['workstations'] = import_count.get('workstations', 0) + 1
        
        if not workstations:
            print(f"  ⚠️ No workstations to import")
    except Exception as e:
        print(f"  ❌ Workstation import error: {str(e)}")
        error_count += 1
    
    # 6. Import BOMs
    print("\n6. Importing BOMs...")
    try:
        with open(import_dir / 'boms.json') as f:
            boms = json.load(f)
        
        with open(import_dir / 'bom_items.json') as f:
            bom_items = json.load(f)
        
        bom_operations_data = []
        if (import_dir / 'bom_operations.json').exists():
            with open(import_dir / 'bom_operations.json') as f:
                bom_operations_data = json.load(f)
        
        for bom in boms:
            if not frappe.db.exists('BOM', {'item': bom['item'], 'is_active': 1}):
                b = frappe.get_doc({
                    'doctype': 'BOM',
                    'item': bom['item'],
                    'quantity': bom.get('quantity', 1),
                    'uom': bom.get('uom', 'Nos'),
                    'company': 'Teksons',
                    'warehouse': bom.get('source_warehouse', 'Raw Materials Stores'),
                    'wip_warehouse': bom.get('wip_warehouse', 'WIP-W'),
                    'fg_warehouse': bom.get('fg_warehouse', 'Finished Goods'),
                    'is_active': 1,
                    'is_default': 1,
                    'currency': 'INR'
                })
                
                # Add BOM items
                items_for_this_bom = [bi for bi in bom_items if bi['parent'] == bom['name']]
                for bi in items_for_this_bom:
                    b.append('items', {
                        'item_code': bi['item_code'],
                        'qty': bi.get('qty', 1),
                        'uom': bi.get('uom', 'Nos'),
                        'rate': bi.get('rate', 0),
                        'amount': bi.get('qty', 1) * bi.get('rate', 0)
                    })
                
                # Add BOM operations
                operations_for_this_bom = [bo for bo in bom_operations_data if bo['parent'] == bom['name']]
                for bo in operations_for_this_bom:
                    b.append('operations', {
                        'operation': bo['operation'],
                        'workstation': bo.get('workstation'),
                        'description': bo.get('description'),
                        'workstation_type': bo.get('workstation_type'),
                        'hour_rate': bo.get('hour_rate', 0),
                        'time_in_mins': bo.get('time_in_mins', 0)
                    })
                
                b.insert(ignore_permissions=True)
                b.submit()  # Submit BOM
                print(f"  ✅ Created and Submitted BOM: {bom['item']}")
                import_count['boms'] = import_count.get('boms', 0) + 1
        
        if not boms:
            print(f"  ⚠️ No BOMs to import")
    except Exception as e:
        print(f"  ❌ BOM import error: {str(e)}")
        import traceback
        traceback.print_exc()
        error_count += 1
    
    # 7. Set Opening Stock
    print("\n7. Setting Opening Stock...")
    try:
        with open(import_dir / 'stock_levels.json') as f:
            stock_levels = json.load(f)
        
        if stock_levels:
            # Create Stock Entry for opening stock
            se = frappe.get_doc({
                'doctype': 'Stock Entry',
                'stock_entry_type': 'Opening Stock',
                'company': 'Teksons',
                'posting_date': frappe.utils.nowdate(),
                'set_posting_time': 1,
                'posting_time': '12:00:00'
            })
            
            for sl in stock_levels:
                # Verify item exists
                if frappe.db.exists('Item', sl['item_code']):
                    se.append('items', {
                        'item_code': sl['item_code'],
                        't_warehouse': sl['warehouse'],
                        'qty': sl['qty'],
                        'basic_rate': 1,  # Set appropriate rate
                        'amount': sl['qty'] * 1,
                        's_warehouse': None,  # Opening stock has no source
                        'transfer_qty': sl['qty'],
                        'conversion_factor': 1
                    })
            
            if se.items:
                se.insert(ignore_permissions=True)
                se.submit()
                print(f"  ✅ Created and Submitted Opening Stock Entry: {se.name}")
                print(f"      Total items: {len(se.items)}")
                import_count['opening_stock'] = len(se.items)
            else:
                print(f"  ⚠️ No valid items for opening stock")
        else:
            print(f"  ⚠️ No stock levels to import")
    except Exception as e:
        print(f"  ❌ Opening Stock import error: {str(e)}")
        import traceback
        traceback.print_exc()
        error_count += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("IMPORT COMPLETE")
    print("=" * 80)
    print(f"Completed: {datetime.now()}")
    print(f"Total records imported: {sum(import_count.values())}")
    print(f"Errors encountered: {error_count}")
    print("=" * 80)
    
    if error_count > 0:
        print("\n⚠️  WARNING: Some imports failed. Check errors above.")
        print("   You may need to fix issues before running validation.")
    else:
        print("\n✅ SUCCESS: All imports completed without errors!")
        print("   You can now run the validation script.")
    
    print("\nNext Steps:")
    print("  1. Verify master data:")
    print("     bench --site [site-name] execute tekson_manufacturing.tests.verify_master_data.verify_master_data")
    print("  2. Run integration validation:")
    print("     bench --site [site-name] execute tekson_manufacturing.tests.sprint_10_validation.run_validation")
    
    return import_count, error_count


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        import_master_data(sys.argv[1])
    else:
        print("Usage: bench execute tekson_manufacturing.scripts.import_master_data.import_master_data --args '/path/to/import/dir'")
