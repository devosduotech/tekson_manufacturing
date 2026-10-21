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
        
        result = {'success': False, 'message': '', 'stock_entry': None}
        
        # Already completed — nothing to do
        if (wo.status == "Completed" or 
            frappe.db.exists("Stock Entry", {"work_order": wo.name, "purpose": "Manufacture", "docstatus": 1})):
            result['success'] = True
            result['message'] = "Work Order already completed"
            self.update_work_order_status(wo.name)
            return result
        
        # Create Stock Entry
        try:
            from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry
            
            se_dict = make_stock_entry(wo.name, "Manufacture", wo.qty)
            se = frappe.get_doc(se_dict)
            
            # Fix s_warehouse for raw materials — only override if material was transferred to WIP
            for item in se.items:
                if not item.is_finished_item:
                    # Only override source warehouse if material was actually transferred to WIP
                    transferred_wh = frappe.db.get_value("Bin",
                        {"item_code": item.item_code, "actual_qty": [">", 0], "warehouse": ["like", "%WIP%"]},
                        "warehouse", order_by="actual_qty desc")
                    if transferred_wh:
                        item.s_warehouse = transferred_wh
                    # Else: keep original s_warehouse from make_stock_entry (e.g., Raw Materials Stores)
                else:
                    item.allow_zero_valuation_rate = 1
            
            # Set FG warehouse to wo.fg_warehouse (from BOM's target_fg_warehouse)
            # If item's BOM has target_fg_warehouse_2, split the FG output
            for item in se.items:
                if item.is_finished_item:
                    item.t_warehouse = wo.fg_warehouse or wo.wip_warehouse
            
            # Split FG output if item's BOM has target_fg_warehouse_2
            if wo.bom_no:
                self._split_fg_output_for_dual_target(se, wo)
            
            # Apply RM Loss % to raw material quantities
            if wo.bom_no:
                apply_rm_loss_to_manufacture_entry(se, wo.bom_no, wo.qty)
            
            se.insert(ignore_permissions=True)
            se.submit()
            
            # Verify stock ledger entries were created
            sle_count = frappe.db.count("Stock Ledger Entry", {"voucher_no": se.name})
            if sle_count == 0:
                frappe.log_error(
                    title=f"WO Complete: No SLE created for {se.name}",
                    message=f"Stock Entry {se.name} submitted but no stock ledger entries created"
                )
            
            result['success'] = True
            result['message'] = "Work Order completed successfully"
            result['stock_entry'] = se.name
            
            self.update_work_order_status(wo.name)
            
        except Exception as e:
            result['message'] = f"Error creating Stock Entry: {str(e)}"
            frappe.log_error(
                title=f"WO Complete Failed: {wo.name}",
                message=str(e)
            )
        
        return result
    
    def _split_fg_output_for_dual_target(self, stock_entry, work_order):
        """
        Split FG output between target_fg_warehouse and target_fg_warehouse_2.
        
        When the item's BOM has target_fg_warehouse_2 set, the produced qty
        is split between the two warehouses based on demand from parent BOMs.
        
        Example:
            Core End Plate BOM: Target1=Ralu In, Target2=RP
            CNC WO qty=2
            Parent BOMs: Core needs 1 from Ralu In, RP needs 1 from RP
            → SE sends 1 to Ralu In, 1 to RP
        
        Args:
            stock_entry: Stock Entry document (Manufacture)
            work_order: Work Order document
        """
        meta = frappe.get_meta("BOM")
        if not meta.has_field("target_fg_warehouse_2"):
            return
        
        fg_item_code = work_order.production_item
        
        # Get the item's own BOM dual targets
        item_bom = frappe.db.get_value("BOM",
            {"item": fg_item_code, "is_active": 1, "docstatus": 1, "is_default": 1},
            ["target_fg_warehouse", "target_fg_warehouse_2"], as_dict=True)
        
        if not item_bom or not item_bom.target_fg_warehouse_2:
            return
        
        target1 = item_bom.target_fg_warehouse
        target2 = item_bom.target_fg_warehouse_2
        
        # Find FG rows in the SE
        fg_rows = [item for item in stock_entry.items if item.is_finished_item and item.item_code == fg_item_code]
        if not fg_rows:
            return
        
        fg_row = fg_rows[0]
        total_qty = fg_row.qty
        
        # Calculate Target2 qty from parent BOM demand
        # Find parent BOMs that use this item with source_warehouse = target2
        parent_demand = frappe.db.sql("""
            SELECT SUM(bi.qty * b.quantity) as total_qty
            FROM `tabBOM Item` bi
            INNER JOIN `tabBOM` b ON bi.parent = b.name
            WHERE bi.item_code = %s
            AND b.is_active = 1 AND b.docstatus = 1
            AND bi.source_warehouse = %s
        """, (fg_item_code, target2), as_dict=True)
        
        target2_demand = parent_demand[0].total_qty if parent_demand and parent_demand[0].total_qty else 0
        
        if target2_demand <= 0 or target2_demand >= total_qty:
            # No split needed — all goes to Target1
            return
        
        target1_qty = total_qty - target2_demand
        target2_qty = target2_demand
        
        # Set Target1 qty on existing row
        fg_row.qty = target1_qty
        fg_row.t_warehouse = target1 or fg_row.t_warehouse
        
        # Add Target2 row
        stock_entry.append("items", {
            "item_code": fg_item_code,
            "qty": target2_qty,
            "s_warehouse": None,
            "t_warehouse": target2,
            "is_finished_item": 1,
            "allow_zero_valuation_rate": 1,
            "basic_rate": fg_row.basic_rate,
            "uom": fg_row.uom,
            "stock_uom": fg_row.stock_uom,
            "conversion_factor": fg_row.conversion_factor,
            "stock_qty": target2_qty * (fg_row.conversion_factor or 1),
        })
        
        frappe.logger("tekson").info(
            "MES Dual-Target FG Split: WO=%s item=%s total=%s | %s(%s)=%s | %s(%s)=%s",
            work_order.name, fg_item_code, total_qty,
            "Target1", target1, target1_qty,
            "Target2", target2, target2_qty
        )
    
    def check_all_job_cards_completed(self, work_order):
        """Check if all Job Cards for the Work Order are completed"""
        job_cards = frappe.get_all(
            "Job Card",
            filters={"work_order": work_order.name, "docstatus": 1},
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
        
        # Single source of truth: delegate to the readiness engine (same path
        # the on_job_card_complete hook uses). The previous inline duplicate
        # also called DependencyResult.get('is_valid') on a dataclass, which
        # raised AttributeError for any next JC that was not Completed.
        from tekson_manufacturing.readiness.job_card_readiness import JobCardReadinessEngine
        JobCardReadinessEngine().refresh_next_job_card(jc)
        
        # Preserve the legacy audit fields without a full save()
        frappe.db.set_value("Job Card", next_jc['name'], {
            "custom_last_refreshed": datetime.now(),
            "custom_refreshed_by": frappe.session.user,
        })
        
        log_mes_event(
            module='EXECUTION',
            level='INFO',
            business_rule='JC-004',
            message=f"Job Card {next_jc['name']} status refreshed",
            context={
                'job_card': next_jc['name'],
                'triggered_by': jc.name,
            }
        )
        
        return {'success': True, 'message': 'Job Cards refreshed', 'refreshed_cards': [next_jc['name']]}
    
    def update_work_order_status(self, work_order):
        """
        Recompute Work Order status from actual production state.

        Delegates to ERPNext's canonical WorkOrder.update_status(), which
        derives the status from docstatus / produced qty / transferred qty.
        This means a cancel path REVERTS the Work Order
        (Completed -> In Process / Not Started) and Completed is only set
        when production is genuinely finished.

        Previously this blind-wrote status = "Completed", so cancelling a
        Job Card or Stock Entry wrongly marked the Work Order as completed
        (ERPNext core had already reverted it a moment earlier).
        """
        if isinstance(work_order, str):
            try:
                wo = frappe.get_doc("Work Order", work_order)
            except frappe.DoesNotExistError:
                return None
        else:
            wo = work_order

        # Never disturb an intentionally Closed/Stopped Work Order:
        # ERPNext's update_status() would overwrite those with a computed one.
        if wo.status in ("Closed", "Stopped"):
            return wo.status

        if hasattr(wo, "update_status"):
            wo.update_status()
        elif hasattr(wo, "get_status"):
            # Fallback for ERPNext builds without update_status()
            wo.db_set("status", wo.get_status())

        return wo.status

    def refresh_work_order_status(self, work_order):
        """
        Recompute Work Order status (canonical recompute, not a force-set).

        Used by the Job Card / Stock Entry cancel handlers and the
        refresh_work_order_status API so a cancelled transaction reverts the
        Work Order instead of leaving it stuck on "Completed".
        """
        return self.update_work_order_status(work_order)


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
    
    # Update dependent Job Cards
    if doc.sequence_id:
        from tekson_manufacturing.services.job_card_service import JobCardService
        
        service = JobCardService()
        service.refresh_status(doc.name)


def on_job_card_cancel(doc, method=None):
    """
    Event handler for Job Card on_cancel

    Called when Job Card is cancelled.

    Recomputes (never force-sets) the Work Order status so cancelling the
    last Job Card reverts the Work Order instead of leaving it "Completed",
    and re-queues readiness so downstream Job Cards' status fields revert
    too (e.g. "Ready to Start" -> "Awaiting Previous Operation").
    """
    if not doc.work_order:
        return

    # Recompute Work Order status (reverts on cancel)
    engine = ExecutionEngine()
    engine.refresh_work_order_status(doc.work_order)

    # Re-evaluate Job Card readiness for this WO (queued, deduplicated)
    try:
        from tekson_manufacturing.readiness.job_card_readiness import (
            enqueue_work_order_refresh,
        )
        enqueue_work_order_refresh(doc.work_order, reason="jc-cancel")
    except Exception:
        frappe.logger("tekson").exception(
            "on_job_card_cancel: failed to queue readiness refresh for WO %s",
            doc.work_order,
        )


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


def apply_rm_loss_to_manufacture_entry(stock_entry, bom_no, wo_qty):
    """
    Apply RM Loss % to raw material quantities in manufacture stock entry.
    
    Raw material qty = BOM qty * WO qty * (1 + RM Loss %)
    This matches what was transferred via Material Request.
    """
    if not bom_no:
        return
    
    # Get BOM Items with RM Loss %
    bom_items = frappe.get_all("BOM Item",
        {"parent": bom_no},
        ["item_code", "qty", "custom_rm_loss_pct", "bom_no", "do_not_explode"])
    
    # Build lookup: item_code -> (qty_per_unit, rm_loss_pct)
    loss_map = {}
    for bi in bom_items:
        if bi.bom_no and not bi.do_not_explode:
            # Sub-assembly - skip (will be exploded separately or has own WO)
            continue
        loss_map[bi.item_code] = {
            "qty_per_unit": bi.qty,
            "rm_loss_pct": bi.custom_rm_loss_pct or 0
        }
    
    # Also check sub-assemblies for raw materials
    for bi in bom_items:
        if bi.bom_no and not bi.do_not_explode:
            sub_bom_items = frappe.get_all("BOM Item",
                {"parent": bi.bom_no},
                ["item_code", "qty", "custom_rm_loss_pct", "do_not_explode"])
            scale = bi.qty / (frappe.db.get_value("BOM", bi.bom_no, "quantity") or 1)
            for sbi in sub_bom_items:
                if sbi.do_not_explode:
                    continue
                if sbi.item_code not in loss_map:
                    loss_map[sbi.item_code] = {
                        "qty_per_unit": sbi.qty * scale,
                        "rm_loss_pct": sbi.custom_rm_loss_pct or 0
                    }
    
    # Apply loss to stock entry raw material items
    for item in stock_entry.items:
        if not item.is_finished_item and item.item_code in loss_map:
            loss_info = loss_map[item.item_code]
            loss_pct = loss_info["rm_loss_pct"] / 100.0
            if loss_pct > 0:
                # qty from make_stock_entry is already BOM qty * wo_qty
                # Apply RM loss: qty = qty * (1 + loss_pct)
                item.qty = item.qty * (1 + loss_pct)


def on_stock_entry_cancel(doc, method=None):
    """
    Event handler for Stock Entry on_cancel

    Called when Stock Entry is cancelled.

    Recomputes (never force-sets) the Work Order status so cancelling a
    Manufacture / material Stock Entry reverts the Work Order instead of
    leaving it "Completed", and re-queues readiness so Job Cards re-evaluate
    against the stock that is no longer there.
    """
    if not doc.work_order:
        return

    # Recompute Work Order status (reverts on cancel)
    engine = ExecutionEngine()
    engine.refresh_work_order_status(doc.work_order)

    # Re-evaluate Job Card readiness for this WO (queued, deduplicated)
    try:
        from tekson_manufacturing.readiness.job_card_readiness import (
            enqueue_work_order_refresh,
        )
        enqueue_work_order_refresh(doc.work_order, reason="se-cancel")
    except Exception:
        frappe.logger("tekson").exception(
            "on_stock_entry_cancel: failed to queue readiness refresh for WO %s",
            doc.work_order,
        )
