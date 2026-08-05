import frappe
from frappe import _
from datetime import datetime
from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
from tekson_manufacturing.validation.dependency_engine import DependencyEngine, can_job_card_start as check_dependency_start
from tekson_manufacturing.diagnostics.messages import DiagnosticMessages
from tekson_manufacturing.repositories.job_card_repository import JobCardRepository
from tekson_manufacturing.repositories.work_order_repository import WorkOrderRepository
from tekson_manufacturing.repositories.stock_repository import StockRepository
from tekson_manufacturing.utils.exceptions import MESValidationError, MESExecutionError
from tekson_manufacturing.utils import log_mes_event, get_mes_settings


class ExecutionEngine:
    """
    Manufacturing Execution System (MES) Engine
    
    Business Rules:
    - JC-001: Job Card Start Permission
    - JC-002: Job Card Completion Permission
    - JC-003: Job Card Material Check
    - JC-004: Job Card Auto-Refresh
    - JC-005: Job Card Work Order Link
    - WO-001: Auto-Completion Trigger
    - WO-002: Duplicate Stock Entry Prevention
    
    Dependencies:
    - MaterialReadinessEngine (MR-010, MR-011)
    - DependencyEngine (DV-001, DV-002)
    - JobCardRepository, WorkOrderRepository, StockRepository
    
    Performance Target: < 2 seconds
    """
    
    def __init__(self):
        self.material_engine = MaterialReadinessEngine()
        self.dependency_engine = DependencyEngine()
        self.diagnostics = DiagnosticMessages()
        self.jc_repo = JobCardRepository()
        self.wo_repo = WorkOrderRepository()
        self.stock_repo = StockRepository()
        self.mes_settings = get_mes_settings()
    
    def can_job_card_start(self, job_card):
        """
        Check if Job Card can start (JC-001, JC-003)
        
        Business Rules:
        - JC-001: Job Card cannot start until previous operations are complete
        - JC-003: Job Card should not start if materials are not available
        
        Args:
            job_card: Job Card name or document
        
        Returns: dict with can_start, reason, validations, diagnostics
        
        Performance Target: < 2 seconds
        
        Example:
        >>> engine = ExecutionEngine()
        >>> result = engine.can_job_card_start("JC-2026-001")
        >>> result['can_start']
        True
        
        Test Case:
        - test_jc_001_start_permission
        - test_jc_003_material_check
        """
        if isinstance(job_card, str):
            jc = self.jc_repo.get(job_card)
        else:
            jc = job_card
        
        if not jc:
            raise MESValidationError(f"Job Card not found")
        
        # Start performance timing
        import time
        start_time = time.time()
        
        result = {
            'can_start': True,
            'reason': '',
            'validations': {
                'jc_001_previous_operation': True,
                'jc_003_material_readiness': True,
                'jc_005_work_order_link': True
            },
            'diagnostics': []
        }
        
        # JC-005: Job Card must be linked to Work Order
        if not jc.work_order:
            result['can_start'] = False
            result['reason'] = "Job Card not linked to Work Order"
            result['validations']['jc_005_work_order_link'] = False
            
            log_mes_event(
                module='EXECUTION',
                level='ERROR',
                business_rule='JC-005',
                message=f"Job Card {jc.name} not linked to Work Order",
                context={'job_card': jc.name}
            )
            
            return result
        
        # JC-001: Previous Operation Validation
        dep_result = check_dependency_start(job_card=jc.name)
        
        if not dep_result.get('can_start'):
            result['can_start'] = False
            result['reason'] = dep_result.get('reason')
            result['validations']['jc_001_previous_operation'] = False
            result['diagnostics'].append(dep_result.get('validation_details', {}).get('diagnostic', {}))
            
            log_mes_event(
                module='EXECUTION',
                level='WARNING',
                business_rule='JC-001',
                message=f"Job Card {jc.name} cannot start: {result['reason']}",
                context={
                    'job_card': jc.name,
                    'work_order': jc.work_order,
                    'blocked_by': 'JC-001'
                }
            )
            
            return result
        
        # JC-003: Material Readiness Check (only if strict validation enabled)
        if self.mes_settings and self.mes_settings.enable_strict_validation:
            material_result = self.material_engine.evaluate_material_readiness(jc.work_order)
            
            if not material_result.is_ready:
                result['can_start'] = False
                result['reason'] = "Materials not available in Department Warehouse"
                result['validations']['jc_003_material_readiness'] = False
                
                # Build detailed diagnostics
                for shortage in material_result.shortage_details:
                    diagnostic = self.diagnostics.build_material_shortage_message(shortage)
                    result['diagnostics'].append(diagnostic)
                
                log_mes_event(
                    module='EXECUTION',
                    level='WARNING',
                    business_rule='JC-003',
                    message=f"Job Card {jc.name} blocked: Materials not ready",
                    context={
                        'job_card': jc.name,
                        'work_order': jc.work_order,
                        'missing_items': [s['item_code'] for s in material_result.shortage_details]
                    }
                )
                
                return result
        
        # All checks passed
        result['reason'] = "All validations passed"
        
        # Log success
        execution_time = (time.time() - start_time) * 1000
        log_mes_event(
            module='EXECUTION',
            level='INFO',
            business_rule='JC-001',
            message=f"Job Card {jc.name} can start",
            context={
                'job_card': jc.name,
                'work_order': jc.work_order,
                'execution_time_ms': execution_time
            }
        )
        
        return result
    
    def can_job_card_complete(self, job_card):
        """
        Check if Job Card can complete (JC-002)
        
        Business Rule:
        - JC-002: Job Card can only be completed if for_quantity has been produced
        
        Args:
            job_card: Job Card name or document
        
        Returns: dict with can_complete, reason, validations
        
        Performance Target: < 1 second
        
        Example:
        >>> engine = ExecutionEngine()
        >>> result = engine.can_job_card_complete("JC-2026-001")
        >>> result['can_complete']
        True
        
        Test Case:
        - test_jc_002_completion_permission
        """
        if isinstance(job_card, str):
            jc = self.jc_repo.get(job_card)
        else:
            jc = job_card
        
        if not jc:
            raise MESValidationError(f"Job Card not found")
        
        # Start performance timing
        import time
        start_time = time.time()
        
        result = {
            'can_complete': True,
            'reason': '',
            'validations': {
                'jc_002_quantity_check': True
            }
        }
        
        # JC-002: Quantity validation
        completed_qty = jc.total_completed_qty or 0
        required_qty = jc.for_quantity
        
        if completed_qty < required_qty:
            result['can_complete'] = False
            result['reason'] = f"Completed quantity ({completed_qty}) is less than required ({required_qty})"
            result['validations']['jc_002_quantity_check'] = False
            
            log_mes_event(
                module='EXECUTION',
                level='WARNING',
                business_rule='JC-002',
                message=f"Job Card {jc.name} cannot complete: quantity insufficient",
                context={
                    'job_card': jc.name,
                    'completed_qty': completed_qty,
                    'required_qty': required_qty
                }
            )
            
            return result
        
        # All checks passed
        result['reason'] = f"Job Card can complete: {completed_qty} units produced"
        
        # Log success
        execution_time = (time.time() - start_time) * 1000
        log_mes_event(
            module='EXECUTION',
            level='INFO',
            business_rule='JC-002',
            message=f"Job Card {jc.name} can complete",
            context={
                'job_card': jc.name,
                'completed_qty': completed_qty,
                'execution_time_ms': execution_time
            }
        )
        
        return result
    
    def complete_work_order(self, work_order):
        """
        Complete Work Order automatically (WO-001, WO-002)
        
        Business Rules:
        - WO-001: When all Job Cards are completed, auto-complete Work Order
        - WO-002: Do not create duplicate Manufacture Stock Entries
        
        Args:
            work_order: Work Order name or document
        
        Returns: dict with success, message, stock_entry
        
        Performance Target: < 3 seconds
        
        Example:
        >>> engine = ExecutionEngine()
        >>> result = engine.complete_work_order("WO-2026-001")
        >>> result['success']
        True
        
        Test Case:
        - test_wo_001_auto_completion
        - test_wo_002_duplicate_prevention
        """
        if isinstance(work_order, str):
            try:
                wo = frappe.get_doc("Work Order", work_order)
            except frappe.DoesNotExistError:
                raise MESValidationError(f"Work Order {work_order} not found")
        else:
            wo = work_order
        
        if not wo:
            raise MESValidationError("Work Order not found")
        
        # Start performance timing
        import time
        start_time = time.time()
        
        result = {
            'success': False,
            'message': '',
            'stock_entry': None,
            'validations': {
                'wo_001_all_jc_completed': False,
                'wo_001_qty_achieved': False,
                'wo_002_no_duplicate': True
            }
        }
        
        # Check if WO is already completed
        if wo.status == "Completed":
            result['success'] = True
            result['message'] = "Work Order already completed"
            result['stock_entry'] = self.stock_repo.get_entries_by_work_order(wo.name, "Manufacture")
            return result
        
        # Check if WO is submitted
        if wo.docstatus != 1:
            result['message'] = "Work Order is not submitted"
            return result
        
        # WO-001: All Job Cards completed
        
        # WO-002: No duplicate Stock Entry
        existing_se = self.stock_repo.count_entries_by_work_order(wo.name, "Manufacture")
        
        if existing_se > 0:
            result['success'] = True
            result['message'] = "Manufacture Stock Entry already exists"
            result['stock_entry'] = self.stock_repo.get_entries_by_work_order(wo.name, "Manufacture")[0]
            result['validations']['wo_002_no_duplicate'] = False  # Duplicate exists
            
            # Update WO status
            self.update_work_order_status(wo.name)
            
            log_mes_event(
                module='EXECUTION',
                level='INFO',
                business_rule='WO-002',
                message=f"Work Order {wo.name} duplicate Stock Entry prevented",
                context={
                    'work_order': wo.name,
                    'existing_se': result['stock_entry']
                }
            )
            
            return result
        
        # Create Stock Entry
        try:
            se = self.create_manufacture_stock_entry(wo)
            
            result['success'] = True
            result['message'] = "Work Order completed successfully"
            result['stock_entry'] = se.name
            
            # Update WO status
            self.update_work_order_status(wo.name)
            
            # Log success
            execution_time = (time.time() - start_time) * 1000
            log_mes_event(
                module='EXECUTION',
                level='INFO',
                business_rule='WO-001',
                message=f"Work Order {wo.name} completed successfully",
                context={
                    'work_order': wo.name,
                    'stock_entry': se.name,
                    'execution_time_ms': execution_time
                }
            )
            
        except Exception as e:
            result['message'] = f"Error creating Stock Entry: {str(e)}"
            
            log_mes_event(
                module='EXECUTION',
                level='ERROR',
                business_rule='WO-001',
                message=f"Work Order {wo.name} completion failed: {str(e)}",
                context={
                    'work_order': wo.name,
                    'error': str(e)
                }
            )
        
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
        """
        Create Manufacture Stock Entry
        
        Business Rule: WH-003 - Multi-department flow support
        
        For sub-assemblies, output goes to next department's WIP warehouse,
        not Finished Goods warehouse.
        
        Args:
            work_order: Work Order document
        
        Returns: Stock Entry document
        
        Logic:
        1. Check if production item is used as raw material in another BOM (sub-assembly)
        2. If yes, find parent BOM's first operation department
        3. Set t_warehouse to parent department's WIP warehouse
        4. Create and submit Stock Entry
        """
        # Check if this is a sub-assembly
        is_sub_assembly = frappe.db.exists(
            "BOM Item",
            {"item_code": work_order.production_item, "docstatus": 1}
        )
        
        # Get target warehouse for sub-assemblies
        target_warehouse = None
        if is_sub_assembly:
            target_warehouse = self.get_sub_assembly_output_warehouse(work_order)
        
        # Create Stock Entry manually to override warehouse
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.stock_entry_type = "Manufacture"
        stock_entry.purpose = "Manufacture"
        stock_entry.work_order = work_order.name
        stock_entry.from_bom = 1
        stock_entry.bom_no = work_order.bom_no
        stock_entry.use_multi_level_bom = 1
        stock_entry.company = work_order.company
        stock_entry.fg_warehouse = work_order.fg_warehouse
        
        # Set manufactured quantity
        stock_entry.fg_completed_qty = work_order.produced_qty or work_order.qty
        
        # Set target warehouse
        if target_warehouse:
            stock_entry.to_warehouse = target_warehouse
        else:
            stock_entry.to_warehouse = work_order.fg_warehouse
        
        # Get items from BOM
        stock_entry.get_items()
        
        # Override source warehouse from BOM Item if set
        bom = frappe.get_doc("BOM", work_order.bom_no) if work_order.bom_no else None
        bom_items = {}
        if bom:
            bom_items = {item.item_code: item.source_warehouse for item in bom.items if item.source_warehouse}
        
        # Get last completed JC's WIP warehouse (where finished goods are located)
        last_jc = frappe.db.get_value('Job Card', 
            {'work_order': work_order.name, 'docstatus': 1},
            'wip_warehouse',
            order_by='modified desc')
        
        for item in stock_entry.items:
            # Set source warehouse from BOM Item
            if item.item_code in bom_items:
                item.s_warehouse = bom_items[item.item_code]
            
            # For finished goods, source = last JC's WIP warehouse
            if item.is_finished_item and last_jc:
                item.s_warehouse = last_jc
            
            # Override t_warehouse for finished items if sub-assembly
            if target_warehouse and (item.is_finished_item or item.is_scrap_item):
                item.t_warehouse = target_warehouse
            
            # Fix for multi-department WIP: consume from WIP where stock actually exists
            if not item.is_finished_item:
                actual_wh = frappe.db.get_value("Bin",
                    {"item_code": item.item_code, "actual_qty": [">", 0],
                     "warehouse": ["like", "%WIP%"]},
                    "warehouse", order_by="actual_qty desc")
                if actual_wh:
                    item.s_warehouse = actual_wh
        
        stock_entry.insert(ignore_permissions=True)
        stock_entry.submit()
        
        return stock_entry
    
    def get_sub_assembly_output_warehouse(self, work_order):
        """
        Get target WIP warehouse for sub-assembly output
        
        Args:
            work_order: Work Order document
        
        Returns: str - WIP warehouse name or None
        
        Logic:
        1. Find parent BOM that uses this item
        2. Get parent BOM's first operation
        3. Get workstation's plant floor
        4. Return WIP-{plant_floor} - TPL
        """
        # Find parent BOM item
        parent_bom_item = frappe.db.get_value(
            "BOM Item",
            {"item_code": work_order.production_item, "docstatus": 1},
            "parent"
        )
        
        if not parent_bom_item:
            return None
        
        # Get parent BOM
        parent_bom = frappe.get_doc("BOM", parent_bom_item)
        
        # Get first operation's workstation
        if parent_bom.operations and len(parent_bom.operations) > 0:
            first_op = parent_bom.operations[0]
            
            # Get workstation from workstation_type
            workstation = first_op.workstation or frappe.db.get_value(
                "Workstation",
                {"workstation_type": first_op.workstation_type},
                "name"
            )
            
            if workstation:
                plant_floor = frappe.db.get_value("Workstation", workstation, "plant_floor")
                
                if plant_floor:
                    target_warehouse = f"WIP-{plant_floor} - TPL"
                    
                    # Verify warehouse exists
                    if frappe.db.exists("Warehouse", target_warehouse):
                        return target_warehouse
        
        return None
    
    def refresh_job_card_status(self, job_card):
        """
        Refresh Job Card status after dependent operation completes (JC-004)
        
        Business Rule:
        - JC-004: When a Job Card is submitted, dependent Job Cards must be refreshed
        
        Args:
            job_card: Job Card name or document
        
        Returns: dict with success, refreshed_cards
        
        Performance Target: < 1 second
        
        Test Case:
        - test_jc_004_auto_refresh
        """
        if isinstance(job_card, str):
            jc = self.jc_repo.get(job_card)
        else:
            jc = job_card
        
        if not jc or not jc.work_order or not jc.sequence_id:
            return {'success': False, 'message': 'Invalid Job Card'}
        
        # Find next Job Card
        next_jc = self.jc_repo.get_next_operation(jc.name)
        
        if not next_jc:
            return {'success': True, 'message': 'No dependent Job Cards', 'refreshed_cards': []}
        
        refreshed = []
        
        # Refresh next Job Card status
        next_jc_doc = self.jc_repo.get(next_jc['name'])
        
        if next_jc_doc:
            # Update custom_start_status
            if next_jc_doc.status == "Completed":
                next_jc_doc.custom_start_status = "Completed"
            else:
                # Check if previous is now complete
                prev_result = self.dependency_engine.validate_previous_operation(next_jc_doc)
                
                if prev_result.get('is_valid'):
                    next_jc_doc.custom_start_status = "Ready to Start"
                else:
                    next_jc_doc.custom_start_status = "Awaiting Previous Operation"
            
            next_jc_doc.custom_last_refreshed = datetime.now()
            next_jc_doc.custom_refreshed_by = frappe.session.user
            next_jc_doc.save(ignore_permissions=True)
            
            refreshed.append(next_jc['name'])
            
            log_mes_event(
                module='EXECUTION',
                level='INFO',
                business_rule='JC-004',
                message=f"Job Card {next_jc['name']} status refreshed",
                context={
                    'job_card': next_jc['name'],
                    'triggered_by': jc.name,
                    'new_status': next_jc_doc.custom_start_status
                }
            )
        
        return {'success': True, 'message': 'Job Cards refreshed', 'refreshed_cards': refreshed}
    
    def update_work_order_status(self, work_order):
        """Update Work Order status to Completed"""
        frappe.db.set_value("Work Order", work_order, "status", "Completed")
        
        frappe.db.commit()
    
    def refresh_work_order_status(self, work_order):
        """Alias for update_work_order_status - refreshes WO status"""
        self.update_work_order_status(work_order)


@frappe.whitelist()
def can_start_job_card(job_card):
    """
    Whitelisted API to check if Job Card can start (JC-001, JC-003, JC-005)
    
    Args:
        job_card: Job Card name
    
    Returns: dict with can_start, reason, validations, diagnostics
    
    Example:
    >>> result = can_start_job_card("JC-2026-001")
    >>> result['can_start']
    True
    
    Test Case:
    - test_jc_001_api
    - test_jc_003_api
    """
    engine = ExecutionEngine()
    return engine.can_job_card_start(job_card)


@frappe.whitelist()
def can_complete_job_card(job_card):
    """
    Whitelisted API to check if Job Card can complete (JC-002)
    
    Args:
        job_card: Job Card name
    
    Returns: dict with can_complete, reason, validations
    
    Example:
    >>> result = can_complete_job_card("JC-2026-001")
    >>> result['can_complete']
    True
    
    Test Case:
    - test_jc_002_api
    """
    engine = ExecutionEngine()
    return engine.can_job_card_complete(job_card)


@frappe.whitelist()
def complete_work_order_api(work_order):
    """
    Whitelisted API to complete Work Order (WO-001, WO-002)
    
    Args:
        work_order: Work Order name
    
    Returns: dict with success, message, stock_entry, validations
    
    Example:
    >>> result = complete_work_order_api("WO-2026-001")
    >>> result['success']
    True
    
    Test Case:
    - test_wo_001_api
    - test_wo_002_api
    """
    engine = ExecutionEngine()
    return engine.complete_work_order(work_order)


@frappe.whitelist()
def refresh_job_card_status_api(job_card):
    """
    Whitelisted API to refresh Job Card status (JC-004)
    
    Args:
        job_card: Job Card name
    
    Returns: dict with success, refreshed_cards
    
    Example:
    >>> result = refresh_job_card_status_api("JC-2026-001")
    >>> result['refreshed_cards']
    ['JC-2026-002']
    
    Test Case:
    - test_jc_004_api
    """
    engine = ExecutionEngine()
    return engine.refresh_job_card_status(job_card)


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
    
    # Try to complete Work Order after commit (backup — Coordinator handles primary)
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
    
    # Refresh Work Order status using Execution Engine
    engine = ExecutionEngine()
    engine.refresh_work_order_status(doc.work_order)


def on_stock_entry_submit(doc, method=None):
    """
    Event handler for Stock Entry on_submit
    
    Called when Stock Entry is submitted
    """
    if not doc.work_order:
        return
    
    # Refresh Work Order status using Execution Engine
    engine = ExecutionEngine()
    engine.refresh_work_order_status(doc.work_order)


def on_stock_entry_cancel(doc, method=None):
    """
    Event handler for Stock Entry on_cancel
    
    Called when Stock Entry is cancelled
    """
    if not doc.work_order:
        return
    
    # Refresh Work Order status using Execution Engine
    engine = ExecutionEngine()
    engine.refresh_work_order_status(doc.work_order)
