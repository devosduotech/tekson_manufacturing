import frappe
from tekson_manufacturing.services.job_card_service import JobCardService
from tekson_manufacturing.services.work_order_service import WorkOrderService
from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine


@frappe.whitelist()
def get_job_card_details(job_card):
    """
    Get Job Card details with all related information
    
    Args:
        job_card: Job Card name
    
    Returns: dict with Job Card, Work Order, dependencies, material readiness
    """
    service = JobCardService()
    return service.get_job_card_details(job_card)


@frappe.whitelist()
def check_can_start(job_card):
    """
    Check if Job Card can start
    
    Args:
        job_card: Job Card name
    
    Returns: dict with can_start, reason, diagnostics
    """
    service = JobCardService()
    return service.can_start(job_card)


@frappe.whitelist()
def check_can_complete(job_card):
    """
    Check if Job Card can complete
    
    Args:
        job_card: Job Card name
    
    Returns: dict with can_complete, reason
    """
    service = JobCardService()
    return service.can_complete(job_card)


@frappe.whitelist()
def refresh_job_card_status(job_card):
    """
    Refresh Job Card status fields
    
    Args:
        job_card: Job Card name
    
    Returns: success message
    """
    service = JobCardService()
    service.refresh_status(job_card)
    
    return {"success": True, "message": "Job Card status refreshed"}
