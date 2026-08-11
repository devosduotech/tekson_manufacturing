"""Planner Exceptions - Overdue, Blocked, Material Short"""
import frappe
from frappe.utils import today, getdate


@frappe.whitelist()
def get_exceptions(planned_date=None):
    """Return exceptions for planned_date with severity classification"""
    if not planned_date:
        planned_date = today()
    
    # 1. Overdue WOs
    overdue_wo = frappe.get_all("Work Order", {
        "docstatus": 1,
        "status": ["!=", "Completed"],
        "planned_start_date": ["<", planned_date]
    }, ["name", "production_item", "planned_start_date", "status"], limit=10)
    
    overdue = []
    severity = {"critical": 0, "high": 0, "medium": 0}
    
    for wo in overdue_wo:
        days = (getdate(planned_date) - getdate(wo.planned_start_date)).days
        overdue.append({
            "name": wo.name,
            "item": wo.production_item,
            "date": str(wo.planned_start_date)[:10],
            "days_overdue": days
        })
        # Severity classification
        if days > 5:
            severity["critical"] += 1
        elif days > 1:
            severity["high"] += 1
        else:
            severity["medium"] += 1
    
    # 2. Blocked Job Cards
    blocked_jcs = frappe.get_all("Job Card", {
        "docstatus": 1,
        "status": "Open",
        "custom_readiness_status": ["in", ["Blocked", "Waiting for Material", "Waiting for Previous Operation"]]
    }, ["name", "work_order", "operation", "custom_readiness_status", "custom_blocked_by"], limit=10)
    
    blocked = [{
        "name": jc.name,
        "wo": jc.work_order,
        "op": jc.operation,
        "reason": jc.custom_blocked_by or jc.custom_readiness_status
    } for jc in blocked_jcs]
    
    # 3. Material Shortage
    short_jcs = frappe.get_all("Job Card", {
        "docstatus": 1,
        "status": "Open",
        "custom_material_status": ["in", ["Waiting for Material", "Material Short"]]
    }, ["name", "work_order", "operation"], limit=10)
    
    material_short = [{
        "name": j.name,
        "wo": j.work_order,
        "op": j.operation
    } for j in short_jcs]
    
    # 4. Waiting for Dependencies
    dep_jcs = frappe.get_all("Job Card", {
        "docstatus": 1,
        "status": "Open",
        "custom_readiness_status": "Waiting for Previous Operation"
    }, ["name", "work_order", "operation"], limit=10)
    
    dependency_wait = [{
        "name": j.name,
        "wo": j.work_order,
        "op": j.operation
    } for j in dep_jcs]
    
    return {
        "summary": {
            "overdue": len(overdue_wo),
            "blocked": len(blocked_jcs),
            "material_short": len(short_jcs),
            "dependency_wait": len(dep_jcs)
        },
        "severity": severity,
        "overdue": overdue,
        "blocked": blocked,
        "material_short": material_short,
        "dependency_wait": dependency_wait
    }
