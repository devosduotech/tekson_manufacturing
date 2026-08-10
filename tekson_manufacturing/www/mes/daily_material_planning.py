"""
Daily Material Planning Page

Access: /app/daily-material-planning
"""

import frappe
from frappe import _


def get_context(context):
    """No context needed — page is client-side"""
    context.title = "Daily Material Planning"
    return context


@frappe.whitelist()
def search_production_plans(txt):
    """Search submitted Production Plans for dropdown"""
    pps = frappe.get_all("Production Plan",
        {"docstatus": 1, "name": ["like", f"%{txt}%"]},
        ["name", "status"],
        limit=20, order_by="creation desc")
    return pps
