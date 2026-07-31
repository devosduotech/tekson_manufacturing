import frappe
from tekson_manufacturing.readiness.material_readiness import MaterialReadinessEngine


@frappe.whitelist()
def get_material_status(item_code, warehouse=None):
    """
    Get material stock status
    
    Args:
        item_code: Item code
        warehouse: Optional warehouse filter
    
    Returns: dict with stock balance
    """
    from tekson_manufacturing.services.material_service import MaterialService
    
    service = MaterialService()
    return {
        'item_code': item_code,
        'warehouse': warehouse,
        'actual_qty': service.get_stock_balance(item_code, warehouse)
    }


@frappe.whitelist()
def check_item_readiness(item_code, required_qty, work_order=None):
    """
    Check if item is ready for production
    
    Args:
        item_code: Item code
        required_qty: Required quantity
        work_order: Optional Work Order reference
    
    Returns: dict with readiness status
    """
    engine = MaterialReadinessEngine(work_order=work_order)
    
    # Classify material
    if work_order:
        wo_doc = frappe.get_doc("Work Order", work_order)
        material_type = engine.classify_material_type(item_code, wo_doc)
    else:
        material_type = "Raw Material"
    
    # Check availability
    availability = engine.check_material_availability(
        item_code, 
        required_qty, 
        None,
        material_type,
        work_order
    )
    
    return {
        'item_code': item_code,
        'material_type': material_type,
        'required_qty': required_qty,
        'available_qty': availability.get('available_qty'),
        'is_available': availability.get('is_available'),
        'shortage_qty': availability.get('shortage_qty'),
        'reason': availability.get('reason')
    }
