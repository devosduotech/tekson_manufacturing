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
        ["name", "bom_no", "wip_warehouse", "qty", "planned_start_date", "source_warehouse"])

    if not wos:
        return {"created_mrs": [], "total_items": 0, "message": _("No Work Orders found for {0}").format(planned_date)}

    # Build set of BOMs that have their own WOs — skip recursion into these
    wo_bom_nos = {wo.bom_no for wo in wos if wo.bom_no}

    # MP-002: Calculate requirements per department WIP
    dept_items = {}

    # Pre-fetch: JC wip_warehouse, Bin stock — batched
    wo_names = [wo.name for wo in wos if wo.bom_no]

    jc_map = {}
    if wo_names:
        for jc in frappe.get_all("Job Card", {"work_order": ["in", wo_names]}, ["work_order", "operation", "wip_warehouse"]):
            jc_map[(jc.work_order, jc.operation)] = jc.wip_warehouse

    item_codes = set()
    for wo in wos:
        if not wo.bom_no: continue
        for item in _get_raw_bom_items(wo.bom_no, wo_bom_nos):
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

        for item in _get_raw_bom_items(wo.bom_no, wo_bom_nos):
            source_wh = item.get("source_warehouse") or getattr(wo, 'source_warehouse', '') or _get_default_source_warehouse()
            if not _is_source_warehouse(source_wh):
                continue

            target_wh = jc_map.get((wo.name, item.get("operation"))) if item.get("operation") else None
            target_wh = target_wh or wo.wip_warehouse

            required_qty = item["qty"] * wo.qty
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
                "company": frappe.defaults.get_defaults().company,
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


def _get_raw_bom_items(bom_no: str, wo_bom_nos: set = None) -> List[Dict]:
    """Get BOM items that are raw materials only (exploded multi-level).
    Skips sub-assemblies whose BOMs have their own Work Orders."""
    return _explode_bom(bom_no, wo_bom_nos=wo_bom_nos)


def _explode_bom(bom_no: str, _memo: Optional[dict] = None, _seen: Optional[set] = None,
                 wo_bom_nos: Optional[set] = None) -> List[Dict]:
    """
    Recursively explode a multi-level BOM to get raw material items per 1 unit.

    Skips sub-assemblies that have their own Work Orders in the current batch —
    those WOs will request their own materials separately.

    Args:
        bom_no: BOM name
        _memo: Cache of BOM name -> list of raw material items (per 1 unit)
        _seen: Set of BOM names already visited (circular reference guard)
        wo_bom_nos: Set of BOM names that have their own Work Orders

    Returns:
        List of raw material items with quantities per 1 unit of this BOM
    """
    if _memo is None:
        _memo = {}
    if _seen is None:
        _seen = set()
    if wo_bom_nos is None:
        wo_bom_nos = set()

    if bom_no in _memo:
        return _memo[bom_no]

    if bom_no in _seen:
        frappe.log_error(f"Circular BOM reference detected: {bom_no}", "Material Planning")
        return []
    _seen.add(bom_no)

    bom_qty = frappe.db.get_value("BOM", bom_no, "quantity") or 1.0
    items = frappe.get_all("BOM Item", {"parent": bom_no},
        ["item_code", "item_name", "qty", "uom", "source_warehouse", "operation", "do_not_explode", "bom_no"])

    result = []
    for item in items:
        sub_bom = item.get("bom_no") or frappe.db.get_value("BOM",
            {"item": item.item_code, "is_active": 1, "docstatus": 1, "is_default": 1},
            "name")

        if sub_bom and not item.get("do_not_explode"):
            if sub_bom in wo_bom_nos:
                # This sub-assembly has its own WO — skip recursion
                # That WO will request its own raw materials
                continue
            sub_per_unit = _explode_bom(sub_bom, _memo, _seen, wo_bom_nos)
            scale = item.qty / bom_qty
            for s in sub_per_unit:
                result.append({**s, "qty": s["qty"] * scale})
        else:
            result.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "qty": item.qty / bom_qty,
                "uom": item.uom,
                "source_warehouse": item.source_warehouse,
                "operation": item.operation,
            })

    _memo[bom_no] = result
    return result


def _is_source_warehouse(warehouse: str) -> bool:
    """Check if warehouse is a valid source (Raw Material Stores or BOF Stores)"""
    if not warehouse:
        return False
    wh_name = frappe.db.get_value("Warehouse", warehouse, "warehouse_name") or ""
    return "Raw Material Stores" in wh_name or "BOF Stores" in wh_name


def _get_default_source_warehouse() -> str:
    """Find a valid default source warehouse (Raw Material Stores or BOF Stores)"""
    company = frappe.defaults.get_defaults().company
    for wh_name in ("Raw Material Stores", "BOF Stores"):
        # Try exact match first
        wh = frappe.db.get_value("Warehouse", {"warehouse_name": wh_name, "company": company}, "name")
        if wh:
            return wh
        # Try contains match (e.g. "Raw Material Stores - TPL")
        wh = frappe.db.get_value("Warehouse", {"warehouse_name": ["like", f"%{wh_name}%"], "company": company}, "name")
        if wh:
            return wh
    return ""
