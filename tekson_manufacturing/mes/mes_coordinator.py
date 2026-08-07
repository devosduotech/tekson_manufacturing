"""
MES Execution Coordinator

Central coordinator for MES execution events.

Orchestrates multiple engines:
- Execution Engine (legacy tracking)
- Readiness Engine (current)
- Machine Availability Engine (future)
- Quality Hold Engine (future)
- OEE Engine (future)
- Notification Engine (future)

Hooks call Coordinator ONLY, Coordinator calls all Engines.
Hooks remain stable as MES grows.

Architecture:
    Hook → Coordinator → Execution Engine → Readiness Engine

Security:
    - Permission validation on all operations
    - Role-based access control
    - Audit trail logging
"""

import frappe
from frappe import _
from typing import Any, Optional

from tekson_manufacturing.security.security_utils import (
    validate_user_permission_for_work_order,
    validate_user_permission_for_job_card,
    validate_stock_entry_permission,
    validate_manufacturing_role,
    log_security_event
)


class MESExecutionCoordinator:
    """
    Central coordinator for MES execution events.
    
    Usage in hooks:
        doc_events = {
            "Work Order": {
                "on_submit": "tekson_manufacturing.mes.mes_coordinator.on_work_order_submit",
            },
            "Stock Entry": {
                "on_submit": "tekson_manufacturing.mes.mes_coordinator.on_stock_entry_submit",
            },
            "Job Card": {
                "on_submit": "tekson_manufacturing.mes.mes_coordinator.on_job_card_complete",
            },
        }
    """
    
    @staticmethod
    def on_work_order_submit(work_order: Any):
        """
        WO Submit = Production Release
        
        Orchestrates:
        1. Permission validation
        2. Execution Engine (legacy tracking)
        3. Readiness Engine (evaluate all JCs)
        
        Args:
            work_order: Work Order document
        
        Performance Target: < 2 seconds for 40 Job Cards
        
        Security:
        - Validates user permission for WO
        - Validates manufacturing role
        - Logs security event
        """
        try:
            # Security: Validate permissions
            validate_user_permission_for_work_order(work_order.name)
            validate_manufacturing_role()
            
            # Step 1: Readiness Engine (evaluate all JCs)
            from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
            engine = JobCardReadinessEngine()
            engine.refresh_work_order(work_order)
            
            # Log success
            log_security_event(
                event_type='WO_SUBMIT',
                user=frappe.session.user,
                doctype='Work Order',
                docname=work_order.name,
                action='Submit and Evaluate',
                success=True
            )
            
        except Exception as e:
            # Log error
            log_security_event(
                event_type='WO_SUBMIT_ERROR',
                user=frappe.session.user,
                doctype='Work Order',
                docname=work_order.name if hasattr(work_order, 'name') else 'Unknown',
                action='Submit and Evaluate',
                success=False,
                reason=str(e)
            )
            
            frappe.log_error(
                title=f"MES Coordinator Error: WO Submit {work_order.name if hasattr(work_order, 'name') else 'Unknown'}",
                message=f"Error coordinating WO submit: {str(e)}"
            )
            raise
    
    @staticmethod
    def on_stock_entry_submit(stock_entry: Any):
        """
        Material Transfer for Manufacture
        
        Orchestrates:
        1. Permission validation
        2. Execution Engine (legacy tracking)
        3. Readiness Engine (refresh affected WO)
        
        Args:
            stock_entry: Stock Entry document
        
        Performance Target: < 3 seconds for 40 Job Cards
        
        Security:
        - Validates user permission for Stock Entry
        - Validates manufacturing role
        - Logs security event
        """
        try:
            # Security: Validate permissions
            validate_stock_entry_permission(stock_entry.name)
            validate_manufacturing_role()
            
            # Skip if not Material Transfer for Manufacture
            if stock_entry.purpose != "Material Transfer for Manufacture":
                return
            
            if not stock_entry.work_order:
                return
            
            # Step 1: Execution Engine (legacy tracking)
            from tekson_manufacturing.execution.execution_engine import on_stock_entry_submit as exec_handler
            exec_handler(stock_entry, method=None)
            
            # Step 2: Readiness Engine (refresh affected WO)
            from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
            engine = JobCardReadinessEngine()
            
            # Get Work Order
            wo = frappe.get_doc('Work Order', stock_entry.work_order)
            
            # Validate WO permission
            validate_user_permission_for_work_order(wo.name)
            
            # Refresh all JCs in this WO
            engine.refresh_work_order(wo)
            
            # Log success
            log_security_event(
                event_type='STOCK_ENTRY_SUBMIT',
                user=frappe.session.user,
                doctype='Stock Entry',
                docname=stock_entry.name,
                action='Material Transfer',
                success=True
            )
            
        except Exception as e:
            # Log error
            log_security_event(
                event_type='STOCK_ENTRY_SUBMIT_ERROR',
                user=frappe.session.user,
                doctype='Stock Entry',
                docname=stock_entry.name if hasattr(stock_entry, 'name') else 'Unknown',
                action='Material Transfer',
                success=False,
                reason=str(e)
            )
            
            frappe.log_error(
                title=f"MES Coordinator Error: Stock Entry Submit {stock_entry.name if hasattr(stock_entry, 'name') else 'Unknown'}",
                message=f"Error coordinating Stock Entry submit: {str(e)}"
            )
            raise
    
    @staticmethod
    def on_job_card_complete(job_card: Any):
        """
        Job Card Completed
        
        Orchestrates:
        1. Permission validation
        2. Execution Engine (legacy tracking)
        3. Readiness Engine (refresh next JC only)
        
        Rationale:
        - JC-20 complete → refresh JC-30
        - JC-30 will refresh JC-40 when it completes
        - No need to refresh JC-40 now (still blocked by JC-30)
        
        Args:
            job_card: Job Card document
        
        Performance Target: < 1 second
        
        Security:
        - Validates user permission for JC
        - Validates manufacturing role
        - Logs security event
        """
        try:
            # Security: Validate permissions
            validate_user_permission_for_job_card(job_card.name)
            validate_manufacturing_role()
            
            # Skip if not completed
            if job_card.status != "Completed":
                return
            
            # Step 1: Execution Engine (legacy tracking)
            from tekson_manufacturing.execution.execution_engine import on_job_card_submit as exec_handler
            exec_handler(job_card, method=None)
            
            # Step 2: Readiness Engine (refresh next JC only)
            from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
            engine = JobCardReadinessEngine()
            engine.refresh_next_job_card(job_card)
            
            # Step 3: Enqueue WO completion (runs in separate worker after commit)
            frappe.enqueue(
                "tekson_manufacturing.execution.execution_engine.complete_work_order_api",
                work_order=job_card.work_order,
                queue="short",
                timeout=30
            )
            
            # Log success
            log_security_event(
                event_type='JOB_CARD_COMPLETE',
                user=frappe.session.user,
                doctype='Job Card',
                docname=job_card.name,
                action='Operation Complete',
                success=True
            )
            
        except Exception as e:
            # Log error
            log_security_event(
                event_type='JOB_CARD_COMPLETE_ERROR',
                user=frappe.session.user,
                doctype='Job Card',
                docname=job_card.name if hasattr(job_card, 'name') else 'Unknown',
                action='Operation Complete',
                success=False,
                reason=str(e)
            )
            
            frappe.log_error(
                title=f"MES Coordinator Error: Job Card Complete {job_card.name if hasattr(job_card, 'name') else 'Unknown'}",
                message=f"Error coordinating Job Card complete: {str(e)}"
            )
            raise


# =============================================================================
# Hook Handlers (thin wrappers)
# =============================================================================

def on_work_order_submit(doc, method):
    """Work Order submit hook handler"""
    coordinator = MESExecutionCoordinator()
    coordinator.on_work_order_submit(doc)

def on_stock_entry_submit(doc, method):
    """Stock Entry submit hook handler"""
    coordinator = MESExecutionCoordinator()
    coordinator.on_stock_entry_submit(doc)

def on_job_card_complete(doc, method):
    """Job Card submit hook handler"""
    coordinator = MESExecutionCoordinator()
    coordinator.on_job_card_complete(doc)
