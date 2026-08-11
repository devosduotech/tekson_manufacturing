"""Department Workload & FG Product Mix"""
import frappe
from collections import Counter


@frappe.whitelist()
def get_dept_load(planned_date=None):
    """Return department-wise WO count"""
    filters = {"docstatus": 1, "status": ["!=", "Completed"]}
    if planned_date:
        filters["planned_start_date"] = planned_date
    
    wos = frappe.get_all("Work Order", filters, ["wip_warehouse", "name", "qty"])
    
    dept_count = Counter()
    dept_qty = Counter()
    
    for wo in wos:
        if wo.wip_warehouse:
            dept_name = wo.wip_warehouse.split(" - ")[0]
            dept_count[dept_name] += 1
            dept_qty[dept_name] += wo.qty or 0
    
    return {
        "dept_count": dict(dept_count.most_common()),
        "dept_qty": dict(dept_qty.most_common())
    }


@frappe.whitelist()
def get_fg_mix(planned_date=None):
    """Return FG product mix by quantity"""
    filters = {"docstatus": 1, "status": ["!=", "Completed"]}
    if planned_date:
        filters["planned_start_date"] = planned_date
    
    wos = frappe.get_all("Work Order", filters, ["production_item", "qty"])
    
    mix = Counter()
    for wo in wos:
        mix[wo.production_item] += wo.qty or 0
    
    return dict(mix.most_common(10))
