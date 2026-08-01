import frappe
from frappe import _
from typing import Dict, List, Any, Optional
from enum import Enum


class DiagnosticCategory(Enum):
    """Diagnostic categories per DM-002"""
    MATERIAL_SHORTAGE = "material_shortage"
    DEPENDENCY_BLOCKING = "dependency_blocking"
    WO_NOT_STARTED = "wo_not_started"
    VALIDATION_PASSED = "validation_passed"
    WARNING = "warning"
    ERROR = "error"
    CONFIGURATION_ERROR = "configuration_error"
    PERMISSION_ERROR = "permission_error"


class SeverityLevel(Enum):
    """Severity levels per DM-003"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DiagnosticMessages:
    """
    Diagnostic Messages Engine - Sprint 4
    
    Builds clear, actionable messages for operators
    instead of generic "Cannot Start" errors
    
    Business Rules:
    - DM-001: Clear Operator Messages
    - DM-002: Diagnostic Categories
    - DM-003: Severity Levels
    - DM-004: UI-Friendly Formatting
    
    Example:
        >>> engine = DiagnosticMessages()
        >>> diagnostic = engine.build_material_shortage_message(shortage_details)
        >>> ui_output = engine.format_for_ui([diagnostic])
    """
    
    def __init__(self):
        self.color_map = {
            'error': '#DC3545',
            'warning': '#FFC107',
            'success': '#28A745',
            'info': '#17A2B8',
            'critical': '#721C24'
        }
    
    def build_material_shortage_message(
        self,
        shortage_details: Dict[str, Any],
        work_order: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build detailed material shortage message per DM-001
        
        Required Format:
        ```
        [Issue Title]
        
        Item: [Item Code/Name]
        Required: [Qty]
        Available: [Qty]
        Shortage: [Qty]
        
        Reason: [Specific reason]
        Action: [Actionable step]
        ```
        
        Args:
            shortage_details: dict with keys:
                - item_code: Item code
                - item_name: Item name (optional)
                - required_qty: Required quantity
                - available_qty: Available quantity
                - shortage_qty: Shortage quantity
                - material_type: Material type
                - reason: Specific reason for shortage
                - action: Actionable step to resolve
            work_order: Work Order name (optional)
        
        Returns:
            dict with formatted message per DM-001
        
        Example:
            >>> details = {
            ...     'item_code': 'COPPER-TUBE-001',
            ...     'item_name': 'Copper Tube',
            ...     'required_qty': 100,
            ...     'available_qty': 60,
            ...     'shortage_qty': 40,
            ...     'material_type': 'Raw Material',
            ...     'reason': 'Stock not transferred from Stores',
            ...     'action': 'Request Stores to transfer 40 kg to WIP-W'
            ... }
            >>> msg = engine.build_material_shortage_message(details)
            >>> msg['title']
            'Material Not Available: Copper Tube'
        """
        item_code = shortage_details.get('item_code', 'Unknown')
        item_name = shortage_details.get('item_name', item_code)
        required_qty = shortage_details.get('required_qty', 0)
        available_qty = shortage_details.get('available_qty', 0)
        shortage_qty = shortage_details.get('shortage_qty', 0)
        material_type = shortage_details.get('material_type', 'Material')
        reason = shortage_details.get('reason', 'Not specified')
        action = shortage_details.get('action', 'Contact Stores Manager')
        warehouse = shortage_details.get('warehouse', work_order or 'N/A')
        
        title = f"Material Not Available: {item_name}"
        
        message_lines = [
            f"<strong>Item:</strong> {item_name} ({item_code})",
            f"<strong>Type:</strong> {material_type}",
            f"<strong>Required:</strong> {required_qty}",
            f"<strong>Available:</strong> {available_qty}",
            f"<strong>Shortage:</strong> {shortage_qty}",
            f"<strong>Warehouse:</strong> {warehouse}",
            "",
            f"<strong>Reason:</strong> {reason}",
            f"<strong>Action Required:</strong> {action}"
        ]
        
        if work_order:
            message_lines.insert(0, f"<strong>Work Order:</strong> {work_order}")
        
        return {
            'type': 'error',
            'category': DiagnosticCategory.MATERIAL_SHORTAGE.value,
            'title': title,
            'message': "<br>".join(message_lines),
            'message_plain': "\n".join([
                f"Item: {item_name} ({item_code})",
                f"Type: {material_type}",
                f"Required: {required_qty}",
                f"Available: {available_qty}",
                f"Shortage: {shortage_qty}",
                "",
                f"Reason: {reason}",
                f"Action: {action}"
            ]),
            'details': shortage_details,
            'severity': SeverityLevel.HIGH.value,
            'can_proceed': False,
            'color': self.color_map['error']
        }
    
    def build_previous_operation_message(
        self,
        previous_op_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build previous operation blocking message per DM-001
        
        Args:
            previous_op_details: dict with keys:
                - operation: Operation name
                - status: Current status
                - job_card: Job Card name
                - department: Department name (optional)
        
        Returns:
            dict with formatted message per DM-001
        
        Example:
            >>> details = {
            ...     'operation': 'Welding',
            ...     'status': 'Work In Progress',
            ...     'job_card': 'JC-2026-001',
            ...     'plant_floor': 'Welding'
            ... }
            >>> msg = engine.build_previous_operation_message(details)
        """
        prev_operation = previous_op_details.get('operation', 'Unknown Operation')
        prev_status = previous_op_details.get('status', 'Unknown')
        prev_jc = previous_op_details.get('job_card', 'N/A')
        department = previous_op_details.get('plant_floor', 'N/A')
        
        title = "Previous Operation Not Complete"
        
        message_lines = [
            f"<strong>Operation:</strong> {prev_operation}",
            f"<strong>Current Status:</strong> {prev_status}",
            f"<strong>Job Card:</strong> {prev_jc}",
            f"<strong>Department:</strong> {department}",
            "",
            "<strong>Action Required:</strong> Wait for previous operation to complete",
            "<strong>Note:</strong> Operations must be completed sequentially"
        ]
        
        return {
            'type': 'warning',
            'category': DiagnosticCategory.DEPENDENCY_BLOCKING.value,
            'title': title,
            'message': "<br>".join(message_lines),
            'message_plain': "\n".join([
                f"Operation: {prev_operation}",
                f"Status: {prev_status}",
                f"Job Card: {prev_jc}",
                "",
                "Action: Wait for previous operation to complete"
            ]),
            'details': previous_op_details,
            'severity': SeverityLevel.MEDIUM.value,
            'can_proceed': False,
            'color': self.color_map['warning']
        }
    
    def build_work_order_not_started_message(
        self,
        work_order: Any
    ) -> Dict[str, Any]:
        """
        Build work order not started message per DM-001
        
        Args:
            work_order: Work Order name or object
        
        Returns:
            dict with formatted message per DM-001
        """
        if isinstance(work_order, str):
            wo = frappe.get_doc("Work Order", work_order)
        else:
            wo = work_order
        
        title = "Work Order Not Started"
        
        message_lines = [
            f"<strong>Work Order:</strong> {wo.name}",
            f"<strong>Item:</strong> {wo.production_item}",
            f"<strong>Quantity:</strong> {wo.qty}",
            f"<strong>Current Status:</strong> {wo.status or 'Not Started'}",
            "",
            "<strong>Action Required:</strong> Start the Work Order",
            "<strong>Note:</strong> Work Order must be started before Job Cards can be executed"
        ]
        
        return {
            'type': 'warning',
            'category': DiagnosticCategory.WO_NOT_STARTED.value,
            'title': title,
            'message': "<br>".join(message_lines),
            'message_plain': "\n".join([
                f"Work Order: {wo.name}",
                f"Item: {wo.production_item}",
                f"Quantity: {wo.qty}",
                f"Status: {wo.status or 'Not Started'}",
                "",
                "Action: Start the Work Order"
            ]),
            'details': {
                'work_order': wo.name,
                'status': wo.status,
                'item': wo.production_item,
                'qty': wo.qty
            },
            'severity': SeverityLevel.MEDIUM.value,
            'can_proceed': False,
            'color': self.color_map['warning']
        }
    
    def build_configuration_error_message(
        self,
        config_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build configuration error message per DM-001
        
        Args:
            config_details: dict with keys:
                - setting_name: MES Setting name
                - expected_value: Expected value
                - actual_value: Actual value (or None if missing)
                - impact: Impact of misconfiguration
        
        Returns:
            dict with formatted message
        """
        setting_name = config_details.get('setting_name', 'MES Setting')
        expected_value = config_details.get('expected_value', 'Configured')
        actual_value = config_details.get('actual_value', 'Not Configured')
        impact = config_details.get('impact', 'System cannot function properly')
        
        title = "Configuration Error"
        
        message_lines = [
            f"<strong>Setting:</strong> {setting_name}",
            f"<strong>Expected:</strong> {expected_value}",
            f"<strong>Current:</strong> {actual_value}",
            "",
            f"<strong>Impact:</strong> {impact}",
            "",
            "<strong>Action Required:</strong> Contact MES Administrator to configure settings"
        ]
        
        return {
            'type': 'error',
            'category': DiagnosticCategory.CONFIGURATION_ERROR.value,
            'title': title,
            'message': "<br>".join(message_lines),
            'message_plain': "\n".join([
                f"Setting: {setting_name}",
                f"Expected: {expected_value}",
                f"Current: {actual_value}",
                "",
                f"Impact: {impact}"
            ]),
            'details': config_details,
            'severity': SeverityLevel.CRITICAL.value,
            'can_proceed': False,
            'color': self.color_map['critical']
        }
    
    def build_permission_error_message(
        self,
        permission_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build permission error message per DM-001
        
        Args:
            permission_details: dict with keys:
                - user: User name
                - role: Required role
                - action: Action attempted
                - doctype: DocType name
        
        Returns:
            dict with formatted message
        """
        user = permission_details.get('user', frappe.session.user)
        role = permission_details.get('role', 'Required Role')
        action = permission_details.get('action', 'perform action')
        doctype = permission_details.get('doctype', 'Document')
        
        title = "Permission Denied"
        
        message_lines = [
            f"<strong>User:</strong> {user}",
            f"<strong>Required Role:</strong> {role}",
            f"<strong>Action:</strong> {action}",
            f"<strong>Document:</strong> {doctype}",
            "",
            "<strong>Action Required:</strong> Contact your manager to request access",
            "<strong>Note:</strong> You do not have permission to perform this action"
        ]
        
        return {
            'type': 'error',
            'category': DiagnosticCategory.PERMISSION_ERROR.value,
            'title': title,
            'message': "<br>".join(message_lines),
            'message_plain': "\n".join([
                f"User: {user}",
                f"Required Role: {role}",
                f"Action: {action}",
                f"Document: {doctype}",
                "",
                "You do not have permission to perform this action"
            ]),
            'details': permission_details,
            'severity': SeverityLevel.HIGH.value,
            'can_proceed': False,
            'color': self.color_map['error']
        }
    
    def build_success_message(
        self,
        message: str = "All validations passed"
    ) -> Dict[str, Any]:
        """
        Build success message per DM-001
        
        Args:
            message: Success message
        
        Returns:
            dict with formatted success message
        """
        return {
            'type': 'success',
            'category': DiagnosticCategory.VALIDATION_PASSED.value,
            'title': "Ready to Start",
            'message': f"<strong>{message}</strong>",
            'message_plain': message,
            'severity': SeverityLevel.NONE.value,
            'can_proceed': True,
            'color': self.color_map['success']
        }
    
    def build_warning_message(
        self,
        warning_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build warning message per DM-003
        
        Args:
            warning_details: dict with keys:
                - title: Warning title
                - message: Warning message
                - impact: Impact if ignored
        
        Returns:
            dict with formatted warning message
        """
        title = warning_details.get('title', 'Warning')
        message = warning_details.get('message', 'Warning message')
        impact = warning_details.get('impact', 'May cause issues')
        
        return {
            'type': 'warning',
            'category': DiagnosticCategory.WARNING.value,
            'title': title,
            'message': f"<strong>Warning:</strong> {message}<br><br><em>{impact}</em>",
            'message_plain': f"Warning: {message}\n\n{impact}",
            'details': warning_details,
            'severity': SeverityLevel.MEDIUM.value,
            'can_proceed': True,
            'color': self.color_map['warning']
        }
    
    def format_for_ui(
        self,
        diagnostics_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Format diagnostics for UI display per DM-004
        
        Requirements:
        - Color coding (red=error, orange=warning, green=success)
        - Clear title
        - Bullet points for details
        - Actionable next steps
        
        Args:
            diagnostics_list: List of diagnostic dicts
        
        Returns:
            dict with formatted UI output
        
        Example:
            >>> diagnostics = [error_diag, warning_diag]
            >>> ui_output = engine.format_for_ui(diagnostics)
            >>> ui_output['has_errors']
            True
            >>> ui_output['can_proceed']
            False
        """
        if not diagnostics_list:
            return {
                'has_errors': False,
                'has_warnings': False,
                'has_success': False,
                'messages': [],
                'can_proceed': True,
                'total_issues': 0
            }
        
        errors = [d for d in diagnostics_list if d.get('type') == 'error']
        warnings = [d for d in diagnostics_list if d.get('type') == 'warning']
        success = [d for d in diagnostics_list if d.get('type') == 'success']
        
        formatted_messages = []
        for diag in diagnostics_list:
            formatted = {
                'type': diag.get('type', 'info'),
                'category': diag.get('category', 'unknown'),
                'title': diag.get('title', 'Message'),
                'message': diag.get('message', ''),
                'severity': diag.get('severity', 'none'),
                'color': diag.get('color', self.color_map.get(diag.get('type', 'info'), '#6C757D')),
                'can_proceed': diag.get('can_proceed', True)
            }
            formatted_messages.append(formatted)
        
        return {
            'has_errors': len(errors) > 0,
            'has_warnings': len(warnings) > 0,
            'has_success': len(success) > 0,
            'errors': errors,
            'warnings': warnings,
            'success': success,
            'messages': formatted_messages,
            'can_proceed': len(errors) == 0,
            'total_issues': len(diagnostics_list),
            'error_count': len(errors),
            'warning_count': len(warnings)
        }
    
    def get_color_code(self, diagnostic_type: str) -> str:
        """
        Get color code for diagnostic type per DM-004
        
        Args:
            diagnostic_type: Type of diagnostic (error, warning, success, info)
        
        Returns:
            Hex color code
        """
        return self.color_map.get(diagnostic_type, '#6C757D')
    
    def build_context_message(
        self,
        diagnostic: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build context-aware diagnostic message per DM-004
        
        Args:
            diagnostic: Base diagnostic dict
            context: Context information with keys:
                - user_role: User role
                - department: User department
                - show_technical: Show technical details (for admins)
        
        Returns:
            dict with context-enhanced message
        """
        user_role = context.get('user_role', 'Operator')
        department = context.get('plant_floor', 'N/A')
        show_technical = context.get('show_technical', False)
        
        enhanced_diagnostic = diagnostic.copy()
        
        context_lines = [
            f"<hr>",
            f"<small>",
            f"<strong>Context:</strong>",
            f"- Role: {user_role}",
            f"- Department: {department}",
        ]
        
        if show_technical:
            context_lines.extend([
                f"- Technical Details: {diagnostic.get('details', {})}",
                f"- Category: {diagnostic.get('category', 'unknown')}",
                f"- Severity: {diagnostic.get('severity', 'none')}"
            ])
        
        context_lines.append(f"</small>")
        
        enhanced_diagnostic['message'] = diagnostic.get('message', '') + "<br>" + "<br>".join(context_lines)
        enhanced_diagnostic['context'] = context
        
        return enhanced_diagnostic
    
    def log_diagnostic(
        self,
        diagnostic: Dict[str, Any],
        reference_doctype: str,
        reference_name: str
    ) -> None:
        """
        Log diagnostic message per DM-004
        
        Args:
            diagnostic: Diagnostic dict to log
            reference_doctype: Reference DocType (e.g., Job Card)
            reference_name: Reference document name
        """
        try:
            frappe.log_error(
                title=f"MES Diagnostic: {diagnostic.get('title', 'Unknown')}",
                message=f"""
Category: {diagnostic.get('category', 'unknown')}
Severity: {diagnostic.get('severity', 'none')}
Type: {diagnostic.get('type', 'info')}
Reference: {reference_doctype} - {reference_name}

Message:
{diagnostic.get('message_plain', diagnostic.get('message', 'No message'))}

Details:
{diagnostic.get('details', {})}
                """.strip()
            )
        except Exception:
            frappe.log_error(
                title="Failed to log MES diagnostic",
                message=f"Diagnostic: {diagnostic.get('title', 'Unknown')}"
            )
    
    def build_aggregated_diagnostic(
        self,
        diagnostics_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build aggregated diagnostic summary
        
        Args:
            diagnostics_list: List of all diagnostics
        
        Returns:
            dict with aggregated summary
        """
        if not diagnostics_list:
            return self.build_success_message("No issues found")
        
        errors = [d for d in diagnostics_list if d.get('type') == 'error']
        warnings = [d for d in diagnostics_list if d.get('type') == 'warning']
        
        summary_lines = []
        
        if errors:
            summary_lines.append(f"<strong>❌ {len(errors)} Error(s) Found:</strong>")
            for i, error in enumerate(errors, 1):
                summary_lines.append(f"{i}. {error.get('title', 'Error')}")
        
        if warnings:
            summary_lines.append(f"<strong>⚠️ {len(warnings)} Warning(s):</strong>")
            for i, warning in enumerate(warnings, 1):
                summary_lines.append(f"{i}. {warning.get('title', 'Warning')}")
        
        return {
            'type': 'error' if errors else 'warning',
            'category': 'aggregated',
            'title': f"Summary: {len(errors)} Errors, {len(warnings)} Warnings",
            'message': "<br>".join(summary_lines),
            'severity': SeverityLevel.HIGH.value if errors else SeverityLevel.MEDIUM.value,
            'can_proceed': len(errors) == 0,
            'error_count': len(errors),
            'warning_count': len(warnings),
            'total_count': len(diagnostics_list)
        }


@frappe.whitelist()
def get_diagnostic_message(
    diagnostic_data: Dict[str, Any],
    work_order: Optional[str] = None
) -> Dict[str, Any]:
    """
    Whitelisted method to build diagnostic message
    
    Args:
        diagnostic_data: dict with diagnostic information
        work_order: Work Order name (optional)
    
    Returns:
        formatted diagnostic message
    
    Example:
        >>> data = {
        ...     'category': 'material_shortage',
        ...     'item_code': 'ITEM-001',
        ...     'shortage_qty': 40
        ... }
        >>> result = get_diagnostic_message(data, "WO-2026-001")
    """
    engine = DiagnosticMessages()
    
    category = diagnostic_data.get('category', '')
    
    if category == 'material_shortage':
        return engine.build_material_shortage_message(diagnostic_data, work_order)
    elif category == 'dependency_blocking':
        return engine.build_previous_operation_message(diagnostic_data)
    elif category == 'wo_not_started':
        return engine.build_work_order_not_started_message(diagnostic_data.get('work_order'))
    elif category == 'configuration_error':
        return engine.build_configuration_error_message(diagnostic_data)
    elif category == 'permission_error':
        return engine.build_permission_error_message(diagnostic_data)
    elif category == 'warning':
        return engine.build_warning_message(diagnostic_data)
    else:
        return engine.build_success_message()


@frappe.whitelist()
def format_diagnostics_for_ui(
    diagnostics_list: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Whitelisted method to format diagnostics for UI
    
    Args:
        diagnostics_list: List of diagnostic dicts
    
    Returns:
        formatted UI output
    
    Example:
        >>> diagnostics = [error_diag, warning_diag]
        >>> result = format_diagnostics_for_ui(diagnostics)
    """
    engine = DiagnosticMessages()
    return engine.format_for_ui(diagnostics_list)


@frappe.whitelist()
def log_diagnostic_message(
    diagnostic_data: Dict[str, Any],
    reference_doctype: str,
    reference_name: str
) -> bool:
    """
    Whitelisted method to log diagnostic message
    
    Args:
        diagnostic_data: Diagnostic dict
        reference_doctype: Reference DocType
        reference_name: Reference document name
    
    Returns:
        True if logged successfully
    
    Example:
        >>> log_diagnostic_message(error_diag, "Job Card", "JC-2026-001")
    """
    engine = DiagnosticMessages()
    engine.log_diagnostic(diagnostic_data, reference_doctype, reference_name)
    return True
