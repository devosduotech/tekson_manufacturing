"""
MES Execution Coordinator

Central coordinator for MES execution events.

Orchestrates multiple engines:
- Readiness Engine (current)
- Machine Availability Engine (future)
- Quality Hold Engine (future)
- OEE Engine (future)
- Notification Engine (future)

Hooks call Coordinator, Coordinator calls Engines.
Hooks remain stable as MES grows.
"""

import frappe
from frappe import _


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
    def on_work_order_submit(work_order):
        """
        WO Submit = Production Release
        
        Evaluates all Job Cards immediately against current WIP stock.
        
        Args:
            work_order: Work Order document
        """
        from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
        
        engine = JobCardReadinessEngine()
        engine.refresh_work_order(work_order)
    
    @staticmethod
    def on_stock_entry_submit(stock_entry):
        """
        Material Transfer for Manufacture
        
        Refreshes Job Cards for affected Work Order.
        
        Phase 1: Refresh all JCs in WO (simpler)
        Phase 2: Refresh only affected JCs (optimization)
        
        Args:
            stock_entry: Stock Entry document
        """
        if stock_entry.purpose != "Material Transfer for Manufacture":
            return
        
        if not stock_entry.work_order:
            return
        
        from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
        
        engine = JobCardReadinessEngine()
        
        # Get Work Order
        wo = frappe.get_doc('Work Order', stock_entry.work_order)
        
        # Refresh all JCs in this WO
        engine.refresh_work_order(wo)
        
        # Phase 2 Optimization (TODO):
        # Get items transferred in this Stock Entry
        # Get BOM items for WO
        # Match items → refresh only JCs that consume those items
    
    @staticmethod
    def on_job_card_complete(job_card):
        """
        Job Card Completed
        
        Refreshes only next Job Card in sequence.
        
        Rationale:
        - JC-20 complete → refresh JC-30
        - JC-30 will refresh JC-40 when it completes
        - No need to refresh JC-40 now (still blocked by JC-30)
        
        Args:
            job_card: Job Card document
        """
        if job_card.status != "Completed":
            return
        
        from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
        
        engine = JobCardReadinessEngine()
        engine.refresh_next_job_card(job_card)


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
