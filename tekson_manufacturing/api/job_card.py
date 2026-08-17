import frappe
from tekson_manufacturing.services.job_card_service import JobCardService
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
    Refresh Job Card status fields using the Readiness Engine (single evaluation)
    
    Re-runs the same dependency + material evaluation used by the auto-update
    hooks, ensuring manual and automatic refresh are consistent.
    
    Args:
        job_card: Job Card name
    
    Returns: dict with success, readiness_status, can_start
    """
    from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
    
    engine = JobCardReadinessEngine()
    result = engine.refresh_job_card(job_card)
    
    return {
        "success": True,
        "message": "Job Card status refreshed",
        "readiness_status": result.readiness_status,
        "can_start": result.can_start,
    }
