"""
Material Transfer Creator

Creates Material Transfer Stock Entries with correct WIP warehouse
based on Job Card's workstation plant_floor (not Work Order's WIP)

Usage:
    # Create transfer for specific WO
    bench --site [site] execute tekson_manufacturing.scripts.create_material_transfer.create_transfer --kwargs '{"work_order": "WO/260802/0001"}'
    
    # Create transfers for all WOs
    bench --site [site] execute tekson_manufacturing.scripts.create_material_transfer.create_all_transfers
"""

import frappe
from frappe import _
from datetime import datetime


def get_correct_wip_warehouse(work_order_name):
    """
    Get the correct WIP warehouse from Job Cards (not Work Order)
    
    Returns the most common WIP warehouse across all Job Cards for the WO
    
    Args:
        work_order_name: Work Order name
    
    Returns: str - Correct WIP warehouse
    """
    jcs = frappe.get_all('Job Card',
        filters={'work_order': work_order_name},
        fields=['wip_warehouse']
    )
    
    if not jcs:
        # Fallback to WO's WIP
        wo = frappe.get_doc('Work Order', work_order_name)
        return wo.wip_warehouse
    
    # Count WIP warehouses
    from collections import Counter
    wip_counter = Counter([jc.wip_warehouse for jc in jcs if jc.wip_warehouse])
    
    if wip_counter:
        # Return most common WIP warehouse
        return wip_counter.most_common(1)[0][0]
    else:
        # Fallback to WO's WIP
        wo = frappe.get_doc('Work Order', work_order_name)
        return wo.wip_warehouse


def is_raw_material_or_bof(item_code):
    """
    Check if item is a Raw Material or BOF purchased item (not sub-assembly)
    
    Uses BOM existence check:
    - Item has BOM → Sub-Assembly (will have own WO/JC)
    - Item has no BOM → Raw Material (needs transfer)
    
    Args:
        item_code: Item code
    
    Returns: True if raw material/BOF, False if sub-assembly
    """
    # Check if item has its own BOM
    item_bom = frappe.db.get_value('BOM', 
        {'item': item_code, 'is_active': 1, 'docstatus': 1}, 
        'name')
    
    # If item has BOM, it's a sub-assembly (skip)
    if item_bom:
        return False
    
    # No BOM means it's a raw material (include)
    return True


def create_transfer(work_order, raw_materials=None, submit=True, skip_sub_assemblies=True):
    """
    Create Material Transfer Stock Entry for a Work Order
    
    Uses correct WIP warehouse from Job Cards (not Work Order)
    
    Args:
        work_order: Work Order name
        raw_materials: List of dicts with item_code, qty, from_warehouse (optional)
                      If None, uses BOM items
        submit: Whether to submit the Stock Entry
        skip_sub_assemblies: If True, only transfer raw materials & BOF items
    
    Returns: Stock Entry document
    """
    print("=" * 80)
    print("CREATING MATERIAL TRANSFER")
    print("=" * 80)
    print("Work Order:", work_order)
    print()
    
    wo = frappe.get_doc('Work Order', work_order)
    
    # Get correct WIP from Job Cards
    correct_wip = get_correct_wip_warehouse(work_order)
    
    print("WO WIP Warehouse (may be old):", wo.wip_warehouse)
    print("Correct WIP (from Job Cards):", correct_wip)
    print()
    
    # Get BOM items if not provided
    if not raw_materials:
        bom = frappe.get_doc('BOM', wo.bom_no)
        raw_materials = []
        skipped_count = 0
        
        for item in bom.items:
            # Skip sub-assemblies if flag is set
            if skip_sub_assemblies and not is_raw_material_or_bof(item.item_code):
                print(f"Skipping sub-assembly: {item.item_code}")
                skipped_count += 1
                continue
            
            item_doc = frappe.get_doc('Item', item.item_code)
            
            # Get default warehouse from item
            from_wh = None
            if item_doc.item_defaults:
                from_wh = item_doc.item_defaults[0].default_warehouse
            
            # Default to Raw Material Stores if not set
            if not from_wh:
                from_wh = 'Raw Material Stores - TPL'
            
            raw_materials.append({
                'item_code': item.item_code,
                'qty': item.qty,
                'from_warehouse': from_wh
            })
        
        if skipped_count > 0:
            print(f"Skipped {skipped_count} sub-assemblies")
        print()
    
    # Create Stock Entry
    se = frappe.get_doc({
        'doctype': 'Stock Entry',
        'stock_entry_type': 'Material Transfer for Manufacture',
        'work_order': work_order,
        'from_warehouse': None,  # Will be set per item
        'to_warehouse': correct_wip,
        'posting_date': frappe.utils.today(),
        'posting_time': frappe.utils.nowtime(),
        'items': []
    })
    
    # Add items
    for rm in raw_materials:
        se.append('items', {
            'item_code': rm['item_code'],
            'qty': rm['qty'],
            's_warehouse': rm['from_warehouse'],
            't_warehouse': correct_wip,
            'allow_zero_valuation_rate': 1
        })
    
    se.insert()
    print("Stock Entry Created:", se.name)
    
    if submit:
        se.submit()
        frappe.db.commit()
        print("Stock Entry Submitted:", se.name)
    
    print()
    print("TRANSFER DETAILS:")
    print("=" * 80)
    for item in se.items:
        print("Item:", item.item_code)
        print("  Qty:", item.qty)
        print("  From:", item.s_warehouse)
        print("  To:", item.t_warehouse)
        print()
    
    # Validate
    print("=" * 80)
    print("VALIDATION:")
    print("=" * 80)
    
    all_correct = True
    for item in se.items:
        if item.t_warehouse != correct_wip:
            print("ERROR:", item.item_code, "transferred to", item.t_warehouse, "instead of", correct_wip)
            all_correct = False
    
    if all_correct:
        print("SUCCESS - All items transferred to correct WIP warehouse!")
        print("To Warehouse:", correct_wip)
    
    print("=" * 80)
    
    return se


def create_all_transfers(submit=True):
    """
    Create Material Transfer for all Work Orders in WO/260802 series
    
    Args:
        submit: Whether to submit Stock Entries
    
    Returns: dict with summary
    """
    print("=" * 80)
    print("CREATING ALL MATERIAL TRANSFERS")
    print("=" * 80)
    print()
    
    # Get all submitted WOs
    all_wos = frappe.get_all('Work Order',
        filters={'name': ['like', 'WO/260802/%'], 'docstatus': 1},
        pluck='name'
    )
    
    print("Total Work Orders:", len(all_wos))
    print()
    
    success = 0
    errors = 0
    skipped = 0
    
    for i, wo_name in enumerate(all_wos, 1):
        print(f"[{i}/{len(all_wos)}] Processing {wo_name}...")
        
        try:
            # Check if transfer already exists
            existing_se = frappe.db.get_value('Stock Entry',
                {'work_order': wo_name, 'stock_entry_type': 'Material Transfer for Manufacture', 'docstatus': 1},
                'name')
            
            if existing_se:
                print(f"  Skipped - Transfer already exists: {existing_se}")
                skipped += 1
                continue
            
            # Create transfer
            se = create_transfer(wo_name, submit=submit)
            print(f"  Created: {se.name}")
            success += 1
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            errors += 1
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("Success:", success)
    print("Skipped:", skipped)
    print("Errors:", errors)
    print("=" * 80)
    
    return {
        'success': success,
        'skipped': skipped,
        'errors': errors,
        'total': len(all_wos)
    }


if __name__ == '__main__':
    # Demo: Create transfer for first WO
    create_transfer('WO/260802/0001', submit=False)
