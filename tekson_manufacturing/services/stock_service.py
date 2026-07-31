"""
Stock Service - Central interface for Stock Entry operations

All Stock Entry and inventory operations go through this service.
No direct Stock Entry access from other modules.
"""

import frappe
from frappe import _
from datetime import datetime


class StockService:
    """
    Stock Service - Central interface for Stock Entry operations
    
    Business Rules:
    - MR-010: Stores transfers materials
    - MR-011: Cumulative availability
    """
    
    def __init__(self):
        pass
    
    def get_stock_balance(self, item_code: str, warehouse: str = None) -> float:
        """
        Get actual stock balance
        
        Args:
            item_code: Item code
            warehouse: Warehouse (optional, defaults to all warehouses)
        
        Returns: Actual stock quantity
        
        Dependencies:
        - Stock Ledger Entry
        
        Example:
        >>> service = StockService()
        >>> service.get_stock_balance("ITEM-001", "WIP-CNC")
        150.5
        """
        filters = {"item_code": item_code, "is_cancelled": 0}
        
        if warehouse:
            filters['warehouse'] = warehouse
        
        result = frappe.db.sql("""
            SELECT SUM(actual_qty) as qty
            FROM `tabStock Ledger Entry`
            WHERE item_code = %(item_code)s
            AND warehouse = %(warehouse)s
            AND is_cancelled = 0
        """, filters, as_dict=True)
        
        return result[0].qty if result and result[0].qty else 0.0
    
    def get_cumulative_transfers(self, item_code: str, work_order: str, warehouse: str) -> float:
        """
        Get cumulative quantity transferred to warehouse
        
        Business Rule: MR-011 - Cumulative availability check
        
        Args:
            item_code: Item code
            work_order: Work Order name
            warehouse: Target warehouse
        
        Returns: Cumulative transferred quantity
        
        Dependencies:
        - Stock Entry
        - Stock Entry Detail
        
        Example:
        >>> service = StockService()
        >>> service.get_cumulative_transfers("ITEM-001", "WO-2026-001", "WIP-CNC")
        100.0
        """
        result = frappe.db.sql("""
            SELECT 
                SUM(sed.qty) as qty,
                COUNT(DISTINCT se.name) as entry_count
            FROM `tabStock Entry Detail` sed
            INNER JOIN `tabStock Entry` se ON sed.parent = se.name
            WHERE sed.item_code = %s
            AND se.work_order = %s
            AND se.purpose = 'Material Transfer for Manufacture'
            AND se.docstatus = 1
            AND sed.t_warehouse = %s
        """, (item_code, work_order, warehouse), as_dict=True)
        
        return result[0].qty if result and result[0].qty else 0.0
    
    def get_transfer_entries(self, item_code: str, work_order: str, warehouse: str) -> list:
        """
        Get all Stock Entries that transferred material
        
        Business Rule: MR-011 - Working set principle
        
        Args:
            item_code: Item code
            work_order: Work Order name
            warehouse: Target warehouse
        
        Returns: list of Stock Entry details
        
        Example:
        >>> service = StockService()
        >>> entries = service.get_transfer_entries("ITEM-001", "WO-2026-001", "WIP-CNC")
        >>> len(entries)
        3
        """
        entries = frappe.db.sql("""
            SELECT 
                se.name as stock_entry,
                se.posting_date,
                se.posting_time,
                sed.qty,
                sed.uom,
                se.user
            FROM `tabStock Entry Detail` sed
            INNER JOIN `tabStock Entry` se ON sed.parent = se.name
            WHERE sed.item_code = %s
            AND se.work_order = %s
            AND se.purpose = 'Material Transfer for Manufacture'
            AND se.docstatus = 1
            AND sed.t_warehouse = %s
            ORDER BY se.posting_date, se.posting_time
        """, (item_code, work_order, warehouse), as_dict=True)
        
        return entries
    
    def create_material_transfer(self, work_order: str, items: list,
                                from_warehouse: str, to_warehouse: str,
                                user: str = None) -> dict:
        """
        Create Material Transfer Stock Entry
        
        Business Rule: MR-010 - Stores transfers materials
        
        Args:
            work_order: Work Order name
            items: list of dicts with item_code, qty
            from_warehouse: Source warehouse
            to_warehouse: Target warehouse
            user: User creating (optional, defaults to current user)
        
        Returns: dict with stock_entry, success, message
        
        Raises:
            MESValidationError: If creation fails
        
        Example:
        >>> service = StockService()
        >>> result = service.create_material_transfer(
        ...     work_order="WO-2026-001",
        ...     items=[{'item_code': 'ITEM-001', 'qty': 100}],
        ...     from_warehouse="Raw Materials Stores",
        ...     to_warehouse="WIP-CNC"
        ... )
        >>> result['success']
        True
        """
        if not user:
            user = frappe.session.user
        
        try:
            se = frappe.new_doc("Stock Entry")
            se.purpose = "Material Transfer for Manufacture"
            se.work_order = work_order
            se.from_warehouse = from_warehouse
            se.to_warehouse = to_warehouse
            se.company = frappe.db.get_value("Work Order", work_order, "company")
            
            for item in items:
                se.append("items", {
                    "item_code": item['item_code'],
                    "qty": item['qty'],
                    "s_warehouse": from_warehouse,
                    "t_warehouse": to_warehouse,
                    "uom": frappe.db.get_value("Item", item['item_code'], "stock_uom"),
                    "basic_rate": item.get('rate', 0)
                })
            
            se.insert(ignore_permissions=True)
            se.submit()
            
            # Log
            frappe.log_error(
                message=f"[MES] [MATERIAL] [INFO] [MR-010] Material transfer created: {se.name} | Context: {{'wo': '{work_order}', 'items': {len(items)}}}",
                title=f"MES Material Transfer - {se.name}"
            )
            
            return {
                'stock_entry': se.name,
                'success': True,
                'message': f"Material transfer {se.name} created successfully",
                'items_transferred': len(se.items)
            }
            
        except Exception as e:
            frappe.log_error(
                message=f"[MES] [MATERIAL] [ERROR] [MR-010] Failed to create material transfer: {str(e)} | Context: {{'wo': '{work_order}'}}",
                title=f"MES Material Transfer Error - {work_order}"
            )
            
            return {
                'stock_entry': None,
                'success': False,
                'message': f"Failed to create transfer: {str(e)}",
                'error': str(e)
            }
    
    def create_manufacture_entry(self, work_order: str, quantity: float,
                                user: str = None) -> dict:
        """
        Create Manufacture Stock Entry
        
        Business Rule: WO-001 - Auto-completion
        
        Args:
            work_order: Work Order name
            quantity: Quantity to manufacture
            user: User creating (optional)
        
        Returns: dict with stock_entry, success, message
        """
        if not user:
            user = frappe.session.user
        
        try:
            wo = frappe.get_doc("Work Order", work_order)
            
            se = frappe.new_doc("Stock Entry")
            se.purpose = "Manufacture"
            se.work_order = work_order
            se.from_warehouse = self.get_department_warehouse(wo)
            se.to_warehouse = self.get_finished_goods_warehouse(wo)
            se.company = wo.company
            
            # Add finished good
            se.append("items", {
                "item_code": wo.production_item,
                "qty": quantity,
                "s_warehouse": se.from_warehouse,
                "t_warehouse": se.to_warehouse,
                "uom": frappe.db.get_value("Item", wo.production_item, "stock_uom")
            })
            
            se.insert(ignore_permissions=True)
            se.submit()
            
            # Log
            frappe.log_error(
                message=f"[MES] [EXECUTION] [INFO] [WO-001] Manufacture entry created: {se.name} | Context: {{'wo': '{work_order}', 'qty': {quantity}}}",
                title=f"MES Manufacture Entry - {se.name}"
            )
            
            return {
                'stock_entry': se.name,
                'success': True,
                'message': f"Manufacture entry {se.name} created successfully"
            }
            
        except Exception as e:
            frappe.log_error(
                message=f"[MES] [EXECUTION] [ERROR] [WO-001] Failed to create manufacture entry: {str(e)} | Context: {{'wo': '{work_order}'}}",
                title=f"MES Manufacture Entry Error - {work_order}"
            )
            
            return {
                'stock_entry': None,
                'success': False,
                'message': f"Failed to create manufacture entry: {str(e)}",
                'error': str(e)
            }
    
    def get_warehouse_type(self, warehouse: str) -> str:
        """
        Get warehouse type (WIP, Raw Material, etc.)
        
        Args:
            warehouse: Warehouse name
        
        Returns: Warehouse type
        
        Example:
        >>> service = StockService()
        >>> service.get_warehouse_type("WIP-CNC")
        'WIP'
        """
        return frappe.db.get_value("Warehouse", warehouse, "custom_warehouse_type") or \
               frappe.db.get_value("Warehouse", warehouse, "warehouse_group")
    
    def get_department_warehouse(self, work_order) -> str:
        """
        Get Department Warehouse for Work Order
        
        Business Rule: WH-002 - Department Warehouse Mapping
        
        Args:
            work_order: Work Order document or name
        
        Returns: Department warehouse name
        
        Raises:
            MESValidationError: If warehouse not found
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
            "Warehouse",
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
                "Warehouse",
                {"name": ["like", f"WIP-{plant_floor}"]},
                "name"
            )
        
        if not warehouse:
            from tekson_manufacturing.utils.exceptions import MESConfigurationError
            raise MESConfigurationError(
                f"Warehouse not found for Plant Floor: {plant_floor}. Please configure Warehouse with Plant Floor '{plant_floor}' under Work In Progress Stores."
            )
        
        return warehouse
    
    def get_finished_goods_warehouse(self, work_order) -> str:
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
            "Warehouse",
            {"warehouse_group": "Finished Goods", "is_group": 0},
            "name"
        )


@frappe.whitelist()
def get_stock_balance(item_code, warehouse=None):
    """
    Whitelisted method to get stock balance
    
    Args:
        item_code: Item code
        warehouse: Warehouse (optional)
    
    Returns: Stock balance
    """
    service = StockService()
    return service.get_stock_balance(item_code, warehouse)


@frappe.whitelist()
def get_cumulative_transfers(item_code, work_order, warehouse):
    """
    Whitelisted method to get cumulative transfers
    
    Args:
        item_code: Item code
        work_order: Work Order name
        warehouse: Warehouse
    
    Returns: Cumulative transferred quantity
    """
    service = StockService()
    return service.get_cumulative_transfers(item_code, work_order, warehouse)


@frappe.whitelist()
def create_material_transfer(work_order, items, from_warehouse, to_warehouse):
    """
    Whitelisted method to create material transfer
    
    Args:
        work_order: Work Order name
        items: JSON string with items list
        from_warehouse: Source warehouse
        to_warehouse: Target warehouse
    
    Returns: dict with stock_entry, success, message
    """
    import json
    
    if isinstance(items, str):
        items = json.loads(items)
    
    service = StockService()
    return service.create_material_transfer(
        work_order=work_order,
        items=items,
        from_warehouse=from_warehouse,
        to_warehouse=to_warehouse
    )
