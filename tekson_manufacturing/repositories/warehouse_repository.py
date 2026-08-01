"""
Warehouse Repository

All Warehouse database operations go through this repository.
No direct frappe.db calls in services or engines.
"""

import frappe
from frappe import _
from typing import Optional, List, Dict, Any
from frappe.model.document import Document


class WarehouseRepository:
    """
    Warehouse Repository - Data access layer for Warehouses
    """
    
    def __init__(self):
        self.doctype = "Warehouse"
    
    def get(self, name: str) -> Optional[Document]:
        """Get Warehouse by name"""
        try:
            return frappe.get_doc(self.doctype, name)
        except frappe.DoesNotExistError:
            return None
    
    def get_by_department(self, department: str) -> Optional[Document]:
        """
        Get warehouse for department
        
        Args:
            department: Department name
        
        Returns: Warehouse document or None
        """
        name = frappe.db.get_value(
            self.doctype,
            {"custom_department": department, "is_group": 0},
            "name"
        )
        
        return self.get(name) if name else None
    
    def get_by_plant_floor(self, plant_floor: str) -> Optional[Document]:
        """
        Get warehouse for plant floor
        
        Args:
            plant_floor: Plant Floor name
        
        Returns: Warehouse document or None
        """
        name = frappe.db.get_value(
            self.doctype,
            {"custom_plant_floor": plant_floor, "is_group": 0},
            "name"
        )
        
        return self.get(name) if name else None
    
    def get_by_warehouse_group(self, warehouse_group: str, 
                              is_group: bool = False) -> List[Dict]:
        """
        Get warehouses by warehouse group
        
        Args:
            warehouse_group: Warehouse Group name
            is_group: Filter by is_group flag (default: False)
        
        Returns: List of Warehouse dicts
        """
        return frappe.db.sql("""
            SELECT 
                name,
                warehouse_group,
                custom_plant_floor,
                custom_department,
                custom_warehouse_type,
                is_group
            FROM `tabWarehouse`
            WHERE warehouse_group = %s
            AND is_group = %s
            ORDER BY name
        """, (warehouse_group, 1 if is_group else 0), as_dict=True)
    
    def get_all_department_warehouses(self) -> List[Dict]:
        """
        Get all department warehouses
        
        Returns: List of warehouse dicts with department info
        """
        return frappe.db.sql("""
            SELECT 
                name,
                warehouse_group,
                custom_plant_floor,
                custom_department,
                custom_warehouse_type
            FROM `tabWarehouse`
            WHERE warehouse_group = 'Work In Progress Stores'
            AND is_group = 0
            ORDER BY name
        """, as_dict=True)
    
    def get_department_warehouse(self, work_order) -> Optional[str]:
        """
        Get Department Warehouse for Work Order
        
        Business Rule: WH-002
        
        Args:
            work_order: Work Order document or name
        
        Returns: Warehouse name or None
        """
        if isinstance(work_order, str):
            wo = frappe.get_doc("Work Order", work_order)
        else:
            wo = work_order
        
        # Get Plant Floor from Work Order
        plant_floor = wo.get('custom_plant_floor') or wo.get('plant_floor')
        
        if not plant_floor:
            # Fallback to default warehouse
            return frappe.db.get_value("Item", wo.production_item, "default_warehouse")
        
        # Map Plant Floor to Warehouse
        warehouse = frappe.db.get_value(
            self.doctype,
            {
                "warehouse_group": "Work In Progress Stores",
                "custom_plant_floor": plant_floor,
                "is_group": 0
            },
            "name"
        )
        
        if not warehouse:
            # Try pattern match
            warehouse = frappe.db.get_value(
                self.doctype,
                {"name": ["like", f"WIP-{plant_floor}"]},
                "name"
            )
        
        return warehouse
    
    def get_finished_goods_warehouse(self, work_order) -> Optional[str]:
        """
        Get Finished Goods Warehouse for Work Order
        
        Args:
            work_order: Work Order document or name
        
        Returns: Finished goods warehouse name
        """
        if isinstance(work_order, str):
            wo = frappe.get_doc("Work Order", work_order)
        else:
            wo = work_order
        
        # Try to get from production item
        fg_warehouse = frappe.db.get_value("Item", wo.production_item, "default_warehouse")
        
        if fg_warehouse:
            return fg_warehouse
        
        # Fallback to Finished Goods warehouse
        return frappe.db.get_value(
            self.doctype,
            {"warehouse_group": "Finished Goods", "is_group": 0},
            "name"
        )
    
    def get_warehouse_type(self, warehouse: str) -> str:
        """
        Get warehouse type
        
        Args:
            warehouse: Warehouse name
        
        Returns: Warehouse type
        """
        wh = self.get(warehouse)
        
        if not wh:
            return ""
        
        return wh.get('custom_warehouse_type') or wh.get('warehouse_group')
    
    def validate_warehouse_access(self, warehouse: str, user: str) -> bool:
        """
        Validate user has access to warehouse
        
        Args:
            warehouse: Warehouse name
            user: User name
        
        Returns: True if user has access
        """
        wh = self.get(warehouse)
        
        if not wh:
            return False
        
        # Check department scope
        if not wh.custom_department:
            return True  # No department restriction
        
        # Get user's department
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
        
        if not employee:
            return False
        
        user_department = frappe.db.get_value("Employee", employee, "department")
        
        return user_department == wh.custom_department
    
    def exists(self, name: str) -> bool:
        """Check if Warehouse exists"""
        return frappe.db.exists(self.doctype, name) is not None
    
    def create(self, wh_dict: Dict) -> frappe.Document:
        """
        Create Warehouse
        
        Args:
            wh_dict: Warehouse data dict
        
        Returns: Created Warehouse document
        """
        wh = frappe.new_doc(self.doctype)
        wh.update(wh_dict)
        wh.insert(ignore_permissions=True)
        return wh
