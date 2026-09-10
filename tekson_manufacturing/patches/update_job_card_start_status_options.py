"""
Update custom_start_status Select field options on Job Card.

Reduces from 7 values to 5:
Awaiting Material, Awaiting Previous Operation, Ready to Start, In Progress, Completed

Runs on app install/update.
"""

import frappe


def execute():
    new_options = "Awaiting Material\nAwaiting Previous Operation\nReady to Start\nIn Progress\nCompleted"

    cf = frappe.db.get_value(
        "Custom Field",
        {"dt": "Job Card", "fieldname": "custom_start_status"},
        ["name", "options"],
        as_dict=True,
    )

    if not cf:
        print("Custom Field custom_start_status not found on Job Card — skipping")
        return

    if cf.options.strip() == new_options.strip():
        print("custom_start_status options already up to date")
        return

    frappe.db.set_value("Custom Field", cf.name, "options", new_options)
    frappe.clear_cache(doctype="Job Card")
    print(f"Updated custom_start_status options to: {new_options}")
