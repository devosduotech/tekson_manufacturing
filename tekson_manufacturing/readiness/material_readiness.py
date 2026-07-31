import frappe
from frappe import _


class MaterialReadinessEngine:
    """
    Material Readiness Engine - Core of MES
    
    Determines if materials are available for production.
    Source-agnostic: checks inventory regardless of origin
    (internal manufacturing, purchase, subcontract, existing stock)
    """
    
    def __init__(self, work_order=None, job_card=None):
        self.work_order = work_order
        self.job_card = job_card
        self.results = {
            'is_ready': True,
            'missing_items': [],
            'shortage_details': []
        }
    
    def evaluate_material_readiness(self, work_order=None):
        """
        Evaluate material readiness for a Work Order
        
        Returns: dict with is_ready, missing_items, shortage_details
        """
        if not work_order:
            work_order = self.work_order
        
        if not work_order:
            frappe.throw(_("Work Order is required"))
        
        wo = frappe.get_doc("Work Order", work_order)
        
        # Get all required materials from BOM
        required_materials = self.get_required_materials(wo)
        
        for material in required_materials:
            item_code = material.get('item_code')
            required_qty = material.get('qty')
            warehouse = material.get('source_warehouse')
            
            # Get material classification
            material_type = self.classify_material_type(item_code, wo)
            
            # Check availability based on material type
            availability = self.check_material_availability(
                item_code, 
                required_qty, 
                warehouse,
                material_type,
                wo
            )
            
            if not availability.get('is_available'):
                self.results['is_ready'] = False
                self.results['missing_items'].append(item_code)
                self.results['shortage_details'].append({
                    'item_code': item_code,
                    'item_name': availability.get('item_name'),
                    'required_qty': required_qty,
                    'available_qty': availability.get('available_qty'),
                    'shortage_qty': availability.get('shortage_qty'),
                    'warehouse': warehouse,
                    'material_type': material_type,
                    'reason': availability.get('reason'),
                    'action': availability.get('action')
                })
        
        return self.results
    
    def get_required_materials(self, work_order):
        """Get all materials required for the work order"""
        materials = []
        
        # Get BOM materials
        if work_order.bom_no:
            bom_items = frappe.get_all(
                "BOM Item",
                filters={"parent": work_order.bom_no},
                fields=["item_code", "qty", "uom", "source_warehouse"]
            )
            
            for item in bom_items:
                materials.append({
                    'item_code': item.item_code,
                    'qty': (item.qty * work_order.qty) / self.get_bom_qty(work_order.bom_no),
                    'uom': item.uom,
                    'source_warehouse': item.source_warehouse
                })
        
        return materials
    
    def get_bom_qty(self, bom_no):
        """Get BOM base quantity"""
        return frappe.db.get_value("BOM", bom_no, "quantity") or 1
    
    def classify_material_type(self, item_code, work_order):
        """
        Classify material type:
        - Raw Material
        - Purchased Component
        - Manufactured Component
        - Common Component
        - Sub Assembly
        - Subcontracted Item
        """
        item = frappe.get_doc("Item", item_code)
        
        # Check if item has default BOM (manufactured)
        has_bom = frappe.db.exists("BOM", {"item": item_code, "is_active": 1})
        
        # Check if item is subcontracted
        is_subcontracted = item.is_sub_contracted_item
        
        # Check if common component (simplified - can be enhanced)
        is_common = self.is_common_component(item_code)
        
        if is_subcontracted:
            return "Subcontracted"
        elif has_bom:
            if is_common:
                return "Common Component"
            else:
                return "Manufactured Component"
        else:
            return "Raw Material"
    
    def is_common_component(self, item_code):
        """
        Check if item is a common component used across multiple FGs
        This can be enhanced with a proper configuration table
        """
        # For now, check if item is used in more than 1 BOM
        bom_count = frappe.db.count("BOM Item", {"item_code": item_code})
        return bom_count > 3  # Threshold can be configured
    
    def check_material_availability(self, item_code, required_qty, warehouse, material_type, work_order):
        """
        Check if material is available
        
        For Raw Materials: Check cumulative transfers
        For Manufactured Components: Check stock in WIP/Stores
        For Common Components: Check global stock
        """
        result = {
            'is_available': True,
            'available_qty': 0,
            'shortage_qty': 0,
            'reason': '',
            'action': ''
        }
        
        # Get item details
        item = frappe.get_doc("Item", item_code)
        result['item_name'] = item.item_name or item_code
        
        # Get actual stock balance
        actual_qty = self.get_actual_stock(item_code, warehouse)
        result['available_qty'] = actual_qty
        
        # Check if sufficient stock
        if actual_qty >= required_qty:
            return result
        
        # Insufficient stock
        result['is_available'] = False
        result['shortage_qty'] = required_qty - actual_qty
        
        # Determine reason and action based on material type
        if material_type == "Raw Material":
            result['reason'] = self.get_raw_material_reason(item_code, work_order)
            result['action'] = "Check pending material transfers"
        
        elif material_type == "Manufactured Component":
            result['reason'] = self.get_manufactured_component_reason(item_code, work_order)
            result['action'] = "Check child work order status"
        
        elif material_type == "Common Component":
            result['reason'] = self.get_common_component_reason(item_code)
            result['action'] = "Check global stock or production"
        
        elif material_type == "Subcontracted":
            result['reason'] = self.get_subcontract_reason(item_code, work_order)
            result['action'] = "Check subcontract order status"
        
        return result
    
    def get_actual_stock(self, item_code, warehouse=None):
        """Get actual stock balance from Stock Ledger"""
        filters = {"item_code": item_code}
        
        if warehouse:
            filters['warehouse'] = warehouse
        
        # Get stock balance
        stock_balance = frappe.db.sql("""
            SELECT SUM(actual_qty) as qty
            FROM `tabStock Ledger Entry`
            WHERE item_code = %s
            AND warehouse = %s
            AND is_cancelled = 0
        """, (item_code, warehouse), as_dict=True)
        
        return stock_balance[0].qty if stock_balance and stock_balance[0].qty else 0
    
    def get_cumulative_transferred_qty(self, item_code, work_order, warehouse):
        """
        Get cumulative quantity transferred to WIP warehouse
        Sums all Material Transfer Stock Entries
        """
        transfers = frappe.db.sql("""
            SELECT SUM(sed.qty) as qty
            FROM `tabStock Entry Detail` sed
            INNER JOIN `tabStock Entry` se ON sed.parent = se.name
            WHERE sed.item_code = %s
            AND se.work_order = %s
            AND se.purpose = 'Material Transfer for Manufacture'
            AND se.docstatus = 1
            AND sed.t_warehouse = %s
        """, (item_code, work_order, warehouse), as_dict=True)
        
        return transfers[0].qty if transfers and transfers[0].qty else 0
    
    def get_raw_material_reason(self, item_code, work_order):
        """Get reason for raw material shortage"""
        # Check if there are pending transfers
        pending_transfer = self.get_pending_transfer_qty(item_code, work_order)
        
        if pending_transfer > 0:
            return f"Pending transfer: {pending_transfer} kg"
        
        # Check purchase orders
        pending_po = self.get_pending_purchase_order_qty(item_code)
        
        if pending_po > 0:
            return f"Pending purchase order: {pending_po} kg"
        
        return "Insufficient stock"
    
    def get_manufactured_component_reason(self, item_code, work_order):
        """Get reason for manufactured component shortage"""
        # Check if there's a child work order
        child_wo = self.get_child_work_order(item_code, work_order)
        
        if child_wo:
            wo_status = frappe.db.get_value("Work Order", child_wo, "status")
            produced_qty = frappe.db.get_value("Work Order", child_wo, "produced_qty")
            
            if wo_status == "Not Started":
                return f"Child WO not started"
            elif wo_status == "In Process":
                return f"Child WO in process ({produced_qty} completed)"
            elif wo_status == "Completed":
                return "Completed but not transferred"
        
        # Check if there's existing stock
        actual_stock = self.get_actual_stock(item_code)
        
        if actual_stock > 0:
            return f"Available in stock: {actual_stock}"
        
        return "No production or stock"
    
    def get_common_component_reason(self, item_code):
        """Get reason for common component shortage"""
        # Check global stock
        actual_stock = self.get_actual_stock(item_code)
        
        if actual_stock > 0:
            return f"Available in stock: {actual_stock} (but reserved)"
        
        # Check if any WO is producing it
        producing_wo = frappe.db.sql("""
            SELECT name, status, produced_qty
            FROM `tabWork Order`
            WHERE production_item = %s
            AND status IN ('In Process', 'Submitted')
            ORDER BY creation DESC
            LIMIT 1
        """, (item_code), as_dict=True)
        
        if producing_wo:
            return f"Being produced: {producing_wo[0].status} ({producing_wo[0].produced_qty} completed)"
        
        return "No stock or production"
    
    def get_subcontract_reason(self, item_code, work_order):
        """Get reason for subcontracted item shortage"""
        # Check subcontract order
        # This can be enhanced with actual subcontract order tracking
        return "Pending subcontract receipt"
    
    def get_pending_transfer_qty(self, item_code, work_order):
        """Get pending transfer quantity"""
        # Simplified - can be enhanced with actual transfer tracking
        return 0
    
    def get_pending_purchase_order_qty(self, item_code):
        """Get pending purchase order quantity"""
        # Simplified - can be enhanced with actual PO tracking
        return 0
    
    def get_child_work_order(self, item_code, parent_wo):
        """Get child work order for an item"""
        child_wo = frappe.db.sql("""
            SELECT name
            FROM `tabWork Order`
            WHERE production_item = %s
            AND (
                (select name from `tabBOM` where item = %s and name = (select bom_no from `tabWork Order` where name = %s))
                IS NOT NULL
            )
            ORDER BY creation DESC
            LIMIT 1
        """, (item_code, item_code, parent_wo), as_dict=True)
        
        return child_wo[0].name if child_wo else None


@frappe.whitelist()
def evaluate_material_readiness(work_order):
    """
    Whitelisted method to evaluate material readiness
    
    Args:
        work_order: Work Order name
    
    Returns: dict with readiness status
    """
    engine = MaterialReadinessEngine(work_order=work_order)
    return engine.evaluate_material_readiness()
