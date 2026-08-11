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
            source_wh = item.get("source_warehouse") or ""
            if not _is_source_warehouse(source_wh):
                continue
            
            # Target: item's operation → JC's wip_warehouse, fallback to WO's
            target_wh = wo.wip_warehouse
            if item.get("operation"):
                jc_wh = frappe.db.get_value("Job Card",
                    {"work_order": wo.name, "operation": item["operation"]}, "wip_warehouse")
                if jc_wh:
                    target_wh = jc_wh
            
            required_qty = (item["qty"] * wo.qty) / (frappe.db.get_value("BOM", wo.bom_no, "quantity") or 1)
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
        # MP-005: Find existing draft MR with items for this target warehouse
        existing = frappe.db.sql("""
            SELECT mr.name FROM `tabMaterial Request` mr
            INNER JOIN `tabMaterial Request Item` mri ON mri.parent = mr.name
            WHERE mr.docstatus = 0 AND mr.schedule_date = %s
            AND mri.warehouse = %s
            LIMIT 1
        """, (planned_date, target_wh), as_dict=True)
        
        if existing:
            mr = frappe.get_doc("Material Request", existing[0].name)
            mr.set("items", [])
        else:
            mr = frappe.get_doc({
                "doctype": "Material Request",
                "material_request_type": "Material Transfer",
                "schedule_date": planned_date,
                "custom_production_plan": production_plan,
            })
        
        for item_key, item_data in items.items():
            mr.append("items", {
                "item_code": item_data["item_code"],
                "item_name": item_data.get("item_name", ""),
                "qty": math.ceil(item_data["qty"]),
                "from_warehouse": item_data["from_warehouse"],
                "warehouse": target_wh,
                "uom": item_data.get("uom", "Nos"),
                "schedule_date": planned_date,
            })
        
        if existing:
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
    """Get BOM items that are raw materials or BOF items only"""
    all_items = frappe.get_all("BOM Item", {"parent": bom_no},
        ["item_code", "item_name", "qty", "uom", "source_warehouse", "operation"])
    
    # Filter: only items from Raw Material Stores or BOF Stores
    return [i for i in all_items if _is_source_warehouse(i.source_warehouse)]


def _is_source_warehouse(warehouse: str) -> bool:
    """Check if warehouse is a valid source (Raw Material Stores or BOF Stores)"""
    if not warehouse:
        return False
    wh_name = frappe.db.get_value("Warehouse", warehouse, "warehouse_name") or ""
    return wh_name in ("Raw Material Stores", "BOF Stores")
