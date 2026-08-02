import frappe
from frappe import _


class JobCardService:
    """
    Job Card Service - Reusable business logic for Job Cards
    
    All Job Card operations go through this service layer.
    No duplicated logic in controllers, APIs, or UI.
    """
    
    def __init__(self):
        pass
    
    def get_job_card_details(self, job_card):
        """Get complete Job Card details with related info"""
        if isinstance(job_card, str):
            jc = frappe.get_doc("Job Card", job_card)
        else:
            jc = job_card
        
        jc.reload()
        
        # Get Work Order details
        wo_details = None
        if jc.work_order:
            wo = frappe.get_doc("Work Order", jc.work_order)
            wo_details = {
                'name': wo.name,
                'production_item': wo.production_item,
                'status': wo.status,
                'qty': wo.qty,
                'produced_qty': wo.produced_qty
            }
        
        # Get previous operation status
        prev_op_status = None
        if jc.sequence_id and jc.sequence_id > 1:
            prev_op_status = self.get_previous_operation_status(jc)
        
        # Get material readiness
        material_readiness = None
        if jc.work_order:
            material_readiness = self.get_material_readiness_status(jc.work_order)
        
        return {
            'job_card': jc.as_dict(),
            'work_order': wo_details,
            'previous_operation': prev_op_status,
            'material_readiness': material_readiness
        }
    
    def get_previous_operation_status(self, job_card):
        """Get previous operation status"""
        if not job_card.sequence_id or job_card.sequence_id == 1:
            return None
        
        prev_jc = frappe.db.sql("""
            SELECT name, operation, status, sequence_id
            FROM `tabJob Card`
            WHERE work_order = %s
            AND sequence_id = %s
            AND docstatus = 1
        """, (job_card.work_order, job_card.sequence_id - 1), as_dict=True)
        
        return prev_jc[0] if prev_jc else None
    
    def get_material_readiness_status(self, work_order):
        """Get material readiness status for Work Order"""
        from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
        
        engine = MaterialReadinessEngine(work_order=work_order)
        return engine.evaluate_material_readiness()
    
    def can_start(self, job_card):
        """Check if Job Card can start"""
        from tekson_manufacturing.execution.execution_engine import ExecutionEngine
        
        engine = ExecutionEngine()
        return engine.can_job_card_start(job_card)
    
    def can_complete(self, job_card):
        """Check if Job Card can complete"""
        from tekson_manufacturing.execution.execution_engine import ExecutionEngine
        
        engine = ExecutionEngine()
        return engine.can_job_card_complete(job_card)
    
    def refresh_status(self, job_card):
        """Refresh Job Card status fields"""
        if isinstance(job_card, str):
            jc = frappe.get_doc("Job Card", job_card)
        else:
            jc = job_card
        
        # Update custom start status
        self.update_start_status(jc)
        
        # Update dependency status
        self.update_dependency_status(jc)
        
        # Update material status
        self.update_material_status(jc)
        
        jc.save(ignore_permissions=True)
        frappe.db.commit()
    
    def update_start_status(self, job_card):
        """
        Update custom_start_status field based on UAT requirements
        
        Status Values:
        - Awaiting
        - Awaiting Previous Operation
        - Awaiting Material
        - Material Available
        - Ready to Start
        - In Progress
        - Completed
        """
        if job_card.status == "Completed":
            job_card.custom_start_status = "Completed"
        elif job_card.status == "Work In Progress":
            job_card.custom_start_status = "In Progress"
        else:
            # Check dependencies first
            prev_op_result = self.get_previous_operation_status(job_card)
            
            if prev_op_result and prev_op_result.get('status') != "Completed":
                job_card.custom_start_status = "Awaiting Previous Operation"
                return
            
            # Check material availability
            if job_card.work_order:
                from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
                
                engine = MaterialReadinessEngine(work_order=job_card.work_order)
                readiness = engine.evaluate_material_readiness()
                
                if not readiness['is_ready']:
                    job_card.custom_start_status = "Awaiting Material"
                else:
                    job_card.custom_start_status = "Material Available"
            else:
                job_card.custom_start_status = "Awaiting"
    
    def update_dependency_status(self, job_card):
        """
        Update custom_dependency_check and custom_can_start_operation
        
        Business Rules:
        - custom_dependency_check: 1 if all previous operations complete
        - custom_can_start_operation: 1 if ready to start
        """
        # Check previous operations
        prev_op_result = self.get_previous_operation_status(job_card)
        
        if not prev_op_result or prev_op_result.get('status') == "Completed":
            job_card.custom_dependency_check = 1
        else:
            job_card.custom_dependency_check = 0
        
        # Can start if dependency check passed AND materials available
        if job_card.custom_dependency_check == 1:
            # Check material availability
            if job_card.work_order:
                from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
                
                engine = MaterialReadinessEngine(work_order=job_card.work_order)
                readiness = engine.evaluate_material_readiness()
                
                if readiness['is_ready']:
                    job_card.custom_can_start_operation = 1
                else:
                    job_card.custom_can_start_operation = 0
            else:
                job_card.custom_can_start_operation = 1
        else:
            job_card.custom_can_start_operation = 0
    
    def update_material_status(self, job_card):
        """
        Update custom_material_available_for_operation and custom_material_status_details
        
        Business Rules:
        - custom_material_available_for_operation: 1 if materials available
        - custom_material_status_details: Detailed status message
        """
        if not job_card.work_order:
            job_card.custom_material_available_for_operation = 0
            job_card.custom_material_status_details = "Work Order not linked"
            return
        
        from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
        
        engine = MaterialReadinessEngine(work_order=job_card.work_order)
        readiness = engine.evaluate_material_readiness()
        
        if readiness['is_ready']:
            job_card.custom_material_available_for_operation = 1
            job_card.custom_material_status_details = "Material available in WIP"
        else:
            job_card.custom_material_available_for_operation = 0
            
            # Build detailed message
            missing_items = readiness.get('missing_items', [])
            
            if missing_items:
                job_card.custom_material_status_details = "Missing: " + ", ".join(missing_items[:3])
                if len(missing_items) > 3:
                    job_card.custom_material_status_details += f" (+{len(missing_items) - 3} more)"
            else:
                job_card.custom_material_status_details = "Material shortage"


class WorkOrderService:
    """
    Work Order Service - Reusable business logic for Work Orders
    """
    
    def __init__(self):
        pass
    
    def get_work_order_details(self, work_order):
        """Get complete Work Order details"""
        if isinstance(work_order, str):
            wo = frappe.get_doc("Work Order", work_order)
        else:
            wo = work_order
        
        wo.reload()
        
        # Get all Job Cards
        job_cards = frappe.get_all(
            "Job Card",
            filters={"work_order": wo.name},
            fields=["name", "operation", "sequence_id", "status", "for_quantity"]
        )
        
        # Get production progress
        total_completed = sum([jc.for_quantity for jc in job_cards if jc.status == "Completed"])
        
        # Get material readiness
        material_readiness = None
        from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
        
        engine = MaterialReadinessEngine(work_order=wo.name)
        material_readiness = engine.evaluate_material_readiness()
        
        return {
            'work_order': wo.as_dict(),
            'job_cards': job_cards,
            'total_completed': total_completed,
            'progress_percent': (total_completed / wo.qty * 100) if wo.qty > 0 else 0,
            'material_readiness': material_readiness
        }
    
    def complete(self, work_order):
        """Complete Work Order"""
        from tekson_manufacturing.execution.execution_engine import ExecutionEngine
        
        engine = ExecutionEngine()
        return engine.complete_work_order(work_order)
    
    def refresh_status(self, work_order):
        """Refresh Work Order status"""
        if isinstance(work_order, str):
            wo = frappe.get_doc("Work Order", work_order)
        else:
            wo = work_order
        
        wo.reload()
        wo.set_status()
        wo.save(ignore_permissions=True)
        frappe.db.commit()


class MaterialService:
    """
    Material Service - Reusable business logic for materials
    """
    
    def __init__(self):
        pass
    
    def get_stock_balance(self, item_code, warehouse=None):
        """Get actual stock balance"""
        from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
        
        engine = MaterialReadinessEngine()
        return engine.get_actual_stock(item_code, warehouse)
    
    def get_cumulative_transfers(self, item_code, work_order, warehouse):
        """Get cumulative material transfers"""
        from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
        
        engine = MaterialReadinessEngine()
        return engine.get_cumulative_transferred_qty(item_code, work_order, warehouse)


@frappe.whitelist()
def get_job_card_service_details(job_card):
    """Whitelisted method to get Job Card details"""
    service = JobCardService()
    return service.get_job_card_details(job_card)


@frappe.whitelist()
def get_work_order_service_details(work_order):
    """Whitelisted method to get Work Order details"""
    service = WorkOrderService()
    return service.get_work_order_details(work_order)
