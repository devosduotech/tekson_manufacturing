"""
Work Order Repository

All Work Order database operations go through this repository.
No direct frappe.db calls in services or engines.
"""

import frappe
from frappe import _
from typing import Optional, List, Dict, Any
from frappe.model.document import Document


class WorkOrderRepository:
    """
    Work Order Repository - Data access layer for Work Orders
    """
    
    def __init__(self):
        self.doctype = "Work Order"
    
    def get(self, name: str) -> Optional[Document]:
        """Get Work Order by name"""
        try:
            return frappe.get_doc(self.doctype, name)
        except frappe.DoesNotExistError:
            return None
    
    def get_by_filters(self, filters: Dict[str, Any], 
                      fields: List[str] = None,
                      order_by: str = None,
                      limit: int = None) -> List[Dict]:
        """Get Work Orders by filters"""
        params = {
            "doctype": self.doctype,
            "filters": filters,
            "fields": fields or ["name"],
            "order_by": order_by
        }
        
        if limit:
            params["limit"] = limit
        
        return frappe.get_all(**params)
    
    def get_by_department(self, department: str) -> List[Dict]:
        """
        Get Work Orders by department
        
        Args:
            department: Department name
        
        Returns: List of Work Order dicts
        """
        return self.get_by_filters(
            {"custom_department": department},
            fields=["name", "production_item", "status", "qty", "produced_qty"]
        )
    
    def get_by_plant_floor(self, plant_floor: str) -> List[Dict]:
        """
        Get Work Orders by plant floor
        
        Args:
            plant_floor: Plant Floor name
        
        Returns: List of Work Order dicts
        """
        return self.get_by_filters(
            {"custom_plant_floor": plant_floor},
            fields=["name", "production_item", "status", "qty"]
        )
    
    def create(self, wo_dict: Dict) -> Document:
        """Create Work Order"""
        wo = frappe.new_doc(self.doctype)
        wo.update(wo_dict)
        wo.insert(ignore_permissions=True)
        return wo
    
    def update(self, name: str, fields: Dict, ignore_permissions: bool = True) -> Document:
        """Update Work Order fields"""
        wo = self.get(name)
        
        if not wo:
            raise frappe.DoesNotExistError(f"Work Order {name} not found")
        
        wo.update(fields)
        wo.save(ignore_permissions=ignore_permissions)
        
        return wo
    
    def submit(self, name: str) -> Document:
        """Submit Work Order"""
        wo = self.get(name)
        
        if not wo:
            raise frappe.DoesNotExistError(f"Work Order {name} not found")
        
        wo.submit()
        return wo
    
    def cancel(self, name: str) -> Document:
        """Cancel Work Order"""
        wo = self.get(name)
        
        if not wo:
            raise frappe.DoesNotExistError(f"Work Order {name} not found")
        
        wo.cancel()
        return wo
    
    def exists(self, name: str) -> bool:
        """Check if Work Order exists"""
        return frappe.db.exists(self.doctype, name) is not None
    
    def count(self, filters: Dict[str, Any] = None) -> int:
        """Count Work Orders"""
        return frappe.db.count(self.doctype, filters=filters or {})
    
    def get_production_progress(self, work_order: str) -> Dict:
        """
        Get production progress for Work Order
        
        Args:
            work_order: Work Order name
        
        Returns: dict with planned_qty, produced_qty, percent_complete
        """
        wo = self.get(work_order)
        
        if not wo:
            return {}
        
        return {
            'planned_qty': wo.qty,
            'produced_qty': wo.produced_qty,
            'percent_complete': (wo.produced_qty / wo.qty * 100) if wo.qty > 0 else 0,
            'status': wo.status
        }
