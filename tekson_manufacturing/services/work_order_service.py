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
    
    # Priority 2: First Operation's Department WIP
    if not doc.wip_warehouse and doc.operations:
        first_op = doc.operations[0]
        department = None
        
        # Get department from workstation
        if first_op.workstation:
            department = frappe.db.get_value('Workstation', first_op.workstation, 'department')
        
        # Build WIP warehouse name from department
        if department:
            dept_short = department.split('-')[0].strip()
            wip_warehouse_name = f'WIP-{dept_short} - TPL'
            
            wip_wh = frappe.db.get_value('Warehouse', {
                'warehouse_name': wip_warehouse_name,
                'is_group': 0
            })
            
            if wip_wh:
                doc.wip_warehouse = wip_wh
    
    # Show message if warehouses set
    if doc.wip_warehouse or doc.fg_warehouse:
        frappe.msgprint(
            _('Warehouses configured: WIP={0}, FG={1}').format(
                frappe.bold(doc.wip_warehouse or 'Default'),
                frappe.bold(doc.fg_warehouse or 'Default')
            ),
            alert=True
        )


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
