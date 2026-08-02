"""
BOM Item Analysis

Analyzes BOM items to determine if they are:
1. Sub-Assembly (has own BOM → will have own WO/JC)
2. Raw Material/BOF (no BOM → needs transfer from stores)

Usage:
    bench --site [site] execute tekson_manufacturing.scripts.analyze_bom_items.analyze_bom --kwargs '{"work_order": "WO/260802/0012"}'
    
    # Analyze all WOs
    bench --site [site] execute tekson_manufacturing.scripts.analyze_bom_items.analyze_all_boms
"""

import frappe
from frappe import _
from collections import Counter


def analyze_bom(work_order):
    """
    Analyze BOM items for a specific Work Order
    
    Args:
        work_order: Work Order name
    
    Returns: dict with analysis results
    """
    print("=" * 80)
    print("BOM ITEM ANALYSIS")
    print("=" * 80)
    print("Work Order:", work_order)
    print()
    
    wo = frappe.get_doc('Work Order', work_order)
    bom = frappe.get_doc('BOM', wo.bom_no)
    
    print("BOM:", bom.name)
    print("Item:", bom.item)
    print()
    
    sub_assemblies = []
    raw_materials = []
    
    print("=" * 80)
    print("BOM ITEMS ANALYSIS:")
    print("=" * 80)
    
    for item in bom.items:
        item_code = item.item_code
        item_qty = item.qty
        
        # Check if item has its own BOM
        item_bom = frappe.db.get_value('BOM', 
            {'item': item_code, 'is_active': 1, 'docstatus': 1}, 
            'name')
        
        # Get item details
        item_doc = frappe.get_doc('Item', item_code)
        item_group = item_doc.item_group
        
        # Get default warehouse
        default_wh = None
        if item_doc.item_defaults:
            default_wh = item_doc.item_defaults[0].default_warehouse
        
        # Classify
        if item_bom:
            classification = "SUB-ASSEMBLY"
            sub_assemblies.append({
                'item_code': item_code,
                'item_group': item_group,
                'qty': item_qty,
                'bom': item_bom,
                'default_warehouse': default_wh
            })
        else:
            classification = "RAW MATERIAL"
            raw_materials.append({
                'item_code': item_code,
                'item_group': item_group,
                'qty': item_qty,
                'default_warehouse': default_wh
            })
        
        print(f"\n{item_code}")
        print(f"  Classification: {classification}")
        print(f"  Item Group: {item_group}")
        print(f"  Qty: {item_qty}")
        if item_bom:
            print(f"  Has BOM: {item_bom}")
        print(f"  Default Warehouse: {default_wh or 'Not Set'}")
    
    print()
    print("=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    print(f"Total Items: {len(bom.items)}")
    print(f"Sub-Assemblies (have BOM): {len(sub_assemblies)}")
    print(f"Raw Materials (no BOM): {len(raw_materials)}")
    print()
    
    # Analyze by Item Group
    print("=" * 80)
    print("ITEM GROUP DISTRIBUTION:")
    print("=" * 80)
    
    group_counter = Counter([item['item_group'] for item in bom.items])
    for group, count in group_counter.most_common():
        print(f"{group}: {count}")
    
    print()
    print("=" * 80)
    print("SUB-ASSEMBLIES (Will have their own WO/JC):")
    print("=" * 80)
    for sa in sub_assemblies:
        print(f"  - {sa['item_code']} ({sa['item_group']})")
        print(f"    BOM: {sa['bom']}")
    
    print()
    print("=" * 80)
    print("RAW MATERIALS (Need transfer from stores):")
    print("=" * 80)
    for rm in raw_materials:
        print(f"  - {rm['item_code']} ({rm['item_group']})")
        print(f"    Default Warehouse: {rm['default_warehouse'] or 'Not Set'}")
    
    print()
    print("=" * 80)
    
    return {
        'total': len(bom.items),
        'sub_assemblies': sub_assemblies,
        'raw_materials': raw_materials,
        'by_group': dict(group_counter)
    }


def analyze_all_boms():
    """
    Analyze BOMs for all Work Orders in WO/260802 series
    
    Returns: dict with aggregate analysis
    """
    print("=" * 80)
    print("BOM ANALYSIS - ALL WORK ORDERS")
    print("=" * 80)
    print()
    
    # Get all WOs
    all_wos = frappe.get_all('Work Order',
        filters={'name': ['like', 'WO/260802/%'], 'docstatus': 1},
        pluck='name'
    )
    
    print(f"Total Work Orders: {len(all_wos)}")
    print()
    
    total_items = 0
    total_sub_assemblies = 0
    total_raw_materials = 0
    all_item_groups = Counter()
    
    # Sample WOs to show (first 5)
    sample_results = []
    
    for i, wo_name in enumerate(all_wos[:5], 1):
        print(f"[{i}/{len(all_wos)}] Analyzing {wo_name}...")
        
        wo = frappe.get_doc('Work Order', wo_name)
        if not wo.bom_no:
            print(f"  Skipped - No BOM")
            continue
        
        bom = frappe.get_doc('BOM', wo.bom_no)
        
        sub_assemblies = 0
        raw_materials = 0
        
        for item in bom.items:
            total_items += 1
            item_bom = frappe.db.get_value('BOM', 
                {'item': item.item_code, 'is_active': 1, 'docstatus': 1}, 
                'name')
            
            item_doc = frappe.get_doc('Item', item.item_code)
            all_item_groups[item_doc.item_group] += 1
            
            if item_bom:
                sub_assemblies += 1
                total_sub_assemblies += 1
            else:
                raw_materials += 1
                total_raw_materials += 1
        
        print(f"  Items: {len(bom.items)}, Sub-Assemblies: {sub_assemblies}, Raw Materials: {raw_materials}")
        sample_results.append({
            'wo': wo_name,
            'items': len(bom.items),
            'sub_assemblies': sub_assemblies,
            'raw_materials': raw_materials
        })
    
    if len(all_wos) > 5:
        print(f"\n... and {len(all_wos) - 5} more WOs")
    
    print()
    print("=" * 80)
    print("AGGREGATE SUMMARY:")
    print("=" * 80)
    print(f"Total WOs Analyzed: {len(all_wos)}")
    print(f"Total BOM Items: {total_items}")
    print(f"Total Sub-Assemblies: {total_sub_assemblies} ({total_sub_assemblies/total_items*100:.1f}%)")
    print(f"Total Raw Materials: {total_raw_materials} ({total_raw_materials/total_items*100:.1f}%)")
    print()
    
    print("=" * 80)
    print("ITEM GROUP DISTRIBUTION (All BOMs):")
    print("=" * 80)
    for group, count in all_item_groups.most_common():
        print(f"{group}: {count} ({count/total_items*100:.1f}%)")
    
    print()
    print("=" * 80)
    print("SAMPLE WO BREAKDOWN:")
    print("=" * 80)
    for result in sample_results:
        print(f"{result['wo']}:")
        print(f"  Items: {result['items']}")
        print(f"  Sub-Assemblies: {result['sub_assemblies']}")
        print(f"  Raw Materials: {result['raw_materials']}")
    
    print()
    print("=" * 80)
    print("RECOMMENDATION:")
    print("=" * 80)
    print("Use BOM existence check to classify items:")
    print("  - Has BOM → Sub-Assembly (skip in transfer)")
    print("  - No BOM → Raw Material (include in transfer)")
    print("=" * 80)
    
    return {
        'total_wos': len(all_wos),
        'total_items': total_items,
        'total_sub_assemblies': total_sub_assemblies,
        'total_raw_materials': total_raw_materials,
        'by_group': dict(all_item_groups)
    }


if __name__ == '__main__':
    # Demo: Analyze first WO
    analyze_bom('WO/260802/0012')
