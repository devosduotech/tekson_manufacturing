"""
Manufacturing Intelligence — Analytics Layer

Shared KPI calculations used by dashboards and reports.
Rule: Dashboards never calculate KPIs directly.
      Reports never calculate KPIs directly.
      All KPI logic lives here, called once.
"""

import frappe
from frappe.utils import flt, today, add_days, getdate
from typing import Dict, List, Any


@frappe.whitelist()
def get_planner_kpis(planned_date=None) -> Dict[str, Any]:
    """
    Planner Dashboard KPIs.
    
    Returns:
        total_wo, completed_wo, in_process_wo, pending_release,
        on_time_pct, planned_vs_actual, wo_list
    """
    if not planned_date:
        planned_date = today()
    
    filters = {"docstatus": 1, "status": ["!=", "Cancelled"], "planned_start_date": ["<=", add_days(planned_date, 7)]}
    
    all_wo = frappe.get_all("Work Order", filters,
        ["name", "production_item", "qty", "status", "planned_start_date", "actual_end_date"],
        order_by="planned_start_date")
    
    total = len(all_wo)
    completed = len([w for w in all_wo if w.status == "Completed"])
    in_process = len([w for w in all_wo if w.status not in ("Completed", "Draft", "Not Started")])
    
    # On-time: completed and actual_end_date <= planned_start_date + buffer
    on_time = 0
    for w in all_wo:
        if w.status == "Completed" and w.actual_end_date:
            if getdate(w.actual_end_date) <= getdate(w.planned_start_date):
                on_time += 1
    
    on_time_pct = round((on_time / completed * 100) if completed > 0 else 0, 1)
    
    # Pending PP releases
    pending_pp = frappe.db.count("Production Plan", {"docstatus": 1, "status": "Submitted"})
    
    return {
        "total_wo": total,
        "completed_wo": completed,
        "in_process_wo": in_process,
        "pending_pp": pending_pp,
        "on_time_pct": on_time_pct,
        "planned_vs_actual": {"planned": total, "completed": completed},
    }


@frappe.whitelist()
def get_stores_kpis(planned_date=None) -> Dict[str, Any]:
    """
    Stores Dashboard KPIs.
    
    Returns:
        pending_transfers, items_short, dept_breakdown, mr_count
    """
    if not planned_date:
        planned_date = today()
    
    # Pending Material Requests for today
    mr_count = frappe.db.count("Material Request", {
        "docstatus": 1, "status": ["!=", "Stopped"],
        "schedule_date": planned_date
    })
    
    # Items with zero stock in WIP for planned WOs
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
    
    return {
        "mr_count": mr_count,
        "items_short": items_short,
        "dept_breakdown": dept_breakdown,
    }
