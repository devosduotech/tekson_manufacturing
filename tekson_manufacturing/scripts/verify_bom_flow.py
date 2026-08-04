"""
BOM Multi-Level Warehouse Flow Verification

Verifies that child component's target_fg_warehouse matches parent BOM item's source_warehouse
for proper multi-department material flow.

Usage:
    # Full verification
    bench --site teksons.dev execute tekson_manufacturing.scripts.verify_bom_flow.check_multi_level_flow
    
    # Check specific BOM
    bench --site teksons.dev execute tekson_manufacturing.scripts.verify_bom_flow.check_single_bom_flow --args '["BOM-R215 CAC-001"]'
"""

import frappe
from typing import Dict, List


def check_multi_level_flow():
    """
    Check all multi-level BOMs for warehouse flow consistency
    
    Rule: Child BOM's target_fg_warehouse should match Parent BOM item's source_warehouse
    """
    print("=" * 80)
    print("MULTI-LEVEL BOM WAREHOUSE FLOW VERIFICATION")
    print("=" * 80)
    
    # Get all BOMs
    all_boms = frappe.get_all('BOM', 
        fields=['name', 'item', 'docstatus', 'target_fg_warehouse'],
        filters={'docstatus': 1},
        order_by='name'
    )
    
    print(f"\nTotal submitted BOMs: {len(all_boms)}")
    
    # Build BOM lookup
    bom_lookup = {}
    for bom in all_boms:
        bom_lookup[bom.name] = bom
    
    # Find multi-level BOMs (BOMs that have sub-assemblies)
    multi_level_boms = []
    flow_issues = []
    flow_ok = []
    
    print("\n" + "=" * 80)
    print("CHECKING: Multi-Level BOM Warehouse Flow")
    print("=" * 80)
    
    for bom in all_boms:
        bom_doc = frappe.get_doc('BOM', bom.name)
        
        # Check if this BOM has sub-assemblies (items with bom_no)
        sub_assemblies = [item for item in bom_doc.items if item.bom_no]
        
        if sub_assemblies:
            multi_level_boms.append({
                'bom': bom.name,
                'item': bom.item,
                'sub_assemblies': len(sub_assemblies)
            })
            
            # Check warehouse flow for each sub-assembly
            bom_flow_result = {
                'bom': bom.name,
                'item': bom.item,
                'issues': [],
                'ok': []
            }
            
            for sub_asm in sub_assemblies:
                child_bom_name = sub_asm.bom_no
                
                # Get child BOM
                if child_bom_name in bom_lookup:
                    child_bom = bom_lookup[child_bom_name]
                    
                    # Compare warehouses
                    parent_source_wh = sub_asm.source_warehouse
                    child_target_wh = child_bom.target_fg_warehouse
                    
                    if parent_source_wh == child_target_wh:
                        bom_flow_result['ok'].append({
                            'sub_assembly': sub_asm.item_code,
                            'child_bom': child_bom_name,
                            'parent_source_wh': parent_source_wh,
                            'child_target_wh': child_target_wh,
                            'match': True
                        })
                    else:
                        bom_flow_result['issues'].append({
                            'sub_assembly': sub_asm.item_code,
                            'child_bom': child_bom_name,
                            'parent_source_wh': parent_source_wh,
                            'child_target_wh': child_target_wh,
                            'match': False
                        })
                        flow_issues.append({
                            'parent_bom': bom.name,
                            'sub_assembly': sub_asm.item_code,
                            'child_bom': child_bom_name,
                            'parent_source_wh': parent_source_wh,
                            'child_target_wh': child_target_wh
                        })
            
            if bom_flow_result['issues']:
                flow_issues.append(bom_flow_result)
            else:
                flow_ok.append(bom_flow_result)
    
    print(f"\nMulti-level BOMs found: {len(multi_level_boms)}")
    print(f"BOMs with correct flow: {len(flow_ok)}")
    print(f"BOMs with flow issues: {len([f for f in flow_issues if isinstance(f, dict) and 'issues' in f])}")
    
    # Show issues
    if flow_issues:
        print("\n" + "=" * 80)
        print("⚠️  WAREHOUSE FLOW MISMATCHES")
        print("=" * 80)
        
        issue_count = 0
        for issue in flow_issues:
            if isinstance(issue, dict) and 'parent_bom' in issue:
                issue_count += 1
                print(f"\n❌ Issue #{issue_count}:")
                print(f"  Parent BOM: {issue['parent_bom']}")
                print(f"  Sub-Assembly: {issue['sub_assembly']}")
                print(f"  Child BOM: {issue['child_bom']}")
                print(f"  Parent Item source_warehouse: {issue['parent_source_wh']}")
                print(f"  Child BOM target_fg_warehouse: {issue['child_target_wh']}")
                print(f"  ⚠️  MISMATCH! These should be the same warehouse")
    else:
        print("\n✅ ALL MULTI-LEVEL BOMs HAVE CORRECT WAREHOUSE FLOW")
    
    # Show detailed flow for sample BOMs
    print("\n" + "=" * 80)
    print("MULTI-LEVEL BOM FLOW DETAILS (Sample)")
    print("=" * 80)
    
    for ml_bom in multi_level_boms[:10]:
        bom_doc = frappe.get_doc('BOM', ml_bom['bom'])
        sub_assemblies = [item for item in bom_doc.items if item.bom_no]
        
        print(f"\n{ml_bom['bom']} → {ml_bom['item']}")
        print(f"  Target FG Warehouse: {bom_doc.target_fg_warehouse}")
        print(f"  Sub-assemblies: {len(sub_assemblies)}")
        
        for sub_asm in sub_assemblies:
            child_bom = frappe.get_doc('BOM', sub_asm.bom_no) if sub_asm.bom_no else None
            status = "✅" if (child_bom and child_bom.target_fg_warehouse == sub_asm.source_warehouse) else "❌"
            
            print(f"  {status} {sub_asm.item_code}")
            print(f"      Parent source_warehouse: {sub_asm.source_warehouse}")
            if child_bom:
                print(f"      Child target_fg_warehouse: {child_bom.target_fg_warehouse}")
                print(f"      Child BOM: {sub_asm.bom_no}")
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_sub_assemblies = sum([ml['sub_assemblies'] for ml in multi_level_boms])
    print(f"Total multi-level BOMs: {len(multi_level_boms)}")
    print(f"Total sub-assembly references: {total_sub_assemblies}")
    print(f"Warehouse flow matches: {total_sub_assemblies - len([i for i in flow_issues if isinstance(i, dict) and 'parent_bom' in i])}")
    print(f"Warehouse flow mismatches: {len([i for i in flow_issues if isinstance(i, dict) and 'parent_bom' in i])}")
    
    if len([i for i in flow_issues if isinstance(i, dict) and 'parent_bom' in i]) == 0:
        print("\n✅ ALL WAREHOUSE FLOWS ARE CORRECT!")
        print("   Multi-department material flow will work correctly")
    else:
        print("\n⚠️  WAREHOUSE FLOW ISSUES FOUND!")
        print("   These mismatches may cause material flow problems in production")
    
    return {
        'total_boms': len(all_boms),
        'multi_level_boms': len(multi_level_boms),
        'total_sub_assemblies': total_sub_assemblies,
        'flow_ok': len(flow_ok),
        'flow_issues': len([i for i in flow_issues if isinstance(i, dict) and 'parent_bom' in i]),
        'issues': [i for i in flow_issues if isinstance(i, dict) and 'parent_bom' in i]
    }


def check_single_bom_flow(bom_name: str):
    """
    Check warehouse flow for a specific BOM
    
    Args:
        bom_name: BOM name to check
    """
    print("=" * 80)
    print(f"WAREHOUSE FLOW CHECK: {bom_name}")
    print("=" * 80)
    
    try:
        bom = frappe.get_doc('BOM', bom_name)
    except Exception as e:
        print(f"❌ BOM not found: {bom_name}")
        return
    
    print(f"\nBOM: {bom.name}")
    print(f"Item: {bom.item}")
    print(f"Target FG Warehouse: {bom.target_fg_warehouse}")
    
    # Find sub-assemblies
    sub_assemblies = [item for item in bom.items if item.bom_no]
    
    if not sub_assemblies:
        print("\nℹ️  This is a single-level BOM (no sub-assemblies)")
        return
    
    print(f"\nSub-assemblies: {len(sub_assemblies)}")
    print("-" * 80)
    
    issues = []
    matches = []
    
    for idx, sub_asm in enumerate(sub_assemblies, 1):
        print(f"\n{idx}. {sub_asm.item_code}")
        print(f"   Parent source_warehouse: {sub_asm.source_warehouse}")
        
        if sub_asm.bom_no:
            try:
                child_bom = frappe.get_doc('BOM', sub_asm.bom_no)
                print(f"   Child BOM: {child_bom.name}")
                print(f"   Child target_fg_warehouse: {child_bom.target_fg_warehouse}")
                
                if sub_asm.source_warehouse == child_bom.target_fg_warehouse:
                    print(f"   ✅ WAREHOUSE MATCH")
                    matches.append(sub_asm.item_code)
                else:
                    print(f"   ❌ WAREHOUSE MISMATCH!")
                    issues.append({
                        'sub_assembly': sub_asm.item_code,
                        'parent_source_wh': sub_asm.source_warehouse,
                        'child_target_wh': child_bom.target_fg_warehouse
                    })
            except Exception as e:
                print(f"   ⚠️  Child BOM not found: {sub_asm.bom_no}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Sub-assemblies checked: {len(sub_assemblies)}")
    print(f"Warehouse matches: {len(matches)}")
    print(f"Warehouse mismatches: {len(issues)}")
    
    if issues:
        print(f"\n⚠️  ISSUES:")
        for issue in issues:
            print(f"   - {issue['sub_assembly']}: {issue['parent_source_wh']} ≠ {issue['child_target_wh']}")
    else:
        print(f"\n✅ ALL WAREHOUSE FLOWS ARE CORRECT")
