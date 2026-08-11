"""Planner Dashboard KPIs — Production Health"""

import frappe
from frappe.utils import flt, today, add_days, getdate
from typing import Dict, Any


@frappe.whitelist()
def get_planner_kpis(planned_date=None) -> Dict[str, Any]:
    if not planned_date:
        planned_date = today()
    
    filters = {"docstatus": 1, "status": ["!=", "Cancelled"], "planned_start_date": ["<=", add_days(planned_date, 7)]}
    
    all_wo = frappe.get_all("Work Order", filters,
        ["name", "production_item", "qty", "status", "planned_start_date", "actual_end_date"])
    
    total = len(all_wo)
    completed = len([w for w in all_wo if w.status == "Completed"])
    in_process = len([w for w in all_wo if w.status not in ("Completed", "Draft", "Not Started")])
    
    on_time = sum(1 for w in all_wo if w.status == "Completed" and w.actual_end_date
                  and getdate(w.actual_end_date) <= getdate(w.planned_start_date))
    on_time_pct = round((on_time / completed * 100) if completed > 0 else 0, 1)
    
    pending_pp = frappe.db.count("Production Plan", {"docstatus": 1, "status": "Submitted"})
    
    return {
        "total_wo": total, "completed_wo": completed, "in_process_wo": in_process,
        "pending_pp": pending_pp, "on_time_pct": on_time_pct,
        "planned_vs_actual": {"planned": total, "completed": completed},
    }
