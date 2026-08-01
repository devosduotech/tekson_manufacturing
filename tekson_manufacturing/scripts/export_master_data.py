"""
Export Master Data from VPS

Exports all master data required for local VM setup:
- Warehouses (Teksons structure)
- Workstations (with warehouse assignments)
- Items (R215, R216, R217 and all components)
- BOMs (multi-level)
- BOM Items
- Operations
- Departments
- Work Orders (for reference)
- Job Cards (for reference)
- Stock Levels (for opening stock)

Usage:
    bench --site [site-name] execute tekson_manufacturing.scripts.export_master_data.export_master_data

Output: /tmp/mes_master_data/
"""

import frappe
import json
import os
from datetime import datetime


def export_master_data():
    """Export all master data for local VM setup"""
    
    print("=" * 80)
    print("EXPORTING MASTER DATA FROM VPS")
    print("=" * 80)
    print(f"Started: {datetime.now()}")
    
    # Create export directory
    export_dir = "/tmp/mes_master_data"
    os.makedirs(export_dir, exist_ok=True)
    
    export_count = {}
    
    # 1. Export Warehouses
    print("\n1. Exporting Warehouses...")
    try:
        warehouses = frappe.get_all('Warehouse', 
            filters={
                'warehouse_name': ['in', [
                    'WIP-W', 'WIP-RA', 'WIP-RP', 'WIP-CNC', 
                    'WIP-Ralu Weld', 'WIP-Ralu In',
                    'Raw Materials Stores', 'BOF Stores',
                    'Incoming Quality Hold Stores', 'Incoming Quality Rejected Stores',
                    'Finished Goods', 'Rejected Stores', 'Scrap Stores'
                ]]
            },
            fields=['*'])
        
        # Also get warehouse groups
        warehouse_groups = frappe.get_all('Warehouse',
            filters={
                'warehouse_name': ['in', [
                    'Work In Progress Stores', 'Stores', 'Receipt and Dispatch Stores'
                ]]
            },
            fields=['*'])
        
        all_warehouses = warehouses + warehouse_groups
        
        with open(f"{export_dir}/warehouses.json", 'w') as f:
            json.dump(all_warehouses, f, indent=2, default=str)
        
        export_count['warehouses'] = len(all_warehouses)
        print(f"  ✅ Exported {len(all_warehouses)} warehouses")
    except Exception as e:
        print(f"  ❌ Warehouse export error: {str(e)}")
        export_count['warehouses'] = 0
    
    # 2. Export Workstations
    print("\n2. Exporting Workstations...")
    try:
        workstations = frappe.get_all('Workstation',
            filters={'plant_floor': ['in', ['W', 'RA', 'RP', 'CNC', 'Ralu Weld', 'Ralu In']]},
            fields=['*'])
        
        with open(f"{export_dir}/workstations.json", 'w') as f:
            json.dump(workstations, f, indent=2, default=str)
        
        export_count['workstations'] = len(workstations)
        print(f"  ✅ Exported {len(workstations)} workstations")
    except Exception as e:
        print(f"  ❌ Workstation export error: {str(e)}")
        export_count['workstations'] = 0
    
    # 3. Export Items (R215, R216, R217 and all BOM components)
    print("\n3. Exporting Items...")
    try:
        # Get FG items
        fg_items = frappe.get_all('Item',
            filters={'item_code': ['like', 'R21%']},
            fields=['*'])
        
        # Get all items used in BOMs for R21x
        bom_items_query = frappe.db.sql("""
            SELECT DISTINCT bi.item_code
            FROM `tabBOM Item` bi
            INNER JOIN `tabBOM` b ON bi.parent = b.name
            WHERE b.item LIKE '%%R21%%'
        """, as_dict=True)
        
        item_codes = [item.item_code for item in bom_items_query]
        
        # Get all those items
        all_items = fg_items + frappe.get_all('Item',
            filters={'item_code': ['in', item_codes]},
            fields=['*'])
        
        # Remove duplicates
        unique_items = {}
        for item in all_items:
            unique_items[item.item_code] = item
        
        items_list = list(unique_items.values())
        
        with open(f"{export_dir}/items.json", 'w') as f:
            json.dump(items_list, f, indent=2, default=str)
        
        export_count['items'] = len(items_list)
        print(f"  ✅ Exported {len(items_list)} items")
    except Exception as e:
        print(f"  ❌ Item export error: {str(e)}")
        export_count['items'] = 0
    
    # 4. Export BOMs
    print("\n4. Exporting BOMs...")
    try:
        boms = frappe.get_all('BOM',
            filters={'item': ['like', '%%R21%%'], 'docstatus': 1},
            fields=['*'])
        
        with open(f"{export_dir}/boms.json", 'w') as f:
            json.dump(boms, f, indent=2, default=str)
        
        export_count['boms'] = len(boms)
        print(f"  ✅ Exported {len(boms)} BOMs")
    except Exception as e:
        print(f"  ❌ BOM export error: {str(e)}")
        export_count['boms'] = 0
    
    # 5. Export BOM Items
    print("\n5. Exporting BOM Items...")
    try:
        if boms:
            bom_names = [bom.name for bom in boms]
            bom_items = frappe.get_all('BOM Item',
                filters={'parent': ['in', bom_names]},
                fields=['*'])
            
            with open(f"{export_dir}/bom_items.json", 'w') as f:
                json.dump(bom_items, f, indent=2, default=str)
            
            export_count['bom_items'] = len(bom_items)
            print(f"  ✅ Exported {len(bom_items)} BOM items")
        else:
            export_count['bom_items'] = 0
            print(f"  ⚠️ No BOMs found, skipping BOM items")
    except Exception as e:
        print(f"  ❌ BOM Item export error: {str(e)}")
        export_count['bom_items'] = 0
    
    # 6. Export BOM Operations
    print("\n6. Exporting BOM Operations...")
    try:
        if boms:
            bom_names = [bom.name for bom in boms]
            bom_operations = frappe.get_all('BOM Operation',
                filters={'parent': ['in', bom_names]},
                fields=['*'])
            
            with open(f"{export_dir}/bom_operations.json", 'w') as f:
                json.dump(bom_operations, f, indent=2, default=str)
            
            export_count['bom_operations'] = len(bom_operations)
            print(f"  ✅ Exported {len(bom_operations)} BOM operations")
        else:
            export_count['bom_operations'] = 0
            print(f"  ⚠️ No BOMs found, skipping BOM operations")
    except Exception as e:
        print(f"  ❌ BOM Operation export error: {str(e)}")
        export_count['bom_operations'] = 0
    
    # 7. Export Operations
    print("\n7. Exporting Operations...")
    try:
        if boms:
            bom_names = [bom.name for bom in boms]
            operation_names = frappe.db.sql("""
                SELECT DISTINCT operation
                FROM `tabBOM Operation`
                WHERE parent IN %s
            """, (bom_names,), as_dict=True)
            
            op_names = [op.operation for op in operation_names]
            
            operations = frappe.get_all('Operation',
                filters={'operation': ['in', op_names]},
                fields=['*'])
            
            with open(f"{export_dir}/operations.json", 'w') as f:
                json.dump(operations, f, indent=2, default=str)
            
            export_count['operations'] = len(operations)
            print(f"  ✅ Exported {len(operations)} operations")
        else:
            export_count['operations'] = 0
            print(f"  ⚠️ No BOMs found, skipping operations")
    except Exception as e:
        print(f"  ❌ Operation export error: {str(e)}")
        export_count['operations'] = 0
    
    # 8. Export Departments
    print("\n8. Exporting Departments...")
    try:
        departments = frappe.get_all('Department',
            filters={'department_name': ['in', ['W', 'RA', 'RP', 'CNC', 'Ralu Weld', 'Ralu In']]},
            fields=['*'])
        
        with open(f"{export_dir}/departments.json", 'w') as f:
            json.dump(departments, f, indent=2, default=str)
        
        export_count['departments'] = len(departments)
        print(f"  ✅ Exported {len(departments)} departments")
    except Exception as e:
        print(f"  ❌ Department export error: {str(e)}")
        export_count['departments'] = 0
    
    # 9. Export Work Orders (for reference)
    print("\n9. Exporting Work Orders...")
    try:
        work_orders = frappe.get_all('Work Order',
            filters={'production_item': ['like', '%%R21%%']},
            fields=['*'])
        
        with open(f"{export_dir}/work_orders.json", 'w') as f:
            json.dump(work_orders, f, indent=2, default=str)
        
        export_count['work_orders'] = len(work_orders)
        print(f"  ✅ Exported {len(work_orders)} work orders")
    except Exception as e:
        print(f"  ❌ Work Order export error: {str(e)}")
        export_count['work_orders'] = 0
    
    # 10. Export Job Cards (for reference)
    print("\n10. Exporting Job Cards...")
    try:
        if work_orders:
            wo_names = [wo.name for wo in work_orders]
            job_cards = frappe.get_all('Job Card',
                filters={'work_order': ['in', wo_names]},
                fields=['*'])
            
            with open(f"{export_dir}/job_cards.json", 'w') as f:
                json.dump(job_cards, f, indent=2, default=str)
            
            export_count['job_cards'] = len(job_cards)
            print(f"  ✅ Exported {len(job_cards)} job cards")
        else:
            export_count['job_cards'] = 0
            print(f"  ⚠️ No Work Orders found, skipping Job Cards")
    except Exception as e:
        print(f"  ❌ Job Card export error: {str(e)}")
        export_count['job_cards'] = 0
    
    # 11. Export Stock Levels (for opening stock)
    print("\n11. Exporting Stock Levels...")
    try:
        stock_levels = frappe.db.sql("""
            SELECT 
                item_code, 
                warehouse, 
                SUM(actual_qty) as qty
            FROM `tabStock Ledger Entry`
            WHERE warehouse IN (
                'Raw Materials Stores', 'BOF Stores',
                'WIP-W', 'WIP-RA', 'WIP-RP', 'WIP-CNC',
                'WIP-Ralu Weld', 'WIP-Ralu In'
            )
            GROUP BY item_code, warehouse
            HAVING qty > 0
        """, as_dict=True)
        
        with open(f"{export_dir}/stock_levels.json", 'w') as f:
            json.dump(stock_levels, f, indent=2, default=str)
        
        export_count['stock_levels'] = len(stock_levels)
        print(f"  ✅ Exported {len(stock_levels)} stock records")
    except Exception as e:
        print(f"  ❌ Stock Level export error: {str(e)}")
        export_count['stock_levels'] = 0
    
    # 12. Export README with instructions
    print("\n12. Creating README...")
    try:
        readme_content = f"""
MES Master Data Export
======================

Exported: {datetime.now()}
Source: VPS Production Data

Files Exported:
{chr(10).join([f"- {k}: {v} records" for k, v in export_count.items()])}

Total Records: {sum(export_count.values())}

Import Instructions:
====================

1. Copy this folder to your local VM:
   scp -r /tmp/mes_master_data user@local-vm:~/Desktop/

2. On local VM, run import script:
   bench --site [site-name] execute tekson_manufacturing.scripts.import_master_data.import_master_data --args '"~/Desktop/mes_master_data"'

3. Verify master data:
   bench --site [site-name] execute tekson_manufacturing.tests.verify_master_data.verify_master_data

4. Run integration validation:
   bench --site [site-name] execute tekson_manufacturing.tests.sprint_10_validation.run_validation

Note: This export contains read-only master data for setup purposes.
      Do not use for production data migration without proper validation.
"""
        
        with open(f"{export_dir}/README.txt", 'w') as f:
            f.write(readme_content)
        
        print(f"  ✅ Created README.txt")
    except Exception as e:
        print(f"  ❌ README creation error: {str(e)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("EXPORT COMPLETE")
    print("=" * 80)
    print(f"Completed: {datetime.now()}")
    print(f"Data saved to: {export_dir}")
    print(f"Total records exported: {sum(export_count.values())}")
    print("=" * 80)
    
    return export_dir, export_count


if __name__ == '__main__':
    export_master_data()
