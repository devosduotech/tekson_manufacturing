"""
Custom Work Order — rounds fractional qty to BOM output multiples before ERPNext validation
"""

import frappe
from erpnext.manufacturing.doctype.work_order.work_order import WorkOrder
import math


class TeksonWorkOrder(WorkOrder):
    def validate(self):
        self._round_production_qty()
        self._set_warehouses()
        super().validate()
    
    def _round_production_qty(self):
        if self.bom_no and self.qty > 0 and self.qty < 1:
            try:
                bom = frappe.get_doc("BOM", self.bom_no)
                bom_qty = bom.quantity
                if bom_qty and bom_qty > 0:
                    rounded = math.ceil(self.qty / bom_qty) * bom_qty
                    if self.qty != rounded:
                        self.qty = rounded
            except Exception:
                pass
    
    def _set_warehouses(self):
        if self.wip_warehouse and self.fg_warehouse:
            return
        if not self.bom_no:
            return
        try:
            bom = frappe.get_doc("BOM", self.bom_no)
            if not self.fg_warehouse:
                self.fg_warehouse = bom.get("target_fg_warehouse") or ""
            if not self.wip_warehouse:
                ops = frappe.get_all("BOM Operation", {"parent": self.bom_no}, 
                    ["workstation_type", "workstation"], order_by="idx asc", limit=1)
                if ops:
                    ws_type = ops[0].workstation_type or ops[0].workstation
                    if ws_type:
                        pf = frappe.db.get_value("Workstation", 
                            {"workstation_type": ws_type}, "plant_floor")
                        if pf:
                            wh = f"WIP-{pf} - TPL"
                            if frappe.db.exists("Warehouse", wh):
                                self.wip_warehouse = wh
        except Exception:
            pass
