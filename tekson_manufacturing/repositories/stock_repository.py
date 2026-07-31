"""
Stock Repository

All Stock Entry and Stock Ledger database operations go through this repository.
No direct frappe.db calls in services or engines.
"""

import frappe
from frappe import _
from typing import Optional, List, Dict, Any


class StockRepository:
    """
    Stock Repository - Data access layer for Stock Entries and Stock Ledger
    """
    
    def __init__(self):
        self.stock_entry_doctype = "Stock Entry"
        self.stock_ledger_doctype = "Stock Ledger Entry"
    
    def get_stock_entry(self, name: str) -> Optional[frappe.Document]:
        """Get Stock Entry by name"""
        try:
            return frappe.get_doc(self.stock_entry_doctype, name)
        except frappe.DoesNotExistError:
            return None
    
    def get_stock_balance(self, item_code: str, warehouse: str = None) -> float:
        """
        Get actual stock balance
        
        Args:
            item_code: Item code
            warehouse: Warehouse (optional)
        
        Returns: Actual stock quantity
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
    
    def get_cumulative_transfers(self, item_code: str, work_order: str, 
                                warehouse: str) -> float:
        """
        Get cumulative quantity transferred to warehouse
        
        Business Rule: MR-011
        
        Args:
            item_code: Item code
            work_order: Work Order name
            warehouse: Target warehouse
        
        Returns: Cumulative transferred quantity
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
    
    def get_transfer_entries(self, item_code: str, work_order: str, 
                            warehouse: str) -> List[Dict]:
        """
        Get all Stock Entries that transferred material
        
        Args:
            item_code: Item code
            work_order: Work Order name
            warehouse: Target warehouse
        
        Returns: List of Stock Entry details
        """
        return frappe.db.sql("""
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
    
    def get_entries_by_work_order(self, work_order: str) -> List[Dict]:
        """
        Get all Stock Entries for Work Order
        
        Args:
            work_order: Work Order name
        
        Returns: List of Stock Entry details
        """
        return frappe.db.sql("""
            SELECT 
                name,
                purpose,
                docstatus,
                posting_date,
                posting_time,
                total_qty
            FROM `tabStock Entry`
            WHERE work_order = %s
            AND docstatus = 1
            ORDER BY posting_date, posting_time
        """, (work_order,), as_dict=True)
    
    def create_stock_entry(self, se_dict: Dict) -> frappe.Document:
        """
        Create Stock Entry
        
        Args:
            se_dict: Stock Entry data dict
        
        Returns: Created Stock Entry document
        """
        se = frappe.new_doc(self.stock_entry_doctype)
        se.update(se_dict)
        se.insert(ignore_permissions=True)
        return se
    
    def submit_stock_entry(self, name: str) -> frappe.Document:
        """Submit Stock Entry"""
        se = self.get_stock_entry(name)
        
        if not se:
            raise frappe.DoesNotExistError(f"Stock Entry {name} not found")
        
        se.submit()
        return se
    
    def cancel_stock_entry(self, name: str) -> frappe.Document:
        """Cancel Stock Entry"""
        se = self.get_stock_entry(name)
        
        if not se:
            raise frappe.DoesNotExistError(f"Stock Entry {name} not found")
        
        se.cancel()
        return se
    
    def get_stock_ledger_entries(self, item_code: str, warehouse: str = None,
                                from_date: str = None, to_date: str = None) -> List[Dict]:
        """
        Get Stock Ledger Entries for item
        
        Args:
            item_code: Item code
            warehouse: Warehouse (optional)
            from_date: From date (optional)
            to_date: To date (optional)
        
        Returns: List of Stock Ledger Entries
        """
        filters = {"item_code": item_code, "is_cancelled": 0}
        
        if warehouse:
            filters['warehouse'] = warehouse
        
        if from_date:
            filters['posting_date'] = [">=", from_date]
        
        if to_date:
            if 'posting_date' in filters:
                filters['posting_date'] = [">=", from_date, "<=", to_date]
            else:
                filters['posting_date'] = ["<=", to_date]
        
        return frappe.db.sql("""
            SELECT 
                name,
                posting_date,
                posting_time,
                actual_qty,
                qty_after_transaction,
                warehouse,
                voucher_type,
                voucher_no
            FROM `tabStock Ledger Entry`
            WHERE item_code = %(item_code)s
            AND is_cancelled = 0
            ORDER BY posting_date, posting_time
        """, filters, as_dict=True)
    
    def exists(self, name: str) -> bool:
        """Check if Stock Entry exists"""
        return frappe.db.exists(self.stock_entry_doctype, name) is not None
    
    def count_entries_by_work_order(self, work_order: str, 
                                   purpose: str = None) -> int:
        """
        Count Stock Entries for Work Order
        
        Args:
            work_order: Work Order name
            purpose: Filter by purpose (optional)
        
        Returns: Count
        """
        filters = {"work_order": work_order, "docstatus": 1}
        
        if purpose:
            filters['purpose'] = purpose
        
        return frappe.db.count(self.stock_entry_doctype, filters=filters)
