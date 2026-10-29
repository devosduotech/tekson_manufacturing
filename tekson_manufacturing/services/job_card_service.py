import frappe
from frappe import _


def compute_status_fields(status, previous_operation, readiness, has_work_order):
    """
    Pure mapping from evaluation inputs to the five Job Card status fields.

    This is the single source of truth used by both the validate hook and any
    caller that needs the status fields, so the rules cannot drift apart.

    Business rules preserved:
    - Completed Job Card   -> start "Completed", cannot start, no material flag
    - Work In Progress     -> start "In Progress", cannot start, no material flag
    - Previous operation incomplete -> "Awaiting Previous Operation" wins over material
    - No Work Order        -> "Awaiting Material", dependency still evaluated
    - Materials missing    -> "Awaiting Material" + missing-item details

    Args:
        status: Job Card status
        previous_operation: previous-operation row (dict) or None
        readiness: MaterialResult or None (None when the JC has no Work Order)
        has_work_order: whether the Job Card is linked to a Work Order

    Returns:
        dict of custom field name -> value (only fields that apply to `status`)
    """
    if status == "Completed":
        return {
            "custom_start_status": "Completed",
            "custom_can_start_operation": 0,
            "custom_material_available_for_operation": 0,
        }

    if status == "Work In Progress":
        return {
            "custom_start_status": "In Progress",
            "custom_can_start_operation": 0,
            "custom_material_available_for_operation": 0,
        }

    # Open Job Card — full evaluation
    dependency_ok = not previous_operation or previous_operation.get("status") == "Completed"
    material_ok = bool(readiness and readiness.is_ready)

    if not dependency_ok:
        start_status = "Awaiting Previous Operation"
    elif not has_work_order:
        start_status = "Awaiting Material"
    elif material_ok:
        start_status = "Ready to Start"
    else:
        start_status = "Awaiting Material"

    if not has_work_order:
        material_details = "Work Order not linked"
    elif material_ok:
        material_details = "Material available in WIP"
    else:
        missing_items = [s.get("item_code", "") for s in (readiness.shortage_details or [])]
        if missing_items:
            material_details = "Missing: " + ", ".join(missing_items[:3])
            if len(missing_items) > 3:
                material_details += f" (+{len(missing_items) - 3} more)"
        else:
            material_details = "Material shortage"

    return {
        "custom_start_status": start_status,
        "custom_dependency_check": 1 if dependency_ok else 0,
        "custom_can_start_operation": 1 if (dependency_ok and (material_ok or not has_work_order)) else 0,
        "custom_material_available_for_operation": 1 if material_ok else 0,
        "custom_material_status_details": material_details,
    }


class JobCardService:
    """
    Job Card Service - Reusable business logic for Job Cards

    All Job Card operations go through this service layer.
    No duplicated logic in controllers, APIs, or UI.
    """
    
    def __init__(self):
        # One shared evaluation per Job Card per service instance, so
        # update_start_status / update_dependency_status / update_material_status
        # never repeat the material readiness evaluation within the same save.
        self._status_evaluations = {}
    
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
            AND docstatus != 2
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
    
    def evaluate_status_fields(self, job_card):
        """
        Evaluate all five Job Card status fields with ONE dependency lookup
        and ONE material readiness evaluation.

        Result is cached per Job Card name for the lifetime of this service
        instance (i.e. for the duration of a single save/refresh), so the three
        update_* methods below all consume the same shared evaluation.

        Args:
            job_card: Job Card document or name

        Returns:
            dict of custom field name -> value
        """
        if isinstance(job_card, str):
            key = job_card
            jc = frappe.get_doc("Job Card", job_card)
        else:
            key = job_card.name
            jc = job_card

        if key in self._status_evaluations:
            return self._status_evaluations[key]

        # Completed / in-progress: only the status-derived fields apply
        # (matches the previous validate-hook behaviour).
        if jc.status in ("Completed", "Work In Progress"):
            fields = compute_status_fields(jc.status, None, None, bool(jc.work_order))
            self._status_evaluations[key] = fields
            return fields

        # One previous-operation lookup (returns None for sequence_id <= 1)
        previous_operation = self.get_previous_operation_status(jc)

        # One material readiness evaluation (None when no Work Order).
        # Pass the Job Card so the engine filters BOM items to this operation
        # and checks its own WIP warehouse — the same evaluation the readiness
        # refresh uses. Without it, saving a Job Card would overwrite the
        # per-operation result with a whole-Work-Order shortage list.
        readiness = None
        if jc.work_order:
            from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine

            engine = MaterialReadinessEngine(work_order=jc.work_order)
            readiness = engine.evaluate_material_readiness(job_card=jc)

        fields = compute_status_fields(jc.status, previous_operation, readiness, bool(jc.work_order))

        frappe.logger("tekson").debug(
            "Job Card %s status evaluation: start=%s dep=%s can_start=%s",
            key,
            fields.get("custom_start_status"),
            fields.get("custom_dependency_check"),
            fields.get("custom_can_start_operation"),
        )

        self._status_evaluations[key] = fields
        return fields

    def update_start_status(self, job_card):
        """
        Update custom_start_status field based on UAT requirements
        
        Status Values:
        - Awaiting Material
        - Awaiting Previous Operation
        - Ready to Start
        - In Progress
        - Completed
        """
        job_card.custom_start_status = self.evaluate_status_fields(job_card)["custom_start_status"]

    def update_dependency_status(self, job_card):
        """
        Update custom_dependency_check and custom_can_start_operation
        
        Business Rules:
        - custom_dependency_check: 1 if all previous operations complete
        - custom_can_start_operation: 1 if ready to start
        """
        fields = self.evaluate_status_fields(job_card)

        # Completed / in-progress Job Cards do not carry dependency fields
        if "custom_dependency_check" not in fields:
            return

        job_card.custom_dependency_check = fields["custom_dependency_check"]
        job_card.custom_can_start_operation = fields["custom_can_start_operation"]

    def update_material_status(self, job_card):
        """
        Update custom_material_available_for_operation and custom_material_status_details
        
        Business Rules:
        - custom_material_available_for_operation: 1 if materials available
        - custom_material_status_details: Detailed status message
        """
        fields = self.evaluate_status_fields(job_card)

        # Completed / in-progress Job Cards do not carry material detail fields
        if "custom_material_status_details" not in fields:
            return

        job_card.custom_material_available_for_operation = fields["custom_material_available_for_operation"]
        job_card.custom_material_status_details = fields["custom_material_status_details"]


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
        """Refresh Work Order status via ERPNext's canonical recompute."""
        if isinstance(work_order, str):
            wo = frappe.get_doc("Work Order", work_order)
        else:
            wo = work_order
        
        wo.reload()
        # Work Order does NOT inherit StatusUpdater (it is plain Document),
        # so the previous wo.set_status() raised AttributeError. update_status()
        # derives the status from actual quantities and db_sets it itself.
        wo.update_status()
        return wo.status




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
