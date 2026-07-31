import frappe
from frappe import _


class DependencyEngine:
    """
    Dependency Engine - Validates operation dependencies
    
    Checks:
    - Previous operation completion
    - Operation sequence validation
    - Multi-dependency validation (future)
    """
    
    def __init__(self):
        pass
    
    def validate_previous_operation(self, job_card):
        """
        Validate if previous operation is completed
        
        Args:
            job_card: Job Card object
        
        Returns: dict with is_valid, reason, diagnostic
        """
        result = {
            'is_valid': True,
            'reason': '',
            'diagnostic': {}
        }
        
        # Check if this is the first operation
        if not job_card.sequence_id or job_card.sequence_id == 1:
            result['reason'] = "First operation - no previous dependency"
            return result
        
        # Get previous Job Card
        prev_jc = self.get_previous_job_card(job_card)
        
        if not prev_jc:
            result['is_valid'] = False
            result['reason'] = "Previous Job Card not found"
            result['diagnostic'] = {
                'type': 'error',
                'message': "Cannot find previous operation Job Card",
                'action': "Check Work Order routing"
            }
            return result
        
        # Check previous Job Card status
        if prev_jc.status != "Completed":
            result['is_valid'] = False
            result['reason'] = f"Previous operation '{prev_jc.operation}' is not completed (Status: {prev_jc.status})"
            
            result['diagnostic'] = {
                'type': 'warning',
                'message': f"Operation '{prev_jc.operation}' must be completed first",
                'action': f"Complete Job Card {prev_jc.name}",
                'previous_job_card': prev_jc.name,
                'previous_operation': prev_jc.operation,
                'previous_status': prev_jc.status
            }
            
            return result
        
        # All checks passed
        result['reason'] = "Previous operation completed"
        return result
    
    def get_previous_job_card(self, job_card):
        """Get the previous Job Card for the same Work Order"""
        if not job_card.work_order:
            return None
        
        prev_jc = frappe.db.sql("""
            SELECT name, operation, status, sequence_id
            FROM `tabJob Card`
            WHERE work_order = %s
            AND sequence_id = %s
            AND docstatus = 1
            ORDER BY creation DESC
            LIMIT 1
        """, (job_card.work_order, job_card.sequence_id - 1), as_dict=True)
        
        return prev_jc[0] if prev_jc else None
    
    def validate_operation_sequence(self, work_order):
        """
        Validate operation sequence for a Work Order
        
        Args:
            work_order: Work Order object
        
        Returns: dict with sequence validation
        """
        result = {
            'is_valid': True,
            'operations': [],
            'issues': []
        }
        
        # Get all Job Cards for the Work Order
        job_cards = frappe.get_all(
            "Job Card",
            filters={"work_order": work_order.name},
            fields=["name", "operation", "sequence_id", "status"],
            order_by="sequence_id ASC"
        )
        
        if not job_cards:
            result['is_valid'] = True
            result['message'] = "No Job Cards found"
            return result
        
        # Check sequence
        prev_seq = 0
        
        for jc in job_cards:
            if jc.sequence_id != prev_seq + 1:
                result['is_valid'] = False
                result['issues'].append({
                    'job_card': jc.name,
                    'issue': f"Sequence gap: Expected {prev_seq + 1}, got {jc.sequence_id}"
                })
            
            prev_seq = jc.sequence_id
            
            result['operations'].append({
                'sequence': jc.sequence_id,
                'operation': jc.operation,
                'status': jc.status
            })
        
        return result
    
    def get_all_dependencies(self, job_card):
        """
        Get all dependencies for a Job Card (future enhancement)
        
        Currently only checks immediate previous operation
        Can be extended to check multiple dependencies
        """
        dependencies = []
        
        # Current: Only previous operation
        prev_jc = self.get_previous_job_card(job_card)
        
        if prev_jc:
            dependencies.append({
                'type': 'previous_operation',
                'job_card': prev_jc.name,
                'operation': prev_jc.operation,
                'status': prev_jc.status,
                'required': True
            })
        
        return dependencies


@frappe.whitelist()
def validate_previous_operation(job_card):
    """
    Whitelisted method to validate previous operation
    
    Args:
        job_card: Job Card name
    
    Returns: dict with validation result
    """
    if isinstance(job_card, str):
        jc = frappe.get_doc("Job Card", job_card)
    else:
        jc = job_card
    
    engine = DependencyEngine()
    return engine.validate_previous_operation(jc)
