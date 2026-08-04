"""
BOM Operations Sequence ID Checker

Checks all BOMs for operation sequence ID (idx) issues

Usage on VM:
    cd ~/frappe-bench
    bench --site teksons.dev execute tekson_manufacturing.scripts.check_bom_operations.verify_operations
"""

import frappe


def verify_operations():
    """Check all BOMs for operation sequence ID issues"""
    print("=" * 80)
    print("BOM OPERATIONS SEQUENCE ID CHECK")
    print("=" * 80)
    
    # Get all BOMs
    all_boms = frappe.get_all('BOM', 
        fields=['name', 'docstatus'],
        order_by='name'
    )
    
    print(f"\nTotal BOMs: {len(all_boms)}")
    
    boms_with_ops = 0
    total_operations = 0
    ops_with_issues = []
    
    for bom in all_boms:
        bom_doc = frappe.get_doc('BOM', bom.name)
        
        if bom_doc.operations:
            boms_with_ops += 1
            
            for op in bom_doc.operations:
                total_operations += 1
                if op.idx == 0 or not op.idx:
                    ops_with_issues.append({
                        'bom': bom.name,
                        'operation': op.operation,
                        'idx': op.idx,
                        'workstation_type': op.workstation_type
                    })
    
    print(f"BOMs with operations: {boms_with_ops}")
    print(f"Total operations: {total_operations}")
    
    if ops_with_issues:
        print(f"\n⚠️  OPERATIONS WITH IDX = 0: {len(ops_with_issues)}")
        print("=" * 80)
        for issue in ops_with_issues:
            print(f"  BOM: {issue['bom']}")
            print(f"    Operation: {issue['operation']}")
            print(f"    idx: {issue['idx']}")
            print(f"    Workstation Type: {issue['workstation_type'] or 'Not Set'}")
            print()
    else:
        print(f"\n✅ ALL OPERATIONS HAVE VALID IDX > 0")
    
    # Show operation sequence for sample BOMs
    print("\n" + "=" * 80)
    print("OPERATION SEQUENCE SAMPLE (First 15 BOMs)")
    print("=" * 80)
    
    for bom in all_boms[:15]:
        bom_doc = frappe.get_doc('BOM', bom.name)
        if bom_doc.operations:
            print(f"\n{bom.name}:")
            for op in bom_doc.operations:
                ws_type = op.workstation_type or 'N/A'
                print(f"  idx={op.idx}: {op.operation} (Type: {ws_type})")
    
    # Summary by workstation type
    print("\n" + "=" * 80)
    print("OPERATIONS BY WORKSTATION TYPE")
    print("=" * 80)
    
    ws_type_counts = {}
    for bom in all_boms:
        bom_doc = frappe.get_doc('BOM', bom.name)
        if bom_doc.operations:
            for op in bom_doc.operations:
                ws_type = op.workstation_type or 'Not Set'
                ws_type_counts[ws_type] = ws_type_counts.get(ws_type, 0) + 1
    
    for ws_type, count in sorted(ws_type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ws_type}: {count} operations")
    
    return {
        'total_boms': len(all_boms),
        'boms_with_ops': boms_with_ops,
        'total_operations': total_operations,
        'issues': ops_with_issues
    }


def check_single_bom(bom_name):
    """Check operations for a specific BOM"""
    print("=" * 80)
    print(f"OPERATION CHECK: {bom_name}")
    print("=" * 80)
    
    try:
        bom = frappe.get_doc('BOM', bom_name)
    except Exception as e:
        print(f"❌ BOM not found: {bom_name}")
        return
    
    print(f"\nBOM: {bom.name}")
    print(f"Item: {bom.item}")
    print(f"Status: {'Submitted' if bom.docstatus == 1 else 'Draft'}")
    
    if not bom.operations:
        print("\n⚠️  No operations defined")
        return
    
    print(f"\nOperations ({len(bom.operations)}):")
    print("-" * 80)
    
    for idx, op in enumerate(bom.operations, 1):
        status = "✅" if op.idx and op.idx > 0 else "❌"
        print(f"{status} Op {idx}:")
        print(f"    Operation: {op.operation}")
        print(f"    idx: {op.idx or 0}")
        print(f"    Workstation: {op.workstation or 'Not Set'}")
        print(f"    Workstation Type: {op.workstation_type or 'Not Set'}")
        print(f"    Operation Time: {op.time_in_mins or 0} mins")
        print()
