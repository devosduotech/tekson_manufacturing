import frappe
from frappe import _
from tekson_manufacturing.execution.execution_engine import ExecutionEngine


def auto_create_manufacture_entry(doc, method=None):
    """
    Auto-create Manufacture Stock Entry when Work Order is completed
    
    Business Rule: WO-003 - Auto-manufacture on WO complete
    
    Trigger: Work Order Before Save
    
    Args:
        doc: Work Order document
        method: Event method name (optional)
    
    Note:
    This is a backup to the Job Card submit trigger.
    Handles cases where WO status is manually set to "Completed".
    
    Logic:
    - Check if WO is submitted and status is "Completed"
    - Check if Manufacture Stock Entry already exists
    - If not, use Execution Engine to create one
    - Show confirmation message
    """
    if (
        doc.docstatus == 1
        and doc.status == "Completed"
    ):
        # Check if Stock Entry already exists
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
                # Use Execution Engine to create
                engine = ExecutionEngine()
                result = engine.complete_work_order(doc.name)
                
                if result.get('success') and result.get('stock_entry'):
                    frappe.msgprint(
                        _("Manufacture Stock Entry Created: {0}").format(result['stock_entry']),
                        alert=True
                    )
                elif result.get('message'):
                    frappe.msgprint(
                        _("Work Order completion note: {0}").format(result['message']),
                        alert=True
                    )
                    
            except Exception as e:
                frappe.log_error(
                    title=_("Work Order Auto-Manufacture Error"),
                    message=f"WO: {doc.name}\nError: {str(e)}"
                )
                # Don't throw - allow WO to save anyway
                frappe.msgprint(
                    _("Note: Could not auto-create Manufacture Entry. Please create manually."),
                    alert=True
                )
