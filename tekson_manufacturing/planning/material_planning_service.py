"""
Daily Material Planning Service

Generates Material Requests for stores — grouped by department WIP.
Business Rules: MP-001 through MP-005.
"""

import frappe
from frappe import _
import math
from datetime import date
from typing import List, Dict, Any, Optional


@frappe.whitelist()
def generate_daily_material_requests(production_plan: str = None, planned_date: str = None) -> Dict[str, Any]:
    """
    Generate Material Requests for WOs starting on a given date.
    
    Args:
        production_plan: PP name — if provided, only considers WOs from this PP
        planned_date: Planned start date (YYYY-MM-DD) — defaults to today
    
    Returns:
        dict with created_mrs (list of MR names), total_items, errors
    """
    if not planned_date:
        planned_date = date.today().strftime("%Y-%m-%d")
    
    # MP-001: Find incomplete WOs for the date
    wo_filters = {
        "docstatus": 1,
        "status": ["!=", "Completed"],
        "planned_start_date": planned_date,
    }
    if production_plan:
        wo_filters["production_plan"] = production_plan
    
    wos = frappe.get_all("Work Order", wo_filters,
        ["name", "bom_no", "wip_warehouse", "qty", "planned_start_date"])
    
    if not wos:
        return {"created_mrs": [], "total_items": 0, "message": _("No Work Orders found for {0}").format(planned_date)}
    
    # MP-002: Calculate requirements per department WIP
    dept_items = {}
    for wo in wos:
        if not wo.bom_no:
            continue
        target_wh = wo.wip_warehouse
        if not target_wh:
            continue
        
        for item in _get_raw_bom_items(wo.bom_no):
            # Only raw materials and BOF items
            source_wh = item.get("source_warehouse") or ""
            if "Raw Material" not in source_wh and "BOF" not in source_wh:
                continue
            
            required_qty = (item["qty"] * wo.qty) / (frappe.db.get_value("BOM", wo.bom_no, "quantity") or 1)
            
            # MP-002: Deduct stock already in target WIP
            in_wip = frappe.db.get_value("Bin",
                {"item_code": item["item_code"], "warehouse": target_wh},
                "actual_qty") or 0
            
            shortage = max(0, required_qty - in_wip)
            if shortage <= 0:
                continue
            
            key = (target_wh, item["item_code"], source_wh)
            if target_wh not in dept_items:
                dept_items[target_wh] = {}
            if key not in dept_items[target_wh]:
                dept_items[target_wh][key] = {
                    "item_code": item["item_code"],
                    "item_name": item.get("item_name", ""),
                    "qty": 0,
                    "from_warehouse": source_wh,
                    "uom": item.get("uom", "Nos"),
                }
            dept_items[target_wh][key]["qty"] += shortage
    
    if not dept_items:
        return {"created_mrs": [], "total_items": 0, "message": _("All materials already in WIP for {0}").format(planned_date)}
    
    # MP-003, MP-004, MP-005: Create/update MRs per department WIP
    created = []
    
    for target_wh, items in dept_items.items():
        dept = target_wh.split(" - ")[0].replace("WIP-", "")
        
        # MP-005: Check for existing draft MR
        existing_mr = frappe.db.exists("Material Request", {
            "docstatus": 0,
            "schedule_date": planned_date,
            "custom_department_wip": target_wh,
        })
        
        if existing_mr:
            mr = frappe.get_doc("Material Request", existing_mr)
            mr.set("items", [])
        else:
            mr = frappe.get_doc({
                "doctype": "Material Request",
                "material_request_type": "Material Transfer",
                "schedule_date": planned_date,
                "custom_department_wip": target_wh,
                "title": f"Daily MR - {dept} - {planned_date}",
            })
        
        for item_key, item_data in items.items():
            mr.append("items", {
                "item_code": item_data["item_code"],
                "item_name": item_data.get("item_name", ""),
                "qty": math.ceil(item_data["qty"]) if _needs_whole_qty(item_data["item_code"]) else round(item_data["qty"], 3),
                "from_warehouse": item_data["from_warehouse"],
                "warehouse": target_wh,
                "uom": item_data.get("uom", "Nos"),
                "schedule_date": planned_date,
            })
        
        if existing_mr:
            mr.save()
        else:
            mr.insert()
        
        created.append({"name": mr.name, "department_wip": target_wh, "items": len(mr.items)})
    
    return {
        "created_mrs": [c["name"] for c in created],
        "total_items": sum(c["items"] for c in created),
        "planned_date": planned_date,
        "details": created,
    }


def _get_raw_bom_items(bom_no: str) -> List[Dict]:
    """Get BOM items filtered to raw materials and BOF items only"""
    items = frappe.get_all("BOM Item",
        {"parent": bom_no, "source_warehouse": ["in", 
            frappe.get_all("Warehouse", {"warehouse_name": ["in", ["Raw Material Stores", "BOF Stores"]]}, pluck="name")]},
        ["item_code", "item_name", "qty", "uom", "source_warehouse"])
    
    if not items:
        # Fallback: get all items and filter in Python
        all_items = frappe.get_all("BOM Item", {"parent": bom_no},
            ["item_code", "item_name", "qty", "uom", "source_warehouse"])
        return [i for i in all_items if i.source_warehouse and 
                ("Raw Material" in i.source_warehouse or "BOF" in i.source_warehouse)]
    
    return items


def _needs_whole_qty(item_code: str) -> bool:
    """Check if item's UOM requires whole number"""
    uom = frappe.db.get_value("Item", item_code, "stock_uom")
    if uom:
        return bool(frappe.db.get_value("UOM", uom, "must_be_whole_number"))
    return False
