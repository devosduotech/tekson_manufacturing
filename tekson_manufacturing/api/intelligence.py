"""Manufacturing Intelligence API"""
import frappe

@frappe.whitelist()
def planner_kpis(planned_date=None):
    from tekson_manufacturing.intelligence.analytics.planner.kpi import get_planner_kpis
    return get_planner_kpis(planned_date)
