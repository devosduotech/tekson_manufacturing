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
def search_production_plans(txt=None):
    """Search submitted Production Plans for dropdown"""
    return frappe.get_all("Production Plan",
        {"docstatus": 1, "name": ["like", f"%{txt or ''}%"]},
        ["name", "status"],
        limit=20, order_by="creation desc")


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
    
    # Pre-fetch: JC wip_warehouse, BOM quantities, Bin stock — batched
    wo_names = [wo.name for wo in wos if wo.bom_no]
    bom_nos = list(set(wo.bom_no for wo in wos if wo.bom_no))
    
    jc_map = {}
    if wo_names:
        for jc in frappe.get_all("Job Card", {"work_order": ["in", wo_names]}, ["work_order", "operation", "wip_warehouse"]):
            jc_map[(jc.work_order, jc.operation)] = jc.wip_warehouse
    
    bom_map = {b["name"]: b["quantity"] or 1 for b in frappe.get_all("BOM", {"name": ["in", bom_nos]}, ["name", "quantity"])} if bom_nos else {}
    
    item_codes = set()
    for wo in wos:
        if not wo.bom_no: continue
        for item in _get_raw_bom_items(wo.bom_no):
            item_codes.add(item["item_code"])
    
    bin_map = {}
    if item_codes:
        for b in frappe.get_all("Bin", {"item_code": ["in", list(item_codes)], "warehouse": ["like", "%WIP%"]}, ["item_code", "warehouse", "actual_qty"]):
            key = (b.item_code, b.warehouse)
            bin_map[key] = (bin_map.get(key, 0) + b.actual_qty) if key in bin_map else b.actual_qty
    
    for wo in wos:
        if not wo.bom_no:
            continue
        if not wo.wip_warehouse:
            continue
        wo_bom_qty = bom_map.get(wo.bom_no, 1)
        
        for item in _get_raw_bom_items(wo.bom_no):
            source_wh = item.get("source_warehouse") or ""
            if not _is_source_warehouse(source_wh):
                continue
            
            target_wh = jc_map.get((wo.name, item.get("operation"))) if item.get("operation") else None
            target_wh = target_wh or wo.wip_warehouse
            
            required_qty = (item["qty"] * wo.qty) / wo_bom_qty
            in_wip = bin_map.get((item["item_code"], target_wh), 0)
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
