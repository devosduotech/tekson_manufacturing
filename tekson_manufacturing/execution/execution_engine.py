import frappe
from frappe import _
from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
from tekson_manufacturing.validation.dependency_engine import DependencyEngine
from tekson_manufacturing.diagnostics.messages import DiagnosticMessages


class ExecutionEngine:
    """
    Manufacturing Execution System (MES) Engine
    
    Central orchestrator for:
    - Job Card execution
    - Work Order completion
    - Validation coordination
    - Diagnostic generation
    """
    
    def __init__(self):
        self.material_engine = MaterialReadinessEngine()
        self.dependency_engine = DependencyEngine()
        self.diagnostics = DiagnosticMessages()
    
    def can_job_card_start(self, job_card):
        """
        Check if a Job Card can start production
        
        Args:
            job_card: Job Card name or object
        
        Returns: dict with can_start, reason, diagnostics
        """
        if isinstance(job_card, str):
            jc = frappe.get_doc("Job Card", job_card)
        else:
            jc = job_card
        
        result = {
            'can_start': True,
            'reason': '',
            'diagnostics': []
        }
        
        # Check 1: Previous Operation Validation
        prev_op_result = self.dependency_engine.validate_previous_operation(jc)
        
        if not prev_op_result.get('is_valid'):
            result['can_start'] = False
            result['reason'] = prev_op_result.get('reason')
            result['diagnostics'].append(prev_op_result.get('diagnostic'))
            return result
        
        # Check 2: Material Readiness
        if jc.work_order:
            material_result = self.material_engine.evaluate_material_readiness(jc.work_order)
            
            if not material_result.get('is_ready'):
                result['can_start'] = False
                result['reason'] = "Materials not available"
                
                # Build detailed diagnostics
                for shortage in material_result.get('shortage_details', []):
                    diagnostic = self.diagnostics.build_material_shortage_message(shortage)
                    result['diagnostics'].append(diagnostic)
                
                return result
        
        # All checks passed
        result['reason'] = "All validations passed"
        return result
    
    def can_job_card_complete(self, job_card):
        """
        Check if a Job Card can be completed
        
        Args:
            job_card: Job Card name or object
        
        Returns: dict with can_complete, reason
        """
        if isinstance(job_card, str):
            jc = frappe.get_doc("Job Card", job_card)
        else:
            jc = job_card
        
        result = {
            'can_complete': True,
            'reason': ''
        }
        
        # Basic validation: For Quantity should be <= Completed Qty
        if jc.for_quantity > (jc.total_completed_qty or 0):
            result['can_complete'] = False
            result['reason'] = f"Completed quantity ({jc.total_completed_qty}) is less than required ({jc.for_quantity})"
        
        return result
    
    def complete_work_order(self, work_order):
        """
        Complete a Work Order automatically
        
        Args:
            work_order: Work Order name or object
        
        Returns: dict with success, message, stock_entry (if created)
        """
        if isinstance(work_order, str):
            wo = frappe.get_doc("Work Order", work_order)
        else:
            wo = work_order
        
        result = {
            'success': False,
            'message': '',
            'stock_entry': None
        }
        
        # Check if WO is already completed
        if wo.status == "Completed":
            result['success'] = True
            result['message'] = "Work Order already completed"
            return result
        
        # Check if WO is submitted
        if wo.docstatus != 1:
            result['message'] = "Work Order is not submitted"
            return result
        
        # Check 1: All Job Cards completed
        jc_check = self.check_all_job_cards_completed(wo)
        
        if not jc_check.get('all_completed'):
            result['message'] = jc_check.get('message')
            return result
        
        # Check 2: Production quantity achieved
        qty_check = self.check_production_quantity(wo)
        
        if not qty_check.get('qty_achieved'):
            result['message'] = qty_check.get('message')
            return result
        
        # Check 3: No duplicate stock entry
        existing_se = self.check_existing_stock_entry(wo)
        
        if existing_se:
            result['success'] = True
            result['message'] = f"Stock Entry already exists: {existing_se}"
            result['stock_entry'] = existing_se
            
            # Update WO status
            self.update_work_order_status(wo.name)
            return result
        
        # Create Stock Entry
        try:
            se = self.create_manufacture_stock_entry(wo)
            
            result['success'] = True
            result['message'] = "Work Order completed successfully"
            result['stock_entry'] = se.name
            
            # Update WO status
            self.update_work_order_status(wo.name)
            
            frappe.db.commit()
            
        except Exception as e:
            result['message'] = f"Error creating Stock Entry: {str(e)}"
        
        return result
    
    def check_all_job_cards_completed(self, work_order):
        """Check if all Job Cards for the Work Order are completed"""
        job_cards = frappe.get_all(
            "Job Card",
            filters={"work_order": work_order.name},
            fields=["name", "status", "operation"]
        )
        
        if not job_cards:
            return {
                'all_completed': True,
                'message': "No Job Cards found"
            }
        
        pending = [jc for jc in job_cards if jc.status != "Completed"]
        
        if pending:
            pending_ops = ", ".join([p.operation for p in pending])
            return {
                'all_completed': False,
                'message': f"Pending Job Cards: {pending_ops}"
            }
        
        return {
            'all_completed': True,
            'message': "All Job Cards completed"
        }
    
    def check_production_quantity(self, work_order):
        """Check if required production quantity is achieved"""
        total_completed = frappe.db.sql("""
            SELECT SUM(for_quantity) as qty
            FROM `tabJob Card`
            WHERE work_order = %s
            AND status = "Completed"
        """, (work_order.name), as_dict=True)
        
        completed_qty = total_completed[0].qty if total_completed and total_completed[0].qty else 0
        
        if completed_qty < work_order.qty:
            return {
                'qty_achieved': False,
                'message': f"Completed quantity ({completed_qty}) is less than required ({work_order.qty})"
            }
        
        return {
            'qty_achieved': True,
            'message': f"Production quantity achieved: {completed_qty}"
        }
    
    def check_existing_stock_entry(self, work_order):
        """Check if Manufacture Stock Entry already exists"""
        existing = frappe.db.exists(
            "Stock Entry",
            {
                "work_order": work_order.name,
                "purpose": "Manufacture",
                "docstatus": 1
            }
        )
        
        return existing
    
    def create_manufacture_stock_entry(self, work_order):
        """Create Manufacture Stock Entry"""
        from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry
        
        se_dict = make_stock_entry(
            work_order_id=work_order.name,
            purpose="Manufacture"
        )
        
        stock_entry = frappe.get_doc(se_dict)
        stock_entry.insert(ignore_permissions=True)
        stock_entry.submit()
        
        return stock_entry
    
    def update_work_order_status(self, work_order):
        """Update Work Order status based on completion"""
        wo = frappe.get_doc("Work Order", work_order)
        wo.reload()
        
        # Update produced quantity
        try:
            wo.update_work_order_qty()
        except Exception:
            pass
        
        # Set status
        wo.set_status()
        wo.save(ignore_permissions=True)
        
        frappe.db.commit()


@frappe.whitelist()
def can_start_job_card(job_card):
    """
    Whitelisted method to check if Job Card can start
    
    Args:
        job_card: Job Card name
    
    Returns: dict with validation result
    """
    engine = ExecutionEngine()
    return engine.can_job_card_start(job_card)


@frappe.whitelist()
def complete_work_order_api(work_order):
    """
    Whitelisted method to complete Work Order
    
    Args:
        work_order: Work Order name
    
    Returns: dict with completion result
    """
    engine = ExecutionEngine()
    return engine.complete_work_order(work_order)


# =================================================================
# Event Handlers (called by hooks.py)
# =================================================================

def on_job_card_submit(doc, method=None):
    """
    Event handler for Job Card on_submit
    
    Called when Job Card is submitted
    """
    if not doc.work_order:
        return
    
    # Use Execution Engine to handle completion
    engine = ExecutionEngine()
    
    # Update dependent Job Cards
    if doc.sequence_id:
        from tekson_manufacturing.services.job_card_service import JobCardService
        
        service = JobCardService()
        service.refresh_status(doc.name)
    
    # Try to complete Work Order after commit
    frappe.db.after_commit.add(
        lambda: engine.complete_work_order(doc.work_order)
    )


def on_job_card_cancel(doc, method=None):
    """
    Event handler for Job Card on_cancel
    
    Called when Job Card is cancelled
    """
    if not doc.work_order:
        return
    
    # Refresh Work Order status
    from tekson_manufacturing.services.work_order_service import WorkOrderService
    
    service = WorkOrderService()
    service.refresh_status(doc.work_order)


def on_stock_entry_submit(doc, method=None):
    """
    Event handler for Stock Entry on_submit
    
    Called when Stock Entry is submitted
    """
    if not doc.work_order:
        return
    
    # Refresh Work Order status
    from tekson_manufacturing.services.work_order_service import WorkOrderService
    
    service = WorkOrderService()
    service.refresh_status(doc.work_order)


def on_stock_entry_cancel(doc, method=None):
    """
    Event handler for Stock Entry on_cancel
    
    Called when Stock Entry is cancelled
    """
    if not doc.work_order:
        return
    
    # Refresh Work Order status
    from tekson_manufacturing.services.work_order_service import WorkOrderService
    
    service = WorkOrderService()
    service.refresh_status(doc.work_order)
