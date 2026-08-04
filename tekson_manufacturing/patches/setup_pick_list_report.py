"""
One-time setup: Create Material Transfer Pick List report in system.
Run once on VM after deploy:
    bench --site teksons.dev execute tekson_manufacturing.patches.setup_pick_list_report.create_report
"""

import frappe
import json
import os


def create_report():
    """Create the Material Transfer Pick List Report DocType if not exists"""
    
    report_name = "Material Transfer Pick List"
    
    if frappe.db.exists("Report", report_name):
        print(f"Report '{report_name}' already exists — skipping")
        return
    
    # Load report JSON
    json_path = os.path.join(
        os.path.dirname(__file__), "..",
        "reports", "material_transfer_pick_list", "material_transfer_pick_list.json"
    )
    
    if not os.path.exists(json_path):
        print(f"Report JSON not found at {json_path}")
        return
    
    with open(json_path) as f:
        report_data = json.load(f)
    
    report = frappe.get_doc(report_data)
    report.insert(ignore_permissions=True)
    frappe.db.commit()
    
    print(f"Report '{report_name}' created successfully")


def create_workspace():
    """Create Tekson Manufacturing Workspace if not exists"""
    
    workspace_name = "Tekson Manufacturing"
    
    if frappe.db.exists("Workspace", workspace_name):
        print(f"Workspace '{workspace_name}' exists — skipping")
        return
    
    json_path = os.path.join(
        os.path.dirname(__file__), "..",
        "workspace", "tekson_manufacturing", "tekson_manufacturing.json"
    )
    
    if not os.path.exists(json_path):
        print(f"Workspace JSON not found at {json_path}")
        return
    
    with open(json_path) as f:
        workspace_data = json.load(f)
    
    ws = frappe.get_doc(workspace_data)
    ws.insert(ignore_permissions=True)
    frappe.db.commit()
    
    print(f"Workspace '{workspace_name}' created successfully")


def setup_all():
    """Create both report and workspace"""
    create_report()
    create_workspace()
    print("\nSetup complete. Clear cache and refresh your browser.")
