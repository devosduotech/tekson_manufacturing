"""
Item Master Default Warehouse Update Utility

Updates item masters with appropriate default warehouses based on item type.

Usage:
    # Review items and their current warehouse settings
    bench --site [site] execute tekson_manufacturing.scripts.item_warehouse_update.run_review
    
    # Auto-assign default warehouses (dry run)
    bench --site [site] execute tekson_manufacturing.scripts.item_warehouse_update.auto_assign_warehouses --kwargs '{"dry_run": True}'
    
    # Auto-assign default warehouses (execute)
    bench --site [site] execute tekson_manufacturing.scripts.item_warehouse_update.auto_assign_warehouses --kwargs '{"dry_run": False}'
    
    # Update specific item
    bench --site [site] execute tekson_manufacturing.scripts.item_warehouse_update.update_item --kwargs '{"item_code": "ITEM-001", "default_warehouse": "Raw Material Stores - TPL"}'
    
    # Bulk update from CSV
    bench --site [site] execute tekson_manufacturing.scripts.item_warehouse_update.bulk_update --kwargs '{"file_path": "/home/karthic/item_warehouses.csv"}'
"""

import frappe
from frappe import _
from datetime import datetime
import csv


# Item type patterns for auto-assignment
ITEM_PATTERNS = {
    # Raw Materials
    'raw_material': {
        'keywords': ['MS', 'STEEL', 'ALUMINIUM', 'ALU', 'BAR', 'SHEET', 'PLATE', 'TUBE', 'PIPE', 'COIL'],
        'warehouse': 'Raw Material Stores - TPL'
    },
    
    # BOF Parts (special components)
    'bof_parts': {
        'keywords': ['BOF', 'BRASS', 'FITTING', 'CONNECTOR', 'VALVE', 'SENSOR', 'SWITCH', 'RELAY'],
        'warehouse': 'BOF Stores - TPL'
    },
    
    # Semi-finished / Sub-assemblies
    'sub_assembly': {
        'keywords': ['SUB ASSY', 'SUB-ASSY', 'SUBASSY', 'TANK', 'CORE', 'HEADER', 'SIDE PANEL', 'END PLATE'],
        'warehouse': None  # Will use WIP based on operation
    },
    
    # Finished Goods
    'finished_goods': {
        'keywords': ['R215', 'R216', 'R217', 'COMBI', 'COOLER', 'RADIATOR', 'CONDENSER', 'EVAPORATOR'],
        'warehouse': 'Finish Goods Stores - TPL'
    }
}


def run_review():
    """
    Review all items and their current warehouse settings
    
    Returns: dict with item summary
    """
    print("=" * 80)
    print("ITEM MASTER WAREHOUSE REVIEW")
    print("=" * 80)
    print(f"Date: {datetime.now()}")
    print()
    
    # Get all items
    items = frappe.get_all('Item',
        fields=['name', 'item_name', 'item_group', 'default_warehouse', 'stock_uom'],
        order_by='name'
    )
    
    print(f"Total Items: {len(items)}")
    print()
    
    # Categorize
    with_warehouse = []
    without_warehouse = []
    by_group = {}
    
    for item in items:
        if item.default_warehouse:
            with_warehouse.append(item)
        else:
            without_warehouse.append(item)
        
        group = item.item_group
        if group not in by_group:
            by_group[group] = []
        by_group[group].append(item)
    
    # Print summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Items with default warehouse: {len(with_warehouse)}")
    print(f"Items without default warehouse: {len(without_warehouse)}")
    print()
    
    # Print by item group
    print("=" * 80)
    print("ITEMS BY GROUP:")
    print("=" * 80)
    
    for group in sorted(by_group.keys()):
        group_items = by_group[group]
        with_wh = sum(1 for i in group_items if i.default_warehouse)
        without_wh = len(group_items) - with_wh
        
        print(f"\n{group} ({len(group_items)} items):")
        print(f"  With warehouse: {with_wh}")
        print(f"  Without warehouse: {without_wh}")
        
        # Show first 5 without warehouse
        without_list = [i for i in group_items if not i.default_warehouse][:5]
        if without_list:
            print("  Items needing warehouse:")
            for item in without_list:
                print(f"    - {item.name}")
            if len(without_list) == 5 and without_wh > 5:
                print(f"    ... and {without_wh - 5} more")
    
    # Show items with warehouses
    if with_warehouse:
        print()
        print("=" * 80)
        print("ITEMS WITH WAREHOUSES (Sample):")
        print("=" * 80)
        
        for item in with_warehouse[:20]:
            print(f"  {item.name}: {item.default_warehouse}")
        
        if len(with_warehouse) > 20:
            print(f"  ... and {len(with_warehouse) - 20} more")
    
    print()
    print("=" * 80)
    
    return {
        'total': len(items),
        'with_warehouse': len(with_warehouse),
        'without_warehouse': len(without_warehouse),
        'by_group': {g: len(items) for g, items in by_group.items()}
    }


def auto_assign_warehouses(dry_run=True):
    """
    Auto-assign default warehouses based on item patterns
    
    Args:
        dry_run: If True, only preview changes
    
    Usage:
        # Preview
        bench execute tekson_manufacturing.scripts.item_warehouse_update.auto_assign_warehouses
        
        # Execute
        bench execute tekson_manufacturing.scripts.item_warehouse_update.auto_assign_warehouses --kwargs '{"dry_run": False}'
    """
    print("=" * 80)
    print("AUTO-ASSIGN DEFAULT WAREHOUSES")
    print("=" * 80)
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTION'}")
    print()
    
    # Get items without default warehouse
    items = frappe.get_all('Item',
        filters={'default_warehouse': ['is', 'not set']},
        fields=['name', 'item_name', 'item_group'],
        order_by='name'
    )
    
    print(f"Found {len(items)} items without default warehouse")
    print()
    
    updates = []
    
    for item in items:
        item_name_upper = (item.name or '').upper()
        item_desc_upper = (item.item_name or '').upper()
        
        assigned_wh = None
        matched_pattern = None
        
        # Check each pattern
        for pattern_type, pattern_data in ITEM_PATTERNS.items():
            keywords = pattern_data['keywords']
            warehouse = pattern_data['warehouse']
            
            # Check if any keyword matches
            for keyword in keywords:
                if keyword in item_name_upper or keyword in item_desc_upper:
                    assigned_wh = warehouse
                    matched_pattern = pattern_type
                    break
            
            if assigned_wh:
                break
        
        # If matched and warehouse is set, add to updates
        if matched_pattern and assigned_wh:
            updates.append({
                'item_code': item.name,
                'item_name': item.item_name,
                'current_warehouse': None,
                'new_warehouse': assigned_wh,
                'pattern': matched_pattern
            })
            
            if dry_run:
                print(f"  📋 {item.name}")
                print(f"      → {assigned_wh} (matched: {matched_pattern})")
        elif matched_pattern:
            # Sub-assembly - will use WIP based on operation
            if dry_run:
                print(f"  ⏭️  {item.name}")
                print(f"      → Will use WIP warehouse from operation (sub-assembly)")
    
    # Execute updates
    if not dry_run and updates:
        print(f"\nExecuting {len(updates)} updates...")
        
        success = 0
        errors = 0
        
        for update in updates:
            try:
                item = frappe.get_doc('Item', update['item_code'])
                item.default_warehouse = update['new_warehouse']
                item.save()
                
                print(f"  ✅ {update['item_code']} → {update['new_warehouse']}")
                success += 1
                
            except Exception as e:
                print(f"  ❌ {update['item_code']}: {str(e)}")
                errors += 1
        
        frappe.db.commit()
        
        print()
        print("=" * 80)
        print("UPDATE SUMMARY")
        print("=" * 80)
        print(f"Success: {success}")
        print(f"Errors: {errors}")
    
    # Print summary
    print()
    print("=" * 80)
    if dry_run:
        print(f"SUMMARY: {len(updates)} items would be updated")
        print(f"         Sub-assemblies will use WIP warehouses from operations")
        print()
        print("To execute, run:")
        print("  bench execute tekson_manufacturing.scripts.item_warehouse_update.auto_assign_warehouses --kwargs '{\"dry_run\": False}'")
    else:
        print(f"SUMMARY: {len(updates)} items updated")
    print("=" * 80)
    
    return {
        'count': len(updates),
        'updates': updates
    }


def update_item(item_code, default_warehouse):
    """
    Update a single item's default warehouse
    
    Args:
        item_code: Item code
        default_warehouse: Warehouse name
    
    Usage:
        bench execute tekson_manufacturing.scripts.item_warehouse_update.update_item --kwargs '{"item_code": "ITEM-001", "default_warehouse": "Raw Material Stores - TPL"}'
    """
    print(f"Updating {item_code}...")
    
    try:
        # Verify warehouse exists
        if not frappe.db.exists('Warehouse', default_warehouse):
            print(f"❌ Warehouse not found: {default_warehouse}")
            return {'success': False, 'error': f"Warehouse not found: {default_warehouse}"}
        
        item = frappe.get_doc('Item', item_code)
        item.default_warehouse = default_warehouse
        item.save()
        frappe.db.commit()
        
        print(f"✅ Successfully updated {item_code}")
        print(f"  Default Warehouse: {default_warehouse}")
        
        return {'success': True, 'item_code': item_code, 'warehouse': default_warehouse}
        
    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error: {str(e)}")
        return {'success': False, 'error': str(e)}


def bulk_update(file_path):
    """
    Bulk update items from CSV file
    
    CSV format:
    item_code,default_warehouse
    
    Args:
        file_path: Path to CSV file
    
    Usage:
        bench execute tekson_manufacturing.scripts.item_warehouse_update.bulk_update --kwargs '{"file_path": "/home/karthic/item_warehouses.csv"}'
    """
    print("=" * 80)
    print("BULK ITEM WAREHOUSE UPDATE")
    print("=" * 80)
    
    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            updates = list(reader)
        
        print(f"Found {len(updates)} items to update")
        print()
        
        success = 0
        errors = 0
        
        for i, row in enumerate(updates, 1):
            item_code = row.get('item_code') or row.get('item')
            warehouse = row.get('default_warehouse') or row.get('warehouse')
            
            if not item_code or not warehouse:
                print(f"[{i}/{len(updates)}] ⚠️  Skipped: Missing data")
                errors += 1
                continue
            
            result = update_item(item_code, warehouse)
            
            if result.get('success'):
                success += 1
            else:
                errors += 1
        
        print()
        print("=" * 80)
        print("BULK UPDATE SUMMARY")
        print("=" * 80)
        print(f"Success: {success}")
        print(f"Errors: {errors}")
        print("=" * 80)
        
        return {'success': success, 'errors': errors, 'total': len(updates)}
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return {'error': f"File not found: {file_path}"}
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {'error': str(e)}


def export_items(file_path):
    """
    Export all items to CSV for review
    
    Args:
        file_path: Path to output CSV file
    
    Usage:
        bench execute tekson_manufacturing.scripts.item_warehouse_update.export_items --kwargs '{"file_path": "/home/karthic/items_export.csv"}'
    """
    print("=" * 80)
    print("ITEM EXPORT")
    print("=" * 80)
    print(f"Output: {file_path}")
    print()
    
    items = frappe.get_all('Item',
        fields=['name', 'item_name', 'item_group', 'default_warehouse', 'stock_uom', 'description'],
        order_by='name'
    )
    
    print(f"Exporting {len(items)} items...")
    
    # Write CSV
    fieldnames = ['item_code', 'item_name', 'item_group', 'default_warehouse', 'stock_uom', 'description']
    
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in items:
            writer.writerow({
                'item_code': item.name,
                'item_name': item.item_name,
                'item_group': item.item_group,
                'default_warehouse': item.default_warehouse or '',
                'stock_uom': item.stock_uom,
                'description': item.description or ''
            })
    
    print()
    print("=" * 80)
    print(f"✅ Successfully exported {len(items)} items to {file_path}")
    print("=" * 80)
    print()
    print("CSV Columns:")
    print("  - item_code: Item code")
    print("  - item_name: Item name/description")
    print("  - item_group: Item group")
    print("  - default_warehouse: Current default warehouse (empty if not set)")
    print("  - stock_uom: Stock UOM")
    print("  - description: Item description")
    print()
    print("To update:")
    print("  1. Open CSV in Excel")
    print("  2. Fill in default_warehouse column")
    print("  3. Save as CSV")
    print("  4. Run bulk_update with the file")
    
    return {'success': True, 'count': len(items), 'file_path': file_path}


if __name__ == '__main__':
    run_review()
