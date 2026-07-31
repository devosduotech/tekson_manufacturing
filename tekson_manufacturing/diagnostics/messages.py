import frappe
from frappe import _


class DiagnosticMessages:
    """
    Diagnostic Messages Engine
    
    Builds clear, actionable messages for operators
    instead of generic "Cannot Start" errors
    """
    
    def __init__(self):
        pass
    
    def build_material_shortage_message(self, shortage_details):
        """
        Build detailed material shortage message
        
        Args:
            shortage_details: dict with item details, shortage qty, reason, action
        
        Returns: dict with formatted message
        """
        item_code = shortage_details.get('item_code')
        item_name = shortage_details.get('item_name')
        required_qty = shortage_details.get('required_qty')
        available_qty = shortage_details.get('available_qty')
        shortage_qty = shortage_details.get('shortage_qty')
        material_type = shortage_details.get('material_type')
        reason = shortage_details.get('reason')
        action = shortage_details.get('action')
        
        # Build title
        title = f"Material Not Available: {item_name or item_code}"
        
        # Build detailed message
        message = []
        message.append(f"Item: {item_name or item_code}")
        message.append(f"Type: {material_type}")
        message.append(f"Required: {required_qty}")
        message.append(f"Available: {available_qty}")
        message.append(f"Shortage: {shortage_qty}")
        message.append("")
        message.append(f"Reason: {reason}")
        message.append(f"Action: {action}")
        
        return {
            'type': 'error',
            'category': 'material_shortage',
            'title': title,
            'message': "\n".join(message),
            'details': shortage_details,
            'severity': 'high'
        }
    
    def build_previous_operation_message(self, previous_op_details):
        """
        Build previous operation blocking message
        
        Args:
            previous_op_details: dict with previous operation info
        
        Returns: dict with formatted message
        """
        prev_operation = previous_op_details.get('operation')
        prev_status = previous_op_details.get('status')
        prev_jc = previous_op_details.get('job_card')
        
        title = f"Previous Operation Not Complete"
        
        message = []
        message.append(f"Operation: {prev_operation}")
        message.append(f"Status: {prev_status}")
        message.append(f"Job Card: {prev_jc}")
        message.append("")
        message.append("This operation must be completed before you can start.")
        
        return {
            'type': 'warning',
            'category': 'dependency_blocking',
            'title': title,
            'message': "\n".join(message),
            'details': previous_op_details,
            'severity': 'medium'
        }
    
    def build_work_order_not_started_message(self, work_order):
        """
        Build work order not started message
        
        Args:
            work_order: Work Order name or object
        
        Returns: dict with formatted message
        """
        if isinstance(work_order, str):
            wo = frappe.get_doc("Work Order", work_order)
        else:
            wo = work_order
        
        title = f"Work Order Not Started"
        
        message = []
        message.append(f"Work Order: {wo.name}")
        message.append(f"Status: {wo.status}")
        message.append(f"Item: {wo.production_item}")
        message.append(f"Quantity: {wo.qty}")
        message.append("")
        message.append("Work Order must be started before Job Cards can be executed.")
        
        return {
            'type': 'warning',
            'category': 'wo_not_started',
            'title': title,
            'message': "\n".join(message),
            'details': {
                'work_order': wo.name,
                'status': wo.status,
                'item': wo.production_item
            },
            'severity': 'medium'
        }
    
    def build_success_message(self, message="All validations passed"):
        """
        Build success message
        
        Args:
            message: Success message
        
        Returns: dict with formatted message
        """
        return {
            'type': 'success',
            'category': 'validation_passed',
            'title': "Ready to Start",
            'message': message,
            'severity': 'none'
        }
    
    def format_for_ui(self, diagnostics_list):
        """
        Format diagnostics for UI display
        
        Args:
            diagnostics_list: List of diagnostic dicts
        
        Returns: dict with formatted UI output
        """
        if not diagnostics_list:
            return {
                'has_errors': False,
                'messages': [],
                'can_proceed': True
            }
        
        errors = [d for d in diagnostics_list if d.get('type') == 'error']
        warnings = [d for d in diagnostics_list if d.get('type') == 'warning']
        
        return {
            'has_errors': len(errors) > 0,
            'has_warnings': len(warnings) > 0,
            'errors': errors,
            'warnings': warnings,
            'can_proceed': len(errors) == 0,
            'total_issues': len(diagnostics_list)
        }
    
    def get_color_code(self, diagnostic_type):
        """Get color code for diagnostic type"""
        color_map = {
            'error': 'red',
            'warning': 'orange',
            'success': 'green',
            'info': 'blue'
        }
        
        return color_map.get(diagnostic_type, 'gray')


@frappe.whitelist()
def get_diagnostic_message(diagnostic_data):
    """
    Whitelisted method to build diagnostic message
    
    Args:
        diagnostic_data: dict with diagnostic information
    
    Returns: formatted diagnostic message
    """
    engine = DiagnosticMessages()
    
    if diagnostic_data.get('category') == 'material_shortage':
        return engine.build_material_shortage_message(diagnostic_data)
    elif diagnostic_data.get('category') == 'dependency_blocking':
        return engine.build_previous_operation_message(diagnostic_data)
    else:
        return engine.build_success_message()
