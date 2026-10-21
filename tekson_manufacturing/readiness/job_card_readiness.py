"""
Job Card Readiness Engine

Orchestrates Material and Dependency engines to evaluate Job Card readiness.
Separates evaluation from persistence for testability and performance.

Persistence rules (important):
    apply_result_to_job_card() writes ONLY the five readiness indicator fields,
    and ONLY when a value actually changed. It never calls jc.save(), so a
    refresh can never re-trigger the validate hook / readiness cascade.
    Real Job Card state transitions (Open -> Work In Progress -> Completed)
    keep going through the normal save path and its validations.
"""

import frappe
from frappe import _
from types import SimpleNamespace
from typing import Any

from tekson_manufacturing.mes.dataclasses import (
    MaterialResult,
    DependencyResult,
    ReadinessResult,
    MaterialStatus,
    ReadinessStatus
)
from tekson_manufacturing.readiness.material_readiness import (
    MaterialReadinessEngine,
    enqueue_inter_department_transfers,
)
from tekson_manufacturing.services.job_card_service import JobCardService, compute_status_fields
from tekson_manufacturing.validation.dependency_engine import DependencyEngine

# Fields owned by the readiness refresh — never written outside these.
READINESS_FIELDS = [
    "custom_start_status",
    "custom_dependency_check",
    "custom_can_start_operation",
    "custom_material_available_for_operation",
    "custom_material_status_details",
]


def map_readiness_result_to_fields(status, previous_operation, has_work_order, result):
    """
    Map a ReadinessResult onto the five custom status fields.

    Delegates to JobCardService.compute_status_fields() so a refresh always
    writes exactly what the validate hook would have written. The previous-
    operation ROW is passed in (row semantics — None == no previous operation)
    rather than ReadinessResult flags, so refresh and save can never disagree.

    Args:
        status: current Job Card status
        previous_operation: previous-operation row (dict) or None
        has_work_order: whether the Job Card is linked to a Work Order
        result: ReadinessResult from evaluate_job_card()

    Returns:
        dict of custom field name -> value
    """
    readiness_view = SimpleNamespace(
        is_ready=result.material_available,
        shortage_details=result.shortage_details,
    )

    return compute_status_fields(status, previous_operation, readiness_view, has_work_order)


class JobCardReadinessEngine:
    """
    Job Card Readiness Engine
    
    Orchestrates Material and Dependency engines to evaluate
    Job Card readiness without setting fields directly.
    
    Separates evaluation from persistence.
    
    Usage:
        engine = JobCardReadinessEngine()
        
        # Evaluate (pure function, no DB writes)
        result = engine.evaluate_job_card(jc)
        
        # Apply (writes only changed readiness fields)
        engine.apply_result_to_job_card(jc.name, result)
    """
    
    def __init__(self):
        """Initialize Readiness Engine with Material and Dependency engines"""
        self.material_engine = MaterialReadinessEngine()
        self.dependency_engine = DependencyEngine()
    
    def refresh_work_order(self, work_order: Any) -> None:
        """
        Evaluate all Job Cards in Work Order
        
        Only changed readiness fields are written — an unchanged Job Card
        produces zero DB writes.
        
        Args:
            work_order: Work Order name or document
        """
        wo_name = work_order if isinstance(work_order, str) else work_order.name

        # Re-entrancy guard: a queued refresh may already be running for this
        # WO in the same process (e.g. nested WO/SE events).
        refreshing = getattr(frappe.local, 'mes_refreshing_wos', None)
        if refreshing is None:
            refreshing = frappe.local.mes_refreshing_wos = set()
        if wo_name in refreshing:
            frappe.logger("tekson").info(
                "refresh_work_order: skipped re-entrant call for %s", wo_name
            )
            return
        refreshing.add(wo_name)
        try:
            # Get all Job Cards for this WO (lightweight — no get_doc per JC)
            job_cards = frappe.get_all('Job Card',
                filters={'work_order': wo_name, 'docstatus': ['!=', 2]},
                fields=['name', 'status', 'work_order', 'operation', 'sequence_id', 'wip_warehouse'],
                order_by='sequence_id')

            frappe.logger("tekson").debug(
                "refresh_work_order: WO %s | JC count %s", wo_name, len(job_cards)
            )

            pending_transfers = []
            for jc_data in job_cards:
                result = self.evaluate_job_card(jc_data)
                self.apply_result_to_job_card(jc_data.get('name'), result)
                pending_transfers.extend(result.pending_transfers)

            # Readiness evaluation is read-only; requested transfers are
            # executed by deduplicated background jobs after this transaction
            # commits (readiness stays blocked until stock actually lands).
            enqueue_inter_department_transfers(pending_transfers)
        finally:
            refreshing.discard(wo_name)
    
    def refresh_job_card(self, job_card: Any) -> ReadinessResult:
        """
        Evaluate single Job Card
        
        Args:
            job_card: Job Card name or document
        
        Returns:
            ReadinessResult from evaluation
        """
        if isinstance(job_card, str):
            jc = frappe.get_doc('Job Card', job_card)
        else:
            jc = job_card
        
        result = self.evaluate_job_card(jc)
        self.apply_result_to_job_card(jc.get('name') if hasattr(jc, 'get') else jc.name, result)
        enqueue_inter_department_transfers(result.pending_transfers)
        return result
    
    def refresh_next_job_card(self, job_card: Any) -> None:
        """
        Refresh all JCs at the next sequence (supports parallel operations)
        
        Rationale:
        - JC-001 complete → refresh ALL JCs with sequence_id = 2
        - Each downstream JC will refresh its own next when it completes
        - Supports parallel operations (multiple JCs at same sequence)
        
        Args:
            job_card: Job Card that was completed
        """
        work_order = job_card.get('work_order') if hasattr(job_card, 'get') else job_card.work_order
        sequence_id = job_card.get('sequence_id') if hasattr(job_card, 'get') else job_card.sequence_id

        # Find ALL JCs at the next sequence (supports parallel operations)
        next_jcs = frappe.get_all('Job Card',
            filters={
                'work_order': work_order,
                'sequence_id': (sequence_id or 0) + 1,
                'docstatus': ['!=', 2]
            },
            fields=['name', 'status', 'work_order', 'operation', 'sequence_id', 'wip_warehouse'])

        pending_transfers = []
        for jc_data in next_jcs:
            result = self.evaluate_job_card(jc_data)
            self.apply_result_to_job_card(jc_data.get('name'), result)
            pending_transfers.extend(result.pending_transfers)

        enqueue_inter_department_transfers(pending_transfers)
    
    def evaluate_job_card(self, job_card) -> ReadinessResult:
        """
        Evaluate readiness — database reads only, no writes.
        
        Args:
            job_card: Job Card document or dict (name/status/work_order/operation/sequence_id)
        
        Returns:
            ReadinessResult with all evaluation data
        """
        if isinstance(job_card, str):
            job_card = frappe.get_doc('Job Card', job_card)

        get = job_card.get
        status = get('status')
        work_order = get('work_order')

        # Completed / in-progress states need no material evaluation:
        # their readiness fields are derived from the status alone.
        if status == "Completed":
            return ReadinessResult.create_completed(MaterialStatus.AVAILABLE)

        if status == "Work In Progress":
            return ReadinessResult.create_in_progress(MaterialStatus.AVAILABLE)

        # JC-005: no Work Order — nothing can be evaluated
        if not work_order:
            return ReadinessResult.create_blocked(
                MaterialStatus.WAITING,
                "Job Card not linked to Work Order"
            )

        # Get material status (job_card may be a name, dict or document —
        # the engine resolves it and applies per-operation filtering)
        material_result = self.material_engine.evaluate_material_readiness(
            work_order=work_order,
            job_card=job_card
        )
        
        # Get dependency status
        dependency_result = self.dependency_engine.validate_previous_operation(job_card)
        
        # Combine results
        return self._combine_results(material_result, dependency_result)
    
    def _combine_results(
        self,
        material_result: MaterialResult,
        dependency_result: DependencyResult
    ) -> ReadinessResult:
        """Combine engine results into ReadinessResult"""
        
        # Determine readiness based on material and dependencies
        if material_result.is_ready and dependency_result.can_start:
            combined = ReadinessResult.create_ready(material_result.status)
        elif not material_result.is_ready:
            combined = ReadinessResult.create_waiting_material(material_result.message)
        elif not dependency_result.can_start:
            combined = ReadinessResult.create_waiting_previous_op(
                dependency_result.previous_jc_name or "Unknown"
            )
        else:
            combined = ReadinessResult.create_blocked(
                material_result.status,
                "Unknown reason"
            )

        combined.shortage_details = material_result.shortage_details
        combined.pending_transfers = material_result.pending_transfers
        return combined
    
    def apply_result_to_job_card(self, job_card_name: str, result: ReadinessResult):
        """
        Write the readiness indicators for a Job Card — changed fields only.
        
        Deliberately does NOT call jc.save(): a readiness refresh must never
        re-run document validation, status normalisation or the validate-hook
        readiness cascade. Job Card state transitions keep using save().
        
        Args:
            job_card_name: Job Card name
            result: ReadinessResult from evaluation
        
        Returns:
            dict of fields that were actually written (empty when unchanged)
        """
        if not job_card_name:
            frappe.throw(_("Job Card not found"))

        current = frappe.db.get_value(
            "Job Card",
            job_card_name,
            ["status", "work_order", "sequence_id", *READINESS_FIELDS],
            as_dict=True
        )

        if not current:
            frappe.throw(_("Job Card {0} not found").format(job_card_name))

        # Same previous-operation row semantics as the validate hook
        # (JobCardService.get_previous_operation_status) — None for seq <= 1.
        previous_operation = None
        if current.status not in ("Completed", "Work In Progress"):
            previous_operation = JobCardService().get_previous_operation_status(current)

        target = map_readiness_result_to_fields(
            current.status, previous_operation, bool(current.work_order), result
        )

        changed = {
            fieldname: value
            for fieldname, value in target.items()
            if current.get(fieldname) != value
        }

        if changed:
            frappe.db.set_value("Job Card", job_card_name, changed)
            frappe.logger("tekson").info(
                "Job Card %s readiness updated: %s",
                job_card_name,
                ", ".join(f"{k}={v}" for k, v in changed.items()),
            )
        else:
            frappe.logger("tekson").debug(
                "Job Card %s readiness unchanged — no write", job_card_name
            )

        return changed


# =============================================================================
# Background refresh jobs (Phase 6 — queue expensive refreshes)
# =============================================================================

def refresh_work_order_job(work_order: str):
    """
    Background job: refresh readiness for every Job Card of a Work Order.
    
    Re-reads current database state when the job runs, so it never acts on
    stale data from the request that queued it.
    """
    frappe.logger("tekson").info("Background readiness refresh started: WO %s", work_order)
    JobCardReadinessEngine().refresh_work_order(work_order)


def enqueue_work_order_refresh(work_order: str, reason: str = ""):
    """
    Queue a deduplicated readiness refresh for a Work Order on the short queue.
    
    Safeguards:
    - deduplicated by job_id: repeated triggers (multiple Stock Entries /
      Job Cards) coalesce into a single queued refresh
    - enqueue_after_commit: the job only enters the queue if the triggering
      transaction actually commits
    - now=True under `bench run-tests` keeps test flows synchronous
    - the job re-reads state and rq retains failures for retry/inspection
    """
    if not work_order:
        return

    try:
        frappe.enqueue(
            "tekson_manufacturing.readiness.job_card_readiness.refresh_work_order_job",
            queue="short",
            timeout=120,
            job_id=f"mes-wo-refresh::{work_order}",
            deduplicate=True,
            enqueue_after_commit=True,
            now=frappe.flags.in_test,
            work_order=work_order,
        )
        frappe.logger("tekson").debug(
            "Queued readiness refresh for WO %s (%s)", work_order, reason or "trigger"
        )
    except Exception:
        # Never fail the caller's business action because queueing failed —
        # log loudly so the miss can be investigated and retried.
        frappe.logger("tekson").exception(
            "Failed to queue readiness refresh for WO %s", work_order
        )
