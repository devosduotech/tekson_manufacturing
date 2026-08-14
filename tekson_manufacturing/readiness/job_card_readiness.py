"""
Job Card Readiness Engine

Orchestrates Material and Dependency engines to evaluate Job Card readiness.
Separates evaluation from persistence for testability and performance.
"""

import frappe
from frappe import _
from typing import Any

from tekson_manufacturing.mes.dataclasses import (
    MaterialResult,
    DependencyResult,
    ReadinessResult,
    MaterialStatus,
    ReadinessStatus
)
from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine
from tekson_manufacturing.validation.dependency_engine import DependencyEngine


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
        
        # Apply (optimized persistence)
        engine.apply_result_to_job_card(jc.name, result)
    """
    
    def __init__(self):
        """Initialize Readiness Engine with Material and Dependency engines"""
        self.material_engine = MaterialReadinessEngine()
        self.dependency_engine = DependencyEngine()
    
    def refresh_work_order(self, work_order: Any) -> None:
        """
        Evaluate all Job Cards in Work Order
        
        Args:
            work_order: Work Order name or document
        
        Performance: < 2 seconds for 40 Job Cards
        """
        if isinstance(work_order, str):
            wo = frappe.get_doc('Work Order', work_order)
        else:
            wo = work_order
        
        # Get all Job Cards for this WO
        job_cards = frappe.get_all('Job Card',
            filters={'work_order': wo.name, 'docstatus': ['!=', 2]},
            order_by='sequence_id')
        
        # Evaluate each Job Card
        for jc_data in job_cards:
            jc = frappe.get_doc('Job Card', jc_data.name)
            result = self.evaluate_job_card(jc)
            self.apply_result_to_job_card(jc.name, result)
    
    def refresh_job_card(self, job_card: Any) -> None:
        """
        Evaluate single Job Card
        
        Args:
            job_card: Job Card name or document
        
        Performance: < 500ms
        """
        if isinstance(job_card, str):
            jc = frappe.get_doc('Job Card', job_card)
        else:
            jc = job_card
        
        result = self.evaluate_job_card(jc)
        self.apply_result_to_job_card(jc.name, result)
    
    def refresh_next_job_card(self, job_card: Any) -> None:
        """
        Refresh only next operation (not entire downstream chain)
        
        Rationale:
        - JC-20 complete → refresh JC-30
        - JC-30 will refresh JC-40 when it completes
        - No need to refresh JC-40 now (still blocked by JC-30)
        
        Args:
            job_card: Job Card that was completed
        """
        # Find NEXT operation only
        next_jc_name = frappe.db.get_value('Job Card',
            filters={
                'work_order': job_card.work_order,
                'sequence_id': job_card.sequence_id + 1,
                'docstatus': ['!=', 2]
            },
            fieldname='name')
        
        if next_jc_name:
            next_jc = frappe.get_doc('Job Card', next_jc_name)
            result = self.evaluate_job_card(next_jc)
            self.apply_result_to_job_card(next_jc_name, result)
    
    def evaluate_job_card(self, job_card) -> ReadinessResult:
        """
        Pure evaluation - no database writes
        
        Args:
            job_card: Job Card document
        
        Returns:
            ReadinessResult with all evaluation data
        """
        # Handle completed/in-progress states first
        if job_card.status == "Completed":
            material_result = self.material_engine.evaluate_material_readiness(
                work_order=job_card.work_order,
                job_card=job_card.name
            )
            return ReadinessResult.create_completed(material_result.status)
        
        if job_card.status == "Work In Progress":
            material_result = self.material_engine.evaluate_material_readiness(
                work_order=job_card.work_order,
                job_card=job_card.name
            )
            return ReadinessResult.create_in_progress(material_result.status)
        
        # Get material status
        material_result = self.material_engine.evaluate_material_readiness(
            work_order=job_card.work_order,
            job_card=job_card.name
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
            return ReadinessResult.create_ready(material_result.status)
        
        elif not material_result.is_ready:
            return ReadinessResult.create_waiting_material(material_result.message)
        
        elif not dependency_result.can_start:
            return ReadinessResult.create_waiting_previous_op(
                dependency_result.previous_jc_name or "Unknown"
            )
        
        else:
            return ReadinessResult.create_blocked(
                material_result.status,
                "Unknown reason"
            )
    
    def apply_result_to_job_card(self, job_card_name: str, result: ReadinessResult):
        """
        Apply ReadinessResult to Job Card (optimized persistence)
        
        Uses frappe.db.set_value() for efficiency (no validations/notifications).
        Only updates fields that have actually changed.
        
        Args:
            job_card_name: Job Card name
            result: ReadinessResult from evaluation
        """
        # Get current values
        current_values = frappe.db.get_value('Job Card', job_card_name, [
            'custom_material_status',
            'custom_readiness_status',
            'custom_can_start_operation',
            'custom_material_available_for_operation',
            'custom_blocked_by',
            'custom_start_status'
        ], as_dict=True)
        
        if not current_values:
            frappe.throw(_("Job Card {0} not found").format(job_card_name))
        
        # Map ReadinessStatus to custom_start_status values
        start_status_map = {
            ReadinessStatus.READY: "Ready to Start",
            ReadinessStatus.WAITING_MATERIAL: "Awaiting Material",
            ReadinessStatus.WAITING_PREVIOUS_OP: "Awaiting Previous Operation",
            ReadinessStatus.BLOCKED: "Awaiting",
            ReadinessStatus.IN_PROGRESS: "In Progress",
            ReadinessStatus.COMPLETED: "Completed",
        }
        new_start_status = start_status_map.get(result.readiness_status, "Awaiting")
        
        # Build update dict only for changed fields
        updates = {}
        
        if current_values.custom_material_status != result.material_status:
            updates['custom_material_status'] = result.material_status
        
        if current_values.custom_readiness_status != result.readiness_status:
            updates['custom_readiness_status'] = result.readiness_status
        
        if current_values.custom_can_start_operation != result.can_start:
            updates['custom_can_start_operation'] = result.can_start
        
        if current_values.custom_material_available_for_operation != result.material_available:
            updates['custom_material_available_for_operation'] = result.material_available
        
        if current_values.custom_blocked_by != result.blocked_by:
            updates['custom_blocked_by'] = result.blocked_by
        
        if current_values.custom_start_status != new_start_status:
            updates['custom_start_status'] = new_start_status
        
        # Always update timestamp
        updates['custom_dependency_last_updated'] = result.last_updated
        
        # Apply updates if any changed
        if updates:
            frappe.db.set_value('Job Card', job_card_name, updates)
