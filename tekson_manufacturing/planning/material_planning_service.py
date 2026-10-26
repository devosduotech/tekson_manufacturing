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

from tekson_manufacturing.utils import operation_warehouse as operation_warehouse_utils


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
        dict with created_mrs (list of MR names), total_items, warnings
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

    # MP-002: Aggregate requirements per department WIP across ALL Work Orders
    # first. Available stock must be deducted once per (WIP, item) — never once
    # per Work Order — otherwise the same stock either covers several WOs at
    # once (requirements get dropped) or the request ignores stock entirely.
    warnings = []

    # Pre-fetch: JC wip_warehouse — batched
    wo_names = [wo.name for wo in wos if wo.bom_no]

    jc_map = {}
    if wo_names:
        for jc in frappe.get_all("Job Card", {"work_order": ["in", wo_names]},
                                 ["work_order", "operation", "wip_warehouse"],
                                 order_by="name asc"):
            # Whitespace-tolerant key; keep the first non-empty WIP so a
            # split/duplicate Job Card with an empty warehouse cannot win.
            key = (jc.work_order, (jc.operation or "").strip())
            if key not in jc_map or not jc_map[key]:
                jc_map[key] = jc.wip_warehouse or ""

    requirements = {}
    default_source_wh = None
    operation_wh_cache = {}

    for wo in wos:
        if not wo.bom_no:
            continue

        for item in _get_raw_bom_items(wo.bom_no, wo_bom_nos):
            source_wh = item.get("source_warehouse") or getattr(wo, "source_warehouse", "") or ""
            if not source_wh:
                if default_source_wh is None:
                    default_source_wh = _get_default_source_warehouse()
                source_wh = default_source_wh
            if not _is_source_warehouse(source_wh):
                warnings.append(
                    _("Item {0}: no valid source warehouse (Raw Material Stores / BOF Stores) — skipped").format(
                        item["item_code"]
                    )
                )
                continue

            # Target warehouse is driven by the BOM Item's operation — the
            # Work Order header (first-operation) warehouse is never used for
            # operation-bearing items. Chain: BOM Operation -> workstation ->
            # plant floor -> WIP-{floor} - TPL; Job Card WIP as fallback.
            operation = (item.get("operation") or "").strip()
            if operation:
                config_wh = operation_warehouse_utils.resolve_operation_warehouse(
                    item.get("source_bom") or wo.bom_no,
                    operation,
                    fallback_bom_no=(wo.bom_no if item.get("source_bom")
                                     and item.get("source_bom") != wo.bom_no else None),
                    cache=operation_wh_cache,
                )
                jc_wh = jc_map.get((wo.name, operation)) or ""
                target_wh = config_wh or jc_wh
                if not target_wh:
                    warnings.append(
                        _("Item {0} on Work Order {1}: warehouse for operation {2} could not be "
                          "resolved — material skipped").format(item["item_code"], wo.name, operation)
                    )
                    continue
                if config_wh and jc_wh and config_wh != jc_wh:
                    warnings.append(
                        _("Work Order {0}: Job Card for operation {1} targets {2} but the operation "
                          "warehouse is {3} — re-save the Job Card to refresh its WIP warehouse").format(
                            wo.name, operation, jc_wh, config_wh)
                    )
            else:
                if not wo.wip_warehouse:
                    warnings.append(
                        _("Work Order {0} has no WIP warehouse — its materials were skipped").format(wo.name)
                    )
                    continue
                target_wh = wo.wip_warehouse
                warnings.append(
                    _("Item {0} on Work Order {1}: BOM Item has no operation — using the Work Order "
                      "WIP warehouse {2}").format(item["item_code"], wo.name, wo.wip_warehouse)
                )

            base_qty = item["qty"] * wo.qty
            if base_qty <= 0:
                continue
            loss_pct = (item.get("rm_loss_pct", 0) or 0) / 100.0

            key = (target_wh, item["item_code"])
            req = requirements.get(key)
            if req is None:
                req = requirements[key] = {
                    "item_name": item.get("item_name", ""),
                    "uom": item.get("uom", "Nos"),
                    "base_qty": 0.0,
                    "loss_qty": 0.0,
                    "sources": {},
                }
            req["base_qty"] += base_qty
            req["loss_qty"] += base_qty * loss_pct
            req["sources"][source_wh] = req["sources"].get(source_wh, 0.0) + base_qty

    warnings = list(dict.fromkeys(warnings))

    if not requirements:
        return {
            "created_mrs": [],
            "total_items": 0,
            "message": _("No material requirements found for {0}").format(planned_date),
            "warnings": warnings,
        }

    # Batch-fetch Bin stock for exactly the (item, target WIP) pairs in play
    bin_map = {}
    item_codes = sorted({key[1] for key in requirements})
    warehouses = sorted({key[0] for key in requirements})
    for b in frappe.get_all(
        "Bin",
        {"item_code": ["in", item_codes], "warehouse": ["in", warehouses]},
        ["item_code", "warehouse", "actual_qty"],
    ):
        bin_key = (b.item_code, b.warehouse)
        bin_map[bin_key] = bin_map.get(bin_key, 0) + b.actual_qty

    # Balance = required (incl. RM Loss) - already available in the target WIP.
    # Because aggregation happens first, a requirement is only dropped when
    # stock truly covers the day's total — not just a single Work Order.
    dept_items = {}
    for (target_wh, item_code), req in requirements.items():
        required_qty = req["base_qty"] + req["loss_qty"]
        in_wip = bin_map.get((item_code, target_wh), 0) or 0
        balance = required_qty - in_wip
        if balance <= 1e-9:  # covers float noise when required == in_wip exactly
            continue

        # Split the balance into BOM portion + RM Loss portion so the
        # Qty = custom_bom_qty + custom_rm_loss_qty invariant still holds.
        # loss_ratio = loss / (base + loss) = loss_pct / (1 + loss_pct)
        loss_ratio = (req["loss_qty"] / required_qty) if required_qty else 0
        rm_loss_pct = (req["loss_qty"] / req["base_qty"]) * 100 if req["base_qty"] else 0
        total_base = req["base_qty"] or 1.0

        for source_wh, source_base in req["sources"].items():
            line_qty = balance * (source_base / total_base)
            line_loss_qty = line_qty * loss_ratio
            key = (target_wh, item_code, source_wh)
            if target_wh not in dept_items:
                dept_items[target_wh] = {}
            dept_items[target_wh][key] = {
                "item_code": item_code,
                "item_name": req["item_name"],
                "qty": line_qty,
                "base_qty": line_qty - line_loss_qty,
                "rm_loss_pct": rm_loss_pct,
                "rm_loss_qty": line_loss_qty,
                "from_warehouse": source_wh,
                "uom": req["uom"],
            }

    if not dept_items:
        return {
            "created_mrs": [],
            "total_items": 0,
            "message": _("All materials already in WIP for {0}").format(planned_date),
            "warnings": warnings,
        }

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
                "qty": math.ceil(round(item_data["qty"], 10)),
                "custom_bom_qty": item_data["base_qty"],
                "custom_rm_loss_pct": item_data.get("rm_loss_pct", 0),
                "custom_rm_loss_qty": item_data["rm_loss_qty"],
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
        "warnings": warnings,
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
        ["item_code", "item_name", "qty", "uom", "source_warehouse", "operation", "do_not_explode", "bom_no", "custom_rm_loss_pct"])

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
                "rm_loss_pct": item.custom_rm_loss_pct or 0,
                "uom": item.uom,
                "source_warehouse": item.source_warehouse,
                "operation": item.operation,
                # BOM this leaf actually came from — its BOM Operation rows
                # define the operation's workstation (and warehouse) even for
                # items exploded from a child BOM.
                "source_bom": bom_no,
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
