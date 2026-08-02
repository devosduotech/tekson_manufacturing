"""
Workstation Review and Cleanup Utility

Reviews all workstations for correct plant_floor assignments.

Usage:
    # Review all workstations
    bench --site [site] execute tekson_manufacturing.scripts.workstation_review.run_review
    
    # Update workstation plant_floor
    bench --site [site] execute tekson_manufacturing.scripts.workstation_review.update_workstation --kwargs '{"workstation": "Workstation Name", "plant_floor": "W"}'
    
    # Bulk update from CSV
    bench --site [site] execute tekson_manufacturing.scripts.workstation_review.bulk_update --kwargs '{"file_path": "/path/to/workstations.csv"}'
"""

import frappe
from frappe import _
from datetime import datetime


# Expected workstation to plant_floor mapping
# Update this based on your actual shop floor layout
EXPECTED_MAPPING = {
    # W Department
    'W Department': 'W',
    'Shearing Machine': 'W',
    
    # CNC Department
    'CNC Department': 'CNC',
    'CNC-01': 'CNC',
    'CNC-02': 'CNC',
    
    # RA Department
    'RA Department': 'RA',
    'CO2 Welding': 'RA',
    'Wiremesh Rolling': 'RA',
    'Wiremesh U Piece Assembly': 'RA',
    'Flattening': 'RA',
    'Folding': 'RA',
    'Manual Rolling & Cutting': 'RA',
    'Manual Dressing': 'RA',
    'Washing Tank': 'RA',
    'Spray Painting': 'RA',
    'Paint Booth 2': 'RA',
    'Spot Welding': 'RA',
    'Dryer': 'RA',
    
    # Ralu In Department
    'Ralu In Department': 'Ralu In',
    'Aluminium Bar Cutting': 'Ralu In',
    'Brazing Furnace': 'Ralu In',
    'Buffing Machine': 'Ralu In',
    'Component Washing Machine': 'Ralu In',
    'Core Fixing': 'Ralu In',
    'Core Jig': 'Ralu In',
    'Core Tightening': 'Ralu In',
    'Cut To Length': 'Ralu In',
    'Deburring Machine': 'Ralu In',
    'Drying Furnace': 'Ralu In',
    'Drying': 'Ralu In',
    'Fin Forming & Cutting': 'Ralu In',
    'Fluxing Machine': 'Ralu In',
    'Manual Brazing': 'Ralu In',
    'Manual Washing Tank': 'Ralu In',
    
    # Ralu Weld Department
    'Ralu Weld Department': 'Ralu Weld',
    'Aluminium Pipe Cutting': 'Ralu Weld',
    'Crimping Machine': 'Ralu Weld',
    'Drying Oven': 'Ralu Weld',
    'Final Assembly': 'Ralu Weld',
    'Flushing & Airblowing': 'Ralu Weld',
    'Helicoil & Tapping Machine': 'Ralu Weld',
    'Leak Test': 'Ralu Weld',
    'Machine Washing': 'Ralu Weld',
    'Mig Welding': 'Ralu Weld',
    'OTG Mig Welding': 'Ralu Weld',
    'Paint Booth 1': 'Ralu Weld',
    'Robo Mig Welding': 'Ralu Weld',
    'Tig Welding': 'Ralu Weld',
    'Vacuum Machine (For Final Assembly Cleaning)': 'Ralu Weld',
    'Weld_Deburring Machine': 'Ralu Weld',
    
    # RP Department
    'RP Department': 'RP',
    'RP-26_Hydraulic Press': 'RP',
    'Corner Cutting, Punching, Folding & Blanking': 'RP',
    'Sr. No. Punching': 'RP',
}


def run_review():
    """
    Review all workstations for plant_floor assignments
    
    Returns: dict with review summary
    """
    print("=" * 80)
    print("WORKSTATION REVIEW")
    print("=" * 80)
    print(f"Date: {datetime.now()}")
    print()
    
    # Get all workstations
    workstations = frappe.get_all('Workstation',
        fields=['name', 'plant_floor', 'warehouse'],
        order_by='name'
    )
    
    print(f"Total Workstations: {len(workstations)}")
    print()
    
    # Categorize
    with_plant_floor = []
    without_plant_floor = []
    mismatched = []
    
    for ws in workstations:
        if not ws.plant_floor:
            without_plant_floor.append(ws)
        elif ws.name in EXPECTED_MAPPING and ws.plant_floor != EXPECTED_MAPPING[ws.name]:
            mismatched.append(ws)
        else:
            with_plant_floor.append(ws)
    
    # Print summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ With plant_floor: {len(with_plant_floor)}")
    print(f"❌ Without plant_floor: {len(without_plant_floor)}")
    print(f"⚠️  Mismatched (differs from expected): {len(mismatched)}")
    print()
    
    # Print workstations without plant_floor
    if without_plant_floor:
        print("=" * 80)
        print("WORKSTATIONS WITHOUT PLANT FLOOR:")
        print("=" * 80)
        for ws in sorted(without_plant_floor, key=lambda x: x.name):
            print(f"  ❌ {ws.name}")
        print()
    
    # Print mismatched workstations
    if mismatched:
        print("=" * 80)
        print("MISMATCHED WORKSTATIONS:")
        print("=" * 80)
        for ws in sorted(mismatched, key=lambda x: x.name):
            expected = EXPECTED_MAPPING.get(ws.name, 'Unknown')
            print(f"  ⚠️  {ws.name}")
            print(f"      Current: {ws.plant_floor}, Expected: {expected}")
        print()
    
    # Group by plant_floor
    print("=" * 80)
    print("WORKSTATIONS BY PLANT FLOOR:")
    print("=" * 80)
    
    by_pf = {}
    for ws in workstations:
        pf = ws.plant_floor or '(Not Set)'
        if pf not in by_pf:
            by_pf[pf] = []
        by_pf[pf].append(ws.name)
    
    for pf in sorted(by_pf.keys()):
        ws_list = by_pf[pf]
        print(f"\n{pf} ({len(ws_list)} workstations):")
        for ws_name in sorted(ws_list)[:10]:
            print(f"  - {ws_name}")
        if len(ws_list) > 10:
            print(f"  ... and {len(ws_list) - 10} more")
    
    print()
    print("=" * 80)
    
    return {
        'total': len(workstations),
        'with_plant_floor': len(with_plant_floor),
        'without_plant_floor': len(without_plant_floor),
        'mismatched': len(mismatched),
        'without_list': [ws.name for ws in without_plant_floor],
        'mismatched_list': [{'name': ws.name, 'current': ws.plant_floor, 'expected': EXPECTED_MAPPING.get(ws.name)} for ws in mismatched]
    }


def update_workstation(workstation, plant_floor):
    """
    Update a single workstation's plant_floor
    
    Args:
        workstation: Workstation name
        plant_floor: Plant floor code (e.g., 'W', 'RA', 'CNC')
    
    Usage:
        bench execute tekson_manufacturing.scripts.workstation_review.update_workstation --kwargs '{"workstation": "Workstation Name", "plant_floor": "W"}'
    """
    print(f"Updating {workstation}...")
    
    try:
        ws = frappe.get_doc('Workstation', workstation)
        ws.plant_floor = plant_floor
        
        # Also update warehouse if not set
        if not ws.warehouse:
            warehouse = f"WIP-{plant_floor} - TPL"
            if frappe.db.exists('Warehouse', warehouse):
                ws.warehouse = warehouse
                print(f"  Warehouse set to: {warehouse}")
        
        ws.save()
        frappe.db.commit()
        
        print(f"✅ Successfully updated {workstation}")
        print(f"  Plant Floor: {plant_floor}")
        print(f"  Warehouse: {ws.warehouse or 'Not set'}")
        
        return {'success': True, 'workstation': workstation, 'plant_floor': plant_floor}
        
    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error: {str(e)}")
        return {'success': False, 'workstation': workstation, 'error': str(e)}


def bulk_update(file_path):
    """
    Bulk update workstations from CSV file
    
    CSV format:
    workstation_name,plant_floor
    
    Args:
        file_path: Path to CSV file
    
    Usage:
        bench execute tekson_manufacturing.scripts.workstation_review.bulk_update --kwargs '{"file_path": "/path/to/workstations.csv"}'
    """
    print("=" * 80)
    print("BULK WORKSTATION UPDATE")
    print("=" * 80)
    
    import csv
    
    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            updates = list(reader)
        
        print(f"Found {len(updates)} workstations to update")
        print()
        
        success = 0
        errors = 0
        
        for i, row in enumerate(updates, 1):
            ws_name = row.get('workstation_name') or row.get('workstation')
            pf = row.get('plant_floor')
            
            if not ws_name or not pf:
                print(f"[{i}/{len(updates)}] ⚠️  Skipped: Missing data")
                errors += 1
                continue
            
            result = update_workstation(ws_name, pf)
            
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


def auto_assign_plant_floor(dry_run=True):
    """
    Auto-assign plant_floor to workstations based on name patterns
    
    Args:
        dry_run: If True, only preview changes
    
    Usage:
        # Preview
        bench execute tekson_manufacturing.scripts.workstation_review.auto_assign_plant_floor
        
        # Execute
        bench execute tekson_manufacturing.scripts.workstation_review.auto_assign_plant_floor --kwargs '{"dry_run": False}'
    """
    print("=" * 80)
    print("AUTO-ASSIGN PLANT FLOOR")
    print("=" * 80)
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTION'}")
    print()
    
    # Get workstations without plant_floor
    workstations = frappe.get_all('Workstation',
        filters={'plant_floor': ['is', 'not set']},
        fields=['name'],
        order_by='name'
    )
    
    print(f"Found {len(workstations)} workstations without plant_floor")
    print()
    
    updates = []
    
    for ws in workstations:
        ws_name = ws.name
        plant_floor = None
        
        # Try to match from expected mapping
        if ws_name in EXPECTED_MAPPING:
            plant_floor = EXPECTED_MAPPING[ws_name]
        else:
            # Try to infer from name patterns
            ws_name_upper = ws_name.upper()
            
            # Check for department keywords
            if ' W ' in ws_name_upper or ws_name_upper.startswith('W '):
                plant_floor = 'W'
            elif ' CNC ' in ws_name_upper or ws_name_upper.startswith('CNC'):
                plant_floor = 'CNC'
            elif ' RA ' in ws_name_upper or ws_name_upper.startswith('RA '):
                plant_floor = 'RA'
            elif ' RALU IN ' in ws_name_upper or 'RALUIN' in ws_name_upper:
                plant_floor = 'Ralu In'
            elif ' RALU WELD ' in ws_name_upper or 'RALUWELD' in ws_name_upper:
                plant_floor = 'Ralu Weld'
            elif ' RP ' in ws_name_upper or ws_name_upper.startswith('RP'):
                plant_floor = 'RP'
        
        if plant_floor:
            updates.append({
                'workstation': ws_name,
                'plant_floor': plant_floor
            })
            
            if dry_run:
                print(f"  📋 {ws_name} → {plant_floor}")
    
    if not dry_run and updates:
        print(f"\nExecuting {len(updates)} updates...")
        for update in updates:
            try:
                ws = frappe.get_doc('Workstation', update['workstation'])
                ws.plant_floor = update['plant_floor']
                
                # Set warehouse
                warehouse = f"WIP-{update['plant_floor']} - TPL"
                if frappe.db.exists('Warehouse', warehouse):
                    ws.warehouse = warehouse
                
                ws.save()
                print(f"  ✅ {update['workstation']} → {update['plant_floor']}")
            except Exception as e:
                print(f"  ❌ {update['workstation']}: {str(e)}")
        
        frappe.db.commit()
    
    print()
    print("=" * 80)
    print(f"SUMMARY: {len(updates)} workstations would be updated")
    print("=" * 80)
    
    if dry_run:
        print("\nTo execute, run:")
        print("  bench execute tekson_manufacturing.scripts.workstation_review.auto_assign_plant_floor --kwargs '{\"dry_run\": False}'")
    
    return {'count': len(updates), 'updates': updates}


if __name__ == '__main__':
    run_review()
