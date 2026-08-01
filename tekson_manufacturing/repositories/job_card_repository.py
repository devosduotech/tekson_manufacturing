"""
Job Card Repository

All Job Card database operations go through this repository.
No direct frappe.db calls in services or engines.
"""

import frappe
from frappe import _
from typing import Optional, List, Dict, Any
from frappe.model.document import Document


class JobCardRepository:
    """
    Job Card Repository - Data access layer for Job Cards
    
    All Job Card queries, inserts, updates go through this repository.
    Business logic belongs in services, not here.
    """
    
    def __init__(self):
        self.doctype = "Job Card"
    
    def get(self, name: str) -> Optional[Document]:
        """
        Get Job Card by name
        
        Args:
            name: Job Card name
        
        Returns: Job Card document or None
        
        Example:
            >>> repo = JobCardRepository()
            >>> jc = repo.get("JC-2026-001")
        """
        try:
            return frappe.get_doc(self.doctype, name)
        except frappe.DoesNotExistError:
            return None
    
    def get_by_work_order(self, work_order: str, 
                         order_by: str = "sequence_id") -> List[Document]:
        """
        Get all Job Cards for Work Order
        
        Args:
            work_order: Work Order name
            order_by: Sort field (default: sequence_id)
        
        Returns: List of Job Card documents
        
        Example:
            >>> repo = JobCardRepository()
            >>> job_cards = repo.get_by_work_order("WO-2026-001")
        """
        names = frappe.get_all(
            self.doctype,
            filters={"work_order": work_order},
            fields=["name"],
            order_by=order_by
        )
        
        return [frappe.get_doc(self.doctype, n.name) for n in names]
    
    def get_by_filters(self, filters: Dict[str, Any], 
                      fields: List[str] = None,
                      order_by: str = None,
                      limit: int = None) -> List[Dict]:
        """
        Get Job Cards by filters
        
        Args:
            filters: Filter dict
            fields: Fields to retrieve (optional)
            order_by: Sort order (optional)
            limit: Max results (optional)
        
        Returns: List of Job Card dicts
        
        Example:
            >>> repo = JobCardRepository()
            >>> jcs = repo.get_by_filters(
            ...     {"custom_department": "CNC", "status": "Work In Progress"},
            ...     fields=["name", "operation", "sequence_id"]
            ... )
        """
        params = {
            "doctype": self.doctype,
            "filters": filters,
            "fields": fields or ["name"],
            "order_by": order_by
        }
        
        if limit:
            params["limit"] = limit
        
        return frappe.get_all(**params)
    
    def get_previous_operation(self, job_card_name: str) -> Optional[Dict]:
        """
        Get previous operation for Job Card
        
        Args:
            job_card_name: Job Card name
        
        Returns: dict with name, operation, sequence_id, status or None
        
        Example:
            >>> repo = JobCardRepository()
            >>> prev_op = repo.get_previous_operation("JC-2026-002")
        """
        jc = self.get(job_card_name)
        
        if not jc or not jc.work_order or jc.sequence_id <= 1:
            return None
        
        prev_jc = frappe.db.sql("""
            SELECT name, operation, sequence_id, status
            FROM `tabJob Card`
            WHERE work_order = %s
            AND sequence_id = %s
            AND docstatus = 1
        """, (jc.work_order, jc.sequence_id - 1), as_dict=True)
        
        return prev_jc[0] if prev_jc else None
    
    def get_next_operation(self, job_card_name: str) -> Optional[Dict]:
        """
        Get next operation for Job Card
        
        Args:
            job_card_name: Job Card name
        
        Returns: dict with name, operation, sequence_id, status or None
        """
        jc = self.get(job_card_name)
        
        if not jc or not jc.work_order:
            return None
        
        next_jc = frappe.db.sql("""
            SELECT name, operation, sequence_id, status
            FROM `tabJob Card`
            WHERE work_order = %s
            AND sequence_id = %s
            AND docstatus = 1
        """, (jc.work_order, jc.sequence_id + 1), as_dict=True)
        
        return next_jc[0] if next_jc else None
    
    def create(self, jc_dict: Dict) -> Document:
        """
        Create Job Card
        
        Args:
            jc_dict: Job Card data dict
        
        Returns: Created Job Card document
        """
        jc = frappe.new_doc(self.doctype)
        jc.update(jc_dict)
        jc.insert(ignore_permissions=True)
        return jc
    
    def update(self, name: str, fields: Dict, ignore_permissions: bool = True) -> Document:
        """
        Update Job Card fields
        
        Args:
            name: Job Card name
            fields: Fields to update
            ignore_permissions: Skip permission check (default: True)
        
        Returns: Updated Job Card document
        """
        jc = self.get(name)
        
        if not jc:
            raise frappe.DoesNotExistError(f"Job Card {name} not found")
        
        jc.update(fields)
        jc.save(ignore_permissions=ignore_permissions)
        
        return jc
    
    def submit(self, name: str) -> Document:
        """
        Submit Job Card
        
        Args:
            name: Job Card name
        
        Returns: Submitted Job Card document
        """
        jc = self.get(name)
        
        if not jc:
            raise frappe.DoesNotExistError(f"Job Card {name} not found")
        
        jc.submit()
        return jc
    
    def cancel(self, name: str) -> Document:
        """
        Cancel Job Card
        
        Args:
            name: Job Card name
        
        Returns: Cancelled Job Card document
        """
        jc = self.get(name)
        
        if not jc:
            raise frappe.DoesNotExistError(f"Job Card {name} not found")
        
        jc.cancel()
        return jc
    
    def delete(self, name: str, force: bool = False) -> bool:
        """
        Delete Job Card
        
        Args:
            name: Job Card name
            force: Force delete (default: False)
        
        Returns: True if deleted
        """
        jc = self.get(name)
        
        if not jc:
            return False
        
        if jc.docstatus == 1:
            if force:
                jc.cancel()
            else:
                raise frappe.ValidationError("Cannot delete submitted Job Card")
        
        jc.delete()
        return True
    
    def exists(self, name: str) -> bool:
        """
        Check if Job Card exists
        
        Args:
            name: Job Card name
        
        Returns: True if exists
        """
        return frappe.db.exists(self.doctype, name) is not None
    
    def count(self, filters: Dict[str, Any] = None) -> int:
        """
        Count Job Cards
        
        Args:
            filters: Filter dict (optional)
        
        Returns: Count
        """
        return frappe.db.count(self.doctype, filters=filters or {})
    
    def get_sequence_details(self, work_order: str) -> List[Dict]:
        """
        Get operation sequence details for Work Order
        
        Args:
            work_order: Work Order name
        
        Returns: List of operations with sequence details
        
        Example:
            >>> repo = JobCardRepository()
            >>> sequence = repo.get_sequence_details("WO-2026-001")
            >>> len(sequence)
            5
        """
        return frappe.db.sql("""
            SELECT 
                name,
                operation,
                sequence_id,
                status,
                for_quantity,
                total_completed_qty,
                custom_start_status,
                custom_dependency_status,
                custom_material_status
            FROM `tabJob Card`
            WHERE work_order = %s
            ORDER BY sequence_id
        """, (work_order,), as_dict=True)
