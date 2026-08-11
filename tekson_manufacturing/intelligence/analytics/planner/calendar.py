"""Production Calendar - WOs by date"""
import frappe
from frappe.utils import today, add_days, getdate


@frappe.whitelist()
def get_calendar(from_date=None, to_date=None, days=7):
    """Return WOs grouped by planned_start_date"""
    if not from_date:
        from_date = today()
    if not to_date:
        to_date = add_days(from_date, days)
    
    wos = frappe.get_all("Work Order", {
        "docstatus": 1,
        "status": ["!=", "Completed"],
        "planned_start_date": ["between", [from_date, to_date]]
    }, ["name", "production_item", "planned_start_date", "status", "qty"],
    order_by="planned_start_date")
    
    calendar = {}
    for wo in wos:
        date_key = str(wo.planned_start_date)[:10]
        if date_key not in calendar:
            calendar[date_key] = {"count": 0, "items": 0, "wos": []}
        calendar[date_key]["count"] += 1
        calendar[date_key]["items"] += wo.qty or 0
        calendar[date_key]["wos"].append({
            "name": wo.name,
            "item": wo.production_item,
            "status": wo.status,
            "qty": wo.qty
        })
    
    return {"from_date": str(from_date), "to_date": str(to_date), "calendar": calendar}
