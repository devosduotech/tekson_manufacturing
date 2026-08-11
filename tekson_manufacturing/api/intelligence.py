import frappe

@frappe.whitelist()
def planner_kpis(planned_date=None):
    from tekson_manufacturing.intelligence.analytics.planner.kpi import get_planner_kpis
    return get_planner_kpis(planned_date)

@frappe.whitelist()  
def planner_calendar(days=7):
    from tekson_manufacturing.intelligence.analytics.planner.calendar import get_calendar
    return get_calendar(days)

@frappe.whitelist()
def planner_exceptions():
    from tekson_manufacturing.intelligence.analytics.planner.exceptions import get_exceptions
    return get_exceptions()

@frappe.whitelist()
def planner_workload():
    from tekson_manufacturing.intelligence.analytics.planner.workload import get_dept_load, get_fg_mix
    return {"dept_load": get_dept_load(), "fg_mix": get_fg_mix()}

@frappe.whitelist()
def stores_kpis(planned_date=None):
    from tekson_manufacturing.intelligence.analytics.stores.kpi import get_stores_kpis
    return get_stores_kpis(planned_date)
