import frappe
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
