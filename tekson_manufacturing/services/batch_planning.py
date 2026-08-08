"""
Batch Planning Service

Converts demand quantity to production batch quantity for
fixed-yield manufacturing processes where one manufacturing
cycle produces multiple output units.
"""

import frappe
import math
from typing import Dict, Any


def get_production_qty(bom_no: str, demand_qty: float) -> Dict[str, Any]:
    """
    Calculate production quantity considering BOM output multiples.
    
    For BOMs with quantity > 1 (multiple output per cycle):
        production_qty = ceil(demand / bom_qty) * bom_qty
    
    For standard BOMs (qty=1):
        production_qty = demand_qty
    
    Returns:
        dict with demand, bom output, batch count, production qty, is_fixed_batch
    """
    bom = frappe.get_cached_doc("BOM", bom_no)
    bom_output = bom.quantity or 1
    
    if bom_output > 1:
        batch_count = math.ceil(demand_qty / bom_output)
        production_qty = batch_count * bom_output
        is_fixed_batch = True
    else:
        batch_count = 1
        production_qty = demand_qty
        is_fixed_batch = False
    
    return {
        "demand_qty": demand_qty,
        "bom_output_qty": bom_output,
        "batch_count": batch_count,
        "production_qty": production_qty,
        "is_fixed_batch": is_fixed_batch,
    }
