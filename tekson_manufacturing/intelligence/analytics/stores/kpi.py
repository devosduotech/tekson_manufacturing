"""Stores Dashboard KPIs"""

import frappe
from frappe.utils import today


@frappe.whitelist()
def get_stores_kpis(planned_date=None):
    if not planned_date:
        planned_date = today()
    
    mr_count = frappe.db.count("Material Request", {
        "docstatus": 1, "status": ["!=", "Stopped"],
        "schedule_date": planned_date
    })
    
    wos = frappe.get_all("Work Order", {
        "docstatus": 1, "planned_start_date": planned_date,
        "status": ["!=", "Completed"]
    }, ["name", "wip_warehouse"])
    
    dept_breakdown = {}
    items_short = 0
    
    for wo in wos:
        if not wo.wip_warehouse: continue
        bom_no = frappe.db.get_value("Work Order", wo.name, "bom_no")
        if not bom_no: continue
        for item in frappe.get_all("BOM Item", {"parent": bom_no}, ["item_code", "source_warehouse"]):
            wh = item.source_warehouse or ""
            if "Raw Material" not in wh and "BOF" not in wh:
                continue
            stock = frappe.db.get_value("Bin", {"item_code": item.item_code, "warehouse": wo.wip_warehouse}, "actual_qty") or 0
            if stock <= 0:
                items_short += 1
                dept = wo.wip_warehouse.split(" - ")[0]
                dept_breakdown[dept] = dept_breakdown.get(dept, 0) + 1
    
    return {"mr_count": mr_count, "items_short": items_short, "dept_breakdown": dept_breakdown}
