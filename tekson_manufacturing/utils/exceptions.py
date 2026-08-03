"""
MES Custom Exceptions

All MES exceptions inherit from these base classes.
"""

import frappe


class MESValidationError(frappe.ValidationError):
    """
    Base exception for MES validation errors
    
    Use for business rule violations.
    
    Example:
        raise MESValidationError("Job Card cannot start. Previous operation not complete.")
    """
    pass


class MESMaterialError(MESValidationError):
    """
    Exception for material-related errors
    
    Use for MR-010, MR-011 violations.
    
    Example:
        raise MESMaterialError("Materials not transferred to Department Warehouse")
    """
    pass


class MESDependencyError(MESValidationError):
    """
    Exception for dependency validation errors
    
    Use for DV-001, DV-002 violations.
    
    Example:
        raise MESDependencyError("Previous operation not completed")
    """
    pass


class MESPermissionError(frappe.PermissionError):
    """
    Exception for permission errors
    
    Use for SEC-001 to SEC-005 violations.
    
    Example:
        raise MESPermissionError("User does not have permission to start Job Cards in this department")
    """
    pass


class MESConfigurationError(frappe.ValidationError):
    """
    Exception for configuration errors
    
    Use when required configuration is missing.
    
    Example:
        raise MESConfigurationError("Warehouse not configured for Plant Floor CNC")
    """
    pass


class MESExceptionError(frappe.ValidationError):
    """
    Exception for MES exception handling errors
    
    Use when exception handling fails.
    
    Example:
        raise MESExceptionError("Failed to create exception log")
    """
    pass


class MESExecutionError(MESValidationError):
    """
    Exception for execution engine errors
    
    Use for execution-related errors in Job Card submit/cancel.
    
    Example:
        raise MESExecutionError("Failed to execute Job Card completion logic")
    """
    pass
