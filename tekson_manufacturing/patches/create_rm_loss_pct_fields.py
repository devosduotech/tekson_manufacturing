"""
Patch to create RM Loss % Custom Fields on BOM Item and Material Request Item
"""

import frappe


def execute():
    # BOM Item - RM Loss %
    if not frappe.db.exists("Custom Field", {"dt": "BOM Item", "fieldname": "custom_rm_loss_pct"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "BOM Item",
            "fieldname": "custom_rm_loss_pct",
            "label": "RM Loss %",
            "fieldtype": "Percent",
            "precision": "2",
            "default": "0",
            "insert_after": "source_warehouse",
            "description": "Expected raw material loss % during manufacturing (cutting, trimming, forming wastage). Applied during Material Request generation.",
        }).insert(ignore_permissions=True)
        frappe.db.commit()
        print("Created Custom Field: BOM Item.custom_rm_loss_pct")

    # Material Request Item - RM Loss %
    if not frappe.db.exists("Custom Field", {"dt": "Material Request Item", "fieldname": "custom_rm_loss_pct"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Material Request Item",
            "fieldname": "custom_rm_loss_pct",
            "label": "RM Loss %",
            "fieldtype": "Percent",
            "precision": "2",
            "default": "0",
            "insert_after": "from_warehouse",
            "description": "RM Loss % from BOM Item - editable for adjustments during Material Request creation.",
        }).insert(ignore_permissions=True)
        frappe.db.commit()
        print("Created Custom Field: Material Request Item.custom_rm_loss_pct")

    # Material Request Item - RM Loss Qty
    if not frappe.db.exists("Custom Field", {"dt": "Material Request Item", "fieldname": "custom_rm_loss_qty"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Material Request Item",
            "fieldname": "custom_rm_loss_qty",
            "label": "RM Loss Qty",
            "fieldtype": "Float",
            "precision": "3",
            "default": "0",
            "insert_after": "custom_rm_loss_pct",
            "description": "Calculated loss quantity (Required Qty × RM Loss %). For traceability and reporting.",
        }).insert(ignore_permissions=True)
        frappe.db.commit()
        print("Created Custom Field: Material Request Item.custom_rm_loss_qty")

    print("All RM Loss % Custom Fields created successfully")
