"""
Batch Planning Service

Two independent rules applied in sequence:
1. Fixed batch: ceil(demand / bom_output) * bom_output
2. Whole-number UOM: ceil(qty) if UOM must_be_whole_number
"""

import frappe
import math
from typing import Dict, Any


def get_production_qty(bom_no: str, demand_qty: float) -> Dict[str, Any]:
    bom = frappe.get_cached_doc("BOM", bom_no)
    bom_output = bom.quantity or 1
    is_fixed_batch = False
    
    # Rule 1: Fixed batch rounding
    if bom_output > 1 and demand_qty % bom_output != 0:
        production_qty = math.ceil(demand_qty / bom_output) * bom_output
        is_fixed_batch = True
    else:
        production_qty = demand_qty
    
    # Rule 2: Whole-number UOM rounding
    item = bom.item
    if _uom_must_be_whole_number(item):
        if production_qty != int(production_qty):
            production_qty = math.ceil(production_qty)
            is_fixed_batch = True
    
    batch_count = math.ceil(production_qty / bom_output) if bom_output > 0 else 1
    
    return {
        "demand_qty": demand_qty,
        "bom_output_qty": bom_output,
        "batch_count": batch_count,
        "production_qty": production_qty,
        "is_fixed_batch": is_fixed_batch,
    }


def _uom_must_be_whole_number(item_code: str) -> bool:
    uom = frappe.db.get_value("Item", item_code, "stock_uom")
    if uom:
        return bool(frappe.db.get_value("UOM", uom, "must_be_whole_number"))
    return False

