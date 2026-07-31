import frappe
from tekson_manufacturing.execution.execution_engine import ExecutionEngine


@frappe.whitelist()
def complete_work_order(work_order):
    """
    Complete Work Order - Wrapper for Execution Engine
    
    This maintains backward compatibility while using the new architecture.
    
    Args:
        work_order: Work Order name
    
    Returns: Stock Entry name or status message
    """
    engine = ExecutionEngine()
    result = engine.complete_work_order(work_order)
    
    if result.get('success'):
        return result.get('stock_entry') or result.get('message')
    else:
        return result.get('message')
