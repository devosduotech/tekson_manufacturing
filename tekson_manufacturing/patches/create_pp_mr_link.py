"""
Create custom_production_plan field on Material Request doctype.
Runs on app install/update.
"""

import frappe


def execute():
    if not frappe.db.exists("Custom Field", {"dt": "Material Request", "fieldname": "custom_production_plan"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Material Request",
            "fieldname": "custom_production_plan",
            "label": "Production Plan",
            "fieldtype": "Link",
            "options": "Production Plan",
            "insert_after": "schedule_date",
        }).insert()
        print("Created custom_production_plan on Material Request")
