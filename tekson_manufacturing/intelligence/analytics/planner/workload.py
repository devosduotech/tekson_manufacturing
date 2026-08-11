"""Department Workload & Capacity"""

import frappe
from collections import Counter


@frappe.whitelist()
def get_dept_load():
    """Return department workload — active WOs per department"""
    wos = frappe.get_all("Work Order", {
        "docstatus": 1, "status": ["!=", "Completed"]
    }, ["wip_warehouse", "name", "qty"])
    
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
def get_fg_mix():
    """Return FG product mix — count of WOs per production_item"""
    wos = frappe.get_all("Work Order", {
        "docstatus": 1, "status": ["!=", "Completed"]
    }, ["production_item", "qty"])
    
    mix = Counter()
    for wo in wos:
        mix[wo.production_item] += wo.qty or 0
    
    return dict(mix.most_common(10))
