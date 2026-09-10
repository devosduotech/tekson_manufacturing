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
            frappe.log_error(
                title="MES Stock Entry Hook FIRED",
                message=f"SE: {stock_entry.name} | Purpose: {stock_entry.purpose} | WO: {stock_entry.work_order or 'None'} | User: {frappe.session.user}"
            )

            # Security: Validate SE submit permission (manufacturing role not required for material transfers)
            validate_stock_entry_permission(stock_entry.name)
            
            # Handle Manufacture SE: update WO status to Completed
            if stock_entry.purpose == "Manufacture":
                if stock_entry.work_order:
                    from tekson_manufacturing.execution.execution_engine import ExecutionEngine
                    engine = ExecutionEngine()
                    engine.update_work_order_status(stock_entry.work_order)
                return
            
            # Handle Material Transfer and Material Transfer for Manufacture
            if stock_entry.purpose not in ("Material Transfer", "Material Transfer for Manufacture"):
                frappe.log_error(
                    title="MES SE Hook: Skipped (wrong purpose)",
                    message=f"SE: {stock_entry.name} | Purpose: {stock_entry.purpose}"
                )
                return
            
            from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
            engine = JobCardReadinessEngine()
            
            # Find affected WOs: from SE work_order, or from target warehouse
            wo_names = set()
            
            if stock_entry.work_order:
                wo_names.add(stock_entry.work_order)
            
            # For Material Transfer (MR flow): find WOs by target warehouse
            if not wo_names and stock_entry.items:
                target_warehouses = set(item.t_warehouse for item in stock_entry.items if item.t_warehouse)
                if target_warehouses:
                    jc_list = frappe.get_all("Job Card",
                        filters={"wip_warehouse": ["in", list(target_warehouses)]},
                        fields=["work_order"])
                    for jc in jc_list:
                        if jc.work_order:
                            wo_names.add(jc.work_order)
            
            if not wo_names:
                frappe.log_error(
                    title="MES SE Hook: Skipped (no WOs found)",
                    message=f"SE: {stock_entry.name} | Purpose: {stock_entry.purpose}"
                )
                return
            
            for wo_name in wo_names:
                wo = frappe.get_doc("Work Order", wo_name)
                engine.refresh_work_order(wo)
            
            frappe.log_error(
                title="MES SE Hook: Readiness refresh completed",
                message=f"SE: {stock_entry.name} | Purpose: {stock_entry.purpose} | WOs: {wo_names}"
            )
            
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
            
            # Step 1: Readiness Engine (refresh next JC only)
            from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
            engine = JobCardReadinessEngine()
            engine.refresh_next_job_card(job_card)
            
            # Step 2: Complete WO ONLY if this was the last Job Card
            all_jcs = frappe.get_all("Job Card",
                {"work_order": job_card.work_order},
                ["name", "status", "docstatus"])
            
            pending = [jc for jc in all_jcs 
                       if jc.name != job_card.name 
                       and jc.docstatus != 2 
                       and jc.status != "Completed"]
            
            if len(pending) == 0:
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
