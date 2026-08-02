"""
Warehouse Cleanup Utility

Identifies and removes unused warehouses from old configuration.

Usage:
    bench --site [site-name] execute tekson_manufacturing.scripts.warehouse_cleanup.run_cleanup
    
    # Dry run (no changes)
    bench --site [site-name] execute tekson_manufacturing.scripts.warehouse_cleanup.run_dry_run
    
    # Force remove specific warehouse
    bench --site [site-name] execute tekson_manufacturing.scripts.warehouse_cleanup.remove_warehouse --kwargs '{"warehouse": "Warehouse Name - TPL"}'
"""

import frappe
from frappe import _
from datetime import datetime


WAREHOUSES_TO_KEEP = [
    # New WIP Warehouses
    'WIP-CNC - TPL', 'WIP-RA - TPL', 'WIP-Ralu In - TPL',
    'WIP-Ralu Weld - TPL', 'WIP-RP - TPL', 'WIP-W - TPL',
    
    # Core Warehouses
    'Raw Material Stores - TPL', 'Finish Goods Stores - TPL',
    'All Warehouses - TPL', 'Stores - TPL', 
    'Receipt and Despatch Stores - TPL', 'Work In Progress - TPL',
    
    # Active Warehouses (have transactions)
    'WIP Warehouse - TPL',  # Has 630+ transactions - needs migration
    'BOF Stores - TPL',  # Has 277+ transactions
]


def get_unused_warehouses():
    """
    Get list of warehouses with zero activity
    
    Returns: list of warehouse names
    """
    warehouses = frappe.get_all('Warehouse', 
        fields=['name', 'is_group', 'parent_warehouse'],
        order_by='name'
    )
    
    unused = []
    
    for wh in warehouses:
        # Skip groups and protected warehouses
        if wh.is_group or wh.name in WAREHOUSES_TO_KEEP:
            continue
        
        # Check for any activity
        sle_count = frappe.db.count('Stock Ledger Entry', {'warehouse': wh.name})
        
        wo_count = frappe.db.count('Work Order', {
            'wip_warehouse': wh.name
        })
        
        se_count = frappe.db.sql("""
            SELECT COUNT(*) FROM `tabStock Entry Detail` 
            WHERE s_warehouse = %s OR t_warehouse = %s
        """, (wh.name, wh.name))[0][0]
        
        if sle_count == 0 and wo_count == 0 and se_count == 0:
            unused.append(wh.name)
    
    return unused


def get_active_warehouses():
    """
    Get warehouses with transactions
    
    Returns: dict with warehouse details and activity counts
    """
    warehouses = frappe.get_all('Warehouse', 
        fields=['name', 'is_group', 'parent_warehouse'],
        order_by='name'
    )
    
    active = []
    
    for wh in warehouses:
        if wh.is_group:
            continue
        
        sle_count = frappe.db.count('Stock Ledger Entry', {'warehouse': wh.name})
        
        wo_count = frappe.db.count('Work Order', {
            'wip_warehouse': wh.name
        })
        
        se_count = frappe.db.sql("""
            SELECT COUNT(*) FROM `tabStock Entry Detail` 
            WHERE s_warehouse = %s OR t_warehouse = %s
        """, (wh.name, wh.name))[0][0]
        
        total = sle_count + wo_count + se_count
        
        if total > 0:
            active.append({
                'warehouse': wh.name,
                'parent': wh.parent_warehouse,
                'sle_count': sle_count,
                'wo_count': wo_count,
                'se_count': se_count,
                'total_activity': total
            })
    
    return sorted(active, key=lambda x: x['total_activity'], reverse=True)


def run_dry_run():
    """
    Dry run - show what would be deleted without making changes
    """
    print("=" * 80)
    print("WAREHOUSE CLEANUP - DRY RUN")
    print("=" * 80)
    print(f"Date: {datetime.now()}")
    print()
    
    unused = get_unused_warehouses()
    active = get_active_warehouses()
    
    print(f"Unused warehouses (will be deleted): {len(unused)}")
    print(f"Active warehouses (will be kept): {len(active)}")
    print()
    
    print("=" * 80)
    print("WAREHOUSES TO BE DELETED:")
    print("=" * 80)
    for wh in unused:
        print(f"  ❌ {wh}")
    
    print()
    print("=" * 80)
    print("ACTIVE WAREHOUSES (KEEP):")
    print("=" * 80)
    for wh in active:
        print(f"  ✅ {wh['warehouse']}")
        print(f"      SLE: {wh['sle_count']}, WO: {wh['wo_count']}, SE: {wh['se_count']}")
    
    print()
    print("=" * 80)
    print("DRY RUN COMPLETE - No changes made")
    print("=" * 80)
    print()
    print("To execute cleanup, run:")
    print("  bench --site [site] execute tekson_manufacturing.scripts.warehouse_cleanup.run_cleanup")
    
    return {
        'unused_count': len(unused),
        'active_count': len(active),
        'unused_list': unused,
        'active_list': active
    }


def run_cleanup(dry_run=False):
    """
    Execute warehouse cleanup
    
    Args:
        dry_run: If True, only show what would be deleted
    
    Returns: dict with cleanup results
    """
    print("=" * 80)
    print("WAREHOUSE CLEANUP - EXECUTION")
    print("=" * 80)
    print(f"Date: {datetime.now()}")
    print()
    
    unused = get_unused_warehouses()
    
    if not unused:
        print("✅ No unused warehouses found. Cleanup complete!")
        return {'deleted': 0, 'errors': []}
    
    print(f"Found {len(unused)} unused warehouses to delete")
    print()
    
    deleted = []
    errors = []
    
    for i, wh_name in enumerate(unused, 1):
        try:
            print(f"[{i}/{len(unused)}] Deleting {wh_name}...")
            
            # Check if warehouse has any children
            children = frappe.db.get_value('Warehouse', 
                {'parent_warehouse': wh_name}, 'name')
            if children:
                errors.append(f"{wh_name}: Has child warehouses")
                print(f"  ⚠️  Skipped: Has child warehouses")
                continue
            
            # Delete warehouse
            frappe.delete_doc('Warehouse', wh_name, force=True, ignore_permissions=True)
            deleted.append(wh_name)
            print(f"  ✅ Deleted")
            
        except Exception as e:
            errors.append(f"{wh_name}: {str(e)}")
            print(f"  ❌ Error: {str(e)}")
    
    frappe.db.commit()
    
    print()
    print("=" * 80)
    print("CLEANUP SUMMARY")
    print("=" * 80)
    print(f"Deleted: {len(deleted)}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print()
        print("Errors:")
        for err in errors:
            print(f"  ❌ {err}")
    
    print()
    print("=" * 80)
    
    return {
        'deleted_count': len(deleted),
        'deleted_list': deleted,
        'errors': errors
    }


def remove_warehouse(warehouse):
    """
    Remove a specific warehouse
    
    Args:
        warehouse: Warehouse name to remove
    
    Usage:
        bench execute tekson_manufacturing.scripts.warehouse_cleanup.remove_warehouse --kwargs '{"warehouse": "Warehouse Name - TPL"}'
    """
    print(f"Removing warehouse: {warehouse}")
    
    if warehouse in WAREHOUSES_TO_KEEP:
        print(f"❌ Cannot remove protected warehouse: {warehouse}")
        return
    
    # Check activity
    sle_count = frappe.db.count('Stock Ledger Entry', {'warehouse': warehouse})
    
    if sle_count > 0:
        print(f"⚠️  WARNING: Warehouse has {sle_count} stock ledger entries!")
        print("This may cause data integrity issues.")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted")
            return
    
    try:
        frappe.delete_doc('Warehouse', warehouse, force=True, ignore_permissions=True)
        frappe.db.commit()
        print(f"✅ Successfully deleted {warehouse}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == '__main__':
    run_dry_run()
