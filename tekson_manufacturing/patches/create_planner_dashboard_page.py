"""Create Planner Dashboard Page on install"""
import frappe

def execute():
    if not frappe.db.exists("Page", "planner-dashboard"):
        page = frappe.get_doc({
            "doctype": "Page",
            "name": "planner-dashboard",
            "page_name": "planner-dashboard",
            "title": "Planner Dashboard",
            "module": "Tekson Manufacturing",
            "roles": [
                {"role": "Manufacturing User"},
                {"role": "System Manager"},
                {"role": "All"}
            ],
            "script": "tekson_manufacturing/tekson_manufacturing/page/planner_dashboard/planner_dashboard.js",
            "standard": "Yes",
            "system_page": 0
        })
        page.insert()
        frappe.db.commit()
        print("Created Planner Dashboard page")
    else:
        print("Planner Dashboard page already exists")
