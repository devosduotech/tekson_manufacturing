"""
BOM Review and Export Utility

Reviews existing BOMs and exports to CSV for analysis.

Usage:
    # Review all BOMs
    bench --site [site] execute tekson_manufacturing.scripts.bom_review.run_review
    
    # Export BOMs to CSV
    bench --site [site] execute tekson_manufacturing.scripts.bom_review.export_boms --kwargs '{"file_path": "/home/karthic/bom_export.csv", "item_code": null}'
    
    # Export specific BOM
    bench --site [site] execute tekson_manufacturing.scripts.bom_review.export_boms --kwargs '{"file_path": "/home/karthic/bom_r215.csv", "item_code": "R215"}'
    
    # Analyze BOM warehouse references
    bench --site [site] execute tekson_manufacturing.scripts.bom_review.analyze_warehouses
"""

import frappe
from frappe import _
from datetime import datetime
import csv


def run_review():
    """
    Review all BOMs
    
    Returns: dict with BOM summary
    """
    print("=" * 80)
    print("BOM REVIEW")
    print("=" * 80)
    print(f"Date: {datetime.now()}")
    print()
    
    # Get all BOMs
    boms = frappe.get_all('BOM',
        filters={'docstatus': 1},
        fields=['name', 'item', 'item_name', 'quantity', 'company', 'creation'],
        order_by='creation desc'
    )
    
    print(f"Total Active BOMs: {len(boms)}")
    print()
    
    # Analyze BOMs
    with_operations = 0
    without_operations = 0
    total_operations = 0
    
    for bom in boms:
        bom_doc = frappe.get_doc('BOM', bom.name)
        op_count = len(bom_doc.operations) if bom_doc.operations else 0
        total_operations += op_count
        
        if op_count > 0:
            with_operations += 1
        else:
            without_operations += 1
    
    # Print summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"BOMs with operations: {with_operations}")
    print(f"BOMs without operations: {without_operations}")
    print(f"Total operations across all BOMs: {total_operations}")
    print(f"Average operations per BOM: {total_operations / len(boms) if boms else 0:.1f}")
    print()
    
    # Show recent BOMs
    print("=" * 80)
    print("RECENT BOMs (Last 20):")
    print("=" * 80)
    
    for bom in boms[:20]:
        bom_doc = frappe.get_doc('BOM', bom.name)
        op_count = len(bom_doc.operations) if bom_doc.operations else 0
        
        print(f"\n{bom.name}:")
        print(f"  Item: {bom.item} - {bom.item_name}")
        print(f"  Quantity: {bom.quantity}")
        print(f"  Company: {bom.company}")
        print(f"  Operations: {op_count}")
        print(f"  Created: {bom.creation}")
        
        # Show operations
        if bom_doc.operations:
            print("  Operations:")
            for i, op in enumerate(bom_doc.operations[:5], 1):
                print(f"    {i}. {op.operation} @ {op.workstation or 'No Workstation'}")
                if hasattr(op, 'workstation') and op.workstation:
                    try:
                        ws = frappe.get_doc('Workstation', op.workstation)
                        print(f"       → Plant Floor: {ws.plant_floor}, WIP: {ws.warehouse or 'Not set'}")
                    except:
                        print(f"       → Workstation not found")
            if len(bom_doc.operations) > 5:
                print(f"    ... and {len(bom_doc.operations) - 5} more")
    
    print()
    print("=" * 80)
    
    return {
        'total': len(boms),
        'with_operations': with_operations,
        'without_operations': without_operations,
        'total_operations': total_operations
    }


def export_boms(file_path, item_code=None):
    """
    Export BOMs to CSV file
    
    Args:
        file_path: Path to output CSV file
        item_code: Filter by item code (optional)
    
    Usage:
        bench execute tekson_manufacturing.scripts.bom_review.export_boms --kwargs '{"file_path": "/home/karthic/bom_export.csv"}'
    """
    print("=" * 80)
    print("BOM EXPORT")
    print("=" * 80)
    print(f"Output: {file_path}")
    if item_code:
        print(f"Filter: {item_code}")
    print()
    
    # Get BOMs
    filters = {'docstatus': 1}
    if item_code:
        filters['item'] = item_code
    
    boms = frappe.get_all('BOM',
        filters=filters,
        fields=['name', 'item', 'item_name', 'quantity', 'company', 'creation'],
        order_by='creation desc'
    )
    
    print(f"Found {len(boms)} BOMs to export")
    print()
    
    # Prepare CSV data
    rows = []
    
    for bom in boms:
        bom_doc = frappe.get_doc('BOM', bom.name)
        
        # Get BOM items
        bom_items = []
        for item in bom_doc.items:
            bom_items.append({
                'item_code': item.item_code,
                'item_name': item.item_name or '',
                'qty': item.qty,
                'uom': item.uom,
                'source_warehouse': item.source_warehouse or '',
                'allow_alternative_item': item.allow_alternative_item or 0
            })
        
        # Get operations
        operations = []
        for i, op in enumerate(bom_doc.operations or [], 1):
            workstation = op.workstation or ''
            plant_floor = ''
            wip_warehouse = ''
            
            if workstation:
                try:
                    ws = frappe.get_doc('Workstation', workstation)
                    plant_floor = ws.plant_floor or ''
                    wip_warehouse = ws.warehouse or ''
                except:
                    pass
            
            operations.append({
                'sequence_id': op.sequence_id or i,
                'operation': op.operation,
                'workstation': workstation,
                'plant_floor': plant_floor,
                'wip_warehouse': wip_warehouse,
                'hour_rate': op.hour_rate or 0,
                'time_in_mins': op.time_in_mins or 0
            })
        
        # Create row for each BOM (with items and operations as JSON for reference)
        import json
        
        row = {
            'bom_name': bom.name,
            'item_code': bom.item,
            'item_name': bom.item_name or '',
            'quantity': bom.quantity,
            'company': bom.company,
            'creation': str(bom.creation),
            'total_items': len(bom_items),
            'total_operations': len(operations),
            'bom_items_json': json.dumps(bom_items),
            'operations_json': json.dumps(operations)
        }
        
        rows.append(row)
        
        # Print progress
        print(f"Exported: {bom.name} ({len(operations)} operations, {len(bom_items)} items)")
    
    # Write CSV
    if rows:
        fieldnames = [
            'bom_name', 'item_code', 'item_name', 'quantity', 'company', 'creation',
            'total_items', 'total_operations', 'bom_items_json', 'operations_json'
        ]
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print()
        print("=" * 80)
        print(f"✅ Successfully exported {len(rows)} BOMs to {file_path}")
        print("=" * 80)
        print()
        print("CSV Columns:")
        print("  - bom_name: BOM document name")
        print("  - item_code: Item being manufactured")
        print("  - item_name: Item description")
        print("  - quantity: BOM quantity")
        print("  - company: Company")
        print("  - creation: Creation date")
        print("  - total_items: Number of raw materials")
        print("  - total_operations: Number of operations")
        print("  - bom_items_json: Raw materials details (JSON)")
        print("  - operations_json: Operations details with workstation/plant_floor (JSON)")
        print()
        print("To analyze in spreadsheet:")
        print("  1. Open CSV in Excel/LibreOffice")
        print("  2. Use text-to-columns on JSON fields if needed")
        print("  3. Or use Python/JSON tools to parse")
        
        return {'success': True, 'count': len(rows), 'file_path': file_path}
    else:
        print("⚠️  No BOMs found to export")
        return {'success': False, 'count': 0}


def analyze_warehouses():
    """
    Analyze warehouse references in BOMs
    
    Identifies BOMs that may need updates based on warehouse structure.
    """
    print("=" * 80)
    print("BOM WAREHOUSE ANALYSIS")
    print("=" * 80)
    print(f"Date: {datetime.now()}")
    print()
    
    # Get all BOMs
    boms = frappe.get_all('BOM',
        filters={'docstatus': 1},
        fields=['name', 'item'],
        order_by='creation desc'
    )
    
    print(f"Analyzing {len(boms)} BOMs...")
    print()
    
    # Track warehouse usage
    warehouse_usage = {}
    bom_issues = []
    
    for bom in boms:
        bom_doc = frappe.get_doc('BOM', bom.name)
        
        # Check BOM items for source warehouse
        for item in bom_doc.items:
            wh = item.source_warehouse
            if wh:
                if wh not in warehouse_usage:
                    warehouse_usage[wh] = []
                warehouse_usage[wh].append(bom.name)
        
        # Check operations for workstation warehouse alignment
        if bom_doc.operations:
            for op in bom_doc.operations:
                if op.workstation:
                    try:
                        ws = frappe.get_doc('Workstation', op.workstation)
                        ws_pf = ws.plant_floor
                        ws_wh = ws.warehouse
                        
                        # Check if workstation has plant_floor set
                        if not ws_pf:
                            bom_issues.append({
                                'bom': bom.name,
                                'item': bom.item,
                                'issue': f"Workstation '{op.workstation}' has no plant_floor",
                                'operation': op.operation
                            })
                        
                        # Check if workstation warehouse matches plant_floor
                        if ws_wh and ws_pf:
                            expected_wh = f"WIP-{ws_pf} - TPL"
                            if ws_wh != expected_wh:
                                bom_issues.append({
                                    'bom': bom.name,
                                    'item': bom.item,
                                    'issue': f"Workstation warehouse mismatch",
                                    'operation': op.operation,
                                    'workstation': op.workstation,
                                    'current_warehouse': ws_wh,
                                    'expected_warehouse': expected_wh
                                })
                    except Exception as e:
                        bom_issues.append({
                            'bom': bom.name,
                            'item': bom.item,
                            'issue': f"Workstation not found: {op.workstation}",
                            'operation': op.operation
                        })
    
    # Print warehouse usage
    print("=" * 80)
    print("WAREHOUSE USAGE IN BOM ITEMS:")
    print("=" * 80)
    
    for wh in sorted(warehouse_usage.keys()):
        boms_using = warehouse_usage[wh]
        print(f"\n{wh}: {len(boms_using)} BOMs")
        for bom_name in boms_using[:5]:
            print(f"  - {bom_name}")
        if len(boms_using) > 5:
            print(f"  ... and {len(boms_using) - 5} more")
    
    # Print issues
    print()
    print("=" * 80)
    print(f"ISSUES FOUND: {len(bom_issues)}")
    print("=" * 80)
    
    if bom_issues:
        # Group by issue type
        by_type = {}
        for issue in bom_issues:
            issue_type = issue['issue']
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append(issue)
        
        for issue_type, issues in by_type.items():
            print(f"\n{issue_type}: {len(issues)} occurrences")
            for issue in issues[:3]:
                print(f"  - {issue['bom']} ({issue['item']})")
                if 'operation' in issue:
                    print(f"    Operation: {issue['operation']}")
            if len(issues) > 3:
                print(f"  ... and {len(issues) - 3} more")
    else:
        print("✅ No issues found!")
    
    print()
    print("=" * 80)
    
    return {
        'warehouse_usage': warehouse_usage,
        'issues': bom_issues,
        'total_boms': len(boms)
    }


if __name__ == '__main__':
    run_review()
