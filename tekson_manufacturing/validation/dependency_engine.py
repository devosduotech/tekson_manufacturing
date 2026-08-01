import frappe
from frappe import _
from datetime import datetime
from tekson_manufacturing.repositories.job_card_repository import JobCardRepository
from tekson_manufacturing.utils.exceptions import MESDependencyError
from tekson_manufacturing.utils import log_mes_event


class DependencyEngine:
    """
    Dependency Engine - Validates operation dependencies
    
    Business Rules:
    - DV-001: Previous operation validation
    - DV-002: Sequence validation
    
    Dependencies:
    - JobCardRepository for data access
    - MES Settings for configuration
    
    Performance Target: < 2 seconds
    """
    
    def __init__(self, job_card=None, work_order=None):
        """
        Initialize Dependency Engine
        
        Args:
            job_card: Job Card name or document (optional)
            work_order: Work Order name or document (optional)
        """
        self.job_card = job_card
        self.work_order = work_order
        self.repo = JobCardRepository()
        
        # Get MES Settings
        self.mes_settings = frappe.get_doc("MES Settings", "MES Settings") if frappe.db.exists("MES Settings", "MES Settings") else None
    
    def validate_previous_operation(self, job_card=None):
        """
        Validate previous operation is complete (DV-001)
        
        Business Rule: DV-001 - A Job Card cannot start until all previous 
        operations are complete.
        
        Args:
            job_card: Job Card name or document (optional, uses self.job_card if not provided)
        
        Returns: dict with is_valid, message, previous_operation, diagnostic
        
        Performance Target: < 1 second
        
        Example:
        >>> engine = DependencyEngine(job_card="JC-2026-002")
        >>> result = engine.validate_previous_operation()
        >>> result['is_valid']
        True
        
        Test Case:
        - test_dv_001_previous_operation_complete
        - test_dv_001_first_operation_no_dependency
        - test_dv_001_previous_operation_not_complete
        """
        if not job_card:
            job_card = self.job_card
        
        if not job_card:
            raise MESDependencyError("Job Card is required for dependency validation")
        
        if isinstance(job_card, str):
            jc = self.repo.get(job_card)
        else:
            jc = job_card
        
        if not jc:
            raise MESDependencyError(f"Job Card {job_card} not found")
        
        # Start performance timing
        import time
        start_time = time.time()
        
        result = {
            'is_valid': True,
            'message': '',
            'previous_operation': None,
            'diagnostic': {}
        }
        
        # DV-001: First operation has no previous dependency
        if not jc.sequence_id or jc.sequence_id == 1:
            result['message'] = "First operation - no previous dependency"
            result['is_valid'] = True
            
            # Log
            execution_time = (time.time() - start_time) * 1000
            log_mes_event(
                module='DEPENDENCY',
                level='INFO',
                business_rule='DV-001',
                message=f"First operation validated for {jc.name}",
                context={
                    'job_card': jc.name,
                    'work_order': jc.work_order,
                    'sequence_id': jc.sequence_id,
                    'execution_time_ms': execution_time
                }
            )
            
            return result
        
        # Get previous Job Card using repository
        prev_op = self.repo.get_previous_operation(jc.name)
        
        if not prev_op:
            result['is_valid'] = False
            result['message'] = "Previous operation Job Card not found"
            result['diagnostic'] = {
                'type': 'error',
                'message': "Cannot find previous operation Job Card",
                'action': "Check Work Order routing configuration"
            }
            
            # Log error
            execution_time = (time.time() - start_time) * 1000
            log_mes_event(
                module='DEPENDENCY',
                level='ERROR',
                business_rule='DV-001',
                message=f"Previous operation not found for {jc.name}",
                context={
                    'job_card': jc.name,
                    'work_order': jc.work_order,
                    'sequence_id': jc.sequence_id,
                    'execution_time_ms': execution_time
                }
            )
            
            return result
        
        # Store previous operation info
        result['previous_operation'] = prev_op
        
        # DV-001: Check if previous operation is completed
        if prev_op.get('status') != "Completed":
            result['is_valid'] = False
            result['message'] = f"Previous operation '{prev_op.get('operation')}' is not completed (Status: {prev_op.get('status')})"
            
            result['diagnostic'] = {
                'type': 'warning',
                'message': f"Operation '{prev_op.get('operation')}' must be completed before starting this operation",
                'action': f"Complete Job Card {prev_op.get('name')} first",
                'previous_job_card': prev_op.get('name'),
                'previous_operation': prev_op.get('operation'),
                'previous_status': prev_op.get('status'),
                'previous_sequence': prev_op.get('sequence_id')
            }
            
            # Log warning
            execution_time = (time.time() - start_time) * 1000
            log_mes_event(
                module='DEPENDENCY',
                level='WARNING',
                business_rule='DV-001',
                message=f"Previous operation not complete for {jc.name}: {prev_op.get('status')}",
                context={
                    'job_card': jc.name,
                    'previous_job_card': prev_op.get('name'),
                    'previous_status': prev_op.get('status'),
                    'execution_time_ms': execution_time
                }
            )
            
            return result
        
        # All checks passed
        result['message'] = "Previous operation completed successfully"
        result['is_valid'] = True
        
        # Log success
        execution_time = (time.time() - start_time) * 1000
        log_mes_event(
            module='DEPENDENCY',
            level='INFO',
            business_rule='DV-001',
            message=f"Previous operation validated for {jc.name}",
            context={
                'job_card': jc.name,
                'previous_job_card': prev_op.get('name'),
                'execution_time_ms': execution_time
            }
        )
        
        return result
    
    def validate_sequence(self, work_order=None):
        """
        Validate operation sequence (DV-002)
        
        Business Rule: DV-002 - Operations must follow the defined sequence 
        without gaps.
        
        Args:
            work_order: Work Order name or document (optional, uses self.work_order)
        
        Returns: dict with is_valid, message, sequence_details, issues
        
        Performance Target: < 1 second
        
        Example:
        >>> engine = DependencyEngine(work_order="WO-2026-001")
        >>> result = engine.validate_sequence()
        >>> result['is_valid']
        True
        
        Test Case:
        - test_dv_002_sequence_valid
        - test_dv_002_sequence_gap
        - test_dv_002_no_job_cards
        """
        if not work_order:
            work_order = self.work_order
        
        if not work_order:
            raise MESDependencyError("Work Order is required for sequence validation")
        
        if isinstance(work_order, str):
            wo = frappe.get_doc("Work Order", work_order)
        else:
            wo = work_order
        
        # Start performance timing
        import time
        start_time = time.time()
        
        result = {
            'is_valid': True,
            'message': '',
            'sequence_details': [],
            'issues': []
        }
        
        # Get sequence details using repository
        sequence = self.repo.get_sequence_details(wo.name)
        
        if not sequence:
            result['message'] = "No Job Cards found for Work Order"
            result['is_valid'] = True
            
            # Log
            execution_time = (time.time() - start_time) * 1000
            log_mes_event(
                module='DEPENDENCY',
                level='INFO',
                business_rule='DV-002',
                message=f"No Job Cards found for {wo.name}",
                context={
                    'work_order': wo.name,
                    'execution_time_ms': execution_time
                }
            )
            
            return result
        
        # DV-002: Validate sequence continuity
        prev_seq = 0
        
        for op in sequence:
            expected_seq = prev_seq + 1
            
            if op['sequence_id'] != expected_seq:
                result['is_valid'] = False
                result['issues'].append({
                    'job_card': op['name'],
                    'operation': op['operation'],
                    'issue': f"Sequence gap: Expected sequence {expected_seq}, found {op['sequence_id']}",
                    'severity': 'High'
                })
            
            prev_seq = op['sequence_id']
            
            result['sequence_details'].append({
                'sequence_id': op['sequence_id'],
                'job_card': op['name'],
                'operation': op['operation'],
                'status': op['status']
            })
        
        # Set message based on validation
        if result['is_valid']:
            result['message'] = f"Operation sequence valid: {len(sequence)} operations in correct order"
        else:
            result['message'] = f"Sequence validation failed: {len(result['issues'])} issue(s) found"
        
        # Log
        execution_time = (time.time() - start_time) * 1000
        log_level = 'ERROR' if not result['is_valid'] else 'INFO'
        
        log_mes_event(
            module='DEPENDENCY',
            level=log_level,
            business_rule='DV-002',
            message=f"Sequence validation for {wo.name}: {'Passed' if result['is_valid'] else 'Failed'}",
            context={
                'work_order': wo.name,
                'total_operations': len(sequence),
                'issues_count': len(result['issues']),
                'execution_time_ms': execution_time
            }
        )
        
        return result
    
    def get_dependency_status(self, job_card=None):
        """
        Get complete dependency status for Job Card
        
        Args:
            job_card: Job Card name or document
        
        Returns: dict with all dependency information
        
        Example:
        >>> engine = DependencyEngine()
        >>> status = engine.get_dependency_status("JC-2026-002")
        >>> status['has_dependencies']
        True
        """
        if not job_card:
            job_card = self.job_card
        
        if isinstance(job_card, str):
            jc = self.repo.get(job_card)
        else:
            jc = job_card
        
        if not jc:
            return {'error': 'Job Card not found'}
        
        # Get previous operation
        prev_op = self.repo.get_previous_operation(jc.name)
        
        # Get next operation
        next_op = self.repo.get_next_operation(jc.name)
        
        return {
            'job_card': jc.name,
            'sequence_id': jc.sequence_id,
            'has_dependencies': prev_op is not None,
            'previous_operation': prev_op,
            'next_operation': next_op,
            'is_first_operation': jc.sequence_id == 1,
            'can_start': prev_op is None or prev_op.get('status') == 'Completed'
        }


@frappe.whitelist()
def validate_previous_operation(job_card):
    """
    Whitelisted API to validate previous operation (DV-001)
    
    Business Rule: DV-001
    
    Args:
        job_card: Job Card name
    
    Returns: dict with is_valid, message, previous_operation, diagnostic
    
    Example:
    >>> result = validate_previous_operation("JC-2026-002")
    >>> result['is_valid']
    True
    
    Test Case:
    - test_dv_001_api_validation
    """
    engine = DependencyEngine(job_card=job_card)
    return engine.validate_previous_operation()


@frappe.whitelist()
def validate_sequence(work_order):
    """
    Whitelisted API to validate operation sequence (DV-002)
    
    Business Rule: DV-002
    
    Args:
        work_order: Work Order name
    
    Returns: dict with is_valid, message, sequence_details, issues
    
    Example:
    >>> result = validate_sequence("WO-2026-001")
    >>> result['is_valid']
    True
    
    Test Case:
    - test_dv_002_api_validation
    """
    engine = DependencyEngine(work_order=work_order)
    return engine.validate_sequence()


@frappe.whitelist()
def get_dependency_status(job_card):
    """
    Whitelisted API to get dependency status
    
    Args:
        job_card: Job Card name
    
    Returns: dict with complete dependency information
    
    Example:
    >>> status = get_dependency_status("JC-2026-002")
    >>> status['has_dependencies']
    True
    """
    engine = DependencyEngine(job_card=job_card)
    return engine.get_dependency_status()


@frappe.whitelist()
def can_job_card_start(job_card):
    """
    Whitelisted API to check if Job Card can start based on dependencies
    
    Combines DV-001 validation with configuration checks
    
    Args:
        job_card: Job Card name
    
    Returns: dict with can_start, reason, validation_details
    
    Example:
    >>> result = can_job_card_start("JC-2026-002")
    >>> result['can_start']
    True
    """
    engine = DependencyEngine(job_card=job_card)
    
    # Check if strict sequence is enabled
    if engine.mes_settings and engine.mes_settings.strict_sequence:
        result = engine.validate_previous_operation()
        
        if not result['is_valid']:
            return {
                'can_start': False,
                'reason': result['message'],
                'validation_details': result,
                'blocked_by': 'DV-001'
            }
    
    # All checks passed
    return {
        'can_start': True,
        'reason': 'All dependency validations passed',
        'validation_details': engine.get_dependency_status(job_card)
    }
