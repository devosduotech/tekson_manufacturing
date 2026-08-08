import frappe
from frappe import _
import math


def set_warehouses(doc, method=None):
    """
    Auto-set Work Order Warehouses from BOM.
    Runs on before_insert and validate.
    """
    if not doc.bom_no:
        return
    
    # FG Warehouse from BOM
    if not doc.fg_warehouse:
        fg_wh = frappe.db.get_value("BOM", doc.bom_no, "target_fg_warehouse")
        if fg_wh:
            doc.fg_warehouse = fg_wh
    
    # WIP Warehouse from BOM's first operation workstation_type → plant_floor
    if not doc.wip_warehouse:
        bom_op = frappe.get_all("BOM Operation",
            {"parent": doc.bom_no},
            ["workstation_type", "workstation"],
            order_by="idx asc", limit=1)
        if bom_op:
            ws_type = bom_op[0].workstation_type or bom_op[0].workstation
            if ws_type:
                pf = frappe.db.get_value("Workstation",
                    {"workstation_type": ws_type}, "plant_floor")
                if pf:
                    wh = f"WIP-{pf} - TPL"
                    if frappe.db.exists("Warehouse", wh):
                        doc.wip_warehouse = wh
    
    if not doc.source_warehouse:
        doc.source_warehouse = "Stores - TPL"


def round_production_qty(doc, method=None):
    """Round WO qty to BOM output quantity multiples."""
    if doc.bom_no and doc.qty > 0:
        bom_qty = frappe.get_cached_doc("BOM", doc.bom_no).quantity
        if bom_qty and bom_qty > 0:
            rounded = math.ceil(doc.qty / bom_qty) * bom_qty
            if doc.qty != rounded:
                doc.qty = rounded


def fix_pp_work_orders(doc, method=None):
    """
    Production Plan on_submit: fix WIP warehouse + round qty
    for all Draft WOs created by this PP.
    """
    wos = frappe.get_all("Work Order",
        {"production_plan": doc.name, "docstatus": 0},
        pluck="name")
    
    for wo_name in wos:
        wo = frappe.get_doc("Work Order", wo_name)
        needs_save = False
        
        if wo.bom_no:
            if not wo.wip_warehouse:
                ops = frappe.get_all("BOM Operation",
                    {"parent": wo.bom_no},
                    ["workstation_type", "workstation"],
                    order_by="idx asc", limit=1)
                if ops:
                    ws = ops[0].workstation_type or ops[0].workstation
                    if ws:
                        pf = frappe.db.get_value("Workstation",
                            {"workstation_type": ws}, "plant_floor")
                        if pf:
                            wh = f"WIP-{pf} - TPL"
                            if frappe.db.exists("Warehouse", wh):
                                wo.wip_warehouse = wh
                                needs_save = True
            if not wo.source_warehouse:
                wo.source_warehouse = "Stores - TPL"
                needs_save = True
            if wo.qty < 1:
                bq = frappe.db.get_value("BOM", wo.bom_no, "quantity") or 1
                rounded = math.ceil(wo.qty / bq) * bq
                if wo.qty != rounded:
                    wo.qty = rounded
                    needs_save = True
        
        if needs_save:
            wo.flags.ignore_validate = True
            wo.save()
            wo.reload()
            # Regenerate required items with correct quantities
            wo.set_required_items()
            wo.save(ignore_permissions=True)
