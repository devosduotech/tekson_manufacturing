import frappe
from erpnext.manufacturing.doctype.job_card.job_card import JobCard
from tekson_manufacturing.execution.execution_engine import ExecutionEngine


class TeksonJobCard(JobCard):
    """
    Tekson Custom Job Card
    
    Extends ERPNext JobCard with MES execution logic
    Uses service-oriented architecture
    """

    def on_submit(self):
        """
        On Job Card Submit:
        1. Call parent on_submit
        2. Trigger Execution Engine
        3. Update dependencies
        4. Attempt Work Order completion
        """
        super().on_submit()

        if not self.work_order:
            return

        # Use Execution Engine
        engine = ExecutionEngine()
        
        # Update dependent Job Cards
        self.update_dependent_job_cards()
        
        # Try to complete Work Order
        frappe.db.after_commit.add(
            lambda: engine.complete_work_order(self.work_order)
        )
    
    def update_dependent_job_cards(self):
        """Update status of Job Cards that depend on this one"""
        if not self.sequence_id:
            return
        
        # Get next Job Card
        next_jc = frappe.db.sql("""
            SELECT name
            FROM `tabJob Card`
            WHERE work_order = %s
            AND sequence_id = %s
            AND docstatus = 1
        """, (self.work_order, self.sequence_id + 1), as_dict=True)
        
        if next_jc:
            # Refresh next Job Card status
            from tekson_manufacturing.services.job_card_service import JobCardService
            
            service = JobCardService()
            service.refresh_status(next_jc[0].name)
