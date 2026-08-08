"""
Custom Production Plan — rounds WO qty to BOM multiples during Release
"""

import frappe
from erpnext.manufacturing.doctype.production_plan.production_plan import ProductionPlan
import math


class TeksonProductionPlan(ProductionPlan):
    def _create_work_orders(self, *args, **kwargs):
        super()._create_work_orders(*args, **kwargs)
        self._round_all_work_order_qty()
    
    def _round_all_work_order_qty(self):
        wos = frappe.get_all("Work Order",
            {"production_plan": self.name, "docstatus": 0},
            ["name", "bom_no", "qty", "wip_warehouse"])
        
        for w in wos:
            updated = {}
            if w.bom_no and w.qty > 0:
                bq = frappe.db.get_value("BOM", w.bom_no, "quantity") or 1
                rounded = math.ceil(w.qty / bq) * bq
                if w.qty != rounded:
                    updated["qty"] = rounded
            
            if not w.wip_warehouse and w.bom_no:
                ops = frappe.get_all("BOM Operation",
                    {"parent": w.bom_no}, ["workstation_type"],
                    order_by="idx asc", limit=1)
                if ops and ops[0].workstation_type:
                    pf = frappe.db.get_value("Workstation",
                        {"workstation_type": ops[0].workstation_type}, "plant_floor")
                    if pf:
                        wh = f"WIP-{pf} - TPL"
                        if frappe.db.exists("Warehouse", wh):
                            updated["wip_warehouse"] = wh
                            updated["source_warehouse"] = "Stores - TPL"
            
            if updated:
                frappe.db.set_value("Work Order", w.name, updated)
