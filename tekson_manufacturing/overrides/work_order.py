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
        if self.bom_no and self.qty > 0:
            bom_qty = frappe.get_cached_doc("BOM", self.bom_no).quantity
            if bom_qty and bom_qty > 0:
                rounded = math.ceil(self.qty / bom_qty) * bom_qty
                if self.qty != rounded:
                    self.qty = rounded
    
    def _set_warehouses(self):
        if self.wip_warehouse and self.fg_warehouse:
            return
        if self.bom_no:
            bom = frappe.get_cached_doc("BOM", self.bom_no)
            if not self.fg_warehouse:
                self.fg_warehouse = bom.get("target_fg_warehouse") or ""
            if not self.wip_warehouse and bom.operations:
                op = bom.operations[0]
                ws_type = op.workstation_type or op.workstation
                if ws_type:
                    pf = frappe.db.get_value("Workstation", {"workstation_type": ws_type}, "plant_floor")
                    if pf:
                        wh = f"WIP-{pf} - TPL"
                        if frappe.db.exists("Warehouse", wh):
                            self.wip_warehouse = wh
