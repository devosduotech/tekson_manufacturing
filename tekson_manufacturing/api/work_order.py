import frappe
from tekson_manufacturing.services.work_order_service import WorkOrderService
from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine


@frappe.whitelist()
def get_work_order_details(work_order):
    """
    Get Work Order details with all related information
    
    Args:
        work_order: Work Order name
    
    Returns: dict with Work Order, Job Cards, progress, material readiness
    """
    service = WorkOrderService()
    return service.get_work_order_details(work_order)


@frappe.whitelist()
def complete_work_order(work_order):
    """
    Complete Work Order
    
    Args:
        work_order: Work Order name
    
    Returns: dict with completion result
    """
    service = WorkOrderService()
    return service.complete(work_order)


@frappe.whitelist()
def refresh_work_order_status(work_order):
    """
    Refresh Work Order status
    
    Args:
        work_order: Work Order name
    
    Returns: success message
    """
    service = WorkOrderService()
    service.refresh_status(work_order)
    
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
