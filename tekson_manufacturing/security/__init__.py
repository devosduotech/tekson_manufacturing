"""
Security Module

Permission validation, role checks, and authorization for MES.
"""

from .security_utils import (
    validate_user_permission_for_work_order,
    validate_user_permission_for_job_card,
    validate_manufacturing_role,
    validate_department_access,
    validate_stock_entry_permission,
    check_role_based_access,
    validate_work_order_ownership,
    log_security_event,
    audit_trail,
    validate_api_access
)

__all__ = [
    'validate_user_permission_for_work_order',
    'validate_user_permission_for_job_card',
    'validate_manufacturing_role',
    'validate_department_access',
    'validate_stock_entry_permission',
    'check_role_based_access',
    'validate_work_order_ownership',
    'log_security_event',
    'audit_trail',
    'validate_api_access'
]
