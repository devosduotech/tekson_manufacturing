"""
Security Enhancements for MES

Permission validation, role checks, and authorization.
"""

import frappe
from frappe import _
from typing import List, Optional


def validate_user_permission_for_work_order(work_order: str) -> bool:
    """
    Validate user has permission to access Work Order
    
    Args:
        work_order: Work Order name
    
    Returns:
        True if user has permission
    
    Raises:
        frappe.PermissionError: If user lacks permission
    """
    if not frappe.has_permission('Work Order', doc=work_order, ptype='read'):
        frappe.throw(
            _("You do not have permission to access Work Order {0}").format(work_order),
            frappe.PermissionError
        )
    return True


def validate_user_permission_for_job_card(job_card: str) -> bool:
    """
    Validate user has permission to access Job Card
    
    Args:
        job_card: Job Card name
    
    Returns:
        True if user has permission
    
    Raises:
        frappe.PermissionError: If user lacks permission
    """
    if not frappe.has_permission('Job Card', doc=job_card, ptype='read'):
        frappe.throw(
            _("You do not have permission to access Job Card {0}").format(job_card),
            frappe.PermissionError
        )
    return True


def validate_manufacturing_role() -> bool:
    """
    Validate user has Manufacturing role
    
    Returns:
        True if user has role
    
    Raises:
        frappe.PermissionError: If user lacks role
    """
    required_roles = ['Manufacturing User', 'Manufacturing Manager', 'Administrator']
    
    user_roles = frappe.get_roles(frappe.session.user)
    
    if not any(role in user_roles for role in required_roles):
        frappe.throw(
            _("This action requires one of these roles: {0}").format(
                ', '.join(required_roles)
            ),
            frappe.PermissionError
        )
    return True


def validate_department_access(department: str) -> bool:
    """
    Validate user has access to specific department
    
    Args:
        department: Department name
    
    Returns:
        True if user has access
    
    Raises:
        frappe.PermissionError: If user lacks department access
    """
    # Get user's allowed departments
    user = frappe.get_doc('User', frappe.session.user)
    
    # Check if user has department restrictions
    allowed_departments = []
    for role_profile in user.role_profiles:
        role_profile_doc = frappe.get_doc('Role Profile', role_profile.role_profile)
        if role_profile_doc.custom_department:
            allowed_departments.append(role_profile_doc.custom_department)
    
    # If no restrictions, allow all
    if not allowed_departments:
        return True
    
    if department not in allowed_departments:
        frappe.throw(
            _("You do not have access to department {0}").format(department),
            frappe.PermissionError
        )
    
    return True


def validate_stock_entry_permission(stock_entry: str) -> bool:
    """
    Validate user has permission for Stock Entry
    
    Args:
        stock_entry: Stock Entry name
    
    Returns:
        True if user has permission
    
    Raises:
        frappe.PermissionError: If user lacks permission
    """
    if not frappe.has_permission('Stock Entry', doc=stock_entry, ptype='read'):
        frappe.throw(
            _("You do not have permission to access Stock Entry {0}").format(stock_entry),
            frappe.PermissionError
        )
    return True


def check_role_based_access(
    action: str,
    required_roles: Optional[List[str]] = None
) -> bool:
    """
    Check role-based access control
    
    Args:
        action: Action being performed
        required_roles: List of roles required
    
    Returns:
        True if access granted
    
    Raises:
        frappe.PermissionError: If access denied
    """
    if required_roles is None:
        required_roles = ['Manufacturing User']
    
    user_roles = frappe.get_roles(frappe.session.user)
    
    if not any(role in user_roles for role in required_roles):
        frappe.throw(
            _("Action '{0}' requires one of these roles: {1}").format(
                action,
                ', '.join(required_roles)
            ),
            frappe.PermissionError
        )
    
    return True


def validate_work_order_ownership(work_order: str) -> bool:
    """
    Validate user is associated with Work Order
    
    Args:
        work_order: Work Order name
    
    Returns:
        True if user is associated
    
    Raises:
        frappe.PermissionError: If not associated
    """
    wo = frappe.get_doc('Work Order', work_order)
    
    # Check if user created it or is assigned
    if wo.owner == frappe.session.user:
        return True
    
    # Check if user is in same department
    user_department = frappe.db.get_value('User', frappe.session.user, 'department')
    if user_department == wo.department:
        return True
    
    # Managers can access all
    if 'Manufacturing Manager' in frappe.get_roles(frappe.session.user):
        return True
    
    return False


def log_security_event(
    event_type: str,
    user: str,
    doctype: str,
    docname: str,
    action: str,
    success: bool,
    reason: Optional[str] = None
):
    """
    Log security-related events
    
    Args:
        event_type: Type of security event
        user: User who performed action
        doctype: Document type
        docname: Document name
        action: Action performed
        success: Whether action succeeded
        reason: Reason for failure (if applicable)
    """
    frappe.log_error(
        title=f"Security Event: {event_type}",
        message=f"""
User: {user}
Document: {doctype} - {docname}
Action: {action}
Success: {success}
Reason: {reason or 'N/A'}
"""
    )


def audit_trail(
    doctype: str,
    docname: str,
    action: str,
    user: Optional[str] = None
):
    """
    Create audit trail entry
    
    Args:
        doctype: Document type
        docname: Document name
        action: Action performed
        user: User (defaults to current user)
    """
    if user is None:
        user = frappe.session.user
    
    # Create Audit Trail entry if DocType exists
    if frappe.db.exists('DocType', 'Audit Trail'):
        audit = frappe.get_doc({
            'doctype': 'Audit Trail',
            'doctype': doctype,
            'document_name': docname,
            'action': action,
            'user': user,
            'timestamp': frappe.utils.now()
        })
        audit.insert(ignore_permissions=True)


def validate_api_access(method_name: str) -> bool:
    """
    Validate API method access
    
    Args:
        method_name: Name of API method
    
    Returns:
        True if access granted
    
    Raises:
        frappe.PermissionError: If access denied
    """
    # Whitelist check (already handled by @frappe.whitelist)
    # Additional role check
    required_roles = {
        'start_job_card': ['Manufacturing User', 'Manufacturing Manager'],
        'refresh_readiness': ['Manufacturing Manager', 'Administrator'],
        'evaluate_material': ['Manufacturing Manager', 'Stock Manager'],
    }
    
    if method_name in required_roles:
        return check_role_based_access(method_name, required_roles[method_name])
    
    # Default: Manufacturing User
    return check_role_based_access(method_name)
