"""
Patch to update RM Loss % Custom Fields on Material Request Item
- Add Qty as per BOM field
- Make RM Loss % and RM Loss Qty read-only (via client script)
"""

import frappe


def execute():
    # Update Material Request Item - RM Loss % (allow saving to DB, client script makes UI read-only)
    cf = frappe.db.get_value("Custom Field", {"dt": "Material Request Item", "fieldname": "custom_rm_loss_pct"}, "name")
    if cf:
        doc = frappe.get_doc("Custom Field", cf)
        doc.read_only = 0
        doc.description = "RM Loss % from BOM Item (read-only via client script)"
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        print("Updated Custom Field: Material Request Item.custom_rm_loss_pct (read_only=0 for DB save)")

    # Update Material Request Item - RM Loss Qty (allow saving to DB)
    cf = frappe.db.get_value("Custom Field", {"dt": "Material Request Item", "fieldname": "custom_rm_loss_qty"}, "name")
    if cf:
        doc = frappe.get_doc("Custom Field", cf)
        doc.read_only = 0
        doc.description = "Calculated loss quantity (read-only via client script)"
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        print("Updated Custom Field: Material Request Item.custom_rm_loss_qty (read_only=0 for DB save)")

    # Material Request Item - Qty as per BOM (new field) - NOT read_only in DB, UI will handle
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
            "read_only": 0,  # Allow saving to DB, client script will make UI read-only
            "description": "Theoretical quantity from BOM without RM Loss %",
        }).insert(ignore_permissions=True)
        frappe.db.commit()
        print("Created Custom Field: Material Request Item.custom_bom_qty")

    print("RM Loss % Custom Fields updated successfully")