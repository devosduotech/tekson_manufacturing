"""
Patch to create Target FG Warehouse 2 (demand-driven split routing) on BOM
and BOM Bulk Creator.

BOM.target_fg_warehouse_2 is the secondary target FG warehouse. When a
consuming BOM Item row's source_warehouse matches this warehouse, the
Production Plan routes that demand into a separate Work Order that outputs
here, instead of combining it with the primary destination.
"""

import frappe


def execute():
    insert_after = "quantity"
    if frappe.get_meta("BOM").has_field("target_fg_warehouse"):
        insert_after = "target_fg_warehouse"

    _create_field(
        dt="BOM",
        fieldname="target_fg_warehouse_2",
        label="Target FG Warehouse 2",
        fieldtype="Link",
        options="Warehouse",
        insert_after=insert_after,
        description=(
            "Secondary target FG warehouse for split routing. When a consuming BOM Item's "
            "source_warehouse matches this warehouse, the Production Plan creates a separate "
            "Work Order that outputs here. Leave empty for single-destination output."
        ),
    )

    _create_field(
        dt="BOM Bulk Creator",
        fieldname="target_fg_warehouse_2",
        label="Target FG Warehouse 2",
        fieldtype="Link",
        options="Warehouse",
        insert_after="target_fg_warehouse",
        description=(
            "Secondary target FG warehouse copied to every generated BOM "
            "(BOM.target_fg_warehouse_2) for demand-driven split routing."
        ),
    )


def _create_field(dt, fieldname, label, fieldtype, options=None, insert_after=None, description=None):
    if frappe.db.exists("Custom Field", {"dt": dt, "fieldname": fieldname}):
        return

    frappe.get_doc(
        {
            "doctype": "Custom Field",
            "dt": dt,
            "fieldname": fieldname,
            "label": label,
            "fieldtype": fieldtype,
            "options": options,
            "insert_after": insert_after,
            "description": description,
        }
    ).insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"Created Custom Field: {dt}.{fieldname}")
