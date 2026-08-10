"""
Custom Production Plan — batch rounding + WO consolidation by planned date
"""

import frappe
from erpnext.manufacturing.doctype.production_plan.production_plan import ProductionPlan
from tekson_manufacturing.services.batch_planning import get_production_qty


class TeksonProductionPlan(ProductionPlan):
    def make_work_order_for_subassembly_items(self, wo_list, subcontracted_po, default_warehouses):
        self._apply_batch_rounding()
        if self.combine_sub_items:
            self._consolidate_by_date()
        super().make_work_order_for_subassembly_items(wo_list, subcontracted_po, default_warehouses)
    
    def _apply_batch_rounding(self):
        for item in self.sub_assembly_items:
            if item.bom_no and item.qty > 0:
                result = get_production_qty(item.bom_no, item.qty)
                if result["is_fixed_batch"]:
                    item.qty = result["production_qty"]
    
    def _consolidate_by_date(self):
        """Group sub-assembly items by (item, BOM, schedule_date) and sum qty"""
        groups = {}
        for item in self.sub_assembly_items:
            if item.type_of_manufacturing in ("Subcontract", "Material Request"):
                continue
            key = (item.production_item, item.bom_no, str(item.schedule_date))
            if key not in groups:
                groups[key] = frappe.copy_doc(item)
                groups[key].qty = 0
            groups[key].qty += item.qty
        
        self.sub_assembly_items = list(groups.values())
