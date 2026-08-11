"""Planner KPIs - Production Health Metrics"""
import frappe
from frappe.utils import flt, today, add_days, getdate


@frappe.whitelist()
def get_planner_kpis(planned_date=None):
    """Return production health KPIs for given date"""
    if not planned_date:
        planned_date = today()
    
    # All WOs up to 7 days from planned_date
    filters = {
        "docstatus": 1,
        "status": ["!=", "Cancelled"],
        "planned_start_date": ["<=", add_days(planned_date, 7)]
    }
    
    all_wo = frappe.get_all("Work Order", filters,
        ["name", "production_item", "qty", "status", "planned_start_date", "actual_end_date"])
    
    total = len(all_wo)
    completed = len([w for w in all_wo if w.status == "Completed"])
    in_process = len([w for w in all_wo if w.status not in ("Completed", "Draft", "Not Started")])
    
    # On-time delivery
    on_time = sum(1 for w in all_wo if w.status == "Completed" and w.actual_end_date
                  and getdate(w.actual_end_date) <= getdate(w.planned_start_date))
    on_time_pct = round((on_time / completed * 100) if completed > 0 else 0, 1)
    
    # Pending Production Plans
    pending_pp = frappe.db.count("Production Plan", {"docstatus": 1, "status": "Submitted"})
    
    # Production Readiness: % of today's WOs where first operation can start
    today_wos = frappe.get_all("Work Order", {
        "docstatus": 1,
        "planned_start_date": planned_date,
        "status": ["!=", "Completed"]
    }, pluck="name")
    
    ready_count = 0
    if today_wos:
        ready_count = frappe.db.count("Job Card", {
            "work_order": ["in", today_wos],
            "docstatus": ["!=", 2],
            "sequence_id": 1,
            "custom_can_start_operation": 1
        })
    
    readiness_pct = round((ready_count / len(today_wos) * 100) if today_wos else 0, 1)
    
    return {
        "total_wo": total,
        "completed_wo": completed,
        "in_process_wo": in_process,
        "pending_pp": pending_pp,
        "on_time_pct": on_time_pct,
        "readiness_pct": readiness_pct,
        "readiness_detail": {"ready": ready_count, "total": len(today_wos)},
        "planned_vs_actual": {"planned": total, "completed": completed}
    }
