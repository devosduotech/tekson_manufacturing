"""Planner Exceptions — delayed, blocked, overdue WOs"""

import frappe
from frappe.utils import today, getdate


@frappe.whitelist()
def get_exceptions():
    """Return WOs needing planner attention"""
    result = {"overdue": [], "delayed": [], "blocked": [], "material_short": [], "dependency_wait": []}
    
    # Overdue: past planned_start_date, not completed
    overdue = frappe.get_all("Work Order", {
        "docstatus": 1, "status": ["!=", "Completed"],
        "planned_start_date": ["<", today()]
    }, ["name", "production_item", "planned_start_date", "status"], limit=20)
    result["overdue"] = [{"name": w.name, "item": w.production_item, "date": str(w.planned_start_date)[:10]} for w in overdue]
    
    # Blocked: JCs that can't start
    blocked = frappe.get_all("Job Card", {
        "docstatus": 1, "status": "Open",
        "custom_readiness_status": ["in", ["Blocked", "Waiting for Material", "Waiting for Previous Operation"]]
    }, ["name", "work_order", "operation", "custom_readiness_status", "custom_blocked_by"], limit=20)
    result["blocked"] = [{"name": j.name, "wo": j.work_order, "op": j.operation, "reason": j.custom_blocked_by} for j in blocked]
    
    # Material Short
    short = frappe.get_all("Job Card", {
        "docstatus": 1, "status": "Open",
        "custom_material_status": ["in", ["Waiting for Material", "Material Short"]]
    }, ["name", "work_order", "operation", "custom_material_status"], limit=20)
    result["material_short"] = [{"name": j.name, "wo": j.work_order, "op": j.operation} for j in short]
    
    # Dependency Waiting
    dep = frappe.get_all("Job Card", {
        "docstatus": 1, "status": "Open",
        "custom_readiness_status": "Waiting for Previous Operation"
    }, ["name", "work_order", "operation"], limit=20)
    result["dependency_wait"] = [{"name": j.name, "wo": j.work_order, "op": j.operation} for j in dep]
    
    return result
