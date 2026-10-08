"""
Patch to update RM Loss % Custom Fields on Material Request Item
- Add Qty as per BOM field
- Make RM Loss % and RM Loss Qty read-only
"""

import frappe


def execute():
    # Update Material Request Item - RM Loss % (make read-only)
    cf = frappe.db.get_value("Custom Field", {"dt": "Material Request Item", "fieldname": "custom_rm_loss_pct"}, "name")
    if cf:
        doc = frappe.get_doc("Custom Field", cf)
        doc.read_only = 1
        doc.description = "RM Loss % from BOM Item (read-only)"
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        print("Updated Custom Field: Material Request Item.custom_rm_loss_pct (read-only)")

    # Update Material Request Item - RM Loss Qty (make read-only)
    cf = frappe.db.get_value("Custom Field", {"dt": "Material Request Item", "fieldname": "custom_rm_loss_qty"}, "name")
    if cf:
        doc = frappe.get_doc("Custom Field", cf)
        doc.read_only = 1
        doc.description = "Calculated loss quantity (read-only)"
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        print("Updated Custom Field: Material Request Item.custom_rm_loss_qty (read-only)")

    # Material Request Item - Qty as per BOM (new field)
    if not frappe.db.exists("Custom Field", {"dt": "Material Request Item", "fieldname": "custom_bom_qty"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Material Request Item",
            "fieldname": "custom_bom_qty",
            "label": "Qty as per BOM",
            "fieldtype": "Float",
            "precision": "3",
            "default": "0",
            "insert_after": "from_warehouse",
            "read_only": 1,
            "description": "Theoretical quantity from BOM without RM Loss % (read-only)",
        }).insert(ignore_permissions=True)
        frappe.db.commit()
        print("Created Custom Field: Material Request Item.custom_bom_qty")

    print("RM Loss % Custom Fields updated successfully")