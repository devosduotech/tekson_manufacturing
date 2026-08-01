"""
MES Utilities

Common utility functions for MES.
"""

import frappe
import json
from datetime import datetime


def log_mes_event(module, level, business_rule, message, context=None):
    """
    Standard MES logging function
    
    Args:
        module: Module code (EXECUTION, MATERIAL, DEPENDENCY, etc.)
        level: Log level (INFO, WARNING, ERROR, CRITICAL)
        business_rule: Business rule code (MR-010, DV-001, etc.)
        message: Human-readable message
        context: dict with relevant document references
    
    Example:
        >>> log_mes_event(
        ...     module='MATERIAL',
        ...     level='INFO',
        ...     business_rule='MR-010',
        ...     message='Material readiness evaluated',
        ...     context={'work_order': 'WO-2026-001', 'is_ready': True}
        ... )
    """
    if context is None:
        context = {}
    
    # Add standard context
    context['timestamp'] = datetime.now().isoformat()
    context['user'] = frappe.session.user if hasattr(frappe, 'session') else 'System'
    
    # Format message
    formatted_message = f"[MES] [{module}] [{level}] [{business_rule}] {message} | Context: {json.dumps(context)}"
    
    # Log
    frappe.log_error(
        message=formatted_message,
        title=f"MES {module} - {business_rule}"
    )


def get_mes_settings():
    """
    Get MES Settings document
    
    Returns: MES Settings document or None if not found
    
    Example:
        >>> settings = get_mes_settings()
        >>> settings.allow_partial_transfer
        1
    """
    try:
        return frappe.get_doc("MES Settings", "MES Settings")
    except Exception:
        return None


def validate_user_permission(doctype, docname, action):
    """
    Validate user has permission for action
    
    Args:
        doctype: DocType name
        docname: Document name
        action: Action (read, write, submit, cancel)
    
    Returns: True if user has permission
    
    Raises:
        MESPermissionError: If user doesn't have permission
    """
    if not frappe.has_permission(doctype, action, docname):
        from tekson_manufacturing.utils.exceptions import MESPermissionError
        
        log_mes_event(
            module='SECURITY',
            level='ERROR',
            business_rule='SEC-001',
            message=f"Permission denied for {action}",
            context={
                'doctype': doctype,
                'docname': docname,
                'user': frappe.session.user
            }
        )
        
        raise MESPermissionError(
            f"You do not have permission to {action} {doctype} {docname}"
        )
    
    return True


def parse_json_field(field_value):
    """
    Parse JSON field value
    
    Args:
        field_value: JSON string or dict
    
    Returns: dict
    
    Example:
        >>> parse_json_field('{"key": "value"}')
        {'key': 'value'}
        >>> parse_json_field({'key': 'value'})
        {'key': 'value'}
    """
    if isinstance(field_value, dict):
        return field_value
    
    if isinstance(field_value, str):
        try:
            return json.loads(field_value)
        except json.JSONDecodeError:
            return {}
    
    return {}


def format_quantity(qty, precision=None):
    """
    Format quantity for display
    
    Args:
        qty: Quantity value
        precision: Decimal precision (optional)
    
    Returns: Formatted quantity string
    
    Example:
        >>> format_quantity(100.5678, 2)
        '100.57'
    """
    if precision is None:
        precision = frappe.db.get_default("float_precision") or 2
    
    return f"{float(qty):.{precision}f}"


def get_department_from_user(user=None):
    """
    Get department from user
    
    Args:
        user: User name (optional, defaults to current user)
    
    Returns: Department name or None
    
    Example:
        >>> get_department_from_user("user@example.com")
        'CNC'
    """
    if not user:
        user = frappe.session.user
    
    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    
    if employee:
        return frappe.db.get_value("Employee", employee, "plant_floor")
    
    return None


def is_user_in_role(role):
    """
    Check if current user has role
    
    Args:
        role: Role name
    
    Returns: True if user has role
    
    Example:
        >>> is_user_in_role("Manufacturing Manager")
        True
    """
    user_roles = frappe.get_roles()
    return role in user_roles
