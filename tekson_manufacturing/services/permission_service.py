"""
MES Security & Permissions Service - Sprint 7

Implements department-scoped permissions, role-based access control,
approval trails, override logging, and segregation of duties.

Business Rules:
- SEC-001: Permission Check
- SEC-002: Department Scope
- SEC-003: Approval Trail
- SEC-004: Override Logging
- SEC-005: Segregation of Duties
"""

import frappe
from frappe import _
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List


class PermissionService:
    """
    Permission Service - Central interface for security operations
    
    Business Rules:
    - SEC-001: Permission Check
    - SEC-002: Department Scope
    - SEC-003: Approval Trail
    - SEC-004: Override Logging
    - SEC-005: Segregation of Duties
    """
    
    def __init__(self):
        self.mes_settings = self._get_mes_settings()
    
    def _get_mes_settings(self) -> Dict:
        """Get MES settings"""
        try:
            return frappe.get_doc("MES Settings", "MES Settings")
        except:
            return frappe._dict()
    
    def check_permission(
        self,
        user: str,
        action: str,
        doctype: str,
        docname: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> bool:
        """
        Check if user has permission for action (SEC-001)
        
        Business Rules:
        - SEC-001: Permission Check
        
        Args:
            user: User name
            action: Action to perform (read, write, submit, cancel)
            doctype: DocType name
            docname: Document name (optional)
            context: Additional context
        
        Returns:
            True if user has permission
        
        Raises:
            frappe.PermissionError: If user lacks permission
        
        Example:
            >>> service = PermissionService()
            >>> service.check_permission("user@example.com", "write", "Job Card", "JC-001")
            True
        """
        # Check if permissions are enabled
        if not self.mes_settings.get('enable_permissions', 1):
            return True
        
        # Check standard ERPNext permissions
        if not frappe.has_permission(doctype, action):
            self._log_permission_check(
                user, action, doctype, docname,
                success=False, reason="Standard permission denied"
            )
            frappe.throw(
                _("You do not have permission to {0} {1}").format(action, doctype),
                frappe.PermissionError
            )
        
        # Check role-based permissions
        user_roles = frappe.get_roles(user)
        required_roles = self._get_required_roles(action, doctype)
        
        if required_roles and not any(role in user_roles for role in required_roles):
            self._log_permission_check(
                user, action, doctype, docname,
                success=False, reason=f"Required roles: {required_roles}"
            )
            frappe.throw(
                _("You need one of these roles to {0}: {1}").format(
                    action, ", ".join(required_roles)
                ),
                frappe.PermissionError
            )
        
        # Check department scope (SEC-002)
        if self.mes_settings.get('department_scope', 1):
            self.check_department_scope(user, doctype, docname)
        
        # Log successful permission check
        self._log_permission_check(
            user, action, doctype, docname,
            success=True, context=context
        )
        
        return True
    
    def check_department_scope(
        self,
        user: str,
        doctype: str,
        docname: Optional[str] = None
    ) -> bool:
        """
        Check department scope restriction (SEC-002)
        
        Business Rules:
        - SEC-002: Department Scope
        
        Args:
            user: User name
            doctype: DocType name
            docname: Document name (optional)
        
        Returns:
            True if user can access document
        
        Raises:
            frappe.PermissionError: If document is outside user's department
        """
        # Get user's department
        user_department = frappe.db.get_value(
            "Employee",
            {"user_id": user},
            "department"
        )
        
        if not user_department:
            # User has no department restriction
            return True
        
        # Get document's department
        doc_department = self._get_document_department(doctype, docname)
        
        if not doc_department:
            # Document has no department
            return True
        
        # Check if departments match
        if user_department != doc_department:
            self._log_department_scope_violation(
                user, user_department, doctype, docname, doc_department
            )
            frappe.throw(
                _("You can only access {0} in your department ({1})").format(
                    doctype, user_department
                ),
                frappe.PermissionError
            )
        
        return True
    
    def _get_document_department(self, doctype: str, docname: str) -> Optional[str]:
        """Get department from document"""
        if not docname:
            return None
        
        # Try to get department from common fields
        department_fields = ['department', 'plant_floor', 'workstation']
        
        for field in department_fields:
            dept = frappe.db.get_value(doctype, docname, field)
            if dept:
                return dept
        
        # For Job Card, get from Workstation
        if doctype == "Job Card":
            workstation = frappe.db.get_value(doctype, docname, "workstation")
            if workstation:
                return frappe.db.get_value("Workstation", workstation, "department")
        
        # For Work Order, get from Warehouse
        if doctype == "Work Order":
            warehouse = frappe.db.get_value(doctype, docname, "source_warehouse")
            if warehouse:
                warehouse_group = frappe.db.get_value("Warehouse", warehouse, "warehouse_group")
                if warehouse_group == "Work In Progress Stores":
                    # Extract department from warehouse name
                    if warehouse.startswith("WIP-"):
                        return warehouse.replace("WIP-", "")
        
        return None
    
    def check_session_timeout(self, user: str) -> bool:
        """
        Check if user session has timed out (SEC-003)
        
        Business Rules:
        - SEC-003: Approval Trail (session tracking)
        
        Args:
            user: User name
        
        Returns:
            True if session is valid
        
        Raises:
            frappe.SessionExpired: If session has timed out
        """
        timeout_seconds = self.mes_settings.get('session_timeout', 3600)
        
        # Get last activity time
        last_activity = frappe.db.get_value(
            "User",
            user,
            "last_active"
        )
        
        if not last_activity:
            return True
        
        # Check if session has expired
        if datetime.now() - last_activity > timedelta(seconds=timeout_seconds):
            frappe.throw(
                _("Your session has expired. Please log in again."),
                frappe.SessionExpired
            )
        
        return True
    
    def check_override_permission(
        self,
        user: str,
        action: str,
        reason: str,
        doctype: str,
        docname: str
    ) -> bool:
        """
        Check if user can override validation (SEC-004)
        
        Business Rules:
        - SEC-004: Override Logging
        
        Args:
            user: User name
            action: Action being overridden
            reason: Reason for override
            doctype: DocType name
            docname: Document name
        
        Returns:
            True if override is allowed
        
        Raises:
            frappe.PermissionError: If user cannot override
        """
        # Check if user has override role
        override_role = self.mes_settings.get('allow_override_role', 'Manufacturing Manager')
        
        if override_role not in frappe.get_roles(user):
            frappe.throw(
                _("You need '{0}' role to override validations").format(override_role),
                frappe.PermissionError
            )
        
        # Log override
        self._log_override(user, action, reason, doctype, docname)
        
        return True
    
    def log_action(
        self,
        user: str,
        action: str,
        doctype: str,
        docname: str,
        success: bool,
        details: Optional[Dict] = None
    ) -> None:
        """
        Log user action for audit trail (SEC-005)
        
        Business Rules:
        - SEC-005: Segregation of Duties
        
        Args:
            user: User name
            action: Action performed
            doctype: DocType name
            docname: Document name
            success: Whether action succeeded
            details: Additional details
        """
        if not self.mes_settings.get('log_all_actions', 1):
            return
        
        log_entry = frappe.get_doc({
            'doctype': 'MES Action Log',
            'user': user,
            'action': action,
            'doctype': doctype,
            'docname': docname,
            'success': success,
            'details': frappe.as_json(details) if details else None,
            'timestamp': datetime.now(),
            'ip_address': frappe.local.request_ip if hasattr(frappe.local, 'request_ip') else None
        })
        
        try:
            log_entry.insert(ignore_permissions=True)
        except:
            # Fallback to error log
            frappe.log_error(
                title=f"MES Action Log: {action}",
                message=f"User: {user}, DocType: {doctype}, DocName: {docname}"
            )
    
    def check_segregation_of_duties(
        self,
        user: str,
        action: str,
        doctype: str,
        docname: str
    ) -> bool:
        """
        Check segregation of duties (SEC-005)
        
        Business Rules:
        - SEC-005: Segregation of Duties
        
        Args:
            user: User name
            action: Action to perform
            doctype: DocType name
            docname: Document name
        
        Returns:
            True if segregation rules are satisfied
        
        Raises:
            frappe.ValidationError: If segregation rules violated
        """
        # Get creator of document
        creator = frappe.db.get_value(doctype, docname, 'owner')
        
        # Check specific segregation rules
        segregation_rules = {
            ('Stock Entry', 'submit'): ['create', 'write'],
            ('Job Card', 'submit'): ['create', 'write'],
            ('Work Order', 'submit'): ['create', 'write']
        }
        
        rule_key = (doctype, action)
        if rule_key in segregation_rules:
            restricted_actions = segregation_rules[rule_key]
            
            # Check if user created the document
            if creator == user and 'create' in restricted_actions:
                # Get approver role
                approver_role = 'Manufacturing Manager'
                
                if approver_role not in frappe.get_roles(user):
                    frappe.throw(
                        _("You cannot approve your own {0}. Please get approval from {1}").format(
                            doctype, approver_role
                        ),
                        frappe.ValidationError
                    )
        
        return True
    
    def _get_required_roles(self, action: str, doctype: str) -> List[str]:
        """Get required roles for action"""
        role_mapping = {
            ('Job Card', 'start'): ['Operator', 'Department Manager'],
            ('Job Card', 'complete'): ['Operator', 'Department Manager'],
            ('Stock Entry', 'submit'): ['Stores Manager', 'Department Manager'],
            ('Work Order', 'submit'): ['Production Manager'],
        }
        
        return role_mapping.get((doctype, action), [])
    
    def _log_permission_check(
        self,
        user: str,
        action: str,
        doctype: str,
        docname: str,
        success: bool,
        reason: str = None,
        context: Dict = None
    ) -> None:
        """Log permission check"""
        if not self.mes_settings.get('log_all_actions', 1):
            return
        
        log_level = "INFO" if success else "ERROR"
        message = f"[MES] [SECURITY] [{log_level}] [SEC-001] "
        message += f"Permission {'granted' if success else 'denied'} for {user}: "
        message += f"{action} on {doctype}"
        
        if docname:
            message += f" ({docname})"
        
        if reason:
            message += f" | Reason: {reason}"
        
        if context:
            message += f" | Context: {context}"
        
        if success:
            frappe.log_error(title="MES Permission Check", message=message)
        else:
            frappe.log_error(title="MES Permission Denied", message=message)
    
    def _log_department_scope_violation(
        self,
        user: str,
        user_department: str,
        doctype: str,
        docname: str,
        doc_department: str
    ) -> None:
        """Log department scope violation"""
        message = f"[MES] [SECURITY] [WARNING] [SEC-002] "
        message += f"Department scope violation: {user} ({user_department}) "
        message += f"tried to access {doctype} {docname} in {doc_department}"
        
        frappe.log_error(title="MES Department Scope Violation", message=message)
    
    def _log_override(
        self,
        user: str,
        action: str,
        reason: str,
        doctype: str,
        docname: str
    ) -> None:
        """Log override action"""
        message = f"[MES] [SECURITY] [WARNING] [SEC-004] "
        message += f"Override: {user} overrode {action} on {doctype} {docname} | "
        message += f"Reason: {reason}"
        
        frappe.log_error(title="MES Override", message=message)
        
        # Also create audit log entry
        self.log_action(
            user=user,
            action=f"OVERRIDE: {action}",
            doctype=doctype,
            docname=docname,
            success=True,
            details={'reason': reason}
        )


# Convenience functions

@frappe.whitelist()
def check_permission(user, action, doctype, docname=None):
    """
    Whitelisted method to check permission
    
    Args:
        user: User name
        action: Action to perform
        doctype: DocType name
        docname: Document name (optional)
    
    Returns:
        dict with has_permission and message
    """
    service = PermissionService()
    
    try:
        result = service.check_permission(user, action, doctype, docname)
        return {
            'has_permission': True,
            'message': 'Permission granted'
        }
    except frappe.PermissionError as e:
        return {
            'has_permission': False,
            'message': str(e)
        }


@frappe.whitelist()
def check_department_scope(user, doctype, docname=None):
    """
    Whitelisted method to check department scope
    
    Args:
        user: User name
        doctype: DocType name
        docname: Document name (optional)
    
    Returns:
        dict with in_scope and message
    """
    service = PermissionService()
    
    try:
        result = service.check_department_scope(user, doctype, docname)
        return {
            'in_scope': True,
            'message': 'User can access document'
        }
    except frappe.PermissionError as e:
        return {
            'in_scope': False,
            'message': str(e)
        }


@frappe.whitelist()
def log_user_action(user, action, doctype, docname, success=True, details=None):
    """
    Whitelisted method to log user action
    
    Args:
        user: User name
        action: Action performed
        doctype: DocType name
        docname: Document name
        success: Whether action succeeded
        details: Additional details (JSON)
    
    Returns:
        dict with logged status
    """
    import json
    
    if isinstance(details, str):
        details = json.loads(details)
    
    service = PermissionService()
    service.log_action(user, action, doctype, docname, success, details)
    
    return {
        'logged': True,
        'message': 'Action logged successfully'
    }
