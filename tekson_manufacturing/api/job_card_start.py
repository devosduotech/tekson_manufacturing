import frappe
from frappe import _
from tekson_manufacturing.utils.job_card_utils import validate_job_card_start


@frappe.whitelist()
def start_job_card(job_card_name):
    """
    Start Job Card with material validation
    
    Business Rule: JC-003 - Job Card should not start if materials are not available
    
    Args:
        job_card_name: Job Card name
    
    Returns: dict with success status
    
    This method ensures material validation runs before allowing JC start,
    bypassing hook registration issues.
    """
    jc = frappe.get_doc('Job Card', job_card_name)
    
    # Change status first
    jc.status = "Work In Progress"
    
    # Validate material readiness (will throw if not ready)
    validate_job_card_start(jc, method=None)
    
    # Save
    jc.save(ignore_permissions=True)
    frappe.db.commit()
    
    return {"success": True, "message": "Job Card started successfully"}


@frappe.whitelist()
def complete_job_card(job_card_name):
    """
    Complete Job Card with validation
    
    Args:
        job_card_name: Job Card name
    
    Returns: dict with success status
    """
    jc = frappe.get_doc('Job Card', job_card_name)
    
    # Validate can complete
    from tekson_manufacturing.services.job_card_service import JobCardService
    service = JobCardService()
    
    can_complete = service.can_complete(job_card_name)
    
    if not can_complete.get('can_complete'):
        frappe.throw(can_complete.get('reason', 'Cannot complete Job Card'))
    
    # Change status
    jc.status = "Completed"
    jc.save(ignore_permissions=True)
    frappe.db.commit()
    
    return {"success": True, "message": "Job Card completed successfully"}
