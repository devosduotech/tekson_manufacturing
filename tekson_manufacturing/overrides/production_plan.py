"""
Custom Production Plan — batch rounding + WO consolidation by planned date
"""

from frappe.utils import flt
from erpnext.manufacturing.doctype.production_plan.production_plan import ProductionPlan
from tekson_manufacturing.services.batch_planning import get_production_qty


class TeksonProductionPlan(ProductionPlan):
    def combine_subassembly_items(self, sub_assembly_items_store):
        """Override ERPNext: include schedule_date in consolidation key"""
        key_wise_data = {}
        for row in sub_assembly_items_store:
            key = (
                row.get("production_item"),
                row.get("fg_warehouse"),
                row.get("bom_no"),
                row.get("type_of_manufacturing"),
                str(row.get("schedule_date", "")),
            )
            if key not in key_wise_data:
                key_wise_data[key] = row
                continue
            existing_row = key_wise_data[key]
            if existing_row:
                existing_row.qty += flt(row.qty)
                existing_row.stock_qty += flt(row.stock_qty)
                existing_row.bom_level = max(existing_row.bom_level, row.bom_level)
                continue
            key_wise_data[key] = row
        
        self.sub_assembly_items = list(key_wise_data.values())
        self.set_sub_assembly_items_based_on_level()
    
    def make_work_order_for_subassembly_items(self, wo_list, subcontracted_po, default_warehouses):
        self._apply_batch_rounding()
        super().make_work_order_for_subassembly_items(wo_list, subcontracted_po, default_warehouses)
    
    def _apply_batch_rounding(self):
        for item in self.sub_assembly_items:
            if item.bom_no and item.qty > 0:
                result = get_production_qty(item.bom_no, item.qty)
                if result["is_fixed_batch"]:
                    item.qty = result["production_qty"]
