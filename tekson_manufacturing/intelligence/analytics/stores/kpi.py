"""Stores KPIs - Material Health Metrics"""
import frappe
from frappe.utils import today


@frappe.whitelist()
def get_stores_kpis(planned_date=None):
    """Return stores health KPIs"""
    if not planned_date:
        planned_date = today()
    
    # Pending Material Requests
    pending_mrs = frappe.db.count("Material Request", {
        "docstatus": 1,
        "status": ["!=", "Cancelled"],
        "material_request_type": "Material Transfer"
    })
    
    # Pending Pick Lists
    pending_pick_lists = frappe.db.count("Pick List", {
        "docstatus": 1,
        "status": "Open"
    })
    
    # WIP Transfers Today
    wip_transfers = frappe.db.count("Stock Entry", {
        "docstatus": 1,
        "stock_entry_type": "Material Transfer for Manufacture",
        "posting_date": planned_date
    })
    
    # Material Shortages (Job Cards waiting for material)
    material_short = frappe.db.count("Job Card", {
        "docstatus": 1,
        "status": "Open",
        "custom_material_status": ["in", ["Waiting for Material", "Material Short"]]
    })
    
    return {
        "pending_mrs": pending_mrs,
        "pending_pick_lists": pending_pick_lists,
        "wip_transfers": wip_transfers,
        "material_short": material_short
    }
