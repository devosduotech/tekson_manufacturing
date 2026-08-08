"""
Custom Work Order — rounds fractional qty to BOM output multiples before ERPNext validation
"""

import frappe
from erpnext.manufacturing.doctype.work_order.work_order import WorkOrder
import math


class TeksonWorkOrder(WorkOrder):
    def validate(self):
        self._set_warehouses()
        self._round_production_qty()
        self._safe_validate()
    
    def _safe_validate(self):
        """Call super validate, handling ERPNext bug for new docs"""
        try:
            super().validate()
        except Exception as e:
            if "use_multi_level_bom" in str(e) and not self.get_doc_before_save():
                self.use_multi_level_bom = 0
                super().validate()
            else:
                raise
