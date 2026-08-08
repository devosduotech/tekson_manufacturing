"""
Custom Work Order — rounds fractional qty to BOM output multiples before ERPNext validation
"""

import frappe
from erpnext.manufacturing.doctype.work_order.work_order import WorkOrder
import math


class TeksonWorkOrder(WorkOrder):
    def validate(self):
        self._round_production_qty()
        super().validate()
    
    def _round_production_qty(self):
        if self.bom_no and self.qty > 0:
            bom_qty = frappe.get_cached_doc("BOM", self.bom_no).quantity
            if bom_qty and bom_qty > 0:
                rounded = math.ceil(self.qty / bom_qty) * bom_qty
                if self.qty != rounded:
                    self.qty = rounded
