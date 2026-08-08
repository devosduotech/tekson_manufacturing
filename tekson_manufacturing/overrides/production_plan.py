"""
Custom Production Plan — rounds WO qty to BOM output multiples
"""

import frappe
from erpnext.manufacturing.doctype.production_plan.production_plan import ProductionPlan
from erpnext.manufacturing.doctype.work_order.work_order import make_work_order
from tekson_manufacturing.services.batch_planning import get_production_qty


class TeksonProductionPlan(ProductionPlan):
    def make_work_order_for_subassembly_items(self, wo_list, subcontracted_po, default_warehouses):
        for item in self.sub_assembly_items:
            if item.bom_no and item.planned_qty > 0:
                result = get_production_qty(item.bom_no, item.planned_qty)
                if result["is_fixed_batch"]:
                    item.planned_qty = result["production_qty"]
        super().make_work_order_for_subassembly_items(wo_list, subcontracted_po, default_warehouses)
