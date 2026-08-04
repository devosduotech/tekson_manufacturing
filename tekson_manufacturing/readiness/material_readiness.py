import frappe
from frappe import _
from datetime import datetime
from typing import Dict, Any, List

from tekson_manufacturing.mes.dataclasses import MaterialResult, MaterialStatus


class MaterialReadinessEngine:
    """
    Material Readiness Engine - Core of MES
    
    Determines if materials are available for production.
    Source-agnostic: checks inventory regardless of origin
    (internal manufacturing, purchase, subcontract, existing stock)
    
    Business Rules:
    - MR-010: Stores transfers materials to Department Warehouse before production starts
    - MR-011: Cumulative availability check across multiple Stock Entries
    """
    
    def __init__(self, work_order=None, job_card=None):
        self.work_order = work_order
        self.job_card = job_card
        self.results = {
            'is_ready': True,
            'missing_items': [],
            'shortage_details': [],
            'transferred_items': [],
            'transfer_summary': {}
        }
    
    def evaluate_material_readiness(self, work_order=None, job_card=None) -> MaterialResult:
        """
        Evaluate material readiness for a Work Order
        
        Business Rules:
        - MR-010: Validates materials transferred to Department Warehouse
        - MR-011: Checks cumulative availability across multiple Stock Entries
        
        Args:
            work_order: Work Order name (optional, uses self.work_order if not provided)
            job_card: Job Card name (optional, for context)
        
        Returns: MaterialResult with is_ready, status, quantities, and details
        
        Dependencies:
        - Work Order
        - BOM
        - Stock Ledger Entry
        - Stock Entry
        
        Test Case:
        - test_mr_010_stores_transfer_validation
        - test_mr_011_cumulative_availability_check
        
        Example:
        >>> engine = MaterialReadinessEngine(work_order="WO-2026-001")
        >>> result = engine.evaluate_material_readiness()
        >>> result.is_ready
        True
        """
        if not work_order:
            work_order = self.work_order
        
        if not work_order:
            frappe.throw(_("Work Order is required"))
        
        # Store in instance for later use
        self.work_order = work_order
        self.job_card = job_card
        wo = frappe.get_doc("Work Order", work_order)
        
        # Get Department Warehouse for the Work Order
        department_warehouse = self.get_department_warehouse(wo)
        
        # Get all required materials from BOM
        required_materials = self.get_required_materials(wo)
        
        # Track shortages
        total_required = 0.0
        total_available = 0.0
        shortage_details = []
        warnings = []
        errors = []
        
        for material in required_materials:
            item_code = material.get('item_code')
            required_qty = material.get('qty')
            total_required += required_qty
            
            # MR-014: Check stock in the BOM item's source warehouse (department WIP)
            item_warehouse = material.get('source_warehouse') or department_warehouse
            
            available_qty = self.get_available_stock_in_wip(
                item_code,
                item_warehouse
            )
            total_available += available_qty
            
            # Check for shortage
            if available_qty < required_qty:
                shortage_qty = required_qty - available_qty
                shortage_details.append({
                    'item_code': item_code,
                    'item_name': material.get('item_name', ''),
                    'required_qty': required_qty,
                    'available_qty': available_qty,
                    'shortage_qty': shortage_qty,
                    'warehouse': item_warehouse
                })
        
        # Calculate totals
        shortage_qty = max(0, total_required - total_available)
        is_ready = len(shortage_details) == 0
        
        # Determine status
        if is_ready:
            status = MaterialStatus.AVAILABLE
            message = _("All materials available")
        elif total_available > 0:
            status = MaterialStatus.SHORT
            message = _("Partial material available. Shortage: {0}").format(shortage_qty)
        else:
            status = MaterialStatus.WAITING
            message = _("Waiting for material transfer")
        
        # Build MaterialResult
        return MaterialResult(
            is_ready=is_ready,
            status=status,
            available_qty=total_available,
            required_qty=total_required,
            shortage_qty=shortage_qty,
            shortage_details=shortage_details,
            warehouse=wo.wip_warehouse or department_warehouse,
            message=message,
            warnings=warnings,
            errors=errors
        )
        
        # Legacy: Also populate self.results for backward compatibility
        self.results['is_ready'] = is_ready
        self.results['missing_items'] = [d['item_code'] for d in shortage_details]
        self.results['shortage_details'] = shortage_details
        
        return self.results
    
    def get_required_materials(self, work_order):
        """
        Get all materials required for the work order from BOM
        
        Args:
            work_order: Work Order document
        
        Returns: list of dicts with item_code, qty, uom, source_warehouse
        
        Dependencies:
        - BOM Item
        - BOM
        
        Example:
        >>> materials = self.get_required_materials(wo)
        >>> len(materials)
        5
        """
        materials = []
        
        # Get BOM materials
        if work_order.bom_no:
            bom_items = frappe.db.get_all(
                "BOM Item",
                filters={"parent": work_order.bom_no},
                fields=["item_code", "qty", "uom", "source_warehouse"]
            )
            
            bom_qty = self.get_bom_qty(work_order.bom_no)
            
            for item in bom_items:
                # Calculate required qty based on WO quantity
                required_qty = (item.qty * work_order.qty) / bom_qty if bom_qty > 0 else item.qty
                
                materials.append({
                    'item_code': item.item_code,
                    'qty': required_qty,
                    'uom': item.uom,
                    'source_warehouse': item.source_warehouse
                })
        
        return materials
    
    def get_bom_qty(self, bom_no):
        """
        Get BOM base quantity
        
        Args:
            bom_no: BOM name
        
        Returns: float - BOM base quantity
        
        Example:
        >>> self.get_bom_qty("BOM-001")
        100.0
        """
        return frappe.db.get_value("BOM", bom_no, "quantity") or 1.0
    
    def determine_transfer_status(self, item_code, required_qty, cumulative_transferred, current_stock):
        """
        Determine transfer status for an item
        
        Business Rules:
        - MR-010: Stores transfer validation
        - MR-011: Cumulative availability
        
        Args:
            item_code: Item code
            required_qty: Required quantity for WO
            cumulative_transferred: Cumulative qty transferred to Department Warehouse
            current_stock: Current stock in Department Warehouse
        
        Returns: dict with status, transfer_percent, item_name, stock_entries
        
        Example:
        >>> self.determine_transfer_status("ITEM-001", 100, 100, 95)
        {'status': 'Fully Transferred', 'transfer_percent': 100.0, ...}
        """
        item = frappe.get_doc("Item", item_code)
        transfer_percent = (cumulative_transferred / required_qty * 100) if required_qty > 0 else 0
        
        result = {
            'item_name': item.item_name or item_code,
            'status': 'Not Transferred',
            'transfer_percent': round(transfer_percent, 2),
            'stock_entries': []
        }
        
        # Get stock entry details
        entries = self.get_transfer_entries(item_code, self.work_order, self.get_department_warehouse(frappe.get_doc("Work Order", self.work_order)))
        result['stock_entries'] = [
            {
                'stock_entry': e.stock_entry,
                'posting_date': e.posting_date,
                'qty': e.qty,
                'user': e.user
            }
            for e in entries
        ]
        
        if cumulative_transferred >= required_qty:
            result['status'] = 'Fully Transferred'
        elif cumulative_transferred > 0:
            result['status'] = 'Partially Transferred'
        
        return result
    
    def classify_material_type(self, item_code, work_order):
        """
        Classify material type:
        - Raw Material
        - Purchased Component
        - Manufactured Component
        - Common Component
        - Sub Assembly
        - Subcontracted Item
        
        Args:
            item_code: Item code
            work_order: Work Order document
        
        Returns: str - Material type classification
        
        Example:
        >>> self.classify_material_type("ITEM-001", wo)
        'Raw Material'
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
    
    def get_department_warehouse(self, work_order):
        """
        Get Department Warehouse for Work Order from Job Card
        
        Business Rule: WH-002 - Department Warehouse Mapping
        Business Rule: MR-014 - Department WIP as Source of Truth
        
        Args:
            work_order: Work Order document
        
        Returns: str - Department warehouse name
        
        Dependencies:
        - Job Card (wip_warehouse field)
        - Warehouse
        
        Example:
        >>> self.get_department_warehouse(wo)
        'WIP-Ralu In - TPL'
        """
        # Get WIP Warehouse from Job Card (not Work Order)
        # Job Card has the correct wip_warehouse assigned during creation
        job_card = frappe.db.get_value(
            "Job Card",
            {"work_order": work_order.name},
            "wip_warehouse"
        )
        
        if job_card:
            return job_card
        
        # Fallback: Try Work Order's wip_warehouse
        if work_order.get('wip_warehouse'):
            return work_order.get('wip_warehouse')
        
        # Fallback: Get Plant Floor from Work Order
        plant_floor = work_order.get('custom_plant_floor') or work_order.get('plant_floor')
        
        if plant_floor:
            # Map Plant Floor to Warehouse
            warehouse = frappe.db.get_value(
                "Warehouse",
                {
                    "name": ["like", f"WIP-{plant_floor}%"],
                    "is_group": 0
                },
                "name"
            )
            
            if warehouse:
                return warehouse
        
        # Final fallback: Use first WIP warehouse
        warehouse = frappe.db.get_value(
            "Warehouse",
            {"name": ["like", "WIP-%"], "is_group": 0},
            "name"
        )
        
        return warehouse
    
    def get_actual_stock(self, item_code, warehouse=None):
        """
        Get actual stock balance from Stock Ledger
        
        Args:
            item_code: Item code
            warehouse: Warehouse name (optional)
        
        Returns: float - Actual stock quantity
        
        Dependencies:
        - Stock Ledger Entry
        
        Example:
        >>> self.get_actual_stock("ITEM-001", "WIP-CNC")
        150.5
        """
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
        
        return stock_balance[0].qty if stock_balance and stock_balance[0].qty else 0.0
    
    def get_available_stock_in_wip(self, item_code, warehouse):
        """
        Get available stock in Department WIP warehouse
        
        Business Rule: MR-014 - Department WIP as Source of Truth
        Business Rule: OD-006 - Material Readiness Based on WIP Availability
        
        This method checks ACTUAL STOCK in the Department WIP warehouse,
        regardless of which Work Order transferred it.
        
        Department WIP is operational inventory shared across Work Orders.
        Material Readiness evaluates current stock, not transfer history.
        
        Args:
            item_code: Item code
            warehouse: Department warehouse name
        
        Returns: float - Available stock quantity
        
        Dependencies:
            - Bin (stock balance)
            - Stock Ledger Entry
        
        Example:
        >>> self.get_available_stock_in_wip("ITEM-001", "WIP-CNC - TPL")
        150.5
        
        Test Case:
        - test_mr_014_department_wip_source_of_truth
        """
        # MR-014: Get actual stock from Bin (real-time availability)
        actual_qty = frappe.db.get_value(
            "Bin",
            {"item_code": item_code, "warehouse": warehouse},
            "actual_qty"
        )
        
        return actual_qty or 0.0
    
    def get_cumulative_transferred_qty(self, item_code, work_order, warehouse):
        """
        Get cumulative quantity transferred to Department Warehouse
        
        Business Rule: MR-011 - Cumulative Availability Check
        
        This method sums ALL Material Transfer entries for the item and work order,
        regardless of whether they were transferred in single or multiple Stock Entries.
        
        Args:
            item_code: Item code
            work_order: Work Order name
            warehouse: Department warehouse name
        
        Returns: float - Cumulative transferred quantity
        
        Dependencies:
        - Stock Entry
        - Stock Entry Detail
        
        Example:
        >>> self.get_cumulative_transferred_qty("ITEM-001", "WO-2026-001", "WIP-CNC")
        100.0
        
        Test Case:
        - test_mr_011_cumulative_availability_check
        """
        transfers = frappe.db.sql("""
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
        
        return transfers[0].qty if transfers and transfers[0].qty else 0.0
    
    def get_transfer_entries(self, item_code, work_order, warehouse):
        """
        Get details of all Stock Entries that transferred material to Department Warehouse
        
        Business Rule: MR-011 - Working Set Principle
        
        Args:
            item_code: Item code
            work_order: Work Order name
            warehouse: Department warehouse name
        
        Returns: list of dicts with stock entry details
        
        Dependencies:
        - Stock Entry
        - Stock Entry Detail
        
        Example:
        >>> entries = self.get_transfer_entries("ITEM-001", "WO-2026-001", "WIP-CNC")
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
                se.owner as user
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
    
    def get_shortage_reason(self, transfer_status):
        """
        Get shortage reason based on transfer status
        
        Args:
            transfer_status: dict with transfer status info
        
        Returns: str - Human-readable shortage reason
        
        Example:
        >>> self.get_shortage_reason({'status': 'Not Transferred', ...})
        'Materials not transferred by Stores'
        """
        status = transfer_status.get('status')
        transfer_percent = transfer_status.get('transfer_percent', 0)
        
        if status == 'Not Transferred':
            return "Materials not transferred by Stores to Department Warehouse"
        elif status == 'Partially Transferred':
            return f"Partial transfer completed ({transfer_percent}%). Remaining quantity pending."
        elif status == 'Fully Transferred':
            return "Materials transferred but consumed/used"
        
        return "Insufficient stock in Department Warehouse"
    
    def get_suggested_action(self, transfer_status):
        """
        Get suggested action based on transfer status
        
        Args:
            transfer_status: dict with transfer status info
        
        Returns: str - Suggested action
        
        Example:
        >>> self.get_suggested_action({'status': 'Partially Transferred', ...})
        'Request Stores to transfer remaining quantity'
        """
        status = transfer_status.get('status')
        
        if status == 'Not Transferred':
            return "Contact Stores department to initiate material transfer"
        elif status == 'Partially Transferred':
            return "Request Stores to transfer remaining quantity"
        elif status == 'Fully Transferred':
            return "Check for material wastage or unauthorized usage"
        
        return "Review material requirements with Planning department"
    
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
    
    Business Rules:
    - MR-010: Stores to Production handoff validation
    - MR-011: Cumulative availability check
    
    Args:
        work_order: Work Order name
    
    Returns: dict with readiness status, transferred items, shortage details
    
    Example:
    >>> result = evaluate_material_readiness("WO-2026-001")
    >>> result['is_ready']
    True
    
    Test Case:
    - test_mr_010_stores_transfer_validation
    - test_mr_011_cumulative_availability_check
    """
    engine = MaterialReadinessEngine(work_order=work_order)
    return engine.evaluate_material_readiness()


@frappe.whitelist()
def can_job_card_start(job_card):
    """
    Check if Job Card can start based on material readiness
    
    Business Rule: MR-010 - Production starts only after Stores transfer
    
    Args:
        job_card: Job Card name
    
    Returns: dict with can_start, reason, material_status
    
    Example:
    >>> result = can_job_card_start("JC-2026-001")
    >>> result['can_start']
    True
    
    Test Case:
    - test_mr_010_job_card_start_permission
    """
    if not job_card:
        return {'can_start': False, 'reason': 'Job Card is required'}
    
    jc = frappe.get_doc("Job Card", job_card)
    
    if not jc.work_order:
        return {'can_start': False, 'reason': 'Job Card not linked to Work Order'}
    
    # Evaluate material readiness for the Work Order
    engine = MaterialReadinessEngine(work_order=jc.work_order)
    readiness = engine.evaluate_material_readiness()
    
    if readiness['is_ready']:
        return {
            'can_start': True,
            'reason': 'Materials available in Department Warehouse',
            'material_status': 'Ready',
            'transfer_summary': readiness['transfer_summary']
        }
    else:
        missing_items = readiness['missing_items']
        return {
            'can_start': False,
            'reason': f"Materials not available: {', '.join(missing_items)}",
            'material_status': 'Not Ready',
            'missing_items': missing_items,
            'shortage_details': readiness['shortage_details'],
            'transfer_summary': readiness['transfer_summary']
        }


@frappe.whitelist()
def get_transfer_suggestions(work_order):
    """
    Get material transfer suggestions for Stores department
    
    Business Rule: MR-010 - Stores responsibility for material transfer
    
    Args:
        work_order: Work Order name
    
    Returns: list of transfer suggestions with items, quantities, warehouses
    
    Example:
    >>> suggestions = get_transfer_suggestions("WO-2026-001")
    >>> len(suggestions)
    5
    
    Test Case:
    - test_mr_010_transfer_suggestions
    """
    if not work_order:
        return []
    
    wo = frappe.get_doc("Work Order", work_order)
    engine = MaterialReadinessEngine(work_order=work_order)
    
    # Get Department Warehouse
    department_warehouse = engine.get_department_warehouse(wo)
    
    # Get required materials
    required_materials = engine.get_required_materials(wo)
    
    suggestions = []
    
    for material in required_materials:
        item_code = material.get('item_code')
        required_qty = material.get('qty')
        source_warehouse = material.get('source_warehouse')
        
        # Get cumulative transferred qty
        cumulative_transferred = engine.get_cumulative_transferred_qty(
            item_code, work_order, department_warehouse
        )
        
        # Calculate remaining qty to transfer
        remaining_qty = required_qty - cumulative_transferred
        
        if remaining_qty > 0:
            # Get current stock in source warehouse
            source_stock = engine.get_actual_stock(item_code, source_warehouse)
            
            suggestions.append({
                'item_code': item_code,
                'item_name': frappe.db.get_value("Item", item_code, "item_name"),
                'required_qty': required_qty,
                'already_transferred': cumulative_transferred,
                'remaining_to_transfer': remaining_qty,
                'available_in_source': source_stock,
                'source_warehouse': source_warehouse,
                'target_warehouse': department_warehouse,
                'can_transfer': source_stock >= remaining_qty,
                'shortage_in_source': max(0, remaining_qty - source_stock)
            })
    
    return suggestions


@frappe.whitelist()
def create_material_transfer_stock_entry(work_order, items=None):
    """
    Create Material Transfer Stock Entry for Stores department
    
    Business Rule: MR-010 - Stores transfers materials to Department Warehouse
    
    Args:
        work_order: Work Order name
        items: List of items to transfer (optional, defaults to all missing items)
    
    Returns: dict with stock_entry name and status
    
    Example:
    >>> result = create_material_transfer_stock_entry("WO-2026-001")
    >>> result['stock_entry']
    'STE-2026-001'
    
    Test Case:
    - test_mr_010_create_transfer_entry
    """
    if not work_order:
        frappe.throw(_("Work Order is required"))
    
    wo = frappe.get_doc("Work Order", work_order)
    engine = MaterialReadinessEngine(work_order=work_order)
    
    # Get Department Warehouse
    department_warehouse = engine.get_department_warehouse(wo)
    
    # Get transfer suggestions
    suggestions = get_transfer_suggestions(work_order)
    
    if not suggestions:
        frappe.msgprint(_("All materials already transferred to Department Warehouse"))
        return {'stock_entry': None, 'status': 'Already Complete'}
    
    # Filter items if specified
    if items:
        suggestions = [s for s in suggestions if s['item_code'] in items]
    
    # Create Stock Entry
    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.purpose = "Material Transfer for Manufacture"
    stock_entry.work_order = work_order
    stock_entry.from_warehouse = suggestions[0]['source_warehouse'] if suggestions else None
    stock_entry.to_warehouse = department_warehouse
    
    for suggestion in suggestions:
        if suggestion['can_transfer']:
            stock_entry.append("items", {
                'item_code': suggestion['item_code'],
                'qty': suggestion['remaining_to_transfer'],
                's_warehouse': suggestion['source_warehouse'],
                't_warehouse': department_warehouse,
                'uom': frappe.db.get_value("Item", suggestion['item_code'], "stock_uom")
            })
    
    stock_entry.insert()
    stock_entry.submit()
    
    frappe.msgprint(_("Stock Entry {0} created and submitted").format(stock_entry.name))
    
    return {
        'stock_entry': stock_entry.name,
        'status': 'Created',
        'items_transferred': len(stock_entry.items)
    }
