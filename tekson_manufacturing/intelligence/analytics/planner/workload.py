"""Department Workload & Capacity"""

import frappe
from collections import Counter


@frappe.whitelist()
def get_dept_load(planned_date=None):
    """Return department workload — WOs for planned_date"""
    filters = {"docstatus": 1, "status": ["!=", "Completed"]}
    if planned_date:
        filters["planned_start_date"] = planned_date
    
    wos = frappe.get_all("Work Order", filters=filters, fields=["wip_warehouse", "name", "qty"])
    
    dept = Counter()
    total_qty = Counter()
    for wo in wos:
        if wo.wip_warehouse:
            dept_name = wo.wip_warehouse.split(" - ")[0]
            dept[dept_name] += 1
            total_qty[dept_name] += wo.qty or 0
    
    return {
        "dept_count": dict(dept.most_common()),
        "dept_qty": dict(total_qty.most_common()),
    }


@frappe.whitelist()
def get_fg_mix(planned_date=None):
    """Return FG product mix — WOs per production_item for planned_date"""
    filters = {"docstatus": 1, "status": ["!=", "Completed"]}
    if planned_date:
        filters["planned_start_date"] = planned_date
    
    wos = frappe.get_all("Work Order", filters=filters, fields=["production_item", "qty"])
    
    mix = Counter()
    for wo in wos:
        mix[wo.production_item] += wo.qty or 0
    
    return dict(mix.most_common(10))
