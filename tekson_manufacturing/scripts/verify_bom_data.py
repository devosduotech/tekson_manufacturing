"""
BOM Data Verification Script

Checks all BOMs for required fields:
- fg_warehouse on BOM
- source_warehouse on all BOM items
- Workstation on operations (optional but recommended)

Usage:
    bench --site teksons.dev execute tekson_manufacturing.scripts.verify_bom_data.verify_all_boms
    bench --site teksons.dev execute tekson_manufacturing.scripts.verify_bom_data.verify_bom --args '["BOM-R215 CAC Core-002"]'
"""

import frappe
from frappe import _


def verify_bom(bom_name):
    """
    Verify a single BOM has all required data
    
    Args:
        bom_name: BOM name
    
    Returns: dict with verification results
    """
    print("\n" + "=" * 80)
    print(f"VERIFYING BOM: {bom_name}")
    print("=" * 80)
    
    try:
        bom = frappe.get_doc('BOM', bom_name)
    except Exception as e:
        print(f"❌ BOM not found: {bom_name}")
        return {'status': 'ERROR', 'message': str(e)}
    
    # Get BOM with all fields
    bom = frappe.get_doc('BOM', bom_name)
    
    # Check if warehouse field exists (ERPNext V15 uses 'target_fg_warehouse')
    target_warehouse = getattr(bom, 'target_fg_warehouse', None) or getattr(bom, 'warehouse', None) or getattr(bom, 'fg_warehouse', None)
    
    result = {
        'bom': bom_name,
        'item': bom.item,
        'docstatus': bom.docstatus,
        'is_active': bom.is_active,
        'target_fg_warehouse': target_warehouse,
        'status': 'OK',
        'issues': [],
        'warnings': []
    }
    
    # Check 1: BOM status
    if bom.docstatus != 1:
        result['warnings'].append(f"BOM is in DRAFT state (docstatus={bom.docstatus})")
        print(f"⚠️  BOM Status: DRAFT")
    else:
        print(f"✅ BOM Status: SUBMITTED")
    
    if not bom.is_active:
        result['warnings'].append("BOM is INACTIVE")
        print(f"⚠️  BOM Active: NO")
    else:
        print(f"✅ BOM Active: YES")
    
    # Check 2: Target FG Warehouse
    if not target_warehouse:
        result['issues'].append("Missing target_fg_warehouse on BOM")
        print(f"❌ Target FG Warehouse: NOT SET")
    else:
        print(f"✅ Target FG Warehouse: {target_warehouse}")
    
    # Check 3: BOM Items - source_warehouse
    print(f"\nChecking {len(bom.items)} BOM items:")
    print("-" * 80)
    
    items_missing_wh = []
    for idx, item in enumerate(bom.items, 1):
        if not item.source_warehouse:
            items_missing_wh.append({
                'idx': idx,
                'item_code': item.item_code,
                'item_name': item.item_name
            })
            print(f"  ❌ Item {idx}: {item.item_code} - source_warehouse NOT SET")
        else:
            print(f"  ✅ Item {idx}: {item.item_code} - {item.source_warehouse}")
    
    if items_missing_wh:
        result['issues'].append(f"{len(items_missing_wh)} items missing source_warehouse")
        result['missing_items'] = items_missing_wh
    else:
        print(f"\n✅ All {len(bom.items)} items have source_warehouse")
    
    # Check 4: Operations - workstation (optional but recommended)
    if bom.operations:
        print(f"\nChecking {len(bom.operations)} operations:")
        print("-" * 80)
        
        ops_missing_ws = []
        for idx, op in enumerate(bom.operations, 1):
            if not op.workstation:
                ops_missing_ws.append({
                    'idx': idx,
                    'operation': op.operation
                })
                print(f"  ⚠️  Op {idx}: {op.operation} - workstation NOT SET")
            else:
                print(f"  ✅ Op {idx}: {op.operation} - {op.workstation}")
        
        if ops_missing_ws:
            result['warnings'].append(f"{len(ops_missing_ws)} operations missing workstation")
            result['missing_workstations'] = ops_missing_ws
        else:
            print(f"\n✅ All {len(bom.operations)} operations have workstation")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if result['issues']:
        print(f"❌ ISSUES: {len(result['issues'])}")
        for issue in result['issues']:
            print(f"   - {issue}")
    else:
        print(f"✅ No critical issues")
    
    if result['warnings']:
        print(f"⚠️  WARNINGS: {len(result['warnings'])}")
        for warning in result['warnings']:
            print(f"   - {warning}")
    else:
        print(f"✅ No warnings")
    
    # Overall status
    if result['issues']:
        result['status'] = 'FAIL'
        print(f"\n🔴 BOM {bom_name}: VERIFICATION FAILED")
    elif result['warnings']:
        result['status'] = 'PASS_WITH_WARNINGS'
        print(f"\n🟡 BOM {bom_name}: PASSED WITH WARNINGS")
    else:
        result['status'] = 'PASS'
        print(f"\n🟢 BOM {bom_name}: VERIFICATION PASSED")
    
    return result


def verify_all_boms():
    """
    Verify all BOMs in the system
    
    Returns: dict with overall summary
    """
    print("=" * 80)
    print("BOM DATA VERIFICATION REPORT")
    print("=" * 80)
    
    # Get all BOMs
    all_boms = frappe.get_all('BOM', 
        fields=['name', 'item', 'docstatus', 'is_active'],
        order_by='name'
    )
    
    print(f"\nTotal BOMs found: {len(all_boms)}")
    
    # Categorize BOMs
    submitted_boms = [b for b in all_boms if b.docstatus == 1]
    draft_boms = [b for b in all_boms if b.docstatus == 0]
    
    print(f"  - Submitted: {len(submitted_boms)}")
    print(f"  - Draft: {len(draft_boms)}")
    
    # Verify all BOMs
    results = []
    passed = []
    passed_with_warnings = []
    failed = []
    
    print("\n" + "=" * 80)
    print("VERIFYING ALL BOMs")
    print("=" * 80)
    
    for bom in all_boms:
        result = verify_bom(bom.name)
        results.append(result)
        
        if result['status'] == 'PASS':
            passed.append(bom.name)
        elif result['status'] == 'PASS_WITH_WARNINGS':
            passed_with_warnings.append(bom.name)
        else:
            failed.append(bom.name)
    
    # Overall Summary
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    print(f"Total BOMs: {len(all_boms)}")
    print(f"  ✅ Passed: {len(passed)}")
    print(f"  🟡 Passed with Warnings: {len(passed_with_warnings)}")
    print(f"  🔴 Failed: {len(failed)}")
    
    if failed:
        print(f"\n🔴 FAILED BOMs ({len(failed)}):")
        for bom_name in failed:
            print(f"   - {bom_name}")
    
    if passed_with_warnings:
        print(f"\n🟡 BOMs WITH WARNINGS ({len(passed_with_warnings)}):")
        for bom_name in passed_with_warnings[:10]:  # Show first 10
            print(f"   - {bom_name}")
        if len(passed_with_warnings) > 10:
            print(f"   ... and {len(passed_with_warnings) - 10} more")
    
    # Detailed report for failed BOMs
    if failed:
        print("\n" + "=" * 80)
        print("DETAILED ISSUES FOR FAILED BOMs")
        print("=" * 80)
        
        for result in results:
            if result['status'] == 'FAIL':
                print(f"\n{result['bom']}:")
                for issue in result['issues']:
                    print(f"  ❌ {issue}")
                if result.get('missing_items'):
                    print(f"  Items missing source_warehouse:")
                    for item in result['missing_items'][:5]:  # Show first 5
                        print(f"    - {item['item_code']}")
                    if len(result['missing_items']) > 5:
                        print(f"    ... and {len(result['missing_items']) - 5} more")
    
    # Summary report
    summary = {
        'total': len(all_boms),
        'submitted': len(submitted_boms),
        'draft': len(draft_boms),
        'passed': len(passed),
        'passed_with_warnings': len(passed_with_warnings),
        'failed': len(failed),
        'failed_boms': failed,
        'results': results
    }
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if draft_boms:
        print(f"\n1. 📝 Review and submit {len(draft_boms)} draft BOMs")
    
    if failed:
        print(f"\n2. 🔧 Fix issues in {len(failed)} failed BOMs:")
        print(f"   - Set fg_warehouse on BOM")
        print(f"   - Set source_warehouse on all BOM items")
    
    if passed_with_warnings:
        print(f"\n3. ⚠️  Consider fixing warnings in {len(passed_with_warnings)} BOMs:")
        print(f"   - Set workstation on operations (recommended)")
    
    if passed and not failed and not passed_with_warnings:
        print(f"\n✅ All {len(passed)} BOMs are ready for production!")
    
    return summary


def fix_bom_items(bom_name, default_warehouse="Stores - TPL", submit=True):
    """
    Fix BOM items by setting source_warehouse to default
    
    Args:
        bom_name: BOM name to fix
        default_warehouse: Default warehouse to set
        submit: Whether to submit after fixing
    
    Returns: True if successful
    """
    print("\n" + "=" * 80)
    print(f"FIXING BOM ITEMS: {bom_name}")
    print("=" * 80)
    
    try:
        bom = frappe.get_doc('BOM', bom_name)
    except Exception as e:
        print(f"❌ BOM not found: {bom_name}")
        return False
    
    if bom.docstatus == 1:
        print(f"⚠️  BOM is submitted. Cannot modify.")
        print(f"   Please cancel BOM first or use amended version")
        return False
    
    # Fix items
    fixed_count = 0
    for item in bom.items:
        if not item.source_warehouse:
            item.source_warehouse = default_warehouse
            fixed_count += 1
            print(f"  ✓ Set source_warehouse = {default_warehouse} for {item.item_code}")
    
    if fixed_count == 0:
        print(f"✅ All items already have source_warehouse")
    else:
        bom.save()
        print(f"\n✅ Fixed {fixed_count} items in BOM {bom_name}")
        
        if submit:
            bom.submit()
            print(f"✅ BOM submitted: {bom_name}")
    
    return True


def fix_all_draft_boms(default_warehouse="Raw Material Stores - TPL", target_warehouse="Finish Goods Stores - TPL"):
    """
    Fix all draft BOMs by setting default warehouses
    
    Args:
        default_warehouse: Default source_warehouse for items
        target_warehouse: Default target_fg_warehouse for BOM
    
    Returns: dict with results
    """
    print("=" * 80)
    print("FIXING ALL DRAFT BOMs")
    print("=" * 80)
    
    # Get draft BOMs
    draft_boms = frappe.get_all('BOM', 
        filters={'docstatus': 0},
        fields=['name', 'item']
    )
    
    print(f"\nFound {len(draft_boms)} draft BOMs")
    
    results = {
        'fixed': [],
        'failed': [],
        'already_ok': []
    }
    
    for bom in draft_boms:
        print(f"\nProcessing: {bom.name}")
        
        try:
            bom_doc = frappe.get_doc('BOM', bom.name)
            
            # Fix target_fg_warehouse if missing
            if not getattr(bom_doc, 'target_fg_warehouse', None):
                bom_doc.target_fg_warehouse = target_warehouse
                print(f"  ✓ Set target_fg_warehouse = {target_warehouse}")
            
            # Fix BOM items
            fixed_items = 0
            for item in bom_doc.items:
                if not item.source_warehouse:
                    item.source_warehouse = default_warehouse
                    fixed_items += 1
            
            # Save
            bom_doc.save()
            
            if fixed_items > 0:
                print(f"  ✓ Fixed {fixed_items} items with source_warehouse = {default_warehouse}")
                results['fixed'].append(bom.name)
            else:
                print(f"  ✅ BOM already has all required fields")
                results['already_ok'].append(bom.name)
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            results['failed'].append({'bom': bom.name, 'error': str(e)})
    
    # Summary
    print("\n" + "=" * 80)
    print("FIX SUMMARY")
    print("=" * 80)
    print(f"  ✅ Fixed: {len(results['fixed'])}")
    print(f"  ✅ Already OK: {len(results['already_ok'])}")
    print(f"  ❌ Failed: {len(results['failed'])}")
    
    if results['failed']:
        print(f"\nFailed BOMs:")
        for fail in results['failed']:
            print(f"  - {fail['bom']}: {fail['error']}")
    
    return results
