"""
WIP Warehouse Migration Utility

Migrates old Work Orders and Job Cards from 'WIP Warehouse - TPL'
to new plant-floor-specific WIP warehouses.

Usage:
    # Dry run - preview migration
    bench --site [site] execute tekson_manufacturing.scripts.migrate_wip_warehouse.run_migration --kwargs '{"dry_run": true}'
    
    # Execute migration
    bench --site [site] execute tekson_manufacturing.scripts.migrate_wip_warehouse.run_migration --kwargs '{"dry_run": false}'
    
    # Migrate specific Work Order
    bench --site [site] execute tekson_manufacturing.scripts.migrate_wip_warehouse.migrate_work_order --kwargs '{"work_order": "WO-2026-001"}'
"""

import frappe
from frappe import _
from datetime import datetime


OLD_WIP_WAREHOUSE = "WIP Warehouse - TPL"


def get_new_wip_warehouse(work_order_doc):
    """
    Determine the correct new WIP warehouse for a Work Order
    
    Priority:
    1. plant_floor field
    2. First Job Card's workstation plant_floor
    3. Default to WIP-W - TPL
    
    Args:
        work_order_doc: Work Order document
    
    Returns: str - New WIP warehouse name
    """
    # Try plant_floor first
    plant_floor = work_order_doc.get('plant_floor')
    
    # Fallback to first Job Card's workstation
    if not plant_floor:
        job_cards = frappe.get_all('Job Card',
            filters={'work_order': work_order_doc.name},
            fields=['workstation'],
            order_by='creation'
        )
        if job_cards and job_cards[0].workstation:
            plant_floor = frappe.db.get_value('Workstation', 
                job_cards[0].workstation, 'plant_floor')
    
    # Default fallback
    if not plant_floor:
        plant_floor = 'W'
    
    # Format: WIP-{plant_floor} - TPL
    return f"WIP-{plant_floor} - TPL"


def migrate_work_order(wo_name, dry_run=True):
    """
    Migrate a single Work Order to new WIP warehouse
    
    Args:
        wo_name: Work Order name
        dry_run: If True, only preview changes
    
    Returns: dict with migration result
    """
    try:
        wo = frappe.get_doc('Work Order', wo_name)
        
        # Skip if already using new warehouse
        if wo.wip_warehouse and wo.wip_warehouse != OLD_WIP_WAREHOUSE:
            return {
                'work_order': wo_name,
                'status': 'skipped',
                'message': f'Already using {wo.wip_warehouse}',
                'old_warehouse': wo.wip_warehouse,
                'new_warehouse': wo.wip_warehouse
            }
        
        # Get new warehouse
        new_warehouse = get_new_wip_warehouse(wo)
        
        if dry_run:
            return {
                'work_order': wo_name,
                'status': 'pending',
                'message': f'Would migrate to {new_warehouse}',
                'old_warehouse': wo.wip_warehouse,
                'new_warehouse': new_warehouse,
                'plant_floor': wo.get('plant_floor')
            }
        
        # Execute migration
        wo.wip_warehouse = new_warehouse
        wo.save()
        
        # Also migrate Job Cards
        job_cards = frappe.get_all('Job Card',
            filters={'work_order': wo_name, 'wip_warehouse': OLD_WIP_WAREHOUSE},
            pluck='name'
        )
        
        jc_migrated = []
        for jc_name in job_cards:
            jc = frappe.get_doc('Job Card', jc_name)
            jc.wip_warehouse = new_warehouse
            jc.save()
            jc_migrated.append(jc_name)
        
        frappe.db.commit()
        
        return {
            'work_order': wo_name,
            'status': 'success',
            'message': f'Migrated to {new_warehouse}',
            'old_warehouse': OLD_WIP_WAREHOUSE,
            'new_warehouse': new_warehouse,
            'job_cards_migrated': len(jc_migrated),
            'job_card_names': jc_migrated
        }
        
    except Exception as e:
        frappe.db.rollback()
        return {
            'work_order': wo_name,
            'status': 'error',
            'message': str(e),
            'old_warehouse': OLD_WIP_WAREHOUSE,
            'new_warehouse': None
        }


def run_migration(dry_run=True):
    """
    Migrate all Work Orders from old WIP warehouse to new ones
    
    Args:
        dry_run: If True, only preview changes
    
    Returns: dict with migration summary
    """
    print("=" * 80)
    print("WIP WAREHOUSE MIGRATION")
    print("=" * 80)
    print(f"Date: {datetime.now()}")
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTION'}")
    print()
    
    # Find all Work Orders using old WIP warehouse
    wo_list = frappe.get_all('Work Order',
        filters={'wip_warehouse': OLD_WIP_WAREHOUSE},
        fields=['name', 'status', 'production_item', 'plant_floor'],
        order_by='creation'
    )
    
    print(f"Found {len(wo_list)} Work Orders using '{OLD_WIP_WAREHOUSE}'")
    print()
    
    if not wo_list:
        print("✅ No Work Orders to migrate!")
        return {'total': 0, 'migrated': 0, 'errors': [], 'results': []}
    
    # Migrate each Work Order
    results = []
    success_count = 0
    error_count = 0
    skip_count = 0
    
    for i, wo_data in enumerate(wo_list, 1):
        result = migrate_work_order(wo_data.name, dry_run)
        results.append(result)
        
        if result['status'] == 'success':
            success_count += 1
            status_icon = "✅"
        elif result['status'] == 'error':
            error_count += 1
            status_icon = "❌"
        elif result['status'] == 'skipped':
            skip_count += 1
            status_icon = "⏭️"
        else:
            status_icon = "📋"
        
        # Print progress
        if i <= 20 or i == len(wo_list):
            print(f"[{i}/{len(wo_list)}] {status_icon} {wo_data.name}")
            print(f"    {result['message']}")
            if result.get('plant_floor'):
                print(f"    Plant Floor: {result['plant_floor']}")
    
    if len(wo_list) > 20:
        print(f"\n... and {len(wo_list) - 20} more")
    
    # Summary
    print()
    print("=" * 80)
    print("MIGRATION SUMMARY")
    print("=" * 80)
    print(f"Total Work Orders: {len(wo_list)}")
    if dry_run:
        print(f"Would migrate: {success_count}")
    else:
        print(f"Migrated: {success_count}")
    print(f"Skipped: {skip_count}")
    print(f"Errors: {error_count}")
    
    if error_count > 0:
        print()
        print("Errors:")
        for r in results:
            if r['status'] == 'error':
                print(f"  ❌ {r['work_order']}: {r['message']}")
    
    print()
    print("=" * 80)
    
    if dry_run:
        print()
        print("To execute migration, run:")
        print("  bench --site [site] execute tekson_manufacturing.scripts.migrate_wip_warehouse.run_migration --kwargs '{\"dry_run\": false}'")
    
    return {
        'total': len(wo_list),
        'migrated': success_count,
        'skipped': skip_count,
        'errors': error_count,
        'results': results
    }


if __name__ == '__main__':
    # Default: dry run
    run_migration(dry_run=True)
