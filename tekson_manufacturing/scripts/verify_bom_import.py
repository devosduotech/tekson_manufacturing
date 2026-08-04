"""
BOM Import Verification Script

Verifies all imported BOMs for:
1. Target FG Warehouse is set
2. All BOM items have Source Warehouse
3. All operations have valid sequence (idx > 0)
4. All warehouses exist in ERPNext

Usage:
    # Full verification
    bench --site teksons.dev execute tekson_manufacturing.scripts.verify_bom_import.verify_all_boms
    
    # Verify specific BOM
    bench --site teksons.dev execute tekson_manufacturing.scripts.verify_bom_import.verify_single_bom --args '["BOM-R215 CAC Core-001"]'
    
    # Verify only submitted BOMs
    bench --site teksons.dev execute tekson_manufacturing.scripts.verify_bom_import.verify_submitted_boms
"""

import frappe
from frappe import _
from typing import Any, Dict, List


def verify_all_boms():
    """Verify all BOMs in the system"""
    print("=" * 80)
    print("BOM IMPORT VERIFICATION REPORT")
    print("=" * 80)
    
    # Get all BOMs
    all_boms = frappe.get_all('BOM', 
        fields=['name', 'item', 'docstatus', 'target_fg_warehouse', 'quantity'],
        order_by='name'
    )
    
    print(f"\nTotal BOMs found: {len(all_boms)}")
    
    # Categorize by status
    submitted = [b for b in all_boms if b.docstatus == 1]
    draft = [b for b in all_boms if b.docstatus == 0]
    
    print(f"  - Submitted: {len(submitted)}")
    print(f"  - Draft: {len(draft)}")
    
    # Verification results
    results = {
        'total': len(all_boms),
        'submitted': len(submitted),
        'draft': len(draft),
        'target_fg_wh_ok': 0,
        'target_fg_wh_missing': 0,
        'source_wh_ok': 0,
        'source_wh_missing': 0,
        'operations_ok': 0,
        'operations_with_zero_idx': 0,
        'passed': [],
        'warnings': [],
        'failed': []
    }
    
    # Get all valid warehouses
    valid_warehouses = set([wh.name for wh in frappe.get_all('Warehouse', fields=['name'])])
    
    print("\n" + "=" * 80)
    print("CHECKING: Target FG Warehouse")
    print("=" * 80)
    
    for bom in all_boms:
        if bom.target_fg_warehouse:
            results['target_fg_wh_ok'] += 1
        else:
            results['target_fg_wh_missing'] += 1
            results['failed'].append({
                'bom': bom.name,
                'issue': 'Missing target_fg_warehouse'
            })
            print(f"  ❌ {bom.name}: Missing target_fg_warehouse")
    
    if results['target_fg_wh_missing'] == 0:
        print(f"✅ All {results['target_fg_wh_ok']} BOMs have target_fg_warehouse set")
    else:
        print(f"⚠️  {results['target_fg_wh_missing']} BOMs missing target_fg_warehouse")
    
    print("\n" + "=" * 80)
    print("CHECKING: BOM Items Source Warehouse")
    print("=" * 80)
    
    total_items = 0
    items_with_wh = 0
    
    for bom in all_boms:
        bom_doc = frappe.get_doc('BOM', bom.name)
        bom_result = {
            'bom': bom.name,
            'items_missing_wh': [],
            'operations_zero_idx': []
        }
        
        # Check items
        for item in bom_doc.items:
            total_items += 1
            if not item.source_warehouse:
                bom_result['items_missing_wh'].append({
                    'item_code': item.item_code,
                    'idx': item.idx
                })
            else:
                items_with_wh += 1
                # Verify warehouse exists
                if item.source_warehouse not in valid_warehouses:
                    print(f"  ⚠️  {bom.name}: Item {item.item_code} has invalid warehouse '{item.source_warehouse}'")
        
        if bom_result['items_missing_wh']:
            results['source_wh_missing'] += 1
            results['failed'].append(bom_result)
            print(f"  ❌ {bom.name}: {len(bom_result['items_missing_wh'])} items missing source_warehouse")
            for item in bom_result['items_missing_wh'][:5]:
                print(f"      - {item['item_code']}")
        else:
            results['source_wh_ok'] += 1
    
    if results['source_wh_missing'] == 0:
        print(f"✅ All {total_items} items have source_warehouse set")
    else:
        print(f"⚠️  {results['source_wh_missing']} BOMs have items missing source_warehouse")
    
    print("\n" + "=" * 80)
    print("CHECKING: Operation Sequence ID (idx)")
    print("=" * 80)
    
    boms_with_ops = 0
    ops_ok = 0
    
    for bom in all_boms:
        bom_doc = frappe.get_doc('BOM', bom.name)
        
        if bom_doc.operations:
            boms_with_ops += 1
            has_zero_idx = False
            
            for op in bom_doc.operations:
                if op.idx == 0 or not op.idx:
                    has_zero_idx = True
                    bom_result['operations_zero_idx'].append({
                        'operation': op.operation,
                        'idx': op.idx
                    })
                else:
                    ops_ok += 1
            
            if has_zero_idx:
                results['operations_with_zero_idx'] += 1
                print(f"  ⚠️  {bom.name}: Has operations with idx = 0")
                for op in bom_result.get('operations_zero_idx', []):
                    print(f"      - Operation '{op['operation']}' has idx = {op['idx']}")
            else:
                results['operations_ok'] += 1
    
    if results['operations_with_zero_idx'] == 0:
        print(f"✅ All {ops_ok} operations have valid idx > 0")
    else:
        print(f"⚠️  {results['operations_with_zero_idx']} BOMs have operations with idx = 0")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_issues = (
        results['target_fg_wh_missing'] + 
        results['source_wh_missing'] + 
        results['operations_with_zero_idx']
    )
    
    if total_issues == 0:
        print(f"✅ PASS: All {results['total']} BOMs verified successfully!")
        results['passed'] = [b.name for b in all_boms]
    else:
        print(f"✅ PASS: {results['total'] - total_issues} BOMs")
        print(f"⚠️  WARNINGS: {results['operations_with_zero_idx']} BOMs (operation idx issues)")
        print(f"❌ FAIL: {total_issues} BOMs")
        
        if results['failed']:
            print(f"\n📋 Failed BOMs ({len(results['failed'])}):")
            for fail in results['failed'][:10]:
                print(f"   - {fail['bom']}")
            if len(results['failed']) > 10:
                print(f"   ... and {len(results['failed']) - 10} more")
    
    # Statistics
    print("\n" + "=" * 80)
    print("STATISTICS")
    print("=" * 80)
    print(f"Total BOMs: {results['total']}")
    print(f"Total Items: {total_items}")
    print(f"BOMs with Operations: {boms_with_ops}")
    print(f"Average items per BOM: {total_items / results['total']:.1f}")
    
    # Warehouse distribution
    print("\n" + "=" * 80)
    print("TARGET FG WAREHOUSE DISTRIBUTION")
    print("=" * 80)
    
    wh_counts = {}
    for bom in all_boms:
        wh = bom.target_fg_warehouse or 'MISSING'
        wh_counts[wh] = wh_counts.get(wh, 0) + 1
    
    for wh, count in sorted(wh_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / results['total']) * 100
        print(f"  {wh}: {count} BOMs ({percentage:.1f}%)")
    
    return results


def verify_single_bom(bom_name: str):
    """Verify a single BOM in detail"""
    print("=" * 80)
    print(f"DETAILED VERIFICATION: {bom_name}")
    print("=" * 80)
    
    try:
        bom = frappe.get_doc('BOM', bom_name)
    except Exception as e:
        print(f"❌ BOM not found: {bom_name}")
        return
    
    print(f"\nBOM: {bom.name}")
    print(f"Item: {bom.item}")
    print(f"Status: {'Submitted' if bom.docstatus == 1 else 'Draft'}")
    print(f"Quantity: {bom.quantity}")
    print(f"Target FG Warehouse: {bom.target_fg_warehouse or '❌ MISSING'}")
    
    # Check items
    print(f"\n{'=' * 80}")
    print(f"BOM ITEMS ({len(bom.items)} items)")
    print(f"{'=' * 80}")
    
    items_ok = 0
    items_missing_wh = 0
    
    for idx, item in enumerate(bom.items, 1):
        if item.source_warehouse:
            items_ok += 1
            status = "✅"
        else:
            items_missing_wh += 1
            status = "❌"
        
        print(f"  {status} Item {idx}: {item.item_code}")
        print(f"      Qty: {item.qty} {item.uom}")
        print(f"      Source Warehouse: {item.source_warehouse or 'MISSING'}")
        if item.bom_no:
            print(f"      Sub-assembly BOM: {item.bom_no}")
    
    print(f"\nSummary: {items_ok}/{len(bom.items)} items have source_warehouse")
    
    # Check operations
    print(f"\n{'=' * 80}")
    print(f"OPERATIONS ({len(bom.operations)} operations)")
    print(f"{'=' * 80}")
    
    ops_ok = 0
    ops_with_issues = 0
    
    for idx, op in enumerate(bom.operations, 1):
        if op.idx and op.idx > 0:
            ops_ok += 1
            status = "✅"
        else:
            ops_with_issues += 1
            status = "⚠️"
        
        print(f"  {status} Op {idx}: {op.operation}")
        print(f"      idx: {op.idx or 0}")
        if op.workstation:
            print(f"      Workstation: {op.workstation}")
        if op.workstation_type:
            print(f"      Workstation Type: {op.workstation_type}")
    
    print(f"\nSummary: {ops_ok}/{len(bom.operations)} operations have valid idx")
    
    # Overall status
    print(f"\n{'=' * 80}")
    print(f"OVERALL STATUS")
    print(f"{'=' * 80}")
    
    issues = []
    if not bom.target_fg_warehouse:
        issues.append("Missing target_fg_warehouse")
    if items_missing_wh > 0:
        issues.append(f"{items_missing_wh} items missing source_warehouse")
    if ops_with_issues > 0:
        issues.append(f"{ops_with_issues} operations with idx = 0")
    
    if issues:
        print(f"⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print(f"✅ NO ISSUES - BOM is ready for production!")


def verify_submitted_boms():
    """Verify only submitted BOMs (docstatus = 1)"""
    print("=" * 80)
    print("SUBMITTED BOM VERIFICATION")
    print("=" * 80)
    
    submitted_boms = frappe.get_all('BOM', 
        filters={'docstatus': 1},
        fields=['name', 'item', 'target_fg_warehouse'],
        order_by='name'
    )
    
    print(f"\nTotal submitted BOMs: {len(submitted_boms)}")
    
    results = {
        'total': len(submitted_boms),
        'passed': 0,
        'failed': 0,
        'issues': []
    }
    
    for bom in submitted_boms:
        bom_doc = frappe.get_doc('BOM', bom.name)
        issues = []
        
        # Check target FG warehouse
        if not bom_doc.target_fg_warehouse:
            issues.append("Missing target_fg_warehouse")
        
        # Check items
        for item in bom_doc.items:
            if not item.source_warehouse:
                issues.append(f"Item {item.item_code} missing source_warehouse")
                break
        
        # Check operations
        for op in bom_doc.operations:
            if not op.idx or op.idx == 0:
                issues.append(f"Operation {op.operation} has idx = 0")
                break
        
        if issues:
            results['failed'] += 1
            results['issues'].append({
                'bom': bom.name,
                'issues': issues
            })
        else:
            results['passed'] += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Passed: {results['passed']} BOMs")
    if results['failed'] > 0:
        print(f"❌ Failed: {results['failed']} BOMs")
        print(f"\nFailed BOMs:")
        for issue in results['issues'][:10]:
            print(f"  - {issue['bom']}: {', '.join(issue['issues'])}")
        if len(results['issues']) > 10:
            print(f"  ... and {len(results['issues']) - 10} more")
    else:
        print(f"✅ All submitted BOMs passed verification!")
    
    return results
