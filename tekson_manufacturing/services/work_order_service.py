import frappe
from frappe import _
from tekson_manufacturing.execution.execution_engine import ExecutionEngine


def set_warehouses(doc, method=None):
    """
    Auto-set Work Order Warehouses
    
    Warehouse Philosophy:
    - WIP Warehouse is a logical production holding warehouse
    - Material transferred once at start, backflushed at completion
    - Intermediate department movement tracked via Job Cards, not Stock Entries
    - BOM defines destination (FG), Process Plan defines execution (WIP)
    
    Priority for FG Warehouse:
    1. Production Plan FG Warehouse (override)
    2. BOM Target FG Warehouse
    3. Manufacturing Settings Default FG
    
    Priority for WIP Warehouse:
    1. Production Plan WIP Warehouse (override)
    2. First Operation's Department WIP (from Process Plan)
    3. Manufacturing Settings Default WIP
    
    Args:
        doc: Work Order document
        method: Event method name (optional)
    """
    if not doc.is_new():
        return


def round_production_qty(doc, method=None):
    """
    Round WO qty to BOM output quantity multiples.
    Runs on validate — catches PP recalculated qty.
    """
    if doc.bom_no and doc.qty > 0:
        import math
        bom_qty = frappe.get_cached_doc("BOM", doc.bom_no).quantity
        if bom_qty:
            rounded = math.ceil(doc.qty / bom_qty) * bom_qty
            if doc.qty != rounded:
                frappe.msgprint(f"Rounding: {doc.qty} → {rounded} (BOM qty={bom_qty})", alert=True)
                doc.qty = rounded
    # ========== FG WAREHOUSE ==========
    
    # Priority 1: Production Plan override
    if doc.production_plan:
        pp = frappe.get_doc('Production Plan', doc.production_plan)
        pp_fg_wh = pp.get('fg_warehouse') or pp.get('for_warehouse')
        
        if pp_fg_wh and not frappe.db.get_value('Warehouse', pp_fg_wh, 'is_group'):
            doc.fg_warehouse = pp_fg_wh
    
    # Priority 2: BOM Target FG Warehouse
    if not doc.fg_warehouse and doc.bom_no:
        bom = frappe.get_doc('BOM', doc.bom_no)
        target_fg_wh = bom.get('target_fg_warehouse')
        
        if target_fg_wh and not frappe.db.get_value('Warehouse', target_fg_wh, 'is_group'):
            doc.fg_warehouse = target_fg_wh
    
    # ========== WIP WAREHOUSE ==========
    
    # Priority 1: Production Plan override
    if doc.production_plan:
        pp = frappe.get_doc('Production Plan', doc.production_plan)
        pp_wip_wh = pp.get('for_warehouse')
        
        if pp_wip_wh and not frappe.db.get_value('Warehouse', pp_wip_wh, 'is_group'):
            doc.wip_warehouse = pp_wip_wh
    
    # Priority 2: First BOM Operation's WIP (from workstation_type → plant_floor)
    if not doc.wip_warehouse and doc.bom_no:
        bom_op = frappe.db.get_all("BOM Operation",
            {"parent": doc.bom_no},
            ["workstation_type", "workstation"],
            order_by="idx asc", limit=1)
        
        if bom_op:
            ws_type = bom_op[0].workstation_type or bom_op[0].workstation
            if ws_type:
                plant_floor = frappe.db.get_value("Workstation",
                    {"workstation_type": ws_type}, "plant_floor",
                    order_by="name asc")
                
                if plant_floor:
                    wip_wh = f"WIP-{plant_floor} - TPL"
                    if frappe.db.exists("Warehouse", wip_wh):
                        doc.wip_warehouse = wip_wh
    
    # Set default source_warehouse for bulk WO creation
    if not doc.source_warehouse:
        doc.source_warehouse = "Stores - TPL"


def auto_create_manufacture_entry(doc, method=None):
    """
    SAFETY NET: Trigger Execution Engine when Work Order status changes to Completed
    
    Business Rule: WO-003 (Safety Net Only)
    
    Trigger: Work Order Before Save
    
    IMPORTANT: This is NOT the primary logic owner.
    - Primary Owner: Execution Engine (triggered by Job Card submit)
    - This hook: Safety net for manual WO status changes
    
    Architecture:
    - Hook detects status change → Delegates to Execution Engine
    - Execution Engine validates: All JCs complete, quantities achieved, no duplicates
    - Hook never creates Stock Entry directly
    
    Args:
        doc: Work Order document
        method: Event method name (optional)
    """
    # Skip if document is new, draft, or not completed
    if (
        doc.is_new()
        or doc.docstatus != 1
        or doc.status != "Completed"
    ):
        return
    
    if not doc.name:
        return
        # Check if Stock Entry already exists (quick check before calling engine)
        existing = frappe.db.exists(
            "Stock Entry",
            {
                "work_order": doc.name,
                "purpose": "Manufacture",
                "docstatus": 1
            }
        )
        
        if not existing:
            try:
                # Delegate to Execution Engine (primary owner)
                engine = ExecutionEngine()
                result = engine.complete_work_order(doc.name)
                
                # Log result for audit trail
                if result.get('success'):
                    if result.get('stock_entry'):
                        frappe.log_error(
                            title=_("WO Safety Net: Manufacture Entry Created"),
                            message=f"WO: {doc.name}\nSE: {result['stock_entry']}"
                        )
                    else:
                        frappe.log_error(
                            title=_("WO Safety Net: Already Complete"),
                            message=f"WO: {doc.name}\nNote: {result.get('message', 'No message')}"
                        )
                    
            except Exception as e:
                frappe.log_error(
                    title=_("WO Safety Net: Error"),
                    message=f"WO: {doc.name}\nError: {str(e)}"
                )
                # Don't throw - safety net should not block WO save
                # The primary flow (JC submit) should still work
