import frappe
from frappe import _
from tekson_manufacturing.execution.execution_engine import ExecutionEngine


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
