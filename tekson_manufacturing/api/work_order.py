import frappe
from tekson_manufacturing.execution.execution_engine import ExecutionEngine
from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine


@frappe.whitelist()
def get_work_order_details(work_order):
    """
    Get Work Order details with all related information
    
    Args:
        work_order: Work Order name
    
    Returns: dict with Work Order, Job Cards, progress, material readiness
    """
    # Return basic WO details (no service needed)
    wo = frappe.get_doc("Work Order", work_order)
    
    # Get Job Cards
    job_cards = frappe.get_all(
        "Job Card",
        filters={"work_order": work_order},
        fields=["name", "operation", "status", "custom_start_status"]
    )
    
    # Get material readiness
    engine = MaterialReadinessEngine(work_order=work_order)
    readiness = engine.evaluate_material_readiness()
    
    return {
        "work_order": wo,
        "job_cards": job_cards,
        "material_readiness": readiness
    }


@frappe.whitelist()
def complete_work_order(work_order):
    """
    Complete Work Order
    
    Args:
        work_order: Work Order name
    
    Returns: dict with completion result
    """
    engine = ExecutionEngine()
    return engine.complete_work_order(work_order)


@frappe.whitelist()
def refresh_work_order_status(work_order):
    """
    Refresh Work Order status
    
    Args:
        work_order: Work Order name
    
    Returns: success message
    """
    engine = ExecutionEngine()
    engine.refresh_work_order_status(work_order)
    
    return {"success": True, "message": "Work Order status refreshed"}


@frappe.whitelist()
def check_material_readiness(work_order):
    """
    Check material readiness for Work Order
    
    Args:
        work_order: Work Order name
    
    Returns: dict with material readiness status
    """
    engine = MaterialReadinessEngine(work_order=work_order)
    return engine.evaluate_material_readiness()
