import frappe
from frappe import _


class WorkOrderService:
    """
    Work Order Service Layer
    
    Business Rules:
    - WO-001: Work Order creation validation
    - WO-002: Warehouse structure validation
    - WO-003: Status management
    """
    
    def __init__(self):
        self.repo = self._get_repository()
    
    def _get_repository(self):
        """Get Work Order Repository"""
        from tekson_manufacturing.repositories.work_order_repository import WorkOrderRepository
        return WorkOrderRepository()
    
    def get_work_order_details(self, work_order_name):
        """
        Get Work Order details with warehouse structure
        
        Args:
            work_order_name: Work Order name
        
        Returns: dict with WO details
        """
        wo = self.repo.get(work_order_name)
        
        if not wo:
            frappe.throw(_("Work Order {0} not found").format(work_order_name))
        
        return {
            'name': wo.name,
            'production_item': wo.production_item,
            'qty': wo.qty,
            'produced_qty': wo.produced_qty or 0,
            'status': wo.status,
            'source_warehouse': wo.source_warehouse,
            'wip_warehouse': wo.wip_warehouse,
            'fg_warehouse': wo.fg_warehouse,
            'custom_plant_floor': wo.get('custom_plant_floor') or wo.get('plant_floor'),
            'bom_no': wo.bom_no,
            'company': wo.company
        }
    
    def complete(self, work_order_name):
        """
        Complete Work Order
        
        Args:
            work_order_name: Work Order name
        
        Returns: dict with success message
        """
        wo = frappe.get_doc('Work Order', work_order_name)
        
        if wo.status != 'Completed':
            frappe.throw(_("Work Order {0} is not in Completed status").format(work_order_name))
        
        return {
            'success': True,
            'message': _("Work Order {0} completed successfully").format(work_order_name)
        }
    
    def refresh_status(self, work_order_name):
        """
        Refresh Work Order status based on Job Cards and Stock Entries
        
        Args:
            work_order_name: Work Order name
        
        Returns: dict with updated status
        """
        wo = frappe.get_doc('Work Order', work_order_name)
        
        # Get Job Card status
        job_cards = frappe.get_all(
            'Job Card',
            filters={'work_order': work_order_name, 'docstatus': 1},
            fields=['name', 'status', 'operation']
        )
        
        # Get Stock Entry status
        stock_entries = frappe.get_all(
            'Stock Entry',
            filters={'work_order': work_order_name, 'docstatus': 1},
            fields=['name', 'stock_entry_type', 'posting_date']
        )
        
        return {
            'work_order': work_order_name,
            'current_status': wo.status,
            'job_cards_count': len(job_cards),
            'stock_entries_count': len(stock_entries),
            'job_cards': job_cards,
            'stock_entries': stock_entries
        }
