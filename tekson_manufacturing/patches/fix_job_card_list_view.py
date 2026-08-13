"""
Fix Job Card List View Settings
Ensures Status column is visible and Plant Floor is included
"""

import frappe
import json

def execute():
    """Fix Job Card List View Settings"""
    try:
        lv = frappe.get_doc('List View Settings', 'Job Card')
        
        # Set proper columns with Status first
        lv.fields = json.dumps([
            {"fieldname": "status", "label": "Status"},
            {"fieldname": "operation", "label": "Operation"},
            {"fieldname": "for_quantity", "label": "For Qty"},
            {"fieldname": "custom_plant_floor", "label": "Plant Floor"},
            {"fieldname": "work_order", "label": "Work Order"},
            {"fieldname": "production_item", "label": "Production Item"}
        ])
        lv.total_fields = '6'
        lv.save()
        
        frappe.clear_cache()
        print("✅ Job Card List View updated successfully!")
        
    except Exception as e:
        print(f"⚠️  Could not update List View Settings: {e}")
        # Don't fail the migration, just warn
        pass
